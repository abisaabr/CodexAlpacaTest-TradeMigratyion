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
OUTPUT_METRICS = DATA_DIR / "qqq_sqzmom_threshold_sweep.csv"
OUTPUT_TRADES_SWING = DATA_DIR / "qqq_sqzmom_trades_threshold_neg4_rth_swing.csv"
OUTPUT_TRADES_INTRADAY = DATA_DIR / "qqq_sqzmom_trades_threshold_neg4_rth_intraday.csv"
OUTPUT_DAILY_SWING = DATA_DIR / "qqq_sqzmom_daily_equity_threshold_neg4_rth_swing.csv"
OUTPUT_DAILY_INTRADAY = DATA_DIR / "qqq_sqzmom_daily_equity_threshold_neg4_rth_intraday.csv"
OUTPUT_YEARLY = DATA_DIR / "qqq_sqzmom_yearly_stats.csv"
OUTPUT_COST_SENSITIVITY = DATA_DIR / "qqq_sqzmom_cost_sensitivity.csv"
OUTPUT_REPORT = REPORTS_DIR / "qqq_sqzmom_backtest_report.md"

TIMEZONE = "America/New_York"
LENGTH = 20
INITIAL_CAPITAL = 25_000.0
COST_BPS_PER_SIDE = 1.0
ENTRY_THRESHOLDS = (-4.0, -2.0, -1.0, -0.5, -0.25, -0.10, -0.05)
COST_SENSITIVITY_BPS = (0.0, 0.25, 0.5, 0.75, 1.0)
SESSION_MODES = (
    ("rth_swing", False),
    ("rth_intraday", True),
)


@dataclass(frozen=True)
class StrategyConfig:
    variant_id: str
    entry_threshold: float
    force_flat_eod: bool
    exit_threshold: float = 0.0
    cost_bps_per_side: float = COST_BPS_PER_SIDE
    initial_capital: float = INITIAL_CAPITAL


def linreg_last(values: np.ndarray, length: int) -> np.ndarray:
    arr = np.asarray(values, dtype=float)
    n = length
    x = np.arange(n, dtype=float)
    sx = float(x.sum())
    sxx = float((x * x).sum())
    denom = n * sxx - sx * sx
    sy = np.convolve(arr, np.ones(n, dtype=float), mode="valid")
    sxy = np.correlate(arr, x, mode="valid")
    slope = (n * sxy - sx * sy) / denom
    intercept = (sy - slope * sx) / n
    out = np.full(arr.shape, np.nan, dtype=float)
    out[n - 1 :] = intercept + slope * (n - 1)
    return out


def load_bars() -> pd.DataFrame:
    df = pd.read_csv(
        SOURCE,
        usecols=["timestamp_utc", "open", "high", "low", "close", "volume"],
    )
    df["timestamp_utc"] = pd.to_datetime(df["timestamp_utc"], utc=True)
    df["timestamp_et"] = df["timestamp_utc"].dt.tz_convert(TIMEZONE)
    df["session_date"] = df["timestamp_et"].dt.date
    et_time = df["timestamp_et"].dt.time
    df["in_rth"] = (et_time >= pd.Timestamp("09:30").time()) & (
        et_time < pd.Timestamp("16:00").time()
    )
    return df.sort_values("timestamp_utc").reset_index(drop=True)


def prepare_indicator_frame(bars: pd.DataFrame, session: str) -> pd.DataFrame:
    if session != "rth":
        raise ValueError(f"Unsupported session: {session}")

    frame = bars.loc[bars["in_rth"], ["timestamp_utc", "timestamp_et", "session_date", "open", "high", "low", "close", "volume"]].copy()
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
    frame["is_last_bar_of_day"] = frame["session_date"].ne(
        frame["session_date"].shift(-1)
    )
    return frame.reset_index(drop=True)


