from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from time import perf_counter

import numpy as np
import pandas as pd
from numba import njit


BASE = Path(r"C:\Users\rabisaab\Downloads")
SOURCE = BASE / "QQQ_1min_20210308-20260308_sip (1).csv"
TIMEZONE = "America/New_York"
INITIAL_CAPITAL = 100_000.0

TIMEFRAMES = [1, 2, 3, 5, 10, 15, 30, 60]
STOP_LOSS_PCTS = [0.25, 0.50, 0.75, 1.00, 1.50, 2.00]
TAKE_PROFIT_PCTS = [0.25, 0.50, 0.75, 1.00, 1.50, 2.00, 3.00, 4.00]

OUTPUTS = {
    "grid": BASE / "qqq_fvg_grid_results.csv",
    "summary": BASE / "qqq_fvg_backtest_summary.md",
    "best_trades": BASE / "qqq_fvg_best_trades.csv",
    "best_equity": BASE / "qqq_fvg_best_daily_equity.csv",
}


@dataclass(frozen=True)
class PreparedTimeframe:
    minutes: int
    bars: pd.DataFrame
    signal: np.ndarray
    session_ids: np.ndarray
    bullish_signal_count: int
    bearish_signal_count: int


def load_minute_data(path: Path) -> pd.DataFrame:
    usecols = ["timestamp_utc", "open", "high", "low", "close", "volume"]
    frame = pd.read_csv(path, usecols=usecols)
    timestamp = pd.to_datetime(frame["timestamp_utc"], utc=True).dt.tz_convert(TIMEZONE)
    frame = frame.drop(columns=["timestamp_utc"])
    frame.index = timestamp
    frame = frame.sort_index()
    frame = frame.between_time("09:30", "15:59").copy()
    session_date = pd.Index(frame.index.date, name="session_date")
    frame["session_date"] = session_date
    counts = frame.groupby("session_date").size()
    full_sessions = counts[counts == 390].index
    frame = frame[frame["session_date"].isin(full_sessions)].copy()
    frame["session_date"] = pd.Index(frame.index.date, name="session_date")
    return frame


def resample_intraday(frame: pd.DataFrame, minutes: int) -> pd.DataFrame:
    if minutes == 1:
        return frame.copy()

    work = frame.reset_index(names="timestamp").copy()
    work["bar_number"] = work.groupby("session_date").cumcount()
    work["bucket"] = work["bar_number"] // minutes

    aggregated = (
        work.groupby(["session_date", "bucket"], sort=True)
        .agg(
            timestamp=("timestamp", "first"),
            open=("open", "first"),
            high=("high", "max"),
            low=("low", "min"),
            close=("close", "last"),
            volume=("volume", "sum"),
            bar_count=("open", "size"),
        )
        .reset_index()
        .drop(columns=["bucket"])
    )

    aggregated = aggregated.set_index("timestamp").sort_index()
    return aggregated


def compute_fvg_signal(bars: pd.DataFrame) -> np.ndarray:
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

    bullish = (
        (low > high_2)
        & (prev_close > high_2)
        & (bar_delta_pct > threshold)
    )
    bearish = (
        (high < low_2)
        & (prev_close < low_2)
        & ((-bar_delta_pct) > threshold)
    )

    signal = np.zeros(n, dtype=np.int8)
    signal[bullish] = 1
    signal[bearish] = -1
    signal[:2] = 0
    return signal


def prepare_timeframe(frame: pd.DataFrame, minutes: int) -> PreparedTimeframe:
    bars = resample_intraday(frame, minutes)
    signal = compute_fvg_signal(bars)
    session_ids, _ = pd.factorize(bars["session_date"], sort=True)
    return PreparedTimeframe(
        minutes=minutes,
        bars=bars,
        signal=signal,
        session_ids=session_ids.astype(np.int32),
        bullish_signal_count=int((signal == 1).sum()),
        bearish_signal_count=int((signal == -1).sum()),
    )


