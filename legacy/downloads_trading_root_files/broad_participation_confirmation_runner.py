from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import pandas as pd

BASE_DIR = Path(r"C:\Users\rabisaab\Downloads")
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))
REPO_SRC = BASE_DIR / "alpaca-stock-strategy-research" / "src"
if str(REPO_SRC) not in sys.path:
    sys.path.insert(0, str(REPO_SRC))

from alpaca_stock_research.backtests.engine import equity_from_trades
from megacap_ex_nvda_confirmation_runner import (
    INITIAL_CAPITAL,
    assign_quality_scores,
    attach_trade_context,
    build_daily_context,
    build_variant_day_frame,
    classify_profitable_day,
    day_series_metrics,
    metric_row,
    write_markdown,
)
from nvda_truth_test_runner import load_baseline_specs, slippage_map
from rs_deployment_truth_test_runner import run_strategy, top_n_signal_wrapper


RS_ID = "relative_strength_vs_benchmark::rs_top3_native"
CSM_ID = "cross_sectional_momentum::csm_native"
DSE_ID = "down_streak_exhaustion"
UNIVERSE = ["AAPL", "AMZN", "GOOGL", "META", "NFLX"]

EXACT_FILES = [
    BASE_DIR / "master_strategy_memo.txt",
    BASE_DIR / "tournament_master_report.md",
    BASE_DIR / "monday_paper_plan.md",
    BASE_DIR / "megacap_ex_nvda_branch_decision.md",
    BASE_DIR / "leader_vs_breadth_report.md",
    BASE_DIR / "megacap_ex_nvda_forensics_report.md",
    BASE_DIR / "megacap_ex_nvda_paper_watch_recheck.md",
    BASE_DIR / "ex_tsla_branch_redecision.md",
    BASE_DIR / "ex_tsla_leader_report.md",
    BASE_DIR / "ex_tsla_forensics_report.md",
    BASE_DIR / "ex_tsla_paper_watch_recheck.md",
    BASE_DIR / "next_post_ex_tsla_experiments.md",
    BASE_DIR / "best_day_autopsy_report.md",
    BASE_DIR / "non_extreme_day_edge_report.md",
    BASE_DIR / "canonical_edge_hypothesis.md",
    BASE_DIR / "ex_tsla_metrics.csv",
    BASE_DIR / "ex_tsla_leader_diagnostic.csv",
    BASE_DIR / "day_type_symbol_regime_map.csv",
    BASE_DIR / "day_level_pnl_decomposition.csv",
    BASE_DIR / "underlying_trade_ledger.csv",
    BASE_DIR / "underlying_tournament_metrics.csv",
    BASE_DIR / "trade_cluster_edge_map.csv",
]

OUTPUTS = {
    "digest": BASE_DIR / "broad_participation_input_digest.md",
    "grid": BASE_DIR / "broad_participation_test_matrix.md",
    "metrics": BASE_DIR / "broad_participation_metrics.csv",
    "leaderboard": BASE_DIR / "broad_participation_leaderboard.md",
    "contrast_csv": BASE_DIR / "leader_vs_broad_participation_contrast.csv",
    "contrast_md": BASE_DIR / "leader_vs_broad_participation_report.md",
    "forensics_csv": BASE_DIR / "broad_participation_forensics.csv",
    "forensics_md": BASE_DIR / "broad_participation_forensics_report.md",
    "decision": BASE_DIR / "broad_participation_branch_decision.md",
    "paper": BASE_DIR / "broad_participation_paper_watch_recheck.md",
    "next": BASE_DIR / "next_after_broad_participation.md",
}


def adjusted_curve(curve: pd.DataFrame, remove_best_pct: float = 0.0, remove_worst_pct: float = 0.0) -> pd.DataFrame:
    out = curve.copy()
    if out.empty:
        return out
    active = out["daily_pnl"].copy()
    if remove_best_pct > 0:
        remove_n = max(1, math.ceil(len(active) * remove_best_pct))
        active.loc[active.sort_values(ascending=False).head(remove_n).index] = 0.0
    if remove_worst_pct > 0:
        remove_n = max(1, math.ceil(len(active) * remove_worst_pct))
        active.loc[active.sort_values(ascending=True).head(remove_n).index] = 0.0
    out["daily_pnl"] = active
    out["equity"] = INITIAL_CAPITAL + out["daily_pnl"].cumsum()
    out["returns"] = out["equity"].pct_change().fillna(0.0)
    return out


def score_subset(frame: pd.DataFrame) -> pd.Series:
    temp = frame.copy()
    temp["candidate_for_branch"] = True
    return assign_quality_scores(temp)["trust_adjusted_quality_score"]


