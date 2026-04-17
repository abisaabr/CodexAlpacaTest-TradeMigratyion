from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from numba import njit

BASE = Path(r"C:\Users\rabisaab\Downloads")
DATA_PATH = BASE / "QQQ_1min_20210308-20260308_sip (1).csv"
REPORT_DIR = BASE / "reports"
REPORT_DIR.mkdir(exist_ok=True)

OUT_METRICS = REPORT_DIR / "qqq_crsi_sweep_metrics.csv"
OUT_BEST = REPORT_DIR / "qqq_crsi_best_by_timeframe.csv"
OUT_LEDGER = REPORT_DIR / "qqq_crsi_best_trade_ledger.csv"
OUT_REPORT = REPORT_DIR / "qqq_crsi_backtest_report.md"
OUT_DIGEST = REPORT_DIR / "qqq_crsi_input_digest.md"

INITIAL_EQUITY = 25_000.0
COST_BPS_PER_SIDE = 2.0
DOMCYCLES = (10, 14, 20, 30, 40)
LEVELINGS = (5.0, 10.0, 15.0, 20.0)
ENTRY_BUFFERS = (0.0, 2.0, 4.0)
EXIT_RATIOS = (0.0, 0.5, 1.0)
TIMEFRAMES = (1, 2, 5, 15, 30, 60)
FAMILY_MAP = {0: "mean_reversion", 1: "breakout"}
VIBRATION = 10
PHASING_LAG = int((VIBRATION - 1) / 2.0)  # Truncated from the Pine script's float lag.


@dataclass(frozen=True)
class SessionData:
    frame: pd.DataFrame
    day_codes: np.ndarray
    day_year_codes: np.ndarray
    unique_days: np.ndarray
    unique_years: np.ndarray
    close_ret: np.ndarray
    session_start: np.ndarray
    session_end: np.ndarray


def load_rth_qqq() -> tuple[pd.DataFrame, pd.Series]:
    frame = pd.read_csv(
        DATA_PATH,
        usecols=["timestamp_utc", "open", "high", "low", "close", "volume"],
        parse_dates=["timestamp_utc"],
    )
    frame["timestamp"] = (
        pd.to_datetime(frame["timestamp_utc"], utc=True)
        .dt.tz_convert("America/New_York")
    )
    frame = frame.drop(columns=["timestamp_utc"]).set_index("timestamp").sort_index()
    rth = frame.between_time("09:30", "15:59").copy()
    rth["session_date"] = pd.Index(rth.index.date)
    full_days = rth.groupby("session_date").size()
    full_days = full_days[full_days == 390].index
    rth = rth[rth["session_date"].isin(full_days)].copy()
    raw_session_counts = frame.groupby(pd.Index(frame.index.date)).size()
    return rth, raw_session_counts


def resample_intraday(frame: pd.DataFrame, minutes: int) -> pd.DataFrame:
    if minutes == 1:
        result = frame.copy()
        result["bar_timeframe_minutes"] = 1
        return result
    work = frame.reset_index().rename(columns={"timestamp": "bar_timestamp"})
    minute_of_day = work["bar_timestamp"].dt.hour * 60 + work["bar_timestamp"].dt.minute - (9 * 60 + 30)
    work["bucket"] = minute_of_day // minutes
    grouped = (
        work.groupby(["session_date", "bucket"], sort=True)
        .agg(
            timestamp=("bar_timestamp", "last"),
            open=("open", "first"),
            high=("high", "max"),
            low=("low", "min"),
            close=("close", "last"),
            volume=("volume", "sum"),
        )
        .reset_index(drop=True)
        .set_index("timestamp")
        .sort_index()
    )
    grouped["session_date"] = pd.Index(grouped.index.date)
    grouped["bar_timeframe_minutes"] = minutes
    return grouped


