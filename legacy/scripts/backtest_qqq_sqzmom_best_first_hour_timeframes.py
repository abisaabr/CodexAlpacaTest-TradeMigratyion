from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from backtest_qqq_sqzmom import (
    COST_BPS_PER_SIDE,
    DATA_DIR,
    INITIAL_CAPITAL,
    REPORTS_DIR,
    build_windows,
    safe_value,
)
from gridtest_qqq_sqzmom_long_short_timeframes import build_indicator_frame as build_timeframe_bars
from sweep_qqq_sqzmom_indicator_params import prepare_param_frame

SOURCE = Path(r"C:\Users\rabisaab\Downloads\QQQ_1min_20210308-20260308_sip (1).csv")
OUTPUT_METRICS = DATA_DIR / "qqq_sqzmom_best_settings_first_hour_timeframes.csv"
OUTPUT_TRADES = DATA_DIR / "qqq_sqzmom_best_settings_first_hour_best_trades.csv"
OUTPUT_DAILY = DATA_DIR / "qqq_sqzmom_best_settings_first_hour_best_daily_equity.csv"
OUTPUT_REPORT = REPORTS_DIR / "qqq_sqzmom_best_settings_first_hour_timeframes_report.md"

TIMEFRAMES = (1, 2, 5, 15, 60)
MODES = (
    ("full_session_reference", False),
    ("first_hour_entry_only", False),
    ("first_hour_flat", True),
)
BEST_SETTINGS = {
    "bb_length": 20,
    "bb_mult": 2.0,
    "kc_length": 20,
    "kc_mult": 1.0,
    "use_true_range": False,
    "formula_mode": "corrected_bbmult",
}
BUY_THRESHOLD = -0.02
SELL_THRESHOLD = 1.5
FIRST_HOUR_END = pd.Timestamp("10:30").time()


def load_raw_bars() -> pd.DataFrame:
    bars = pd.read_csv(
        SOURCE,
        usecols=["timestamp_utc", "open", "high", "low", "close", "volume"],
    )
    bars["timestamp_utc"] = pd.to_datetime(bars["timestamp_utc"], utc=True)
    bars["timestamp_et"] = bars["timestamp_utc"].dt.tz_convert("America/New_York")
    bars["session_date"] = bars["timestamp_et"].dt.date
    time_values = bars["timestamp_et"].dt.time
    bars["in_rth"] = (time_values >= pd.Timestamp("09:30").time()) & (
        time_values < pd.Timestamp("16:00").time()
    )
    return bars.sort_values("timestamp_utc").reset_index(drop=True)


def build_param_frame_for_timeframe(raw_bars: pd.DataFrame, timeframe_minutes: int) -> pd.DataFrame:
    if timeframe_minutes == 1:
        frame = prepare_param_frame(bars=raw_bars, **BEST_SETTINGS)
    else:
        timeframe_bars = build_timeframe_bars(raw_bars, timeframe_minutes)
        timeframe_bars["in_rth"] = True
        frame = prepare_param_frame(bars=timeframe_bars, **BEST_SETTINGS)
    frame["bar_time"] = pd.to_datetime(frame["timestamp_et"]).dt.time
    frame["first_hour_mask"] = frame["bar_time"] < FIRST_HOUR_END
    next_first_hour_mask = frame["first_hour_mask"].shift(-1).eq(True)
    frame["first_hour_end_bar"] = frame["first_hour_mask"] & (
        frame["session_date"].ne(frame["session_date"].shift(-1))
        | (~next_first_hour_mask)
    )
    return frame.reset_index(drop=True)


