from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

BASE = Path(r"C:\Users\rabisaab\Downloads")
SOURCE = BASE / "QQQ_1min_20210308-20260308_sip (1).csv"
DATA_DIR = BASE / "data"
REPORTS_DIR = BASE / "reports"

OUTPUT_GRID = DATA_DIR / "qqq_wvf_long_short_grid.csv"
OUTPUT_TOP_FULL_LONG = DATA_DIR / "qqq_wvf_top_full_history_long.csv"
OUTPUT_TOP_FULL_SHORT = DATA_DIR / "qqq_wvf_top_full_history_short.csv"
OUTPUT_TOP_STABLE_LONG = DATA_DIR / "qqq_wvf_top_stability_long.csv"
OUTPUT_TOP_STABLE_SHORT = DATA_DIR / "qqq_wvf_top_stability_short.csv"
OUTPUT_TRADES_LONG = DATA_DIR / "qqq_wvf_best_stable_long_trades.csv"
OUTPUT_TRADES_SHORT = DATA_DIR / "qqq_wvf_best_stable_short_trades.csv"
OUTPUT_DAILY_LONG = DATA_DIR / "qqq_wvf_best_stable_long_daily_equity.csv"
OUTPUT_DAILY_SHORT = DATA_DIR / "qqq_wvf_best_stable_short_daily_equity.csv"
OUTPUT_REPORT = REPORTS_DIR / "qqq_wvf_backtest_report.md"

TIMEZONE = "America/New_York"
INITIAL_CAPITAL = 25_000.0
COST_BPS_PER_SIDE = 1.0

PINE_PD = 22
PINE_BBL = 20
PINE_LB = 50
PINE_PL = 1.01

TIMEFRAMES = (15, 30, 60)
MULT_VALUES = (2.0, 2.5, 3.0)
PH_VALUES = (0.85, 0.90)
TRIGGER_MODES = ("band", "percentile", "either")
LONG_CONFIRM_MODES = ("none", "close_up", "green_bar")
SHORT_CONFIRM_MODES = ("none", "close_down", "red_bar")
TREND_WINDOWS = (0, 20, 50)
HOLD_BARS = (4, 8)


@dataclass(frozen=True)
class StrategyConfig:
    variant_id: str
    side: str
    timeframe_minutes: int
    mult: float
    ph: float
    trigger_mode: str
    confirm_mode: str
    trend_window: int
    hold_bars: int
    cost_bps_per_side: float = COST_BPS_PER_SIDE
    initial_capital: float = INITIAL_CAPITAL


def safe_value(value: float) -> str:
    if pd.isna(value):
        return "nan"
    if np.isinf(value):
        return "inf"
    return f"{value:.2f}"


def load_bars() -> pd.DataFrame:
    frame = pd.read_csv(
        SOURCE,
        usecols=["timestamp_utc", "open", "high", "low", "close", "volume"],
    )
    frame["timestamp_utc"] = pd.to_datetime(frame["timestamp_utc"], utc=True)
    frame["timestamp_et"] = frame["timestamp_utc"].dt.tz_convert(TIMEZONE)
    et_time = frame["timestamp_et"].dt.time
    frame["in_rth"] = (et_time >= pd.Timestamp("09:30").time()) & (
        et_time < pd.Timestamp("16:00").time()
    )
    frame = frame.loc[frame["in_rth"]].copy()
    frame["session_date"] = frame["timestamp_et"].dt.tz_localize(None).dt.normalize()
    return frame.sort_values("timestamp_utc").reset_index(drop=True)