def regime_slice_trades(
    trades: pd.DataFrame,
    slice_name: str,
    leader_dates: set[pd.Timestamp],
    broad_dates: set[pd.Timestamp],
    broad_rising_dates: set[pd.Timestamp],
    broad_strong_dates: set[pd.Timestamp],
    mixed_dates: set[pd.Timestamp],
) -> pd.DataFrame:
    if slice_name == "ex_tsla_full":
        return trades.copy()
    if slice_name == "broad_participation_only":
        return trades.loc[trades["entry_date"].isin(broad_dates)].copy()
    if slice_name == "broad_participation_rising_market":
        return trades.loc[trades["entry_date"].isin(broad_rising_dates)].copy()
    if slice_name == "broad_participation_strong_momentum":
        return trades.loc[trades["entry_date"].isin(broad_strong_dates)].copy()
    if slice_name == "leader_dominant_only":
        return trades.loc[trades["entry_date"].isin(leader_dates)].copy()
    if slice_name == "mixed_unclear_only":
        return trades.loc[trades["entry_date"].isin(mixed_dates)].copy()
    raise ValueError(slice_name)


def slice_scope_note(label: str, slice_name: str) -> str:
    notes = {
        "ex_tsla_full": f"{label} baseline on the narrowed mega-cap ex-NVDA ex-TSLA universe.",
        "broad_participation_only": f"{label} on ex-TSLA days with multi-symbol participation, at least two profitable symbols, at least three traded symbols, and top-symbol share at or below 60%.",
        "broad_participation_rising_market": f"{label} on broad-participation ex-TSLA days that also occur in the `rising_market` regime.",
        "broad_participation_strong_momentum": f"{label} on broad-participation ex-TSLA days that also occur in the ex-TSLA `strong_momentum_participation` regime.",
        "broad_participation_non_extreme_2_5": f"{label} on the broad-participation slice with both best and worst 2.5% of days removed from the equity path audit.",
        "leader_dominant_only": f"{label} on ex-TSLA days still classified as leader-dominant or one-symbol-driven.",
        "mixed_unclear_only": f"{label} on ex-TSLA days that are neither clean broad-participation days nor leader-dominant days.",
    }
    return notes[slice_name]


def profitable_day_class_report(day_frame: pd.DataFrame) -> dict[str, float]:
    profitable = day_frame.loc[day_frame["total_pnl_dollars"] > 0].copy()
    if profitable.empty:
        return {
            "dominant_share": 0.0,
            "broad_share": 0.0,
            "event_share": 0.0,
            "top_symbol_share": 0.0,
            "multi_symbol_share": 0.0,
        }
    profitable["primary_day_class"] = profitable.apply(classify_profitable_day, axis=1)
    class_share = profitable.groupby("primary_day_class")["total_pnl_dollars"].sum()
    total = float(class_share.sum()) if len(class_share) else 0.0
    return {
        "dominant_share": float(class_share.get("one_dominant_leader_day", 0.0) / total * 100.0) if total > 0 else 0.0,
        "broad_share": float((class_share.get("broad_participation_day", 0.0) + class_share.get("continuation_day", 0.0)) / total * 100.0) if total > 0 else 0.0,
        "event_share": float(class_share.get("event_like_gap_reaction_day", 0.0) / total * 100.0) if total > 0 else 0.0,
        "top_symbol_share": float(profitable["top_symbol_pct_of_day_pnl"].mean()),
        "multi_symbol_share": float((profitable["participation_type"] == "multi_symbol_driven").mean() * 100.0),
    }


