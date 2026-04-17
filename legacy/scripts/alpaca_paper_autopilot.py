from __future__ import annotations

import argparse
import json
import math
import os
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

import pandas as pd
import requests


ROOT = Path(r"C:\Users\rabisaab\Downloads")
RESEARCH_SRC = ROOT / "alpaca-stock-strategy-research" / "src"
if str(RESEARCH_SRC) not in sys.path:
    sys.path.insert(0, str(RESEARCH_SRC))

from alpaca_stock_research.backtests.engine import run_backtest
from alpaca_stock_research.backtests.strategies import build_signals
from alpaca_stock_research.data.alpaca import AlpacaClient
from alpaca_stock_research.features.signals import add_features


PAPER_BASE_URL = "https://paper-api.alpaca.markets"
DATA_BASE_URL = "https://data.alpaca.markets"
LOCAL_EVIDENCE_FILES = [
    ROOT / "best_strategies_consolidated.txt",
    ROOT / "daily_paper_engine_candidates.md",
    ROOT / "recent_2m_final_decision.md",
    ROOT / "tomorrow_alpaca_paper_runbook.md",
]
REQUESTED_SYMBOLS = ["QQQ", "SPY", "NVDA", "TSLA", "MSFT", "AMD"]


def require_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def paper_headers() -> dict[str, str]:
    return {
        "APCA-API-KEY-ID": require_env("APCA_API_KEY_ID"),
        "APCA-API-SECRET-KEY": require_env("APCA_API_SECRET_KEY"),
        "Content-Type": "application/json",
    }


def paper_get(path: str) -> Any:
    response = requests.get(f"{PAPER_BASE_URL}{path}", headers=paper_headers(), timeout=30)
    response.raise_for_status()
    return response.json()


def paper_post(path: str, payload: dict[str, Any]) -> Any:
    response = requests.post(f"{PAPER_BASE_URL}{path}", headers=paper_headers(), json=payload, timeout=30)
    response.raise_for_status()
    return response.json()


def stock_data_get(path: str, params: dict[str, Any]) -> Any:
    response = requests.get(f"{DATA_BASE_URL}{path}", headers=paper_headers(), params=params, timeout=60)
    response.raise_for_status()
    return response.json()


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


def underlying_from_symbol(symbol: str) -> str:
    prefix: list[str] = []
    for char in symbol:
        if char.isalpha():
            prefix.append(char)
            continue
        break
    return "".join(prefix) or symbol


def slugify(value: str) -> str:
    clean = []
    for char in value.lower():
        if char.isalnum():
            clean.append(char)
        else:
            clean.append("_")
    slug = "".join(clean)
    while "__" in slug:
        slug = slug.replace("__", "_")
    return slug.strip("_")


def latest_completed_session_date() -> datetime.date:
    now_local = datetime.now().astimezone()
    return now_local.date() - timedelta(days=1)


def fetch_daily_frame(symbols: list[str], lookback_days: int = 900) -> pd.DataFrame:
    client = AlpacaClient()
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=lookback_days)
    params = {
        "symbols": ",".join(symbols),
        "timeframe": "1Day",
        "start": start.isoformat().replace("+00:00", "Z"),
        "end": end.isoformat().replace("+00:00", "Z"),
        "adjustment": "split",
        "feed": "sip",
        "limit": 10000,
        "sort": "asc",
    }
    rows: list[dict[str, Any]] = []
    for page in client.get_stock_bars(params):
        for symbol, bars in page.get("bars", {}).items():
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
    frame = pd.DataFrame(rows).sort_values(["symbol", "timestamp"]).reset_index(drop=True)
    if frame.empty:
        return frame
    cutoff = datetime.now().astimezone().date()
    frame = frame[frame["timestamp"].dt.tz_convert("America/New_York").dt.date < cutoff].copy()
    return frame.reset_index(drop=True)