def resample_rth_bars(frame: pd.DataFrame, timeframe_minutes: int) -> pd.DataFrame:
    work = frame.loc[
        :,
        [
            "timestamp_utc",
            "timestamp_et",
            "session_date",
            "open",
            "high",
            "low",
            "close",
            "volume",
        ],
    ].copy()
    work["bucket"] = work.groupby("session_date").cumcount() // timeframe_minutes
    grouped = work.groupby(["session_date", "bucket"], sort=False)
    out = grouped.agg(
        open_time_utc=("timestamp_utc", "first"),
        close_time_utc=("timestamp_utc", "last"),
        open_time_et=("timestamp_et", "first"),
        close_time_et=("timestamp_et", "last"),
        open=("open", "first"),
        high=("high", "max"),
        low=("low", "min"),
        close=("close", "last"),
        volume=("volume", "sum"),
    )
    out = out.reset_index(drop=True)
    out["session_date"] = out["open_time_et"].dt.tz_localize(None).dt.normalize()
    out["ema_20"] = out["close"].ewm(span=20, adjust=False).mean()
    out["ema_50"] = out["close"].ewm(span=50, adjust=False).mean()
    out["prev_close"] = out["close"].shift(1)
    out["close_up"] = out["close"] > out["prev_close"]
    out["close_down"] = out["close"] < out["prev_close"]
    out["green_bar"] = out["close"] > out["open"]
    out["red_bar"] = out["close"] < out["open"]
    out["is_last_bar_of_day"] = out["session_date"].ne(out["session_date"].shift(-1))

    highest_close = out["close"].rolling(PINE_PD).max()
    out["wvf"] = (
        (highest_close - out["low"]) / highest_close.replace(0.0, np.nan)
    ) * 100.0
    out["wvf_mid"] = out["wvf"].rolling(PINE_BBL).mean()
    out["wvf_std"] = out["wvf"].rolling(PINE_BBL).std(ddof=0)
    out["wvf_high_roll"] = out["wvf"].rolling(PINE_LB).max()
    out["wvf_low_roll"] = out["wvf"].rolling(PINE_LB).min()
    return out


def build_windows(trading_dates: list[pd.Timestamp]) -> dict[str, tuple[pd.Timestamp, pd.Timestamp]]:
    start = pd.Timestamp(trading_dates[0]).normalize()
    end = pd.Timestamp(trading_dates[-1]).normalize()

    def nearest_start(days_back: int) -> pd.Timestamp:
        candidate = end - pd.Timedelta(days=days_back)
        for trade_date in trading_dates:
            ts = pd.Timestamp(trade_date).normalize()
            if ts >= candidate:
                return ts
        return start

    return {
        "full_history": (start, end),
        "last_1y": (nearest_start(365), end),
        "last_90d": (nearest_start(90), end),
        "ytd_2026": (pd.Timestamp("2026-01-02"), end),
    }


def summarize_performance(
    daily_equity: pd.DataFrame,
    trade_subset: pd.DataFrame,
    exposure_pct: float,
    initial_capital: float,
) -> dict[str, float]:
    if daily_equity.empty:
        return {
            "total_return_pct": 0.0,
            "cagr_pct": 0.0,
            "max_drawdown_pct": 0.0,
            "daily_sharpe": 0.0,
            "trade_count": 0,
            "win_rate_pct": 0.0,
            "profit_factor": 0.0,
            "avg_trade_return_pct": 0.0,
            "median_trade_return_pct": 0.0,
            "avg_trade_pnl": 0.0,
            "avg_hold_bars": 0.0,
            "avg_hold_minutes": 0.0,
            "exposure_pct": exposure_pct,
            "profitable_days_pct": 0.0,
            "avg_trades_per_day": 0.0,
            "final_equity": initial_capital,
        }

    returns = daily_equity["daily_return"].to_numpy(dtype=float)
    equity = daily_equity["equity"].to_numpy(dtype=float)
    final_equity = float(equity[-1])
    total_return_pct = (final_equity / initial_capital - 1.0) * 100.0
    years = max(
        (daily_equity["session_date"].iloc[-1] - daily_equity["session_date"].iloc[0]).days
        / 365.25,
        1.0 / 365.25,
    )
    cagr_pct = ((final_equity / initial_capital) ** (1.0 / years) - 1.0) * 100.0
    drawdown = daily_equity["equity"] / daily_equity["equity"].cummax() - 1.0
    max_drawdown_pct = abs(float(drawdown.min()) * 100.0)
    daily_sharpe = (
        float(returns.mean() / returns.std(ddof=0) * np.sqrt(252))
        if len(returns) > 1 and returns.std(ddof=0) > 0.0
        else 0.0
    )

    trade_count = int(len(trade_subset))
    if trade_count > 0:
        pnl = trade_subset["pnl_dollars"].to_numpy(dtype=float)
        trade_returns = trade_subset["return_pct"].to_numpy(dtype=float)
        hold_bars = trade_subset["bars_held"].to_numpy(dtype=float)
        hold_minutes = trade_subset["hold_minutes"].to_numpy(dtype=float)
        wins = pnl[pnl > 0.0]
        losses = pnl[pnl < 0.0]
        win_rate_pct = float((pnl > 0.0).mean() * 100.0)
        profit_factor = (
            float(wins.sum() / abs(losses.sum()))
            if len(losses) > 0
            else (float("inf") if len(wins) > 0 else 0.0)
        )
        avg_trade_return_pct = float(trade_returns.mean())
        median_trade_return_pct = float(np.median(trade_returns))
        avg_trade_pnl = float(pnl.mean())
        avg_hold_bars = float(hold_bars.mean())
        avg_hold_minutes = float(hold_minutes.mean())
    else:
        win_rate_pct = 0.0
        profit_factor = 0.0
        avg_trade_return_pct = 0.0
        median_trade_return_pct = 0.0
        avg_trade_pnl = 0.0
        avg_hold_bars = 0.0
        avg_hold_minutes = 0.0

    profitable_days_pct = float((daily_equity["daily_return"] > 0.0).mean() * 100.0)
    avg_trades_per_day = trade_count / max(len(daily_equity), 1)
    return {
        "total_return_pct": total_return_pct,
        "cagr_pct": cagr_pct,
        "max_drawdown_pct": max_drawdown_pct,
        "daily_sharpe": daily_sharpe,
        "trade_count": trade_count,
        "win_rate_pct": win_rate_pct,
        "profit_factor": profit_factor,
        "avg_trade_return_pct": avg_trade_return_pct,
        "median_trade_return_pct": median_trade_return_pct,
        "avg_trade_pnl": avg_trade_pnl,
        "avg_hold_bars": avg_hold_bars,
        "avg_hold_minutes": avg_hold_minutes,
        "exposure_pct": exposure_pct,
        "profitable_days_pct": profitable_days_pct,
        "avg_trades_per_day": avg_trades_per_day,
        "final_equity": final_equity,
    }


