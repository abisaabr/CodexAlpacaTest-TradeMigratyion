from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from time import perf_counter

import numpy as np
import pandas as pd
from numba import njit

from qqq_fvg_backtest_runner import (
    BASE,
    INITIAL_CAPITAL,
    SOURCE,
    STOP_LOSS_PCTS,
    TAKE_PROFIT_PCTS,
    TIMEFRAMES,
    load_minute_data,
    markdown_table,
    resample_intraday,
)


MODES = ["event", "active"]
COST_BPS_PER_SIDE = [0.0, 1.0, 2.0, 5.0]
REALISTIC_COST_BPS = 2.0

OUTPUTS = {
    "grid": BASE / "qqq_fvg_extended_grid_results.csv",
    "summary": BASE / "qqq_fvg_extended_summary.md",
    "best_overall_realistic_trades": BASE / "qqq_fvg_best_realistic_trades.csv",
    "best_overall_realistic_equity": BASE / "qqq_fvg_best_realistic_daily_equity.csv",
    "best_event_realistic_trades": BASE / "qqq_fvg_best_event_realistic_trades.csv",
    "best_event_realistic_equity": BASE / "qqq_fvg_best_event_realistic_daily_equity.csv",
    "best_active_realistic_trades": BASE / "qqq_fvg_best_active_realistic_trades.csv",
    "best_active_realistic_equity": BASE / "qqq_fvg_best_active_realistic_daily_equity.csv",
}


@dataclass(frozen=True)
class PreparedTimeframeSignals:
    minutes: int
    bars: pd.DataFrame
    session_ids: np.ndarray
    event_signal: np.ndarray
    active_signal: np.ndarray
    bullish_event_count: int
    bearish_event_count: int
    bullish_active_bars: int
    bearish_active_bars: int


