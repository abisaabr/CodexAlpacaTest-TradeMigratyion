from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter

import numpy as np
import pandas as pd
from numba import njit

from qqq_fvg_backtest_runner import BASE, load_minute_data, markdown_table
from qqq_fvg_active_hybrid_runner import build_change_only_signal
from qqq_fvg_active_variants_runner import prepare_timeframe_variants


SOURCE = BASE / "QQQ_1min_20210308-20260308_sip (1).csv"
FROZEN_FILE = BASE / "qqq_fvg_frozen_winners.md"
COST_BPS_PER_SIDE = [0.0, 2.0]
REALISTIC_COST_BPS = 2.0

START_OFFSETS_MIN = [0, 30, 60]
CUTOFFS = [None, "14:30"]
TREND_FILTERS = ["none", "vwap", "ema10", "vwap_ema10"]

OUTPUTS = {
    "grid": BASE / "qqq_fvg_frozen_layered_results.csv",
    "summary": BASE / "qqq_fvg_frozen_layered_summary.md",
    "best_by_winner": BASE / "qqq_fvg_frozen_layered_best_by_winner.csv",
    "best_realistic_trades": BASE / "qqq_fvg_frozen_layered_best_realistic_trades.csv",
    "best_realistic_equity": BASE / "qqq_fvg_frozen_layered_best_realistic_daily_equity.csv",
}


@dataclass(frozen=True)
class FrozenWinner:
    winner_id: str
    variant: str
    timeframe_min: int
    entry_mode: str
    stop_loss_pct: float
    take_profit_pct: float


FROZEN_WINNERS = [
    FrozenWinner(
        winner_id="dominant_count_10m_always_on",
        variant="active_dominant_count_session_reset",
        timeframe_min=10,
        entry_mode="always_on_active",
        stop_loss_pct=1.25,
        take_profit_pct=3.50,
    ),
    FrozenWinner(
        winner_id="uncontested_15m_hybrid",
        variant="active_uncontested_session_reset",
        timeframe_min=15,
        entry_mode="hybrid_reentry_once",
        stop_loss_pct=0.50,
        take_profit_pct=4.25,
    ),
]


@dataclass(frozen=True)
class PreparedWinner:
    winner: FrozenWinner
    bars: pd.DataFrame
    session_ids: np.ndarray
    base_signal: np.ndarray
    bullish_signal_count: int
    bearish_signal_count: int
    allow_long_by_layer: dict[str, np.ndarray]
    allow_short_by_layer: dict[str, np.ndarray]


def hhmm_to_minutes(value: str) -> int:
    hour, minute = value.split(":")
    return int(hour) * 60 + int(minute)


def layer_id(start_offset_min: int, cutoff: str | None, trend_filter: str) -> str:
    cutoff_label = cutoff.replace(":", "") if cutoff else "none"
    return f"start_{start_offset_min:02d}_cutoff_{cutoff_label}_trend_{trend_filter}"


BASE_LAYER_ID = layer_id(0, None, "none")


def compute_layer_permissions(
    bars: pd.DataFrame,
    start_offset_min: int,
    cutoff: str | None,
    trend_filter: str,
) -> tuple[np.ndarray, np.ndarray]:
    entry_minutes = bars["entry_clock_minute"].to_numpy(dtype=np.int32)
    start_minute = 9 * 60 + 30 + start_offset_min
    within = entry_minutes >= start_minute
    if cutoff is not None:
        within &= entry_minutes <= hhmm_to_minutes(cutoff)
    within &= entry_minutes >= 0

    close = bars["close"].to_numpy(dtype=np.float64)
    vwap = bars["session_vwap"].to_numpy(dtype=np.float64)
    ema10 = bars["ema10"].to_numpy(dtype=np.float64)
    ema10_prev = bars["ema10_prev"].to_numpy(dtype=np.float64)

    allow_long = within.copy()
    allow_short = within.copy()

    if trend_filter in {"vwap", "vwap_ema10"}:
        allow_long &= close > vwap
        allow_short &= close < vwap

    if trend_filter in {"ema10", "vwap_ema10"}:
        allow_long &= (close > ema10) & (ema10 > ema10_prev)
        allow_short &= (close < ema10) & (ema10 < ema10_prev)

    allow_long &= np.isfinite(close)
    allow_short &= np.isfinite(close)
    return allow_long.astype(np.bool_), allow_short.astype(np.bool_)