def build_session_data(frame: pd.DataFrame) -> SessionData:
    session_dates = pd.to_datetime(frame["session_date"])
    unique_days, day_codes = np.unique(session_dates.to_numpy(), return_inverse=True)
    unique_years = np.unique(session_dates.dt.year.to_numpy())
    year_lookup = {year: idx for idx, year in enumerate(unique_years)}
    day_year_codes = np.array([year_lookup[pd.Timestamp(day).year] for day in unique_days], dtype=np.int32)
    session_change = frame["session_date"].ne(frame["session_date"].shift()).fillna(True)
    session_end = frame["session_date"].ne(frame["session_date"].shift(-1)).fillna(True)
    close_ret = frame["close"].shift(-1).div(frame["close"]).sub(1.0).to_numpy(dtype=np.float64)
    close_ret[session_end.to_numpy()] = 0.0
    close_ret[np.isnan(close_ret)] = 0.0
    return SessionData(
        frame=frame,
        day_codes=day_codes.astype(np.int32),
        day_year_codes=day_year_codes,
        unique_days=unique_days,
        unique_years=unique_years,
        close_ret=close_ret,
        session_start=session_change.to_numpy(dtype=np.bool_),
        session_end=session_end.to_numpy(dtype=np.bool_),
    )


def rma(values: np.ndarray, length: int) -> np.ndarray:
    out = np.full(values.shape[0], np.nan, dtype=np.float64)
    if length <= 0 or values.shape[0] < length:
        return out
    seed = float(np.nanmean(values[:length]))
    out[length - 1] = seed
    alpha = 1.0 / float(length)
    for idx in range(length, values.shape[0]):
        out[idx] = out[idx - 1] + alpha * (values[idx] - out[idx - 1])
    return out


def compute_crsi(close: pd.Series, domcycle: int) -> pd.Series:
    cyclelen = domcycle // 2
    change = close.diff().to_numpy(dtype=np.float64)
    change[np.isnan(change)] = 0.0
    up = np.maximum(change, 0.0)
    down = np.maximum(-change, 0.0)
    up_rma = rma(up, cyclelen)
    down_rma = rma(down, cyclelen)
    rsi = np.full(close.shape[0], np.nan, dtype=np.float64)
    valid = ~np.isnan(up_rma) & ~np.isnan(down_rma)
    zero_down = valid & (down_rma == 0.0)
    zero_up = valid & (up_rma == 0.0)
    rsi[zero_down] = 100.0
    rsi[~zero_down & zero_up] = 0.0
    ratio_mask = valid & ~zero_down & ~zero_up
    rsi[ratio_mask] = 100.0 - 100.0 / (1.0 + (up_rma[ratio_mask] / down_rma[ratio_mask]))
    torque = 2.0 / (VIBRATION + 1.0)
    crsi = np.full(close.shape[0], np.nan, dtype=np.float64)
    for idx in range(close.shape[0]):
        if idx - PHASING_LAG < 0:
            continue
        current_rsi = rsi[idx]
        lagged_rsi = rsi[idx - PHASING_LAG]
        if np.isnan(current_rsi) or np.isnan(lagged_rsi):
            continue
        previous = 0.0 if idx == 0 or np.isnan(crsi[idx - 1]) else crsi[idx - 1]
        crsi[idx] = torque * (2.0 * current_rsi - lagged_rsi) + (1.0 - torque) * previous
    return pd.Series(crsi, index=close.index, name="crsi")


def compute_bands(crsi: pd.Series, domcycle: int, leveling: float) -> tuple[pd.Series, pd.Series]:
    memory = domcycle * 2
    rolling = crsi.rolling(memory, min_periods=memory)
    lower_bound = rolling.min()
    upper_bound = rolling.max()
    lower_quantile = rolling.quantile(leveling / 100.0, interpolation="higher")
    upper_quantile = rolling.quantile(1.0 - leveling / 100.0, interpolation="lower")
    lower_np = lower_bound.to_numpy(dtype=np.float64)
    upper_np = upper_bound.to_numpy(dtype=np.float64)
    low_q_np = lower_quantile.to_numpy(dtype=np.float64)
    high_q_np = upper_quantile.to_numpy(dtype=np.float64)
    step_np = (upper_np - lower_np) / 100.0
    low_band = np.full(crsi.shape[0], np.nan, dtype=np.float64)
    high_band = np.full(crsi.shape[0], np.nan, dtype=np.float64)
    valid = np.isfinite(lower_np) & np.isfinite(upper_np) & np.isfinite(low_q_np) & np.isfinite(high_q_np)
    flat = valid & (step_np <= 0.0)
    low_band[flat] = lower_np[flat]
    high_band[flat] = upper_np[flat]
    stepped = valid & (step_np > 0.0)
    low_steps = np.ceil(np.maximum(low_q_np[stepped] - lower_np[stepped], 0.0) / step_np[stepped])
    high_steps = np.ceil(np.maximum(upper_np[stepped] - high_q_np[stepped], 0.0) / step_np[stepped])
    low_band[stepped] = lower_np[stepped] + low_steps * step_np[stepped]
    high_band[stepped] = upper_np[stepped] - high_steps * step_np[stepped]
    return (
        pd.Series(low_band, index=crsi.index, name="low_band"),
        pd.Series(high_band, index=crsi.index, name="high_band"),
    )


