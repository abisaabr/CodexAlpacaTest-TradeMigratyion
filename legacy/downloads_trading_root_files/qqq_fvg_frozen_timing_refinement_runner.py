from __future__ import annotations

from time import perf_counter

import pandas as pd

from qqq_fvg_backtest_runner import BASE, load_minute_data, markdown_table
from qqq_fvg_frozen_layered_runner import (
    COST_BPS_PER_SIDE,
    FROZEN_WINNERS,
    REALISTIC_COST_BPS,
    SOURCE,
    mode_to_code,
    prepare_winner,
    run_active_mode_with_filter_detailed,
    run_active_mode_with_filter_metrics,
)


START_OFFSETS_MIN = [0, 15, 30, 45, 60]
CUTOFFS = [None, "13:30", "14:00", "14:15", "14:30", "14:45", "15:00"]
BLOCK_WINDOWS = [
    ("none", None, None),
    ("lunch_1130_1230", "11:30", "12:30"),
    ("lunch_1130_1300", "11:30", "13:00"),
    ("lunch_1200_1330", "12:00", "13:30"),
]

OUTPUTS = {
    "grid": BASE / "qqq_fvg_frozen_timing_refinement_results.csv",
    "summary": BASE / "qqq_fvg_frozen_timing_refinement_summary.md",
    "best_by_winner": BASE / "qqq_fvg_frozen_timing_refinement_best_by_winner.csv",
    "best_realistic_trades": BASE / "qqq_fvg_frozen_timing_refinement_best_realistic_trades.csv",
    "best_realistic_equity": BASE / "qqq_fvg_frozen_timing_refinement_best_realistic_daily_equity.csv",
}


def hhmm_to_minutes(value: str) -> int:
    hour, minute = value.split(":")
    return int(hour) * 60 + int(minute)


def timing_layer_id(start_offset_min: int, cutoff: str | None, block_label: str) -> str:
    cutoff_label = cutoff.replace(":", "") if cutoff else "none"
    return f"start_{start_offset_min:02d}_cutoff_{cutoff_label}_block_{block_label}"


BASE_LAYER_ID = timing_layer_id(0, None, "none")


