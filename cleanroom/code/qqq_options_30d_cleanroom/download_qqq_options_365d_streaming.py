from __future__ import annotations

import argparse
import gzip
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import date, datetime, time as dtime, timedelta
from pathlib import Path
from typing import Iterable

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from download_qqq_options import (
    ET,
    UTC,
    AlpacaClient,
    ContractDay,
    RateLimiter,
    build_contract_day_universe,
    build_spot_reference_map,
    contracts_to_frame,
    fetch_one_contract_day,
    get_env,
    local_market_window,
    resolve_today,
    select_stock_feed,
)


def step_label(step: int) -> str:
    sign = "p" if step >= 0 else "n"
    return f"{sign}{abs(int(step)):02d}"


def slot_label(dte: int, option_type: str, strike_step_distance: int) -> str:
    return f"dte{int(dte):02d}_{option_type}_step_{step_label(int(strike_step_distance))}"


class IncrementalParquetWriter:
    def __init__(self, path: Path, compression: str = "snappy") -> None:
        self.path = path
        self.compression = compression
        self.writer: pq.ParquetWriter | None = None
        self.schema: pa.Schema | None = None

    def write(self, frame: pd.DataFrame) -> None:
        if frame.empty:
            return
        table = pa.Table.from_pandas(frame, preserve_index=False)
        if self.writer is None:
            self.schema = table.schema.remove_metadata()
            self.writer = pq.ParquetWriter(self.path, self.schema, compression=self.compression)
        if self.schema is not None:
            table = table.replace_schema_metadata(None).cast(self.schema)
        self.writer.write_table(table)

    def close(self) -> None:
        if self.writer is not None:
            self.writer.close()
            self.writer = None


def append_csv(frame: pd.DataFrame, path: Path, compression: str = "gzip") -> None:
    if frame.empty:
        return
    write_header = not path.exists()
    if compression == "gzip":
        mode = "wt" if write_header else "at"
        for attempt in range(6):
            try:
                with gzip.open(path, mode, encoding="utf-8", newline="") as handle:
                    frame.to_csv(handle, index=False, header=write_header)
                return
            except PermissionError:
                if attempt == 5:
                    raise
                time.sleep(0.5 * (attempt + 1))
        return
    mode = "w" if write_header else "a"
    for attempt in range(6):
        try:
            with path.open(mode, encoding="utf-8", newline="") as handle:
                frame.to_csv(handle, index=False, header=write_header)
            return
        except PermissionError:
            if attempt == 5:
                raise
            time.sleep(0.5 * (attempt + 1))


def csv_ready_dense(frame: pd.DataFrame) -> pd.DataFrame:
    dense_csv = frame.copy()
    dense_csv["timestamp_et"] = dense_csv["timestamp_et"].astype(str)
    dense_csv["timestamp"] = dense_csv["timestamp"].astype(str)
    dense_csv["trade_date"] = dense_csv["trade_date"].astype(str)
    dense_csv["expiration_date"] = dense_csv["expiration_date"].astype(str)
    return dense_csv


def csv_ready_wide(frame: pd.DataFrame) -> pd.DataFrame:
    wide_csv = frame.copy()
    wide_csv["timestamp_et"] = wide_csv["timestamp_et"].astype(str)
    wide_csv["timestamp_utc"] = wide_csv["timestamp_utc"].astype(str)
    wide_csv["trade_date"] = wide_csv["trade_date"].astype(str)
    return wide_csv


