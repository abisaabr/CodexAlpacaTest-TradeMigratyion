from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from time import perf_counter

import numpy as np
import pandas as pd

from qqq_fvg_backtest_runner import BASE, load_minute_data, markdown_table
from qqq_fvg_extended_runner import run_backtest_detailed_with_cost, run_backtest_metrics_with_cost
from qqq_fvg_active_variants_runner import prepare_timeframe_variants


SOURCE = BASE / "QQQ_1min_20210308-20260308_sip (1).csv"
COST_BPS_PER_SIDE = [0.0, 2.0]
REALISTIC_COST_BPS = 2.0

OUTPUTS = {
    "grid": BASE / "qqq_fvg_active_fine_grid_results.csv",
    "summary": BASE / "qqq_fvg_active_fine_summary.md",
    "best_by_candidate": BASE / "qqq_fvg_active_fine_best_by_candidate.csv",
    "best_realistic_trades": BASE / "qqq_fvg_active_fine_best_realistic_trades.csv",
    "best_realistic_equity": BASE / "qqq_fvg_active_fine_best_realistic_daily_equity.csv",
}


@dataclass(frozen=True)
class CandidateSpec:
    candidate_id: str
    timeframe_min: int
    variant: str
    stop_values: tuple[float, ...]
    target_values: tuple[float, ...]


CANDIDATES = [
    CandidateSpec(
        candidate_id="dominant_count_10m",
        timeframe_min=10,
        variant="active_dominant_count_session_reset",
        stop_values=tuple(np.round(np.arange(0.75, 2.51, 0.25), 2)),
        target_values=tuple(np.round(np.arange(1.50, 4.51, 0.25), 2)),
    ),
    CandidateSpec(
        candidate_id="uncontested_15m",
        timeframe_min=15,
        variant="active_uncontested_session_reset",
        stop_values=tuple(np.round(np.arange(0.25, 1.76, 0.25), 2)),
        target_values=tuple(np.round(np.arange(1.50, 4.51, 0.25), 2)),
    ),
]

ENTRY_MODES = ["always_on_active", "change_only"]


def build_change_only_signal(signal: np.ndarray) -> np.ndarray:
    out = np.zeros_like(signal)
    if len(signal) == 0:
        return out

    out[0] = signal[0] if signal[0] != 0 else 0
    prev = signal[0]
    for i in range(1, len(signal)):
        current = signal[i]
        if current != 0 and current != prev:
            out[i] = current
        prev = current
    return out


