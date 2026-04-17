from __future__ import annotations

from datetime import time
from typing import Any

import numpy as np
import pandas as pd

from backtest_qqq_wvf import (
    DATA_DIR,
    REPORTS_DIR,
    SOURCE,
    StrategyConfig,
    build_windows,
    load_bars,
    safe_value,
    summarize_performance,
    window_metrics,
)
from backtest_qqq_wvf_core_params import (
    apply_indicator_params,
    build_base_resampled,
)

OUTPUT_GRID = DATA_DIR / "qqq_wvf_first_hour_timeframe_grid.csv"
OUTPUT_REPORT = REPORTS_DIR / "qqq_wvf_first_hour_timeframe_report.md"

FIRST_HOUR_END = time(10, 30)
TIMEFRAMES = (15, 30, 60)

SETUPS: tuple[dict[str, Any], ...] = (
    {
        "label": "best_long_stable_core",
        "side": "long",
        "pd_lookback": 44,
        "bb_length": 20,
        "lb_lookback": 20,
        "mult": 1.5,
        "ph": 0.90,
        "trigger_mode": "either",
        "confirm_mode": "none",
        "trend_window": 0,
        "hold_bars": 8,
    },
    {
        "label": "best_short_stable_core",
        "side": "short",
        "pd_lookback": 11,
        "bb_length": 30,
        "lb_lookback": 20,
        "mult": 2.5,
        "ph": 0.80,
        "trigger_mode": "band",
        "confirm_mode": "red_bar",
        "trend_window": 0,
        "hold_bars": 4,
    },
)


def simulate_first_hour(frame: pd.DataFrame, config: StrategyConfig) -> dict[str, Any]:
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

    allowed = close_times.dt.time < FIRST_HOUR_END
    same_day_next = session_dates.eq(session_dates.shift(-1))
    next_open_allowed = same_day_next & (open_times.shift(-1).dt.time < FIRST_HOUR_END)
    next_allowed_bar = same_day_next & allowed.shift(-1, fill_value=False)
    last_allowed_bar = allowed & ~next_allowed_bar
    last_bar_of_day = session_dates.ne(session_dates.shift(-1))

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

        if position != 0 and bool(last_allowed_bar.iloc[i]):
            equity_bar_close *= 1.0 - cost_rate
            equity_close[i] = equity_bar_close
            close_trade(
                exit_idx=i,
                exit_time=close_times.iloc[i],
                exit_price=closes[i],
                exit_equity=equity_bar_close,
                exit_reason="first_hour_close",
            )
            pending_exit_idx = None
            pending_exit_reason = None

        if bool(allowed.iloc[i]) and position != 0 and pending_exit_idx is None:
            if exit_signal[i] and bool(next_open_allowed.iloc[i]):
                pending_exit_idx = i
                pending_exit_reason = "midline_next_open"
            elif bars_held >= config.hold_bars and bool(next_open_allowed.iloc[i]):
                pending_exit_idx = i
                pending_exit_reason = "hold_limit_next_open"

        if (
            bool(allowed.iloc[i])
            and position == 0
            and pending_entry_idx is None
            and entry_signal[i]
            and bool(next_open_allowed.iloc[i])
        ):
            pending_entry_idx = i

        if i == len(frame) - 1:
            equity = equity_close[i]
            break

        if position != 0:
            same_day = session_dates.iloc[i + 1] == session_dates.iloc[i]
            if same_day:
                equity = equity_bar_close * (
                    1.0 + position * (opens[i + 1] / closes[i] - 1.0)
                )
            else:
                equity = equity_bar_close
        else:
            equity = equity_bar_close

    daily_equity = pd.DataFrame(
        {
            "session_date": session_dates[last_bar_of_day.to_numpy(dtype=bool)].reset_index(drop=True),
            "equity": equity_close[last_bar_of_day.to_numpy(dtype=bool)],
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


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    bars = load_bars()
    trading_dates = sorted(pd.to_datetime(bars["session_date"]).unique())
    windows = build_windows(trading_dates)
    base_frames = {timeframe: build_base_resampled(bars, timeframe) for timeframe in TIMEFRAMES}

    rows: list[dict[str, Any]] = []
    result_cache: dict[str, dict[str, Any]] = {}

    for setup in SETUPS:
        for timeframe in TIMEFRAMES:
            frame = apply_indicator_params(
                base_frames[timeframe],
                pd_lookback=int(setup["pd_lookback"]),
                bb_length=int(setup["bb_length"]),
                lb_lookback=int(setup["lb_lookback"]),
            )
            bar_sessions = pd.to_datetime(frame["session_date"])
            variant_id = f"{setup['label']}_{timeframe}m_first_hour"
            config = StrategyConfig(
                variant_id=variant_id,
                side=str(setup["side"]),
                timeframe_minutes=timeframe,
                mult=float(setup["mult"]),
                ph=float(setup["ph"]),
                trigger_mode=str(setup["trigger_mode"]),
                confirm_mode=str(setup["confirm_mode"]),
                trend_window=int(setup["trend_window"]),
                hold_bars=int(setup["hold_bars"]),
            )
            result = simulate_first_hour(frame, config)
            result_cache[variant_id] = result

            row: dict[str, Any] = {
                "variant_id": variant_id,
                "label": setup["label"],
                "side": setup["side"],
                "timeframe_minutes": timeframe,
                "first_hour_only": True,
                "pd_lookback": setup["pd_lookback"],
                "bb_length": setup["bb_length"],
                "lb_lookback": setup["lb_lookback"],
                "mult": setup["mult"],
                "ph": setup["ph"],
                "trigger_mode": setup["trigger_mode"],
                "confirm_mode": setup["confirm_mode"],
                "trend_window": setup["trend_window"],
                "hold_bars": setup["hold_bars"],
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
            rows.append(row)

    grid = pd.DataFrame(rows).sort_values(
        ["label", "timeframe_minutes"]
    ).reset_index(drop=True)
    grid.to_csv(OUTPUT_GRID, index=False)

    report_lines = [
        "# QQQ WVF First-Hour Backtest",
        "",
        f"- Source data: `{SOURCE}`.",
        "- Only the first trading hour was tradable. Entries were only allowed if the next-bar-open fill also stayed inside that first hour, and any open position was forced flat on the last bar that ended before 10:30 ET.",
        "",
        "| Label | Side | Timeframe | Full return | Max DD | Last 1y | Last 90d | YTD 2026 | Trades |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]

    for row in grid.itertuples():
        report_lines.append(
            f"| {row.label} | {row.side} | {row.timeframe_minutes}m | "
            f"{safe_value(float(row.full_history_total_return_pct))}% | "
            f"{safe_value(float(row.full_history_max_drawdown_pct))}% | "
            f"{safe_value(float(row.last_1y_total_return_pct))}% | "
            f"{safe_value(float(row.last_90d_total_return_pct))}% | "
            f"{safe_value(float(row.ytd_2026_total_return_pct))}% | "
            f"{int(row.full_history_trade_count)} |"
        )

    OUTPUT_REPORT.write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    print(grid[
        [
            "variant_id",
            "label",
            "side",
            "timeframe_minutes",
            "full_history_total_return_pct",
            "full_history_max_drawdown_pct",
            "last_1y_total_return_pct",
            "last_90d_total_return_pct",
            "ytd_2026_total_return_pct",
            "full_history_trade_count",
        ]
    ].to_string(index=False))
    print()
    print(f"Report: {OUTPUT_REPORT}")


if __name__ == "__main__":
    main()