@njit(cache=False)
def simulate_metrics(
    close: np.ndarray,
    close_ret: np.ndarray,
    day_codes: np.ndarray,
    day_year_codes: np.ndarray,
    session_start: np.ndarray,
    session_end: np.ndarray,
    crsi: np.ndarray,
    low_band: np.ndarray,
    high_band: np.ndarray,
    family_code: int,
    entry_buffer: float,
    exit_ratio: float,
    cost_rate: float,
) -> np.ndarray:
    n = close.shape[0]
    num_days = int(day_codes.max()) + 1
    num_years = int(day_year_codes.max()) + 1
    daily_log = np.zeros(num_days, dtype=np.float64)
    yearly_log = np.zeros(num_years, dtype=np.float64)
    equity = 1.0
    peak = 1.0
    max_dd = 0.0
    state = 0
    prev_position = 0
    entry_price = 0.0
    entry_index = -1
    trade_count = 0
    win_count = 0
    sum_trade = 0.0
    sum_wins = 0.0
    sum_losses = 0.0
    long_count = 0
    short_count = 0
    long_sum = 0.0
    short_sum = 0.0
    hold_sum = 0.0
    valid_levels = 0
    sum_low = 0.0
    sum_high = 0.0
    sum_width = 0.0
    sum_long_entry = 0.0
    sum_long_exit = 0.0
    sum_short_entry = 0.0
    sum_short_exit = 0.0
    for idx in range(n):
        current_low = low_band[idx]
        current_high = high_band[idx]
        current_crsi = crsi[idx]
        if not np.isnan(current_low) and not np.isnan(current_high) and not np.isnan(current_crsi):
            width = current_high - current_low
            if width >= 0.0:
                valid_levels += 1
                sum_low += current_low
                sum_high += current_high
                sum_width += width
                if family_code == 0:
                    sum_long_entry += current_low - entry_buffer
                    sum_long_exit += current_low + exit_ratio * width
                    sum_short_entry += current_high + entry_buffer
                    sum_short_exit += current_high - exit_ratio * width
                else:
                    sum_long_entry += current_high + entry_buffer
                    sum_long_exit += current_high - exit_ratio * width
                    sum_short_entry += current_low - entry_buffer
                    sum_short_exit += current_low + exit_ratio * width
        new_state = state
        if session_end[idx]:
            new_state = 0
        elif idx > 0 and not session_start[idx]:
            prev_low = low_band[idx - 1]
            prev_high = high_band[idx - 1]
            prev_crsi = crsi[idx - 1]
            if (
                not np.isnan(prev_low)
                and not np.isnan(prev_high)
                and not np.isnan(prev_crsi)
                and not np.isnan(current_low)
                and not np.isnan(current_high)
                and not np.isnan(current_crsi)
            ):
                prev_width = prev_high - prev_low
                current_width = current_high - current_low
                if prev_width >= 0.0 and current_width >= 0.0:
                    if family_code == 0:
                        prev_long_entry = prev_low - entry_buffer
                        current_long_entry = current_low - entry_buffer
                        prev_short_entry = prev_high + entry_buffer
                        current_short_entry = current_high + entry_buffer
                        prev_long_exit = prev_low + exit_ratio * prev_width
                        current_long_exit = current_low + exit_ratio * current_width
                        prev_short_exit = prev_high - exit_ratio * prev_width
                        current_short_exit = current_high - exit_ratio * current_width
                        long_entry = prev_crsi > prev_long_entry and current_crsi <= current_long_entry
                        short_entry = prev_crsi < prev_short_entry and current_crsi >= current_short_entry
                        long_exit = prev_crsi < prev_long_exit and current_crsi >= current_long_exit
                        short_exit = prev_crsi > prev_short_exit and current_crsi <= current_short_exit
                    else:
                        prev_long_entry = prev_high + entry_buffer
                        current_long_entry = current_high + entry_buffer
                        prev_short_entry = prev_low - entry_buffer
                        current_short_entry = current_low - entry_buffer
                        prev_long_exit = prev_high - exit_ratio * prev_width
                        current_long_exit = current_high - exit_ratio * current_width
                        prev_short_exit = prev_low + exit_ratio * prev_width
                        current_short_exit = current_low + exit_ratio * current_width
                        long_entry = prev_crsi < prev_long_entry and current_crsi >= current_long_entry
                        short_entry = prev_crsi > prev_short_entry and current_crsi <= current_short_entry
                        long_exit = prev_crsi > prev_long_exit and current_crsi <= current_long_exit
                        short_exit = prev_crsi < prev_short_exit and current_crsi >= current_short_exit
                    if state == 1:
                        if short_entry and not long_entry:
                            new_state = -1
                        elif long_exit:
                            new_state = 0
                    elif state == -1:
                        if long_entry and not short_entry:
                            new_state = 1
                        elif short_exit:
                            new_state = 0
                    else:
                        if long_entry and not short_entry:
                            new_state = 1
                        elif short_entry and not long_entry:
                            new_state = -1
        if new_state != state:
            if state != 0 and entry_index >= 0:
                trade_ret = state * (close[idx] / entry_price - 1.0) - 2.0 * cost_rate
                trade_count += 1
                sum_trade += trade_ret
                hold_sum += idx - entry_index
                if trade_ret > 0.0:
                    win_count += 1
                    sum_wins += trade_ret
                elif trade_ret < 0.0:
                    sum_losses += trade_ret
                if state == 1:
                    long_count += 1
                    long_sum += trade_ret
                else:
                    short_count += 1
                    short_sum += trade_ret
            if new_state != 0:
                entry_price = close[idx]
                entry_index = idx
            else:
                entry_price = 0.0
                entry_index = -1
            state = new_state
        position = state
        turnover = abs(position - prev_position)
        net_ret = position * close_ret[idx] - cost_rate * turnover
        daily_log[day_codes[idx]] += math.log1p(net_ret)
        equity *= 1.0 + net_ret
        if equity > peak:
            peak = equity
        drawdown = 1.0 - equity / peak
        if drawdown > max_dd:
            max_dd = drawdown
        prev_position = position
    positive_days = 0
    daily_sum = 0.0
    daily_sq = 0.0
    worst_year = 1e9
    best_year = -1e9
    positive_years = 0
    for day_idx in range(num_days):
        daily_ret = math.expm1(daily_log[day_idx])
        yearly_log[day_year_codes[day_idx]] += daily_log[day_idx]
        if daily_ret > 0.0:
            positive_days += 1
        daily_sum += daily_ret
        daily_sq += daily_ret * daily_ret
    daily_mean = daily_sum / num_days if num_days else 0.0
    if num_days > 1:
        daily_var = max(daily_sq / num_days - daily_mean * daily_mean, 0.0)
        daily_std = math.sqrt(daily_var)
        sharpe = (daily_mean / daily_std) * math.sqrt(252.0) if daily_std > 0.0 else 0.0
    else:
        sharpe = 0.0
    for year_idx in range(num_years):
        year_ret = math.expm1(yearly_log[year_idx])
        if year_ret > 0.0:
            positive_years += 1
        if year_ret < worst_year:
            worst_year = year_ret
        if year_ret > best_year:
            best_year = year_ret
    win_rate = (win_count / trade_count) if trade_count else 0.0
    avg_trade = (sum_trade / trade_count) if trade_count else 0.0
    avg_win = (sum_wins / win_count) if win_count else 0.0
    loss_count = trade_count - win_count
    avg_loss = (sum_losses / loss_count) if loss_count else 0.0
    profit_factor = (sum_wins / abs(sum_losses)) if sum_losses < 0.0 else (999.0 if sum_wins > 0.0 else 0.0)
    avg_hold = (hold_sum / trade_count) if trade_count else 0.0
    long_avg = (long_sum / long_count) if long_count else 0.0
    short_avg = (short_sum / short_count) if short_count else 0.0
    if valid_levels:
        avg_low = sum_low / valid_levels
        avg_high = sum_high / valid_levels
        avg_width = sum_width / valid_levels
        avg_long_entry = sum_long_entry / valid_levels
        avg_long_exit = sum_long_exit / valid_levels
        avg_short_entry = sum_short_entry / valid_levels
        avg_short_exit = sum_short_exit / valid_levels
    else:
        avg_low = np.nan
        avg_high = np.nan
        avg_width = np.nan
        avg_long_entry = np.nan
        avg_long_exit = np.nan
        avg_short_entry = np.nan
        avg_short_exit = np.nan
    return np.array(
        [
            equity,
            (equity - 1.0) * 100.0,
            max_dd * 100.0,
            sharpe,
            profit_factor,
            trade_count,
            win_rate * 100.0,
            avg_trade * 100.0,
            avg_win * 100.0,
            avg_loss * 100.0,
            avg_hold,
            long_count,
            short_count,
            long_avg * 100.0,
            short_avg * 100.0,
            positive_days / num_days * 100.0 if num_days else 0.0,
            positive_years,
            worst_year * 100.0 if num_years else 0.0,
            best_year * 100.0 if num_years else 0.0,
            avg_low,
            avg_high,
            avg_width,
            avg_long_entry,
            avg_long_exit,
            avg_short_entry,
            avg_short_exit,
        ],
        dtype=np.float64,
    )