def simulate(frame: pd.DataFrame, config: StrategyConfig) -> dict[str, Any]:
    if frame.empty:
        empty_daily = pd.DataFrame(columns=["session_date", "equity"])
        empty_trades = pd.DataFrame()
        return {
            "metrics": {
                "variant_id": config.variant_id,
                "entry_threshold": config.entry_threshold,
                "exit_threshold": config.exit_threshold,
                "force_flat_eod": config.force_flat_eod,
                "cost_bps_per_side": config.cost_bps_per_side,
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
                "avg_hold_minutes": 0.0,
                "avg_bars_held": 0.0,
                "exposure_pct": 0.0,
                "profitable_days_pct": 0.0,
                "avg_trades_per_day": 0.0,
                "dark_red_turns": 0,
                "eligible_dark_red_turns": 0,
                "eligible_dark_red_share_pct": 0.0,
                "dark_green_turns": 0,
                "final_equity": config.initial_capital,
            },
            "trades": empty_trades,
            "daily_equity": empty_daily,
        }

    timestamps = pd.to_datetime(frame["timestamp_et"]).reset_index(drop=True)
    dates = pd.to_datetime(frame["session_date"]).reset_index(drop=True)
    opens = frame["open"].to_numpy(dtype=float)
    closes = frame["close"].to_numpy(dtype=float)
    vals = frame["val"].to_numpy(dtype=float)
    colors = frame["color"].to_numpy(dtype=object)
    prev_colors = frame["prev_color"].to_numpy(dtype=object)
    last_bar = frame["is_last_bar_of_day"].to_numpy(dtype=bool)

    dark_red_turn = (colors == "maroon") & (prev_colors == "red")
    dark_green_turn = (colors == "green") & (prev_colors == "lime")
    entry_signal = dark_red_turn & (vals > config.entry_threshold)
    exit_signal = dark_green_turn & (vals > config.exit_threshold)

    cash = float(config.initial_capital)
    shares = 0.0
    cost_rate = config.cost_bps_per_side / 10_000.0
    equity_close = np.full(len(frame), np.nan, dtype=float)
    in_market = np.zeros(len(frame), dtype=bool)

    pending_action: str | None = None
    pending_signal_idx: int | None = None

    entry_fill_idx: int | None = None
    entry_signal_idx: int | None = None
    entry_time: pd.Timestamp | None = None
    entry_price: float | None = None
    entry_equity: float | None = None
    trades: list[dict[str, Any]] = []

    def close_trade(exit_idx: int, exit_price: float, exit_time_value: pd.Timestamp, reason: str, add_current_bar: bool) -> None:
        nonlocal cash, shares, entry_fill_idx, entry_signal_idx, entry_time, entry_price, entry_equity

        if shares <= 0.0 or entry_time is None or entry_price is None or entry_equity is None:
            return

        cash = shares * exit_price * (1.0 - cost_rate)
        equity_after = cash
        bars_held = max(0, exit_idx - int(entry_fill_idx or 0)) + (1 if add_current_bar else 0)
        trades.append(
            {
                "variant_id": config.variant_id,
                "entry_threshold": config.entry_threshold,
                "exit_threshold": config.exit_threshold,
                "force_flat_eod": config.force_flat_eod,
                "entry_signal_time": timestamps.iloc[int(entry_signal_idx or 0)].isoformat(),
                "entry_time": entry_time.isoformat(),
                "entry_price": entry_price,
                "entry_val": float(vals[int(entry_signal_idx or 0)]),
                "exit_signal_time": timestamps.iloc[exit_idx].isoformat(),
                "exit_time": exit_time_value.isoformat(),
                "exit_price": exit_price,
                "exit_val": float(vals[exit_idx]),
                "exit_reason": reason,
                "bars_held": bars_held,
                "hold_minutes": float((exit_time_value - entry_time).total_seconds() / 60.0),
                "equity_before": entry_equity,
                "equity_after": equity_after,
                "pnl_dollars": equity_after - entry_equity,
                "return_pct": (equity_after / entry_equity - 1.0) * 100.0,
            }
        )
        shares = 0.0
        entry_fill_idx = None
        entry_signal_idx = None
        entry_time = None
        entry_price = None
        entry_equity = None

    for i in range(len(frame)):
        if pending_action == "entry" and shares == 0.0:
            shares = cash / (opens[i] * (1.0 + cost_rate))
            entry_fill_idx = i
            entry_signal_idx = pending_signal_idx
            entry_time = timestamps.iloc[i]
            entry_price = opens[i]
            entry_equity = cash
            cash = 0.0
            pending_action = None
            pending_signal_idx = None
        elif pending_action == "exit" and shares > 0.0:
            close_trade(
                exit_idx=i,
                exit_price=opens[i],
                exit_time_value=timestamps.iloc[i],
                reason="dark_green_next_open",
                add_current_bar=False,
            )
            pending_action = None
            pending_signal_idx = None

        in_market[i] = shares > 0.0

        if config.force_flat_eod and shares > 0.0 and last_bar[i]:
            close_trade(
                exit_idx=i,
                exit_price=closes[i],
                exit_time_value=timestamps.iloc[i] + pd.Timedelta(minutes=1),
                reason="eod_close",
                add_current_bar=True,
            )
            equity_close[i] = cash
            pending_action = None
            pending_signal_idx = None
            continue

        equity_close[i] = shares * closes[i] if shares > 0.0 else cash

        if i == len(frame) - 1:
            continue

        if shares == 0.0 and entry_signal[i]:
            if not (config.force_flat_eod and last_bar[i]):
                pending_action = "entry"
                pending_signal_idx = i
        elif shares > 0.0 and exit_signal[i]:
            pending_action = "exit"
            pending_signal_idx = i

    if shares > 0.0:
        close_trade(
            exit_idx=len(frame) - 1,
            exit_price=closes[-1],
            exit_time_value=timestamps.iloc[-1] + pd.Timedelta(minutes=1),
            reason="final_close",
            add_current_bar=True,
        )
        equity_close[-1] = cash

    daily_equity = (
        pd.DataFrame(
            {
                "session_date": dates.dt.date,
                "equity": equity_close,
            }
        )
        .groupby("session_date", as_index=False)
        .last()
    )

    trade_df = pd.DataFrame(trades)
    daily_returns = daily_equity["equity"].pct_change().fillna(
        daily_equity["equity"].iloc[0] / config.initial_capital - 1.0
    )
    daily_pnl = daily_equity["equity"].diff().fillna(
        daily_equity["equity"].iloc[0] - config.initial_capital
    )

    equity_series = pd.Series(equity_close)
    drawdown = equity_series / equity_series.cummax() - 1.0
    total_days = max(1.0, (dates.iloc[-1] - dates.iloc[0]).days / 365.25)

    gross_profit = float(trade_df.loc[trade_df["pnl_dollars"] > 0.0, "pnl_dollars"].sum()) if not trade_df.empty else 0.0
    gross_loss = float(trade_df.loc[trade_df["pnl_dollars"] < 0.0, "pnl_dollars"].sum()) if not trade_df.empty else 0.0

    metrics = {
        "variant_id": config.variant_id,
        "entry_threshold": config.entry_threshold,
        "exit_threshold": config.exit_threshold,
        "force_flat_eod": config.force_flat_eod,
        "cost_bps_per_side": config.cost_bps_per_side,
        "total_return_pct": (cash / config.initial_capital - 1.0) * 100.0,
        "cagr_pct": ((cash / config.initial_capital) ** (1.0 / total_days) - 1.0) * 100.0,
        "max_drawdown_pct": abs(float(drawdown.min()) * 100.0),
        "daily_sharpe": float(daily_returns.mean() / daily_returns.std(ddof=0) * np.sqrt(252.0))
        if len(daily_returns) > 1 and daily_returns.std(ddof=0) > 0.0
        else 0.0,
        "trade_count": int(len(trade_df)),
        "win_rate_pct": float((trade_df["pnl_dollars"] > 0.0).mean() * 100.0) if not trade_df.empty else 0.0,
        "profit_factor": float(gross_profit / abs(gross_loss)) if gross_loss < 0.0 else (float("inf") if gross_profit > 0.0 else 0.0),
        "avg_trade_return_pct": float(trade_df["return_pct"].mean()) if not trade_df.empty else 0.0,
        "median_trade_return_pct": float(trade_df["return_pct"].median()) if not trade_df.empty else 0.0,
        "avg_trade_pnl": float(trade_df["pnl_dollars"].mean()) if not trade_df.empty else 0.0,
        "avg_hold_minutes": float(trade_df["hold_minutes"].mean()) if not trade_df.empty else 0.0,
        "avg_bars_held": float(trade_df["bars_held"].mean()) if not trade_df.empty else 0.0,
        "exposure_pct": float(in_market.mean() * 100.0),
        "profitable_days_pct": float((daily_pnl > 0.0).mean() * 100.0),
        "avg_trades_per_day": float(len(trade_df) / len(daily_equity)) if len(daily_equity) else 0.0,
        "dark_red_turns": int(dark_red_turn.sum()),
        "eligible_dark_red_turns": int(entry_signal.sum()),
        "eligible_dark_red_share_pct": float(entry_signal.sum() / dark_red_turn.sum() * 100.0)
        if dark_red_turn.sum() > 0
        else 0.0,
        "dark_green_turns": int(dark_green_turn.sum()),
        "final_equity": float(cash),
    }

    return {
        "metrics": metrics,
        "trades": trade_df,
        "daily_equity": daily_equity.assign(daily_return=daily_returns, daily_pnl=daily_pnl),
    }


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