def build_dense_panel_day(option_bars: pd.DataFrame, manifest_day: pd.DataFrame) -> pd.DataFrame:
    if manifest_day.empty:
        return pd.DataFrame()

    raw_groups: dict[str, pd.DataFrame] = {}
    if not option_bars.empty:
        for symbol, group in option_bars.groupby("symbol", sort=False):
            raw_groups[symbol] = group.copy()

    trade_date = pd.to_datetime(manifest_day["trade_date"].iloc[0]).date()
    session_minutes = pd.date_range(
        start=datetime.combine(trade_date, dtime(9, 30), ET),
        periods=390,
        freq="min",
        tz=ET,
    )

    dense_frames: list[pd.DataFrame] = []
    for row in manifest_day.itertuples(index=False):
        dense = pd.DataFrame({"timestamp_et": session_minutes})
        dense["trade_date"] = trade_date
        dense["symbol"] = row.symbol
        dense["expiration_date"] = pd.to_datetime(row.expiration_date).date()
        dense["dte"] = int(row.dte)
        dense["option_type"] = row.option_type
        dense["strike_price"] = float(row.strike_price)
        dense["strike_step_distance"] = int(row.strike_step_distance)
        dense["spot_reference"] = float(row.spot_reference)

        observed = raw_groups.get(row.symbol)
        if observed is None or observed.empty:
            dense["timestamp"] = dense["timestamp_et"].dt.tz_convert(UTC)
            dense["open"] = pd.NA
            dense["high"] = pd.NA
            dense["low"] = pd.NA
            dense["close"] = pd.NA
            dense["volume"] = 0
            dense["trade_count"] = 0
            dense["vwap"] = pd.NA
            dense["has_trade_bar"] = False
            dense["is_synthetic_bar"] = False
            dense["session_has_any_trade"] = False
            dense_frames.append(dense)
            continue

        observed = observed[
            [
                "timestamp",
                "timestamp_et",
                "open",
                "high",
                "low",
                "close",
                "volume",
                "trade_count",
                "vwap",
            ]
        ].copy()
        observed["has_trade_bar"] = True
        dense = dense.merge(
            observed[
                ["timestamp_et", "timestamp", "open", "high", "low", "close", "volume", "trade_count", "vwap", "has_trade_bar"]
            ],
            on="timestamp_et",
            how="left",
        )
        dense["timestamp"] = dense["timestamp"].fillna(dense["timestamp_et"].dt.tz_convert(UTC))
        dense["has_trade_bar"] = dense["has_trade_bar"].astype("boolean").fillna(False)

        reference_close = dense["close"].ffill().bfill()
        reference_vwap = dense["vwap"].ffill()
        reference_vwap = reference_vwap.fillna(reference_close)
        for price_col in ["open", "high", "low", "close"]:
            dense[price_col] = dense[price_col].fillna(reference_close)
        dense["vwap"] = dense["vwap"].fillna(reference_vwap)
        dense["volume"] = dense["volume"].fillna(0)
        dense["trade_count"] = dense["trade_count"].fillna(0)
        dense["is_synthetic_bar"] = ((~dense["has_trade_bar"]) & dense["close"].notna()).astype("boolean")
        dense["session_has_any_trade"] = True
        dense_frames.append(dense)

    dense_panel = pd.concat(dense_frames, ignore_index=True)
    dense_panel = dense_panel.sort_values(["trade_date", "symbol", "timestamp_et"]).reset_index(drop=True)
    return dense_panel


def build_slot_map_day(dense_day: pd.DataFrame) -> pd.DataFrame:
    if dense_day.empty:
        return pd.DataFrame()
    slot_map = (
        dense_day[
            [
                "trade_date",
                "slot",
                "symbol",
                "expiration_date",
                "dte",
                "option_type",
                "strike_price",
                "strike_step_distance",
                "spot_reference",
                "session_has_any_trade",
            ]
        ]
        .drop_duplicates()
        .sort_values(["trade_date", "dte", "option_type", "strike_step_distance", "symbol"])
        .reset_index(drop=True)
    )
    slot_map["trade_date"] = slot_map["trade_date"].astype(str)
    slot_map["expiration_date"] = slot_map["expiration_date"].astype(str)
    return slot_map