@njit(cache=False)
def generate_positions(
    session_start: np.ndarray,
    session_end: np.ndarray,
    crsi: np.ndarray,
    low_band: np.ndarray,
    high_band: np.ndarray,
    family_code: int,
    entry_buffer: float,
    exit_ratio: float,
) -> np.ndarray:
    n = crsi.shape[0]
    positions = np.zeros(n, dtype=np.int8)
    state = 0
    for idx in range(n):
        new_state = state
        if session_end[idx]:
            new_state = 0
        elif idx > 0 and not session_start[idx]:
            prev_low = low_band[idx - 1]
            prev_high = high_band[idx - 1]
            prev_crsi = crsi[idx - 1]
            current_low = low_band[idx]
            current_high = high_band[idx]
            current_crsi = crsi[idx]
            if (
                not np.isnan(prev_low)
                and not np.isnan(prev_high)
                and not np.isnan(prev_crsi)
                and not np.isnan(current_low)
                and not np.isnan(current_high)
                and not np.isnan(current_crsi)
            ):
                prev_width = prev_high - prev_low
                current_width = current_high - current_low
                if prev_width >= 0.0 and current_width >= 0.0:
                    if family_code == 0:
                        prev_long_entry = prev_low - entry_buffer
                        current_long_entry = current_low - entry_buffer
                        prev_short_entry = prev_high + entry_buffer
                        current_short_entry = current_high + entry_buffer
                        prev_long_exit = prev_low + exit_ratio * prev_width
                        current_long_exit = current_low + exit_ratio * current_width
                        prev_short_exit = prev_high - exit_ratio * prev_width
                        current_short_exit = current_high - exit_ratio * current_width
                        long_entry = prev_crsi > prev_long_entry and current_crsi <= current_long_entry
                        short_entry = prev_crsi < prev_short_entry and current_crsi >= current_short_entry
                        long_exit = prev_crsi < prev_long_exit and current_crsi >= current_long_exit
                        short_exit = prev_crsi > prev_short_exit and current_crsi <= current_short_exit
                    else:
                        prev_long_entry = prev_high + entry_buffer
                        current_long_entry = current_high + entry_buffer
                        prev_short_entry = prev_low - entry_buffer
                        current_short_entry = current_low - entry_buffer
                        prev_long_exit = prev_high - exit_ratio * prev_width
                        current_long_exit = current_high - exit_ratio * current_width
                        prev_short_exit = prev_low + exit_ratio * prev_width
                        current_short_exit = current_low + exit_ratio * current_width
                        long_entry = prev_crsi < prev_long_entry and current_crsi >= current_long_entry
                        short_entry = prev_crsi > prev_short_entry and current_crsi <= current_short_entry
                        long_exit = prev_crsi > prev_long_exit and current_crsi <= current_long_exit
                        short_exit = prev_crsi < prev_short_exit and current_crsi >= current_short_exit
                    if state == 1:
                        if short_entry and not long_entry:
                            new_state = -1
                        elif long_exit:
                            new_state = 0
                    elif state == -1:
                        if long_entry and not short_entry:
                            new_state = 1
                        elif short_exit:
                            new_state = 0
                    else:
                        if long_entry and not short_entry:
                            new_state = 1
                        elif short_entry and not long_entry:
                            new_state = -1
        state = new_state
        positions[idx] = state
    return positions


