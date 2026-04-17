from __future__ import annotations

import argparse
import json
import math
import os
import random
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import date, datetime, time as dtime, timedelta
from pathlib import Path
from typing import Any, Iterable

import pandas as pd
import requests
from zoneinfo import ZoneInfo


ET = ZoneInfo("America/New_York")
UTC = ZoneInfo("UTC")


def iso_z(dt: datetime) -> str:
    return dt.astimezone(UTC).isoformat().replace("+00:00", "Z")


def floor_dollar(value: float) -> float:
    return math.floor(value * 1000 + 0.5) / 1000


class RateLimiter:
    def __init__(self, requests_per_second: float) -> None:
        self.requests_per_second = requests_per_second
        self.lock = threading.Lock()
        self.next_allowed = time.monotonic()

    def wait(self) -> None:
        if self.requests_per_second <= 0:
            return
        with self.lock:
            now = time.monotonic()
            if now < self.next_allowed:
                time.sleep(self.next_allowed - now)
                now = time.monotonic()
            spacing = 1.0 / self.requests_per_second
            self.next_allowed = max(now, self.next_allowed) + spacing


@dataclass(frozen=True)
class ContractDay:
    trade_date: date
    symbol: str
    expiration_date: date
    dte: int
    option_type: str
    strike_price: float
    strike_step_distance: int
    spot_reference: float


