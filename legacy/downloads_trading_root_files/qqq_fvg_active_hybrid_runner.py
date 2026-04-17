from __future__ import annotations

from pathlib import Path
from time import perf_counter

import numpy as np
import pandas as pd
from numba import njit

from qqq_fvg_backtest_runner import BASE, load_minute_data, markdown_table
from qqq_fvg_extended_runner import run_backtest_detailed_with_cost, run_backtest_metrics_with_cost
from qqq_fvg_active_fine_runner import CANDIDATES, COST_BPS_PER_SIDE, REALISTIC_COST_BPS, SOURCE
from qqq_fvg_active_variants_runner import prepare_timeframe_variants


ENTRY_MODES = ["always_on_active", "change_only", "hybrid_reentry_once"]

OUTPUTS = {
    "grid": BASE / "qqq_fvg_active_hybrid_grid_results.csv",
    "summary": BASE / "qqq_fvg_active_hybrid_summary.md",
    "best_by_candidate": BASE / "qqq_fvg_active_hybrid_best_by_candidate.csv",
    "best_realistic_trades": BASE / "qqq_fvg_active_hybrid_best_realistic_trades.csv",
    "best_realistic_equity": BASE / "qqq_fvg_active_hybrid_best_realistic_daily_equity.csv",
    "best_hybrid_realistic_trades": BASE / "qqq_fvg_active_hybrid_best_hybrid_trades.csv",
    "best_hybrid_realistic_equity": BASE / "qqq_fvg_active_hybrid_best_hybrid_daily_equity.csv",
}


def build_change_only_signal(signal: np.ndarray) -> np.ndarray:
    out = np.zeros_like(signal)
    if len(signal) == 0:
        return out

    out[0] = signal[0] if signal[0] != 0 else 0
    prev = signal[0]
    for i in range(1, len(signal)):
        current = signal[i]
        if current != 0 and current != prev:
            out[i] = current
        prev = current
    return out


@njit(cache=True)
def run_hybrid_backtest_metrics_with_cost(
    open_: np.ndarray,
    high: np.ndarray,
    low: np.ndarray,
    close: np.ndarray,
    active_signal: np.ndarray,
    session_ids: np.ndarray,
    stop_loss_pct: float,
    take_profit_pct: float,
    cost_bps_per_side: float,
) -> tuple[float, float, float, float, float, float, int, int, int, int, int, float, float, float]:
    n = len(open_)
    session_count = int(session_ids[-1]) + 1 if n else 0
    eod_equity = np.zeros(session_count, dtype=np.float64)

    cost_pct = cost_bps_per_side / 10000.0
    equity = 100_000.0
    peak_equity = 100_000.0
    max_drawdown = 0.0

    position = 0
    pending_signal = 0
    entry_price = 0.0
    base_equity = 100_000.0
    entry_bar = -1

    trade_count = 0
    win_count = 0
    long_trades = 0
    short_trades = 0
    bars_in_position = 0
    holding_bars_total = 0

    gross_profit = 0.0
    gross_loss = 0.0

    prev_bias = 0
    reentry_used = False

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

        stop_exit = False
        exited = False
        if position != 0:
            if position == 1:
                stop_price = entry_price * (1.0 - stop_loss_pct)
                target_price = entry_price * (1.0 + take_profit_pct)
                if low[i] <= stop_price:
                    exit_price = stop_price
                    stop_exit = True
                    exited = True
                elif high[i] >= target_price:
                    exit_price = target_price
                    exited = True
            else:
                stop_price = entry_price * (1.0 + stop_loss_pct)
                target_price = entry_price * (1.0 - take_profit_pct)
                if high[i] >= stop_price:
                    exit_price = stop_price
                    stop_exit = True
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

        current_bias = int(active_signal[i])
        if not last_bar_of_session:
            changed = current_bias != prev_bias
            if changed:
                reentry_used = False

            pending_signal = 0
            if current_bias != 0 and changed:
                if position == 0 or current_bias != position:
                    pending_signal = current_bias
            elif stop_exit and current_bias != 0 and current_bias == prev_bias and not reentry_used and position == 0:
                pending_signal = current_bias
                reentry_used = True
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

        prev_bias = current_bias

    daily_returns = np.zeros(session_count, dtype=np.float64)
    if session_count > 0:
        daily_returns[0] = (eod_equity[0] / 100_000.0) - 1.0
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

    total_return_pct = ((equity / 100_000.0) - 1.0) * 100.0
    cagr = 0.0
    if session_count > 0 and equity > 0.0:
        cagr = ((equity / 100_000.0) ** (252.0 / session_count) - 1.0) * 100.0

    avg_trade_return_pct = ((gross_profit - gross_loss) / trade_count) * 100.0 if trade_count else 0.0
    exposure_pct = (bars_in_position / n) * 100.0 if n else 0.0
    avg_holding_bars = holding_bars_total / trade_count if trade_count else 0.0
    profit_factor = gross_profit / gross_loss if gross_loss > 0.0 else 0.0

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