def build_trade_ledger(
    frame: pd.DataFrame,
    positions: np.ndarray,
    family_name: str,
    timeframe_minutes: int,
    domcycle: int,
    leveling: float,
    entry_buffer: float,
    exit_ratio: float,
) -> pd.DataFrame:
    close = frame["close"].to_numpy(dtype=np.float64)
    timestamps = frame.index.to_numpy()
    rows: list[dict[str, object]] = []
    active_side = 0
    entry_idx = -1
    entry_price = 0.0
    for idx in range(len(positions)):
        previous = int(positions[idx - 1]) if idx > 0 else 0
        current = int(positions[idx])
        if previous == 0 and current != 0:
            active_side = current
            entry_idx = idx
            entry_price = close[idx]
        elif previous != 0 and current != previous:
            exit_idx = idx
            trade_return = active_side * (close[exit_idx] / entry_price - 1.0) - 2.0 * (COST_BPS_PER_SIDE / 10000.0)
            rows.append(
                {
                    "timeframe_minutes": timeframe_minutes,
                    "family": family_name,
                    "domcycle": domcycle,
                    "leveling": leveling,
                    "entry_buffer": entry_buffer,
                    "exit_ratio": exit_ratio,
                    "side": "long" if active_side == 1 else "short",
                    "entry_time": pd.Timestamp(timestamps[entry_idx]),
                    "exit_time": pd.Timestamp(timestamps[exit_idx]),
                    "entry_price": float(entry_price),
                    "exit_price": float(close[exit_idx]),
                    "holding_bars": int(exit_idx - entry_idx),
                    "trade_return_pct": float(trade_return * 100.0),
                    "pnl_dollars_on_25k": float(INITIAL_EQUITY * trade_return),
                }
            )
            if current != 0:
                active_side = current
                entry_idx = idx
                entry_price = close[idx]
            else:
                active_side = 0
                entry_idx = -1
                entry_price = 0.0
    return pd.DataFrame(rows)