class AlpacaClient:
    def __init__(
        self,
        api_key: str,
        api_secret: str,
        trading_base_url: str,
        rate_limiter: RateLimiter,
        timeout: int = 45,
        max_retries: int = 7,
    ) -> None:
        self.api_key = api_key
        self.api_secret = api_secret
        self.trading_base_url = trading_base_url.rstrip("/")
        self.data_base_url = "https://data.alpaca.markets"
        self.rate_limiter = rate_limiter
        self.timeout = timeout
        self.max_retries = max_retries
        self.session = requests.Session()
        self.session.headers.update(
            {
                "APCA-API-KEY-ID": self.api_key,
                "APCA-API-SECRET-KEY": self.api_secret,
                "Accept": "application/json",
            }
        )

    def _request(self, url: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        last_error: Exception | None = None
        for attempt in range(1, self.max_retries + 1):
            self.rate_limiter.wait()
            try:
                response = self.session.get(url, params=params, timeout=self.timeout)
            except requests.RequestException as exc:
                last_error = exc
                self._sleep_backoff(attempt, None)
                continue

            if response.status_code in (429, 500, 502, 503, 504):
                last_error = RuntimeError(
                    f"temporary HTTP {response.status_code} for {url}: {response.text[:500]}"
                )
                self._sleep_backoff(attempt, response)
                continue

            if response.status_code >= 400:
                raise RuntimeError(
                    f"HTTP {response.status_code} for {url} with params={params}: {response.text[:1200]}"
                )

            try:
                return response.json()
            except ValueError as exc:
                raise RuntimeError(f"invalid JSON from {url}: {response.text[:1000]}") from exc

        raise RuntimeError(f"request failed after retries for {url}: {last_error}")

    @staticmethod
    def _sleep_backoff(attempt: int, response: requests.Response | None) -> None:
        retry_after = None
        if response is not None:
            retry_after_header = response.headers.get("Retry-After")
            if retry_after_header:
                try:
                    retry_after = float(retry_after_header)
                except ValueError:
                    retry_after = None
        if retry_after is None:
            retry_after = min(30.0, (2 ** (attempt - 1)) * 0.5) + random.random() * 0.25
        time.sleep(retry_after)

    def fetch_calendar(self, start_date: date, end_date: date) -> list[dict[str, Any]]:
        url = f"{self.trading_base_url}/v2/calendar"
        payload = self._request(
            url,
            params={"start": start_date.isoformat(), "end": end_date.isoformat()},
        )
        if isinstance(payload, list):
            return payload
        raise RuntimeError(f"unexpected calendar payload: {payload}")

    def fetch_option_contracts(
        self,
        underlying_symbol: str,
        expiration_date_gte: date,
        expiration_date_lte: date,
        status: str,
    ) -> list[dict[str, Any]]:
        url = f"{self.trading_base_url}/v2/options/contracts"
        params: dict[str, Any] = {
            "underlying_symbols": underlying_symbol,
            "expiration_date_gte": expiration_date_gte.isoformat(),
            "expiration_date_lte": expiration_date_lte.isoformat(),
            "status": status,
            "limit": 1000,
        }
        contracts: list[dict[str, Any]] = []
        page_token: str | None = None
        while True:
            if page_token:
                params["page_token"] = page_token
            else:
                params.pop("page_token", None)
            payload = self._request(url, params=params)
            page_contracts = payload.get("option_contracts", [])
            if not isinstance(page_contracts, list):
                raise RuntimeError(f"unexpected option contracts payload: {payload}")
            contracts.extend(page_contracts)
            page_token = payload.get("next_page_token")
            if not page_token:
                break
        return contracts

    def fetch_stock_bars(
        self,
        symbol: str,
        start_dt: datetime,
        end_dt: datetime,
        feed: str,
    ) -> list[dict[str, Any]]:
        url = f"{self.data_base_url}/v2/stocks/bars"
        params: dict[str, Any] = {
            "symbols": symbol,
            "timeframe": "1Min",
            "start": iso_z(start_dt),
            "end": iso_z(end_dt),
            "limit": 10000,
            "sort": "asc",
            "feed": feed,
        }
        bars: list[dict[str, Any]] = []
        page_token: str | None = None
        while True:
            if page_token:
                params["page_token"] = page_token
            else:
                params.pop("page_token", None)
            payload = self._request(url, params=params)
            page_bars = payload.get("bars", {})
            symbol_bars = []
            if isinstance(page_bars, dict):
                symbol_bars = page_bars.get(symbol, [])
            elif isinstance(page_bars, list):
                symbol_bars = page_bars
            else:
                raise RuntimeError(f"unexpected stock bars payload: {payload}")
            for bar in symbol_bars:
                bar["S"] = symbol
            bars.extend(symbol_bars)
            page_token = payload.get("next_page_token")
            if not page_token:
                break
        return bars

    def fetch_option_bars_single_symbol(
        self,
        symbol: str,
        start_dt: datetime,
        end_dt: datetime,
    ) -> list[dict[str, Any]]:
        url = f"{self.data_base_url}/v1beta1/options/bars"
        params: dict[str, Any] = {
            "symbols": symbol,
            "timeframe": "1Min",
            "start": iso_z(start_dt),
            "end": iso_z(end_dt),
            "limit": 10000,
            "sort": "asc",
        }
        bars: list[dict[str, Any]] = []
        page_token: str | None = None
        while True:
            if page_token:
                params["page_token"] = page_token
            else:
                params.pop("page_token", None)
            payload = self._request(url, params=params)
            page_bars = payload.get("bars", {})
            symbol_bars = []
            if isinstance(page_bars, dict):
                symbol_bars = page_bars.get(symbol, [])
            elif isinstance(page_bars, list):
                symbol_bars = page_bars
            else:
                raise RuntimeError(f"unexpected option bars payload for {symbol}: {payload}")
            for bar in symbol_bars:
                bar["S"] = symbol
            bars.extend(symbol_bars)
            page_token = payload.get("next_page_token")
            if not page_token:
                break
        return bars


def get_env(name_candidates: Iterable[str]) -> str:
    for name in name_candidates:
        value = os.environ.get(name)
        if value:
            return value
    joined = ", ".join(name_candidates)
    raise RuntimeError(f"missing required environment variable; expected one of: {joined}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Download the last 30 days of QQQ 1-minute options data for 0-7 DTE and +/-5 strike steps around ATM."
    )
    parser.add_argument("--underlying", default="QQQ")
    parser.add_argument("--lookback-days", type=int, default=30)
    parser.add_argument("--max-dte", type=int, default=7)
    parser.add_argument("--strike-steps", type=int, default=5)
    parser.add_argument("--output-dir", default="output")
    parser.add_argument("--stock-feed-order", default="sip,delayed_sip,iex")
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--requests-per-second", type=float, default=2.5)
    parser.add_argument("--max-contract-days", type=int, default=0)
    parser.add_argument("--today", default="")
    return parser


def resolve_today(raw_today: str) -> date:
    if raw_today:
        return date.fromisoformat(raw_today)
    return datetime.now(ET).date()


def local_market_window(trade_date: date) -> tuple[datetime, datetime]:
    start_dt = datetime.combine(trade_date, dtime(9, 30), ET)
    end_dt = datetime.combine(trade_date, dtime(16, 0), ET)
    return start_dt, end_dt


def bars_to_frame(records: list[dict[str, Any]]) -> pd.DataFrame:
    if not records:
        return pd.DataFrame(
            columns=["symbol", "timestamp", "open", "high", "low", "close", "volume", "trade_count", "vwap"]
        )
    rows = []
    for item in records:
        rows.append(
            {
                "symbol": item.get("S") or item.get("symbol"),
                "timestamp": pd.to_datetime(item.get("t"), utc=True),
                "open": item.get("o"),
                "high": item.get("h"),
                "low": item.get("l"),
                "close": item.get("c"),
                "volume": item.get("v"),
                "trade_count": item.get("n"),
                "vwap": item.get("vw"),
            }
        )
    frame = pd.DataFrame(rows)
    frame = frame.sort_values(["symbol", "timestamp"]).reset_index(drop=True)
    return frame


def contracts_to_frame(records: list[dict[str, Any]]) -> pd.DataFrame:
    if not records:
        return pd.DataFrame()
    frame = pd.DataFrame(records).copy()
    if "expiration_date" in frame.columns:
        frame["expiration_date"] = pd.to_datetime(frame["expiration_date"]).dt.date
    if "strike_price" in frame.columns:
        frame["strike_price"] = pd.to_numeric(frame["strike_price"])
    if "size" in frame.columns:
        frame["size"] = pd.to_numeric(frame["size"], errors="coerce")
    return frame


def select_stock_feed(
    client: AlpacaClient,
    symbol: str,
    start_dt: datetime,
    end_dt: datetime,
    feed_order: list[str],
) -> tuple[str, pd.DataFrame]:
    last_error: Exception | None = None
    for feed in feed_order:
        try:
            bars = client.fetch_stock_bars(symbol, start_dt, end_dt, feed=feed)
            frame = bars_to_frame(bars)
            if not frame.empty:
                return feed, frame
        except Exception as exc:
            last_error = exc
    raise RuntimeError(f"unable to fetch underlying bars for {symbol}: {last_error}")


def build_spot_reference_map(underlying_bars: pd.DataFrame) -> dict[date, float]:
    if underlying_bars.empty:
        raise RuntimeError("underlying bars are empty")
    frame = underlying_bars.copy()
    frame["trade_date"] = frame["timestamp"].dt.tz_convert(ET).dt.date
    frame["time_et"] = frame["timestamp"].dt.tz_convert(ET).dt.time
    frame = frame.sort_values(["trade_date", "timestamp"])
    first_bars = frame.groupby("trade_date", as_index=False).first()
    spot_map = {
        row.trade_date: floor_dollar(float(row.open if pd.notna(row.open) else row.close))
        for row in first_bars.itertuples(index=False)
    }
    return spot_map


def choose_strike_window(strikes: list[float], spot: float, strike_steps: int) -> list[float]:
    unique_strikes = sorted({float(x) for x in strikes})
    if not unique_strikes:
        return []
    center_index = min(range(len(unique_strikes)), key=lambda idx: abs(unique_strikes[idx] - spot))
    start_index = max(0, center_index - strike_steps)
    end_index = min(len(unique_strikes), center_index + strike_steps + 1)
    return unique_strikes[start_index:end_index]


def build_contract_day_universe(
    contracts: pd.DataFrame,
    trading_dates: list[date],
    spot_map: dict[date, float],
    max_dte: int,
    strike_steps: int,
    underlying_symbol: str = "QQQ",
) -> pd.DataFrame:
    required = {"symbol", "expiration_date", "type", "strike_price"}
    missing = required - set(contracts.columns)
    if missing:
        raise RuntimeError(f"contracts frame is missing columns: {sorted(missing)}")

    frame = contracts.copy()
    if "root_symbol" in frame.columns:
        frame = frame[frame["root_symbol"] == underlying_symbol]
    if "size" in frame.columns:
        frame = frame[(frame["size"].isna()) | (frame["size"] == 100)]
    if "status" in frame.columns:
        frame = frame[frame["status"].isin(["active", "inactive"])]
    frame = frame.dropna(subset=["symbol", "expiration_date", "type", "strike_price"])
    frame = frame.drop_duplicates(subset=["symbol"])

    rows: list[dict[str, Any]] = []
    for trade_date in trading_dates:
        spot = spot_map.get(trade_date)
        if spot is None:
            continue
        expiry_cutoff = trade_date + timedelta(days=max_dte)
        eligible = frame[
            (frame["expiration_date"] >= trade_date) & (frame["expiration_date"] <= expiry_cutoff)
        ].copy()
        if eligible.empty:
            continue

        expiries = sorted(set(eligible["expiration_date"]))
        for expiry in expiries:
            expiry_slice = eligible[eligible["expiration_date"] == expiry].copy()
            selected_strikes = choose_strike_window(
                expiry_slice["strike_price"].tolist(),
                spot=spot,
                strike_steps=strike_steps,
            )
            if not selected_strikes:
                continue
            for option_type in ("call", "put"):
                typed = expiry_slice[expiry_slice["type"] == option_type].copy()
                if typed.empty:
                    continue
                typed["strike_distance"] = (typed["strike_price"] - spot).abs()
                typed = typed.sort_values(["strike_distance", "symbol"])
                for strike in selected_strikes:
                    exact = typed[typed["strike_price"] == strike].copy()
                    if exact.empty:
                        continue
                    chosen = exact.iloc[0]
                    rows.append(
                        {
                            "trade_date": trade_date,
                            "symbol": chosen["symbol"],
                            "expiration_date": chosen["expiration_date"],
                            "dte": (chosen["expiration_date"] - trade_date).days,
                            "option_type": option_type,
                            "strike_price": float(chosen["strike_price"]),
                            "spot_reference": float(spot),
                            "strike_step_distance": selected_strikes.index(strike)
                            - min(range(len(selected_strikes)), key=lambda i: abs(selected_strikes[i] - spot)),
                        }
                    )

    universe = pd.DataFrame(rows)
    if universe.empty:
        raise RuntimeError("daily option universe selection returned no contracts")
    universe = universe.drop_duplicates(subset=["trade_date", "symbol"]).sort_values(
        ["trade_date", "expiration_date", "option_type", "strike_price", "symbol"]
    )
    return universe.reset_index(drop=True)


def build_dense_panel(option_bars: pd.DataFrame, manifest: pd.DataFrame) -> pd.DataFrame:
    minute_cache: dict[date, pd.DatetimeIndex] = {}
    raw_groups: dict[tuple[str, str], pd.DataFrame] = {}
    if not option_bars.empty:
        for (trade_date, symbol), group in option_bars.groupby(["trade_date", "symbol"], sort=False):
            raw_groups[(str(trade_date), symbol)] = group.copy()

    dense_frames: list[pd.DataFrame] = []
    manifest_ok = manifest[manifest["status"] == "ok"].copy()
    for row in manifest_ok.itertuples(index=False):
        trade_date = date.fromisoformat(str(row.trade_date))
        session_minutes = minute_cache.get(trade_date)
        if session_minutes is None:
            session_start = datetime.combine(trade_date, dtime(9, 30), ET)
            session_minutes = pd.date_range(start=session_start, periods=390, freq="min", tz=ET)
            minute_cache[trade_date] = session_minutes

        dense = pd.DataFrame({"timestamp_et": session_minutes})
        dense["trade_date"] = trade_date
        dense["symbol"] = row.symbol
        dense["expiration_date"] = date.fromisoformat(str(row.expiration_date))
        dense["dte"] = int(row.dte)
        dense["option_type"] = row.option_type
        dense["strike_price"] = float(row.strike_price)
        dense["strike_step_distance"] = int(row.strike_step_distance)
        dense["spot_reference"] = float(row.spot_reference)

        observed = raw_groups.get((str(row.trade_date), row.symbol))
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
        dense["has_trade_bar"] = dense["has_trade_bar"].infer_objects(copy=False).fillna(False).astype(bool)

        reference_close = dense["close"].ffill().bfill()
        reference_vwap = dense["vwap"].ffill()
        reference_vwap = reference_vwap.fillna(reference_close)
        for price_col in ["open", "high", "low", "close"]:
            dense[price_col] = dense[price_col].fillna(reference_close)
        dense["vwap"] = dense["vwap"].fillna(reference_vwap)
        dense["volume"] = dense["volume"].fillna(0)
        dense["trade_count"] = dense["trade_count"].fillna(0)
        dense["is_synthetic_bar"] = (~dense["has_trade_bar"]) & dense["close"].notna()
        dense["session_has_any_trade"] = True
        dense_frames.append(dense)

    if not dense_frames:
        return pd.DataFrame()

    dense_panel = pd.concat(dense_frames, ignore_index=True)
    dense_panel = dense_panel.sort_values(["trade_date", "symbol", "timestamp_et"]).reset_index(drop=True)
    return dense_panel


def fetch_one_contract_day(
    client: AlpacaClient,
    contract_day: ContractDay,
) -> tuple[ContractDay, pd.DataFrame, dict[str, Any]]:
    start_dt, end_dt = local_market_window(contract_day.trade_date)
    t0 = time.time()
    bars = client.fetch_option_bars_single_symbol(contract_day.symbol, start_dt, end_dt)
    frame = bars_to_frame(bars)
    elapsed = round(time.time() - t0, 3)

    if not frame.empty:
        frame["timestamp_et"] = frame["timestamp"].dt.tz_convert(ET)
        frame = frame[
            (frame["timestamp_et"].dt.date == contract_day.trade_date)
            & (frame["timestamp_et"].dt.time >= dtime(9, 30))
            & (frame["timestamp_et"].dt.time < dtime(16, 0))
        ].copy()
        frame["trade_date"] = contract_day.trade_date
        frame["expiration_date"] = contract_day.expiration_date
        frame["dte"] = contract_day.dte
        frame["option_type"] = contract_day.option_type
        frame["strike_price"] = contract_day.strike_price
        frame["strike_step_distance"] = contract_day.strike_step_distance
        frame["spot_reference"] = contract_day.spot_reference

    manifest_row = {
        "trade_date": contract_day.trade_date.isoformat(),
        "symbol": contract_day.symbol,
        "expiration_date": contract_day.expiration_date.isoformat(),
        "dte": contract_day.dte,
        "option_type": contract_day.option_type,
        "strike_price": contract_day.strike_price,
        "strike_step_distance": contract_day.strike_step_distance,
        "spot_reference": contract_day.spot_reference,
        "bar_count": int(len(frame)),
        "elapsed_seconds": elapsed,
        "status": "ok",
    }
    return contract_day, frame, manifest_row


def main() -> None:
    args = build_parser().parse_args()
    today = resolve_today(args.today)
    start_date = today - timedelta(days=args.lookback_days)
    end_date = today
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    api_key = get_env(["ALPACA_API_KEY", "APCA_API_KEY_ID"])
    api_secret = get_env(["ALPACA_SECRET_KEY", "APCA_API_SECRET_KEY"])
    trading_base_url = os.environ.get("ALPACA_API_BASE_URL", "https://paper-api.alpaca.markets")

    rate_limiter = RateLimiter(args.requests_per_second)
    client = AlpacaClient(
        api_key=api_key,
        api_secret=api_secret,
        trading_base_url=trading_base_url,
        rate_limiter=rate_limiter,
    )

    print(
        json.dumps(
            {
                "phase": "calendar",
                "underlying": args.underlying,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            }
        )
    )
    calendar = client.fetch_calendar(start_date, end_date)
    trading_dates = [date.fromisoformat(item["date"]) for item in calendar]
    if not trading_dates:
        raise RuntimeError("no trading dates returned for the requested window")

    print(json.dumps({"phase": "underlying", "trading_days": len(trading_dates)}))
    first_window_start, _ = local_market_window(trading_dates[0])
    _, last_window_end = local_market_window(trading_dates[-1])
    feed_order = [feed.strip() for feed in args.stock_feed_order.split(",") if feed.strip()]
    stock_feed, underlying_bars = select_stock_feed(
        client=client,
        symbol=args.underlying,
        start_dt=first_window_start,
        end_dt=last_window_end,
        feed_order=feed_order,
    )
    if underlying_bars.empty:
        raise RuntimeError("underlying bars request returned no data")
    spot_map = build_spot_reference_map(underlying_bars)
    underlying_bars.to_parquet(output_dir / "qqq_underlying_1min.parquet", index=False)

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
    if all_contracts.empty:
        raise RuntimeError("no QQQ option contracts were returned")
    all_contracts.to_parquet(output_dir / "qqq_option_contracts.parquet", index=False)

    print(
        json.dumps(
            {
                "phase": "universe",
                "contracts_active": int(len(active_contracts)),
                "contracts_inactive": int(len(inactive_contracts)),
                "contracts_total": int(len(all_contracts)),
                "stock_feed": stock_feed,
            }
        )
    )
    contract_day_universe = build_contract_day_universe(
        contracts=all_contracts,
        trading_dates=trading_dates,
        spot_map=spot_map,
        max_dte=args.max_dte,
        strike_steps=args.strike_steps,
        underlying_symbol=args.underlying,
    )
    if args.max_contract_days > 0:
        contract_day_universe = contract_day_universe.head(args.max_contract_days).copy()
    contract_day_universe.to_parquet(output_dir / "qqq_option_daily_universe.parquet", index=False)

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
        for row in contract_day_universe.itertuples(index=False)
    ]

    print(
        json.dumps(
            {
                "phase": "download",
                "contract_days": len(contract_days),
                "workers": args.workers,
                "requests_per_second": args.requests_per_second,
            }
        )
    )
    all_bar_frames: list[pd.DataFrame] = []
    manifest_rows: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []

    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {
            executor.submit(fetch_one_contract_day, client, contract_day): contract_day for contract_day in contract_days
        }
        completed = 0
        for future in as_completed(futures):
            contract_day = futures[future]
            completed += 1
            try:
                _, frame, manifest_row = future.result()
                manifest_rows.append(manifest_row)
                if not frame.empty:
                    all_bar_frames.append(frame)
            except Exception as exc:
                failures.append(
                    {
                        "trade_date": contract_day.trade_date.isoformat(),
                        "symbol": contract_day.symbol,
                        "error": str(exc),
                    }
                )
                manifest_rows.append(
                    {
                        "trade_date": contract_day.trade_date.isoformat(),
                        "symbol": contract_day.symbol,
                        "expiration_date": contract_day.expiration_date.isoformat(),
                        "dte": contract_day.dte,
                        "option_type": contract_day.option_type,
                        "strike_price": contract_day.strike_price,
                        "strike_step_distance": contract_day.strike_step_distance,
                        "spot_reference": contract_day.spot_reference,
                        "bar_count": 0,
                        "elapsed_seconds": None,
                        "status": "error",
                        "error": str(exc),
                    }
                )
            if completed % 100 == 0 or completed == len(contract_days):
                print(json.dumps({"phase": "progress", "completed": completed, "total": len(contract_days)}))

    if failures:
        retry_failures: list[dict[str, Any]] = []
        for failure in failures:
            trade_date = date.fromisoformat(failure["trade_date"])
            matching = next(
                item for item in contract_days if item.trade_date == trade_date and item.symbol == failure["symbol"]
            )
            try:
                _, frame, manifest_row = fetch_one_contract_day(client, matching)
                manifest_rows = [
                    row
                    for row in manifest_rows
                    if not (row["trade_date"] == failure["trade_date"] and row["symbol"] == failure["symbol"])
                ]
                manifest_rows.append(manifest_row)
                if not frame.empty:
                    all_bar_frames.append(frame)
            except Exception as exc:
                retry_failures.append({**failure, "retry_error": str(exc)})
        failures = retry_failures

    manifest = pd.DataFrame(manifest_rows).sort_values(["trade_date", "symbol"]).reset_index(drop=True)
    manifest.to_csv(output_dir / "fetch_manifest.csv", index=False)

    if failures:
        failure_path = output_dir / "failures.json"
        failure_path.write_text(json.dumps(failures, indent=2))
        raise RuntimeError(
            f"{len(failures)} contract-day requests still failed after a second pass. See {failure_path}."
        )

    if all_bar_frames:
        option_bars = pd.concat(all_bar_frames, ignore_index=True)
        option_bars = option_bars.sort_values(["trade_date", "symbol", "timestamp"]).reset_index(drop=True)
    else:
        option_bars = pd.DataFrame()
    option_bars.to_parquet(output_dir / "qqq_option_1min_bars.parquet", index=False)
    dense_panel = build_dense_panel(option_bars=option_bars, manifest=manifest)
    dense_panel.to_parquet(output_dir / "qqq_option_1min_dense.parquet", index=False)

    nonempty_days = int((manifest["bar_count"] > 0).sum())
    minute_fill_nonempty = 0.0
    minute_fill_selected = 0.0
    dense_minute_fill_selected = 0.0
    dense_minute_fill_nonempty = 0.0
    if len(manifest) > 0:
        minute_fill_selected = float(manifest["bar_count"].sum()) / float(len(manifest) * 390) * 100.0
        if not dense_panel.empty:
            dense_minute_fill_selected = float(dense_panel["close"].notna().mean() * 100.0)
    if nonempty_days > 0:
        minute_fill_nonempty = float(manifest.loc[manifest["bar_count"] > 0, "bar_count"].sum()) / float(
            nonempty_days * 390
        ) * 100.0
        if not dense_panel.empty:
            dense_nonempty = dense_panel[dense_panel["session_has_any_trade"] == True]
            if not dense_nonempty.empty:
                dense_minute_fill_nonempty = float(dense_nonempty["close"].notna().mean() * 100.0)
    audit = {
        "underlying": args.underlying,
        "window_start": start_date.isoformat(),
        "window_end": end_date.isoformat(),
        "trading_days": len(trading_dates),
        "stock_feed_used": stock_feed,
        "selected_contract_days": int(len(manifest)),
        "unique_contracts": int(manifest["symbol"].nunique()),
        "bar_rows_downloaded": int(len(option_bars)),
        "successful_contract_day_requests": int((manifest["status"] == "ok").sum()),
        "failed_contract_day_requests": int((manifest["status"] != "ok").sum()),
        "request_fill_rate": round(float((manifest["status"] == "ok").mean() * 100.0), 3),
        "nonempty_contract_day_ratio": round(float((manifest["bar_count"] > 0).mean() * 100.0), 3),
        "empty_contract_day_ratio": round(float((manifest["bar_count"] == 0).mean() * 100.0), 3),
        "nonempty_contract_days": nonempty_days,
        "minute_fill_pct_on_selected_contract_days": round(minute_fill_selected, 3),
        "minute_fill_pct_on_nonempty_contract_days": round(minute_fill_nonempty, 3),
        "dense_minute_fill_pct_on_selected_contract_days": round(dense_minute_fill_selected, 3),
        "dense_minute_fill_pct_on_nonempty_contract_days": round(dense_minute_fill_nonempty, 3),
    }
    (output_dir / "audit_report.json").write_text(json.dumps(audit, indent=2))
    print(json.dumps({"phase": "done", **audit}))


if __name__ == "__main__":
    main()