def window_metrics(
    daily_equity: pd.DataFrame,
    trades: pd.DataFrame,
    bar_sessions: pd.Series,
    in_position: np.ndarray,
    window_start: pd.Timestamp,
    window_end: pd.Timestamp,
    initial_capital: float,
) -> dict[str, float]:
    daily_mask = (daily_equity["session_date"] >= window_start) & (
        daily_equity["session_date"] <= window_end
    )
    daily_subset = daily_equity.loc[daily_mask].copy()
    if daily_subset.empty:
        return summarize_performance(
            daily_equity=daily_subset,
            trade_subset=trades.iloc[0:0].copy(),
            exposure_pct=0.0,
            initial_capital=initial_capital,
        )

    normalized_equity = initial_capital * np.cumprod(
        1.0 + daily_subset["daily_return"].to_numpy(dtype=float)
    )
    daily_subset["equity"] = normalized_equity

    if "entry_session_date" in trades.columns:
        trade_mask = (trades["entry_session_date"] >= window_start) & (
            trades["entry_session_date"] <= window_end
        )
        trade_subset = trades.loc[trade_mask].copy()
    else:
        trade_subset = trades.copy()

    bar_mask = (bar_sessions >= window_start) & (bar_sessions <= window_end)
    if bar_mask.any():
        exposure_pct = float(
            in_position[bar_mask.to_numpy(dtype=bool)].mean() * 100.0
        )
    else:
        exposure_pct = 0.0

    return summarize_performance(
        daily_equity=daily_subset,
        trade_subset=trade_subset,
        exposure_pct=exposure_pct,
        initial_capital=initial_capital,
    )