def build_wide_day(
    dense_day: pd.DataFrame,
    underlying_day: pd.DataFrame,
    all_slots: list[str],
    underlying_prefix: str,
) -> pd.DataFrame:
    if dense_day.empty:
        return pd.DataFrame()
    dense_day = dense_day.copy()
    dense_day["slot"] = [
        slot_label(dte=row.dte, option_type=row.option_type, strike_step_distance=row.strike_step_distance)
        for row in dense_day.itertuples(index=False)
    ]

    features = ["close", "volume", "trade_count", "vwap", "has_trade_bar", "is_synthetic_bar"]
    wide_parts: list[pd.DataFrame] = []
    for feature in features:
        pivot = dense_day.pivot(index="timestamp_et", columns="slot", values=feature)
        pivot = pivot.reindex(columns=all_slots)
        if feature in {"has_trade_bar", "is_synthetic_bar"}:
            pivot = pivot.astype("boolean")
        else:
            pivot = pivot.apply(pd.to_numeric, errors="coerce").astype("float64")
        pivot.columns = [f"{col}_{feature}" for col in pivot.columns]
        wide_parts.append(pivot)

    wide = pd.concat(wide_parts, axis=1).sort_index(axis=1).reset_index()
    wide["timestamp_utc"] = wide["timestamp_et"].dt.tz_convert("UTC")
    wide["trade_date"] = wide["timestamp_et"].dt.date

    underlying_cols = [
        f"{underlying_prefix}_open",
        f"{underlying_prefix}_high",
        f"{underlying_prefix}_low",
        f"{underlying_prefix}_close",
        f"{underlying_prefix}_volume",
        f"{underlying_prefix}_trade_count",
        f"{underlying_prefix}_vwap",
    ]
    if not underlying_day.empty:
        merge_cols = ["timestamp_et", *underlying_cols]
        wide = wide.merge(underlying_day[merge_cols], on="timestamp_et", how="left")
    else:
        for column in underlying_cols:
            wide[column] = pd.NA

    front_cols = [
        "timestamp_et",
        "timestamp_utc",
        "trade_date",
        *underlying_cols,
    ]
    remaining_cols = [col for col in wide.columns if col not in front_cols]
    wide = wide[front_cols + remaining_cols]
    return wide


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Streamed 365-day options downloader with compressed CSV exports.")
    parser.add_argument("--underlying", default="QQQ")
    parser.add_argument("--lookback-days", type=int, default=365)
    parser.add_argument("--max-dte", type=int, default=7)
    parser.add_argument("--strike-steps", type=int, default=5)
    parser.add_argument("--today", default="")
    parser.add_argument("--workers", type=int, default=6)
    parser.add_argument("--requests-per-second", type=float, default=2.8)
    parser.add_argument("--stock-feed-order", default="sip,delayed_sip,iex")
    parser.add_argument("--output-dir", default="output")
    parser.add_argument("--tag", default="365d")
    parser.add_argument("--csv-compression", default="gzip", choices=["gzip", "none"])
    return parser


def make_names(output_dir: Path, underlying: str, tag: str, csv_compression: str) -> dict[str, Path]:
    prefix = f"{underlying.lower()}_{tag}"
    csv_suffix = ".csv.gz" if csv_compression == "gzip" else ".csv"
    return {
        "underlying_parquet": output_dir / f"{prefix}_underlying_1min.parquet",
        "contracts_parquet": output_dir / f"{prefix}_option_contracts.parquet",
        "universe_parquet": output_dir / f"{prefix}_option_daily_universe.parquet",
        "raw_parquet": output_dir / f"{prefix}_option_1min_bars.parquet",
        "dense_parquet": output_dir / f"{prefix}_option_1min_dense.parquet",
        "dense_csv": output_dir / f"{prefix}_option_1min_dense{csv_suffix}",
        "wide_parquet": output_dir / f"{prefix}_option_1min_wide_backtest.parquet",
        "wide_csv": output_dir / f"{prefix}_option_1min_wide_backtest{csv_suffix}",
        "slot_map_csv": output_dir / f"{prefix}_option_slot_map.csv",
        "manifest_csv": output_dir / f"{prefix}_fetch_manifest.csv",
        "audit_json": output_dir / f"{prefix}_audit_report.json",
        "empty_csv": output_dir / f"{prefix}_confirmed_empty_contract_days.csv",
        "failures_json": output_dir / f"{prefix}_failures.json",
    }


