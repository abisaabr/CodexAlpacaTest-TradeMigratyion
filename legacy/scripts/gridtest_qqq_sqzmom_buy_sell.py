from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from backtest_qqq_sqzmom import (
    DATA_DIR,
    REPORTS_DIR,
    StrategyConfig,
    build_windows,
    load_bars,
    prepare_indicator_frame,
    safe_value,
    simulate,
)

OUTPUT_GRID = DATA_DIR / "qqq_sqzmom_buy_sell_grid.csv"
OUTPUT_TOP_FULL = DATA_DIR / "qqq_sqzmom_buy_sell_top_full_history.csv"
OUTPUT_TOP_RECENT = DATA_DIR / "qqq_sqzmom_buy_sell_top_last_1y.csv"
OUTPUT_TOP_STABLE = DATA_DIR / "qqq_sqzmom_buy_sell_top_stability.csv"
OUTPUT_BEST_TRADES = DATA_DIR / "qqq_sqzmom_buy_sell_best_stable_trades.csv"
OUTPUT_BEST_DAILY = DATA_DIR / "qqq_sqzmom_buy_sell_best_stable_daily_equity.csv"
OUTPUT_REPORT = REPORTS_DIR / "qqq_sqzmom_buy_sell_grid_report.md"

ENTRY_THRESHOLDS = (-4.0, -2.5, -1.5, -1.0, -0.75, -0.5, -0.35, -0.25, -0.15, -0.10, -0.05, -0.02)
EXIT_THRESHOLDS = (0.0, 0.02, 0.05, 0.10, 0.15, 0.25, 0.35, 0.50, 0.75, 1.0, 1.5)
SESSION_MODES = (
    ("rth_swing", False),
    ("rth_intraday", True),
)


