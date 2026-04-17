from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from backtest_qqq_sqzmom import (
    DATA_DIR,
    REPORTS_DIR,
    INITIAL_CAPITAL,
    LENGTH,
    TIMEZONE,
    build_windows,
    linreg_last,
    load_bars,
    safe_value,
)

OUTPUT_GRID = DATA_DIR / "qqq_sqzmom_long_short_timeframe_grid.csv"
OUTPUT_TOP = DATA_DIR / "qqq_sqzmom_long_short_timeframe_top.csv"
OUTPUT_POSITIVE_ALL = DATA_DIR / "qqq_sqzmom_long_short_timeframe_positive_all_windows.csv"
OUTPUT_WINNER_TRADES = DATA_DIR / "qqq_sqzmom_long_short_timeframe_winner_trades.csv"
OUTPUT_WINNER_DAILY = DATA_DIR / "qqq_sqzmom_long_short_timeframe_winner_daily_equity.csv"
OUTPUT_REPORT = REPORTS_DIR / "qqq_sqzmom_long_short_timeframe_report.md"

TIMEFRAMES = (1, 2, 5, 15, 60)
BUY_THRESHOLDS = (-0.5, -0.25, -0.15, -0.10, -0.05, -0.02)
SELL_THRESHOLDS = (0.35, 0.5, 0.75, 1.0, 1.5)
SESSION_MODES = (
    ("swing", False),
    ("intraday", True),
)
COST_BPS_PER_SIDE = 1.0


def build_indicator_frame(raw_bars: pd.DataFrame, timeframe_minutes: int) -> pd.DataFrame:
    rth = raw_bars.loc[
        raw_bars["in_rth"],
        ["timestamp_utc", "timestamp_et", "session_date", "open", "high", "low", "close", "volume"],
    ].copy()

    if timeframe_minutes == 1:
        frame = rth.copy()
    else:
        frame_parts: list[pd.DataFrame] = []
        rule = f"{timeframe_minutes}min"
        for session_date, day in rth.groupby("session_date", sort=True):
            day = day.sort_values("timestamp_et").set_index("timestamp_et")
            resampled = day.resample(rule, label="left", closed="left").agg(
                {
                    "timestamp_utc": "first",
                    "open": "first",
                    "high": "max",
                    "low": "min",
                    "close": "last",
                    "volume": "sum",
                }
            )
            resampled = resampled.dropna(subset=["open", "high", "low", "close"]).reset_index()
            resampled["session_date"] = session_date
            frame_parts.append(resampled)
        frame = pd.concat(frame_parts, ignore_index=True)

    highest = frame["high"].rolling(LENGTH).max()
    lowest = frame["low"].rolling(LENGTH).min()
    close_sma = frame["close"].rolling(LENGTH).mean()
    mean_source = ((highest + lowest) / 2.0 + close_sma) / 2.0
    deviation_source = (frame["close"] - mean_source).to_numpy(dtype=float)
    frame["val"] = linreg_last(deviation_source, LENGTH)

    prev_val = frame["val"].shift(1).fillna(0.0)
    positive = frame["val"] > 0.0
    growing = frame["val"] > prev_val
    frame["color"] = np.select(
        [
            positive & growing,
            positive & ~growing,
            ~positive & (frame["val"] < prev_val),
            ~positive & ~(frame["val"] < prev_val),
        ],
        ["lime", "green", "red", "maroon"],
        default="",
    )
    frame["prev_color"] = frame["color"].shift(1).fillna("")
    frame["is_last_bar_of_day"] = frame["session_date"].ne(frame["session_date"].shift(-1))
    return frame.reset_index(drop=True)