def run_hybrid_backtest_detailed_with_cost(
    bars: pd.DataFrame,
    active_signal: np.ndarray,
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

    equity = 100_000.0
    position = 0
    pending_signal = 0
    pending_entry_reason = ""
    entry_price = 0.0
    entry_bar = -1
    entry_equity = 100_000.0
    entry_reason = ""
    trades: list[dict[str, object]] = []
    daily_equity: list[dict[str, object]] = []

    prev_bias = 0
    reentry_used = False
    equity_before_entry_for_trade = 100_000.0

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
            entry_reason = pending_entry_reason
            pending_signal = 0
            pending_entry_reason = ""

        current_exit_reason = ""
        if position != 0:
            if position == 1:
                stop_price = entry_price * (1.0 - stop_loss_pct)
                target_price = entry_price * (1.0 + take_profit_pct)
                if low[i] <= stop_price:
                    current_exit_reason = "stop_loss"
                    close_trade(i, stop_price, current_exit_reason)
                elif high[i] >= target_price:
                    current_exit_reason = "take_profit"
                    close_trade(i, target_price, current_exit_reason)
            else:
                stop_price = entry_price * (1.0 + stop_loss_pct)
                target_price = entry_price * (1.0 - take_profit_pct)
                if high[i] >= stop_price:
                    current_exit_reason = "stop_loss"
                    close_trade(i, stop_price, current_exit_reason)
                elif low[i] <= target_price:
                    current_exit_reason = "take_profit"
                    close_trade(i, target_price, current_exit_reason)

        if last_bar_of_session and position != 0:
            current_exit_reason = "session_close"
            close_trade(i, close[i], current_exit_reason)

        current_bias = int(active_signal[i])
        if not last_bar_of_session:
            changed = current_bias != prev_bias
            if changed:
                reentry_used = False

            pending_signal = 0
            pending_entry_reason = ""
            if current_bias != 0 and changed:
                if position == 0 or current_bias != position:
                    pending_signal = current_bias
                    pending_entry_reason = "bias_change"
            elif current_exit_reason == "stop_loss" and current_bias != 0 and current_bias == prev_bias and not reentry_used and position == 0:
                pending_signal = current_bias
                reentry_used = True
                pending_entry_reason = "stop_reentry"
        else:
            pending_signal = 0
            pending_entry_reason = ""

        if last_bar_of_session:
            daily_equity.append(
                {
                    "session_date": pd.Timestamp(session_labels[session_ids[i]]),
                    "equity": equity,
                }
            )

        prev_bias = current_bias

    trades_df = pd.DataFrame(trades)
    equity_df = pd.DataFrame(daily_equity)
    return trades_df, equity_df


def build_summary(results: pd.DataFrame, runtime_seconds: float) -> str:
    realistic = results[results["cost_bps_per_side"] == REALISTIC_COST_BPS].copy()
    best_realistic = realistic.sort_values(
        ["total_return_pct", "sharpe", "profit_factor"],
        ascending=[False, False, False],
    ).iloc[0]

    best_by_candidate = (
        results.sort_values(
            ["candidate_id", "entry_mode", "cost_bps_per_side", "total_return_pct", "sharpe"],
            ascending=[True, True, True, False, False],
        )
        .groupby(["candidate_id", "entry_mode", "cost_bps_per_side"], as_index=False)
        .head(1)
        .reset_index(drop=True)
    )

    realistic_top = realistic.sort_values(
        ["total_return_pct", "sharpe", "profit_factor"],
        ascending=[False, False, False],
    ).head(24)

    entry_mode_compare = (
        realistic.groupby(["candidate_id", "entry_mode"])
        .agg(
            positive=("total_return_pct", lambda s: int((s > 0).sum())),
            combos=("candidate_id", "size"),
            median_return=("total_return_pct", "median"),
            best_return=("total_return_pct", "max"),
            median_dd=("max_drawdown_pct", "median"),
            best_sharpe=("sharpe", "max"),
            median_trades=("trade_count", "median"),
        )
        .reset_index()
        .sort_values(["candidate_id", "best_return"], ascending=[True, False])
    )

    by_candidate_view = best_by_candidate[
        [
            "candidate_id",
            "entry_mode",
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
    by_candidate_view["cost_bps_per_side"] = by_candidate_view["cost_bps_per_side"].map(lambda x: f"{x:.1f}")
    for column in ["stop_loss_pct", "take_profit_pct", "total_return_pct", "max_drawdown_pct"]:
        by_candidate_view[column] = by_candidate_view[column].map(lambda x: f"{x:.2f}%")
    by_candidate_view["sharpe"] = by_candidate_view["sharpe"].map(lambda x: f"{x:.2f}")
    by_candidate_view["trade_count"] = by_candidate_view["trade_count"].map(lambda x: f"{int(x)}")

    top_view = realistic_top[
        [
            "candidate_id",
            "entry_mode",
            "timeframe_label",
            "stop_loss_pct",
            "take_profit_pct",
            "total_return_pct",
            "max_drawdown_pct",
            "sharpe",
            "profit_factor",
            "trade_count",
            "win_rate_pct",
            "exposure_pct",
        ]
    ].copy()
    for column in [
        "stop_loss_pct",
        "take_profit_pct",
        "total_return_pct",
        "max_drawdown_pct",
        "win_rate_pct",
        "exposure_pct",
    ]:
        top_view[column] = top_view[column].map(lambda x: f"{x:.2f}%")
    top_view["sharpe"] = top_view["sharpe"].map(lambda x: f"{x:.2f}")
    top_view["profit_factor"] = top_view["profit_factor"].map(lambda x: f"{x:.2f}")
    top_view["trade_count"] = top_view["trade_count"].map(lambda x: f"{int(x)}")

    entry_mode_view = entry_mode_compare.copy()
    entry_mode_view["positive"] = entry_mode_view.apply(
        lambda row: f"{int(row['positive'])}/{int(row['combos'])}",
        axis=1,
    )
    entry_mode_view = entry_mode_view.drop(columns=["combos"])
    for column in ["median_return", "best_return", "median_dd"]:
        entry_mode_view[column] = entry_mode_view[column].map(lambda x: f"{x:.2f}%")
    entry_mode_view["best_sharpe"] = entry_mode_view["best_sharpe"].map(lambda x: f"{x:.2f}")
    entry_mode_view["median_trades"] = entry_mode_view["median_trades"].map(lambda x: f"{x:.0f}")

    lines = [
        "# QQQ Active FVG Hybrid Re-entry Study",
        "",
        "## Scope",
        "",
        "- Candidates: `active_dominant_count_session_reset` on `10m` and `active_uncontested_session_reset` on `15m`.",
        "- Entry modes:",
        "  - `always_on_active`: keep re-entering while the active bias persists.",
        "  - `change_only`: enter only when the active bias changes to a new non-zero state.",
        "  - `hybrid_reentry_once`: behave like `change_only`, but permit one same-direction re-entry inside the same bias regime after a stop-out.",
        f"- Costs tested: `{', '.join(f'{x:.1f}' for x in COST_BPS_PER_SIDE)}` bps per side.",
        "",
        "## Best Realistic Result (`2.0` Bps Per Side)",
        "",
        f"- Candidate: `{best_realistic['candidate_id']}`.",
        f"- Variant: `{best_realistic['variant']}`.",
        f"- Entry mode: `{best_realistic['entry_mode']}`.",
        f"- Timeframe: `{best_realistic['timeframe_label']}`.",
        f"- Stop loss: `{best_realistic['stop_loss_pct']:.2f}%`.",
        f"- Take profit: `{best_realistic['take_profit_pct']:.2f}%`.",
        f"- Total return: `{best_realistic['total_return_pct']:.2f}%`.",
        f"- CAGR: `{best_realistic['cagr_pct']:.2f}%`.",
        f"- Max drawdown: `{best_realistic['max_drawdown_pct']:.2f}%`.",
        f"- Sharpe: `{best_realistic['sharpe']:.2f}`.",
        f"- Profit factor: `{best_realistic['profit_factor']:.2f}`.",
        f"- Trades: `{int(best_realistic['trade_count'])}` with win rate `{best_realistic['win_rate_pct']:.2f}%`.",
        "",
        "## Best By Candidate, Entry Mode, And Cost",
        "",
        markdown_table(by_candidate_view),
        "",
        "## Top 24 Under `2.0` Bps Per Side",
        "",
        markdown_table(top_view),
        "",
        "## Entry Mode Comparison At `2.0` Bps",
        "",
        markdown_table(entry_mode_view),
        "",
        "## Output Files",
        "",
        f"- Full grid: `{OUTPUTS['grid']}`.",
        f"- Best-by-candidate table: `{OUTPUTS['best_by_candidate']}`.",
        f"- Best realistic trades: `{OUTPUTS['best_realistic_trades']}`.",
        f"- Best realistic daily equity: `{OUTPUTS['best_realistic_equity']}`.",
        f"- Best hybrid-specific trades: `{OUTPUTS['best_hybrid_realistic_trades']}`.",
        f"- Best hybrid-specific daily equity: `{OUTPUTS['best_hybrid_realistic_equity']}`.",
        f"- Runtime: `{runtime_seconds:.2f}` seconds.",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    start = perf_counter()
    minute_frame = load_minute_data(SOURCE)
    prepared = {candidate.timeframe_min: prepare_timeframe_variants(minute_frame, candidate.timeframe_min) for candidate in CANDIDATES}

    rows: list[dict[str, float | int | str]] = []
    for candidate in CANDIDATES:
        tf_data = prepared[candidate.timeframe_min]
        bars = tf_data.bars
        open_ = bars["open"].to_numpy(dtype=np.float64)
        high = bars["high"].to_numpy(dtype=np.float64)
        low = bars["low"].to_numpy(dtype=np.float64)
        close = bars["close"].to_numpy(dtype=np.float64)

        base_signal = tf_data.signals[candidate.variant]
        signals = {
            "always_on_active": base_signal,
            "change_only": build_change_only_signal(base_signal),
        }

        for entry_mode in ENTRY_MODES:
            bullish_signal_count = int((base_signal == 1).sum())
            bearish_signal_count = int((base_signal == -1).sum())
            for cost_bps_per_side in COST_BPS_PER_SIDE:
                for stop_loss_pct in candidate.stop_values:
                    for take_profit_pct in candidate.target_values:
                        if entry_mode == "always_on_active":
                            signal = signals["always_on_active"]
                            metrics = run_backtest_metrics_with_cost(
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
                        elif entry_mode == "change_only":
                            signal = signals["change_only"]
                            metrics = run_backtest_metrics_with_cost(
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
                        else:
                            metrics = run_hybrid_backtest_metrics_with_cost(
                                open_,
                                high,
                                low,
                                close,
                                base_signal,
                                tf_data.session_ids,
                                stop_loss_pct / 100.0,
                                take_profit_pct / 100.0,
                                cost_bps_per_side,
                            )

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
                        ) = metrics

                        rows.append(
                            {
                                "candidate_id": candidate.candidate_id,
                                "variant": candidate.variant,
                                "entry_mode": entry_mode,
                                "timeframe_min": candidate.timeframe_min,
                                "timeframe_label": f"{candidate.timeframe_min}m",
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
                                "avg_holding_minutes": avg_holding_bars * candidate.timeframe_min,
                                "exposure_pct": exposure_pct,
                                "bullish_signal_count": bullish_signal_count,
                                "bearish_signal_count": bearish_signal_count,
                            }
                        )

    results = pd.DataFrame(rows).sort_values(
        ["cost_bps_per_side", "total_return_pct", "sharpe", "profit_factor"],
        ascending=[True, False, False, False],
    ).reset_index(drop=True)
    results.to_csv(OUTPUTS["grid"], index=False)

    best_by_candidate = (
        results.sort_values(
            ["candidate_id", "entry_mode", "cost_bps_per_side", "total_return_pct", "sharpe"],
            ascending=[True, True, True, False, False],
        )
        .groupby(["candidate_id", "entry_mode", "cost_bps_per_side"], as_index=False)
        .head(1)
        .reset_index(drop=True)
    )
    best_by_candidate.to_csv(OUTPUTS["best_by_candidate"], index=False)

    realistic = results[results["cost_bps_per_side"] == REALISTIC_COST_BPS].copy()
    best_realistic = realistic.sort_values(
        ["total_return_pct", "sharpe", "profit_factor"],
        ascending=[False, False, False],
    ).iloc[0]
    best_hybrid_realistic = realistic[realistic["entry_mode"] == "hybrid_reentry_once"].sort_values(
        ["total_return_pct", "sharpe", "profit_factor"],
        ascending=[False, False, False],
    ).iloc[0]

    best_candidate = next(candidate for candidate in CANDIDATES if candidate.candidate_id == best_realistic["candidate_id"])
    best_tf = prepared[best_candidate.timeframe_min]
    base_signal = best_tf.signals[best_candidate.variant]
    if best_realistic["entry_mode"] == "always_on_active":
        best_signal = base_signal
        trades_df, equity_df = run_backtest_detailed_with_cost(
            best_tf.bars,
            best_signal,
            float(best_realistic["stop_loss_pct"]) / 100.0,
            float(best_realistic["take_profit_pct"]) / 100.0,
            float(best_realistic["cost_bps_per_side"]),
            f"{best_realistic['variant']}|always_on_active",
        )
    elif best_realistic["entry_mode"] == "change_only":
        best_signal = build_change_only_signal(base_signal)
        trades_df, equity_df = run_backtest_detailed_with_cost(
            best_tf.bars,
            best_signal,
            float(best_realistic["stop_loss_pct"]) / 100.0,
            float(best_realistic["take_profit_pct"]) / 100.0,
            float(best_realistic["cost_bps_per_side"]),
            f"{best_realistic['variant']}|change_only",
        )
    else:
        trades_df, equity_df = run_hybrid_backtest_detailed_with_cost(
            best_tf.bars,
            base_signal,
            float(best_realistic["stop_loss_pct"]) / 100.0,
            float(best_realistic["take_profit_pct"]) / 100.0,
            float(best_realistic["cost_bps_per_side"]),
            f"{best_realistic['variant']}|hybrid_reentry_once",
        )

    trades_df.to_csv(OUTPUTS["best_realistic_trades"], index=False)
    equity_df.to_csv(OUTPUTS["best_realistic_equity"], index=False)

    hybrid_candidate = next(candidate for candidate in CANDIDATES if candidate.candidate_id == best_hybrid_realistic["candidate_id"])
    hybrid_tf = prepared[hybrid_candidate.timeframe_min]
    hybrid_base_signal = hybrid_tf.signals[hybrid_candidate.variant]
    hybrid_trades_df, hybrid_equity_df = run_hybrid_backtest_detailed_with_cost(
        hybrid_tf.bars,
        hybrid_base_signal,
        float(best_hybrid_realistic["stop_loss_pct"]) / 100.0,
        float(best_hybrid_realistic["take_profit_pct"]) / 100.0,
        float(best_hybrid_realistic["cost_bps_per_side"]),
        f"{best_hybrid_realistic['variant']}|hybrid_reentry_once",
    )
    hybrid_trades_df.to_csv(OUTPUTS["best_hybrid_realistic_trades"], index=False)
    hybrid_equity_df.to_csv(OUTPUTS["best_hybrid_realistic_equity"], index=False)

    runtime_seconds = perf_counter() - start
    summary = build_summary(results, runtime_seconds)
    OUTPUTS["summary"].write_text(summary + "\n", encoding="utf-8")
    print(summary)


if __name__ == "__main__":
    main()