def prepare_winner(minute_frame: pd.DataFrame, winner: FrozenWinner) -> PreparedWinner:
    tf_data = prepare_timeframe_variants(minute_frame, winner.timeframe_min)
    bars = tf_data.bars.copy()
    clock_minutes = (bars.index.hour * 60 + bars.index.minute).to_numpy(dtype=np.int32)
    session_values = bars["session_date"].to_numpy()
    entry_clock_minute = np.full(len(bars), -1, dtype=np.int32)
    if len(bars) > 1:
        same_session_next = session_values[:-1] == session_values[1:]
        entry_clock_minute[:-1] = np.where(same_session_next, clock_minutes[1:], -1)
    bars["entry_clock_minute"] = entry_clock_minute
    typical_price = (bars["high"] + bars["low"] + bars["close"]) / 3.0
    price_volume = typical_price * bars["volume"]
    bars["session_vwap"] = price_volume.groupby(bars["session_date"]).cumsum() / bars["volume"].groupby(bars["session_date"]).cumsum()
    bars["ema10"] = bars["close"].ewm(span=10, adjust=False).mean()
    bars["ema10_prev"] = bars["ema10"].shift(1)

    base_signal = tf_data.signals[winner.variant]
    if winner.entry_mode == "change_only":
        base_signal = build_change_only_signal(base_signal)

    allow_long_by_layer: dict[str, np.ndarray] = {}
    allow_short_by_layer: dict[str, np.ndarray] = {}
    for start_offset_min in START_OFFSETS_MIN:
        for cutoff in CUTOFFS:
            for trend_filter in TREND_FILTERS:
                key = layer_id(start_offset_min, cutoff, trend_filter)
                allow_long, allow_short = compute_layer_permissions(bars, start_offset_min, cutoff, trend_filter)
                allow_long_by_layer[key] = allow_long
                allow_short_by_layer[key] = allow_short

    return PreparedWinner(
        winner=winner,
        bars=bars,
        session_ids=tf_data.session_ids,
        base_signal=base_signal,
        bullish_signal_count=int((base_signal == 1).sum()),
        bearish_signal_count=int((base_signal == -1).sum()),
        allow_long_by_layer=allow_long_by_layer,
        allow_short_by_layer=allow_short_by_layer,
    )


def mode_to_code(mode: str) -> int:
    return {"always_on_active": 0, "change_only": 1, "hybrid_reentry_once": 2}[mode]