@njit(cache=True)
def run_backtest_metrics(
    open_: np.ndarray,
    high: np.ndarray,
    low: np.ndarray,
    close: np.ndarray,
    signal: np.ndarray,
    session_ids: np.ndarray,
    stop_loss_pct: float,
    take_profit_pct: float,
) -> tuple[float, float, float, float, float, float, int, int, int, int, int, float, float, float]:
    n = len(open_)
    session_count = int(session_ids[-1]) + 1 if n else 0
    eod_equity = np.zeros(session_count, dtype=np.float64)

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
                equity = base_equity * (1.0 + trade_return)
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
            base_equity = equity
            entry_bar = i
            pending_signal = 0

        exited = False
        if position != 0:
            if position == 1:
                stop_price = entry_price * (1.0 - stop_loss_pct)
                target_price = entry_price * (1.0 + take_profit_pct)
                hit_stop = low[i] <= stop_price
                hit_target = high[i] >= target_price
                if hit_stop:
                    exit_price = stop_price
                    exited = True
                elif hit_target:
                    exit_price = target_price
                    exited = True
            else:
                stop_price = entry_price * (1.0 + stop_loss_pct)
                target_price = entry_price * (1.0 - take_profit_pct)
                hit_stop = high[i] >= stop_price
                hit_target = low[i] <= target_price
                if hit_stop:
                    exit_price = stop_price
                    exited = True
                elif hit_target:
                    exit_price = target_price
                    exited = True

            if exited:
                trade_return = position * ((exit_price - entry_price) / entry_price)
                equity = base_equity * (1.0 + trade_return)
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
            equity = base_equity * (1.0 + trade_return)
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