def compute_fvg_components(
    bars: pd.DataFrame,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    open_ = bars["open"].to_numpy(dtype=np.float64)
    high = bars["high"].to_numpy(dtype=np.float64)
    low = bars["low"].to_numpy(dtype=np.float64)
    close = bars["close"].to_numpy(dtype=np.float64)
    n = len(bars)

    prev_open = np.full(n, np.nan, dtype=np.float64)
    prev_close = np.full(n, np.nan, dtype=np.float64)
    prev_open[1:] = open_[:-1]
    prev_close[1:] = close[:-1]

    high_2 = np.full(n, np.nan, dtype=np.float64)
    low_2 = np.full(n, np.nan, dtype=np.float64)
    high_2[2:] = high[:-2]
    low_2[2:] = low[:-2]

    bar_delta_pct = (prev_close - prev_open) / (prev_open * 100.0)
    abs_delta = np.nan_to_num(np.abs(bar_delta_pct), nan=0.0)
    cumulative_abs = np.cumsum(abs_delta)
    bar_index = np.arange(n, dtype=np.float64)
    threshold = np.full(n, np.nan, dtype=np.float64)
    valid_index = bar_index > 0
    threshold[valid_index] = (cumulative_abs[valid_index] / bar_index[valid_index]) * 2.0

    bullish_event = (
        (low > high_2)
        & (prev_close > high_2)
        & (bar_delta_pct > threshold)
    )
    bearish_event = (
        (high < low_2)
        & (prev_close < low_2)
        & ((-bar_delta_pct) > threshold)
    )

    event_signal = np.zeros(n, dtype=np.int8)
    event_signal[bullish_event] = 1
    event_signal[bearish_event] = -1
    event_signal[:2] = 0

    bullish_bottom = np.full(n, np.nan, dtype=np.float64)
    bearish_top = np.full(n, np.nan, dtype=np.float64)
    bullish_bottom[bullish_event] = high_2[bullish_event]
    bearish_top[bearish_event] = high[bearish_event]

    return event_signal, bullish_event, bearish_event, bullish_bottom, bearish_top


def build_active_signal(
    bars: pd.DataFrame,
    bullish_event: np.ndarray,
    bearish_event: np.ndarray,
    bullish_bottom: np.ndarray,
    bearish_top: np.ndarray,
) -> np.ndarray:
    high = bars["high"].to_numpy(dtype=np.float64)
    low = bars["low"].to_numpy(dtype=np.float64)
    active: list[tuple[int, float]] = []
    state_signal = np.zeros(len(bars), dtype=np.int8)

    for i in range(len(bars)):
        if active:
            survivors: list[tuple[int, float]] = []
            for bias, invalidation_level in active:
                if bias == 1:
                    if not (low[i] < invalidation_level):
                        survivors.append((bias, invalidation_level))
                else:
                    if not (high[i] > invalidation_level):
                        survivors.append((bias, invalidation_level))
            active = survivors

        if bullish_event[i]:
            active.append((1, float(bullish_bottom[i])))
        if bearish_event[i]:
            active.append((-1, float(bearish_top[i])))

        if active:
            state_signal[i] = active[-1][0]

    return state_signal


def prepare_signals(frame: pd.DataFrame, minutes: int) -> PreparedTimeframeSignals:
    bars = resample_intraday(frame, minutes)
    event_signal, bullish_event, bearish_event, bullish_bottom, bearish_top = compute_fvg_components(bars)
    active_signal = build_active_signal(bars, bullish_event, bearish_event, bullish_bottom, bearish_top)
    session_ids, _ = pd.factorize(bars["session_date"], sort=True)
    return PreparedTimeframeSignals(
        minutes=minutes,
        bars=bars,
        session_ids=session_ids.astype(np.int32),
        event_signal=event_signal,
        active_signal=active_signal,
        bullish_event_count=int(bullish_event.sum()),
        bearish_event_count=int(bearish_event.sum()),
        bullish_active_bars=int((active_signal == 1).sum()),
        bearish_active_bars=int((active_signal == -1).sum()),
    )


@njit(cache=True)
def run_backtest_metrics_with_cost(
    open_: np.ndarray,
    high: np.ndarray,
    low: np.ndarray,
    close: np.ndarray,
    signal: np.ndarray,
    session_ids: np.ndarray,
    stop_loss_pct: float,
    take_profit_pct: float,
    cost_bps_per_side: float,
) -> tuple[float, float, float, float, float, float, int, int, int, int, int, float, float, float]:
    n = len(open_)
    session_count = int(session_ids[-1]) + 1 if n else 0
    eod_equity = np.zeros(session_count, dtype=np.float64)

    cost_pct = cost_bps_per_side / 10000.0
    equity = INITIAL_CAPITAL
    peak_equity = INITIAL_CAPITAL
    max_drawdown = 0.0

    position = 0
    pending_signal = 0
    entry_price = 0.0
    base_equity = INITIAL_CAPITAL
    entry_bar = -1

    trade_count = 0
    win_count = 0
    long_trades = 0
    short_trades = 0
    bars_in_position = 0
    holding_bars_total = 0

    gross_profit = 0.0
    gross_loss = 0.0

    for i in range(n):
        last_bar_of_session = i == n - 1 or session_ids[i + 1] != session_ids[i]

        if pending_signal != 0:
            if position != 0:
                exit_price = open_[i]
                trade_return = position * ((exit_price - entry_price) / entry_price)
                equity = base_equity * (1.0 + trade_return) * (1.0 - cost_pct)
                trade_count += 1
                holding_bars_total += i - entry_bar
                if position == 1:
                    long_trades += 1
                else:
                    short_trades += 1
                if trade_return > 0.0:
                    win_count += 1
                    gross_profit += trade_return
                elif trade_return < 0.0:
                    gross_loss += -trade_return
                position = 0

            position = pending_signal
            entry_price = open_[i]
            equity = equity * (1.0 - cost_pct)
            base_equity = equity
            entry_bar = i
            pending_signal = 0

        exited = False
        if position != 0:
            if position == 1:
                stop_price = entry_price * (1.0 - stop_loss_pct)
                target_price = entry_price * (1.0 + take_profit_pct)
                if low[i] <= stop_price:
                    exit_price = stop_price
                    exited = True
                elif high[i] >= target_price:
                    exit_price = target_price
                    exited = True
            else:
                stop_price = entry_price * (1.0 + stop_loss_pct)
                target_price = entry_price * (1.0 - take_profit_pct)
                if high[i] >= stop_price:
                    exit_price = stop_price
                    exited = True
                elif low[i] <= target_price:
                    exit_price = target_price
                    exited = True

            if exited:
                trade_return = position * ((exit_price - entry_price) / entry_price)
                equity = base_equity * (1.0 + trade_return) * (1.0 - cost_pct)
                trade_count += 1
                holding_bars_total += i - entry_bar + 1
                if position == 1:
                    long_trades += 1
                else:
                    short_trades += 1
                if trade_return > 0.0:
                    win_count += 1
                    gross_profit += trade_return
                elif trade_return < 0.0:
                    gross_loss += -trade_return
                position = 0

        if last_bar_of_session and position != 0:
            exit_price = close[i]
            trade_return = position * ((exit_price - entry_price) / entry_price)
            equity = base_equity * (1.0 + trade_return) * (1.0 - cost_pct)
            trade_count += 1
            holding_bars_total += i - entry_bar + 1
            if position == 1:
                long_trades += 1
            else:
                short_trades += 1
            if trade_return > 0.0:
                win_count += 1
                gross_profit += trade_return
            elif trade_return < 0.0:
                gross_loss += -trade_return
            position = 0

        if not last_bar_of_session:
            current_signal = int(signal[i])
            if current_signal != 0:
                if position == 0 or current_signal != position:
                    pending_signal = current_signal
                else:
                    pending_signal = 0
        else:
            pending_signal = 0

        if position != 0:
            bars_in_position += 1
            mark_return = position * ((close[i] - entry_price) / entry_price)
            mark_equity = base_equity * (1.0 + mark_return)
        else:
            mark_equity = equity

        if mark_equity > peak_equity:
            peak_equity = mark_equity
        if peak_equity > 0.0:
            drawdown = 1.0 - (mark_equity / peak_equity)
            if drawdown > max_drawdown:
                max_drawdown = drawdown

        if last_bar_of_session:
            eod_equity[session_ids[i]] = equity

    daily_returns = np.zeros(session_count, dtype=np.float64)
    if session_count > 0:
        daily_returns[0] = (eod_equity[0] / INITIAL_CAPITAL) - 1.0
        for j in range(1, session_count):
            prev_equity = eod_equity[j - 1]
            if prev_equity != 0.0:
                daily_returns[j] = (eod_equity[j] / prev_equity) - 1.0

    sharpe = 0.0
    if session_count > 1:
        mean_ret = daily_returns.mean()
        std_ret = daily_returns.std()
        if std_ret > 0.0:
            sharpe = mean_ret / std_ret * np.sqrt(252.0)

    total_return_pct = ((equity / INITIAL_CAPITAL) - 1.0) * 100.0
    cagr = 0.0
    if session_count > 0 and equity > 0.0:
        cagr = ((equity / INITIAL_CAPITAL) ** (252.0 / session_count) - 1.0) * 100.0

    win_rate = (win_count / trade_count) * 100.0 if trade_count else 0.0
    profit_factor = gross_profit / gross_loss if gross_loss > 0.0 else 0.0
    avg_trade_return_pct = ((gross_profit - gross_loss) / trade_count) * 100.0 if trade_count else 0.0
    avg_holding_bars = holding_bars_total / trade_count if trade_count else 0.0
    exposure_pct = (bars_in_position / n) * 100.0 if n else 0.0

    return (
        equity,
        total_return_pct,
        cagr,
        max_drawdown * 100.0,
        sharpe,
        profit_factor,
        trade_count,
        win_count,
        long_trades,
        short_trades,
        session_count,
        avg_trade_return_pct,
        avg_holding_bars,
        exposure_pct,
    )


def run_backtest_detailed_with_cost(
    bars: pd.DataFrame,
    signal: np.ndarray,
    stop_loss_pct: float,
    take_profit_pct: float,
    cost_bps_per_side: float,
    mode: str,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    open_ = bars["open"].to_numpy(dtype=np.float64)
    high = bars["high"].to_numpy(dtype=np.float64)
    low = bars["low"].to_numpy(dtype=np.float64)
    close = bars["close"].to_numpy(dtype=np.float64)
    session_ids, session_labels = pd.factorize(bars["session_date"], sort=True)
    timestamps = bars.index.to_numpy()
    cost_pct = cost_bps_per_side / 10000.0

    equity = INITIAL_CAPITAL
    position = 0
    pending_signal = 0
    entry_price = 0.0
    entry_bar = -1
    entry_equity = INITIAL_CAPITAL
    entry_reason = ""
    trades: list[dict[str, object]] = []
    daily_equity: list[dict[str, object]] = []

    def close_trade(exit_bar: int, exit_price: float, reason: str) -> None:
        nonlocal equity, position
        gross_price_return = position * ((exit_price - entry_price) / entry_price)
        exit_equity = entry_equity * (1.0 + gross_price_return) * (1.0 - cost_pct)
        net_return_pct = (exit_equity / equity_before_entry_for_trade - 1.0) * 100.0
        trades.append(
            {
                "entry_time": pd.Timestamp(timestamps[entry_bar]),
                "exit_time": pd.Timestamp(timestamps[exit_bar]),
                "mode": mode,
                "side": "long" if position == 1 else "short",
                "entry_price": entry_price,
                "exit_price": exit_price,
                "gross_price_return_pct": gross_price_return * 100.0,
                "net_trade_return_pct": net_return_pct,
                "bars_held": exit_bar - entry_bar + (0 if reason == "reverse_open" else 1),
                "entry_reason": entry_reason,
                "exit_reason": reason,
                "cost_bps_per_side": cost_bps_per_side,
                "equity_after_trade": exit_equity,
            }
        )
        equity = exit_equity
        position = 0

    equity_before_entry_for_trade = INITIAL_CAPITAL
    for i in range(len(bars)):
        last_bar_of_session = i == len(bars) - 1 or session_ids[i + 1] != session_ids[i]

        if pending_signal != 0:
            if position != 0:
                close_trade(i, open_[i], "reverse_open")
            position = pending_signal
            entry_price = open_[i]
            equity_before_entry_for_trade = equity
            equity = equity * (1.0 - cost_pct)
            entry_equity = equity
            entry_bar = i
            entry_reason = "bullish_fvg" if pending_signal == 1 else "bearish_fvg"
            if mode == "active":
                entry_reason += "_active"
            pending_signal = 0

        if position != 0:
            if position == 1:
                stop_price = entry_price * (1.0 - stop_loss_pct)
                target_price = entry_price * (1.0 + take_profit_pct)
                if low[i] <= stop_price:
                    close_trade(i, stop_price, "stop_loss")
                elif high[i] >= target_price:
                    close_trade(i, target_price, "take_profit")
            else:
                stop_price = entry_price * (1.0 + stop_loss_pct)
                target_price = entry_price * (1.0 - take_profit_pct)
                if high[i] >= stop_price:
                    close_trade(i, stop_price, "stop_loss")
                elif low[i] <= target_price:
                    close_trade(i, target_price, "take_profit")

        if last_bar_of_session and position != 0:
            close_trade(i, close[i], "session_close")

        if last_bar_of_session:
            pending_signal = 0
            daily_equity.append(
                {
                    "session_date": pd.Timestamp(session_labels[session_ids[i]]),
                    "equity": equity,
                }
            )
        else:
            current_signal = int(signal[i])
            if current_signal != 0:
                if position == 0 or current_signal != position:
                    pending_signal = current_signal
                else:
                    pending_signal = 0

    trades_df = pd.DataFrame(trades)
    equity_df = pd.DataFrame(daily_equity)
    return trades_df, equity_df


def save_best_detail(
    label: str,
    row: pd.Series,
    prepared: dict[int, PreparedTimeframeSignals],
) -> None:
    tf_data = prepared[int(row["timeframe_min"])]
    signal = tf_data.event_signal if row["mode"] == "event" else tf_data.active_signal
    trades_df, equity_df = run_backtest_detailed_with_cost(
        tf_data.bars,
        signal,
        float(row["stop_loss_pct"]) / 100.0,
        float(row["take_profit_pct"]) / 100.0,
        float(row["cost_bps_per_side"]),
        str(row["mode"]),
    )
    trades_df.to_csv(OUTPUTS[f"{label}_trades"], index=False)
    equity_df.to_csv(OUTPUTS[f"{label}_equity"], index=False)


def cost_curve(
    results: pd.DataFrame,
    mode: str,
    timeframe_min: int,
    stop_loss_pct: float,
    take_profit_pct: float,
) -> pd.DataFrame:
    subset = results[
        (results["mode"] == mode)
        & (results["timeframe_min"] == timeframe_min)
        & (results["stop_loss_pct"] == stop_loss_pct)
        & (results["take_profit_pct"] == take_profit_pct)
    ].copy()
    return subset.sort_values("cost_bps_per_side")[
        [
            "mode",
            "timeframe_label",
            "stop_loss_pct",
            "take_profit_pct",
            "cost_bps_per_side",
            "total_return_pct",
            "max_drawdown_pct",
            "sharpe",
            "trade_count",
        ]
    ]


def build_summary(results: pd.DataFrame, prepared: dict[int, PreparedTimeframeSignals], runtime_seconds: float) -> str:
    realistic = results[results["cost_bps_per_side"] == REALISTIC_COST_BPS].copy()
    best_realistic = realistic.sort_values(
        ["total_return_pct", "sharpe", "profit_factor"],
        ascending=[False, False, False],
    ).iloc[0]
    best_by_mode_cost = (
        results.sort_values(
            ["mode", "cost_bps_per_side", "total_return_pct", "sharpe"],
            ascending=[True, True, False, False],
        )
        .groupby(["mode", "cost_bps_per_side"], as_index=False)
        .head(1)
        .reset_index(drop=True)
    )
    top_realistic = realistic.sort_values(
        ["total_return_pct", "sharpe", "profit_factor"],
        ascending=[False, False, False],
    ).head(12)

    stability = (
        realistic.groupby(["mode", "timeframe_label"])
        .agg(
            combos=("mode", "size"),
            positive=("total_return_pct", lambda s: int((s > 0).sum())),
            median_return=("total_return_pct", "median"),
            best_return=("total_return_pct", "max"),
            median_dd=("max_drawdown_pct", "median"),
            best_sharpe=("sharpe", "max"),
        )
        .reset_index()
        .sort_values(["mode", "timeframe_label"])
    )

    best_event_nocost = results[(results["mode"] == "event") & (results["cost_bps_per_side"] == 0.0)].sort_values(
        ["total_return_pct", "sharpe", "profit_factor"],
        ascending=[False, False, False],
    ).iloc[0]
    best_active_nocost = results[(results["mode"] == "active") & (results["cost_bps_per_side"] == 0.0)].sort_values(
        ["total_return_pct", "sharpe", "profit_factor"],
        ascending=[False, False, False],
    ).iloc[0]

    event_curve = cost_curve(
        results,
        "event",
        int(best_event_nocost["timeframe_min"]),
        float(best_event_nocost["stop_loss_pct"]),
        float(best_event_nocost["take_profit_pct"]),
    )
    active_curve = cost_curve(
        results,
        "active",
        int(best_active_nocost["timeframe_min"]),
        float(best_active_nocost["stop_loss_pct"]),
        float(best_active_nocost["take_profit_pct"]),
    )

    def fmt_percent_columns(frame: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
        out = frame.copy()
        for column in columns:
            out[column] = out[column].map(lambda x: f"{x:.2f}%")
        return out

    best_by_mode_cost_table = best_by_mode_cost[
        [
            "mode",
            "cost_bps_per_side",
            "timeframe_label",
            "stop_loss_pct",
            "take_profit_pct",
            "total_return_pct",
            "max_drawdown_pct",
            "sharpe",
            "trade_count",
        ]
    ].copy()
    best_by_mode_cost_table["cost_bps_per_side"] = best_by_mode_cost_table["cost_bps_per_side"].map(lambda x: f"{x:.1f}")
    best_by_mode_cost_table["stop_loss_pct"] = best_by_mode_cost_table["stop_loss_pct"].map(lambda x: f"{x:.2f}%")
    best_by_mode_cost_table["take_profit_pct"] = best_by_mode_cost_table["take_profit_pct"].map(lambda x: f"{x:.2f}%")
    best_by_mode_cost_table["total_return_pct"] = best_by_mode_cost_table["total_return_pct"].map(lambda x: f"{x:.2f}%")
    best_by_mode_cost_table["max_drawdown_pct"] = best_by_mode_cost_table["max_drawdown_pct"].map(lambda x: f"{x:.2f}%")
    best_by_mode_cost_table["sharpe"] = best_by_mode_cost_table["sharpe"].map(lambda x: f"{x:.2f}")
    best_by_mode_cost_table["trade_count"] = best_by_mode_cost_table["trade_count"].map(lambda x: f"{int(x)}")

    top_realistic_table = top_realistic[
        [
            "mode",
            "timeframe_label",
            "stop_loss_pct",
            "take_profit_pct",
            "total_return_pct",
            "max_drawdown_pct",
            "sharpe",
            "profit_factor",
            "trade_count",
            "win_rate_pct",
        ]
    ].copy()
    for column in ["stop_loss_pct", "take_profit_pct", "total_return_pct", "max_drawdown_pct", "win_rate_pct"]:
        top_realistic_table[column] = top_realistic_table[column].map(lambda x: f"{x:.2f}%")
    top_realistic_table["sharpe"] = top_realistic_table["sharpe"].map(lambda x: f"{x:.2f}")
    top_realistic_table["profit_factor"] = top_realistic_table["profit_factor"].map(lambda x: f"{x:.2f}")
    top_realistic_table["trade_count"] = top_realistic_table["trade_count"].map(lambda x: f"{int(x)}")

    stability_table = stability[
        ["mode", "timeframe_label", "positive", "combos", "median_return", "best_return", "median_dd", "best_sharpe"]
    ].copy()
    stability_table["positive"] = stability_table.apply(lambda row: f"{int(row['positive'])}/{int(row['combos'])}", axis=1)
    stability_table = stability_table.drop(columns=["combos"])
    for column in ["median_return", "best_return", "median_dd"]:
        stability_table[column] = stability_table[column].map(lambda x: f"{x:.2f}%")
    stability_table["best_sharpe"] = stability_table["best_sharpe"].map(lambda x: f"{x:.2f}")

    for table in (event_curve, active_curve):
        table["cost_bps_per_side"] = table["cost_bps_per_side"].map(lambda x: f"{x:.1f}")
        for column in ["stop_loss_pct", "take_profit_pct", "total_return_pct", "max_drawdown_pct"]:
            table[column] = table[column].map(lambda x: f"{x:.2f}%")
        table["sharpe"] = table["sharpe"].map(lambda x: f"{x:.2f}")
        table["trade_count"] = table["trade_count"].map(lambda x: f"{int(x)}")

    best_realistic_tf = prepared[int(best_realistic["timeframe_min"])]
    lines = [
        "# QQQ FVG Extended Comparison",
        "",
        "## What Changed",
        "",
        "- Added per-side cost/slippage scenarios: `0.0`, `1.0`, `2.0`, and `5.0` bps per side.",
        "- Added an `active` mode that stays aligned with the most recent still-active unfilled FVG after invalidating gaps the same way the Pine indicator deletes them.",
        "- Kept the earlier assumptions: regular-hours only, next-bar-open entries, one position at a time, session-close flattening, stop-first tie-break, and no leverage.",
        "",
        "## Best Realistic Setting (`2.0` bps per side)",
        "",
        f"- Mode: `{best_realistic['mode']}`.",
        f"- Timeframe: `{best_realistic['timeframe_label']}`.",
        f"- Stop loss: `{best_realistic['stop_loss_pct']:.2f}%`.",
        f"- Take profit: `{best_realistic['take_profit_pct']:.2f}%`.",
        f"- Total return: `{best_realistic['total_return_pct']:.2f}%`.",
        f"- CAGR: `{best_realistic['cagr_pct']:.2f}%`.",
        f"- Max drawdown: `{best_realistic['max_drawdown_pct']:.2f}%`.",
        f"- Sharpe: `{best_realistic['sharpe']:.2f}`.",
        f"- Profit factor: `{best_realistic['profit_factor']:.2f}`.",
        f"- Trades: `{int(best_realistic['trade_count'])}` with win rate `{best_realistic['win_rate_pct']:.2f}%`.",
        f"- Event signals on this timeframe: `{best_realistic_tf.bullish_event_count}` bullish / `{best_realistic_tf.bearish_event_count}` bearish.",
        f"- Active-state bars on this timeframe: `{best_realistic_tf.bullish_active_bars}` bullish / `{best_realistic_tf.bearish_active_bars}` bearish.",
        "",
        "## Best Setting By Mode And Cost",
        "",
        markdown_table(best_by_mode_cost_table),
        "",
        "## Top 12 Under `2.0` Bps Per Side",
        "",
        markdown_table(top_realistic_table),
        "",
        "## Cost Sensitivity Of Best Event Spec",
        "",
        markdown_table(event_curve),
        "",
        "## Cost Sensitivity Of Best Active Spec",
        "",
        markdown_table(active_curve),
        "",
        "## Robustness Under `2.0` Bps Per Side",
        "",
        markdown_table(stability_table),
        "",
        "## Output Files",
        "",
        f"- Full comparison grid: `{OUTPUTS['grid']}`.",
        f"- Summary: `{OUTPUTS['summary']}`.",
        f"- Best realistic overall trades: `{OUTPUTS['best_overall_realistic_trades']}`.",
        f"- Best realistic overall daily equity: `{OUTPUTS['best_overall_realistic_equity']}`.",
        f"- Best realistic event-mode trades: `{OUTPUTS['best_event_realistic_trades']}`.",
        f"- Best realistic active-mode trades: `{OUTPUTS['best_active_realistic_trades']}`.",
        f"- Runtime: `{runtime_seconds:.2f}` seconds.",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    start = perf_counter()
    minute_frame = load_minute_data(SOURCE)
    prepared = {minutes: prepare_signals(minute_frame, minutes) for minutes in TIMEFRAMES}

    rows: list[dict[str, float | int | str]] = []
    for minutes, tf_data in prepared.items():
        open_ = tf_data.bars["open"].to_numpy(dtype=np.float64)
        high = tf_data.bars["high"].to_numpy(dtype=np.float64)
        low = tf_data.bars["low"].to_numpy(dtype=np.float64)
        close = tf_data.bars["close"].to_numpy(dtype=np.float64)

        for mode in MODES:
            signal = tf_data.event_signal if mode == "event" else tf_data.active_signal
            for cost_bps_per_side in COST_BPS_PER_SIDE:
                for stop_loss_pct in STOP_LOSS_PCTS:
                    for take_profit_pct in TAKE_PROFIT_PCTS:
                        (
                            ending_equity,
                            total_return_pct,
                            cagr_pct,
                            max_drawdown_pct,
                            sharpe,
                            profit_factor,
                            trade_count,
                            win_count,
                            long_trades,
                            short_trades,
                            session_count,
                            avg_trade_return_pct,
                            avg_holding_bars,
                            exposure_pct,
                        ) = run_backtest_metrics_with_cost(
                            open_,
                            high,
                            low,
                            close,
                            signal,
                            tf_data.session_ids,
                            stop_loss_pct / 100.0,
                            take_profit_pct / 100.0,
                            cost_bps_per_side,
                        )

                        rows.append(
                            {
                                "mode": mode,
                                "timeframe_min": minutes,
                                "timeframe_label": f"{minutes}m",
                                "cost_bps_per_side": cost_bps_per_side,
                                "stop_loss_pct": stop_loss_pct,
                                "take_profit_pct": take_profit_pct,
                                "ending_equity": ending_equity,
                                "total_return_pct": total_return_pct,
                                "cagr_pct": cagr_pct,
                                "max_drawdown_pct": max_drawdown_pct,
                                "sharpe": sharpe,
                                "profit_factor": profit_factor,
                                "trade_count": trade_count,
                                "win_count": win_count,
                                "win_rate_pct": (win_count / trade_count * 100.0) if trade_count else 0.0,
                                "long_trades": long_trades,
                                "short_trades": short_trades,
                                "session_count": session_count,
                                "avg_trade_return_pct": avg_trade_return_pct,
                                "avg_holding_bars": avg_holding_bars,
                                "avg_holding_minutes": avg_holding_bars * minutes,
                                "exposure_pct": exposure_pct,
                                "bullish_event_count": tf_data.bullish_event_count,
                                "bearish_event_count": tf_data.bearish_event_count,
                                "bullish_active_bars": tf_data.bullish_active_bars,
                                "bearish_active_bars": tf_data.bearish_active_bars,
                                "bar_count": len(tf_data.bars),
                            }
                        )

    results = pd.DataFrame(rows).sort_values(
        ["cost_bps_per_side", "total_return_pct", "sharpe", "profit_factor"],
        ascending=[True, False, False, False],
    ).reset_index(drop=True)
    results.to_csv(OUTPUTS["grid"], index=False)

    realistic = results[results["cost_bps_per_side"] == REALISTIC_COST_BPS].copy()
    best_realistic_overall = realistic.sort_values(
        ["total_return_pct", "sharpe", "profit_factor"],
        ascending=[False, False, False],
    ).iloc[0]
    best_realistic_event = realistic[realistic["mode"] == "event"].sort_values(
        ["total_return_pct", "sharpe", "profit_factor"],
        ascending=[False, False, False],
    ).iloc[0]
    best_realistic_active = realistic[realistic["mode"] == "active"].sort_values(
        ["total_return_pct", "sharpe", "profit_factor"],
        ascending=[False, False, False],
    ).iloc[0]

    save_best_detail("best_overall_realistic", best_realistic_overall, prepared)
    save_best_detail("best_event_realistic", best_realistic_event, prepared)
    save_best_detail("best_active_realistic", best_realistic_active, prepared)

    runtime_seconds = perf_counter() - start
    summary = build_summary(results, prepared, runtime_seconds)
    OUTPUTS["summary"].write_text(summary + "\n", encoding="utf-8")
    print(summary)


if __name__ == "__main__":
    main()
