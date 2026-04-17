from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from backtest_qqq_wvf import (
    DATA_DIR,
    OUTPUT_REPORT,
    REPORTS_DIR,
    SOURCE,
    PINE_PL,
    StrategyConfig,
    build_windows,
    load_bars,
    safe_value,
    simulate,
    window_metrics,
)

OUTPUT_GRID = DATA_DIR / "qqq_wvf_core_params_grid.csv"
OUTPUT_TOP_LONG = DATA_DIR / "qqq_wvf_core_params_top_long.csv"
OUTPUT_TOP_SHORT = DATA_DIR / "qqq_wvf_core_params_top_short.csv"
OUTPUT_TRADES_LONG = DATA_DIR / "qqq_wvf_core_params_best_long_trades.csv"
OUTPUT_TRADES_SHORT = DATA_DIR / "qqq_wvf_core_params_best_short_trades.csv"
OUTPUT_DAILY_LONG = DATA_DIR / "qqq_wvf_core_params_best_long_daily_equity.csv"
OUTPUT_DAILY_SHORT = DATA_DIR / "qqq_wvf_core_params_best_short_daily_equity.csv"
OUTPUT_SUMMARY = REPORTS_DIR / "qqq_wvf_core_params_report.md"

PD_VALUES = (11, 22, 34, 44)
BBL_VALUES = (10, 20, 30)
LB_VALUES = (20, 50, 100)
MULT_VALUES = (1.5, 2.0, 2.5, 3.0)
PH_VALUES = (0.80, 0.85, 0.90, 0.95)

ARCHETYPES: tuple[dict[str, Any], ...] = (
    {
        "archetype": "long_stable_60m",
        "side": "long",
        "timeframe_minutes": 60,
        "trigger_mode": "either",
        "confirm_mode": "none",
        "trend_window": 0,
        "hold_bars": 8,
    },
    {
        "archetype": "long_fast_30m",
        "side": "long",
        "timeframe_minutes": 30,
        "trigger_mode": "either",
        "confirm_mode": "green_bar",
        "trend_window": 0,
        "hold_bars": 8,
    },
    {
        "archetype": "long_trend_60m",
        "side": "long",
        "timeframe_minutes": 60,
        "trigger_mode": "either",
        "confirm_mode": "none",
        "trend_window": 50,
        "hold_bars": 8,
    },
    {
        "archetype": "short_stable_15m",
        "side": "short",
        "timeframe_minutes": 15,
        "trigger_mode": "band",
        "confirm_mode": "red_bar",
        "trend_window": 0,
        "hold_bars": 4,
    },
    {
        "archetype": "short_allwindows_60m",
        "side": "short",
        "timeframe_minutes": 60,
        "trigger_mode": "band",
        "confirm_mode": "red_bar",
        "trend_window": 50,
        "hold_bars": 4,
    },
    {
        "archetype": "short_full_15m",
        "side": "short",
        "timeframe_minutes": 15,
        "trigger_mode": "band",
        "confirm_mode": "red_bar",
        "trend_window": 50,
        "hold_bars": 8,
    },
)


def build_base_resampled(frame: pd.DataFrame, timeframe_minutes: int) -> pd.DataFrame:
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
    return out


def apply_indicator_params(
    base_frame: pd.DataFrame,
    pd_lookback: int,
    bb_length: int,
    lb_lookback: int,
) -> pd.DataFrame:
    frame = base_frame.copy()
    highest_close = frame["close"].rolling(pd_lookback).max()
    frame["wvf"] = (
        (highest_close - frame["low"]) / highest_close.replace(0.0, np.nan)
    ) * 100.0
    frame["wvf_mid"] = frame["wvf"].rolling(bb_length).mean()
    frame["wvf_std"] = frame["wvf"].rolling(bb_length).std(ddof=0)
    frame["wvf_high_roll"] = frame["wvf"].rolling(lb_lookback).max()
    frame["wvf_low_roll"] = frame["wvf"].rolling(lb_lookback).min()
    return frame


def top_table(df: pd.DataFrame, top_n: int = 15) -> pd.DataFrame:
    cols = [
        "variant_id",
        "archetype",
        "side",
        "timeframe_minutes",
        "pd_lookback",
        "bb_length",
        "lb_lookback",
        "mult",
        "ph",
        "full_history_total_return_pct",
        "full_history_max_drawdown_pct",
        "last_1y_total_return_pct",
        "last_90d_total_return_pct",
        "ytd_2026_total_return_pct",
        "full_history_trade_count",
        "positive_window_count",
        "stability_score",
    ]
    return df.head(top_n).loc[:, cols].reset_index(drop=True)