def choose_timeframe_winner(frame: pd.DataFrame) -> pd.Series:
    eligible = frame[
        (frame["trade_count"] >= 20)
        & (frame["profit_factor"] >= 1.05)
        & (frame["positive_years"] >= 3)
        & (frame["max_drawdown_pct"] <= 35.0)
    ]
    ranked = eligible if not eligible.empty else frame
    return ranked.sort_values(
        ["total_return_pct", "sharpe", "profit_factor", "positive_days_pct"],
        ascending=[False, False, False, False],
    ).iloc[0]


def main() -> None:
    raw_rth, raw_session_counts = load_rth_qqq()
    full_rth_days = int(raw_rth["session_date"].nunique())
    rows: list[dict[str, object]] = []
    best_ledgers: list[pd.DataFrame] = []
    digest_lines = [
        "# QQQ cRSI Backtest Input Digest",
        "",
        f"- Source file: `{DATA_PATH}`",
        f"- Regular-hours one-minute bars after filtering: `{len(raw_rth):,}`.",
        f"- Full regular-hours sessions kept: `{full_rth_days}` days with exactly `390` bars.",
        f"- Raw file session size range before filtering: min `{int(raw_session_counts.min())}`, median `{float(raw_session_counts.median()):.0f}`, max `{int(raw_session_counts.max())}` bars/day.",
        "- Session window used for backtests: `09:30` to `15:59` America/New_York, no overnight holdings.",
        f"- Trading cost assumption: `{COST_BPS_PER_SIDE:.1f}` bps per side.",
        f"- cRSI implementation assumption: `vibration={VIBRATION}`, `phasingLag={PHASING_LAG}` using truncated indexing from the Pine script's `(vibration - 1) / 2` expression.",
        f"- Parameter sweep: domcycle `{DOMCYCLES}`, leveling `{LEVELINGS}`, entry buffer `{ENTRY_BUFFERS}`, exit ratio `{EXIT_RATIOS}`, families `{tuple(FAMILY_MAP.values())}`.",
    ]
    for timeframe in TIMEFRAMES:
        tf_frame = resample_intraday(raw_rth, timeframe)
        session_data = build_session_data(tf_frame)
        close = tf_frame["close"].to_numpy(dtype=np.float64)
        for domcycle in DOMCYCLES:
            crsi = compute_crsi(tf_frame["close"], domcycle)
            for leveling in LEVELINGS:
                low_band, high_band = compute_bands(crsi, domcycle, leveling)
                crsi_np = crsi.to_numpy(dtype=np.float64)
                low_np = low_band.to_numpy(dtype=np.float64)
                high_np = high_band.to_numpy(dtype=np.float64)
                for family_code, family_name in FAMILY_MAP.items():
                    for entry_buffer in ENTRY_BUFFERS:
                        for exit_ratio in EXIT_RATIOS:
                            metric_values = simulate_metrics(
                                close=close,
                                close_ret=session_data.close_ret,
                                day_codes=session_data.day_codes,
                                day_year_codes=session_data.day_year_codes,
                                session_start=session_data.session_start,
                                session_end=session_data.session_end,
                                crsi=crsi_np,
                                low_band=low_np,
                                high_band=high_np,
                                family_code=family_code,
                                entry_buffer=entry_buffer,
                                exit_ratio=exit_ratio,
                                cost_rate=COST_BPS_PER_SIDE / 10000.0,
                            )
                            rows.append(
                                {
                                    "timeframe_minutes": timeframe,
                                    "family": family_name,
                                    "domcycle": domcycle,
                                    "leveling": leveling,
                                    "entry_buffer": entry_buffer,
                                    "exit_ratio": exit_ratio,
                                    "final_equity": float(INITIAL_EQUITY * metric_values[0]),
                                    "total_return_pct": float(metric_values[1]),
                                    "max_drawdown_pct": float(metric_values[2]),
                                    "sharpe": float(metric_values[3]),
                                    "profit_factor": float(metric_values[4]),
                                    "trade_count": int(metric_values[5]),
                                    "win_rate_pct": float(metric_values[6]),
                                    "avg_trade_return_pct": float(metric_values[7]),
                                    "avg_win_pct": float(metric_values[8]),
                                    "avg_loss_pct": float(metric_values[9]),
                                    "avg_holding_bars": float(metric_values[10]),
                                    "long_trade_count": int(metric_values[11]),
                                    "short_trade_count": int(metric_values[12]),
                                    "long_avg_trade_return_pct": float(metric_values[13]),
                                    "short_avg_trade_return_pct": float(metric_values[14]),
                                    "positive_days_pct": float(metric_values[15]),
                                    "positive_years": int(metric_values[16]),
                                    "worst_year_return_pct": float(metric_values[17]),
                                    "best_year_return_pct": float(metric_values[18]),
                                    "avg_low_band": float(metric_values[19]),
                                    "avg_high_band": float(metric_values[20]),
                                    "avg_band_width": float(metric_values[21]),
                                    "avg_long_entry_level": float(metric_values[22]),
                                    "avg_long_exit_level": float(metric_values[23]),
                                    "avg_short_entry_level": float(metric_values[24]),
                                    "avg_short_exit_level": float(metric_values[25]),
                                }
                            )
    metrics = pd.DataFrame(rows)
    metrics["rank_in_timeframe"] = (
        metrics.groupby("timeframe_minutes")["total_return_pct"]
        .rank(method="min", ascending=False)
        .astype(int)
    )
    metrics = metrics.sort_values(
        ["timeframe_minutes", "rank_in_timeframe", "sharpe", "profit_factor"],
        ascending=[True, True, False, False],
    ).reset_index(drop=True)
    metrics.to_csv(OUT_METRICS, index=False)
    winners = []
    report_lines = [
        "# QQQ cRSI Backtest Report",
        "",
        "This sweep optimized how the fuchsia `cRSI` line should be compared to the aqua dynamic bands on regular-hours QQQ data.",
        "",
        "| Timeframe | Winning family | Domcycle | Leveling | Entry buffer | Exit ratio | Return | Max DD | Sharpe | PF | Trades | Typical long trigger | Typical short trigger |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |",
    ]
    for timeframe, group in metrics.groupby("timeframe_minutes", sort=True):
        winner = choose_timeframe_winner(group)
        winners.append(winner)
        family_code = 0 if winner["family"] == "mean_reversion" else 1
        tf_frame = resample_intraday(raw_rth, int(timeframe))
        session_data = build_session_data(tf_frame)
        crsi = compute_crsi(tf_frame["close"], int(winner["domcycle"]))
        low_band, high_band = compute_bands(crsi, int(winner["domcycle"]), float(winner["leveling"]))
        positions = generate_positions(
            session_start=session_data.session_start,
            session_end=session_data.session_end,
            crsi=crsi.to_numpy(dtype=np.float64),
            low_band=low_band.to_numpy(dtype=np.float64),
            high_band=high_band.to_numpy(dtype=np.float64),
            family_code=family_code,
            entry_buffer=float(winner["entry_buffer"]),
            exit_ratio=float(winner["exit_ratio"]),
        )
        best_ledgers.append(
            build_trade_ledger(
                frame=tf_frame,
                positions=positions,
                family_name=str(winner["family"]),
                timeframe_minutes=int(timeframe),
                domcycle=int(winner["domcycle"]),
                leveling=float(winner["leveling"]),
                entry_buffer=float(winner["entry_buffer"]),
                exit_ratio=float(winner["exit_ratio"]),
            )
        )
        report_lines.append(
            "| "
            f"{int(timeframe)}m | {winner['family']} | {int(winner['domcycle'])} | {winner['leveling']:.1f} | "
            f"{winner['entry_buffer']:.1f} | {winner['exit_ratio']:.1f} | {winner['total_return_pct']:.2f}% | "
            f"{winner['max_drawdown_pct']:.2f}% | {winner['sharpe']:.2f} | {winner['profit_factor']:.2f} | "
            f"{int(winner['trade_count'])} | buy `{winner['avg_long_entry_level']:.2f}` / sell `{winner['avg_long_exit_level']:.2f}` | "
            f"short `{winner['avg_short_entry_level']:.2f}` / cover `{winner['avg_short_exit_level']:.2f}` |"
        )
    winners_df = pd.DataFrame(winners).sort_values("timeframe_minutes").reset_index(drop=True)
    winners_df.to_csv(OUT_BEST, index=False)
    if best_ledgers:
        pd.concat(best_ledgers, ignore_index=True).to_csv(OUT_LEDGER, index=False)
    overall = winners_df.sort_values(
        ["total_return_pct", "sharpe", "profit_factor"],
        ascending=[False, False, False],
    ).iloc[0]
    report_lines += [
        "",
        "## Readout",
        "",
        f"- Best winning timeframe in this sweep: `{int(overall['timeframe_minutes'])}m` with the `{overall['family']}` interpretation.",
        f"- Typical winning long rule on that timeframe: compare the fuchsia line to the aqua band trigger at about `{overall['avg_long_entry_level']:.2f}` and exit near `{overall['avg_long_exit_level']:.2f}`.",
        f"- Typical winning short rule on that timeframe: short around `{overall['avg_short_entry_level']:.2f}` and cover near `{overall['avg_short_exit_level']:.2f}`.",
        "- `leveling` changes the aqua bands themselves. Lower values make the bands more extreme, higher values pull them closer to the middle.",
        "- `entry_buffer` is an extra offset beyond the aqua band. `0.0` means trade exactly at the band; `2.0` means wait for cRSI to move 2 points farther.",
        "- `exit_ratio` controls where inside the channel the position exits. `0.0` exits when cRSI re-crosses the entry-side aqua band, `0.5` exits near the middle, and `1.0` exits at the opposite aqua band.",
    ]
    OUT_REPORT.write_text("\n".join(report_lines) + "\n", encoding="utf-8")
    OUT_DIGEST.write_text("\n".join(digest_lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