def simulate(frame: pd.DataFrame, config: StrategyConfig) -> dict[str, Any]:
    if frame.empty:
        empty_daily = pd.DataFrame(columns=["session_date", "equity", "daily_return"])
        empty_trades = pd.DataFrame()
        empty_metrics = summarize_performance(
            daily_equity=empty_daily,
            trade_subset=empty_trades,
            exposure_pct=0.0,
            initial_capital=config.initial_capital,
        )
        return {
            "metrics": empty_metrics,
            "daily_equity": empty_daily,
            "trades": empty_trades,
            "in_position": np.array([], dtype=bool),
        }

    opens = frame["open"].to_numpy(dtype=float)
    closes = frame["close"].to_numpy(dtype=float)
    wvf = frame["wvf"].to_numpy(dtype=float)
    wvf_mid = frame["wvf_mid"].to_numpy(dtype=float)
    wvf_std = frame["wvf_std"].to_numpy(dtype=float)
    wvf_high = frame["wvf_high_roll"].to_numpy(dtype=float)
    close_up = frame["close_up"].fillna(False).to_numpy(dtype=bool)
    close_down = frame["close_down"].fillna(False).to_numpy(dtype=bool)
    green_bar = frame["green_bar"].to_numpy(dtype=bool)
    red_bar = frame["red_bar"].to_numpy(dtype=bool)
    open_times = pd.to_datetime(frame["open_time_et"]).reset_index(drop=True)
    close_times = pd.to_datetime(frame["close_time_et"]).reset_index(drop=True)
    session_dates = pd.to_datetime(frame["session_date"]).reset_index(drop=True)

    upper_band = wvf_mid + config.mult * wvf_std
    range_high = wvf_high * config.ph
    band_trigger = wvf >= upper_band
    percentile_trigger = wvf >= range_high
    if config.trigger_mode == "band":
        trigger = band_trigger
    elif config.trigger_mode == "percentile":
        trigger = percentile_trigger
    else:
        trigger = band_trigger | percentile_trigger

    trigger_prev = np.zeros(len(frame), dtype=bool)
    trigger_prev[1:] = trigger[:-1]
    fresh_trigger = trigger & ~trigger_prev

    if config.side == "long":
        if config.confirm_mode == "close_up":
            confirmation = close_up
        elif config.confirm_mode == "green_bar":
            confirmation = green_bar
        else:
            confirmation = np.ones(len(frame), dtype=bool)
        if config.trend_window == 20:
            trend_ok = frame["close"].to_numpy(dtype=float) > frame["ema_20"].to_numpy(dtype=float)
        elif config.trend_window == 50:
            trend_ok = frame["close"].to_numpy(dtype=float) > frame["ema_50"].to_numpy(dtype=float)
        else:
            trend_ok = np.ones(len(frame), dtype=bool)
        entry_signal = fresh_trigger & confirmation & trend_ok
    else:
        if config.confirm_mode == "close_down":
            confirmation = close_down
        elif config.confirm_mode == "red_bar":
            confirmation = red_bar
        else:
            confirmation = np.ones(len(frame), dtype=bool)
        if config.trend_window == 20:
            trend_ok = frame["close"].to_numpy(dtype=float) < frame["ema_20"].to_numpy(dtype=float)
        elif config.trend_window == 50:
            trend_ok = frame["close"].to_numpy(dtype=float) < frame["ema_50"].to_numpy(dtype=float)
        else:
            trend_ok = np.ones(len(frame), dtype=bool)
        entry_signal = fresh_trigger & confirmation & trend_ok

    exit_signal = wvf <= wvf_mid
    position_sign = 1 if config.side == "long" else -1
    cost_rate = config.cost_bps_per_side / 10_000.0

    equity = float(config.initial_capital)
    in_position = np.zeros(len(frame), dtype=bool)
    equity_close = np.full(len(frame), np.nan, dtype=float)

    position = 0
    bars_held = 0
    pending_entry_idx: int | None = None
    pending_exit_idx: int | None = None
    pending_exit_reason: str | None = None
    entry_signal_idx: int | None = None
    entry_fill_idx: int | None = None
    entry_time: pd.Timestamp | None = None
    entry_price: float | None = None
    equity_before_trade: float | None = None
    trades: list[dict[str, Any]] = []

    def close_trade(
        exit_idx: int,
        exit_time: pd.Timestamp,
        exit_price: float,
        exit_equity: float,
        exit_reason: str,
    ) -> None:
        nonlocal position, bars_held, entry_signal_idx, entry_fill_idx
        nonlocal entry_time, entry_price, equity_before_trade

        if (
            position == 0
            or entry_signal_idx is None
            or entry_fill_idx is None
            or entry_time is None
            or entry_price is None
            or equity_before_trade is None
        ):
            return

        trades.append(
            {
                "variant_id": config.variant_id,
                "side": config.side,
                "timeframe_minutes": config.timeframe_minutes,
                "mult": config.mult,
                "ph": config.ph,
                "trigger_mode": config.trigger_mode,
                "confirm_mode": config.confirm_mode,
                "trend_window": config.trend_window,
                "hold_bars": config.hold_bars,
                "entry_signal_time": close_times.iloc[entry_signal_idx].isoformat(),
                "entry_time": entry_time.isoformat(),
                "entry_session_date": session_dates.iloc[entry_fill_idx].normalize(),
                "entry_price": entry_price,
                "entry_wvf": float(wvf[entry_signal_idx]),
                "entry_upper_band": float(upper_band[entry_signal_idx]),
                "entry_range_high": float(range_high[entry_signal_idx]),
                "exit_signal_time": close_times.iloc[exit_idx].isoformat(),
                "exit_time": exit_time.isoformat(),
                "exit_price": exit_price,
                "exit_wvf": float(wvf[exit_idx]),
                "exit_midline": float(wvf_mid[exit_idx]),
                "exit_reason": exit_reason,
                "bars_held": int(bars_held),
                "hold_minutes": float((exit_time - entry_time).total_seconds() / 60.0),
                "equity_before": float(equity_before_trade),
                "equity_after": float(exit_equity),
                "pnl_dollars": float(exit_equity - equity_before_trade),
                "return_pct": float((exit_equity / equity_before_trade - 1.0) * 100.0),
            }
        )
        position = 0
        bars_held = 0
        entry_signal_idx = None
        entry_fill_idx = None
        entry_time = None
        entry_price = None
        equity_before_trade = None

    for i in range(len(frame)):
        if pending_exit_idx is not None and position != 0:
            equity *= 1.0 - cost_rate
            close_trade(
                exit_idx=pending_exit_idx,
                exit_time=open_times.iloc[i],
                exit_price=opens[i],
                exit_equity=equity,
                exit_reason=str(pending_exit_reason or "signal_exit_next_open"),
            )
            pending_exit_idx = None
            pending_exit_reason = None

        if pending_entry_idx is not None and position == 0:
            equity_before_trade = equity
            equity *= 1.0 - cost_rate
            position = position_sign
            entry_signal_idx = pending_entry_idx
            entry_fill_idx = i
            entry_time = open_times.iloc[i]
            entry_price = opens[i]
            bars_held = 0
            pending_entry_idx = None

        in_position[i] = position != 0

        if position != 0:
            equity_bar_close = equity * (
                1.0 + position * (closes[i] / opens[i] - 1.0)
            )
        else:
            equity_bar_close = equity
        equity_close[i] = equity_bar_close

        if position != 0:
            bars_held += 1

        if i == len(frame) - 1:
            if position != 0:
                equity_bar_close *= 1.0 - cost_rate
                equity_close[i] = equity_bar_close
                close_trade(
                    exit_idx=i,
                    exit_time=close_times.iloc[i],
                    exit_price=closes[i],
                    exit_equity=equity_bar_close,
                    exit_reason="final_close",
                )
            equity = equity_close[i]
            break

        if position != 0 and pending_exit_idx is None:
            if exit_signal[i]:
                pending_exit_idx = i
                pending_exit_reason = "midline_next_open"
            elif bars_held >= config.hold_bars:
                pending_exit_idx = i
                pending_exit_reason = "hold_limit_next_open"

        if position == 0 and pending_entry_idx is None and entry_signal[i]:
            pending_entry_idx = i

        if position != 0:
            equity = equity_bar_close * (
                1.0 + position * (opens[i + 1] / closes[i] - 1.0)
            )
        else:
            equity = equity_bar_close

    last_day_mask = frame["is_last_bar_of_day"].to_numpy(dtype=bool)
    daily_equity = pd.DataFrame(
        {
            "session_date": pd.to_datetime(
                frame.loc[last_day_mask, "session_date"]
            ).reset_index(drop=True),
            "equity": equity_close[last_day_mask],
        }
    )
    daily_equity["daily_return"] = daily_equity["equity"].pct_change().fillna(
        daily_equity["equity"].iloc[0] / config.initial_capital - 1.0
    )

    trades_df = pd.DataFrame(trades)
    if not trades_df.empty:
        trades_df["entry_session_date"] = pd.to_datetime(trades_df["entry_session_date"])

    metrics = summarize_performance(
        daily_equity=daily_equity,
        trade_subset=trades_df,
        exposure_pct=float(in_position.mean() * 100.0),
        initial_capital=config.initial_capital,
    )
    return {
        "metrics": metrics,
        "daily_equity": daily_equity,
        "trades": trades_df,
        "in_position": in_position,
    }