def choose_best_stable(df: pd.DataFrame) -> pd.Series:
    eligible = df[
        (df["full_history_trade_count"] >= 50)
        & (df["positive_window_count"] == 4)
    ]
    if eligible.empty:
        eligible = df[
            (df["full_history_trade_count"] >= 50)
            & (df["positive_window_count"] >= 3)
        ]
    if eligible.empty:
        eligible = df[df["full_history_trade_count"] >= 25]
    if eligible.empty:
        eligible = df
    return eligible.sort_values(
        ["stability_score", "full_history_total_return_pct"],
        ascending=[True, False],
    ).iloc[0]


def describe_row(row: pd.Series) -> str:
    return (
        f"{row['variant_id']} | archetype {row['archetype']} | {int(row['timeframe_minutes'])}m | "
        f"pd {int(row['pd_lookback'])} | bbl {int(row['bb_length'])} | lb {int(row['lb_lookback'])} | "
        f"mult {float(row['mult']):.2f} | ph {float(row['ph']):.2f}"
    )


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    bars = load_bars()
    trading_dates = sorted(pd.to_datetime(bars["session_date"]).unique())
    windows = build_windows(trading_dates)

    timeframes = sorted({int(item["timeframe_minutes"]) for item in ARCHETYPES})
    base_frames = {timeframe: build_base_resampled(bars, timeframe) for timeframe in timeframes}

    indicator_cache: dict[tuple[int, int, int, int], pd.DataFrame] = {}
    for timeframe in timeframes:
        for pd_lookback in PD_VALUES:
            for bb_length in BBL_VALUES:
                for lb_lookback in LB_VALUES:
                    indicator_cache[(timeframe, pd_lookback, bb_length, lb_lookback)] = apply_indicator_params(
                        base_frames[timeframe],
                        pd_lookback=pd_lookback,
                        bb_length=bb_length,
                        lb_lookback=lb_lookback,
                    )

    rows: list[dict[str, Any]] = []
    result_cache: dict[str, dict[str, Any]] = {}

    for archetype in ARCHETYPES:
        timeframe = int(archetype["timeframe_minutes"])
        for pd_lookback in PD_VALUES:
            for bb_length in BBL_VALUES:
                for lb_lookback in LB_VALUES:
                    frame = indicator_cache[(timeframe, pd_lookback, bb_length, lb_lookback)]
                    bar_sessions = pd.to_datetime(frame["session_date"])
                    for mult in MULT_VALUES:
                        for ph in PH_VALUES:
                            variant_id = (
                                f"{archetype['archetype']}_pd{pd_lookback}_bbl{bb_length}_"
                                f"lb{lb_lookback}_mult{mult:g}_ph{ph:g}"
                            )
                            config = StrategyConfig(
                                variant_id=variant_id,
                                side=str(archetype["side"]),
                                timeframe_minutes=timeframe,
                                mult=float(mult),
                                ph=float(ph),
                                trigger_mode=str(archetype["trigger_mode"]),
                                confirm_mode=str(archetype["confirm_mode"]),
                                trend_window=int(archetype["trend_window"]),
                                hold_bars=int(archetype["hold_bars"]),
                            )
                            result = simulate(frame, config)
                            result_cache[variant_id] = result
                            row: dict[str, Any] = {
                                "variant_id": variant_id,
                                "archetype": archetype["archetype"],
                                "side": archetype["side"],
                                "timeframe_minutes": timeframe,
                                "pd_lookback": pd_lookback,
                                "bb_length": bb_length,
                                "lb_lookback": lb_lookback,
                                "mult": mult,
                                "ph": ph,
                                "pl": PINE_PL,
                                "trigger_mode": archetype["trigger_mode"],
                                "confirm_mode": archetype["confirm_mode"],
                                "trend_window": archetype["trend_window"],
                                "hold_bars": archetype["hold_bars"],
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

    grid = pd.DataFrame(rows)
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
    grid = grid.sort_values(
        ["side", "stability_score", "full_history_total_return_pct"],
        ascending=[True, True, False],
    ).reset_index(drop=True)
    grid.to_csv(OUTPUT_GRID, index=False)

    long_grid = grid[grid["side"] == "long"].copy()
    short_grid = grid[grid["side"] == "short"].copy()
    top_long = top_table(long_grid)
    top_short = top_table(short_grid)
    top_long.to_csv(OUTPUT_TOP_LONG, index=False)
    top_short.to_csv(OUTPUT_TOP_SHORT, index=False)

    best_long = choose_best_stable(long_grid)
    best_short = choose_best_stable(short_grid)
    best_long_result = result_cache[str(best_long["variant_id"])]
    best_short_result = result_cache[str(best_short["variant_id"])]
    best_long_result["trades"].to_csv(OUTPUT_TRADES_LONG, index=False)
    best_short_result["trades"].to_csv(OUTPUT_TRADES_SHORT, index=False)
    best_long_result["daily_equity"].to_csv(OUTPUT_DAILY_LONG, index=False)
    best_short_result["daily_equity"].to_csv(OUTPUT_DAILY_SHORT, index=False)

    report_lines = [
        "# QQQ WVF Core-Parameter Scan",
        "",
        "## What changed from the first pass",
        "",
        "- The first pass held the Pine core inputs fixed and optimized the trading archetype around them.",
        "- This pass keeps a small set of the strongest long/short archetypes from the first run and explicitly scans the indicator inputs `pd`, `bbl`, `lb`, `mult`, and `ph`.",
        f"- `pl` was held at `{PINE_PL}` because in the pasted Pine it only affects the optional `rangeLow` display line and does not change the spike condition used for entries.",
        f"- Source data: `{SOURCE}`.",
        f"- Total variants tested in this pass: `{len(grid)}`.",
        "",
        "## Best Long Core Setting",
        "",
        f"- `{describe_row(best_long)}`.",
        f"- Full-history return `{safe_value(float(best_long['full_history_total_return_pct']))}%`, max drawdown `{safe_value(float(best_long['full_history_max_drawdown_pct']))}%`, trades `{int(best_long['full_history_trade_count'])}`.",
        f"- Last 1y `{safe_value(float(best_long['last_1y_total_return_pct']))}%`, last 90d `{safe_value(float(best_long['last_90d_total_return_pct']))}%`, YTD 2026 `{safe_value(float(best_long['ytd_2026_total_return_pct']))}%`, stability score `{int(best_long['stability_score'])}`.",
        "",
        "## Best Short Core Setting",
        "",
        f"- `{describe_row(best_short)}`.",
        f"- Full-history return `{safe_value(float(best_short['full_history_total_return_pct']))}%`, max drawdown `{safe_value(float(best_short['full_history_max_drawdown_pct']))}%`, trades `{int(best_short['full_history_trade_count'])}`.",
        f"- Last 1y `{safe_value(float(best_short['last_1y_total_return_pct']))}%`, last 90d `{safe_value(float(best_short['last_90d_total_return_pct']))}%`, YTD 2026 `{safe_value(float(best_short['ytd_2026_total_return_pct']))}%`, stability score `{int(best_short['stability_score'])}`.",
        "",
        "## Output Files",
        "",
        f"- Full scan grid: `{OUTPUT_GRID}`",
        f"- Long leaderboard: `{OUTPUT_TOP_LONG}`",
        f"- Short leaderboard: `{OUTPUT_TOP_SHORT}`",
        f"- Best long trades: `{OUTPUT_TRADES_LONG}`",
        f"- Best short trades: `{OUTPUT_TRADES_SHORT}`",
        f"- Best long daily equity: `{OUTPUT_DAILY_LONG}`",
        f"- Best short daily equity: `{OUTPUT_DAILY_SHORT}`",
        "",
    ]
    OUTPUT_SUMMARY.write_text("\n".join(report_lines), encoding="utf-8")

    preview_cols = [
        "variant_id",
        "archetype",
        "pd_lookback",
        "bb_length",
        "lb_lookback",
        "mult",
        "ph",
        "full_history_total_return_pct",
        "last_1y_total_return_pct",
        "last_90d_total_return_pct",
        "ytd_2026_total_return_pct",
        "full_history_max_drawdown_pct",
        "full_history_trade_count",
        "positive_window_count",
        "stability_score",
    ]
    print("Top long rows:")
    print(top_long.loc[:, preview_cols].head(10).to_string(index=False))
    print()
    print("Top short rows:")
    print(top_short.loc[:, preview_cols].head(10).to_string(index=False))
    print()
    print(f"Report: {OUTPUT_SUMMARY}")


if __name__ == "__main__":
    main()
