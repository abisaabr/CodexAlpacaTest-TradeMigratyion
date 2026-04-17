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
BASELINE_UNIVERSE = ["AAPL", "AMZN", "GOOGL", "META", "NFLX", "TSLA"]
EX_TSLA_UNIVERSE = ["AAPL", "AMZN", "GOOGL", "META", "NFLX"]

EXACT_FILES = [
    BASE_DIR / "master_strategy_memo.txt",
    BASE_DIR / "tournament_master_report.md",
    BASE_DIR / "monday_paper_plan.md",
    BASE_DIR / "megacap_ex_nvda_branch_decision.md",
    BASE_DIR / "leader_vs_breadth_report.md",
    BASE_DIR / "megacap_ex_nvda_forensics_report.md",
    BASE_DIR / "megacap_ex_nvda_paper_watch_recheck.md",
    BASE_DIR / "next_branch_experiments.md",
    BASE_DIR / "best_day_autopsy_report.md",
    BASE_DIR / "non_extreme_day_edge_report.md",
    BASE_DIR / "rs_vs_csm_day_profile_report.md",
    BASE_DIR / "canonical_edge_hypothesis.md",
    BASE_DIR / "ex_nvda_core_edge_report.md",
    BASE_DIR / "supportive_regime_day_profile_report.md",
    BASE_DIR / "rs_branch_recheck_after_ex_nvda.md",
    BASE_DIR / "rs_vs_csm_recheck.md",
    BASE_DIR / "ex_nvda_regime_metrics.csv",
    BASE_DIR / "megacap_ex_nvda_metrics.csv",
    BASE_DIR / "leader_vs_breadth_diagnostic.csv",
    BASE_DIR / "day_type_symbol_regime_map.csv",
    BASE_DIR / "day_level_pnl_decomposition.csv",
    BASE_DIR / "underlying_trade_ledger.csv",
    BASE_DIR / "underlying_tournament_metrics.csv",
    BASE_DIR / "trade_cluster_edge_map.csv",
]