@njit(cache=True)
def run_active_mode_with_filter_metrics(
    open_: np.ndarray,
    high: np.ndarray,
    low: np.ndarray,
    close: np.ndarray,
    active_signal: np.ndarray,
    session_ids: np.ndarray,
    allow_long: np.ndarray,
    allow_short: np.ndarray,
    stop_loss_pct: float,
    take_profit_pct: float,
    cost_bps_per_side: float,
    mode_code: int,
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
        allowed_bias = 0
        if current_bias == 1 and allow_long[i]:
            allowed_bias = 1
        elif current_bias == -1 and allow_short[i]:
            allowed_bias = -1

        if not last_bar_of_session:
            changed = current_bias != prev_bias
            if changed:
                reentry_used = False

            pending_signal = 0
            if mode_code == 0:
                if allowed_bias != 0 and (position == 0 or allowed_bias != position):
                    pending_signal = allowed_bias
            elif mode_code == 1:
                if allowed_bias != 0 and changed and (position == 0 or allowed_bias != position):
                    pending_signal = allowed_bias
            else:
                if allowed_bias != 0 and changed and (position == 0 or allowed_bias != position):
                    pending_signal = allowed_bias
                elif (
                    stop_exit
                    and current_bias != 0
                    and current_bias == prev_bias
                    and allowed_bias == current_bias
                    and not reentry_used
                    and position == 0
                ):
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


def run_active_mode_with_filter_detailed(
    bars: pd.DataFrame,
    active_signal: np.ndarray,
    session_ids: np.ndarray,
    allow_long: np.ndarray,
    allow_short: np.ndarray,
    stop_loss_pct: float,
    take_profit_pct: float,
    cost_bps_per_side: float,
    mode: str,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    open_ = bars["open"].to_numpy(dtype=np.float64)
    high = bars["high"].to_numpy(dtype=np.float64)
    low = bars["low"].to_numpy(dtype=np.float64)
    close = bars["close"].to_numpy(dtype=np.float64)
    timestamps = bars.index.to_numpy()
    session_dates = bars["session_date"].to_numpy()

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
        stop_exit = False
        if position != 0:
            if position == 1:
                stop_price = entry_price * (1.0 - stop_loss_pct)
                target_price = entry_price * (1.0 + take_profit_pct)
                if low[i] <= stop_price:
                    current_exit_reason = "stop_loss"
                    stop_exit = True
                    close_trade(i, stop_price, current_exit_reason)
                elif high[i] >= target_price:
                    current_exit_reason = "take_profit"
                    close_trade(i, target_price, current_exit_reason)
            else:
                stop_price = entry_price * (1.0 + stop_loss_pct)
                target_price = entry_price * (1.0 - take_profit_pct)
                if high[i] >= stop_price:
                    current_exit_reason = "stop_loss"
                    stop_exit = True
                    close_trade(i, stop_price, current_exit_reason)
                elif low[i] <= target_price:
                    current_exit_reason = "take_profit"
                    close_trade(i, target_price, current_exit_reason)

        if last_bar_of_session and position != 0:
            current_exit_reason = "session_close"
            close_trade(i, close[i], current_exit_reason)

        current_bias = int(active_signal[i])
        allowed_bias = 0
        if current_bias == 1 and allow_long[i]:
            allowed_bias = 1
        elif current_bias == -1 and allow_short[i]:
            allowed_bias = -1

        if not last_bar_of_session:
            changed = current_bias != prev_bias
            if changed:
                reentry_used = False

            pending_signal = 0
            pending_entry_reason = ""
            if mode == "always_on_active":
                if allowed_bias != 0 and (position == 0 or allowed_bias != position):
                    pending_signal = allowed_bias
                    pending_entry_reason = "filter_pass"
            elif mode == "change_only":
                if allowed_bias != 0 and changed and (position == 0 or allowed_bias != position):
                    pending_signal = allowed_bias
                    pending_entry_reason = "bias_change"
            else:
                if allowed_bias != 0 and changed and (position == 0 or allowed_bias != position):
                    pending_signal = allowed_bias
                    pending_entry_reason = "bias_change"
                elif (
                    current_exit_reason == "stop_loss"
                    and current_bias != 0
                    and current_bias == prev_bias
                    and allowed_bias == current_bias
                    and not reentry_used
                    and position == 0
                ):
                    pending_signal = current_bias
                    reentry_used = True
                    pending_entry_reason = "stop_reentry"
        else:
            pending_signal = 0
            pending_entry_reason = ""

        if last_bar_of_session:
            daily_equity.append(
                {
                    "session_date": pd.Timestamp(session_dates[i]),
                    "equity": equity,
                }
            )

        prev_bias = current_bias

    return pd.DataFrame(trades), pd.DataFrame(daily_equity)


def build_best_by_winner(results: pd.DataFrame) -> pd.DataFrame:
    best = (
        results.sort_values(
            ["winner_id", "cost_bps_per_side", "total_return_pct", "sharpe", "profit_factor"],
            ascending=[True, True, False, False, False],
        )
        .groupby(["winner_id", "cost_bps_per_side"], as_index=False)
        .head(1)
        .reset_index(drop=True)
    )

    baseline = results[results["layer_id"] == BASE_LAYER_ID].copy()
    baseline = baseline.rename(
        columns={
            "layer_id": "baseline_layer_id",
            "start_offset_min": "baseline_start_offset_min",
            "cutoff": "baseline_cutoff",
            "trend_filter": "baseline_trend_filter",
            "ending_equity": "baseline_ending_equity",
            "total_return_pct": "baseline_total_return_pct",
            "cagr_pct": "baseline_cagr_pct",
            "max_drawdown_pct": "baseline_max_drawdown_pct",
            "sharpe": "baseline_sharpe",
            "profit_factor": "baseline_profit_factor",
            "trade_count": "baseline_trade_count",
            "win_count": "baseline_win_count",
            "win_rate_pct": "baseline_win_rate_pct",
            "avg_trade_return_pct": "baseline_avg_trade_return_pct",
            "avg_holding_bars": "baseline_avg_holding_bars",
            "avg_holding_minutes": "baseline_avg_holding_minutes",
            "exposure_pct": "baseline_exposure_pct",
        }
    )

    keep_baseline_cols = [
        "winner_id",
        "cost_bps_per_side",
        "baseline_layer_id",
        "baseline_start_offset_min",
        "baseline_cutoff",
        "baseline_trend_filter",
        "baseline_ending_equity",
        "baseline_total_return_pct",
        "baseline_cagr_pct",
        "baseline_max_drawdown_pct",
        "baseline_sharpe",
        "baseline_profit_factor",
        "baseline_trade_count",
        "baseline_win_count",
        "baseline_win_rate_pct",
        "baseline_avg_trade_return_pct",
        "baseline_avg_holding_bars",
        "baseline_avg_holding_minutes",
        "baseline_exposure_pct",
    ]

    compare = best.merge(
        baseline[keep_baseline_cols],
        on=["winner_id", "cost_bps_per_side"],
        how="left",
    )
    compare["delta_total_return_pct"] = compare["total_return_pct"] - compare["baseline_total_return_pct"]
    compare["delta_cagr_pct"] = compare["cagr_pct"] - compare["baseline_cagr_pct"]
    compare["delta_max_drawdown_pct"] = compare["max_drawdown_pct"] - compare["baseline_max_drawdown_pct"]
    compare["delta_sharpe"] = compare["sharpe"] - compare["baseline_sharpe"]
    compare["delta_profit_factor"] = compare["profit_factor"] - compare["baseline_profit_factor"]
    compare["delta_trade_count"] = compare["trade_count"] - compare["baseline_trade_count"]
    compare["beats_frozen_return"] = compare["delta_total_return_pct"] > 1e-9
    compare["beats_frozen_sharpe"] = compare["delta_sharpe"] > 1e-9
    return compare


def build_summary(results: pd.DataFrame, best_by_winner: pd.DataFrame, runtime_seconds: float) -> str:
    realistic = results[results["cost_bps_per_side"] == REALISTIC_COST_BPS].copy()
    realistic_best = best_by_winner[best_by_winner["cost_bps_per_side"] == REALISTIC_COST_BPS].copy()
    overall_best = realistic.sort_values(
        ["total_return_pct", "sharpe", "profit_factor"],
        ascending=[False, False, False],
    ).iloc[0]

    top_realistic = realistic.sort_values(
        ["total_return_pct", "sharpe", "profit_factor"],
        ascending=[False, False, False],
    ).head(16)

    trend_effect = (
        realistic.groupby(["winner_id", "trend_filter"])
        .agg(
            best_return=("total_return_pct", "max"),
            median_return=("total_return_pct", "median"),
            best_sharpe=("sharpe", "max"),
            median_trades=("trade_count", "median"),
        )
        .reset_index()
        .sort_values(["winner_id", "best_return"], ascending=[True, False])
    )

    compare_view = realistic_best[
        [
            "winner_id",
            "timeframe_label",
            "entry_mode",
            "layer_id",
            "start_offset_min",
            "cutoff",
            "trend_filter",
            "baseline_total_return_pct",
            "total_return_pct",
            "delta_total_return_pct",
            "baseline_sharpe",
            "sharpe",
            "delta_sharpe",
            "baseline_max_drawdown_pct",
            "max_drawdown_pct",
            "delta_max_drawdown_pct",
            "baseline_trade_count",
            "trade_count",
            "delta_trade_count",
        ]
    ].copy()
    for column in [
        "baseline_total_return_pct",
        "total_return_pct",
        "delta_total_return_pct",
        "baseline_max_drawdown_pct",
        "max_drawdown_pct",
        "delta_max_drawdown_pct",
    ]:
        compare_view[column] = compare_view[column].map(lambda x: f"{x:.2f}%")
    for column in ["baseline_sharpe", "sharpe", "delta_sharpe"]:
        compare_view[column] = compare_view[column].map(lambda x: f"{x:.2f}")
    for column in ["baseline_trade_count", "trade_count", "delta_trade_count"]:
        compare_view[column] = compare_view[column].map(lambda x: f"{int(x)}")

    top_view = top_realistic[
        [
            "winner_id",
            "timeframe_label",
            "entry_mode",
            "layer_id",
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
        top_view[column] = top_view[column].map(lambda x: f"{x:.2f}%")
    top_view["sharpe"] = top_view["sharpe"].map(lambda x: f"{x:.2f}")
    top_view["profit_factor"] = top_view["profit_factor"].map(lambda x: f"{x:.2f}")
    top_view["trade_count"] = top_view["trade_count"].map(lambda x: f"{int(x)}")

    trend_view = trend_effect.copy()
    for column in ["best_return", "median_return"]:
        trend_view[column] = trend_view[column].map(lambda x: f"{x:.2f}%")
    trend_view["best_sharpe"] = trend_view["best_sharpe"].map(lambda x: f"{x:.2f}")
    trend_view["median_trades"] = trend_view["median_trades"].map(lambda x: f"{x:.0f}")

    winner_notes: list[str] = []
    for _, row in realistic_best.sort_values("winner_id").iterrows():
        layer_desc = (
            f"`{row['layer_id']}`"
            if row["layer_id"] != BASE_LAYER_ID
            else "`baseline_no_extra_filter`"
        )
        winner_notes.append(
            "- "
            f"`{row['winner_id']}` best layer: {layer_desc}, return `{row['total_return_pct']:.2f}%` "
            f"vs frozen `{row['baseline_total_return_pct']:.2f}%`, delta `{row['delta_total_return_pct']:.2f}%`, "
            f"Sharpe delta `{row['delta_sharpe']:.2f}`, drawdown delta `{row['delta_max_drawdown_pct']:.2f}%`."
        )

    improved = realistic_best[realistic_best["delta_total_return_pct"] > 1e-9].copy()
    if improved.empty:
        improvement_block = [
            "## Incremental Improvement",
            "",
            "- No tested wrapper beat the frozen baselines on total return under `2.0` bps per side.",
            "- Some wrappers may still improve drawdown or Sharpe; see the comparison table below.",
            "",
        ]
    else:
        best_improvement = improved.sort_values(
            ["delta_total_return_pct", "delta_sharpe"],
            ascending=[False, False],
        ).iloc[0]
        improvement_block = [
            "## Incremental Improvement",
            "",
            f"- Best verified improvement vs frozen baseline: `{best_improvement['winner_id']}` with layer `{best_improvement['layer_id']}`.",
            f"- Return delta: `{best_improvement['delta_total_return_pct']:.2f}%`.",
            f"- Sharpe delta: `{best_improvement['delta_sharpe']:.2f}`.",
            f"- Drawdown delta: `{best_improvement['delta_max_drawdown_pct']:.2f}%`.",
            "",
        ]

    lines = [
        "# QQQ Frozen Winner Layered Filter Study",
        "",
        "## Scope",
        "",
        f"- Frozen baselines defined in `{FROZEN_FILE}`.",
        "- Base engines were not re-optimized. Only entry wrappers were added on top.",
        "- Layer families tested:",
        "  - Session start delay: `0`, `30`, and `60` minutes after the regular session open.",
        "  - Entry cutoff: none or `14:30` ET.",
        "  - Trend gating: `none`, `vwap`, `ema10`, and `vwap_ema10`.",
        "- Timing filters use the actual next-bar entry time, not the signal bar timestamp.",
        "- Exit behavior remains frozen: stop loss, take profit, reverse-on-next-open when allowed, and flat by session close.",
        f"- Costs tested: `{', '.join(f'{x:.1f}' for x in COST_BPS_PER_SIDE)}` bps per side.",
        "",
        "## Best Realistic Result (`2.0` Bps Per Side)",
        "",
        f"- Winner: `{overall_best['winner_id']}`.",
        f"- Variant: `{overall_best['variant']}`.",
        f"- Entry mode: `{overall_best['entry_mode']}`.",
        f"- Layer: `{overall_best['layer_id']}`.",
        f"- Timeframe: `{overall_best['timeframe_label']}`.",
        f"- Stop loss: `{overall_best['stop_loss_pct']:.2f}%`.",
        f"- Take profit: `{overall_best['take_profit_pct']:.2f}%`.",
        f"- Total return: `{overall_best['total_return_pct']:.2f}%`.",
        f"- CAGR: `{overall_best['cagr_pct']:.2f}%`.",
        f"- Max drawdown: `{overall_best['max_drawdown_pct']:.2f}%`.",
        f"- Sharpe: `{overall_best['sharpe']:.2f}`.",
        f"- Profit factor: `{overall_best['profit_factor']:.2f}`.",
        f"- Trades: `{int(overall_best['trade_count'])}` with win rate `{overall_best['win_rate_pct']:.2f}%`.",
        "",
    ]
    lines.extend(improvement_block)
    lines.extend(
        [
            "## Winner-Level Comparison At `2.0` Bps",
            "",
            *winner_notes,
            "",
            markdown_table(compare_view),
            "",
            "## Top 16 Layered Results Under `2.0` Bps",
            "",
            markdown_table(top_view),
            "",
            "## Trend Filter Snapshot Under `2.0` Bps",
            "",
            markdown_table(trend_view),
            "",
            "## Output Files",
            "",
            f"- Full grid: `{OUTPUTS['grid']}`.",
            f"- Best-by-winner table: `{OUTPUTS['best_by_winner']}`.",
            f"- Best realistic trades: `{OUTPUTS['best_realistic_trades']}`.",
            f"- Best realistic daily equity: `{OUTPUTS['best_realistic_equity']}`.",
            f"- Runtime: `{runtime_seconds:.2f}` seconds.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    start = perf_counter()
    minute_frame = load_minute_data(SOURCE)
    prepared_winners = [prepare_winner(minute_frame, winner) for winner in FROZEN_WINNERS]

    rows: list[dict[str, float | int | str | bool]] = []
    for prepared in prepared_winners:
        winner = prepared.winner
        bars = prepared.bars
        open_ = bars["open"].to_numpy(dtype=np.float64)
        high = bars["high"].to_numpy(dtype=np.float64)
        low = bars["low"].to_numpy(dtype=np.float64)
        close = bars["close"].to_numpy(dtype=np.float64)
        mode_code = mode_to_code(winner.entry_mode)

        for start_offset_min in START_OFFSETS_MIN:
            for cutoff in CUTOFFS:
                for trend_filter in TREND_FILTERS:
                    key = layer_id(start_offset_min, cutoff, trend_filter)
                    allow_long = prepared.allow_long_by_layer[key]
                    allow_short = prepared.allow_short_by_layer[key]

                    for cost_bps_per_side in COST_BPS_PER_SIDE:
                        metrics = run_active_mode_with_filter_metrics(
                            open_,
                            high,
                            low,
                            close,
                            prepared.base_signal,
                            prepared.session_ids,
                            allow_long,
                            allow_short,
                            winner.stop_loss_pct / 100.0,
                            winner.take_profit_pct / 100.0,
                            cost_bps_per_side,
                            mode_code,
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
                                "winner_id": winner.winner_id,
                                "variant": winner.variant,
                                "entry_mode": winner.entry_mode,
                                "timeframe_min": winner.timeframe_min,
                                "timeframe_label": f"{winner.timeframe_min}m",
                                "layer_id": key,
                                "is_baseline_layer": key == BASE_LAYER_ID,
                                "start_offset_min": start_offset_min,
                                "cutoff": cutoff or "none",
                                "trend_filter": trend_filter,
                                "cost_bps_per_side": cost_bps_per_side,
                                "stop_loss_pct": winner.stop_loss_pct,
                                "take_profit_pct": winner.take_profit_pct,
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
                                "avg_holding_minutes": avg_holding_bars * winner.timeframe_min,
                                "exposure_pct": exposure_pct,
                                "bullish_signal_count": prepared.bullish_signal_count,
                                "bearish_signal_count": prepared.bearish_signal_count,
                            }
                        )

    results = pd.DataFrame(rows).sort_values(
        ["cost_bps_per_side", "total_return_pct", "sharpe", "profit_factor"],
        ascending=[True, False, False, False],
    )
    results.to_csv(OUTPUTS["grid"], index=False)

    best_by_winner = build_best_by_winner(results)
    best_by_winner.to_csv(OUTPUTS["best_by_winner"], index=False)

    best_realistic = results[results["cost_bps_per_side"] == REALISTIC_COST_BPS].sort_values(
        ["total_return_pct", "sharpe", "profit_factor"],
        ascending=[False, False, False],
    ).iloc[0]
    best_prepared = next(item for item in prepared_winners if item.winner.winner_id == best_realistic["winner_id"])
    best_allow_long = best_prepared.allow_long_by_layer[best_realistic["layer_id"]]
    best_allow_short = best_prepared.allow_short_by_layer[best_realistic["layer_id"]]
    trades_df, equity_df = run_active_mode_with_filter_detailed(
        best_prepared.bars,
        best_prepared.base_signal,
        best_prepared.session_ids,
        best_allow_long,
        best_allow_short,
        float(best_realistic["stop_loss_pct"]) / 100.0,
        float(best_realistic["take_profit_pct"]) / 100.0,
        float(best_realistic["cost_bps_per_side"]),
        str(best_realistic["entry_mode"]),
    )

    for frame in (trades_df, equity_df):
        frame["winner_id"] = best_realistic["winner_id"]
        frame["variant"] = best_realistic["variant"]
        frame["entry_mode"] = best_realistic["entry_mode"]
        frame["timeframe_label"] = best_realistic["timeframe_label"]
        frame["layer_id"] = best_realistic["layer_id"]
        frame["start_offset_min"] = int(best_realistic["start_offset_min"])
        frame["cutoff"] = best_realistic["cutoff"]
        frame["trend_filter"] = best_realistic["trend_filter"]
        frame["stop_loss_pct"] = float(best_realistic["stop_loss_pct"])
        frame["take_profit_pct"] = float(best_realistic["take_profit_pct"])
        frame["cost_bps_per_side"] = float(best_realistic["cost_bps_per_side"])

    trades_df.to_csv(OUTPUTS["best_realistic_trades"], index=False)
    equity_df.to_csv(OUTPUTS["best_realistic_equity"], index=False)

    runtime_seconds = perf_counter() - start
    OUTPUTS["summary"].write_text(build_summary(results, best_by_winner, runtime_seconds), encoding="utf-8")


if __name__ == "__main__":
    main()