def build_summary(results: pd.DataFrame, runtime_seconds: float) -> str:
    realistic = results[results["cost_bps_per_side"] == REALISTIC_COST_BPS].copy()
    best_realistic = realistic.sort_values(
        ["total_return_pct", "sharpe", "profit_factor"],
        ascending=[False, False, False],
    ).iloc[0]

    best_by_candidate = (
        results.sort_values(
            ["candidate_id", "entry_mode", "cost_bps_per_side", "total_return_pct", "sharpe"],
            ascending=[True, True, True, False, False],
        )
        .groupby(["candidate_id", "entry_mode", "cost_bps_per_side"], as_index=False)
        .head(1)
        .reset_index(drop=True)
    )

    realistic_top = realistic.sort_values(
        ["total_return_pct", "sharpe", "profit_factor"],
        ascending=[False, False, False],
    ).head(20)

    entry_mode_compare = (
        realistic.groupby(["candidate_id", "entry_mode"])
        .agg(
            positive=("total_return_pct", lambda s: int((s > 0).sum())),
            combos=("candidate_id", "size"),
            median_return=("total_return_pct", "median"),
            best_return=("total_return_pct", "max"),
            median_dd=("max_drawdown_pct", "median"),
            best_sharpe=("sharpe", "max"),
            median_trades=("trade_count", "median"),
        )
        .reset_index()
        .sort_values(["candidate_id", "best_return"], ascending=[True, False])
    )

    by_candidate_view = best_by_candidate[
        [
            "candidate_id",
            "entry_mode",
            "cost_bps_per_side",
            "timeframe_label",
            "stop_loss_pct",
            "take_profit_pct",
            "total_return_pct",
            "max_drawdown_pct",
            "sharpe",
            "trade_count",
        ]
    ].copy()
    by_candidate_view["cost_bps_per_side"] = by_candidate_view["cost_bps_per_side"].map(lambda x: f"{x:.1f}")
    for column in ["stop_loss_pct", "take_profit_pct", "total_return_pct", "max_drawdown_pct"]:
        by_candidate_view[column] = by_candidate_view[column].map(lambda x: f"{x:.2f}%")
    by_candidate_view["sharpe"] = by_candidate_view["sharpe"].map(lambda x: f"{x:.2f}")
    by_candidate_view["trade_count"] = by_candidate_view["trade_count"].map(lambda x: f"{int(x)}")

    top_view = realistic_top[
        [
            "candidate_id",
            "entry_mode",
            "timeframe_label",
            "stop_loss_pct",
            "take_profit_pct",
            "total_return_pct",
            "max_drawdown_pct",
            "sharpe",
            "profit_factor",
            "trade_count",
            "win_rate_pct",
            "exposure_pct",
        ]
    ].copy()
    for column in [
        "stop_loss_pct",
        "take_profit_pct",
        "total_return_pct",
        "max_drawdown_pct",
        "win_rate_pct",
        "exposure_pct",
    ]:
        top_view[column] = top_view[column].map(lambda x: f"{x:.2f}%")
    top_view["sharpe"] = top_view["sharpe"].map(lambda x: f"{x:.2f}")
    top_view["profit_factor"] = top_view["profit_factor"].map(lambda x: f"{x:.2f}")
    top_view["trade_count"] = top_view["trade_count"].map(lambda x: f"{int(x)}")

    entry_mode_view = entry_mode_compare.copy()
    entry_mode_view["positive"] = entry_mode_view.apply(
        lambda row: f"{int(row['positive'])}/{int(row['combos'])}",
        axis=1,
    )
    entry_mode_view = entry_mode_view.drop(columns=["combos"])
    for column in ["median_return", "best_return", "median_dd"]:
        entry_mode_view[column] = entry_mode_view[column].map(lambda x: f"{x:.2f}%")
    entry_mode_view["best_sharpe"] = entry_mode_view["best_sharpe"].map(lambda x: f"{x:.2f}")
    entry_mode_view["median_trades"] = entry_mode_view["median_trades"].map(lambda x: f"{x:.0f}")

    lines = [
        "# QQQ Active FVG Fine Optimization",
        "",
        "## Scope",
        "",
        "- Candidate 1: `active_dominant_count_session_reset` on `10m`.",
        "- Candidate 2: `active_uncontested_session_reset` on `15m`.",
        "- Entry modes:",
        "  - `always_on_active`: current active-bias behavior.",
        "  - `change_only`: only emit an entry when active bias changes to a new non-zero state.",
        "- Costs tested: `0.0` and `2.0` bps per side.",
        "",
        "## Best Realistic Result (`2.0` Bps Per Side)",
        "",
        f"- Candidate: `{best_realistic['candidate_id']}`.",
        f"- Variant: `{best_realistic['variant']}`.",
        f"- Entry mode: `{best_realistic['entry_mode']}`.",
        f"- Timeframe: `{best_realistic['timeframe_label']}`.",
        f"- Stop loss: `{best_realistic['stop_loss_pct']:.2f}%`.",
        f"- Take profit: `{best_realistic['take_profit_pct']:.2f}%`.",
        f"- Total return: `{best_realistic['total_return_pct']:.2f}%`.",
        f"- CAGR: `{best_realistic['cagr_pct']:.2f}%`.",
        f"- Max drawdown: `{best_realistic['max_drawdown_pct']:.2f}%`.",
        f"- Sharpe: `{best_realistic['sharpe']:.2f}`.",
        f"- Profit factor: `{best_realistic['profit_factor']:.2f}`.",
        f"- Trades: `{int(best_realistic['trade_count'])}` with win rate `{best_realistic['win_rate_pct']:.2f}%`.",
        "",
        "## Best By Candidate, Entry Mode, And Cost",
        "",
        markdown_table(by_candidate_view),
        "",
        "## Top 20 Under `2.0` Bps Per Side",
        "",
        markdown_table(top_view),
        "",
        "## Entry Mode Comparison At `2.0` Bps",
        "",
        markdown_table(entry_mode_view),
        "",
        "## Output Files",
        "",
        f"- Full grid: `{OUTPUTS['grid']}`.",
        f"- Best-by-candidate table: `{OUTPUTS['best_by_candidate']}`.",
        f"- Best realistic trades: `{OUTPUTS['best_realistic_trades']}`.",
        f"- Best realistic daily equity: `{OUTPUTS['best_realistic_equity']}`.",
        f"- Runtime: `{runtime_seconds:.2f}` seconds.",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    start = perf_counter()
    minute_frame = load_minute_data(SOURCE)
    prepared = {candidate.timeframe_min: prepare_timeframe_variants(minute_frame, candidate.timeframe_min) for candidate in CANDIDATES}

    rows: list[dict[str, float | int | str]] = []
    for candidate in CANDIDATES:
        tf_data = prepared[candidate.timeframe_min]
        bars = tf_data.bars
        open_ = bars["open"].to_numpy(dtype=np.float64)
        high = bars["high"].to_numpy(dtype=np.float64)
        low = bars["low"].to_numpy(dtype=np.float64)
        close = bars["close"].to_numpy(dtype=np.float64)

        base_signal = tf_data.signals[candidate.variant]
        signals = {
            "always_on_active": base_signal,
            "change_only": build_change_only_signal(base_signal),
        }

        for entry_mode, signal in signals.items():
            bullish_signal_count = int((signal == 1).sum())
            bearish_signal_count = int((signal == -1).sum())
            for cost_bps_per_side in COST_BPS_PER_SIDE:
                for stop_loss_pct in candidate.stop_values:
                    for take_profit_pct in candidate.target_values:
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
                        ) = run_backtest_metrics_with_cost(
                            open_,
                            high,
                            low,
                            close,
                            signal,
                            tf_data.session_ids,
                            stop_loss_pct / 100.0,
                            take_profit_pct / 100.0,
                            cost_bps_per_side,
                        )

                        rows.append(
                            {
                                "candidate_id": candidate.candidate_id,
                                "variant": candidate.variant,
                                "entry_mode": entry_mode,
                                "timeframe_min": candidate.timeframe_min,
                                "timeframe_label": f"{candidate.timeframe_min}m",
                                "cost_bps_per_side": cost_bps_per_side,
                                "stop_loss_pct": stop_loss_pct,
                                "take_profit_pct": take_profit_pct,
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
                                "avg_holding_minutes": avg_holding_bars * candidate.timeframe_min,
                                "exposure_pct": exposure_pct,
                                "bullish_signal_count": bullish_signal_count,
                                "bearish_signal_count": bearish_signal_count,
                            }
                        )

    results = pd.DataFrame(rows).sort_values(
        ["cost_bps_per_side", "total_return_pct", "sharpe", "profit_factor"],
        ascending=[True, False, False, False],
    ).reset_index(drop=True)
    results.to_csv(OUTPUTS["grid"], index=False)

    best_by_candidate = (
        results.sort_values(
            ["candidate_id", "entry_mode", "cost_bps_per_side", "total_return_pct", "sharpe"],
            ascending=[True, True, True, False, False],
        )
        .groupby(["candidate_id", "entry_mode", "cost_bps_per_side"], as_index=False)
        .head(1)
        .reset_index(drop=True)
    )
    best_by_candidate.to_csv(OUTPUTS["best_by_candidate"], index=False)

    realistic = results[results["cost_bps_per_side"] == REALISTIC_COST_BPS].copy()
    best_realistic = realistic.sort_values(
        ["total_return_pct", "sharpe", "profit_factor"],
        ascending=[False, False, False],
    ).iloc[0]

    best_candidate = next(candidate for candidate in CANDIDATES if candidate.candidate_id == best_realistic["candidate_id"])
    best_tf = prepared[best_candidate.timeframe_min]
    best_base_signal = best_tf.signals[best_candidate.variant]
    best_signal = (
        best_base_signal
        if best_realistic["entry_mode"] == "always_on_active"
        else build_change_only_signal(best_base_signal)
    )
    trades_df, equity_df = run_backtest_detailed_with_cost(
        best_tf.bars,
        best_signal,
        float(best_realistic["stop_loss_pct"]) / 100.0,
        float(best_realistic["take_profit_pct"]) / 100.0,
        float(best_realistic["cost_bps_per_side"]),
        f"{best_realistic['variant']}|{best_realistic['entry_mode']}",
    )
    trades_df.to_csv(OUTPUTS["best_realistic_trades"], index=False)
    equity_df.to_csv(OUTPUTS["best_realistic_equity"], index=False)

    runtime_seconds = perf_counter() - start
    summary = build_summary(results, runtime_seconds)
    OUTPUTS["summary"].write_text(summary + "\n", encoding="utf-8")
    print(summary)


if __name__ == "__main__":
    main()