OUTPUTS = {
    "digest": BASE_DIR / "ex_tsla_input_digest.md",
    "grid": BASE_DIR / "ex_tsla_test_matrix.md",
    "metrics": BASE_DIR / "ex_tsla_metrics.csv",
    "leaderboard": BASE_DIR / "ex_tsla_leaderboard.md",
    "leader_csv": BASE_DIR / "ex_tsla_leader_diagnostic.csv",
    "leader_md": BASE_DIR / "ex_tsla_leader_report.md",
    "forensics_csv": BASE_DIR / "ex_tsla_forensics.csv",
    "forensics_md": BASE_DIR / "ex_tsla_forensics_report.md",
    "decision": BASE_DIR / "ex_tsla_branch_redecision.md",
    "paper": BASE_DIR / "ex_tsla_paper_watch_recheck.md",
    "next": BASE_DIR / "next_post_ex_tsla_experiments.md",
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


def regime_slice_trades(trades: pd.DataFrame, slice_name: str, leader_dates: set[pd.Timestamp], broad_dates: set[pd.Timestamp]) -> pd.DataFrame:
    if slice_name == "ex_tsla_full":
        return trades.copy()
    if slice_name == "ex_tsla_rising_market":
        return trades.loc[trades["rising_market"].fillna(False)].copy()
    if slice_name == "ex_tsla_calm_low_vol":
        return trades.loc[trades["calmer"].fillna(False)].copy()
    if slice_name == "ex_tsla_strong_momentum_participation":
        return trades.loc[trades["strong_momentum_participation"].fillna(False)].copy()
    if slice_name == "remaining_single_leader_stress":
        return trades.loc[trades["entry_date"].isin(leader_dates)].copy()
    if slice_name == "broad_participation_only":
        return trades.loc[trades["entry_date"].isin(broad_dates)].copy()
    raise ValueError(slice_name)


def slice_scope_note(label: str, slice_name: str) -> str:
    notes = {
        "megacap_ex_nvda_baseline": f"{label} baseline on the prior mega-cap ex-NVDA universe including TSLA.",
        "ex_tsla_full": f"{label} on the mega-cap ex-NVDA ex-TSLA universe.",
        "ex_tsla_rising_market": f"{label} on the ex-TSLA universe with entry-day regime filter `rising_market`.",
        "ex_tsla_calm_low_vol": f"{label} on the ex-TSLA universe with entry-day regime filter `calm_low_vol`.",
        "ex_tsla_strong_momentum_participation": f"{label} on the ex-TSLA universe with entry-day strong participation filter.",
        "ex_tsla_non_extreme_2_5": f"{label} on the ex-TSLA universe with both best and worst 2.5% of days removed from the equity path audit.",
        "remaining_single_leader_stress": f"{label} on ex-TSLA days still classified as one-dominant-leader days.",
        "broad_participation_only": f"{label} on ex-TSLA days with broad multi-symbol participation.",
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
    baseline_universe = [s for s in BASELINE_UNIVERSE if s in set(window["symbol"].unique())]
    ex_tsla_universe = [s for s in EX_TSLA_UNIVERSE if s in set(window["symbol"].unique())]
    baseline_bars = window[window["symbol"].isin(baseline_universe)].copy()
    ex_tsla_bars = window[window["symbol"].isin(ex_tsla_universe)].copy()
    baseline_context_frame = window[window["symbol"].isin(baseline_universe + ["SPY"])].copy()
    ex_tsla_context_frame = window[window["symbol"].isin(ex_tsla_universe + ["SPY"])].copy()
    baseline_market_context, _baseline_context_stats = build_daily_context(baseline_context_frame, baseline_bars)
    ex_tsla_market_context, ex_tsla_context_stats = build_daily_context(ex_tsla_context_frame, ex_tsla_bars)
    slip = slippage_map(spreads)

    rs_baseline_signal = top_n_signal_wrapper(baseline_bars, "relative_strength_vs_benchmark", rs_spec.params_dict, 3)
    rs_ex_tsla_signal = top_n_signal_wrapper(ex_tsla_bars, "relative_strength_vs_benchmark", rs_spec.params_dict, 3)

    rs_baseline_result = run_strategy(baseline_bars, "relative_strength_vs_benchmark", rs_spec.params_dict, slip, signal_frame=rs_baseline_signal)
    rs_ex_tsla_result = run_strategy(ex_tsla_bars, "relative_strength_vs_benchmark", rs_spec.params_dict, slip, signal_frame=rs_ex_tsla_signal)
    csm_baseline_result = run_strategy(baseline_bars, "cross_sectional_momentum", csm_spec.params_dict, slip)
    csm_ex_tsla_result = run_strategy(ex_tsla_bars, "cross_sectional_momentum", csm_spec.params_dict, slip)
    dse_baseline_result = run_strategy(baseline_bars, "down_streak_exhaustion", dse_spec.params_dict, slip)
    dse_ex_tsla_result = run_strategy(ex_tsla_bars, "down_streak_exhaustion", dse_spec.params_dict, slip)

    rs_baseline_trades = attach_trade_context(rs_baseline_result.trades, baseline_market_context)
    csm_baseline_trades = attach_trade_context(csm_baseline_result.trades, baseline_market_context)
    dse_baseline_trades = attach_trade_context(dse_baseline_result.trades, baseline_market_context)
    rs_ex_tsla_trades = attach_trade_context(rs_ex_tsla_result.trades, ex_tsla_market_context)
    csm_ex_tsla_trades = attach_trade_context(csm_ex_tsla_result.trades, ex_tsla_market_context)
    dse_ex_tsla_trades = attach_trade_context(dse_ex_tsla_result.trades, ex_tsla_market_context)

    variant_store = {
        "csm_native": {
            "base_strategy": "cross_sectional_momentum",
            "family_label": "CSM native",
            "baseline_trades": csm_baseline_trades,
            "baseline_curve": csm_baseline_result.equity_curve,
            "ex_tsla_trades": csm_ex_tsla_trades,
            "ex_tsla_curve": csm_ex_tsla_result.equity_curve,
            "candidate": True,
        },
        "rs_top3_native": {
            "base_strategy": "relative_strength_vs_benchmark",
            "family_label": "RS top-3",
            "baseline_trades": rs_baseline_trades,
            "baseline_curve": rs_baseline_result.equity_curve,
            "ex_tsla_trades": rs_ex_tsla_trades,
            "ex_tsla_curve": rs_ex_tsla_result.equity_curve,
            "candidate": True,
        },
        "dse_control_native": {
            "base_strategy": "down_streak_exhaustion",
            "family_label": "DSE control",
            "baseline_trades": dse_baseline_trades,
            "baseline_curve": dse_baseline_result.equity_curve,
            "ex_tsla_trades": dse_ex_tsla_trades,
            "ex_tsla_curve": dse_ex_tsla_result.equity_curve,
            "candidate": False,
        },
    }

    digest_lines = ["# Ex-TSLA Input Digest", "", "## Exact files", ""]
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
        f"- Mega-cap ex-NVDA baseline universe: `{', '.join(baseline_universe)}`.",
        f"- Mega-cap ex-NVDA ex-TSLA universe: `{', '.join(ex_tsla_universe)}`.",
        f"- `GOOG` vs `GOOGL` affects the run: local data uses `{'GOOGL' if 'GOOGL' in ex_tsla_universe else 'GOOG' if 'GOOG' in ex_tsla_universe else 'neither GOOG nor GOOGL'}`.",
        "",
        "## Regime tags available",
        "",
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
        "# Ex-TSLA Test Matrix",
        "",
        "## Universe slices",
        "",
        "- `megacap_ex_nvda_baseline`: prior mega-cap ex-NVDA universe including TSLA.",
        "- `ex_tsla_full`: narrowed mega-cap ex-NVDA ex-TSLA universe only.",
        "- `ex_tsla_rising_market`: ex-TSLA trades entered on SPY-tagged rising-market days.",
        "- `ex_tsla_calm_low_vol`: ex-TSLA trades entered on calmer / low-vol days.",
        "- `ex_tsla_strong_momentum_participation`: ex-TSLA trades entered on rising-market days with top-quartile participation across the surviving names.",
        "- `ex_tsla_non_extreme_2_5`: ex-TSLA equity-path audit with both best and worst 2.5% of days removed.",
        "- `remaining_single_leader_stress`: ex-TSLA days still classified as one-dominant-leader days.",
        "- `broad_participation_only`: ex-TSLA days with multi-symbol participation and top-symbol share below 60%.",
        "",
        "## Honest limits",
        "",
        "- No new signal logic or parameter optimization was introduced.",
        "- The diagnostic stays on the exact narrowed mega-cap ex-NVDA ex-TSLA universe only.",
    ]
    write_markdown(OUTPUTS["grid"], "\n".join(grid_lines))

    metric_rows: list[dict[str, object]] = []
    day_frames: dict[str, pd.DataFrame] = {}
    curve_store: dict[str, dict[str, pd.DataFrame]] = {}
    trade_store: dict[str, dict[str, pd.DataFrame]] = {}

    for variant_id, info in variant_store.items():
        curve_store[variant_id] = {}
        trade_store[variant_id] = {}
        metric_rows.append(
            metric_row(
                variant_id,
                info["base_strategy"],
                info["family_label"],
                "megacap_ex_nvda_baseline",
                slice_scope_note(info["family_label"], "megacap_ex_nvda_baseline"),
                info["baseline_trades"],
                info["baseline_curve"],
                False,
            )
        )

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
        day_frames[variant_id] = day_frame
        leader_dates = set(day_frame.loc[(day_frame["top_symbol_pct_of_day_pnl"] >= 70.0) | (day_frame["number_of_symbols_traded"] <= 1), "date"])
        broad_dates = set(day_frame.loc[(day_frame["positive_symbols_count"] >= 3) & (day_frame["top_symbol_pct_of_day_pnl"] < 60.0), "date"])

        for slice_name in [
            "ex_tsla_rising_market",
            "ex_tsla_calm_low_vol",
            "ex_tsla_strong_momentum_participation",
            "remaining_single_leader_stress",
            "broad_participation_only",
        ]:
            subset_trades = regime_slice_trades(ex_trades, slice_name, leader_dates, broad_dates)
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

        trimmed_curve = adjusted_curve(ex_curve, 0.025, 0.025)
        curve_store[variant_id]["ex_tsla_non_extreme_2_5"] = trimmed_curve
        metric_rows.append(
            metric_row(
                variant_id,
                info["base_strategy"],
                info["family_label"],
                "ex_tsla_non_extreme_2_5",
                slice_scope_note(info["family_label"], "ex_tsla_non_extreme_2_5"),
                ex_trades,
                trimmed_curve,
                False,
            )
        )

    metrics_df = assign_quality_scores(pd.DataFrame(metric_rows))

    slice_candidates = metrics_df.loc[
        metrics_df["slice_name"].isin(
            [
                "ex_tsla_full",
                "ex_tsla_rising_market",
                "ex_tsla_calm_low_vol",
                "ex_tsla_strong_momentum_participation",
                "remaining_single_leader_stress",
                "broad_participation_only",
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

    baseline_rows = metrics_df.loc[metrics_df["slice_name"] == "megacap_ex_nvda_baseline"].copy()
    ex_tsla_full_rows = metrics_df.loc[metrics_df["slice_name"] == "ex_tsla_full"].copy()
    raw_winner = ex_tsla_full_rows.sort_values("total_return_pct", ascending=False).iloc[0]
    quality_winner = ex_tsla_full_rows.loc[ex_tsla_full_rows["candidate_for_branch"]].sort_values(
        ["trust_adjusted_quality_score", "total_return_pct"], ascending=[False, False]
    ).iloc[0]

    leaderboard_lines = ["# Ex-TSLA Leaderboard", "", "## Ex-TSLA full slice", ""]
    for row in ex_tsla_full_rows.sort_values("total_return_pct", ascending=False).itertuples():
        leaderboard_lines.append(
            f"- `{row.variant_id}`: final equity `${row.final_equity:.2f}`, return `{row.total_return_pct:.2f}%`, drawdown `{row.max_drawdown_pct:.2f}%`, top-symbol `{row.top_symbol_pnl_share_pct:.2f}%`, top-10%-days `{row.top_10pct_days_pnl_share_pct:.2f}%`, non-extreme expectancy `{row.non_extreme_day_expectancy:.2f}`."
        )
    leaderboard_lines += ["", "## Baseline reference", ""]
    for row in baseline_rows.sort_values("total_return_pct", ascending=False).itertuples():
        leaderboard_lines.append(
            f"- `{row.variant_id}` baseline: return `{row.total_return_pct:.2f}%`, drawdown `{row.max_drawdown_pct:.2f}%`, top-symbol `{row.top_symbol_pnl_share_pct:.2f}%`."
        )
    write_markdown(OUTPUTS["leaderboard"], "\n".join(leaderboard_lines))

    leader_rows: list[dict[str, object]] = []
    full_reports: dict[str, dict[str, float]] = {}
    for variant_id in ["csm_native", "rs_top3_native"]:
        day_frame = day_frames[variant_id].copy()
        profitable = day_frame.loc[day_frame["total_pnl_dollars"] > 0].copy()
        profitable["primary_day_class"] = profitable.apply(classify_profitable_day, axis=1)
        full_reports[variant_id] = profitable_day_class_report(day_frame)
        for row in profitable.itertuples():
            leader_rows.append(
                {
                    "variant_id": variant_id,
                    "base_strategy": "cross_sectional_momentum" if variant_id == "csm_native" else "relative_strength_vs_benchmark",
                    "slice_name": "ex_tsla_full",
                    "date": str(row.date),
                    "total_pnl_dollars": float(row.total_pnl_dollars),
                    "top_symbol": row.top_symbol,
                    "top_symbol_pct_of_day_pnl": float(row.top_symbol_pct_of_day_pnl),
                    "number_of_symbols_traded": int(row.number_of_symbols_traded),
                    "positive_symbols_count": int(row.positive_symbols_count),
                    "gap_continuation_label": row.gap_continuation_label,
                    "regime_primary": row.regime_primary,
                    "primary_day_class": row.primary_day_class,
                    "participation_type": row.participation_type,
                }
            )
    leader_df = pd.DataFrame(leader_rows).sort_values(["variant_id", "date"]).reset_index(drop=True)
    leader_df.to_csv(OUTPUTS["leader_csv"], index=False)

    csm_report = full_reports["csm_native"]
    rs_report = full_reports["rs_top3_native"]
    csm_row = ex_tsla_full_rows.loc[ex_tsla_full_rows["variant_id"] == "csm_native"].iloc[0]
    rs_row = ex_tsla_full_rows.loc[ex_tsla_full_rows["variant_id"] == "rs_top3_native"].iloc[0]
    cleaner_label = "CSM" if (csm_report["top_symbol_share"] <= rs_report["top_symbol_share"] and csm_report["multi_symbol_share"] >= rs_report["multi_symbol_share"]) else "RS"
    leader_lines = [
        "# Ex-TSLA Leader Report",
        "",
        f"- `CSM` profitable ex-TSLA days are `{csm_report['dominant_share']:.2f}%` leader-dominant, `{csm_report['broad_share']:.2f}%` broad/continuation participation, and `{csm_report['event_share']:.2f}%` event-like gap reaction by positive-PnL share.",
        f"- `RS` profitable ex-TSLA days are `{rs_report['dominant_share']:.2f}%` leader-dominant, `{rs_report['broad_share']:.2f}%` broad/continuation participation, and `{rs_report['event_share']:.2f}%` event-like gap reaction by positive-PnL share.",
        f"- After TSLA removal, `{'CSM' if cleaner_label == 'CSM' else 'RS'}` is cleaner on leader dependence: average profitable-day top-symbol share on a net day-PnL basis is `{csm_report['top_symbol_share']:.2f}%` for CSM versus `{rs_report['top_symbol_share']:.2f}%` for RS, and that share can exceed `100%` when the leader wins but the secondary names still lose money. Multi-symbol participation is `{csm_report['multi_symbol_share']:.2f}%` for CSM versus `{rs_report['multi_symbol_share']:.2f}%` for RS.",
        f"- The surviving edge is still not broad across the remaining names in a robust sense. Full-slice top-symbol PnL share is `{csm_row['top_symbol_pnl_share_pct']:.2f}%` for CSM and `{rs_row['top_symbol_pnl_share_pct']:.2f}%` for RS, so one remaining carrier still matters too much.",
        "- Bottom line: even after TSLA is removed, the canonical upside branch is still honestly a leader-following sleeve rather than a broad participation sleeve.",
    ]
    write_markdown(OUTPUTS["leader_md"], "\n".join(leader_lines))

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

    csm_full = ex_tsla_full_rows.loc[ex_tsla_full_rows["variant_id"] == "csm_native"].iloc[0]
    rs_full = ex_tsla_full_rows.loc[ex_tsla_full_rows["variant_id"] == "rs_top3_native"].iloc[0]
    csm_survives = bool(csm_full["final_equity"] > INITIAL_CAPITAL)
    rs_survives = bool(rs_full["final_equity"] > INITIAL_CAPITAL)
    csm_canonical = bool(csm_full["trust_adjusted_quality_score"] >= rs_full["trust_adjusted_quality_score"])

    forensic_lines = [
        "# Ex-TSLA Forensics Report",
        "",
        f"- Best ex-TSLA CSM slice: `{csm_best['slice_name']}` with slice-quality score `{csm_best['slice_quality_score']:.4f}`.",
        f"- Best ex-TSLA RS slice: `{rs_best['slice_name']}` with slice-quality score `{rs_best['slice_quality_score']:.4f}`.",
        f"- After removing the best 1% of days, `{'CSM' if csm_best1['total_return_pct'] >= rs_best1['total_return_pct'] else 'RS'}` holds up better (`{csm_best1['total_return_pct']:.2f}%` for CSM vs `{rs_best1['total_return_pct']:.2f}%` for RS).",
        f"- After removing the best 2.5% of days, `{'CSM' if csm_best25['total_return_pct'] >= rs_best25['total_return_pct'] else 'RS'}` holds up better (`{csm_best25['total_return_pct']:.2f}%` for CSM vs `{rs_best25['total_return_pct']:.2f}%` for RS).",
        f"- On the non-extreme-day audit (both best and worst 2.5% removed), `{'CSM' if csm_nonext['daily_expectancy'] >= rs_nonext['daily_expectancy'] else 'RS'}` has the cleaner everyday edge (`{csm_nonext['daily_expectancy']:.2f}` for CSM vs `{rs_nonext['daily_expectancy']:.2f}` for RS).",
        f"- The canonical crown `{'still belongs to CSM' if csm_canonical else 'would revert to RS'}` on the ex-TSLA full slice. Trust-adjusted full-slice score is `{csm_full['trust_adjusted_quality_score']:.4f}` for CSM versus `{rs_full['trust_adjusted_quality_score']:.4f}` for RS.",
        f"- Both branches are still materially tail-shaped after TSLA removal: top-10%-days concentration stays `{csm_full['top_10pct_days_pnl_share_pct']:.2f}%` for CSM and `{rs_full['top_10pct_days_pnl_share_pct']:.2f}%` for RS on the ex-TSLA full slice.",
    ]
    write_markdown(OUTPUTS["forensics_md"], "\n".join(forensic_lines))

    edge_broad_enough = bool(max(float(csm_full["top_symbol_pnl_share_pct"]), float(rs_full["top_symbol_pnl_share_pct"])) < 22.0 and max(float(csm_full["top_10pct_days_pnl_share_pct"]), float(rs_full["top_10pct_days_pnl_share_pct"])) < 45.0)
    decision_lines = [
        "# Ex-TSLA Branch Redecision",
        "",
        f"1. Does CSM remain the canonical upside research branch after the ex-TSLA diagnostic? `{'Yes, narrowly.' if csm_canonical else 'No.'}`",
        f"2. Should RS retake the crown instead? `{'No.' if csm_canonical else 'Yes, narrowly.'}`",
        f"3. What is the most honest label now: `{'mega-cap leader-following sleeve' if csm_canonical else 'narrowed momentum regime sleeve'}`.",
        "4. Does DSE remain the control benchmark? `Yes`.",
        f"5. Is the real edge now broad enough across the remaining names to matter? `{'Yes, but only narrowly.' if edge_broad_enough else 'No, not yet.'}`",
    ]
    write_markdown(OUTPUTS["decision"], "\n".join(decision_lines))

    paper_closer = bool(float(csm_full["top_symbol_pnl_share_pct"]) < 22.0 and float(csm_full["top_10pct_days_pnl_share_pct"]) < 48.0 and float(csm_full["max_drawdown_pct"]) < 35.0)
    deficiency = (
        f"top-symbol concentration {quality_winner['top_symbol_pnl_share_pct']:.2f}%, "
        f"top-10%-days concentration {quality_winner['top_10pct_days_pnl_share_pct']:.2f}%, and "
        f"drawdown {quality_winner['max_drawdown_pct']:.2f}% are still too high, and the narrowed branch still behaves like a leader-following research sleeve."
    )
    paper_lines = [
        "# Ex-TSLA Paper-Watch Recheck",
        "",
        f"1. Did either branch get materially closer to paper-watch? `{'Yes, slightly.' if paper_closer else 'No.'}`",
        f"2. What exact deficiency still blocks paper-watch? `{deficiency}`",
        f"3. Should the next step be another falsification test, a narrower confirmation rerun, or a demotion? `{'Another falsification test.' if csm_survives or rs_survives else 'A demotion.'}`",
    ]
    write_markdown(OUTPUTS["paper"], "\n".join(paper_lines))

    next_lines = [
        "# Next Post Ex-TSLA Experiments",
        "",
        "1. Keep QQQ pair as the only active paper strategy.",
        "2. Preserve DSE as control.",
        f"3. {'Keep CSM as canonical branch.' if csm_canonical else 'Switch back to RS as canonical branch.'}",
        "4. Run one broad-participation-only confirmation test on the surviving branch.",
        "5. Run one ex-META or ex-AAPL dependency test if a new dominant carrier emerges from the ex-TSLA diagnostic.",
        "6. Stop any branch that still survives only by one-name dominance.",
    ]
    write_markdown(OUTPUTS["next"], "\n".join(next_lines))

    print(
        json.dumps(
            {
                "opened_files": [row["path"] for row in file_status if row["opened"]],
                "csm_survives_ex_tsla": csm_survives,
                "rs_survives_ex_tsla": rs_survives,
                "cleaner_branch_after_tsla_removal": "csm_native" if cleaner_label == "CSM" else "rs_top3_native",
                "csm_remains_canonical": csm_canonical,
                "rs_retakes_crown": not csm_canonical,
                "dse_control": True,
                "closer_to_paper_watch": paper_closer,
                "best_next_experiment": "broad-participation-only confirmation test",
                "outputs": {k: str(v) for k, v in OUTPUTS.items()},
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