def chunked_retry_contract_days(
    client: AlpacaClient,
    contract_days: list[ContractDay],
    workers: int,
    max_passes: int = 3,
) -> tuple[list[pd.DataFrame], list[dict], list[dict]]:
    pending = contract_days[:]
    all_frames: list[pd.DataFrame] = []
    all_manifest_rows: list[dict] = []
    last_failures: list[dict] = []

    for attempt in range(1, max_passes + 1):
        if not pending:
            break
        attempt_failures: list[dict] = []
        successful_contract_days: set[tuple[date, str]] = set()
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {
                executor.submit(fetch_one_contract_day, client, contract_day): contract_day for contract_day in pending
            }
            for future in as_completed(futures):
                contract_day = futures[future]
                try:
                    _, frame, manifest_row = future.result()
                    all_manifest_rows.append(manifest_row)
                    successful_contract_days.add((contract_day.trade_date, contract_day.symbol))
                    if not frame.empty:
                        all_frames.append(frame)
                except Exception as exc:
                    attempt_failures.append(
                        {
                            "trade_date": contract_day.trade_date.isoformat(),
                            "symbol": contract_day.symbol,
                            "expiration_date": contract_day.expiration_date.isoformat(),
                            "dte": contract_day.dte,
                            "option_type": contract_day.option_type,
                            "strike_price": contract_day.strike_price,
                            "strike_step_distance": contract_day.strike_step_distance,
                            "spot_reference": contract_day.spot_reference,
                            "error": str(exc),
                            "attempt": attempt,
                        }
                    )
        if not attempt_failures:
            pending = []
            last_failures = []
            break
        failed_keys = {(date.fromisoformat(item["trade_date"]), item["symbol"]) for item in attempt_failures}
        pending = [item for item in pending if (item.trade_date, item.symbol) in failed_keys]
        last_failures = attempt_failures
    return all_frames, all_manifest_rows, last_failures