def summarize_yearly(daily_equity: pd.DataFrame, initial_capital: float, variant_id: str) -> pd.DataFrame:
    if daily_equity.empty:
        return pd.DataFrame()

    work = daily_equity.copy()
    work["session_date"] = pd.to_datetime(work["session_date"])
    work["year"] = work["session_date"].dt.year
    work["daily_return"] = work["equity"].pct_change().fillna(
        work["equity"].iloc[0] / initial_capital - 1.0
    )

    rows: list[dict[str, Any]] = []
    for year, group in work.groupby("year"):
        compounded = float(np.prod(1.0 + group["daily_return"].to_numpy()) - 1.0)
        dd = group["equity"] / group["equity"].cummax() - 1.0
        rows.append(
            {
                "variant_id": variant_id,
                "year": int(year),
                "sessions": int(len(group)),
                "year_return_pct": compounded * 100.0,
                "year_max_drawdown_pct": abs(float(dd.min()) * 100.0),
                "year_end_equity": float(group["equity"].iloc[-1]),
            }
        )
    return pd.DataFrame(rows)


def safe_value(value: float) -> str:
    if pd.isna(value):
        return "nan"
    if np.isinf(value):
        return "inf"
    return f"{value:.2f}"


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    bars = load_bars()
    rth_dates = sorted(pd.to_datetime(bars.loc[bars["in_rth"], "session_date"]).unique())
    windows = build_windows(rth_dates)
    indicator_frame = prepare_indicator_frame(bars, session="rth")

    metrics_rows: list[dict[str, Any]] = []
    selected_outputs: dict[str, dict[str, Any]] = {}

    for mode_name, force_flat_eod in SESSION_MODES:
        for threshold in ENTRY_THRESHOLDS:
            variant_key = f"{mode_name}_threshold_{threshold:g}"
            config = StrategyConfig(
                variant_id=variant_key,
                entry_threshold=threshold,
                force_flat_eod=force_flat_eod,
            )
            row: dict[str, Any] = {
                "variant_id": variant_key,
                "session_mode": "rth",
                "force_flat_eod": force_flat_eod,
                "entry_threshold": threshold,
                "cost_bps_per_side": config.cost_bps_per_side,
            }
            for window_name, (start_date, end_date) in windows.items():
                window_frame = indicator_frame[
                    (pd.to_datetime(indicator_frame["session_date"]) >= start_date)
                    & (pd.to_datetime(indicator_frame["session_date"]) <= end_date)
                ].reset_index(drop=True)
                result = simulate(window_frame, config)
                metrics = result["metrics"]
                for key, value in metrics.items():
                    if key in {"variant_id", "entry_threshold", "exit_threshold", "force_flat_eod", "cost_bps_per_side"}:
                        continue
                    row[f"{window_name}_{key}"] = value
                row[f"{window_name}_start"] = start_date.date().isoformat()
                row[f"{window_name}_end"] = end_date.date().isoformat()

                if threshold == -4.0 and window_name == "full_history":
                    selected_outputs[mode_name] = result

            metrics_rows.append(row)

    metrics_df = pd.DataFrame(metrics_rows).sort_values(
        ["force_flat_eod", "full_history_total_return_pct"],
        ascending=[True, False],
    )

    for metric_name in ("total_return_pct", "daily_sharpe", "max_drawdown_pct"):
        ascending = metric_name == "max_drawdown_pct"
        metrics_df[f"full_history_{metric_name}_rank"] = (
            metrics_df.groupby("force_flat_eod")[f"full_history_{metric_name}"]
            .rank(method="min", ascending=ascending)
            .astype(int)
        )

    metrics_df.to_csv(OUTPUT_METRICS, index=False)

    swing_result = selected_outputs["rth_swing"]
    intraday_result = selected_outputs["rth_intraday"]
    swing_result["trades"].to_csv(OUTPUT_TRADES_SWING, index=False)
    intraday_result["trades"].to_csv(OUTPUT_TRADES_INTRADAY, index=False)
    swing_result["daily_equity"].to_csv(OUTPUT_DAILY_SWING, index=False)
    intraday_result["daily_equity"].to_csv(OUTPUT_DAILY_INTRADAY, index=False)

    yearly_df = pd.concat(
        [
            summarize_yearly(
                swing_result["daily_equity"],
                INITIAL_CAPITAL,
                "rth_swing_threshold_-4",
            ),
            summarize_yearly(
                intraday_result["daily_equity"],
                INITIAL_CAPITAL,
                "rth_intraday_threshold_-4",
            ),
        ],
        ignore_index=True,
    )
    yearly_df.to_csv(OUTPUT_YEARLY, index=False)

    cost_rows: list[dict[str, Any]] = []
    for mode_name, force_flat_eod in SESSION_MODES:
        for cost_bps in COST_SENSITIVITY_BPS:
            result = simulate(
                indicator_frame,
                StrategyConfig(
                    variant_id=f"{mode_name}_threshold_-4_cost_{cost_bps:g}",
                    entry_threshold=-4.0,
                    force_flat_eod=force_flat_eod,
                    cost_bps_per_side=cost_bps,
                ),
            )
            metrics = result["metrics"]
            cost_rows.append(
                {
                    "mode_name": mode_name,
                    "force_flat_eod": force_flat_eod,
                    "entry_threshold": -4.0,
                    "exit_threshold": 0.0,
                    "cost_bps_per_side": cost_bps,
                    "total_return_pct": metrics["total_return_pct"],
                    "cagr_pct": metrics["cagr_pct"],
                    "max_drawdown_pct": metrics["max_drawdown_pct"],
                    "daily_sharpe": metrics["daily_sharpe"],
                    "trade_count": metrics["trade_count"],
                    "win_rate_pct": metrics["win_rate_pct"],
                }
            )
    cost_df = pd.DataFrame(cost_rows)
    cost_df.to_csv(OUTPUT_COST_SENSITIVITY, index=False)

    example_rows = metrics_df[metrics_df["entry_threshold"] == -4.0].copy()
    best_full_return = (
        metrics_df.sort_values("full_history_total_return_pct", ascending=False)
        .iloc[0]
        .to_dict()
    )
    best_last_year = (
        metrics_df.sort_values("last_1y_total_return_pct", ascending=False)
        .iloc[0]
        .to_dict()
    )
    intraday_example = example_rows.loc[example_rows["force_flat_eod"]].iloc[0].to_dict()
    swing_example = example_rows.loc[~example_rows["force_flat_eod"]].iloc[0].to_dict()
    zero_cost_swing = cost_df[
        (cost_df["mode_name"] == "rth_swing")
        & (cost_df["cost_bps_per_side"] == 0.0)
    ].iloc[0].to_dict()
    quarter_bp_swing = cost_df[
        (cost_df["mode_name"] == "rth_swing")
        & (cost_df["cost_bps_per_side"] == 0.25)
    ].iloc[0].to_dict()

    exact_pass_rate = float(swing_example["full_history_eligible_dark_red_share_pct"])
    report_lines = [
        "# QQQ Squeeze Momentum Backtest",
        "",
        "## Rule interpretation used",
        "",
        "- Indicator recreated from the LazyBear histogram `val`; the squeeze-state cross was not used for entries or exits.",
        "- `dark red` was treated as the `maroon` histogram state: `val <= 0` and `val >= val[1]`.",
        "- `dark green` was treated as the `green` histogram state: `val > 0` and `val <= val[1]`.",
        "- To match `turns dark red` / `turns dark green`, signals only fire on color transitions: `red -> maroon` for entry and `lime -> green` for exit.",
        "- Orders execute on the next bar open. The intraday variant also forces a flat exit on the last regular-session bar.",
        f"- Transaction cost assumption: `{COST_BPS_PER_SIDE:.1f}` bp per side.",
        "",
        "## Exact `>-4` rule",
        "",
        "| Variant | Full return | CAGR | Max DD | Daily Sharpe | Trades | Win rate | Exposure | Last 1y return | Last 90d return |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        f"| RTH swing | {safe_value(float(swing_example['full_history_total_return_pct']))}% | {safe_value(float(swing_example['full_history_cagr_pct']))}% | {safe_value(float(swing_example['full_history_max_drawdown_pct']))}% | {safe_value(float(swing_example['full_history_daily_sharpe']))} | {int(swing_example['full_history_trade_count'])} | {safe_value(float(swing_example['full_history_win_rate_pct']))}% | {safe_value(float(swing_example['full_history_exposure_pct']))}% | {safe_value(float(swing_example['last_1y_total_return_pct']))}% | {safe_value(float(swing_example['last_90d_total_return_pct']))}% |",
        f"| RTH intraday | {safe_value(float(intraday_example['full_history_total_return_pct']))}% | {safe_value(float(intraday_example['full_history_cagr_pct']))}% | {safe_value(float(intraday_example['full_history_max_drawdown_pct']))}% | {safe_value(float(intraday_example['full_history_daily_sharpe']))} | {int(intraday_example['full_history_trade_count'])} | {safe_value(float(intraday_example['full_history_win_rate_pct']))}% | {safe_value(float(intraday_example['full_history_exposure_pct']))}% | {safe_value(float(intraday_example['last_1y_total_return_pct']))}% | {safe_value(float(intraday_example['last_90d_total_return_pct']))}% |",
        "",
        "## Cost sensitivity for the exact `>-4` rule",
        "",
        "| Variant | Cost/side (bps) | Full return | CAGR | Max DD | Daily Sharpe |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]

    for row in cost_df.itertuples():
        label = "RTH swing" if row.mode_name == "rth_swing" else "RTH intraday"
        report_lines.append(
            f"| {label} | {safe_value(float(row.cost_bps_per_side))} | {safe_value(float(row.total_return_pct))}% | {safe_value(float(row.cagr_pct))}% | {safe_value(float(row.max_drawdown_pct))}% | {safe_value(float(row.daily_sharpe))} |"
        )

    report_lines += [
        "",
        "## Threshold sweep takeaways",
        "",
        f"- On regular-session bars, the `>-4` filter passed `{exact_pass_rate:.2f}%` of all dark-red turns, so it behaves almost like an unfiltered `red -> maroon` entry rule.",
        f"- The swing version is only mildly positive at zero assumed friction: `{safe_value(float(zero_cost_swing['total_return_pct']))}%` total return with `{safe_value(float(zero_cost_swing['max_drawdown_pct']))}%` max drawdown.",
        f"- It is already negative by `{safe_value(float(quarter_bp_swing['cost_bps_per_side']))}` bp per side: `{safe_value(float(quarter_bp_swing['total_return_pct']))}%` total return. That means the raw edge is too thin for real-world execution unless fills are unusually favorable.",
        f"- Best full-history return in this sweep: `{best_full_return['variant_id']}` at `{safe_value(float(best_full_return['full_history_total_return_pct']))}%` with `{safe_value(float(best_full_return['full_history_max_drawdown_pct']))}%` max drawdown.",
        f"- Best last-1-year return in this sweep: `{best_last_year['variant_id']}` at `{safe_value(float(best_last_year['last_1y_total_return_pct']))}%`.",
        "- If the full-history winner and recent winner differ, that is a warning that the threshold is not especially stable and may be getting fit to one slice of the sample.",
        "",
        "## Output files",
        "",
        f"- Sweep metrics: `{OUTPUT_METRICS}`",
        f"- Exact `>-4` swing trades: `{OUTPUT_TRADES_SWING}`",
        f"- Exact `>-4` intraday trades: `{OUTPUT_TRADES_INTRADAY}`",
        f"- Exact `>-4` swing daily equity: `{OUTPUT_DAILY_SWING}`",
        f"- Exact `>-4` intraday daily equity: `{OUTPUT_DAILY_INTRADAY}`",
        f"- Year-by-year stats for both exact-rule variants: `{OUTPUT_YEARLY}`",
        f"- Cost sensitivity for the exact `>-4` rule: `{OUTPUT_COST_SENSITIVITY}`",
        "",
    ]

    OUTPUT_REPORT.write_text("\n".join(report_lines), encoding="utf-8")

    preview_columns = [
        "variant_id",
        "full_history_total_return_pct",
        "full_history_cagr_pct",
        "full_history_max_drawdown_pct",
        "full_history_daily_sharpe",
        "full_history_trade_count",
        "last_1y_total_return_pct",
        "last_90d_total_return_pct",
    ]
    print(metrics_df[preview_columns].to_string(index=False))
    print()
    print(f"Report: {OUTPUT_REPORT}")


if __name__ == "__main__":
    main()