def fetch_intraday_frame(symbols: list[str]) -> pd.DataFrame:
    start = datetime.now(timezone.utc).astimezone().replace(hour=9, minute=30, second=0, microsecond=0).astimezone(timezone.utc)
    params = {
        "symbols": ",".join(symbols),
        "timeframe": "1Min",
        "start": start.isoformat().replace("+00:00", "Z"),
        "end": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "adjustment": "split",
        "feed": "sip",
        "limit": 10000,
        "sort": "asc",
    }
    payload = stock_data_get("/v2/stocks/bars", params)
    rows: list[dict[str, Any]] = []
    for symbol, bars in payload.get("bars", {}).items():
        for bar in bars:
            rows.append(
                {
                    "symbol": symbol,
                    "timestamp": pd.Timestamp(bar["t"]).tz_convert("America/New_York"),
                    "open": bar["o"],
                    "high": bar["h"],
                    "low": bar["l"],
                    "close": bar["c"],
                    "volume": bar["v"],
                }
            )
    return pd.DataFrame(rows).sort_values(["symbol", "timestamp"]).reset_index(drop=True)


def fetch_latest_quotes(symbols: list[str]) -> pd.DataFrame:
    payload = stock_data_get("/v2/stocks/quotes/latest", {"symbols": ",".join(symbols), "feed": "sip"})
    rows: list[dict[str, Any]] = []
    for symbol, wrapper in payload.get("quotes", {}).items():
        rows.append(
            {
                "symbol": symbol,
                "bid_price": wrapper["bp"],
                "ask_price": wrapper["ap"],
                "bid_size": wrapper["bs"],
                "ask_size": wrapper["as"],
                "quote_timestamp": pd.Timestamp(wrapper["t"]).tz_convert("America/New_York"),
            }
        )
    return pd.DataFrame(rows).sort_values("symbol").reset_index(drop=True)


def strategy_library() -> list[dict[str, Any]]:
    variants: list[dict[str, Any]] = []
    for rsi_cap in (20, 30):
        for streak_length in (3, 4, 5):
            for holding_bars in (3, 5):
                variants.append(
                    {
                        "template": "down_streak_exhaustion",
                        "variant": f"dse_rsi{rsi_cap}_streak{streak_length}_hold{holding_bars}",
                        "params": {
                            "holding_bars": holding_bars,
                            "profit_target_pct": 0.0,
                            "rsi_cap": rsi_cap,
                            "streak_length": streak_length,
                            "use_profit_target": False,
                        },
                    }
                )
    for rsi_entry in (20, 25, 30):
        for holding_bars in (3, 5):
            for use_profit_target in (False, True):
                variants.append(
                    {
                        "template": "rsi_pullback",
                        "variant": f"rsi_pullback_rsi{rsi_entry}_hold{holding_bars}_{'pt3' if use_profit_target else 'hold_only'}",
                        "params": {
                            "holding_bars": holding_bars,
                            "profit_target_pct": 0.03 if use_profit_target else 0.0,
                            "rsi_entry": rsi_entry,
                            "rsi_window": 14,
                            "use_profit_target": use_profit_target,
                        },
                    }
                )
    for excess_return_threshold in (0.0, 0.05):
        for lookback_window in (20, 60):
            for holding_bars in (5, 10, 20):
                variants.append(
                    {
                        "template": "relative_strength_vs_benchmark",
                        "variant": f"rs_lb{lookback_window}_hold{holding_bars}_thr{str(excess_return_threshold).replace('.', 'p')}",
                        "params": {
                            "excess_return_threshold": excess_return_threshold,
                            "holding_bars": holding_bars,
                            "lookback_window": lookback_window,
                            "profit_target_pct": 0.0,
                            "use_profit_target": False,
                        },
                    }
                )
    for rank_cutoff in (0.2, 0.3):
        for lookback_window in (20, 60):
            for holding_bars in (5, 10):
                variants.append(
                    {
                        "template": "cross_sectional_momentum",
                        "variant": f"csm_lb{lookback_window}_hold{holding_bars}_rank{str(rank_cutoff).replace('.', 'p')}",
                        "params": {
                            "holding_bars": holding_bars,
                            "lookback_window": lookback_window,
                            "profit_target_pct": 0.0,
                            "rank_cutoff": rank_cutoff,
                            "use_profit_target": False,
                        },
                    }
                )
    for breakout_window in (20, 55):
        for consolidation_window in (5, 10):
            for consolidation_range_pct in (0.08, 0.12):
                for holding_bars in (5, 10):
                    variants.append(
                        {
                            "template": "breakout_consolidation",
                            "variant": (
                                f"breakout_bw{breakout_window}_cw{consolidation_window}_"
                                f"range{str(consolidation_range_pct).replace('.', 'p')}_hold{holding_bars}"
                            ),
                            "params": {
                                "holding_bars": holding_bars,
                                "breakout_window": breakout_window,
                                "consolidation_window": consolidation_window,
                                "consolidation_range_pct": consolidation_range_pct,
                                "profit_target_pct": 0.0,
                                "use_profit_target": False,
                            },
                        }
                    )
    for pullback_window in (20, 55):
        for pullback_drawdown_pct in (0.03, 0.05):
            for holding_bars in (5, 10):
                variants.append(
                    {
                        "template": "pullback_in_trend",
                        "variant": (
                            f"pullback_pw{pullback_window}_dd{str(pullback_drawdown_pct).replace('.', 'p')}_hold{holding_bars}"
                        ),
                        "params": {
                            "holding_bars": holding_bars,
                            "pullback_window": pullback_window,
                            "pullback_drawdown_pct": pullback_drawdown_pct,
                            "profit_target_pct": 0.0,
                            "use_profit_target": False,
                        },
                    }
                )
    return variants