def main() -> None:
    args = build_parser().parse_args()
    today = resolve_today(args.today)
    start_date = today - timedelta(days=args.lookback_days)
    end_date = today
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    names = make_names(output_dir, args.underlying, args.tag, args.csv_compression)
    underlying_prefix = args.underlying.lower()

    api_key = get_env(["ALPACA_API_KEY", "APCA_API_KEY_ID"])
    api_secret = get_env(["ALPACA_SECRET_KEY", "APCA_API_SECRET_KEY"])
    trading_base_url = get_env(["ALPACA_API_BASE_URL"])

    client = AlpacaClient(
        api_key=api_key,
        api_secret=api_secret,
        trading_base_url=trading_base_url,
        rate_limiter=RateLimiter(args.requests_per_second),
    )

    print(json.dumps({"phase": "calendar", "start_date": start_date.isoformat(), "end_date": end_date.isoformat()}))
    calendar = client.fetch_calendar(start_date, end_date)
    trading_dates = [date.fromisoformat(item["date"]) for item in calendar]
    if not trading_dates:
        raise RuntimeError("no trading dates found for requested lookback")

    first_window_start, _ = local_market_window(trading_dates[0])
    _, last_window_end = local_market_window(trading_dates[-1])
    stock_feed, underlying_bars = select_stock_feed(
        client=client,
        symbol=args.underlying,
        start_dt=first_window_start,
        end_dt=last_window_end,
        feed_order=[feed.strip() for feed in args.stock_feed_order.split(",") if feed.strip()],
    )
    if underlying_bars.empty:
        raise RuntimeError("underlying bars request returned no data")
    underlying_bars.to_parquet(names["underlying_parquet"], index=False)
    spot_map = build_spot_reference_map(underlying_bars)

    print(json.dumps({"phase": "contracts"}))
    active_contracts = contracts_to_frame(
        client.fetch_option_contracts(
            underlying_symbol=args.underlying,
            expiration_date_gte=start_date,
            expiration_date_lte=end_date + timedelta(days=args.max_dte),
            status="active",
        )
    )
    inactive_contracts = contracts_to_frame(
        client.fetch_option_contracts(
            underlying_symbol=args.underlying,
            expiration_date_gte=start_date,
            expiration_date_lte=end_date + timedelta(days=args.max_dte),
            status="inactive",
        )
    )
    all_contracts = pd.concat([active_contracts, inactive_contracts], ignore_index=True)
    all_contracts = all_contracts.drop_duplicates(subset=["symbol"]).reset_index(drop=True)
    all_contracts.to_parquet(names["contracts_parquet"], index=False)

    contract_day_universe = build_contract_day_universe(
        contracts=all_contracts,
        trading_dates=trading_dates,
        spot_map=spot_map,
        max_dte=args.max_dte,
        strike_steps=args.strike_steps,
        underlying_symbol=args.underlying,
    )
    contract_day_universe.to_parquet(names["universe_parquet"], index=False)
    all_slots = [
        slot_label(dte=dte, option_type=option_type, strike_step_distance=step)
        for dte in range(args.max_dte + 1)
        for option_type in ("call", "put")
        for step in range(-args.strike_steps, args.strike_steps + 1)
    ]

    underlying_small = underlying_bars.copy()
    underlying_small["timestamp"] = pd.to_datetime(underlying_small["timestamp"], utc=True)
    underlying_small["timestamp_et"] = underlying_small["timestamp"].dt.tz_convert(ET)
    underlying_small["trade_date"] = underlying_small["timestamp_et"].dt.date
    if "symbol" in underlying_small.columns:
        underlying_small = underlying_small[underlying_small["symbol"] == args.underlying].copy()
    if "S" in underlying_small.columns:
        underlying_small = underlying_small[underlying_small["S"] == args.underlying].copy()
    underlying_small = underlying_small[
        ["trade_date", "timestamp_et", "open", "high", "low", "close", "volume", "trade_count", "vwap"]
    ].rename(
        columns={
            "open": f"{underlying_prefix}_open",
            "high": f"{underlying_prefix}_high",
            "low": f"{underlying_prefix}_low",
            "close": f"{underlying_prefix}_close",
            "volume": f"{underlying_prefix}_volume",
            "trade_count": f"{underlying_prefix}_trade_count",
            "vwap": f"{underlying_prefix}_vwap",
        }
    )

    raw_writer = IncrementalParquetWriter(names["raw_parquet"])
    dense_writer = IncrementalParquetWriter(names["dense_parquet"])
    wide_writer = IncrementalParquetWriter(names["wide_parquet"])

    manifest_rows: list[dict] = []
    failure_rows: list[dict] = []
    unique_contracts: set[str] = set()
    selected_contract_days = 0
    successful_requests = 0
    failed_requests = 0
    nonempty_contract_days = 0
    raw_bar_rows = 0
    raw_minute_count = 0
    dense_non_na_count = 0
    dense_non_na_nonempty_count = 0

    universe_by_date = {
        trade_date: group.copy().reset_index(drop=True)
        for trade_date, group in contract_day_universe.groupby("trade_date", sort=True)
    }
    total_dates = len(universe_by_date)
    for idx, trade_date in enumerate(sorted(universe_by_date), start=1):
        day_universe = universe_by_date[trade_date]
        contract_days = [
            ContractDay(
                trade_date=row.trade_date,
                symbol=row.symbol,
                expiration_date=row.expiration_date,
                dte=int(row.dte),
                option_type=str(row.option_type),
                strike_price=float(row.strike_price),
                strike_step_distance=int(row.strike_step_distance),
                spot_reference=float(row.spot_reference),
            )
            for row in day_universe.itertuples(index=False)
        ]

        day_frames, day_manifest_rows, day_failures = chunked_retry_contract_days(
            client=client,
            contract_days=contract_days,
            workers=args.workers,
            max_passes=3,
        )

        selected_contract_days += len(contract_days)
        successful_requests += len(day_manifest_rows)
        failed_requests += len(day_failures)
        manifest_rows.extend(day_manifest_rows)
        failure_rows.extend(day_failures)
        unique_contracts.update(day_universe["symbol"].tolist())

        manifest_day = pd.DataFrame(day_manifest_rows)
        if manifest_day.empty:
            print(json.dumps({"phase": "progress", "trade_date": trade_date.isoformat(), "index": idx, "total_dates": total_dates, "status": "no_successful_requests"}))
            continue

        manifest_day = manifest_day.sort_values(["trade_date", "symbol"]).reset_index(drop=True)

        if day_frames:
            option_bars_day = pd.concat(day_frames, ignore_index=True)
            option_bars_day = option_bars_day.sort_values(["trade_date", "symbol", "timestamp"]).reset_index(drop=True)
        else:
            option_bars_day = pd.DataFrame()
        raw_writer.write(option_bars_day)

        raw_bar_rows += len(option_bars_day)
        raw_minute_count += int(manifest_day["bar_count"].sum())
        nonempty_contract_days += int((manifest_day["bar_count"] > 0).sum())

        dense_day = build_dense_panel_day(option_bars=option_bars_day, manifest_day=manifest_day)
        dense_day["slot"] = [
            slot_label(dte=row.dte, option_type=row.option_type, strike_step_distance=row.strike_step_distance)
            for row in dense_day.itertuples(index=False)
        ]
        dense_writer.write(dense_day.drop(columns=["slot"]))

        dense_non_na_count += int(dense_day["close"].notna().sum())
        nonempty_dense_day = dense_day[dense_day["session_has_any_trade"] == True]
        dense_non_na_nonempty_count += int(nonempty_dense_day["close"].notna().sum())

        dense_csv_day = csv_ready_dense(dense_day.drop(columns=["slot"]))
        append_csv(dense_csv_day, names["dense_csv"], compression=args.csv_compression)

        slot_map_day = build_slot_map_day(dense_day)
        append_csv(slot_map_day, names["slot_map_csv"], compression="none")

        underlying_day = underlying_small[underlying_small["trade_date"] == trade_date].copy()
        wide_day = build_wide_day(
            dense_day,
            underlying_day,
            all_slots=all_slots,
            underlying_prefix=underlying_prefix,
        )
        wide_writer.write(wide_day)
        wide_csv_day = csv_ready_wide(wide_day)
        append_csv(wide_csv_day, names["wide_csv"], compression=args.csv_compression)

        print(
            json.dumps(
                {
                    "phase": "progress",
                    "trade_date": trade_date.isoformat(),
                    "index": idx,
                    "total_dates": total_dates,
                    "contract_days": len(contract_days),
                    "successful_requests": len(day_manifest_rows),
                    "failed_requests": len(day_failures),
                    "raw_rows_day": int(len(option_bars_day)),
                }
            )
        )

    raw_writer.close()
    dense_writer.close()
    wide_writer.close()

    manifest = pd.DataFrame(manifest_rows).sort_values(["trade_date", "symbol"]).reset_index(drop=True)
    manifest.to_csv(names["manifest_csv"], index=False)

    if failure_rows:
        names["failures_json"].write_text(json.dumps(failure_rows, indent=2))

    empty_contract_days = manifest[manifest["bar_count"] == 0].copy()
    if not empty_contract_days.empty:
        empty_contract_days.to_csv(names["empty_csv"], index=False)

    total_possible_minutes = selected_contract_days * 390
    total_nonempty_possible_minutes = max(nonempty_contract_days * 390, 1)
    audit = {
        "underlying": args.underlying,
        "window_start": start_date.isoformat(),
        "window_end": end_date.isoformat(),
        "trading_days": len(trading_dates),
        "stock_feed_used": stock_feed,
        "selected_contract_days": int(selected_contract_days),
        "unique_contracts": int(len(unique_contracts)),
        "bar_rows_downloaded": int(raw_bar_rows),
        "successful_contract_day_requests": int(successful_requests),
        "failed_contract_day_requests": int(failed_requests),
        "request_fill_rate": round((successful_requests / max(selected_contract_days, 1)) * 100.0, 3),
        "nonempty_contract_day_ratio": round((nonempty_contract_days / max(selected_contract_days, 1)) * 100.0, 3),
        "empty_contract_day_ratio": round(((selected_contract_days - nonempty_contract_days) / max(selected_contract_days, 1)) * 100.0, 3),
        "nonempty_contract_days": int(nonempty_contract_days),
        "minute_fill_pct_on_selected_contract_days": round((raw_minute_count / max(total_possible_minutes, 1)) * 100.0, 3),
        "minute_fill_pct_on_nonempty_contract_days": round((raw_minute_count / total_nonempty_possible_minutes) * 100.0, 3),
        "dense_minute_fill_pct_on_selected_contract_days": round((dense_non_na_count / max(total_possible_minutes, 1)) * 100.0, 3),
        "dense_minute_fill_pct_on_nonempty_contract_days": round((dense_non_na_nonempty_count / total_nonempty_possible_minutes) * 100.0, 3),
        "csv_compression": args.csv_compression,
    }
    names["audit_json"].write_text(json.dumps(audit, indent=2))
    print(json.dumps({"phase": "done", **audit}))


if __name__ == "__main__":
    main()