def simulate_long_only_window(
    frame: pd.DataFrame,
    entry_mask: pd.Series,
    force_flat_mask: pd.Series | None = None,
    cost_bps_per_side: float = COST_BPS_PER_SIDE,
) -> dict[str, Any]:
    if frame.empty:
        return {
            "metrics": {
                "total_return_pct": 0.0,
                "cagr_pct": 0.0,
                "max_drawdown_pct": 0.0,
                "daily_sharpe": 0.0,
                "trade_count": 0,
                "win_rate_pct": 0.0,
                "profit_factor": 0.0,
                "avg_trade_pnl": 0.0,
                "avg_hold_minutes": 0.0,
                "exposure_pct": 0.0,
                "profitable_days_pct": 0.0,
                "eligible_entry_share_pct": 0.0,
                "final_equity": INITIAL_CAPITAL,
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
    force_flat = np.zeros(len(frame), dtype=bool) if force_flat_mask is None else force_flat_mask.to_numpy(dtype=bool)
    allowed_entries = entry_mask.to_numpy(dtype=bool)

    dark_red_turn = (colors == "maroon") & (prev_colors == "red")
    dark_green_turn = (colors == "green") & (prev_colors == "lime")
    entry_signal = dark_red_turn & (vals > BUY_THRESHOLD) & allowed_entries
    exit_signal = dark_green_turn & (vals > SELL_THRESHOLD)

    cash = float(INITIAL_CAPITAL)
    shares = 0.0
    cost_rate = cost_bps_per_side / 10_000.0
    equity_close = np.full(len(frame), np.nan, dtype=float)
    in_market = np.zeros(len(frame), dtype=bool)

    pending_action: str | None = None
    pending_signal_idx: int | None = None
    entry_time: pd.Timestamp | None = None
    entry_price: float | None = None
    entry_equity: float | None = None
    entry_signal_idx: int | None = None
    trades: list[dict[str, Any]] = []

    def close_trade(exit_idx: int, exit_price: float, exit_time_value: pd.Timestamp, reason: str) -> None:
        nonlocal cash, shares, entry_time, entry_price, entry_equity, entry_signal_idx
        if shares <= 0.0 or entry_time is None or entry_price is None or entry_equity is None:
            return
        cash = shares * exit_price * (1.0 - cost_rate)
        trades.append(
            {
                "entry_signal_time": timestamps.iloc[int(entry_signal_idx or 0)].isoformat(),
                "entry_time": entry_time.isoformat(),
                "entry_price": entry_price,
                "entry_val": float(vals[int(entry_signal_idx or 0)]),
                "exit_signal_time": timestamps.iloc[exit_idx].isoformat(),
                "exit_time": exit_time_value.isoformat(),
                "exit_price": exit_price,
                "exit_val": float(vals[exit_idx]),
                "exit_reason": reason,
                "hold_minutes": float((exit_time_value - entry_time).total_seconds() / 60.0),
                "equity_before": entry_equity,
                "equity_after": cash,
                "pnl_dollars": cash - entry_equity,
                "return_pct": (cash / entry_equity - 1.0) * 100.0,
            }
        )
        shares = 0.0
        entry_time = None
        entry_price = None
        entry_equity = None
        entry_signal_idx = None

    for i in range(len(frame)):
        if pending_action == "entry" and shares == 0.0:
            shares = cash / (opens[i] * (1.0 + cost_rate))
            entry_time = timestamps.iloc[i]
            entry_price = opens[i]
            entry_equity = cash
            entry_signal_idx = pending_signal_idx
            cash = 0.0
            pending_action = None
            pending_signal_idx = None
        elif pending_action == "exit" and shares > 0.0:
            close_trade(i, opens[i], timestamps.iloc[i], "dark_green_next_open")
            pending_action = None
            pending_signal_idx = None

        in_market[i] = shares > 0.0

        if force_flat[i]:
            if shares > 0.0:
                close_trade(i, closes[i], timestamps.iloc[i] + pd.Timedelta(minutes=1), "first_hour_close")
            pending_action = None
            pending_signal_idx = None

        equity_close[i] = shares * closes[i] if shares > 0.0 else cash

        if i == len(frame) - 1:
            continue

        if shares == 0.0 and entry_signal[i]:
            pending_action = "entry"
            pending_signal_idx = i
        elif shares > 0.0 and exit_signal[i]:
            pending_action = "exit"
            pending_signal_idx = i

    if shares > 0.0:
        close_trade(len(frame) - 1, closes[-1], timestamps.iloc[-1] + pd.Timedelta(minutes=1), "final_close")
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
        "total_return_pct": (cash / INITIAL_CAPITAL - 1.0) * 100.0,
        "cagr_pct": ((cash / INITIAL_CAPITAL) ** (1.0 / total_years) - 1.0) * 100.0,
        "max_drawdown_pct": abs(float(drawdown.min()) * 100.0),
        "daily_sharpe": float(daily_returns.mean() / daily_returns.std(ddof=0) * np.sqrt(252.0))
        if len(daily_returns) > 1 and daily_returns.std(ddof=0) > 0.0
        else 0.0,
        "trade_count": int(len(trade_df)),
        "win_rate_pct": float((trade_df["pnl_dollars"] > 0.0).mean() * 100.0) if not trade_df.empty else 0.0,
        "profit_factor": float(gross_profit / abs(gross_loss)) if gross_loss < 0.0 else (float("inf") if gross_profit > 0.0 else 0.0),
        "avg_trade_pnl": float(trade_df["pnl_dollars"].mean()) if not trade_df.empty else 0.0,
        "avg_hold_minutes": float(trade_df["hold_minutes"].mean()) if not trade_df.empty else 0.0,
        "exposure_pct": float(in_market.mean() * 100.0),
        "profitable_days_pct": float((daily_pnl > 0.0).mean() * 100.0),
        "eligible_entry_share_pct": float(entry_signal.sum() / dark_red_turn.sum() * 100.0) if dark_red_turn.sum() > 0 else 0.0,
        "final_equity": float(cash),
    }
    return {
        "metrics": metrics,
        "trades": trade_df,
        "daily_equity": daily_equity.assign(daily_return=daily_returns, daily_pnl=daily_pnl),
    }


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    raw_bars = load_raw_bars()
    windows = build_windows(sorted(pd.to_datetime(raw_bars.loc[raw_bars["in_rth"], "session_date"]).unique()))
    timeframe_frames = {
        timeframe: build_param_frame_for_timeframe(raw_bars, timeframe)
        for timeframe in TIMEFRAMES
    }

    rows: list[dict[str, Any]] = []
    best_variant_result: dict[str, Any] | None = None
    best_variant_row: dict[str, Any] | None = None

    for timeframe, frame in timeframe_frames.items():
        for mode_name, use_force_flat in MODES:
            row: dict[str, Any] = {
                "timeframe_minutes": timeframe,
                "mode_name": mode_name,
                "bb_length": BEST_SETTINGS["bb_length"],
                "bb_mult": BEST_SETTINGS["bb_mult"],
                "kc_length": BEST_SETTINGS["kc_length"],
                "kc_mult": BEST_SETTINGS["kc_mult"],
                "use_true_range": BEST_SETTINGS["use_true_range"],
                "buy_threshold": BUY_THRESHOLD,
                "sell_threshold": SELL_THRESHOLD,
                "cost_bps_per_side": COST_BPS_PER_SIDE,
            }
            full_history_result: dict[str, Any] | None = None

            for window_name, (start_date, end_date) in windows.items():
                window_frame = frame[
                    (pd.to_datetime(frame["session_date"]) >= start_date)
                    & (pd.to_datetime(frame["session_date"]) <= end_date)
                ].reset_index(drop=True)

                if mode_name == "full_session_reference":
                    entry_mask = window_frame["sqz_off"]
                    force_flat_mask = None
                elif mode_name == "first_hour_entry_only":
                    entry_mask = window_frame["sqz_off"] & window_frame["first_hour_mask"]
                    force_flat_mask = None
                elif mode_name == "first_hour_flat":
                    entry_mask = window_frame["sqz_off"] & window_frame["first_hour_mask"]
                    force_flat_mask = window_frame["first_hour_end_bar"]
                else:
                    raise ValueError(f"Unsupported mode: {mode_name}")

                result = simulate_long_only_window(
                    frame=window_frame,
                    entry_mask=entry_mask,
                    force_flat_mask=force_flat_mask,
                )
                for key, value in result["metrics"].items():
                    row[f"{window_name}_{key}"] = value
                row[f"{window_name}_start"] = start_date.date().isoformat()
                row[f"{window_name}_end"] = end_date.date().isoformat()

                if window_name == "full_history":
                    full_history_result = result

            rows.append(row)
            if best_variant_row is None or row["full_history_total_return_pct"] > best_variant_row["full_history_total_return_pct"]:
                best_variant_row = row
                best_variant_result = full_history_result

    metrics_df = pd.DataFrame(rows).sort_values(
        ["mode_name", "full_history_total_return_pct"],
        ascending=[True, False],
    ).reset_index(drop=True)
    metrics_df.to_csv(OUTPUT_METRICS, index=False)

    if best_variant_result is not None:
        best_variant_result["trades"].to_csv(OUTPUT_TRADES, index=False)
        best_variant_result["daily_equity"].to_csv(OUTPUT_DAILY, index=False)

    report_lines = [
        "# QQQ SQZMOM Best Settings First-Hour Backtest",
        "",
        "## Settings used",
        "",
        f"- Best corrected indicator inputs from the prior sweep: BB Length `{BEST_SETTINGS['bb_length']}`, BB Mult `{BEST_SETTINGS['bb_mult']}`, KC Length `{BEST_SETTINGS['kc_length']}`, KC Mult `{BEST_SETTINGS['kc_mult']}`, Use TrueRange `{BEST_SETTINGS['use_true_range']}`.",
        f"- Entry rule: buy on `red -> maroon` when `val > {BUY_THRESHOLD}` and `sqzOff` is true.",
        f"- Exit rule: sell on `lime -> green` when `val > {SELL_THRESHOLD}`.",
        "- Execution: next-bar-open fills, 1 bp per side.",
        "- First-hour window: `09:30` through `10:29:59` America/New_York.",
        "- `first_hour_entry_only` means the entry signal must occur inside the first hour, but the position can exit later.",
        "- `first_hour_flat` means entries are only taken from first-hour signals and any open position is forcibly closed on the last bar that starts before `10:30`.",
        "",
        "## Results",
        "",
        "| Mode | TF | Full return | CAGR | Max DD | Trades | Last 1y | Last 90d | YTD 2026 |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]

    for row in metrics_df.itertuples():
        report_lines.append(
            f"| {row.mode_name} | {int(row.timeframe_minutes)}m | {safe_value(float(row.full_history_total_return_pct))}% | {safe_value(float(row.full_history_cagr_pct))}% | {safe_value(float(row.full_history_max_drawdown_pct))}% | {int(row.full_history_trade_count)} | {safe_value(float(row.last_1y_total_return_pct))}% | {safe_value(float(row.last_90d_total_return_pct))}% | {safe_value(float(row.ytd_2026_total_return_pct))}% |"
        )

    if best_variant_row is not None:
        report_lines.extend(
            [
                "",
                "## Best Full-History Row",
                "",
                f"- Mode `{best_variant_row['mode_name']}`, timeframe `{int(best_variant_row['timeframe_minutes'])}m`.",
                f"- Full-history return `{safe_value(float(best_variant_row['full_history_total_return_pct']))}%`, CAGR `{safe_value(float(best_variant_row['full_history_cagr_pct']))}%`, max DD `{safe_value(float(best_variant_row['full_history_max_drawdown_pct']))}%`, trades `{int(best_variant_row['full_history_trade_count'])}`.",
                f"- Last 1y `{safe_value(float(best_variant_row['last_1y_total_return_pct']))}%`, last 90d `{safe_value(float(best_variant_row['last_90d_total_return_pct']))}%`, YTD 2026 `{safe_value(float(best_variant_row['ytd_2026_total_return_pct']))}%`.",
                "",
            ]
        )

    report_lines.extend(
        [
            "## Output files",
            "",
            f"- Metrics: `{OUTPUT_METRICS}`",
            f"- Trades for the best full-history row: `{OUTPUT_TRADES}`",
            f"- Daily equity for the best full-history row: `{OUTPUT_DAILY}`",
            "",
        ]
    )
    OUTPUT_REPORT.write_text("\n".join(report_lines), encoding="utf-8")

    preview_cols = [
        "mode_name",
        "timeframe_minutes",
        "full_history_total_return_pct",
        "full_history_cagr_pct",
        "full_history_max_drawdown_pct",
        "full_history_trade_count",
        "last_1y_total_return_pct",
        "last_90d_total_return_pct",
        "ytd_2026_total_return_pct",
    ]
    print(metrics_df[preview_cols].to_string(index=False))
    print()
    print(f"Report: {OUTPUT_REPORT}")


if __name__ == "__main__":
    main()
