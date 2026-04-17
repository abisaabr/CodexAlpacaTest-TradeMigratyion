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
    TIMEZONE,
    build_windows,
    linreg_last,
    load_bars,
    safe_value,
)

OUTPUT_HIST_KC = DATA_DIR / "qqq_sqzmom_histogram_kc_length_sweep.csv"
OUTPUT_SQZ_LITERAL = DATA_DIR / "qqq_sqzmom_squeeze_param_grid_literal.csv"
OUTPUT_SQZ_CORRECTED = DATA_DIR / "qqq_sqzmom_squeeze_param_grid_corrected_bbmult.csv"
OUTPUT_REPORT = REPORTS_DIR / "qqq_sqzmom_indicator_param_report.md"

BUY_THRESHOLD = -0.02
SELL_THRESHOLD = 1.5
KC_LENGTH_SWEEP = (10, 15, 20, 25, 30, 40, 50)
BB_LENGTHS = (10, 20, 30)
BB_MULTS = (1.5, 2.0, 2.5)
KC_LENGTHS = (10, 20, 30)
KC_MULTS = (1.0, 1.5, 2.0)
USE_TRUE_RANGE_VALUES = (False, True)


def true_range(high: pd.Series, low: pd.Series, close: pd.Series) -> pd.Series:
    prev_close = close.shift(1)
    return pd.concat(
        [
            high - low,
            (high - prev_close).abs(),
            (low - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)


def prepare_param_frame(
    bars: pd.DataFrame,
    bb_length: int,
    bb_mult: float,
    kc_length: int,
    kc_mult: float,
    use_true_range: bool,
    formula_mode: str,
) -> pd.DataFrame:
    frame = bars.loc[
        bars["in_rth"],
        ["timestamp_utc", "timestamp_et", "session_date", "open", "high", "low", "close", "volume"],
    ].copy()

    source = frame["close"]
    basis = source.rolling(bb_length).mean()
    if formula_mode == "literal":
        dev_mult = kc_mult
    elif formula_mode == "corrected_bbmult":
        dev_mult = bb_mult
    else:
        raise ValueError(f"Unsupported formula mode: {formula_mode}")
    dev = source.rolling(bb_length).std(ddof=0) * dev_mult
    upper_bb = basis + dev
    lower_bb = basis - dev

    ma = source.rolling(kc_length).mean()
    if use_true_range:
        range_series = true_range(frame["high"], frame["low"], frame["close"])
    else:
        range_series = frame["high"] - frame["low"]
    range_ma = range_series.rolling(kc_length).mean()
    upper_kc = ma + range_ma * kc_mult
    lower_kc = ma - range_ma * kc_mult

    highest = frame["high"].rolling(kc_length).max()
    lowest = frame["low"].rolling(kc_length).min()
    close_sma = frame["close"].rolling(kc_length).mean()
    mean_source = ((highest + lowest) / 2.0 + close_sma) / 2.0
    deviation_source = (frame["close"] - mean_source).to_numpy(dtype=float)
    frame["val"] = linreg_last(deviation_source, kc_length)

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
    frame["sqz_on"] = (lower_bb > lower_kc) & (upper_bb < upper_kc)
    frame["sqz_off"] = (lower_bb < lower_kc) & (upper_bb > upper_kc)
    frame["no_sqz"] = (~frame["sqz_on"]) & (~frame["sqz_off"])
    frame["is_last_bar_of_day"] = frame["session_date"].ne(frame["session_date"].shift(-1))
    return frame.reset_index(drop=True)


def simulate_long_only(
    frame: pd.DataFrame,
    buy_threshold: float,
    sell_threshold: float,
    entry_mask: pd.Series | None = None,
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
    last_bar = frame["is_last_bar_of_day"].to_numpy(dtype=bool)

    dark_red_turn = (colors == "maroon") & (prev_colors == "red")
    dark_green_turn = (colors == "green") & (prev_colors == "lime")
    allowed_entries = np.ones(len(frame), dtype=bool) if entry_mask is None else entry_mask.to_numpy(dtype=bool)
    entry_signal = dark_red_turn & (vals > buy_threshold) & allowed_entries
    exit_signal = dark_green_turn & (vals > sell_threshold)

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
        equity_close[i] = shares * closes[i] if shares > 0.0 else cash

        if i == len(frame) - 1:
            continue

        if shares == 0.0 and entry_signal[i]:
            if not last_bar[i]:
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
    daily_returns = daily_equity["equity"].pct_change().fillna(daily_equity["equity"].iloc[0] / INITIAL_CAPITAL - 1.0)
    daily_pnl = daily_equity["equity"].diff().fillna(daily_equity["equity"].iloc[0] - INITIAL_CAPITAL)
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


def summarize_grid(grid: pd.DataFrame) -> tuple[dict[str, Any], pd.DataFrame]:
    grid = grid.copy()
    grid["positive_window_count"] = (
        (grid["full_history_total_return_pct"] > 0.0).astype(int)
        + (grid["last_1y_total_return_pct"] > 0.0).astype(int)
        + (grid["last_90d_total_return_pct"] > 0.0).astype(int)
        + (grid["ytd_2026_total_return_pct"] > 0.0).astype(int)
    )
    best_full = grid.sort_values("full_history_total_return_pct", ascending=False).iloc[0].to_dict()
    positive_all = grid[grid["positive_window_count"] == 4].sort_values("full_history_total_return_pct", ascending=False)
    return best_full, positive_all


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    bars = load_bars()
    rth_dates = sorted(pd.to_datetime(bars.loc[bars["in_rth"], "session_date"]).unique())
    windows = build_windows(rth_dates)

    hist_rows: list[dict[str, Any]] = []
    for kc_length in KC_LENGTH_SWEEP:
        frame = prepare_param_frame(
            bars=bars,
            bb_length=20,
            bb_mult=2.0,
            kc_length=kc_length,
            kc_mult=1.5,
            use_true_range=True,
            formula_mode="literal",
        )
        row: dict[str, Any] = {
            "kc_length": kc_length,
            "buy_threshold": BUY_THRESHOLD,
            "sell_threshold": SELL_THRESHOLD,
        }
        for window_name, (start_date, end_date) in windows.items():
            window_frame = frame[
                (pd.to_datetime(frame["session_date"]) >= start_date)
                & (pd.to_datetime(frame["session_date"]) <= end_date)
            ].reset_index(drop=True)
            result = simulate_long_only(window_frame, BUY_THRESHOLD, SELL_THRESHOLD)
            for key, value in result["metrics"].items():
                row[f"{window_name}_{key}"] = value
            row[f"{window_name}_start"] = start_date.date().isoformat()
            row[f"{window_name}_end"] = end_date.date().isoformat()
        hist_rows.append(row)
    hist_df = pd.DataFrame(hist_rows).sort_values("full_history_total_return_pct", ascending=False)
    hist_df.to_csv(OUTPUT_HIST_KC, index=False)

    formula_outputs = {
        "literal": OUTPUT_SQZ_LITERAL,
        "corrected_bbmult": OUTPUT_SQZ_CORRECTED,
    }
    formula_grids: dict[str, pd.DataFrame] = {}
    formula_best: dict[str, dict[str, Any]] = {}
    formula_positive_all: dict[str, pd.DataFrame] = {}

    for formula_mode, output_path in formula_outputs.items():
        rows: list[dict[str, Any]] = []
        for bb_length in BB_LENGTHS:
            for bb_mult in BB_MULTS:
                for kc_length in KC_LENGTHS:
                    for kc_mult in KC_MULTS:
                        for use_true_range in USE_TRUE_RANGE_VALUES:
                            frame = prepare_param_frame(
                                bars=bars,
                                bb_length=bb_length,
                                bb_mult=bb_mult,
                                kc_length=kc_length,
                                kc_mult=kc_mult,
                                use_true_range=use_true_range,
                                formula_mode=formula_mode,
                            )
                            row: dict[str, Any] = {
                                "formula_mode": formula_mode,
                                "bb_length": bb_length,
                                "bb_mult": bb_mult,
                                "kc_length": kc_length,
                                "kc_mult": kc_mult,
                                "use_true_range": use_true_range,
                                "buy_threshold": BUY_THRESHOLD,
                                "sell_threshold": SELL_THRESHOLD,
                            }
                            for window_name, (start_date, end_date) in windows.items():
                                window_frame = frame[
                                    (pd.to_datetime(frame["session_date"]) >= start_date)
                                    & (pd.to_datetime(frame["session_date"]) <= end_date)
                                ].reset_index(drop=True)
                                result = simulate_long_only(
                                    window_frame,
                                    BUY_THRESHOLD,
                                    SELL_THRESHOLD,
                                    entry_mask=window_frame["sqz_off"],
                                )
                                for key, value in result["metrics"].items():
                                    row[f"{window_name}_{key}"] = value
                                row[f"{window_name}_start"] = start_date.date().isoformat()
                                row[f"{window_name}_end"] = end_date.date().isoformat()
                            rows.append(row)
        grid = pd.DataFrame(rows).sort_values("full_history_total_return_pct", ascending=False).reset_index(drop=True)
        grid.to_csv(output_path, index=False)
        formula_grids[formula_mode] = grid
        best_full, positive_all = summarize_grid(grid)
        formula_best[formula_mode] = best_full
        formula_positive_all[formula_mode] = positive_all

    hist_best = hist_df.iloc[0].to_dict()
    literal_best = formula_best["literal"]
    corrected_best = formula_best["corrected_bbmult"]
    literal_positive_all = formula_positive_all["literal"]
    corrected_positive_all = formula_positive_all["corrected_bbmult"]

    report_lines = [
        "# QQQ SQZMOM Indicator Parameter Sweep",
        "",
        "## Assumptions",
        "",
        "- Market: QQQ 1-minute regular-session bars only.",
        f"- Trade rule baseline: buy on `red -> maroon` when `val > {BUY_THRESHOLD}`, sell on `lime -> green` when `val > {SELL_THRESHOLD}`.",
        "- Histogram-only sweep keeps the original long-only rule and varies only `KC Length` because that is the only indicator input that changes `val`.",
        "- Full squeeze-aware sweep adds an entry filter: the long entry is only allowed when `sqzOff` is true on the signal bar.",
        f"- Friction: `{COST_BPS_PER_SIDE:.1f}` bp per side.",
        "",
        "## Histogram-only `KC Length` sweep",
        "",
        f"- Best `KC Length`: `{int(hist_best['kc_length'])}`.",
        f"- Full-history return: `{safe_value(float(hist_best['full_history_total_return_pct']))}%`.",
        f"- Last 1y return: `{safe_value(float(hist_best['last_1y_total_return_pct']))}%`.",
        f"- Last 90d return: `{safe_value(float(hist_best['last_90d_total_return_pct']))}%`.",
        f"- YTD 2026 return: `{safe_value(float(hist_best['ytd_2026_total_return_pct']))}%`.",
        "",
        "## Full squeeze-aware grid, literal pasted code",
        "",
        f"- Best full-history row: BB Length `{int(literal_best['bb_length'])}`, BB Mult `{literal_best['bb_mult']}`, KC Length `{int(literal_best['kc_length'])}`, KC Mult `{literal_best['kc_mult']}`, Use TrueRange `{bool(literal_best['use_true_range'])}`.",
        f"- Full-history return: `{safe_value(float(literal_best['full_history_total_return_pct']))}%`, max DD `{safe_value(float(literal_best['full_history_max_drawdown_pct']))}%`, last 1y `{safe_value(float(literal_best['last_1y_total_return_pct']))}%`, last 90d `{safe_value(float(literal_best['last_90d_total_return_pct']))}%`, YTD 2026 `{safe_value(float(literal_best['ytd_2026_total_return_pct']))}%`.",
        f"- Positive in all four windows: `{len(literal_positive_all)}` rows.",
        "",
        "## Full squeeze-aware grid, corrected BB multiplier",
        "",
        f"- Best full-history row: BB Length `{int(corrected_best['bb_length'])}`, BB Mult `{corrected_best['bb_mult']}`, KC Length `{int(corrected_best['kc_length'])}`, KC Mult `{corrected_best['kc_mult']}`, Use TrueRange `{bool(corrected_best['use_true_range'])}`.",
        f"- Full-history return: `{safe_value(float(corrected_best['full_history_total_return_pct']))}%`, max DD `{safe_value(float(corrected_best['full_history_max_drawdown_pct']))}%`, last 1y `{safe_value(float(corrected_best['last_1y_total_return_pct']))}%`, last 90d `{safe_value(float(corrected_best['last_90d_total_return_pct']))}%`, YTD 2026 `{safe_value(float(corrected_best['ytd_2026_total_return_pct']))}%`.",
        f"- Positive in all four windows: `{len(corrected_positive_all)}` rows.",
        "",
        "## Key read",
        "",
        "- If the literal-code sweep shows identical performance across different `BB Mult` values, that confirms the pasted script is not actually using `BB MultFactor` in its current form.",
        "- The corrected-BB run is included only to show what changes if that line is fixed to use the BB multiplier the way the original indicator is usually written.",
        "",
        "## Output files",
        "",
        f"- Histogram-only KC sweep: `{OUTPUT_HIST_KC}`",
        f"- Full squeeze-aware literal grid: `{OUTPUT_SQZ_LITERAL}`",
        f"- Full squeeze-aware corrected-BB grid: `{OUTPUT_SQZ_CORRECTED}`",
        "",
    ]

    OUTPUT_REPORT.write_text("\n".join(report_lines), encoding="utf-8")

    print("Histogram KC sweep top rows")
    print(hist_df[["kc_length", "full_history_total_return_pct", "last_1y_total_return_pct", "last_90d_total_return_pct", "ytd_2026_total_return_pct"]].head(10).to_string(index=False))
    print()
    print("Literal squeeze-aware top rows")
    print(formula_grids["literal"][["bb_length", "bb_mult", "kc_length", "kc_mult", "use_true_range", "full_history_total_return_pct", "last_1y_total_return_pct", "last_90d_total_return_pct", "ytd_2026_total_return_pct"]].head(10).to_string(index=False))
    print()
    print("Corrected-BB squeeze-aware top rows")
    print(formula_grids["corrected_bbmult"][["bb_length", "bb_mult", "kc_length", "kc_mult", "use_true_range", "full_history_total_return_pct", "last_1y_total_return_pct", "last_90d_total_return_pct", "ytd_2026_total_return_pct"]].head(10).to_string(index=False))
    print()
    print(f"Report: {OUTPUT_REPORT}")


if __name__ == "__main__":
    main()