def append_atr(frame: pd.DataFrame) -> pd.DataFrame:
    data = frame.copy().sort_values(["symbol", "timestamp"]).reset_index(drop=True)
    data["prev_close"] = data.groupby("symbol")["close"].shift(1)
    tr = pd.concat(
        [
            (data["high"] - data["low"]).abs(),
            (data["high"] - data["prev_close"]).abs(),
            (data["low"] - data["prev_close"]).abs(),
        ],
        axis=1,
    ).max(axis=1)
    data["atr14"] = tr.groupby(data["symbol"]).transform(lambda s: s.rolling(14).mean())
    return data


def intraday_snapshot(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame()
    rows: list[dict[str, Any]] = []
    for symbol in sorted(frame["symbol"].unique()):
        symbol_frame = frame[frame["symbol"] == symbol].copy().reset_index(drop=True)
        if symbol_frame.empty:
            continue
        symbol_frame["ema8"] = symbol_frame["close"].ewm(span=8, adjust=False).mean()
        symbol_frame["ema21"] = symbol_frame["close"].ewm(span=21, adjust=False).mean()
        typical_price = (symbol_frame["high"] + symbol_frame["low"] + symbol_frame["close"]) / 3.0
        symbol_frame["cum_pv"] = (typical_price * symbol_frame["volume"]).cumsum()
        symbol_frame["cum_v"] = symbol_frame["volume"].cumsum()
        symbol_frame["vwap"] = symbol_frame["cum_pv"] / symbol_frame["cum_v"]
        window = symbol_frame.head(10)
        latest = symbol_frame.iloc[-1]
        mean_volume = max(float(symbol_frame.tail(min(20, len(symbol_frame)))["volume"].mean()), 1.0)
        rows.append(
            {
                "symbol": symbol,
                "intraday_last_timestamp": latest["timestamp"],
                "intraday_last_close": float(latest["close"]),
                "intraday_vwap": float(latest["vwap"]),
                "intraday_ema8": float(latest["ema8"]),
                "intraday_ema21": float(latest["ema21"]),
                "opening_range_high": float(window["high"].max()),
                "opening_range_low": float(window["low"].min()),
                "relative_volume_now": float(latest["volume"] / mean_volume),
                "bull_orb_live": bool(
                    latest["close"] > window["high"].max() * 1.0015
                    and latest["close"] > latest["vwap"]
                    and latest["ema8"] > latest["ema21"]
                    and latest["volume"] / mean_volume >= 1.0
                ),
                "bear_orb_live": bool(
                    latest["close"] < window["low"].min() * 0.9985
                    and latest["close"] < latest["vwap"]
                    and latest["ema8"] < latest["ema21"]
                    and latest["volume"] / mean_volume >= 1.0
                ),
            }
        )
    return pd.DataFrame(rows).sort_values("symbol").reset_index(drop=True)


def evaluate_strategy_grid(
    daily_bars: pd.DataFrame,
    features: pd.DataFrame,
    symbols: list[str],
) -> pd.DataFrame:
    variants = strategy_library()
    slippage = {symbol: 2.0 for symbol in symbols}
    rows: list[dict[str, Any]] = []
    feature_view = features.copy()
    if "atr14" not in feature_view.columns:
        if "atr14_x" in feature_view.columns:
            feature_view["atr14"] = feature_view["atr14_x"]
        elif "atr14_y" in feature_view.columns:
            feature_view["atr14"] = feature_view["atr14_y"]
        else:
            feature_view["atr14"] = float("nan")
    latest_feature_rows = feature_view.groupby("symbol", group_keys=False).tail(1).copy()
    latest_feature_rows = latest_feature_rows[["symbol", "close", "ma_20", "ma_50", "ma_200", "rsi_5", "rsi_14", "down_streak", "atr14"]]
    for variant in variants:
        signal_frame = build_signals(features, variant["template"], variant["params"])
        latest_signals = signal_frame.groupby("symbol", group_keys=False).tail(1)[["symbol", "signal"]].rename(columns={"signal": "live_signal"})
        for symbol in symbols:
            symbol_bars = daily_bars[daily_bars["symbol"] == symbol].copy()
            symbol_signals = signal_frame[signal_frame["symbol"] == symbol].copy()
            if symbol_signals.empty:
                continue
            result = run_backtest(
                symbol_bars,
                symbol_signals,
                variant["variant"],
                "full",
                variant["params"],
                variant["params"]["holding_bars"],
                100000.0,
                slippage,
                1.0,
                3,
                0.5,
                0.03,
                variant["params"].get("profit_target_pct") if variant["params"].get("use_profit_target") else None,
            )
            metrics = result.metrics
            live_signal = int(latest_signals[latest_signals["symbol"] == symbol]["live_signal"].iloc[0])
            latest_row = latest_feature_rows[latest_feature_rows["symbol"] == symbol].iloc[0]
            rows.append(
                {
                    "symbol": symbol,
                    "template": variant["template"],
                    "variant": variant["variant"],
                    "params_json": json.dumps(variant["params"], sort_keys=True),
                    "holding_bars": int(variant["params"]["holding_bars"]),
                    "live_signal": live_signal,
                    "trade_count": int(metrics.get("trade_count", 0)),
                    "total_return_pct": float(metrics.get("total_return", 0.0) * 100.0),
                    "cagr_pct": float(metrics.get("cagr", 0.0) * 100.0),
                    "win_rate_pct": float(metrics.get("win_rate", 0.0) * 100.0),
                    "profit_factor": float(metrics.get("profit_factor", 0.0)),
                    "max_drawdown_pct": float(metrics.get("max_drawdown", 0.0) * 100.0),
                    "latest_close": float(latest_row["close"]),
                    "ma_20": float(latest_row["ma_20"]) if pd.notna(latest_row["ma_20"]) else float("nan"),
                    "ma_50": float(latest_row["ma_50"]) if pd.notna(latest_row["ma_50"]) else float("nan"),
                    "ma_200": float(latest_row["ma_200"]) if pd.notna(latest_row["ma_200"]) else float("nan"),
                    "rsi_5": float(latest_row["rsi_5"]) if pd.notna(latest_row["rsi_5"]) else float("nan"),
                    "rsi_14": float(latest_row["rsi_14"]) if pd.notna(latest_row["rsi_14"]) else float("nan"),
                    "down_streak": float(latest_row["down_streak"]) if pd.notna(latest_row["down_streak"]) else float("nan"),
                    "atr14": float(latest_row["atr14"]) if pd.notna(latest_row["atr14"]) else float("nan"),
                }
            )
    return pd.DataFrame(rows).sort_values(["symbol", "variant"]).reset_index(drop=True)


def choose_candidates(
    evaluations: pd.DataFrame,
    intraday: pd.DataFrame,
    quotes: pd.DataFrame,
    open_positions: list[dict[str, Any]],
) -> pd.DataFrame:
    if evaluations.empty:
        return pd.DataFrame()
    protected_underlyings = {underlying_from_symbol(item["symbol"]) for item in open_positions}
    live = evaluations[evaluations["live_signal"] == 1].copy()
    if live.empty:
        return live
    live = live.merge(intraday, on="symbol", how="left")
    live = live.merge(quotes, on="symbol", how="left")
    live["underlying_blocked"] = live["symbol"].isin(protected_underlyings)
    live["spread_bps"] = ((live["ask_price"] - live["bid_price"]) / ((live["ask_price"] + live["bid_price"]) / 2.0)) * 10000.0
    qualified = live[
        (live["trade_count"] >= 5)
        & (live["profit_factor"] >= 1.15)
        & (live["total_return_pct"] > 0)
        & (live["max_drawdown_pct"] <= 20.0)
        & (~live["underlying_blocked"])
        & (live["spread_bps"] <= 15.0)
    ].copy()
    if qualified.empty:
        return qualified
    qualified["score"] = (
        qualified["profit_factor"] * 3.0
        + qualified["win_rate_pct"] / 100.0
        + qualified["total_return_pct"] / 25.0
        - qualified["max_drawdown_pct"] / 20.0
        - qualified["spread_bps"] / 10.0
    )
    qualified = qualified.sort_values(["score", "profit_factor", "total_return_pct"], ascending=[False, False, False])
    qualified = qualified.groupby("symbol", as_index=False, group_keys=False).head(1)
    return qualified.reset_index(drop=True)


def size_trade(account: dict[str, Any], row: pd.Series) -> dict[str, Any] | None:
    ask = float(row["ask_price"])
    bid = float(row["bid_price"])
    atr14 = float(row["atr14"]) if pd.notna(row["atr14"]) else ask * 0.03
    risk_budget = min(float(account.get("equity", 0.0)) * 0.00125, 125.0)
    stop_distance = max(ask * 0.02, min(ask * 0.04, atr14 * 0.75))
    qty_by_risk = math.floor(risk_budget / stop_distance)
    notional_cap = float(account.get("equity", 0.0)) * 0.04
    qty_by_notional = math.floor(notional_cap / ask)
    qty = max(0, min(qty_by_risk, qty_by_notional))
    if qty < 1:
        return None
    chase_buffer = max(0.02, (ask - bid) * 0.5, ask * 0.0005)
    limit_price = round(ask + chase_buffer, 2)
    stop_price = round(limit_price - stop_distance, 2)
    if stop_price <= 0:
        return None
    take_profit_price = round(limit_price + (limit_price - stop_price) * 1.8, 2)
    return {
        "qty": qty,
        "limit_price": limit_price,
        "stop_price": stop_price,
        "take_profit_price": take_profit_price,
        "risk_budget_usd": round(risk_budget, 2),
    }


def submit_bracket_order(symbol: str, variant: str, plan: dict[str, Any]) -> dict[str, Any]:
    client_order_id = f"codex-{slugify(symbol)}-{slugify(variant)}-{uuid4().hex[:8]}"
    payload = {
        "symbol": symbol,
        "qty": str(plan["qty"]),
        "side": "buy",
        "type": "limit",
        "limit_price": f"{plan['limit_price']:.2f}",
        "time_in_force": "gtc",
        "order_class": "bracket",
        "take_profit": {"limit_price": f"{plan['take_profit_price']:.2f}"},
        "stop_loss": {"stop_price": f"{plan['stop_price']:.2f}"},
        "client_order_id": client_order_id,
    }
    order = paper_post("/v2/orders", payload)
    order_id = order["id"]
    latest = order
    for _ in range(8):
        time.sleep(2)
        latest = paper_get(f"/v2/orders/{order_id}")
        if str(latest.get("status", "")).lower() in {"filled", "partially_filled", "accepted", "new"}:
            if latest.get("filled_avg_price") or str(latest.get("status", "")).lower() in {"accepted", "new"}:
                break
    latest["submitted_payload"] = payload
    return latest


def read_local_evidence_excerpt(limit: int = 60) -> list[str]:
    lines: list[str] = []
    for path in LOCAL_EVIDENCE_FILES:
        if not path.exists():
            continue
        content = path.read_text(encoding="utf-8", errors="ignore").splitlines()
        lines.append(f"Source: {path.name}")
        lines.extend(content[:limit])
        lines.append("")
    return lines


def write_summary(
    output_dir: Path,
    account: dict[str, Any],
    positions: list[dict[str, Any]],
    evaluations: pd.DataFrame,
    candidates: pd.DataFrame,
    orders: list[dict[str, Any]],
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    summary_path = output_dir / "strategy_consolidation.md"
    top_live = evaluations[evaluations["live_signal"] == 1].copy()
    top_live = top_live.sort_values(["profit_factor", "total_return_pct"], ascending=[False, False]).head(12)
    lines = [
        "# Strategy Consolidation And Paper Run",
        "",
        f"Generated: {datetime.now().astimezone().isoformat()}",
        "",
        "## Local Research Conclusions",
        "- Best confirmed research family: `down_streak_exhaustion`.",
        "- Best deployable intraday engine: `qqq_led_tqqq_sqqq_pair_opening_range_intraday_system`.",
        "- Best paper-only supporting family: durable cRSI presets.",
        "- Latest local runbook approved only the QQQ-led pair for the Monday 2026-04-06 session.",
        "- This run preserved existing account positions and only submitted new orders where the live signal and symbol-specific backtest both cleared risk gates.",
        "",
        "## Account Snapshot",
        f"- Equity: `{account.get('equity')}`",
        f"- Buying power: `{account.get('buying_power')}`",
        f"- Options trading level: `{account.get('options_trading_level')}`",
        f"- Open positions before this run: `{len(positions)}`",
        "",
        "## Active Strategy Variants Today",
    ]
    if top_live.empty:
        lines.append("- No active daily signals were found in the evaluated grid.")
    else:
        for row in top_live.itertuples():
            lines.append(
                f"- `{row.symbol}` | `{row.variant}` | PF `{row.profit_factor:.2f}` | return `{row.total_return_pct:.2f}%` | drawdown `{row.max_drawdown_pct:.2f}%`"
            )
    lines.append("")
    lines.append("## Orders Submitted")
    if not orders:
        lines.append("- No new orders were submitted because no candidate cleared both the live signal and risk gates.")
    else:
        for order in orders:
            lines.append(
                f"- `{order['symbol']}` | status `{order.get('status')}` | variant `{order['strategy_variant']}` | qty `{order['qty']}` | limit `{order['limit_price']}` | stop `{order['stop_price']}` | take-profit `{order['take_profit_price']}`"
            )
    lines.append("")
    lines.append("## Source Notes")
    lines.extend(read_local_evidence_excerpt(limit=12))
    summary_path.write_text("\n".join(lines), encoding="utf-8")


def write_trade_log(output_dir: Path, orders: list[dict[str, Any]]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    trade_log_path = output_dir / "paper_trade_log.csv"
    columns = [
        "timestamp",
        "symbol",
        "strategy_variant",
        "strategy_template",
        "status",
        "order_id",
        "client_order_id",
        "qty",
        "entry_price",
        "entry_limit_price",
        "exit_plan",
        "stop_price",
        "take_profit_price",
        "time_exit_plan",
        "exit_price",
        "pnl",
    ]
    rows: list[dict[str, Any]] = []
    for order in orders:
        rows.append(
            {
                "timestamp": datetime.now().astimezone().isoformat(),
                "symbol": order["symbol"],
                "strategy_variant": order["strategy_variant"],
                "strategy_template": order["strategy_template"],
                "status": order.get("status"),
                "order_id": order.get("id"),
                "client_order_id": order.get("client_order_id"),
                "qty": order["qty"],
                "entry_price": order.get("filled_avg_price") or "",
                "entry_limit_price": order["limit_price"],
                "exit_plan": f"Bracket stop {order['stop_price']} / target {order['take_profit_price']}",
                "stop_price": order["stop_price"],
                "take_profit_price": order["take_profit_price"],
                "time_exit_plan": order["time_exit_plan"],
                "exit_price": "",
                "pnl": "",
            }
        )
    pd.DataFrame(rows, columns=columns).to_csv(trade_log_path, index=False)


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate local strategy families and optionally submit guarded Alpaca paper trades.")
    parser.add_argument("--execute", action="store_true", help="Submit qualified paper orders instead of running in analysis-only mode.")
    parser.add_argument("--max-orders", type=int, default=2, help="Maximum number of new paper orders to submit.")
    parser.add_argument("--symbols", nargs="*", default=REQUESTED_SYMBOLS, help="Symbols to evaluate.")
    args = parser.parse_args()
    assert_paper_trading_env_safe(execution_requested=bool(args.execute))

    output_dir = ROOT / "reports" / f"paper_autonomy_{datetime.now().astimezone().strftime('%Y%m%d_%H%M%S')}"
    output_dir.mkdir(parents=True, exist_ok=True)

    account = paper_get("/v2/account")
    clock = paper_get("/v2/clock")
    open_positions = paper_get("/v2/positions")
    open_orders = paper_get("/v2/orders?status=open&limit=100")

    daily_bars = append_atr(fetch_daily_frame(args.symbols))
    features = add_features(daily_bars)
    intraday = intraday_snapshot(fetch_intraday_frame(args.symbols))
    quotes = fetch_latest_quotes(args.symbols)
    evaluations = evaluate_strategy_grid(daily_bars, features, args.symbols)
    candidates = choose_candidates(evaluations, intraday, quotes, open_positions)

    orders: list[dict[str, Any]] = []
    if args.execute and bool(clock.get("is_open")):
        for _, row in candidates.head(args.max_orders).iterrows():
            plan = size_trade(account, row)
            if plan is None:
                continue
            live_order = submit_bracket_order(str(row["symbol"]), str(row["variant"]), plan)
            live_order["symbol"] = str(row["symbol"])
            live_order["strategy_variant"] = str(row["variant"])
            live_order["strategy_template"] = str(row["template"])
            live_order["qty"] = plan["qty"]
            live_order["limit_price"] = plan["limit_price"]
            live_order["stop_price"] = plan["stop_price"]
            live_order["take_profit_price"] = plan["take_profit_price"]
            live_order["time_exit_plan"] = f"{int(row['holding_bars'])} trading days if neither bracket leg fills"
            orders.append(live_order)

    evaluations.to_csv(output_dir / "strategy_signal_scan.csv", index=False)
    candidates.to_csv(output_dir / "qualified_candidates.csv", index=False)
    intraday.to_csv(output_dir / "intraday_snapshot.csv", index=False)
    quotes.to_csv(output_dir / "latest_quotes.csv", index=False)
    with (output_dir / "account_snapshot.json").open("w", encoding="utf-8") as handle:
        json.dump(
            {
                "generated_at": datetime.now().astimezone().isoformat(),
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
                        "pattern_day_trader",
                        "daytrade_count",
                    ]
                },
                "clock": {key: clock.get(key) for key in ["timestamp", "is_open", "next_open", "next_close"]},
                "open_positions": open_positions,
                "open_orders": open_orders,
            },
            handle,
            indent=2,
        )
    if orders:
        with (output_dir / "submitted_orders.json").open("w", encoding="utf-8") as handle:
            json.dump(orders, handle, indent=2, default=str)
    write_trade_log(output_dir, orders)
    write_summary(output_dir, account, open_positions, evaluations, candidates, orders)

    print(f"output_dir={output_dir}")
    print(f"clock_is_open={clock.get('is_open')}")
    print(f"qualified_candidates={len(candidates)}")
    print(f"submitted_orders={len(orders)}")
    if not candidates.empty:
        print(candidates.head(args.max_orders).to_string(index=False, max_colwidth=120))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