def top_table(df: pd.DataFrame, sort_column: str, ascending: bool = False, top_n: int = 15) -> pd.DataFrame:
    cols = [
        "variant_id",
        "side",
        "timeframe_minutes",
        "mult",
        "ph",
        "trigger_mode",
        "confirm_mode",
        "trend_window",
        "hold_bars",
        "full_history_total_return_pct",
        "full_history_max_drawdown_pct",
        "full_history_daily_sharpe",
        "full_history_trade_count",
        "last_1y_total_return_pct",
        "last_90d_total_return_pct",
        "ytd_2026_total_return_pct",
        "stability_score",
        "positive_window_count",
    ]
    return (
        df.sort_values(sort_column, ascending=ascending)
        .head(top_n)
        .loc[:, cols]
        .reset_index(drop=True)
    )


def choose_best_stable(df: pd.DataFrame) -> pd.Series:
    eligible = df[
        (df["full_history_trade_count"] >= 10)
        & (df["positive_window_count"] == 4)
    ]
    if eligible.empty:
        eligible = df[
            (df["full_history_trade_count"] >= 10)
            & (df["positive_window_count"] >= 3)
        ]
    if eligible.empty:
        eligible = df[df["full_history_trade_count"] >= 10]
    if eligible.empty:
        eligible = df
    return eligible.sort_values(
        ["stability_score", "full_history_total_return_pct"],
        ascending=[True, False],
    ).iloc[0]