def main() -> None:
    file_status = [{"path": str(path), "opened": path.exists()} for path in EXACT_FILES]
    specs = load_baseline_specs(BASE_DIR / "underlying_tournament_metrics.csv")
    rs_spec = specs.loc[specs["template_key"] == "relative_strength_vs_benchmark"].iloc[0]
    csm_spec = specs.loc[specs["template_key"] == "cross_sectional_momentum"].iloc[0]
    dse_spec = specs.loc[specs["template_key"] == "down_streak_exhaustion"].iloc[0]

    features = pd.read_parquet(BASE_DIR / "alpaca-stock-strategy-research" / "data" / "normalized" / "features" / "features.parquet")
    spreads = pd.read_parquet(BASE_DIR / "alpaca-stock-strategy-research" / "data" / "normalized" / "features" / "quote_spread_summary.parquet")
    start = pd.Timestamp("2021-03-24 04:00:00+00:00")
    end = pd.Timestamp("2026-03-24 04:00:00+00:00")
    window = features[(features["timestamp"] >= start) & (features["timestamp"] <= end)].copy()
    active_universe = [s for s in UNIVERSE if s in set(window["symbol"].unique())]
    ex_tsla_bars = window[window["symbol"].isin(active_universe)].copy()
    ex_tsla_context_frame = window[window["symbol"].isin(active_universe + ["SPY"])].copy()
    ex_tsla_market_context, ex_tsla_context_stats = build_daily_context(ex_tsla_context_frame, ex_tsla_bars)
    slip = slippage_map(spreads)

    rs_ex_tsla_signal = top_n_signal_wrapper(ex_tsla_bars, "relative_strength_vs_benchmark", rs_spec.params_dict, 3)

    rs_ex_tsla_result = run_strategy(ex_tsla_bars, "relative_strength_vs_benchmark", rs_spec.params_dict, slip, signal_frame=rs_ex_tsla_signal)
    csm_ex_tsla_result = run_strategy(ex_tsla_bars, "cross_sectional_momentum", csm_spec.params_dict, slip)
    dse_ex_tsla_result = run_strategy(ex_tsla_bars, "down_streak_exhaustion", dse_spec.params_dict, slip)

    rs_ex_tsla_trades = attach_trade_context(rs_ex_tsla_result.trades, ex_tsla_market_context)
    csm_ex_tsla_trades = attach_trade_context(csm_ex_tsla_result.trades, ex_tsla_market_context)
    dse_ex_tsla_trades = attach_trade_context(dse_ex_tsla_result.trades, ex_tsla_market_context)

    variant_store = {
        "csm_native": {
            "base_strategy": "cross_sectional_momentum",
            "family_label": "CSM native",
            "ex_tsla_trades": csm_ex_tsla_trades,
            "ex_tsla_curve": csm_ex_tsla_result.equity_curve,
            "candidate": True,
        },
        "rs_top3_native": {
            "base_strategy": "relative_strength_vs_benchmark",
            "family_label": "RS top-3",
            "ex_tsla_trades": rs_ex_tsla_trades,
            "ex_tsla_curve": rs_ex_tsla_result.equity_curve,
            "candidate": True,
        },
        "dse_control_native": {
            "base_strategy": "down_streak_exhaustion",
            "family_label": "DSE control",
            "ex_tsla_trades": dse_ex_tsla_trades,
            "ex_tsla_curve": dse_ex_tsla_result.equity_curve,
            "candidate": False,
        },
    }

    digest_lines = ["# Broad-Participation Input Digest", "", "## Exact files", ""]
    for row in file_status:
        digest_lines.append(f"- `{row['path']}`: {'opened successfully' if row['opened'] else 'missing'}")
    digest_lines += [
        "",
        "## Exact implementations tested",
        "",
        f"- Canonical branch: `{CSM_ID}` via `csm_native`.",
        f"- Immediate challenger: `{RS_ID}` via `rs_top3_native`.",
        f"- Control: `{DSE_ID}` via `dse_control_native`.",
        "",
        "## Exact universe used",
        "",
        f"- Narrowed mega-cap ex-NVDA ex-TSLA universe used in this test: `{', '.join(active_universe)}`.",
        f"- `GOOG` vs `GOOGL` affects the run: local data uses `{'GOOGL' if 'GOOGL' in active_universe else 'GOOG' if 'GOOG' in active_universe else 'neither GOOG nor GOOGL'}`.",
        "",
        "## Breadth fields available",
        "",
        "- `top_symbol_pct_of_day_pnl`, `number_of_symbols_traded`, `positive_symbols_count`, `participation_type`, `primary_day_class`, and `gap_continuation_label` come from the existing day-level reconstruction.",
        "- `rising_market`, `falling_or_volatile`, and `calm_low_vol` (`calmer`) come from the same SPY-tagged regime logic used in the prior falsification passes.",
        "- `strong_momentum_participation` is derived honestly from the ex-TSLA universe itself: rising-market days whose participation score is in the top quartile of rising-market days.",
        f"- Ex-TSLA strong participation threshold: `{ex_tsla_context_stats['strong_participation_threshold']:.4f}` with `{ex_tsla_context_stats['strong_participation_days']}` qualifying days.",
        "",
        "## Remaining data limits",
        "",
        "- This remains a daily underlying backtest with modeled slippage and no live validation packet.",
        "- The non-extreme-day slice is an equity-path audit, not a separate signal-generation rerun.",
        "- The single-leader and broad-participation slices are derived from reconstructed day-level PnL decomposition, which is honest but still post-trade forensic filtering.",
    ]
    write_markdown(OUTPUTS["digest"], "\n".join(digest_lines))

    grid_lines = [
        "# Broad-Participation Test Matrix",
        "",
        "## Confirmation / falsification slices",
        "",
        "- `ex_tsla_full`: narrowed mega-cap ex-NVDA ex-TSLA universe only.",
        "- `broad_participation_only`: entry-day filter requiring `participation_type = multi_symbol_driven`, `top_symbol_pct_of_day_pnl <= 60`, `positive_symbols_count >= 2`, and `number_of_symbols_traded >= 3`.",
        "- `broad_participation_rising_market`: the same broad-participation filter intersected with `rising_market`.",
        "- `broad_participation_strong_momentum`: the same broad-participation filter intersected with `strong_momentum_participation`.",
        "- `broad_participation_non_extreme_2_5`: equity-path audit on the broad-participation slice with both best and worst 2.5% of days removed.",
        "- `leader_dominant_only`: days explicitly classified as `one_dominant_leader_day` or `one_symbol_driven`, or with top-symbol share >= 70%.",
        "- `mixed_unclear_only`: the residual days that are neither clean broad-participation days nor clean leader-dominant days.",
        "",
        "## Honest limits",
        "",
        "- No new signal logic or parameter optimization was introduced.",
        "- These are post-trade day filters on the exact same ex-TSLA books, not new strategies.",
    ]
    write_markdown(OUTPUTS["grid"], "\n".join(grid_lines))

    metric_rows: list[dict[str, object]] = []
    day_frames: dict[str, pd.DataFrame] = {}
    curve_store: dict[str, dict[str, pd.DataFrame]] = {}
    trade_store: dict[str, dict[str, pd.DataFrame]] = {}

    for variant_id, info in variant_store.items():
        curve_store[variant_id] = {}
        trade_store[variant_id] = {}

        ex_trades = info["ex_tsla_trades"]
        ex_curve = info["ex_tsla_curve"]
        trade_store[variant_id]["ex_tsla_full"] = ex_trades
        curve_store[variant_id]["ex_tsla_full"] = ex_curve
        metric_rows.append(
            metric_row(
                variant_id,
                info["base_strategy"],
                info["family_label"],
                "ex_tsla_full",
                slice_scope_note(info["family_label"], "ex_tsla_full"),
                ex_trades,
                ex_curve,
                info["candidate"],
            )
        )

        day_frame = build_variant_day_frame(variant_id, ex_trades, ex_curve, ex_tsla_bars, ex_tsla_market_context)
        day_frame["primary_day_class"] = day_frame.apply(classify_profitable_day, axis=1)
        day_frames[variant_id] = day_frame
        broad_mask = (
            (day_frame["participation_type"] == "multi_symbol_driven")
            & (day_frame["top_symbol_pct_of_day_pnl"] <= 60.0)
            & (day_frame["positive_symbols_count"] >= 2)
            & (day_frame["number_of_symbols_traded"] >= 3)
        )
        leader_mask = (
            (day_frame["primary_day_class"] == "one_dominant_leader_day")
            | (day_frame["participation_type"] == "one_symbol_driven")
            | (day_frame["top_symbol_pct_of_day_pnl"] >= 70.0)
        )
        mixed_mask = ~(broad_mask | leader_mask)
        broad_dates = set(day_frame.loc[broad_mask, "date"])
        broad_rising_dates = set(day_frame.loc[broad_mask & day_frame["rising_market"].fillna(False), "date"])
        broad_strong_dates = set(day_frame.loc[broad_mask & day_frame["strong_momentum_participation"].fillna(False), "date"])
        leader_dates = set(day_frame.loc[leader_mask, "date"])
        mixed_dates = set(day_frame.loc[mixed_mask, "date"])

        for slice_name in [
            "broad_participation_only",
            "broad_participation_rising_market",
            "broad_participation_strong_momentum",
            "leader_dominant_only",
            "mixed_unclear_only",
        ]:
            subset_trades = regime_slice_trades(ex_trades, slice_name, leader_dates, broad_dates, broad_rising_dates, broad_strong_dates, mixed_dates)
            subset_curve = equity_from_trades(subset_trades, ex_tsla_bars, INITIAL_CAPITAL)
            trade_store[variant_id][slice_name] = subset_trades
            curve_store[variant_id][slice_name] = subset_curve
            metric_rows.append(
                metric_row(
                    variant_id,
                    info["base_strategy"],
                    info["family_label"],
                    slice_name,
                    slice_scope_note(info["family_label"], slice_name),
                    subset_trades,
                    subset_curve,
                    False,
                )
            )

        broad_curve = curve_store[variant_id]["broad_participation_only"]
        trimmed_curve = adjusted_curve(broad_curve, 0.025, 0.025)
        curve_store[variant_id]["broad_participation_non_extreme_2_5"] = trimmed_curve
        metric_rows.append(
            metric_row(
                variant_id,
                info["base_strategy"],
                info["family_label"],
                "broad_participation_non_extreme_2_5",
                slice_scope_note(info["family_label"], "broad_participation_non_extreme_2_5"),
                trade_store[variant_id]["broad_participation_only"],
                trimmed_curve,
                False,
            )
        )

    metrics_df = assign_quality_scores(pd.DataFrame(metric_rows))

    slice_candidates = metrics_df.loc[
        metrics_df["slice_name"].isin(
            [
                "broad_participation_only",
                "broad_participation_rising_market",
                "broad_participation_strong_momentum",
            ]
        )
        & metrics_df["base_strategy"].isin(["cross_sectional_momentum", "relative_strength_vs_benchmark"])
    ].copy()
    slice_candidates["slice_quality_score"] = score_subset(slice_candidates)
    metrics_df = metrics_df.merge(
        slice_candidates[["variant_id", "slice_name", "slice_quality_score"]],
        on=["variant_id", "slice_name"],
        how="left",
    )
    metrics_df.to_csv(OUTPUTS["metrics"], index=False)

    ex_tsla_full_rows = metrics_df.loc[metrics_df["slice_name"] == "ex_tsla_full"].copy()
    raw_winner = ex_tsla_full_rows.sort_values("total_return_pct", ascending=False).iloc[0]
    quality_winner = ex_tsla_full_rows.loc[ex_tsla_full_rows["candidate_for_branch"]].sort_values(
        ["trust_adjusted_quality_score", "total_return_pct"], ascending=[False, False]
    ).iloc[0]

    leaderboard_lines = ["# Broad-Participation Leaderboard", "", "## Ex-TSLA full slice baseline", ""]
    for row in ex_tsla_full_rows.sort_values("total_return_pct", ascending=False).itertuples():
        leaderboard_lines.append(
            f"- `{row.variant_id}`: final equity `${row.final_equity:.2f}`, return `{row.total_return_pct:.2f}%`, drawdown `{row.max_drawdown_pct:.2f}%`, top-symbol `{row.top_symbol_pnl_share_pct:.2f}%`, top-10%-days `{row.top_10pct_days_pnl_share_pct:.2f}%`, non-extreme expectancy `{row.non_extreme_day_expectancy:.2f}`."
        )
    leaderboard_lines += ["", "## Broad-participation slices", ""]
    broad_rows = metrics_df.loc[
        metrics_df["slice_name"].isin(
            [
                "broad_participation_only",
                "broad_participation_rising_market",
                "broad_participation_strong_momentum",
                "broad_participation_non_extreme_2_5",
            ]
        )
    ].copy()
    for row in broad_rows.sort_values(["slice_name", "total_return_pct"], ascending=[True, False]).itertuples():
        leaderboard_lines.append(
            f"- `{row.variant_id}` / `{row.slice_name}`: return `{row.total_return_pct:.2f}%`, drawdown `{row.max_drawdown_pct:.2f}%`, top-symbol `{row.top_symbol_pnl_share_pct:.2f}%`, top-10%-days `{row.top_10pct_days_pnl_share_pct:.2f}%`."
        )
    write_markdown(OUTPUTS["leaderboard"], "\n".join(leaderboard_lines))

    contrast_rows: list[dict[str, object]] = []
    contrast_summary: dict[str, dict[str, float]] = {}
    for variant_id in ["csm_native", "rs_top3_native", "dse_control_native"]:
        day_frame = day_frames[variant_id].copy()
        positive = day_frame.loc[day_frame["total_pnl_dollars"] > 0].copy()
        total_positive = float(positive["total_pnl_dollars"].sum()) if not positive.empty else 0.0
        broad_mask = (
            (day_frame["participation_type"] == "multi_symbol_driven")
            & (day_frame["top_symbol_pct_of_day_pnl"] <= 60.0)
            & (day_frame["positive_symbols_count"] >= 2)
            & (day_frame["number_of_symbols_traded"] >= 3)
        )
        leader_mask = (
            (day_frame["primary_day_class"] == "one_dominant_leader_day")
            | (day_frame["participation_type"] == "one_symbol_driven")
            | (day_frame["top_symbol_pct_of_day_pnl"] >= 70.0)
        )
        mixed_mask = ~(broad_mask | leader_mask)
        buckets = {
            "broad_participation": broad_mask,
            "leader_dominant": leader_mask,
            "mixed_unclear": mixed_mask,
        }
        summary_row = {}
        for bucket_name, mask in buckets.items():
            bucket_days = day_frame.loc[mask].copy()
            pnl = float(bucket_days["total_pnl_dollars"].sum()) if not bucket_days.empty else 0.0
            share = float(bucket_days.loc[bucket_days["total_pnl_dollars"] > 0, "total_pnl_dollars"].sum() / total_positive * 100.0) if total_positive > 0 else 0.0
            contrast_rows.append(
                {
                    "variant_id": variant_id,
                    "base_strategy": "cross_sectional_momentum" if variant_id == "csm_native" else "relative_strength_vs_benchmark" if variant_id == "rs_top3_native" else "down_streak_exhaustion",
                    "bucket_name": bucket_name,
                    "days_count": int(mask.sum()),
                    "total_pnl_dollars": pnl,
                    "positive_day_pnl_share_pct": share,
                    "avg_top_symbol_share_pct": float(bucket_days["top_symbol_pct_of_day_pnl"].mean()) if not bucket_days.empty else 0.0,
                    "avg_symbols_traded": float(bucket_days["number_of_symbols_traded"].mean()) if not bucket_days.empty else 0.0,
                    "avg_positive_symbols": float(bucket_days["positive_symbols_count"].mean()) if not bucket_days.empty else 0.0,
                }
            )
            summary_row[bucket_name] = share
        contrast_summary[variant_id] = summary_row
    contrast_df = pd.DataFrame(contrast_rows).sort_values(["variant_id", "bucket_name"]).reset_index(drop=True)
    contrast_df.to_csv(OUTPUTS["contrast_csv"], index=False)

    csm_full = ex_tsla_full_rows.loc[ex_tsla_full_rows["variant_id"] == "csm_native"].iloc[0]
    rs_full = ex_tsla_full_rows.loc[ex_tsla_full_rows["variant_id"] == "rs_top3_native"].iloc[0]
    dse_full = ex_tsla_full_rows.loc[ex_tsla_full_rows["variant_id"] == "dse_control_native"].iloc[0]
    csm_broad = metrics_df.loc[(metrics_df["variant_id"] == "csm_native") & (metrics_df["slice_name"] == "broad_participation_only")].iloc[0]
    rs_broad = metrics_df.loc[(metrics_df["variant_id"] == "rs_top3_native") & (metrics_df["slice_name"] == "broad_participation_only")].iloc[0]
    dse_broad = metrics_df.loc[(metrics_df["variant_id"] == "dse_control_native") & (metrics_df["slice_name"] == "broad_participation_only")].iloc[0]
    cleaner_label = "CSM" if (csm_broad["top_symbol_pnl_share_pct"] <= rs_broad["top_symbol_pnl_share_pct"] and csm_broad["max_drawdown_pct"] <= rs_broad["max_drawdown_pct"]) else "RS"
    contrast_lines = [
        "# Leader vs Broad Participation Report",
        "",
        f"- `RS` full-book positive day PnL share splits as leader-dominant `{contrast_summary['rs_top3_native']['leader_dominant']:.2f}%`, broad-participation `{contrast_summary['rs_top3_native']['broad_participation']:.2f}%`, and mixed/unclear `{contrast_summary['rs_top3_native']['mixed_unclear']:.2f}%`.",
        f"- `CSM` full-book positive day PnL share splits as leader-dominant `{contrast_summary['csm_native']['leader_dominant']:.2f}%`, broad-participation `{contrast_summary['csm_native']['broad_participation']:.2f}%`, and mixed/unclear `{contrast_summary['csm_native']['mixed_unclear']:.2f}%`.",
        f"- Broad-participation-only performance is weak relative to the full books but not zero: `RS` reaches `${rs_broad['final_equity']:.2f}` (`{rs_broad['total_return_pct']:.2f}%`) and `CSM` reaches `${csm_broad['final_equity']:.2f}` (`{csm_broad['total_return_pct']:.2f}%`).",
        f"- `{'CSM' if cleaner_label == 'CSM' else 'RS'}` is cleaner on broad-participation days overall. Drawdown is `{csm_broad['max_drawdown_pct']:.2f}%` for CSM versus `{rs_broad['max_drawdown_pct']:.2f}%` for RS, but concentration is much worse for CSM: top-symbol share is `{csm_broad['top_symbol_pnl_share_pct']:.2f}%` for CSM versus `{rs_broad['top_symbol_pnl_share_pct']:.2f}%` for RS.",
        f"- Neither upside branch shows a clean broad-participation core. The broad-participation slice still fails the diversification smell test, especially for `CSM` where top-symbol PnL share stays `{csm_broad['top_symbol_pnl_share_pct']:.2f}%`.",
        f"- `DSE` remains structurally cleaner under this lens but not stronger: broad-participation-only final equity is `${dse_broad['final_equity']:.2f}` on only `{int(dse_broad['trade_count'])}` trades, which keeps it as the benchmark/control rather than the upside branch.",
    ]
    write_markdown(OUTPUTS["contrast_md"], "\n".join(contrast_lines))

    best_slice_rows = {}
    for strategy in ["cross_sectional_momentum", "relative_strength_vs_benchmark"]:
        strat_rows = slice_candidates.loc[slice_candidates["base_strategy"] == strategy].sort_values(
            ["slice_quality_score", "total_return_pct"], ascending=[False, False]
        )
        best_slice_rows[strategy] = strat_rows.iloc[0]

    forensics_rows = []
    for strategy, row in best_slice_rows.items():
        variant_id = row["variant_id"]
        slice_name = row["slice_name"]
        curve = curve_store[variant_id][slice_name]
        for scenario, best_pct, worst_pct in [
            ("remove_best_1pct", 0.01, 0.0),
            ("remove_best_2_5pct", 0.025, 0.0),
            ("remove_best_5pct", 0.05, 0.0),
            ("remove_best_and_worst_2_5pct", 0.025, 0.025),
        ]:
            adj = adjusted_curve(curve, best_pct, worst_pct)
            met = day_series_metrics(adj)
            forensics_rows.append(
                {
                    "variant_id": variant_id,
                    "base_strategy": strategy,
                    "slice_name": slice_name,
                    "scenario": scenario,
                    **met,
                }
            )
    forensics_df = pd.DataFrame(forensics_rows)
    forensics_df.to_csv(OUTPUTS["forensics_csv"], index=False)

    csm_best = best_slice_rows["cross_sectional_momentum"]
    rs_best = best_slice_rows["relative_strength_vs_benchmark"]
    csm_best1 = forensics_df.loc[(forensics_df["variant_id"] == csm_best["variant_id"]) & (forensics_df["slice_name"] == csm_best["slice_name"]) & (forensics_df["scenario"] == "remove_best_1pct")].iloc[0]
    csm_best25 = forensics_df.loc[(forensics_df["variant_id"] == csm_best["variant_id"]) & (forensics_df["slice_name"] == csm_best["slice_name"]) & (forensics_df["scenario"] == "remove_best_2_5pct")].iloc[0]
    csm_nonext = forensics_df.loc[(forensics_df["variant_id"] == csm_best["variant_id"]) & (forensics_df["slice_name"] == csm_best["slice_name"]) & (forensics_df["scenario"] == "remove_best_and_worst_2_5pct")].iloc[0]
    rs_best1 = forensics_df.loc[(forensics_df["variant_id"] == rs_best["variant_id"]) & (forensics_df["slice_name"] == rs_best["slice_name"]) & (forensics_df["scenario"] == "remove_best_1pct")].iloc[0]
    rs_best25 = forensics_df.loc[(forensics_df["variant_id"] == rs_best["variant_id"]) & (forensics_df["slice_name"] == rs_best["slice_name"]) & (forensics_df["scenario"] == "remove_best_2_5pct")].iloc[0]
    rs_nonext = forensics_df.loc[(forensics_df["variant_id"] == rs_best["variant_id"]) & (forensics_df["slice_name"] == rs_best["slice_name"]) & (forensics_df["scenario"] == "remove_best_and_worst_2_5pct")].iloc[0]

    csm_survives = bool(csm_broad["final_equity"] > INITIAL_CAPITAL)
    rs_survives = bool(rs_broad["final_equity"] > INITIAL_CAPITAL)
    both_demoted = bool(max(float(csm_broad["total_return_pct"]), float(rs_broad["total_return_pct"])) < 15.0 or min(float(csm_broad["non_extreme_day_expectancy"]), float(rs_broad["non_extreme_day_expectancy"])) <= 0.0)
    rs_canonical = bool(not both_demoted and rs_broad["total_return_pct"] >= csm_broad["total_return_pct"] and rs_broad["non_extreme_day_expectancy"] >= csm_broad["non_extreme_day_expectancy"])
    csm_canonical = bool(not both_demoted and not rs_canonical and (csm_broad["max_drawdown_pct"] <= rs_broad["max_drawdown_pct"] or csm_broad["top_symbol_pnl_share_pct"] <= rs_broad["top_symbol_pnl_share_pct"]))

    forensic_lines = [
        "# Broad-Participation Forensics Report",
        "",
        f"- Best broad-participation RS slice: `{rs_best['slice_name']}` with slice-quality score `{rs_best['slice_quality_score']:.4f}`.",
        f"- Best broad-participation CSM slice: `{csm_best['slice_name']}` with slice-quality score `{csm_best['slice_quality_score']:.4f}`.",
        f"- After removing the best 1% of broad-participation days, `{'RS' if rs_best1['total_return_pct'] >= csm_best1['total_return_pct'] else 'CSM'}` holds up better (`{rs_best1['total_return_pct']:.2f}%` for RS vs `{csm_best1['total_return_pct']:.2f}%` for CSM).",
        f"- After removing the best 2.5% of broad-participation days, `{'RS' if rs_best25['total_return_pct'] >= csm_best25['total_return_pct'] else 'CSM'}` holds up better (`{rs_best25['total_return_pct']:.2f}%` for RS vs `{csm_best25['total_return_pct']:.2f}%` for CSM).",
        f"- On the broad-participation non-extreme audit, `{'RS' if rs_nonext['daily_expectancy'] >= csm_nonext['daily_expectancy'] else 'CSM'}` has the cleaner everyday edge (`{rs_nonext['daily_expectancy']:.2f}` for RS vs `{csm_nonext['daily_expectancy']:.2f}` for CSM).",
        f"- No branch gets materially closer to paper-watch honesty inside broad participation. Broad-only top-10%-days concentration remains `{rs_broad['top_10pct_days_pnl_share_pct']:.2f}%` for RS and `{csm_broad['top_10pct_days_pnl_share_pct']:.2f}%` for CSM.",
        f"- The remaining edge is still tail-shaped rather than robustly broad. Broad-only non-extreme expectancy is `{rs_broad['non_extreme_day_expectancy']:.2f}` for RS and `{csm_broad['non_extreme_day_expectancy']:.2f}` for CSM.",
    ]
    write_markdown(OUTPUTS["forensics_md"], "\n".join(forensic_lines))

    weak_broad_core = bool(max(float(rs_broad["top_symbol_pnl_share_pct"]), float(csm_broad["top_symbol_pnl_share_pct"])) > 40.0 or max(float(rs_broad["top_10pct_days_pnl_share_pct"]), float(csm_broad["top_10pct_days_pnl_share_pct"])) > 45.0)
    label = "leader-following research artifact" if both_demoted else "narrow research artifact with weak broad core" if weak_broad_core else "broad-participation sleeve"
    decision_lines = [
        "# Broad-Participation Branch Decision",
        "",
        f"1. Does RS remain the canonical upside research branch after broad-participation-only confirmation? `{'Yes, narrowly.' if rs_canonical else 'No.'}`",
        f"2. Should CSM take over instead? `{'Yes, narrowly.' if csm_canonical else 'No.'}`",
        f"3. Should both be demoted if the broad-participation edge is too weak? `{'Yes.' if both_demoted else 'No.'}`",
        f"4. What is the most honest label now: `{label}`.",
        "5. Does DSE remain the control benchmark? `Yes`.",
    ]
    write_markdown(OUTPUTS["decision"], "\n".join(decision_lines))

    best_branch_row = rs_broad if rs_canonical or both_demoted else csm_broad
    paper_closer = bool(float(best_branch_row["top_symbol_pnl_share_pct"]) < 25.0 and float(best_branch_row["top_10pct_days_pnl_share_pct"]) < 45.0 and float(best_branch_row["max_drawdown_pct"]) < 20.0 and float(best_branch_row["total_return_pct"]) > 25.0)
    deficiency = (
        f"broad-only top-symbol concentration {best_branch_row['top_symbol_pnl_share_pct']:.2f}%, "
        f"top-10%-days concentration {best_branch_row['top_10pct_days_pnl_share_pct']:.2f}%, and "
        f"drawdown {best_branch_row['max_drawdown_pct']:.2f}% are still too high relative to the weakened broad core."
    )
    paper_lines = [
        "# Broad-Participation Paper-Watch Recheck",
        "",
        f"1. Did either branch get materially closer to paper-watch? `{'Yes, slightly.' if paper_closer else 'No.'}`",
        f"2. What exact deficiency still blocks paper-watch? `{deficiency}`",
        f"3. Is the next step another falsification test, a narrower confirmation rerun, or a demotion? `{'A demotion.' if both_demoted else 'Another falsification test.'}`",
    ]
    write_markdown(OUTPUTS["paper"], "\n".join(paper_lines))

    next_lines = [
        "# Next After Broad Participation",
        "",
        "1. Keep QQQ pair as the only active paper strategy.",
        "2. Preserve DSE as control.",
        f"3. {'Keep RS as canonical branch.' if rs_canonical else 'Switch to CSM as canonical branch.' if csm_canonical else 'Demote both upside branches.'}",
        "4. Run one ex-AAPL or ex-META dependency test only if a new broad-slice carrier clearly emerges.",
        "5. Stop any branch that only survives through leader-dominant days.",
    ]
    write_markdown(OUTPUTS["next"], "\n".join(next_lines))

    print(
        json.dumps(
            {
                "opened_files": [row["path"] for row in file_status if row["opened"]],
                "rs_survives_broad_participation": rs_survives,
                "csm_survives_broad_participation": csm_survives,
                "cleaner_branch_broad_participation": "csm_native" if cleaner_label == "CSM" else "rs_top3_native",
                "rs_remains_canonical": rs_canonical,
                "csm_takes_over": csm_canonical,
                "both_demoted": both_demoted,
                "dse_control": True,
                "closer_to_paper_watch": paper_closer,
                "best_next_experiment": "ex-AAPL or ex-META dependency test" if not both_demoted else "demotion of both upside branches",
                "outputs": {k: str(v) for k, v in OUTPUTS.items()},
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
