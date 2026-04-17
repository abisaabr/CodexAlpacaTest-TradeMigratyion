from __future__ import annotations

import argparse
import gzip
import json
import shutil
from pathlib import Path

import pandas as pd

from download_qqq_options_365d_streaming import (
    IncrementalParquetWriter,
    append_csv,
    build_wide_day,
    csv_ready_dense,
    csv_ready_wide,
    make_names,
    slot_label,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Fill fully empty option contract-days from neighboring same-contract sessions.")
    parser.add_argument("--underlying", required=True)
    parser.add_argument("--tag", default="365d")
    parser.add_argument("--output-dir", default="output")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    output_dir = Path(args.output_dir).resolve()
    names = make_names(output_dir, args.underlying, args.tag, "gzip")
    underlying_prefix = args.underlying.lower()

    manifest = pd.read_csv(names["manifest_csv"])
    dense = pd.read_parquet(names["dense_parquet"])
    underlying = pd.read_parquet(names["underlying_parquet"])

    manifest["trade_date"] = pd.to_datetime(manifest["trade_date"]).dt.date
    dense["trade_date"] = pd.to_datetime(dense["trade_date"]).dt.date
    dense["expiration_date"] = pd.to_datetime(dense["expiration_date"]).dt.date
    dense["timestamp_et"] = pd.to_datetime(dense["timestamp_et"])
    dense["timestamp"] = pd.to_datetime(dense["timestamp"], utc=True)

    dense["neighbor_session_filled"] = False

    anchors = (
        dense[dense["close"].notna()]
        .sort_values(["symbol", "trade_date", "timestamp_et"])
        .groupby(["symbol", "trade_date"], as_index=False)
        .agg(first_close=("close", "first"), last_close=("close", "last"))
    )
    anchor_by_symbol = {
        symbol: group.sort_values("trade_date").reset_index(drop=True)
        for symbol, group in anchors.groupby("symbol", sort=False)
    }

    imputed_rows: list[dict] = []
    empty = manifest[manifest["bar_count"] == 0].copy()
    for row in empty.itertuples(index=False):
        anchor_group = anchor_by_symbol.get(row.symbol)
        if anchor_group is None or anchor_group.empty:
            continue
        prev_rows = anchor_group[anchor_group["trade_date"] < row.trade_date]
        next_rows = anchor_group[anchor_group["trade_date"] > row.trade_date]
        prev_close = float(prev_rows.iloc[-1]["last_close"]) if not prev_rows.empty else None
        next_close = float(next_rows.iloc[0]["first_close"]) if not next_rows.empty else None
        if prev_close is None and next_close is None:
            continue

        if prev_close is not None and next_close is not None:
            anchor_price = (prev_close + next_close) / 2.0
            source = "prev_next_avg"
        elif prev_close is not None:
            anchor_price = prev_close
            source = "prev_last_close"
        else:
            anchor_price = next_close
            source = "next_first_close"

        mask = (dense["symbol"] == row.symbol) & (dense["trade_date"] == row.trade_date)
        if not mask.any():
            continue
        dense.loc[mask, ["open", "high", "low", "close", "vwap"]] = anchor_price
        dense.loc[mask, ["volume", "trade_count"]] = 0.0
        dense.loc[mask, "has_trade_bar"] = False
        dense.loc[mask, "is_synthetic_bar"] = True
        dense.loc[mask, "neighbor_session_filled"] = True
        imputed_rows.append(
            {
                "trade_date": str(row.trade_date),
                "symbol": row.symbol,
                "expiration_date": row.expiration_date,
                "dte": int(row.dte),
                "option_type": row.option_type,
                "strike_price": float(row.strike_price),
                "source": source,
                "anchor_price": anchor_price,
                "prev_close": prev_close,
                "next_close": next_close,
            }
        )

    dense = dense.sort_values(["trade_date", "symbol", "timestamp_et"]).reset_index(drop=True)
    dense.to_parquet(names["dense_parquet"], index=False)

    dense_csv_gz = names["dense_csv"]
    if dense_csv_gz.exists():
        dense_csv_gz.unlink()
    dense_csv_plain = output_dir / f"{underlying_prefix}_{args.tag}_option_1min_dense.csv"
    if dense_csv_plain.exists():
        dense_csv_plain.unlink()
    append_csv(csv_ready_dense(dense), dense_csv_gz, compression="gzip")
    csv_ready_dense(dense).to_csv(dense_csv_plain, index=False)

    dense["slot"] = [
        slot_label(dte=row.dte, option_type=row.option_type, strike_step_distance=row.strike_step_distance)
        for row in dense.itertuples(index=False)
    ]
    slot_map = (
        dense[
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
                "neighbor_session_filled",
            ]
        ]
        .drop_duplicates()
        .sort_values(["trade_date", "dte", "option_type", "strike_step_distance", "symbol"])
        .reset_index(drop=True)
    )
    slot_map["trade_date"] = slot_map["trade_date"].astype(str)
    slot_map["expiration_date"] = slot_map["expiration_date"].astype(str)
    slot_map.to_csv(names["slot_map_csv"], index=False)

    underlying["timestamp"] = pd.to_datetime(underlying["timestamp"], utc=True)
    underlying["timestamp_et"] = underlying["timestamp"].dt.tz_convert("America/New_York")
    underlying["trade_date"] = underlying["timestamp_et"].dt.date
    if "symbol" in underlying.columns:
        underlying = underlying[underlying["symbol"] == args.underlying].copy()
    if "S" in underlying.columns:
        underlying = underlying[underlying["S"] == args.underlying].copy()
    underlying_small = underlying[
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

    all_slots = sorted(dense["slot"].dropna().unique().tolist())
    wide_parquet = names["wide_parquet"]
    if wide_parquet.exists():
        wide_parquet.unlink()
    wide_csv_gz = names["wide_csv"]
    if wide_csv_gz.exists():
        wide_csv_gz.unlink()
    wide_csv_plain = output_dir / f"{underlying_prefix}_{args.tag}_option_1min_wide_backtest.csv"
    if wide_csv_plain.exists():
        wide_csv_plain.unlink()

    wide_writer = IncrementalParquetWriter(wide_parquet)
    wrote_plain_header = False
    for trade_date, dense_day in dense.groupby("trade_date", sort=True):
        underlying_day = underlying_small[underlying_small["trade_date"] == trade_date].copy()
        wide_day = build_wide_day(
            dense_day.drop(columns=["slot"]).copy(),
            underlying_day,
            all_slots=all_slots,
            underlying_prefix=underlying_prefix,
        )
        wide_writer.write(wide_day)
        wide_csv_day = csv_ready_wide(wide_day)
        append_csv(wide_csv_day, wide_csv_gz, compression="gzip")
        wide_csv_day.to_csv(wide_csv_plain, index=False, header=not wrote_plain_header, mode="w" if not wrote_plain_header else "a")
        wrote_plain_header = True
    wide_writer.close()

    dense_fill_selected = float(dense["close"].notna().mean() * 100.0)
    dense_nonempty = dense[dense["session_has_any_trade"] == True]
    dense_fill_nonempty = float(dense_nonempty["close"].notna().mean() * 100.0) if not dense_nonempty.empty else 0.0

    audit = json.loads(names["audit_json"].read_text())
    audit["dense_minute_fill_pct_on_selected_contract_days"] = round(dense_fill_selected, 3)
    audit["dense_minute_fill_pct_on_nonempty_contract_days"] = round(dense_fill_nonempty, 3)
    audit["neighbor_filled_empty_contract_days"] = int(len(imputed_rows))
    names["audit_json"].write_text(json.dumps(audit, indent=2))

    report_path = output_dir / f"{underlying_prefix}_{args.tag}_neighbor_fill_report.csv"
    pd.DataFrame(imputed_rows).to_csv(report_path, index=False)
    print(
        json.dumps(
            {
                "underlying": args.underlying,
                "imputed_empty_contract_days": len(imputed_rows),
                "dense_fill_selected_pct": round(dense_fill_selected, 3),
                "dense_fill_nonempty_pct": round(dense_fill_nonempty, 3),
                "report": str(report_path),
            }
        )
    )


if __name__ == "__main__":
    main()