def simulate_long_short(
    frame: pd.DataFrame,
    timeframe_minutes: int,
    mode_name: str,
    force_flat_eod: bool,
    buy_threshold: float,
    sell_threshold: float,
    cost_bps_per_side: float = COST_BPS_PER_SIDE,
) -> dict[str, Any]:
    variant_id = f"{timeframe_minutes}m_{mode_name}_buy_{buy_threshold:g}_sell_{sell_threshold:g}"
    if frame.empty:
        return {
            "metrics": {
                "variant_id": variant_id,
                "timeframe_minutes": timeframe_minutes,
                "mode_name": mode_name,
                "force_flat_eod": force_flat_eod,
                "buy_threshold": buy_threshold,
                "sell_threshold": sell_threshold,
                "cost_bps_per_side": cost_bps_per_side,
                "final_equity": INITIAL_CAPITAL,
                "total_return_pct": 0.0,
                "cagr_pct": 0.0,
                "max_drawdown_pct": 0.0,
                "daily_sharpe": 0.0,
                "trade_count": 0,
                "long_trade_count": 0,
                "short_trade_count": 0,
                "win_rate_pct": 0.0,
                "profit_factor": 0.0,
                "avg_trade_pnl": 0.0,
                "avg_trade_return_pct": 0.0,
                "avg_hold_minutes": 0.0,
                "exposure_pct": 0.0,
                "profitable_days_pct": 0.0,
            },
            "trades": pd.DataFrame(),
            "daily_equity": pd.DataFrame(columns=["session_date", "equity"]),
        }

    timestamps = pd.to_datetime(frame["timestamp_et"]).reset_index(drop=True)
    dates = pd.to_datetime(frame["session_date"]).reset_index(drop=True)
    opens = frame["open"].to_numpy(dtype=float)
    closes = frame["close"].to_numpy(dtype=float)
    vals = frame["val"].to_numpy(dtype=float)
    colors = frame["color"].to_numpy(dtype=object)
    prev_colors = frame["prev_color"].to_numpy(dtype=object)
    last_bar = frame["is_last_bar_of_day"].to_numpy(dtype=bool)

    long_signal = (colors == "maroon") & (prev_colors == "red") & (vals > buy_threshold)
    short_signal = (colors == "green") & (prev_colors == "lime") & (vals > sell_threshold)

    cash = float(INITIAL_CAPITAL)
    qty = 0.0
    position = 0
    cost_rate = cost_bps_per_side / 10_000.0
    equity_close = np.full(len(frame), np.nan, dtype=float)
    in_market = np.zeros(len(frame), dtype=bool)

    pending_action: str | None = None
    pending_signal_idx: int | None = None

    entry_time: pd.Timestamp | None = None
    entry_price: float | None = None
    entry_equity: float | None = None
    entry_signal_idx: int | None = None
    entry_side: str | None = None
    trades: list[dict[str, Any]] = []

    def current_equity(mark_price: float) -> float:
        if position == 1:
            return cash + qty * mark_price
        if position == -1:
            return cash - qty * mark_price
        return cash

    def open_long(price: float, ts: pd.Timestamp, signal_idx: int) -> None:
        nonlocal cash, qty, position, entry_time, entry_price, entry_equity, entry_signal_idx, entry_side
        starting_equity = cash
        qty = cash / (price * (1.0 + cost_rate))
        cash = 0.0
        position = 1
        entry_time = ts
        entry_price = price
        entry_equity = starting_equity
        entry_signal_idx = signal_idx
        entry_side = "long"

    def open_short(price: float, ts: pd.Timestamp, signal_idx: int) -> None:
        nonlocal cash, qty, position, entry_time, entry_price, entry_equity, entry_signal_idx, entry_side
        starting_equity = cash
        qty = cash / price
        cash = cash + qty * price * (1.0 - cost_rate)
        position = -1
        entry_time = ts
        entry_price = price
        entry_equity = starting_equity
        entry_signal_idx = signal_idx
        entry_side = "short"

    def close_position(price: float, ts: pd.Timestamp, signal_idx: int, reason: str) -> None:
        nonlocal cash, qty, position, entry_time, entry_price, entry_equity, entry_signal_idx, entry_side
        if position == 0 or entry_time is None or entry_price is None or entry_equity is None or entry_side is None:
            return

        if position == 1:
            cash = cash + qty * price * (1.0 - cost_rate)
        else:
            cash = cash - qty * price * (1.0 + cost_rate)

        exit_equity = cash
        trades.append(
            {
                "variant_id": variant_id,
                "timeframe_minutes": timeframe_minutes,
                "mode_name": mode_name,
                "side": entry_side,
                "buy_threshold": buy_threshold,
                "sell_threshold": sell_threshold,
                "entry_signal_time": timestamps.iloc[int(entry_signal_idx or 0)].isoformat(),
                "entry_time": entry_time.isoformat(),
                "entry_price": entry_price,
                "entry_val": float(vals[int(entry_signal_idx or 0)]),
                "exit_signal_time": timestamps.iloc[signal_idx].isoformat(),
                "exit_time": ts.isoformat(),
                "exit_price": price,
                "exit_val": float(vals[signal_idx]),
                "exit_reason": reason,
                "bars_held": max(1, int(round((ts - entry_time).total_seconds() / 60.0 / timeframe_minutes))),
                "hold_minutes": float((ts - entry_time).total_seconds() / 60.0),
                "equity_before": entry_equity,
                "equity_after": exit_equity,
                "pnl_dollars": exit_equity - entry_equity,
                "return_pct": (exit_equity / entry_equity - 1.0) * 100.0,
            }
        )

        qty = 0.0
        position = 0
        entry_time = None
        entry_price = None
        entry_equity = None
        entry_signal_idx = None
        entry_side = None

    for i in range(len(frame)):
        if pending_action is not None:
            if pending_action == "open_long" and position == 0:
                open_long(opens[i], timestamps.iloc[i], int(pending_signal_idx or 0))
            elif pending_action == "open_short" and position == 0:
                open_short(opens[i], timestamps.iloc[i], int(pending_signal_idx or 0))
            elif pending_action == "flip_to_short" and position == 1:
                close_position(opens[i], timestamps.iloc[i], i, "flip_to_short")
                open_short(opens[i], timestamps.iloc[i], int(pending_signal_idx or 0))
            elif pending_action == "flip_to_long" and position == -1:
                close_position(opens[i], timestamps.iloc[i], i, "flip_to_long")
                open_long(opens[i], timestamps.iloc[i], int(pending_signal_idx or 0))
            pending_action = None
            pending_signal_idx = None

        in_market[i] = position != 0

        if force_flat_eod and position != 0 and last_bar[i]:
            close_position(closes[i], timestamps.iloc[i] + pd.Timedelta(minutes=timeframe_minutes), i, "eod_close")
            equity_close[i] = cash
            continue

        equity_close[i] = current_equity(closes[i])

        if i == len(frame) - 1:
            continue

        if position == 0:
            if long_signal[i]:
                pending_action = "open_long"
                pending_signal_idx = i
            elif short_signal[i]:
                pending_action = "open_short"
                pending_signal_idx = i
        elif position == 1 and short_signal[i]:
            pending_action = "flip_to_short"
            pending_signal_idx = i
        elif position == -1 and long_signal[i]:
            pending_action = "flip_to_long"
            pending_signal_idx = i

    if position != 0:
        close_position(
            closes[-1],
            timestamps.iloc[-1] + pd.Timedelta(minutes=timeframe_minutes),
            len(frame) - 1,
            "final_close",
        )
        equity_close[-1] = cash

    daily_equity = (
        pd.DataFrame({"session_date": dates.dt.date, "equity": equity_close})
        .groupby("session_date", as_index=False)
        .last()
    )
    daily_returns = daily_equity["equity"].pct_change().fillna(
        daily_equity["equity"].iloc[0] / INITIAL_CAPITAL - 1.0
    )
    daily_pnl = daily_equity["equity"].diff().fillna(
        daily_equity["equity"].iloc[0] - INITIAL_CAPITAL
    )
    trade_df = pd.DataFrame(trades)
    equity_series = pd.Series(equity_close)
    drawdown = equity_series / equity_series.cummax() - 1.0
    total_years = max(1.0, (dates.iloc[-1] - dates.iloc[0]).days / 365.25)
    gross_profit = float(trade_df.loc[trade_df["pnl_dollars"] > 0.0, "pnl_dollars"].sum()) if not trade_df.empty else 0.0
    gross_loss = float(trade_df.loc[trade_df["pnl_dollars"] < 0.0, "pnl_dollars"].sum()) if not trade_df.empty else 0.0

    metrics = {
        "variant_id": variant_id,
        "timeframe_minutes": timeframe_minutes,
        "mode_name": mode_name,
        "force_flat_eod": force_flat_eod,
        "buy_threshold": buy_threshold,
        "sell_threshold": sell_threshold,
        "cost_bps_per_side": cost_bps_per_side,
        "final_equity": float(cash),
        "total_return_pct": (cash / INITIAL_CAPITAL - 1.0) * 100.0,
        "cagr_pct": ((cash / INITIAL_CAPITAL) ** (1.0 / total_years) - 1.0) * 100.0,
        "max_drawdown_pct": abs(float(drawdown.min()) * 100.0),
        "daily_sharpe": float(daily_returns.mean() / daily_returns.std(ddof=0) * np.sqrt(252.0))
        if len(daily_returns) > 1 and daily_returns.std(ddof=0) > 0.0
        else 0.0,
        "trade_count": int(len(trade_df)),
        "long_trade_count": int((trade_df["side"] == "long").sum()) if not trade_df.empty else 0,
        "short_trade_count": int((trade_df["side"] == "short").sum()) if not trade_df.empty else 0,
        "win_rate_pct": float((trade_df["pnl_dollars"] > 0.0).mean() * 100.0) if not trade_df.empty else 0.0,
        "profit_factor": float(gross_profit / abs(gross_loss)) if gross_loss < 0.0 else (float("inf") if gross_profit > 0.0 else 0.0),
        "avg_trade_pnl": float(trade_df["pnl_dollars"].mean()) if not trade_df.empty else 0.0,
        "avg_trade_return_pct": float(trade_df["return_pct"].mean()) if not trade_df.empty else 0.0,
        "avg_hold_minutes": float(trade_df["hold_minutes"].mean()) if not trade_df.empty else 0.0,
        "exposure_pct": float(in_market.mean() * 100.0),
        "profitable_days_pct": float((daily_pnl > 0.0).mean() * 100.0),
    }
    return {
        "metrics": metrics,
        "trades": trade_df,
        "daily_equity": daily_equity.assign(daily_return=daily_returns, daily_pnl=daily_pnl),
    }


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    raw_bars = load_bars()
    timeframe_frames = {tf: build_indicator_frame(raw_bars, tf) for tf in TIMEFRAMES}
    timeframe_windows = {
        tf: build_windows(sorted(pd.to_datetime(frame["session_date"]).unique()))
        for tf, frame in timeframe_frames.items()
    }

    rows: list[dict[str, Any]] = []
    full_history_cache: dict[str, dict[str, Any]] = {}

    for timeframe_minutes in TIMEFRAMES:
        frame = timeframe_frames[timeframe_minutes]
        windows = timeframe_windows[timeframe_minutes]
        window_frames = {
            name: frame[
                (pd.to_datetime(frame["session_date"]) >= start_date)
                & (pd.to_datetime(frame["session_date"]) <= end_date)
            ].reset_index(drop=True)
            for name, (start_date, end_date) in windows.items()
        }

        for mode_name, force_flat_eod in SESSION_MODES:
            for buy_threshold in BUY_THRESHOLDS:
                for sell_threshold in SELL_THRESHOLDS:
                    variant_id = f"{timeframe_minutes}m_{mode_name}_buy_{buy_threshold:g}_sell_{sell_threshold:g}"
                    row: dict[str, Any] = {
                        "variant_id": variant_id,
                        "timeframe_minutes": timeframe_minutes,
                        "mode_name": mode_name,
                        "force_flat_eod": force_flat_eod,
                        "buy_threshold": buy_threshold,
                        "sell_threshold": sell_threshold,
                        "cost_bps_per_side": COST_BPS_PER_SIDE,
                    }
                    for window_name, window_frame in window_frames.items():
                        result = simulate_long_short(
                            window_frame,
                            timeframe_minutes=timeframe_minutes,
                            mode_name=mode_name,
                            force_flat_eod=force_flat_eod,
                            buy_threshold=buy_threshold,
                            sell_threshold=sell_threshold,
                        )
                        metrics = result["metrics"]
                        for key, value in metrics.items():
                            if key in {
                                "variant_id",
                                "timeframe_minutes",
                                "mode_name",
                                "force_flat_eod",
                                "buy_threshold",
                                "sell_threshold",
                                "cost_bps_per_side",
                            }:
                                continue
                            row[f"{window_name}_{key}"] = value
                        row[f"{window_name}_start"] = windows[window_name][0].date().isoformat()
                        row[f"{window_name}_end"] = windows[window_name][1].date().isoformat()
                        if window_name == "full_history":
                            full_history_cache[variant_id] = result
                    rows.append(row)

    grid = pd.DataFrame(rows)
    grid["positive_window_count"] = (
        (grid["full_history_total_return_pct"] > 0.0).astype(int)
        + (grid["last_1y_total_return_pct"] > 0.0).astype(int)
        + (grid["last_90d_total_return_pct"] > 0.0).astype(int)
        + (grid["ytd_2026_total_return_pct"] > 0.0).astype(int)
    )

    for column in (
        "full_history_total_return_pct",
        "last_1y_total_return_pct",
        "last_90d_total_return_pct",
        "ytd_2026_total_return_pct",
    ):
        grid[f"{column}_rank"] = (
            grid.groupby(["timeframe_minutes", "mode_name"])[column]
            .rank(method="min", ascending=False)
            .astype(int)
        )

    grid["stability_score"] = (
        grid["full_history_total_return_pct_rank"]
        + grid["last_1y_total_return_pct_rank"]
        + grid["last_90d_total_return_pct_rank"]
        + grid["ytd_2026_total_return_pct_rank"]
    )
    grid["stability_rank"] = (
        grid.groupby(["timeframe_minutes", "mode_name"])["stability_score"]
        .rank(method="min", ascending=True)
        .astype(int)
    )
    grid = grid.sort_values(
        ["stability_score", "full_history_total_return_pct"],
        ascending=[True, False],
    ).reset_index(drop=True)
    grid.to_csv(OUTPUT_GRID, index=False)

    top_cols = [
        "variant_id",
        "timeframe_minutes",
        "mode_name",
        "buy_threshold",
        "sell_threshold",
        "full_history_total_return_pct",
        "full_history_cagr_pct",
        "full_history_max_drawdown_pct",
        "full_history_daily_sharpe",
        "full_history_trade_count",
        "last_1y_total_return_pct",
        "last_90d_total_return_pct",
        "ytd_2026_total_return_pct",
        "positive_window_count",
        "stability_score",
    ]
    top = grid.sort_values("full_history_total_return_pct", ascending=False).loc[:, top_cols].head(20).copy()
    top.to_csv(OUTPUT_TOP, index=False)
    positive_all = (
        grid[grid["positive_window_count"] == 4]
        .sort_values("full_history_total_return_pct", ascending=False)
        .loc[:, top_cols]
        .copy()
    )
    positive_all.to_csv(OUTPUT_POSITIVE_ALL, index=False)

    winner = grid.iloc[0].to_dict()
    best_full = grid.sort_values("full_history_total_return_pct", ascending=False).iloc[0].to_dict()
    winner_result = full_history_cache[str(best_full["variant_id"])]
    winner_result["trades"].to_csv(OUTPUT_WINNER_TRADES, index=False)
    winner_result["daily_equity"].to_csv(OUTPUT_WINNER_DAILY, index=False)

    timeframe_summary_lines: list[str] = []
    for timeframe_minutes in TIMEFRAMES:
        sub = grid[grid["timeframe_minutes"] == timeframe_minutes].sort_values(
            "full_history_total_return_pct",
            ascending=False,
        )
        best = sub.iloc[0]
        timeframe_summary_lines.extend(
            [
                f"### {timeframe_minutes}m",
                "",
                f"- Best row: `{best['variant_id']}`.",
                f"- Mode `{best['mode_name']}`, buy `>{best['buy_threshold']}` on dark red, short/flip on dark green `>{best['sell_threshold']}`.",
                f"- Full-history return `{safe_value(float(best['full_history_total_return_pct']))}%`, CAGR `{safe_value(float(best['full_history_cagr_pct']))}%`, max DD `{safe_value(float(best['full_history_max_drawdown_pct']))}%`, last 1y `{safe_value(float(best['last_1y_total_return_pct']))}%`, last 90d `{safe_value(float(best['last_90d_total_return_pct']))}%`.",
                "",
            ]
        )

    report_lines = [
        "# QQQ SQZMOM Long/Short Timeframe Grid",
        "",
        "## What was tested",
        "",
        "- Long/short reversal engine on QQQ regular-session bars only.",
        "- Long signal: `red -> maroon` with `val > buy_threshold`.",
        "- Short signal / long exit / short flip: `lime -> green` with `val > sell_threshold`.",
        "- If already short, a new long signal flips the position to long on the next bar open.",
        "- If already long, a new short signal flips the position to short on the next bar open.",
        "- Timeframes tested: `1m`, `2m`, `5m`, `15m`, `60m`.",
        "- Modes tested: swing and end-of-day-flat intraday.",
        f"- Friction: `{COST_BPS_PER_SIDE:.1f}` bp per side.",
        "",
        "## Headline findings",
        "",
        f"- Total rows tested: `{len(grid)}`.",
        f"- Positive full-history rows: `{int((grid['full_history_total_return_pct'] > 0.0).sum())}`.",
        f"- Positive in all four windows: `{int((grid['positive_window_count'] == 4).sum())}`.",
        f"- Best full-history row: `{best_full['variant_id']}` with full-history return `{safe_value(float(best_full['full_history_total_return_pct']))}%`, CAGR `{safe_value(float(best_full['full_history_cagr_pct']))}%`, max DD `{safe_value(float(best_full['full_history_max_drawdown_pct']))}%`, last 1y `{safe_value(float(best_full['last_1y_total_return_pct']))}%`, last 90d `{safe_value(float(best_full['last_90d_total_return_pct']))}%`, YTD 2026 `{safe_value(float(best_full['ytd_2026_total_return_pct']))}%`.",
        "",
        "## Top rows",
        "",
        "| Variant | TF | Mode | Buy threshold | Sell threshold | Full return | Max DD | Last 1y | Last 90d | YTD 2026 | Stability |",
        "| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]

    for row in top.head(10).itertuples():
        report_lines.append(
            f"| {row.variant_id} | {int(row.timeframe_minutes)}m | {row.mode_name} | {row.buy_threshold} | {row.sell_threshold} | {safe_value(float(row.full_history_total_return_pct))}% | {safe_value(float(row.full_history_max_drawdown_pct))}% | {safe_value(float(row.last_1y_total_return_pct))}% | {safe_value(float(row.last_90d_total_return_pct))}% | {safe_value(float(row.ytd_2026_total_return_pct))}% | {int(row.stability_score)} |"
        )

    report_lines.extend(
        [
            "",
            "## Positive In All Windows",
            "",
        ]
    )

    if positive_all.empty:
        report_lines.append("- No rows were positive in all four windows.")
    else:
        report_lines.extend(
            [
                "| Variant | TF | Mode | Full return | Max DD | Last 1y | Last 90d | YTD 2026 |",
                "| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: |",
            ]
        )
        for row in positive_all.head(10).itertuples():
            report_lines.append(
                f"| {row.variant_id} | {int(row.timeframe_minutes)}m | {row.mode_name} | {safe_value(float(row.full_history_total_return_pct))}% | {safe_value(float(row.full_history_max_drawdown_pct))}% | {safe_value(float(row.last_1y_total_return_pct))}% | {safe_value(float(row.last_90d_total_return_pct))}% | {safe_value(float(row.ytd_2026_total_return_pct))}% |"
            )

    report_lines.extend(
        [
            "",
            "## Per-timeframe summary",
            "",
            *timeframe_summary_lines,
            "## Important options note",
            "",
            "- This is still an honest underlying-signal backtest, not a quote-accurate options replay.",
            "- Local project notes repeatedly mark full historical options replay as blocked by incomplete expired-contract quote coverage and chain reconstruction gaps.",
            "- That means calls, puts, verticals, and iron condors can be shadow-mapped from these signals, but not fairly execution-tested across the whole 2021-2026 sample with the data currently in this workspace.",
            "",
            "## Output files",
            "",
            f"- Full grid: `{OUTPUT_GRID}`",
            f"- Top full-history rows: `{OUTPUT_TOP}`",
            f"- Positive-all-window rows: `{OUTPUT_POSITIVE_ALL}`",
            f"- Winner trades: `{OUTPUT_WINNER_TRADES}`",
            f"- Winner daily equity: `{OUTPUT_WINNER_DAILY}`",
            "",
        ]
    )
    OUTPUT_REPORT.write_text("\n".join(report_lines), encoding="utf-8")

    print(top.to_string(index=False))
    print()
    print(f"Report: {OUTPUT_REPORT}")


if __name__ == "__main__":
    main()