def compute_timing_permissions(
    bars: pd.DataFrame,
    start_offset_min: int,
    cutoff: str | None,
    block_start: str | None,
    block_end: str | None,
):
    entry_minutes = bars["entry_clock_minute"].to_numpy(dtype="int32")
    start_minute = 9 * 60 + 30 + start_offset_min
    allow = entry_minutes >= start_minute
    if cutoff is not None:
        allow &= entry_minutes <= hhmm_to_minutes(cutoff)
    if block_start is not None and block_end is not None:
        blocked = (entry_minutes >= hhmm_to_minutes(block_start)) & (entry_minutes < hhmm_to_minutes(block_end))
        allow &= ~blocked
    allow &= entry_minutes >= 0
    return allow.copy(), allow.copy()


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

    baseline = results[results["layer_id"] == BASE_LAYER_ID].copy().rename(
        columns={
            "layer_id": "baseline_layer_id",
            "start_offset_min": "baseline_start_offset_min",
            "cutoff": "baseline_cutoff",
            "block_window": "baseline_block_window",
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

    compare = best.merge(
        baseline[
            [
                "winner_id",
                "cost_bps_per_side",
                "baseline_layer_id",
                "baseline_start_offset_min",
                "baseline_cutoff",
                "baseline_block_window",
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
        ],
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
    return compare


def build_summary(results: pd.DataFrame, best_by_winner: pd.DataFrame, runtime_seconds: float) -> str:
    realistic = results[results["cost_bps_per_side"] == REALISTIC_COST_BPS].copy()
    realistic_best = best_by_winner[best_by_winner["cost_bps_per_side"] == REALISTIC_COST_BPS].copy()
    overall_best = realistic.sort_values(
        ["total_return_pct", "sharpe", "profit_factor"],
        ascending=[False, False, False],
    ).iloc[0]
    improved = realistic_best[realistic_best["delta_total_return_pct"] > 1e-9].copy()

    compare_view = realistic_best[
        [
            "winner_id",
            "timeframe_label",
            "entry_mode",
            "layer_id",
            "start_offset_min",
            "cutoff",
            "block_window",
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

    top_view = realistic.sort_values(
        ["total_return_pct", "sharpe", "profit_factor"],
        ascending=[False, False, False],
    ).head(16)[
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

    block_view = (
        realistic.groupby(["winner_id", "block_window"])
        .agg(
            best_return=("total_return_pct", "max"),
            median_return=("total_return_pct", "median"),
            best_sharpe=("sharpe", "max"),
            median_trades=("trade_count", "median"),
        )
        .reset_index()
        .sort_values(["winner_id", "best_return"], ascending=[True, False])
    )
    for column in ["best_return", "median_return"]:
        block_view[column] = block_view[column].map(lambda x: f"{x:.2f}%")
    block_view["best_sharpe"] = block_view["best_sharpe"].map(lambda x: f"{x:.2f}")
    block_view["median_trades"] = block_view["median_trades"].map(lambda x: f"{x:.0f}")

    if improved.empty:
        improvement_lines = [
            "- No refined timing window beat the frozen baseline on total return under `2.0` bps per side.",
        ]
    else:
        improvement_lines = []
        for _, row in improved.sort_values(["delta_total_return_pct", "delta_sharpe"], ascending=[False, False]).iterrows():
            improvement_lines.append(
                "- "
                f"`{row['winner_id']}` improved by `{row['delta_total_return_pct']:.2f}%` with layer "
                f"`{row['layer_id']}`. Sharpe delta `{row['delta_sharpe']:.2f}`, drawdown delta `{row['delta_max_drawdown_pct']:.2f}%`."
            )

    lines = [
        "# QQQ Frozen Winner Timing Refinement",
        "",
        "## Scope",
        "",
        "- Frozen winners only. No changes to variant, timeframe, entry mode, stop, or target.",
        "- Timing refinements tested:",
        "  - Session start delays: `0`, `15`, `30`, `45`, `60` minutes.",
        "  - Entry cutoffs: none, `13:30`, `14:00`, `14:15`, `14:30`, `14:45`, `15:00`.",
        "  - Block windows: none, `11:30-12:30`, `11:30-13:00`, `12:00-13:30`.",
        "- Timing rules use actual next-bar entry times.",
        f"- Costs tested: `{', '.join(f'{x:.1f}' for x in COST_BPS_PER_SIDE)}` bps per side.",
        "",
        "## Best Realistic Result (`2.0` Bps Per Side)",
        "",
        f"- Winner: `{overall_best['winner_id']}`.",
        f"- Layer: `{overall_best['layer_id']}`.",
        f"- Total return: `{overall_best['total_return_pct']:.2f}%`.",
        f"- CAGR: `{overall_best['cagr_pct']:.2f}%`.",
        f"- Max drawdown: `{overall_best['max_drawdown_pct']:.2f}%`.",
        f"- Sharpe: `{overall_best['sharpe']:.2f}`.",
        f"- Trades: `{int(overall_best['trade_count'])}`.",
        "",
        "## Incremental Improvement",
        "",
        *improvement_lines,
        "",
        "## Winner-Level Comparison At `2.0` Bps",
        "",
        markdown_table(compare_view),
        "",
        "## Top 16 Timing Layers Under `2.0` Bps",
        "",
        markdown_table(top_view),
        "",
        "## Block Window Snapshot Under `2.0` Bps",
        "",
        markdown_table(block_view),
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
    return "\n".join(lines)


def main() -> None:
    start = perf_counter()
    minute_frame = load_minute_data(SOURCE)
    prepared_winners = [prepare_winner(minute_frame, winner) for winner in FROZEN_WINNERS]

    rows = []
    for prepared in prepared_winners:
        winner = prepared.winner
        bars = prepared.bars
        open_ = bars["open"].to_numpy(dtype="float64")
        high = bars["high"].to_numpy(dtype="float64")
        low = bars["low"].to_numpy(dtype="float64")
        close = bars["close"].to_numpy(dtype="float64")
        mode_code = mode_to_code(winner.entry_mode)

        for start_offset_min in START_OFFSETS_MIN:
            for cutoff in CUTOFFS:
                for block_label, block_start, block_end in BLOCK_WINDOWS:
                    layer = timing_layer_id(start_offset_min, cutoff, block_label)
                    allow_long, allow_short = compute_timing_permissions(
                        bars,
                        start_offset_min,
                        cutoff,
                        block_start,
                        block_end,
                    )
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
                                "layer_id": layer,
                                "is_baseline_layer": layer == BASE_LAYER_ID,
                                "start_offset_min": start_offset_min,
                                "cutoff": cutoff or "none",
                                "block_window": block_label,
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
    block_def = next(item for item in BLOCK_WINDOWS if item[0] == best_realistic["block_window"])
    best_allow_long, best_allow_short = compute_timing_permissions(
        best_prepared.bars,
        int(best_realistic["start_offset_min"]),
        None if best_realistic["cutoff"] == "none" else str(best_realistic["cutoff"]),
        block_def[1],
        block_def[2],
    )
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
        frame["block_window"] = best_realistic["block_window"]
        frame["stop_loss_pct"] = float(best_realistic["stop_loss_pct"])
        frame["take_profit_pct"] = float(best_realistic["take_profit_pct"])
        frame["cost_bps_per_side"] = float(best_realistic["cost_bps_per_side"])
    trades_df.to_csv(OUTPUTS["best_realistic_trades"], index=False)
    equity_df.to_csv(OUTPUTS["best_realistic_equity"], index=False)

    runtime_seconds = perf_counter() - start
    OUTPUTS["summary"].write_text(build_summary(results, best_by_winner, runtime_seconds), encoding="utf-8")


if __name__ == "__main__":
    main()