def describe_row(row: pd.Series) -> str:
    return (
        f"{row['variant_id']} | {int(row['timeframe_minutes'])}m | mult {row['mult']:.2f} | "
        f"ph {row['ph']:.2f} | {row['trigger_mode']} | {row['confirm_mode']} | "
        f"trend {int(row['trend_window'])} | hold {int(row['hold_bars'])}"
    )


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    bars = load_bars()
    trading_dates = sorted(pd.to_datetime(bars["session_date"]).unique())
    windows = build_windows(trading_dates)
    timeframe_frames = {
        timeframe: resample_rth_bars(bars, timeframe) for timeframe in TIMEFRAMES
    }

    results_rows: list[dict[str, Any]] = []
    full_results: dict[str, dict[str, Any]] = {}

    for side, confirm_modes in (
        ("long", LONG_CONFIRM_MODES),
        ("short", SHORT_CONFIRM_MODES),
    ):
        for timeframe in TIMEFRAMES:
            frame = timeframe_frames[timeframe]
            bar_sessions = pd.to_datetime(frame["session_date"])
            for mult in MULT_VALUES:
                for ph in PH_VALUES:
                    for trigger_mode in TRIGGER_MODES:
                        for confirm_mode in confirm_modes:
                            for trend_window in TREND_WINDOWS:
                                for hold_bars in HOLD_BARS:
                                    variant_id = (
                                        f"{side}_{timeframe}m_mult{mult:g}_ph{ph:g}_"
                                        f"{trigger_mode}_{confirm_mode}_ema{trend_window}_hold{hold_bars}"
                                    )
                                    config = StrategyConfig(
                                        variant_id=variant_id,
                                        side=side,
                                        timeframe_minutes=timeframe,
                                        mult=mult,
                                        ph=ph,
                                        trigger_mode=trigger_mode,
                                        confirm_mode=confirm_mode,
                                        trend_window=trend_window,
                                        hold_bars=hold_bars,
                                    )
                                    result = simulate(frame, config)
                                    full_results[variant_id] = result
                                    row: dict[str, Any] = {
                                        "variant_id": variant_id,
                                        "side": side,
                                        "timeframe_minutes": timeframe,
                                        "pd": PINE_PD,
                                        "bbl": PINE_BBL,
                                        "lb": PINE_LB,
                                        "pl": PINE_PL,
                                        "mult": mult,
                                        "ph": ph,
                                        "trigger_mode": trigger_mode,
                                        "confirm_mode": confirm_mode,
                                        "trend_window": trend_window,
                                        "hold_bars": hold_bars,
                                        "cost_bps_per_side": config.cost_bps_per_side,
                                    }
                                    for window_name, (window_start, window_end) in windows.items():
                                        metrics = window_metrics(
                                            daily_equity=result["daily_equity"],
                                            trades=result["trades"],
                                            bar_sessions=bar_sessions,
                                            in_position=result["in_position"],
                                            window_start=window_start,
                                            window_end=window_end,
                                            initial_capital=config.initial_capital,
                                        )
                                        for key, value in metrics.items():
                                            row[f"{window_name}_{key}"] = value
                                        row[f"{window_name}_start"] = window_start.date().isoformat()
                                        row[f"{window_name}_end"] = window_end.date().isoformat()
                                    results_rows.append(row)

    grid = pd.DataFrame(results_rows)
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
            grid.groupby("side")[column]
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
        grid.groupby("side")["stability_score"]
        .rank(method="min", ascending=True)
        .astype(int)
    )

    grid = grid.sort_values(
        ["side", "stability_score", "full_history_total_return_pct"],
        ascending=[True, True, False],
    ).reset_index(drop=True)
    grid.to_csv(OUTPUT_GRID, index=False)

    long_grid = grid[grid["side"] == "long"].reset_index(drop=True)
    short_grid = grid[grid["side"] == "short"].reset_index(drop=True)

    top_full_long = top_table(long_grid, "full_history_total_return_pct", ascending=False)
    top_full_short = top_table(short_grid, "full_history_total_return_pct", ascending=False)
    top_stable_long = top_table(long_grid, "stability_score", ascending=True)
    top_stable_short = top_table(short_grid, "stability_score", ascending=True)
    top_full_long.to_csv(OUTPUT_TOP_FULL_LONG, index=False)
    top_full_short.to_csv(OUTPUT_TOP_FULL_SHORT, index=False)
    top_stable_long.to_csv(OUTPUT_TOP_STABLE_LONG, index=False)
    top_stable_short.to_csv(OUTPUT_TOP_STABLE_SHORT, index=False)

    best_long = choose_best_stable(long_grid)
    best_short = choose_best_stable(short_grid)

    best_long_result = full_results[str(best_long["variant_id"])]
    best_short_result = full_results[str(best_short["variant_id"])]
    best_long_result["trades"].to_csv(OUTPUT_TRADES_LONG, index=False)
    best_short_result["trades"].to_csv(OUTPUT_TRADES_SHORT, index=False)
    best_long_result["daily_equity"].to_csv(OUTPUT_DAILY_LONG, index=False)
    best_short_result["daily_equity"].to_csv(OUTPUT_DAILY_SHORT, index=False)

    long_positive_all = int((long_grid["positive_window_count"] == 4).sum())
    short_positive_all = int((short_grid["positive_window_count"] == 4).sum())

    report_lines = [
        "# QQQ Williams Vix Fix Backtest",
        "",
        "## Setup",
        "",
        f"- Source data: `{SOURCE}`.",
        f"- Source bars loaded: `{len(bars):,}` regular-session 1-minute bars from `{bars['timestamp_et'].iloc[0]}` through `{bars['timestamp_et'].iloc[-1]}`.",
        f"- Pine inputs held at the pasted defaults unless noted: `pd={PINE_PD}`, `bbl={PINE_BBL}`, `lb={PINE_LB}`, `pl={PINE_PL}`.",
        f"- Optimized fields: timeframe `{TIMEFRAMES}`, `mult` `{MULT_VALUES}`, `ph` `{PH_VALUES}`, trigger mode `{TRIGGER_MODES}`, confirmation, trend filter, and hold bars `{HOLD_BARS}`.",
        "- Orders fill on the next bar open after the signal bar. Open positions are marked to each bar close and closed on the final sample close if still open.",
        f"- Transaction cost assumption: `{COST_BPS_PER_SIDE:.1f}` bp per side.",
        "",
        "## Best Long Variant",
        "",
        f"- Chosen for stability: `{describe_row(best_long)}`.",
        f"- Full-history return `{safe_value(float(best_long['full_history_total_return_pct']))}%`, max drawdown `{safe_value(float(best_long['full_history_max_drawdown_pct']))}%`, daily Sharpe `{safe_value(float(best_long['full_history_daily_sharpe']))}`, trades `{int(best_long['full_history_trade_count'])}`.",
        f"- Last 1y `{safe_value(float(best_long['last_1y_total_return_pct']))}%`, last 90d `{safe_value(float(best_long['last_90d_total_return_pct']))}%`, YTD 2026 `{safe_value(float(best_long['ytd_2026_total_return_pct']))}%`, stability score `{int(best_long['stability_score'])}`.",
        "",
        "## Best Short Variant",
        "",
        f"- Chosen for stability: `{describe_row(best_short)}`.",
        f"- Full-history return `{safe_value(float(best_short['full_history_total_return_pct']))}%`, max drawdown `{safe_value(float(best_short['full_history_max_drawdown_pct']))}%`, daily Sharpe `{safe_value(float(best_short['full_history_daily_sharpe']))}`, trades `{int(best_short['full_history_trade_count'])}`.",
        f"- Last 1y `{safe_value(float(best_short['last_1y_total_return_pct']))}%`, last 90d `{safe_value(float(best_short['last_90d_total_return_pct']))}%`, YTD 2026 `{safe_value(float(best_short['ytd_2026_total_return_pct']))}%`, stability score `{int(best_short['stability_score'])}`.",
        "",
        "## Coverage",
        "",
        f"- Total variants tested: `{len(grid)}`.",
        f"- Long variants positive in all four windows: `{long_positive_all}`.",
        f"- Short variants positive in all four windows: `{short_positive_all}`.",
        "",
        "## Full-History Leaders",
        "",
        "| Side | Variant | Full return | Max DD | Last 1y | Last 90d | YTD 2026 | Trades | Stability score |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        f"| Long | {top_full_long.iloc[0]['variant_id']} | {safe_value(float(top_full_long.iloc[0]['full_history_total_return_pct']))}% | {safe_value(float(top_full_long.iloc[0]['full_history_max_drawdown_pct']))}% | {safe_value(float(top_full_long.iloc[0]['last_1y_total_return_pct']))}% | {safe_value(float(top_full_long.iloc[0]['last_90d_total_return_pct']))}% | {safe_value(float(top_full_long.iloc[0]['ytd_2026_total_return_pct']))}% | {int(top_full_long.iloc[0]['full_history_trade_count'])} | {int(top_full_long.iloc[0]['stability_score'])} |",
        f"| Short | {top_full_short.iloc[0]['variant_id']} | {safe_value(float(top_full_short.iloc[0]['full_history_total_return_pct']))}% | {safe_value(float(top_full_short.iloc[0]['full_history_max_drawdown_pct']))}% | {safe_value(float(top_full_short.iloc[0]['last_1y_total_return_pct']))}% | {safe_value(float(top_full_short.iloc[0]['last_90d_total_return_pct']))}% | {safe_value(float(top_full_short.iloc[0]['ytd_2026_total_return_pct']))}% | {int(top_full_short.iloc[0]['full_history_trade_count'])} | {int(top_full_short.iloc[0]['stability_score'])} |",
        "",
        "## Output Files",
        "",
        f"- Full grid: `{OUTPUT_GRID}`",
        f"- Long full-history leaderboard: `{OUTPUT_TOP_FULL_LONG}`",
        f"- Short full-history leaderboard: `{OUTPUT_TOP_FULL_SHORT}`",
        f"- Long stability leaderboard: `{OUTPUT_TOP_STABLE_LONG}`",
        f"- Short stability leaderboard: `{OUTPUT_TOP_STABLE_SHORT}`",
        f"- Best stable long trades: `{OUTPUT_TRADES_LONG}`",
        f"- Best stable short trades: `{OUTPUT_TRADES_SHORT}`",
        f"- Best stable long daily equity: `{OUTPUT_DAILY_LONG}`",
        f"- Best stable short daily equity: `{OUTPUT_DAILY_SHORT}`",
        "",
    ]
    OUTPUT_REPORT.write_text("\n".join(report_lines), encoding="utf-8")

    preview_cols = [
        "variant_id",
        "side",
        "full_history_total_return_pct",
        "full_history_max_drawdown_pct",
        "last_1y_total_return_pct",
        "last_90d_total_return_pct",
        "ytd_2026_total_return_pct",
        "stability_score",
    ]
    print("Top long stability rows:")
    print(top_stable_long.loc[:, preview_cols].head(10).to_string(index=False))
    print()
    print("Top short stability rows:")
    print(top_stable_short.loc[:, preview_cols].head(10).to_string(index=False))
    print()
    print(f"Report: {OUTPUT_REPORT}")


if __name__ == "__main__":
    main()