def run_backtest_detailed(
    bars: pd.DataFrame,
    signal: np.ndarray,
    stop_loss_pct: float,
    take_profit_pct: float,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    open_ = bars["open"].to_numpy(dtype=np.float64)
    high = bars["high"].to_numpy(dtype=np.float64)
    low = bars["low"].to_numpy(dtype=np.float64)
    close = bars["close"].to_numpy(dtype=np.float64)
    session_ids, session_labels = pd.factorize(bars["session_date"], sort=True)
    timestamps = bars.index.to_numpy()

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
        trade_return = position * ((exit_price - entry_price) / entry_price)
        exit_equity = entry_equity * (1.0 + trade_return)
        trades.append(
            {
                "entry_time": pd.Timestamp(timestamps[entry_bar]),
                "exit_time": pd.Timestamp(timestamps[exit_bar]),
                "side": "long" if position == 1 else "short",
                "entry_price": entry_price,
                "exit_price": exit_price,
                "return_pct": trade_return * 100.0,
                "bars_held": exit_bar - entry_bar + (0 if reason == "reverse_open" else 1),
                "entry_reason": entry_reason,
                "exit_reason": reason,
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
            entry_bar = i
            entry_equity = equity
            entry_reason = "bullish_fvg" if pending_signal == 1 else "bearish_fvg"
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


def markdown_table(frame: pd.DataFrame) -> str:
    headers = list(frame.columns)
    rows = [headers]
    for _, row in frame.iterrows():
        rows.append([str(value) for value in row.tolist()])

    widths = [max(len(row[i]) for row in rows) for i in range(len(headers))]
    header_line = "| " + " | ".join(value.ljust(widths[i]) for i, value in enumerate(rows[0])) + " |"
    separator = "| " + " | ".join("-" * widths[i] for i in range(len(headers))) + " |"
    body = [
        "| " + " | ".join(value.ljust(widths[i]) for i, value in enumerate(row)) + " |"
        for row in rows[1:]
    ]
    return "\n".join([header_line, separator, *body])


def build_summary(
    results: pd.DataFrame,
    best: pd.Series,
    minute_frame: pd.DataFrame,
    prepared: dict[int, PreparedTimeframe],
    runtime_seconds: float,
) -> str:
    top_overall = results.sort_values(
        ["total_return_pct", "sharpe", "profit_factor"],
        ascending=[False, False, False],
    ).head(15)
    best_by_timeframe = (
        results.sort_values(
            ["timeframe_min", "total_return_pct", "sharpe"],
            ascending=[True, False, False],
        )
        .groupby("timeframe_min", as_index=False)
        .head(1)
        .sort_values("timeframe_min")
    )

    overall_table = top_overall[
        [
            "timeframe_label",
            "stop_loss_pct",
            "take_profit_pct",
            "total_return_pct",
            "cagr_pct",
            "max_drawdown_pct",
            "sharpe",
            "profit_factor",
            "trade_count",
            "win_rate_pct",
        ]
    ].copy()
    overall_table["stop_loss_pct"] = overall_table["stop_loss_pct"].map(lambda x: f"{x:.2f}%")
    overall_table["take_profit_pct"] = overall_table["take_profit_pct"].map(lambda x: f"{x:.2f}%")
    overall_table["total_return_pct"] = overall_table["total_return_pct"].map(lambda x: f"{x:.2f}%")
    overall_table["cagr_pct"] = overall_table["cagr_pct"].map(lambda x: f"{x:.2f}%")
    overall_table["max_drawdown_pct"] = overall_table["max_drawdown_pct"].map(lambda x: f"{x:.2f}%")
    overall_table["sharpe"] = overall_table["sharpe"].map(lambda x: f"{x:.2f}")
    overall_table["profit_factor"] = overall_table["profit_factor"].map(lambda x: f"{x:.2f}")
    overall_table["trade_count"] = overall_table["trade_count"].map(lambda x: f"{int(x)}")
    overall_table["win_rate_pct"] = overall_table["win_rate_pct"].map(lambda x: f"{x:.2f}%")

    timeframe_table = best_by_timeframe[
        [
            "timeframe_label",
            "stop_loss_pct",
            "take_profit_pct",
            "total_return_pct",
            "max_drawdown_pct",
            "sharpe",
            "trade_count",
        ]
    ].copy()
    timeframe_table["stop_loss_pct"] = timeframe_table["stop_loss_pct"].map(lambda x: f"{x:.2f}%")
    timeframe_table["take_profit_pct"] = timeframe_table["take_profit_pct"].map(lambda x: f"{x:.2f}%")
    timeframe_table["total_return_pct"] = timeframe_table["total_return_pct"].map(lambda x: f"{x:.2f}%")
    timeframe_table["max_drawdown_pct"] = timeframe_table["max_drawdown_pct"].map(lambda x: f"{x:.2f}%")
    timeframe_table["sharpe"] = timeframe_table["sharpe"].map(lambda x: f"{x:.2f}")
    timeframe_table["trade_count"] = timeframe_table["trade_count"].map(lambda x: f"{int(x)}")

    best_tf = prepared[int(best["timeframe_min"])]
    lines = [
        "# QQQ LuxAlgo FVG Backtest",
        "",
        "## Extracted Fair Value Gap Logic",
        "",
        "The Pine logic used for each timeframe bar was translated as:",
        "",
        "```text",
        "bar_delta_pct[t] = (close[t-1] - open[t-1]) / (open[t-1] * 100)",
        "auto_threshold[t] = 2 * cumulative_abs(bar_delta_pct) / bar_index",
        "bullish_fvg[t] = low[t] > high[t-2] and close[t-1] > high[t-2] and bar_delta_pct[t] > auto_threshold[t]",
        "bearish_fvg[t] = high[t] < low[t-2] and close[t-1] < low[t-2] and -bar_delta_pct[t] > auto_threshold[t]",
        "```",
        "",
        "## Backtest Assumptions",
        "",
        f"- Source file: `{SOURCE}`.",
        f"- Data window after filtering incomplete sessions: `{minute_frame.index.min()}` through `{minute_frame.index.max()}`.",
        "- Session filter: regular trading hours only, `09:30-15:59` ET, and positions are forced flat at each session close.",
        "- Entry timing: next bar open after a new bullish or bearish FVG forms.",
        "- Direction: long on bullish FVG, short on bearish FVG, one position at a time.",
        "- Exit timing: stop loss, take profit, opposite-signal reversal on next bar open, or session close.",
        "- Intrabar tie-break: if both stop and target are touched in the same bar, the stop is assumed to fill first.",
        "- Trading costs and slippage: not included.",
        f"- Grid size: `{len(TIMEFRAMES)} timeframes x {len(STOP_LOSS_PCTS)} stop values x {len(TAKE_PROFIT_PCTS)} target values = {len(results)}` combinations.",
        "",
        "## Best Overall Setting",
        "",
        f"- Timeframe: `{best['timeframe_label']}`.",
        f"- Stop loss: `{best['stop_loss_pct']:.2f}%`.",
        f"- Take profit: `{best['take_profit_pct']:.2f}%`.",
        f"- Total return: `{best['total_return_pct']:.2f}%` on `{INITIAL_CAPITAL:,.0f}` starting capital.",
        f"- CAGR: `{best['cagr_pct']:.2f}%`.",
        f"- Max drawdown: `{best['max_drawdown_pct']:.2f}%`.",
        f"- Sharpe: `{best['sharpe']:.2f}`.",
        f"- Profit factor: `{best['profit_factor']:.2f}`.",
        f"- Trades: `{int(best['trade_count'])}` with win rate `{best['win_rate_pct']:.2f}%`.",
        f"- Average trade: `{best['avg_trade_return_pct']:.3f}%`.",
        f"- Average holding time: `{best['avg_holding_bars'] * int(best['timeframe_min']):.1f}` minutes.",
        f"- Bullish signals on this timeframe: `{best_tf.bullish_signal_count}`.",
        f"- Bearish signals on this timeframe: `{best_tf.bearish_signal_count}`.",
        "",
        "## Top 15 Overall",
        "",
        markdown_table(overall_table),
        "",
        "## Best By Timeframe",
        "",
        markdown_table(timeframe_table),
        "",
        "## Output Files",
        "",
        f"- Full grid: `{OUTPUTS['grid']}`.",
        f"- Best trade ledger: `{OUTPUTS['best_trades']}`.",
        f"- Best daily equity: `{OUTPUTS['best_equity']}`.",
        f"- Runtime: `{runtime_seconds:.2f}` seconds.",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    start = perf_counter()
    minute_frame = load_minute_data(SOURCE)
    prepared = {minutes: prepare_timeframe(minute_frame, minutes) for minutes in TIMEFRAMES}

    rows: list[dict[str, float | int | str]] = []
    for minutes, tf_data in prepared.items():
        open_ = tf_data.bars["open"].to_numpy(dtype=np.float64)
        high = tf_data.bars["high"].to_numpy(dtype=np.float64)
        low = tf_data.bars["low"].to_numpy(dtype=np.float64)
        close = tf_data.bars["close"].to_numpy(dtype=np.float64)

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
                ) = run_backtest_metrics(
                    open_,
                    high,
                    low,
                    close,
                    tf_data.signal,
                    tf_data.session_ids,
                    stop_loss_pct / 100.0,
                    take_profit_pct / 100.0,
                )

                rows.append(
                    {
                        "timeframe_min": minutes,
                        "timeframe_label": f"{minutes}m",
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
                        "bullish_signal_count": tf_data.bullish_signal_count,
                        "bearish_signal_count": tf_data.bearish_signal_count,
                        "bar_count": len(tf_data.bars),
                    }
                )

    results = pd.DataFrame(rows).sort_values(
        ["total_return_pct", "sharpe", "profit_factor"],
        ascending=[False, False, False],
    ).reset_index(drop=True)
    results.to_csv(OUTPUTS["grid"], index=False)

    best = results.iloc[0]
    best_tf = prepared[int(best["timeframe_min"])]
    trades_df, equity_df = run_backtest_detailed(
        best_tf.bars,
        best_tf.signal,
        float(best["stop_loss_pct"]) / 100.0,
        float(best["take_profit_pct"]) / 100.0,
    )
    trades_df.to_csv(OUTPUTS["best_trades"], index=False)
    equity_df.to_csv(OUTPUTS["best_equity"], index=False)

    runtime_seconds = perf_counter() - start
    summary = build_summary(results, best, minute_frame, prepared, runtime_seconds)
    OUTPUTS["summary"].write_text(summary + "\n", encoding="utf-8")

    print(summary)


if __name__ == "__main__":
    main()