def top_table(df: pd.DataFrame, sort_column: str, ascending: bool = False, top_n: int = 15) -> pd.DataFrame:
    cols = [
        "variant_id",
        "mode_name",
        "entry_threshold",
        "exit_threshold",
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
    return df.sort_values(sort_column, ascending=ascending).head(top_n).loc[:, cols].reset_index(drop=True)


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    bars = load_bars()
    indicator_frame = prepare_indicator_frame(bars, session="rth")
    rth_dates = sorted(pd.to_datetime(bars.loc[bars["in_rth"], "session_date"]).unique())
    windows = build_windows(rth_dates)
    window_frames = {
        window_name: indicator_frame[
            (pd.to_datetime(indicator_frame["session_date"]) >= start_date)
            & (pd.to_datetime(indicator_frame["session_date"]) <= end_date)
        ].reset_index(drop=True)
        for window_name, (start_date, end_date) in windows.items()
    }

    rows: list[dict[str, Any]] = []
    result_cache: dict[str, dict[str, Any]] = {}

    for mode_name, force_flat_eod in SESSION_MODES:
        for entry_threshold in ENTRY_THRESHOLDS:
            for exit_threshold in EXIT_THRESHOLDS:
                variant_id = f"{mode_name}_buy_{entry_threshold:g}_sell_{exit_threshold:g}"
                row: dict[str, Any] = {
                    "variant_id": variant_id,
                    "mode_name": mode_name,
                    "force_flat_eod": force_flat_eod,
                    "entry_threshold": entry_threshold,
                    "exit_threshold": exit_threshold,
                    "cost_bps_per_side": 1.0,
                }
                for window_name, frame in window_frames.items():
                    result = simulate(
                        frame,
                        StrategyConfig(
                            variant_id=variant_id,
                            entry_threshold=entry_threshold,
                            exit_threshold=exit_threshold,
                            force_flat_eod=force_flat_eod,
                        ),
                    )
                    metrics = result["metrics"]
                    for key, value in metrics.items():
                        if key in {
                            "variant_id",
                            "entry_threshold",
                            "exit_threshold",
                            "force_flat_eod",
                            "cost_bps_per_side",
                        }:
                            continue
                        row[f"{window_name}_{key}"] = value
                    row[f"{window_name}_start"] = windows[window_name][0].date().isoformat()
                    row[f"{window_name}_end"] = windows[window_name][1].date().isoformat()
                    if window_name == "full_history":
                        result_cache[variant_id] = result

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
            grid.groupby("mode_name")[column]
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
        grid.groupby("mode_name")["stability_score"]
        .rank(method="min", ascending=True)
        .astype(int)
    )

    grid = grid.sort_values(
        ["mode_name", "stability_score", "full_history_total_return_pct"],
        ascending=[True, True, False],
    ).reset_index(drop=True)
    grid.to_csv(OUTPUT_GRID, index=False)

    top_full = top_table(grid, "full_history_total_return_pct", ascending=False)
    top_recent = top_table(grid, "last_1y_total_return_pct", ascending=False)
    top_stable = top_table(grid, "stability_score", ascending=True)
    top_full.to_csv(OUTPUT_TOP_FULL, index=False)
    top_recent.to_csv(OUTPUT_TOP_RECENT, index=False)
    top_stable.to_csv(OUTPUT_TOP_STABLE, index=False)

    best_stable = top_stable.iloc[0].to_dict()
    best_result = result_cache[str(best_stable["variant_id"])]
    best_result["trades"].to_csv(OUTPUT_BEST_TRADES, index=False)
    best_result["daily_equity"].to_csv(OUTPUT_BEST_DAILY, index=False)

    positive_full = int((grid["full_history_total_return_pct"] > 0.0).sum())
    positive_recent = int((grid["last_1y_total_return_pct"] > 0.0).sum())
    positive_90d = int((grid["last_90d_total_return_pct"] > 0.0).sum())
    positive_all_windows = int((grid["positive_window_count"] == 4).sum())

    mode_summaries: list[str] = []
    for mode_name in grid["mode_name"].unique():
        mode_grid = grid[grid["mode_name"] == mode_name]
        best_mode_full = mode_grid.sort_values("full_history_total_return_pct", ascending=False).iloc[0]
        best_mode_stable = mode_grid.sort_values(["stability_score", "full_history_total_return_pct"], ascending=[True, False]).iloc[0]
        mode_summaries.extend(
            [
                f"### {mode_name}",
                "",
                f"- Best full-history pair: buy `>{best_mode_full['entry_threshold']}` on dark red, sell `>{best_mode_full['exit_threshold']}` on dark green. Return `{safe_value(float(best_mode_full['full_history_total_return_pct']))}%`, max DD `{safe_value(float(best_mode_full['full_history_max_drawdown_pct']))}%`, last 1y `{safe_value(float(best_mode_full['last_1y_total_return_pct']))}%`.",
                f"- Most stable pair: buy `>{best_mode_stable['entry_threshold']}` on dark red, sell `>{best_mode_stable['exit_threshold']}` on dark green. Stability score `{int(best_mode_stable['stability_score'])}`, full-history return `{safe_value(float(best_mode_stable['full_history_total_return_pct']))}%`, last 90d `{safe_value(float(best_mode_stable['last_90d_total_return_pct']))}%`.",
                "",
            ]
        )

    report_lines = [
        "# QQQ SQZMOM Buy/Sell Grid",
        "",
        "## Grid tested",
        "",
        f"- Entry thresholds on `red -> maroon`: `{', '.join(str(x) for x in ENTRY_THRESHOLDS)}`.",
        f"- Exit thresholds on `lime -> green`: `{', '.join(str(x) for x in EXIT_THRESHOLDS)}`.",
        "- Two execution modes were tested: `rth_swing` and `rth_intraday`.",
        "- Execution assumption: next-bar-open fills, plus forced end-of-day flattening for the intraday mode.",
        "- Cost assumption: `1.0 bp` per side.",
        "",
        "## Headline results",
        "",
        f"- Total parameter pairs tested: `{len(grid)}`.",
        f"- Positive full-history pairs: `{positive_full}`.",
        f"- Positive last-1-year pairs: `{positive_recent}`.",
        f"- Positive last-90-day pairs: `{positive_90d}`.",
        f"- Positive in all four windows: `{positive_all_windows}`.",
        "",
        "## Best overall rows",
        "",
        "| Bucket | Variant | Full return | Max DD | Last 1y | Last 90d | YTD 2026 | Stability score |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
        f"| Best full history | {top_full.iloc[0]['variant_id']} | {safe_value(float(top_full.iloc[0]['full_history_total_return_pct']))}% | {safe_value(float(top_full.iloc[0]['full_history_max_drawdown_pct']))}% | {safe_value(float(top_full.iloc[0]['last_1y_total_return_pct']))}% | {safe_value(float(top_full.iloc[0]['last_90d_total_return_pct']))}% | {safe_value(float(top_full.iloc[0]['ytd_2026_total_return_pct']))}% | {int(top_full.iloc[0]['stability_score'])} |",
        f"| Best last 1y | {top_recent.iloc[0]['variant_id']} | {safe_value(float(top_recent.iloc[0]['full_history_total_return_pct']))}% | {safe_value(float(top_recent.iloc[0]['full_history_max_drawdown_pct']))}% | {safe_value(float(top_recent.iloc[0]['last_1y_total_return_pct']))}% | {safe_value(float(top_recent.iloc[0]['last_90d_total_return_pct']))}% | {safe_value(float(top_recent.iloc[0]['ytd_2026_total_return_pct']))}% | {int(top_recent.iloc[0]['stability_score'])} |",
        f"| Best stability | {top_stable.iloc[0]['variant_id']} | {safe_value(float(top_stable.iloc[0]['full_history_total_return_pct']))}% | {safe_value(float(top_stable.iloc[0]['full_history_max_drawdown_pct']))}% | {safe_value(float(top_stable.iloc[0]['last_1y_total_return_pct']))}% | {safe_value(float(top_stable.iloc[0]['last_90d_total_return_pct']))}% | {safe_value(float(top_stable.iloc[0]['ytd_2026_total_return_pct']))}% | {int(top_stable.iloc[0]['stability_score'])} |",
        "",
        "## Mode summaries",
        "",
    ]
    report_lines.extend(mode_summaries)
    report_lines.extend(
        [
            "## Output files",
            "",
            f"- Full grid: `{OUTPUT_GRID}`",
            f"- Top full-history rows: `{OUTPUT_TOP_FULL}`",
            f"- Top last-1-year rows: `{OUTPUT_TOP_RECENT}`",
            f"- Top stability rows: `{OUTPUT_TOP_STABLE}`",
            f"- Trades for the best-stability pair: `{OUTPUT_BEST_TRADES}`",
            f"- Daily equity for the best-stability pair: `{OUTPUT_BEST_DAILY}`",
            "",
        ]
    )
    OUTPUT_REPORT.write_text("\n".join(report_lines), encoding="utf-8")

    preview_cols = [
        "variant_id",
        "full_history_total_return_pct",
        "full_history_max_drawdown_pct",
        "last_1y_total_return_pct",
        "last_90d_total_return_pct",
        "ytd_2026_total_return_pct",
        "stability_score",
    ]
    print(top_stable.loc[:, preview_cols].to_string(index=False))
    print()
    print(f"Report: {OUTPUT_REPORT}")


if __name__ == "__main__":
    main()
