from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
from uuid import uuid4

import pandas as pd
import requests


ROOT = Path(r"C:\Users\rabisaab\Downloads")
TOURNAMENT_ROOT = ROOT / "equity_strategy_tournament"
if str(TOURNAMENT_ROOT) not in sys.path:
    sys.path.insert(0, str(TOURNAMENT_ROOT))

from tournament.options.selectors import select_contracts
from tournament.options.signals import generate_signals


PAPER_BASE_URL = "https://paper-api.alpaca.markets"
DATA_BASE_URL = "https://data.alpaca.markets"
PROMOTION_TABLE_PATH = TOURNAMENT_ROOT / "outputs" / "paper_promotions" / "promotion_table.csv"
PROMOTED_STATUS = "promoted_now"
SHADOW_STATUSES = {"shadow_only"}
RUN_PRIORITY = [
    "options_recent_otm_focus",
    "options_optimization",
]
RUN_UNIVERSE_RULES = {
    "options_recent_otm_focus": {"dte_min": 2, "dte_max": 2, "strike_window": 3, "min_volume": 20, "min_open_interest": 0},
    "options_optimization": {"dte_min": 0, "dte_max": 3, "strike_window": 3, "min_volume": 20, "min_open_interest": 0},
}
RANGE_TIMEFRAMES = {
    "5min": {"rule": "5min", "range_cap": 0.0075, "vwap_cap": 0.0018, "ema_cap": 0.0012, "min_crosses": 2},
    "15min": {"rule": "15min", "range_cap": 0.0110, "vwap_cap": 0.0024, "ema_cap": 0.0018, "min_crosses": 2},
    "30min": {"rule": "30min", "range_cap": 0.0140, "vwap_cap": 0.0030, "ema_cap": 0.0025, "min_crosses": 1},
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run measured Alpaca paper-options scans and optionally submit guarded paper trades.")
    parser.add_argument("--symbols", nargs="*", default=["SPY", "QQQ"])
    parser.add_argument("--execute-single-leg", action="store_true", help="Submit live paper single-leg option orders for qualified candidates.")
    parser.add_argument("--execute-mleg", action="store_true", help="Submit live paper multi-leg debit spreads for qualified candidates.")
    parser.add_argument("--max-orders", type=int, default=1)
    parser.add_argument("--signal-staleness-minutes", type=int, default=5)
    parser.add_argument("--target-daily-pnl", type=float, default=200.0)
    return parser.parse_args()


def require_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def request_headers() -> dict[str, str]:
    return {
        "APCA-API-KEY-ID": require_env("APCA_API_KEY_ID"),
        "APCA-API-SECRET-KEY": require_env("APCA_API_SECRET_KEY"),
        "Content-Type": "application/json",
    }


def paper_get(path: str, params: dict[str, Any] | None = None) -> Any:
    response = requests.get(f"{PAPER_BASE_URL}{path}", headers=request_headers(), params=params, timeout=30)
    response.raise_for_status()
    return response.json()


def paper_post(path: str, payload: dict[str, Any]) -> Any:
    response = requests.post(f"{PAPER_BASE_URL}{path}", headers=request_headers(), json=payload, timeout=30)
    response.raise_for_status()
    return response.json()


def data_get(path: str, params: dict[str, Any]) -> Any:
    response = requests.get(f"{DATA_BASE_URL}{path}", headers=request_headers(), params=params, timeout=60)
    response.raise_for_status()
    return response.json()


def paper_get_optional_by_client_order_id(client_order_id: str) -> Any | None:
    response = requests.get(
        f"{PAPER_BASE_URL}/v2/orders:by_client_order_id",
        headers=request_headers(),
        params={"client_order_id": client_order_id},
        timeout=30,
    )
    if response.status_code == 404:
        return None
    response.raise_for_status()
    return response.json()


def slugify(value: str) -> str:
    clean = []
    for char in value.lower():
        clean.append(char if char.isalnum() else "_")
    slug = "".join(clean)
    while "__" in slug:
        slug = slug.replace("__", "_")
    return slug.strip("_")


def underlying_from_symbol(symbol: str) -> str:
    letters: list[str] = []
    for char in symbol:
        if char.isalpha():
            letters.append(char)
            continue
        break
    return "".join(letters) or symbol


def now_local() -> datetime:
    return datetime.now().astimezone()


def assert_paper_trading_env_safe(*, execution_requested: bool) -> None:
    configured_base = os.environ.get("APCA_API_BASE_URL", "").strip()
    if not configured_base:
        return
    normalized = configured_base.rstrip("/").lower()
    if "paper-api.alpaca.markets" in normalized:
        return
    if execution_requested:
        raise RuntimeError(
            f"APCA_API_BASE_URL points to a non-paper endpoint ({configured_base}). Refusing order submission."
        )


def _coerce_setup_numeric_columns(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return frame.copy()
    out = frame.copy()
    numeric_columns = [
        "days_tested",
        "trade_count",
        "total_pnl",
        "pnl_per_day",
        "expectancy",
        "max_drawdown",
        "positive_day_ratio",
        "daily_pnl_std",
        "drawdown_adjusted_return",
        "promotion_rank",
        "stressed_pnl_per_day",
        "stressed_expectancy",
    ]
    for column in numeric_columns:
        if column in out.columns:
            out[column] = pd.to_numeric(out[column], errors="coerce")
    return out


def _add_setup_labels(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return frame.copy()
    out = frame.copy()
    out["setup_label"] = (
        out["source_run"].astype(str)
        + " | "
        + out["symbol"].astype(str)
        + " | "
        + out["strategy_name"].astype(str)
        + " | "
        + out["contract_target"].astype(str)
    )
    return out


def load_promotion_setups(symbols: list[str], statuses: set[str]) -> pd.DataFrame:
    if not PROMOTION_TABLE_PATH.exists():
        return pd.DataFrame()
    setups = pd.read_csv(PROMOTION_TABLE_PATH)
    setups = _coerce_setup_numeric_columns(setups)
    setups = setups.loc[
        setups["symbol"].isin(symbols)
        & (setups["deployment_target"] == "options_autopilot")
        & (setups["paper_status"].isin(statuses))
        & setups["template"].isin(["failed_breakout_mean_reversion", "lux_fair_value_gap", "opening_range_breakout", "vwap_reclaim_reject", "momentum_continuation"])
    ].copy()
    if setups.empty:
        return setups
    setups = _add_setup_labels(setups)
    setups = setups.sort_values(
        ["promotion_rank", "pnl_per_day", "drawdown_adjusted_return", "expectancy"],
        ascending=[True, False, False, False],
    )
    return setups.reset_index(drop=True)


def load_recommended_setups(symbols: list[str]) -> pd.DataFrame:
    promoted = load_promotion_setups(symbols, {PROMOTED_STATUS})
    if not promoted.empty:
        return promoted
    rows: list[pd.DataFrame] = []
    for run_name in RUN_PRIORITY:
        parameter_summary_path = TOURNAMENT_ROOT / "outputs" / run_name / "parameter_summary.csv"
        if not parameter_summary_path.exists():
            continue
        frame = pd.read_csv(parameter_summary_path)
        frame["source_run"] = run_name
        rows.append(frame)
    if not rows:
        return pd.DataFrame()
    setups = _coerce_setup_numeric_columns(pd.concat(rows, ignore_index=True))
    setups = setups.loc[
        setups["symbol"].isin(symbols)
        & (setups["trade_count"] >= 25)
        & (setups["pnl_per_day"] > 0)
        & (setups["expectancy"] > 0)
        & (setups["positive_day_ratio"] >= 0.45)
    ].copy()
    if setups.empty:
        return setups
    setups["run_priority"] = setups["source_run"].apply(lambda value: RUN_PRIORITY.index(value) if value in RUN_PRIORITY else 99)
    setups = _add_setup_labels(setups)
    setups = setups.sort_values(
        ["run_priority", "pnl_per_day", "drawdown_adjusted_return", "expectancy"],
        ascending=[True, False, False, False],
    )
    setups = setups.groupby("symbol", group_keys=False).head(1).reset_index(drop=True)
    return setups


def load_shadow_setups(symbols: list[str]) -> pd.DataFrame:
    return load_promotion_setups(symbols, SHADOW_STATUSES)


def fetch_intraday_bars(symbols: list[str]) -> pd.DataFrame:
    start_local = now_local().replace(hour=9, minute=30, second=0, microsecond=0)
    start_utc = start_local.astimezone(pd.Timestamp.utcnow().tz)
    end_utc = now_local().astimezone(pd.Timestamp.utcnow().tz)
    payload = data_get(
        "/v2/stocks/bars",
        {
            "symbols": ",".join(symbols),
            "timeframe": "1Min",
            "start": start_utc.isoformat().replace("+00:00", "Z"),
            "end": end_utc.isoformat().replace("+00:00", "Z"),
            "adjustment": "split",
            "feed": "sip",
            "limit": 10000,
            "sort": "asc",
        },
    )
    rows: list[dict[str, Any]] = []
    for symbol, bars in payload.get("bars", {}).items():
        for bar in bars:
            rows.append(
                {
                    "symbol": symbol,
                    "timestamp": pd.Timestamp(bar["t"]),
                    "open": bar["o"],
                    "high": bar["h"],
                    "low": bar["l"],
                    "close": bar["c"],
                    "volume": bar["v"],
                }
            )
    frame = pd.DataFrame(rows)
    if frame.empty:
        return frame
    frame["timestamp"] = pd.to_datetime(frame["timestamp"], utc=True)
    return frame.sort_values(["symbol", "timestamp"]).reset_index(drop=True)


def fetch_stock_quotes(symbols: list[str]) -> pd.DataFrame:
    payload = data_get("/v2/stocks/quotes/latest", {"symbols": ",".join(symbols), "feed": "sip"})
    rows: list[dict[str, Any]] = []
    for symbol, quote in payload.get("quotes", {}).items():
        rows.append(
            {
                "symbol": symbol,
                "underlying_bid": float(quote["bp"]),
                "underlying_ask": float(quote["ap"]),
                "underlying_quote_timestamp": pd.Timestamp(quote["t"]),
            }
        )
    return pd.DataFrame(rows)


def aggregate_symbol_bars(symbol_bars: pd.DataFrame, rule: str) -> pd.DataFrame:
    bars = symbol_bars.copy()
    if bars.empty:
        return bars
    bars = bars.sort_values("timestamp").reset_index(drop=True)
    bars["timestamp"] = pd.to_datetime(bars["timestamp"], utc=True)
    bars = bars.set_index("timestamp")
    aggregated = (
        bars.resample(rule, label="right", closed="right")
        .agg({"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"})
        .dropna(subset=["open", "high", "low", "close"])
        .reset_index()
    )
    return aggregated


def evaluate_range_regimes(intraday_bars: pd.DataFrame, symbols: list[str]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for symbol in symbols:
        symbol_bars = intraday_bars.loc[intraday_bars["symbol"] == symbol].copy()
        if symbol_bars.empty:
            continue
        for timeframe_name, config in RANGE_TIMEFRAMES.items():
            bars = aggregate_symbol_bars(symbol_bars, config["rule"])
            if len(bars) < 6:
                continue
            bars["ema8"] = bars["close"].ewm(span=8, adjust=False).mean()
            bars["ema21"] = bars["close"].ewm(span=21, adjust=False).mean()
            typical_price = (bars["high"] + bars["low"] + bars["close"]) / 3.0
            bars["cum_pv"] = (typical_price * bars["volume"]).cumsum()
            bars["cum_v"] = bars["volume"].cumsum().replace(0, pd.NA)
            bars["session_vwap"] = bars["cum_pv"] / bars["cum_v"]
            latest = bars.iloc[-1]
            session_high = float(bars["high"].max())
            session_low = float(bars["low"].min())
            last_close = float(latest["close"])
            realized_range_pct = (session_high - session_low) / max(last_close, 0.01)
            vwap_distance_pct = abs(last_close - float(latest["session_vwap"])) / max(last_close, 0.01)
            ema_spread_pct = abs(float(latest["ema8"]) - float(latest["ema21"])) / max(last_close, 0.01)
            vwap_sign = (bars["close"] >= bars["session_vwap"]).astype(int)
            vwap_crosses = int(vwap_sign.diff().abs().fillna(0).sum())
            score = 0
            score += int(realized_range_pct <= float(config["range_cap"]))
            score += int(vwap_distance_pct <= float(config["vwap_cap"]))
            score += int(ema_spread_pct <= float(config["ema_cap"]))
            score += int(vwap_crosses >= int(config["min_crosses"]))
            rows.append(
                {
                    "symbol": symbol,
                    "timeframe": timeframe_name,
                    "bar_count": int(len(bars)),
                    "session_high": session_high,
                    "session_low": session_low,
                    "last_close": last_close,
                    "session_vwap": float(latest["session_vwap"]),
                    "realized_range_pct": realized_range_pct,
                    "vwap_distance_pct": vwap_distance_pct,
                    "ema_spread_pct": ema_spread_pct,
                    "vwap_crosses": vwap_crosses,
                    "range_score": score,
                    "is_range_bound": score >= 3,
                }
            )
    return pd.DataFrame(rows)


def build_pyramid_plan(*, pnl_per_day: float, target_daily_pnl: float, max_total_scale: int = 4) -> dict[str, Any]:
    if pnl_per_day <= 0:
        return {
            "scale_needed": None,
            "recommended_total_scale": 1,
            "stage_sizes": [1],
            "notes": "No positive daily edge available, so pyramiding is not recommended.",
        }
    raw_scale = int(math.ceil(target_daily_pnl / pnl_per_day))
    total_scale = max(1, min(raw_scale, max_total_scale))
    remaining = total_scale
    stage_sizes: list[int] = []
    stage_template = [1, 1, 2]
    for size in stage_template:
        if remaining <= 0:
            break
        stage = min(size, remaining)
        stage_sizes.append(stage)
        remaining -= stage
    if remaining > 0:
        stage_sizes.append(remaining)
    notes = (
        "Stage 1 on initial fill. Stage 2 only if a fresh same-direction signal appears and the first tranche is in profit. "
        "Stage 3 only if unrealized PnL stays positive, the setup remains live, and it is still before 14:30 ET."
    )
    return {
        "scale_needed": raw_scale,
        "recommended_total_scale": total_scale,
        "stage_sizes": stage_sizes,
        "notes": notes,
    }


def build_client_order_id(prefix: str, row: pd.Series, structure: str) -> str:
    signal_timestamp = row.get("recent_signal_timestamp") or row.get("signal_timestamp") or ""
    seed = "|".join(
        [
            prefix,
            str(row.get("symbol", "")),
            str(row.get("setup_id", "")),
            str(row.get("strategy_name", "")),
            str(structure),
            str(row.get("contract_target", "")),
            str(row.get("signal_direction", "")),
            str(pd.Timestamp(signal_timestamp)) if signal_timestamp not in {"", None} and not pd.isna(signal_timestamp) else "",
            str(row.get("option_symbol", "")),
        ]
    )
    digest = hashlib.sha1(seed.encode("utf-8")).hexdigest()[:12]
    return f"codex-{prefix}-{slugify(str(row.get('symbol', 'na')))}-{digest}"[:48]


def risk_plan_details(risk_signature: str | float | None) -> dict[str, str]:
    if not risk_signature or (isinstance(risk_signature, float) and pd.isna(risk_signature)):
        return {
            "stop_plan": "",
            "target_plan": "",
            "time_stop_plan": "",
            "session_exit_plan": "",
        }
    risk = json.loads(str(risk_signature))
    stop = float(risk.get("initial_stop_loss_pct", 0.0))
    activation = float(risk.get("trailing_stop_activation_pct", 0.0))
    trail = float(risk.get("trailing_stop_distance_pct", 0.0))
    time_stop_minutes = int(risk.get("time_stop_minutes", 0) or 0)
    max_holding_minutes = int(risk.get("max_holding_minutes", 0) or 0)
    use_take_profit = bool(risk.get("use_take_profit", False))
    take_profit_pct = float(risk.get("take_profit_pct", 0.0) or 0.0)
    target_plan = (
        f"Fixed take profit at +{take_profit_pct:.0%}."
        if use_take_profit and take_profit_pct > 0
        else f"Trail armed after +{activation:.0%} with {trail:.0%} giveback."
    )
    return {
        "stop_plan": f"Hard stop at -{stop:.0%}.",
        "target_plan": target_plan,
        "time_stop_plan": f"Time stop {time_stop_minutes}m; max hold {max_holding_minutes}m.",
        "session_exit_plan": "Mandatory end-of-day flat.",
    }


def build_pyramid_lookup(pyramid_plans: pd.DataFrame) -> dict[tuple[str, str, str], dict[str, str]]:
    lookup: dict[tuple[str, str, str], dict[str, str]] = {}
    if pyramid_plans.empty:
        return lookup
    for row in pyramid_plans.to_dict(orient="records"):
        lookup[(str(row["symbol"]), str(row["strategy_name"]), str(row["source_run"]))] = {
            "stage_sizes": str(row.get("stage_sizes", "")),
            "notes": str(row.get("notes", "")),
        }
    return lookup


def build_entry_reason(row: pd.Series) -> str:
    direction = int(row.get("signal_direction", row.get("recent_signal_direction", 0)))
    signal_timestamp = row.get("recent_signal_timestamp") or row.get("signal_timestamp")
    signal_text = ""
    if signal_timestamp is not None and not pd.isna(signal_timestamp):
        signal_text = f" at {pd.Timestamp(signal_timestamp)}"
    return f"{row.get('template', 'signal')} direction={direction}{signal_text}"


def evaluate_live_signals(setups: pd.DataFrame, intraday_bars: pd.DataFrame, *, signal_staleness_minutes: int) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for row in setups.itertuples(index=False):
        bars = intraday_bars.loc[intraday_bars["symbol"] == row.symbol].copy()
        if bars.empty:
            continue
        parameters = json.loads(row.parameter_signature)
        signals = generate_signals(str(row.template), bars, parameters, "America/New_York")
        if signals.empty:
            continue
        latest = signals.iloc[-1]
        recent_cutoff = pd.Timestamp(latest["timestamp"]) - pd.Timedelta(minutes=signal_staleness_minutes)
        recent_signals = signals.loc[
            (signals["timestamp"] >= recent_cutoff)
            & (signals["signal_direction"] != 0)
        ].copy()
        recent_signal_direction = int(recent_signals.iloc[-1]["signal_direction"]) if not recent_signals.empty else 0
        recent_signal_timestamp = pd.Timestamp(recent_signals.iloc[-1]["timestamp"]) if not recent_signals.empty else pd.NaT
        universe = RUN_UNIVERSE_RULES.get(str(row.source_run), RUN_UNIVERSE_RULES["options_optimization"])
        rows.append(
            {
                "symbol": row.symbol,
                "source_run": row.source_run,
                "setup_id": row.setup_id,
                "strategy_name": row.strategy_name,
                "template": row.template,
                "contract_target": row.contract_target,
                "parameter_signature": row.parameter_signature,
                "risk_signature": row.risk_signature,
                "pnl_per_day": float(row.pnl_per_day),
                "expectancy": float(row.expectancy),
                "max_drawdown": float(row.max_drawdown),
                "positive_day_ratio": float(row.positive_day_ratio),
                "signal_direction": int(latest["signal_direction"]),
                "signal_timestamp": pd.Timestamp(latest["timestamp"]),
                "recent_signal_direction": recent_signal_direction,
                "recent_signal_timestamp": recent_signal_timestamp,
                "underlying_close": float(latest["close"]),
                "dte_min": int(universe["dte_min"]),
                "dte_max": int(universe["dte_max"]),
                "strike_window": int(universe["strike_window"]),
                "min_volume": int(universe["min_volume"]),
                "min_open_interest": int(universe["min_open_interest"]),
            }
        )
    return pd.DataFrame(rows)


def fetch_option_contracts(symbol: str, *, dte_min: int, dte_max: int) -> list[dict[str, Any]]:
    today = now_local().date()
    expiration_start = today + timedelta(days=dte_min)
    expiration_end = today + timedelta(days=dte_max)
    contracts: list[dict[str, Any]] = []
    page_token: str | None = None
    while True:
        params: dict[str, Any] = {
            "underlying_symbols": symbol,
            "expiration_date_gte": expiration_start.isoformat(),
            "expiration_date_lte": expiration_end.isoformat(),
            "status": "active",
            "limit": 1000,
        }
        if page_token:
            params["page_token"] = page_token
        payload = paper_get("/v2/options/contracts", params=params)
        contracts.extend(payload.get("option_contracts", []))
        page_token = payload.get("next_page_token")
        if not page_token:
            break
    return contracts


def chunked(items: list[str], chunk_size: int) -> list[list[str]]:
    return [items[index : index + chunk_size] for index in range(0, len(items), chunk_size)]


def fetch_option_snapshots(option_symbols: list[str]) -> dict[str, Any]:
    snapshots: dict[str, Any] = {}
    for batch in chunked(option_symbols, 50):
        payload = data_get("/v1beta1/options/snapshots", {"symbols": ",".join(batch), "feed": "opra"})
        snapshots.update(payload.get("snapshots", {}))
    return snapshots


def build_option_chain_frame(
    *,
    underlying_symbol: str,
    underlying_price: float,
    dte_min: int,
    dte_max: int,
) -> pd.DataFrame:
    contracts = fetch_option_contracts(underlying_symbol, dte_min=dte_min, dte_max=dte_max)
    if not contracts:
        return pd.DataFrame()
    strikes = sorted({float(contract["strike_price"]) for contract in contracts if contract.get("strike_price") is not None})
    if not strikes:
        return pd.DataFrame()
    nearest_index = min(range(len(strikes)), key=lambda index: abs(strikes[index] - underlying_price))
    strike_floor = strikes[max(0, nearest_index - 4)]
    strike_ceiling = strikes[min(len(strikes) - 1, nearest_index + 4)]
    filtered = [
        contract
        for contract in contracts
        if strike_floor <= float(contract["strike_price"]) <= strike_ceiling
    ]
    snapshots = fetch_option_snapshots([str(contract["symbol"]) for contract in filtered])
    rows: list[dict[str, Any]] = []
    today = now_local().date()
    for contract in filtered:
        symbol = str(contract["symbol"])
        snapshot = snapshots.get(symbol, {})
        quote = snapshot.get("latestQuote", {})
        minute_bar = snapshot.get("minuteBar", {})
        daily_bar = snapshot.get("dailyBar", {})
        latest_trade = snapshot.get("latestTrade", {})
        bid = float(quote.get("bp", 0.0) or 0.0)
        ask = float(quote.get("ap", 0.0) or 0.0)
        mark = 0.0
        if bid > 0 and ask > 0:
            mark = (bid + ask) / 2.0
        elif minute_bar.get("c") is not None:
            mark = float(minute_bar["c"])
        elif latest_trade.get("p") is not None:
            mark = float(latest_trade["p"])
        elif daily_bar.get("c") is not None:
            mark = float(daily_bar["c"])
        expiration_date = pd.Timestamp(contract["expiration_date"]).date()
        rows.append(
            {
                "option_symbol": symbol,
                "underlying_symbol": underlying_symbol,
                "expiration": pd.Timestamp(contract["expiration_date"]),
                "option_type": str(contract["type"]).lower(),
                "strike": float(contract["strike_price"]),
                "dte": int((expiration_date - today).days),
                "close": mark,
                "volume": int(daily_bar.get("v", 0) or 0),
                "open_interest": int(contract.get("open_interest") or 0),
                "multiplier": int(contract.get("multiplier") or 100),
                "bid_price": bid,
                "ask_price": ask,
                "spread_bps": (((ask - bid) / ((ask + bid) / 2.0)) * 10000.0) if bid > 0 and ask > 0 else float("inf"),
                "quote_timestamp": pd.Timestamp(quote["t"]) if quote.get("t") else pd.NaT,
                "mark_price": mark,
                "daily_volume": int(daily_bar.get("v", 0) or 0),
            }
        )
    return pd.DataFrame(rows)


def choose_single_leg_candidate(signal_row: pd.Series, chain: pd.DataFrame) -> pd.Series | None:
    if chain.empty:
        return None
    selected, _ = select_contracts(
        chain,
        underlying_price=float(signal_row["underlying_close"]),
        direction=int(signal_row["signal_direction"]),
        allowed_sides=["call", "put"],
        target_mode=str(signal_row["contract_target"]),
        dte_min=int(signal_row["dte_min"]),
        dte_max=int(signal_row["dte_max"]),
        strike_window=int(signal_row["strike_window"]),
        min_volume=int(signal_row["min_volume"]),
        min_open_interest=int(signal_row["min_open_interest"]),
    )
    if selected.empty:
        return None
    selected = selected.sort_values(["spread_bps", "daily_volume", "dte"], ascending=[True, False, True]).reset_index(drop=True)
    return selected.iloc[0]


def choose_vertical_spread(signal_row: pd.Series, long_leg: pd.Series, chain: pd.DataFrame) -> dict[str, Any] | None:
    expiry = pd.Timestamp(long_leg["expiration"])
    option_type = str(long_leg["option_type"])
    candidates = chain.loc[(chain["expiration"] == expiry) & (chain["option_type"] == option_type)].copy()
    if candidates.empty:
        return None
    if option_type == "call":
        short_candidates = candidates.loc[candidates["strike"] > float(long_leg["strike"])].sort_values("strike")
    else:
        short_candidates = candidates.loc[candidates["strike"] < float(long_leg["strike"])].sort_values("strike", ascending=False)
    short_candidates = short_candidates.loc[
        (short_candidates["bid_price"] > 0)
        & (short_candidates["ask_price"] > 0)
        & (short_candidates["spread_bps"] <= 400.0)
    ]
    if short_candidates.empty:
        return None
    short_leg = short_candidates.iloc[0]
    net_debit = max(0.01, float(long_leg["ask_price"]) - float(short_leg["bid_price"]))
    if net_debit <= 0:
        return None
    structure = "bull_call_spread" if int(signal_row["signal_direction"]) > 0 else "bear_put_spread"
    return {
        "structure": structure,
        "long_leg_symbol": str(long_leg["option_symbol"]),
        "short_leg_symbol": str(short_leg["option_symbol"]),
        "expiration": str(expiry.date()),
        "net_debit_estimate": round(net_debit, 2),
        "long_strike": float(long_leg["strike"]),
        "short_strike": float(short_leg["strike"]),
    }


def choose_iron_condor_candidate(symbol: str, chain: pd.DataFrame, regime_row: pd.Series) -> dict[str, Any] | None:
    if chain.empty:
        return None
    chain = chain.loc[(chain["bid_price"] > 0) & (chain["ask_price"] > 0)].copy()
    if chain.empty:
        return None
    underlying_price = float(regime_row["last_close"])
    shorts, _ = select_contracts(
        chain,
        underlying_price=underlying_price,
        direction=1,
        allowed_sides=["call", "put"],
        target_mode="symmetric_otm_1",
        dte_min=2,
        dte_max=2,
        strike_window=3,
        min_volume=5,
        min_open_interest=0,
    )
    if shorts.empty or len(shorts) < 2:
        return None
    expiry = pd.Timestamp(shorts.iloc[0]["expiration"])
    same_expiry = chain.loc[chain["expiration"] == expiry].copy()
    longs, _ = select_contracts(
        same_expiry,
        underlying_price=underlying_price,
        direction=1,
        allowed_sides=["call", "put"],
        target_mode="symmetric_otm_2",
        dte_min=2,
        dte_max=2,
        strike_window=3,
        min_volume=5,
        min_open_interest=0,
    )
    if longs.empty or len(longs) < 2:
        return None
    short_call = shorts.loc[shorts["option_type"] == "call"]
    short_put = shorts.loc[shorts["option_type"] == "put"]
    long_call = longs.loc[longs["option_type"] == "call"]
    long_put = longs.loc[longs["option_type"] == "put"]
    if short_call.empty or short_put.empty or long_call.empty or long_put.empty:
        return None
    short_call_leg = short_call.sort_values("strike").iloc[0]
    short_put_leg = short_put.sort_values("strike", ascending=False).iloc[0]
    long_call_leg = long_call.sort_values("strike").iloc[0]
    long_put_leg = long_put.sort_values("strike", ascending=False).iloc[0]
    call_width = float(long_call_leg["strike"]) - float(short_call_leg["strike"])
    put_width = float(short_put_leg["strike"]) - float(long_put_leg["strike"])
    if call_width <= 0 or put_width <= 0:
        return None
    net_credit = (
        float(short_call_leg["bid_price"])
        + float(short_put_leg["bid_price"])
        - float(long_call_leg["ask_price"])
        - float(long_put_leg["ask_price"])
    )
    if net_credit <= 0.05:
        return None
    width_dollars = max(call_width, put_width) * 100.0
    max_loss = width_dollars - net_credit * 100.0
    average_spread_bps = float(
        pd.Series(
            [
                short_call_leg["spread_bps"],
                short_put_leg["spread_bps"],
                long_call_leg["spread_bps"],
                long_put_leg["spread_bps"],
            ]
        ).replace([pd.NA, float("inf")], pd.NA).dropna().mean()
    )
    return {
        "symbol": symbol,
        "timeframe": str(regime_row["timeframe"]),
        "range_score": int(regime_row["range_score"]),
        "structure": "iron_condor",
        "expiration": str(expiry.date()),
        "short_call_symbol": str(short_call_leg["option_symbol"]),
        "long_call_symbol": str(long_call_leg["option_symbol"]),
        "short_put_symbol": str(short_put_leg["option_symbol"]),
        "long_put_symbol": str(long_put_leg["option_symbol"]),
        "short_call_strike": float(short_call_leg["strike"]),
        "long_call_strike": float(long_call_leg["strike"]),
        "short_put_strike": float(short_put_leg["strike"]),
        "long_put_strike": float(long_put_leg["strike"]),
        "net_credit_estimate": round(net_credit, 2),
        "max_loss_estimate": round(max_loss, 2),
        "reward_risk_ratio": round((net_credit * 100.0) / max(max_loss, 0.01), 3),
        "breakeven_low": round(float(short_put_leg["strike"]) - net_credit, 2),
        "breakeven_high": round(float(short_call_leg["strike"]) + net_credit, 2),
        "average_spread_bps": round(average_spread_bps, 1) if not math.isnan(average_spread_bps) else float("inf"),
    }


def size_single_leg(account: dict[str, Any], contract: pd.Series) -> dict[str, Any] | None:
    ask = float(contract["ask_price"])
    bid = float(contract["bid_price"])
    if ask <= 0:
        return None
    premium_cap = min(float(account.get("equity", 0.0)) * 0.0015, 150.0)
    contracts_affordable = math.floor(premium_cap / max(ask * 100.0, 1.0))
    qty = min(1, contracts_affordable)
    if qty < 1:
        return None
    chase_buffer = max(0.02, (ask - bid) * 0.25)
    limit_price = round(ask + chase_buffer, 2)
    return {
        "qty": qty,
        "limit_price": limit_price,
        "premium_cap_usd": round(premium_cap, 2),
    }


def size_condor(account: dict[str, Any], condor: pd.Series) -> dict[str, Any] | None:
    max_risk = float(condor["max_loss_estimate"])
    if max_risk <= 0:
        return None
    risk_cap = min(float(account.get("equity", 0.0)) * 0.0020, 200.0)
    qty = math.floor(risk_cap / max_risk)
    qty = min(1, qty)
    if qty < 1:
        return None
    limit_price = round(float(condor["net_credit_estimate"]), 2)
    return {
        "qty": qty,
        "limit_price": limit_price,
        "risk_cap_usd": round(risk_cap, 2),
    }


def build_single_leg_order_payload(contract_symbol: str, qty: int, limit_price: float, client_order_id: str) -> dict[str, Any]:
    return {
        "symbol": contract_symbol,
        "qty": str(qty),
        "side": "buy",
        "type": "limit",
        "limit_price": f"{limit_price:.2f}",
        "time_in_force": "day",
        "client_order_id": client_order_id,
    }


def build_mleg_order_payload(*, long_leg_symbol: str, short_leg_symbol: str, qty: int, limit_price: float, option_type: str) -> dict[str, Any]:
    return {
        "order_class": "mleg",
        "qty": str(qty),
        "type": "limit",
        "limit_price": f"{limit_price:.2f}",
        "time_in_force": "day",
        "legs": [
            {
                "symbol": long_leg_symbol,
                "ratio_qty": "1",
                "side": "buy",
                "position_intent": "buy_to_open",
            },
            {
                "symbol": short_leg_symbol,
                "ratio_qty": "1",
                "side": "sell",
                "position_intent": "sell_to_open",
            },
        ],
    }


def build_condor_order_payload(
    *,
    long_put_symbol: str,
    short_put_symbol: str,
    short_call_symbol: str,
    long_call_symbol: str,
    qty: int,
    limit_price: float,
) -> dict[str, Any]:
    return {
        "order_class": "mleg",
        "qty": str(qty),
        "type": "limit",
        "limit_price": f"{limit_price:.2f}",
        "time_in_force": "day",
        "legs": [
            {
                "symbol": long_put_symbol,
                "ratio_qty": "1",
                "side": "buy",
                "position_intent": "buy_to_open",
            },
            {
                "symbol": short_put_symbol,
                "ratio_qty": "1",
                "side": "sell",
                "position_intent": "sell_to_open",
            },
            {
                "symbol": short_call_symbol,
                "ratio_qty": "1",
                "side": "sell",
                "position_intent": "sell_to_open",
            },
            {
                "symbol": long_call_symbol,
                "ratio_qty": "1",
                "side": "buy",
                "position_intent": "buy_to_open",
            },
        ],
    }


def submit_order(payload: dict[str, Any]) -> dict[str, Any]:
    order = paper_post("/v2/orders", payload)
    order_id = order["id"]
    latest = order
    for _ in range(6):
        time.sleep(2)
        latest = paper_get(f"/v2/orders/{order_id}")
        if str(latest.get("status", "")).lower() in {"new", "accepted", "filled", "partially_filled"}:
            break
    latest["submitted_payload"] = payload
    return latest


def build_exit_plan_text(risk_signature: str) -> str:
    details = risk_plan_details(risk_signature)
    return (
        f"{details['stop_plan']} {details['target_plan']} {details['time_stop_plan']} {details['session_exit_plan']}".strip()
    )


def build_condor_exit_plan_text(condor: pd.Series) -> str:
    return (
        f"Range thesis on {condor['timeframe']}. Exit near 50% credit capture, on break of "
        f"{condor['breakeven_low']}/{condor['breakeven_high']}, or end-of-day review if the range breaks."
    )


def write_trade_log(output_dir: Path, orders: list[dict[str, Any]]) -> None:
    columns = [
        "timestamp",
        "underlying_symbol",
        "option_symbol",
        "structure",
        "strategy_name",
        "strategy_signature",
        "source_run",
        "paper_status",
        "template",
        "regime_tag",
        "order_type",
        "entry_reason",
        "signal_timestamp",
        "parameter_signature",
        "risk_signature",
        "status",
        "order_id",
        "client_order_id",
        "qty",
        "entry_limit_price",
        "entry_filled_price",
        "stop_plan",
        "target_plan",
        "time_stop_plan",
        "session_exit_plan",
        "pyramid_plan",
        "exit_price",
        "exit_reason",
        "pnl",
        "mfe",
        "mae",
    ]
    rows: list[dict[str, Any]] = []
    for order in orders:
        rows.append(
            {
                "timestamp": now_local().isoformat(),
                "underlying_symbol": order["underlying_symbol"],
                "option_symbol": order.get("option_symbol") or order.get("long_leg_symbol", ""),
                "structure": order["structure"],
                "strategy_name": order["strategy_name"],
                "strategy_signature": order.get("strategy_signature", ""),
                "source_run": order["source_run"],
                "paper_status": order.get("paper_status", ""),
                "template": order.get("template", ""),
                "regime_tag": order.get("regime_tag", ""),
                "order_type": order.get("order_type", ""),
                "entry_reason": order.get("entry_reason", ""),
                "signal_timestamp": order.get("signal_timestamp", ""),
                "parameter_signature": order.get("parameter_signature", ""),
                "risk_signature": order.get("risk_signature", ""),
                "status": order.get("status"),
                "order_id": order.get("id"),
                "client_order_id": order.get("client_order_id"),
                "qty": order["qty"],
                "entry_limit_price": order["entry_limit_price"],
                "entry_filled_price": order.get("filled_avg_price") or "",
                "stop_plan": order.get("stop_plan", ""),
                "target_plan": order.get("target_plan", ""),
                "time_stop_plan": order.get("time_stop_plan", ""),
                "session_exit_plan": order.get("session_exit_plan", ""),
                "pyramid_plan": order.get("pyramid_plan", ""),
                "exit_price": "",
                "exit_reason": "",
                "pnl": "",
                "mfe": "",
                "mae": "",
            }
        )
    pd.DataFrame(rows, columns=columns).to_csv(output_dir / "paper_options_trade_log.csv", index=False)


def write_summary(
    output_dir: Path,
    *,
    account: dict[str, Any],
    signal_scan: pd.DataFrame,
    shadow_signal_scan: pd.DataFrame,
    range_scan: pd.DataFrame,
    selected: pd.DataFrame,
    shadow_spreads: pd.DataFrame,
    condor_candidates: pd.DataFrame,
    pyramid_plans: pd.DataFrame,
    orders: list[dict[str, Any]],
) -> None:
    lines = [
        "# Alpaca Options Autopilot",
        "",
        f"Generated: {now_local().isoformat()}",
        "",
        "## Account Snapshot",
        f"- Equity: `{account.get('equity')}`",
        f"- Options buying power: `{account.get('options_buying_power')}`",
        f"- Options trading level: `{account.get('options_trading_level')}`",
        "",
        "## Live Signal Scan",
    ]
    if signal_scan.empty:
        lines.append("- No qualifying setup rows were available.")
    else:
        for row in signal_scan.itertuples(index=False):
            status_text = f" | status `{row.paper_status}`" if hasattr(row, "paper_status") else ""
            lines.append(
                f"- `{row.symbol}` | `{row.strategy_name}` | run `{row.source_run}`{status_text} | latest `{row.signal_direction}` | "
                f"recent `{row.recent_signal_direction}` | "
                f"pnl/day `{row.pnl_per_day:.2f}` | expectancy `{row.expectancy:.2f}`"
            )
    lines.extend(["", "## Shadow Signal Scan"])
    if shadow_signal_scan.empty:
        lines.append("- No shadow-only directional setup produced a live signal snapshot.")
    else:
        for row in shadow_signal_scan.itertuples(index=False):
            lines.append(
                f"- `{row.symbol}` | `{row.strategy_name}` | run `{row.source_run}` | latest `{row.signal_direction}` | "
                f"recent `{row.recent_signal_direction}` | pnl/day `{row.pnl_per_day:.2f}` | expectancy `{row.expectancy:.2f}`"
            )
    lines.extend(["", "## Range Regimes"])
    if range_scan.empty:
        lines.append("- No multi-timeframe range scan rows were produced.")
    else:
        for row in range_scan.sort_values(["symbol", "range_score", "timeframe"], ascending=[True, False, True]).itertuples(index=False):
            lines.append(
                f"- `{row.symbol}` | `{row.timeframe}` | range-bound `{bool(row.is_range_bound)}` | "
                f"score `{row.range_score}` | range `{row.realized_range_pct:.2%}` | VWAP dist `{row.vwap_distance_pct:.2%}`"
            )
    lines.extend(["", "## Selected Contracts"])
    if selected.empty:
        lines.append("- No live single-leg option candidate cleared the current filters.")
    else:
        for row in selected.itertuples(index=False):
            lines.append(
                f"- `{row.symbol}` -> `{row.option_symbol}` | target `{row.contract_target}` | bid `{row.bid_price:.2f}` | "
                f"ask `{row.ask_price:.2f}` | spread_bps `{row.spread_bps:.1f}` | signal `{row.signal_direction}`"
            )
    lines.extend(["", "## Shadow Debit Spreads"])
    if shadow_spreads.empty:
        lines.append("- No shadow debit spread candidate was available from the current live selections.")
    else:
        for row in shadow_spreads.itertuples(index=False):
            lines.append(
                f"- `{row.symbol}` | `{row.structure}` | long `{row.long_leg_symbol}` | short `{row.short_leg_symbol}` | "
                f"net debit `{row.net_debit_estimate:.2f}`"
            )
    lines.extend(["", "## Shadow Iron Condors"])
    if condor_candidates.empty:
        lines.append("- No iron condor candidate cleared the current range and chain filters.")
    else:
        for row in condor_candidates.itertuples(index=False):
            lines.append(
                f"- `{row.symbol}` | `{row.timeframe}` | credit `{row.net_credit_estimate:.2f}` | max loss `{row.max_loss_estimate:.2f}` | "
                f"BE `{row.breakeven_low}` / `{row.breakeven_high}`"
            )
    lines.extend(["", "## Pyramid Plans"])
    if pyramid_plans.empty:
        lines.append("- No staged pyramid plans were produced.")
    else:
        for row in pyramid_plans.itertuples(index=False):
            lines.append(
                f"- `{row.symbol}` | scale-needed `{row.scale_needed}` | recommended-total-scale `{row.recommended_total_scale}` | "
                f"stages `{row.stage_sizes}`"
            )
    lines.extend(["", "## Submitted Orders"])
    if not orders:
        lines.append("- No live paper option orders were submitted.")
    else:
        for order in orders:
            lines.append(
                f"- `{order['underlying_symbol']}` | `{order['structure']}` | status `{order.get('status')}` | "
                f"limit `{order['entry_limit_price']}` | exit `{order['exit_plan']}`"
            )
    (output_dir / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    assert_paper_trading_env_safe(execution_requested=bool(args.execute_single_leg or args.execute_mleg))
    output_dir = ROOT / "reports" / f"options_autonomy_{now_local().strftime('%Y%m%d_%H%M%S')}"
    output_dir.mkdir(parents=True, exist_ok=True)

    account = paper_get("/v2/account")
    clock = paper_get("/v2/clock")
    open_positions = paper_get("/v2/positions")
    open_orders = paper_get("/v2/orders", params={"status": "open", "limit": 100, "nested": True})

    protected_underlyings = {underlying_from_symbol(position["symbol"]) for position in open_positions}
    protected_underlyings.update(underlying_from_symbol(order["symbol"]) for order in open_orders if order.get("symbol"))
    existing_client_order_ids = {str(order.get("client_order_id")) for order in open_orders if order.get("client_order_id")}
    setups = load_recommended_setups(args.symbols)
    shadow_setups = load_shadow_setups(args.symbols)
    intraday_bars = fetch_intraday_bars(args.symbols)
    stock_quotes = fetch_stock_quotes(args.symbols)
    range_scan = evaluate_range_regimes(intraday_bars, args.symbols)
    signal_scan = evaluate_live_signals(setups, intraday_bars, signal_staleness_minutes=args.signal_staleness_minutes)
    shadow_signal_scan = evaluate_live_signals(shadow_setups, intraday_bars, signal_staleness_minutes=args.signal_staleness_minutes)
    if not signal_scan.empty:
        signal_scan = signal_scan.merge(stock_quotes, on="symbol", how="left")
        signal_scan["underlying_blocked"] = signal_scan["symbol"].isin(protected_underlyings)
        signal_scan["signal_live"] = signal_scan["recent_signal_direction"] != 0
    if not shadow_signal_scan.empty:
        shadow_signal_scan = shadow_signal_scan.merge(stock_quotes, on="symbol", how="left")
        shadow_signal_scan["underlying_blocked"] = shadow_signal_scan["symbol"].isin(protected_underlyings)
        shadow_signal_scan["signal_live"] = shadow_signal_scan["recent_signal_direction"] != 0

    selected_rows: list[dict[str, Any]] = []
    shadow_spread_rows: list[dict[str, Any]] = []
    condor_rows: list[dict[str, Any]] = []
    pyramid_rows: list[dict[str, Any]] = []
    submitted_orders: list[dict[str, Any]] = []
    chain_cache: dict[str, pd.DataFrame] = {}

    if not setups.empty:
        for row in setups.itertuples(index=False):
            plan = build_pyramid_plan(pnl_per_day=float(row.pnl_per_day), target_daily_pnl=float(args.target_daily_pnl))
            pyramid_rows.append(
                {
                    "symbol": row.symbol,
                    "strategy_name": row.strategy_name,
                    "source_run": row.source_run,
                    "pnl_per_day": float(row.pnl_per_day),
                    "scale_needed": plan["scale_needed"],
                    "recommended_total_scale": plan["recommended_total_scale"],
                    "stage_sizes": json.dumps(plan["stage_sizes"]),
                    "notes": plan["notes"],
                }
            )
    pyramid_lookup = build_pyramid_lookup(pd.DataFrame(pyramid_rows))

    if not signal_scan.empty:
        live_signals = signal_scan.loc[(signal_scan["signal_live"]) & (~signal_scan["underlying_blocked"])].copy()
        for _, signal_row in live_signals.iterrows():
            signal_row = signal_row.copy()
            signal_row["signal_direction"] = int(signal_row["recent_signal_direction"])
            symbol_key = str(signal_row["symbol"])
            if symbol_key not in chain_cache:
                chain_cache[symbol_key] = build_option_chain_frame(
                    underlying_symbol=symbol_key,
                    underlying_price=float(signal_row["underlying_close"]),
                    dte_min=int(signal_row["dte_min"]),
                    dte_max=int(signal_row["dte_max"]),
                )
            chain = chain_cache[symbol_key]
            if chain.empty:
                continue
            single_leg = choose_single_leg_candidate(signal_row, chain)
            if single_leg is None:
                continue
            selected_rows.append(
                {
                    **signal_row.to_dict(),
                    **single_leg.to_dict(),
                }
            )
            shadow_spread = choose_vertical_spread(signal_row, single_leg, chain)
            if shadow_spread is not None:
                shadow_spread_rows.append(
                    {
                        "symbol": signal_row["symbol"],
                        "strategy_name": signal_row["strategy_name"],
                        "source_run": signal_row["source_run"],
                        **shadow_spread,
                    }
                )

    if not range_scan.empty:
        candidate_regimes = range_scan.loc[range_scan["is_range_bound"]].copy()
        candidate_regimes = candidate_regimes.sort_values(["symbol", "range_score", "realized_range_pct"], ascending=[True, False, True])
        candidate_regimes = candidate_regimes.groupby("symbol", group_keys=False).head(1)
        for _, regime_row in candidate_regimes.iterrows():
            symbol_key = str(regime_row["symbol"])
            if symbol_key in protected_underlyings:
                continue
            if symbol_key not in chain_cache:
                chain_cache[symbol_key] = build_option_chain_frame(
                    underlying_symbol=symbol_key,
                    underlying_price=float(regime_row["last_close"]),
                    dte_min=2,
                    dte_max=2,
                )
            chain = chain_cache[symbol_key]
            condor = choose_iron_condor_candidate(symbol_key, chain, regime_row)
            if condor is not None:
                condor_rows.append(condor)

    selected = pd.DataFrame(selected_rows)
    shadow_spreads = pd.DataFrame(shadow_spread_rows)
    condor_candidates = pd.DataFrame(condor_rows)
    pyramid_plans = pd.DataFrame(pyramid_rows)
    if not selected.empty:
        selected = selected.sort_values(["pnl_per_day", "expectancy", "spread_bps"], ascending=[False, False, True]).reset_index(drop=True)
    if not condor_candidates.empty:
        condor_candidates = condor_candidates.sort_values(
            ["range_score", "reward_risk_ratio", "net_credit_estimate"],
            ascending=[False, False, False],
        ).reset_index(drop=True)

    if bool(clock.get("is_open")) and not selected.empty:
        for _, row in selected.head(args.max_orders).iterrows():
            plan = size_single_leg(account, row)
            if plan is None:
                continue
            client_order_id = build_client_order_id("opt", row, "single_leg")
            if client_order_id in existing_client_order_ids or paper_get_optional_by_client_order_id(client_order_id) is not None:
                continue
            risk_details = risk_plan_details(str(row["risk_signature"]))
            exit_plan = build_exit_plan_text(str(row["risk_signature"]))
            pyramid_plan = pyramid_lookup.get((str(row["symbol"]), str(row["strategy_name"]), str(row["source_run"])), {})
            if args.execute_single_leg:
                payload = build_single_leg_order_payload(str(row["option_symbol"]), plan["qty"], plan["limit_price"], client_order_id)
                order = submit_order(payload)
                order.update(
                    {
                        "underlying_symbol": str(row["symbol"]),
                        "option_symbol": str(row["option_symbol"]),
                        "structure": "single_leg",
                        "strategy_name": str(row["strategy_name"]),
                        "strategy_signature": str(row.get("setup_id", "")),
                        "source_run": str(row["source_run"]),
                        "paper_status": str(row.get("paper_status", PROMOTED_STATUS)),
                        "template": str(row.get("template", "")),
                        "regime_tag": f"directional_signal_{int(row['signal_direction'])}",
                        "order_type": "limit_single_leg",
                        "entry_reason": build_entry_reason(row),
                        "signal_timestamp": str(row.get("recent_signal_timestamp", row.get("signal_timestamp", ""))),
                        "parameter_signature": str(row.get("parameter_signature", "")),
                        "risk_signature": str(row.get("risk_signature", "")),
                        "qty": plan["qty"],
                        "entry_limit_price": plan["limit_price"],
                        "exit_plan": exit_plan,
                        "stop_plan": risk_details["stop_plan"],
                        "target_plan": risk_details["target_plan"],
                        "time_stop_plan": risk_details["time_stop_plan"],
                        "session_exit_plan": risk_details["session_exit_plan"],
                        "pyramid_plan": json.dumps(pyramid_plan, sort_keys=True),
                    }
                )
                submitted_orders.append(order)
                existing_client_order_ids.add(client_order_id)
                protected_underlyings.add(str(row["symbol"]))
            if args.execute_mleg:
                matching_spread = shadow_spreads.loc[
                    (shadow_spreads["symbol"] == row["symbol"]) & (shadow_spreads["strategy_name"] == row["strategy_name"])
                ]
                if not matching_spread.empty:
                    spread = matching_spread.iloc[0]
                    spread_payload = build_mleg_order_payload(
                        long_leg_symbol=str(spread["long_leg_symbol"]),
                        short_leg_symbol=str(spread["short_leg_symbol"]),
                        qty=1,
                        limit_price=float(spread["net_debit_estimate"]),
                        option_type=str(row["option_type"]),
                    )
                    spread_client_order_id = build_client_order_id("mleg", row, str(spread["structure"]))
                    if spread_client_order_id in existing_client_order_ids or paper_get_optional_by_client_order_id(spread_client_order_id) is not None:
                        continue
                    spread_payload["client_order_id"] = spread_client_order_id
                    order = submit_order(spread_payload)
                    order.update(
                        {
                            "underlying_symbol": str(row["symbol"]),
                            "long_leg_symbol": str(spread["long_leg_symbol"]),
                            "short_leg_symbol": str(spread["short_leg_symbol"]),
                            "structure": str(spread["structure"]),
                            "strategy_name": str(row["strategy_name"]),
                            "strategy_signature": str(row.get("setup_id", "")),
                            "source_run": str(row["source_run"]),
                            "paper_status": str(row.get("paper_status", PROMOTED_STATUS)),
                            "template": str(row.get("template", "")),
                            "regime_tag": f"directional_signal_{int(row['signal_direction'])}",
                            "order_type": "limit_mleg",
                            "entry_reason": build_entry_reason(row),
                            "signal_timestamp": str(row.get("recent_signal_timestamp", row.get("signal_timestamp", ""))),
                            "parameter_signature": str(row.get("parameter_signature", "")),
                            "risk_signature": str(row.get("risk_signature", "")),
                            "qty": 1,
                            "entry_limit_price": float(spread["net_debit_estimate"]),
                            "exit_plan": exit_plan,
                            "stop_plan": risk_details["stop_plan"],
                            "target_plan": risk_details["target_plan"],
                            "time_stop_plan": risk_details["time_stop_plan"],
                            "session_exit_plan": risk_details["session_exit_plan"],
                            "pyramid_plan": json.dumps(pyramid_plan, sort_keys=True),
                        }
                    )
                    submitted_orders.append(order)
                    existing_client_order_ids.add(spread_client_order_id)
                    protected_underlyings.add(str(row["symbol"]))

    if bool(clock.get("is_open")) and args.execute_mleg and not condor_candidates.empty:
        remaining_slots = max(0, args.max_orders - len(submitted_orders))
        for _, condor in condor_candidates.head(remaining_slots).iterrows():
            plan = size_condor(account, condor)
            if plan is None:
                continue
            condor_client_order_id = build_client_order_id("condor", condor, "iron_condor")
            if condor_client_order_id in existing_client_order_ids or paper_get_optional_by_client_order_id(condor_client_order_id) is not None:
                continue
            payload = build_condor_order_payload(
                long_put_symbol=str(condor["long_put_symbol"]),
                short_put_symbol=str(condor["short_put_symbol"]),
                short_call_symbol=str(condor["short_call_symbol"]),
                long_call_symbol=str(condor["long_call_symbol"]),
                qty=plan["qty"],
                limit_price=plan["limit_price"],
            )
            payload["client_order_id"] = condor_client_order_id
            order = submit_order(payload)
            order.update(
                {
                    "underlying_symbol": str(condor["symbol"]),
                    "long_put_symbol": str(condor["long_put_symbol"]),
                    "short_put_symbol": str(condor["short_put_symbol"]),
                    "short_call_symbol": str(condor["short_call_symbol"]),
                    "long_call_symbol": str(condor["long_call_symbol"]),
                    "structure": "iron_condor",
                    "strategy_name": "range_bound_condor_shadow",
                    "strategy_signature": "range_bound_condor_shadow",
                    "source_run": "live_range_scan",
                    "paper_status": "shadow_only",
                    "template": "iron_condor",
                    "regime_tag": f"range_bound_{condor['timeframe']}",
                    "order_type": "limit_mleg_credit",
                    "entry_reason": f"range regime score={int(condor['range_score'])} timeframe={condor['timeframe']}",
                    "signal_timestamp": str(now_local()),
                    "parameter_signature": json.dumps({"timeframe": condor["timeframe"]}, sort_keys=True),
                    "risk_signature": json.dumps({"max_loss_estimate": float(condor["max_loss_estimate"])}, sort_keys=True),
                    "qty": plan["qty"],
                    "entry_limit_price": plan["limit_price"],
                    "exit_plan": build_condor_exit_plan_text(condor),
                    "stop_plan": f"Defined-risk max loss {float(condor['max_loss_estimate']):.2f}.",
                    "target_plan": "Target roughly 50% credit capture.",
                    "time_stop_plan": "Intraday range review through the close.",
                    "session_exit_plan": "Re-evaluate or flatten if the range breaks before close.",
                    "pyramid_plan": "",
                }
            )
            submitted_orders.append(order)
            existing_client_order_ids.add(condor_client_order_id)
            protected_underlyings.add(str(condor["symbol"]))

    signal_scan.to_csv(output_dir / "live_signal_scan.csv", index=False)
    shadow_signal_scan.to_csv(output_dir / "shadow_signal_scan.csv", index=False)
    range_scan.to_csv(output_dir / "range_scan.csv", index=False)
    selected.to_csv(output_dir / "selected_single_leg_candidates.csv", index=False)
    shadow_spreads.to_csv(output_dir / "shadow_spread_candidates.csv", index=False)
    condor_candidates.to_csv(output_dir / "shadow_condor_candidates.csv", index=False)
    pyramid_plans.to_csv(output_dir / "pyramid_plans.csv", index=False)
    with (output_dir / "account_snapshot.json").open("w", encoding="utf-8") as handle:
        json.dump(
            {
                "generated_at": now_local().isoformat(),
                "account": {
                    key: account.get(key)
                    for key in [
                        "id",
                        "status",
                        "equity",
                        "buying_power",
                        "cash",
                        "options_trading_level",
                        "options_buying_power",
                    ]
                },
                "clock": {key: clock.get(key) for key in ["timestamp", "is_open", "next_open", "next_close"]},
                "open_positions": open_positions,
                "open_orders": open_orders,
            },
            handle,
            indent=2,
        )
    if submitted_orders:
        with (output_dir / "submitted_orders.json").open("w", encoding="utf-8") as handle:
            json.dump(submitted_orders, handle, indent=2, default=str)
    write_trade_log(output_dir, submitted_orders)
    write_summary(
        output_dir,
        account=account,
        signal_scan=signal_scan,
        shadow_signal_scan=shadow_signal_scan,
        range_scan=range_scan,
        selected=selected,
        shadow_spreads=shadow_spreads,
        condor_candidates=condor_candidates,
        pyramid_plans=pyramid_plans,
        orders=submitted_orders,
    )

    print(f"output_dir={output_dir}")
    print(f"clock_is_open={clock.get('is_open')}")
    print(f"selected_candidates={len(selected)}")
    print(f"shadow_spreads={len(shadow_spreads)}")
    print(f"condor_candidates={len(condor_candidates)}")
    print(f"submitted_orders={len(submitted_orders)}")
    if not selected.empty:
        print(selected.to_string(index=False, max_colwidth=120))
    if not condor_candidates.empty:
        print(condor_candidates.to_string(index=False, max_colwidth=120))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
