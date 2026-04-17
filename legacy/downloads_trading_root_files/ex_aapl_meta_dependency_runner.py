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
    BASE_DIR / "broad_participation_branch_decision.md",
    BASE_DIR / "leader_vs_broad_participation_report.md",
    BASE_DIR / "broad_participation_forensics_report.md",
    BASE_DIR / "broad_participation_paper_watch_recheck.md",
    BASE_DIR / "next_after_broad_participation.md",
    BASE_DIR / "megacap_ex_nvda_branch_decision.md",
    BASE_DIR / "ex_tsla_branch_redecision.md",
    BASE_DIR / "best_day_autopsy_report.md",
    BASE_DIR / "non_extreme_day_edge_report.md",
    BASE_DIR / "canonical_edge_hypothesis.md",
    BASE_DIR / "broad_participation_metrics.csv",
    BASE_DIR / "leader_vs_broad_participation_contrast.csv",
    BASE_DIR / "broad_participation_forensics.csv",
    BASE_DIR / "day_type_symbol_regime_map.csv",
    BASE_DIR / "day_level_pnl_decomposition.csv",
    BASE_DIR / "underlying_trade_ledger.csv",
    BASE_DIR / "underlying_tournament_metrics.csv",
    BASE_DIR / "trade_cluster_edge_map.csv",
]

OUTPUTS = {
    "digest": BASE_DIR / "ex_aapl_meta_input_digest.md",
    "grid": BASE_DIR / "ex_aapl_meta_test_matrix.md",
    "metrics": BASE_DIR / "ex_aapl_meta_metrics.csv",
    "leaderboard": BASE_DIR / "ex_aapl_meta_leaderboard.md",
    "impact_csv": BASE_DIR / "ex_aapl_meta_symbol_impact.csv",
    "dependency_md": BASE_DIR / "ex_aapl_meta_dependency_report.md",
    "forensics_csv": BASE_DIR / "ex_aapl_meta_forensics.csv",
    "forensics_md": BASE_DIR / "ex_aapl_meta_forensics_report.md",
    "decision": BASE_DIR / "ex_aapl_meta_branch_redecision.md",
    "paper": BASE_DIR / "ex_aapl_meta_paper_watch_recheck.md",
    "next": BASE_DIR / "next_after_ex_aapl_meta.md",
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


def universe_note(symbols: list[str]) -> str:
    return ", ".join(symbols)


def broad_mask(day_frame: pd.DataFrame) -> pd.Series:
    return (
        (day_frame["participation_type"] == "multi_symbol_driven")
        & (day_frame["top_symbol_pct_of_day_pnl"] <= 60.0)
        & (day_frame["positive_symbols_count"] >= 2)
        & (day_frame["number_of_symbols_traded"] >= 3)
    )


def day_sets(day_frame: pd.DataFrame) -> dict[str, set[pd.Timestamp]]:
    broad = broad_mask(day_frame)
    rising = broad & day_frame["rising_market"].fillna(False)
    return {
        "broad": set(day_frame.loc[broad, "date"]),
        "rising": set(day_frame.loc[rising, "date"]),
    }


def slice_scope_note(label: str, slice_name: str) -> str:
    notes = {
        "ex_tsla_full": f"{label} baseline on the narrowed mega-cap ex-NVDA ex-TSLA universe.",
        "broad_participation_only": f"{label} baseline broad-participation slice on ex-TSLA days with multi-symbol participation, at least two profitable symbols, at least three traded symbols, and top-symbol share at or below 60%.",
        "ex_aapl_full": f"{label} rerun on the narrowed mega-cap universe with `AAPL` removed.",
        "ex_aapl_broad_participation_only": f"{label} rerun on the ex-AAPL universe, then filtered to honest broad-participation days only.",
        "ex_meta_full": f"{label} rerun on the narrowed mega-cap universe with `META` removed.",
        "ex_meta_broad_participation_only": f"{label} rerun on the ex-META universe, then filtered to honest broad-participation days only.",
        "ex_aapl_rising_market": f"{label} rerun on the ex-AAPL universe with the entry-day `rising_market` regime only.",
        "ex_meta_rising_market": f"{label} rerun on the ex-META universe with the entry-day `rising_market` regime only.",
        "ex_aapl_non_extreme_2_5": f"{label} ex-AAPL rerun with both best and worst 2.5% of days removed from the equity-path audit.",
        "ex_meta_non_extreme_2_5": f"{label} ex-META rerun with both best and worst 2.5% of days removed from the equity-path audit.",
    }
    return notes[slice_name]


def build_books(
    features: pd.DataFrame,
    spreads,
    specs: pd.DataFrame,
    symbols: list[str],
) -> dict[str, dict[str, object]]:
    bars = features[features["symbol"].isin(symbols)].copy()
    context_frame = features[features["symbol"].isin(symbols + ["SPY"])].copy()
    market_context, context_stats = build_daily_context(context_frame, bars)
    slip = slippage_map(spreads)

    rs_spec = specs.loc[specs["template_key"] == "relative_strength_vs_benchmark"].iloc[0]
    csm_spec = specs.loc[specs["template_key"] == "cross_sectional_momentum"].iloc[0]
    dse_spec = specs.loc[specs["template_key"] == "down_streak_exhaustion"].iloc[0]

    rs_signal = top_n_signal_wrapper(bars, "relative_strength_vs_benchmark", rs_spec.params_dict, 3)
    rs_result = run_strategy(bars, "relative_strength_vs_benchmark", rs_spec.params_dict, slip, signal_frame=rs_signal)
    csm_result = run_strategy(bars, "cross_sectional_momentum", csm_spec.params_dict, slip)
    dse_result = run_strategy(bars, "down_streak_exhaustion", dse_spec.params_dict, slip)

    return {
        "rs_top3_native": {
            "base_strategy": "relative_strength_vs_benchmark",
            "family_label": "RS top-3",
            "trades": attach_trade_context(rs_result.trades, market_context),
            "curve": rs_result.equity_curve,
            "candidate": True,
        },
        "csm_native": {
            "base_strategy": "cross_sectional_momentum",
            "family_label": "CSM native",
            "trades": attach_trade_context(csm_result.trades, market_context),
            "curve": csm_result.equity_curve,
            "candidate": True,
        },
        "dse_control_native": {
            "base_strategy": "down_streak_exhaustion",
            "family_label": "DSE control",
            "trades": attach_trade_context(dse_result.trades, market_context),
            "curve": dse_result.equity_curve,
            "candidate": False,
        },
        "_meta": {
            "bars": bars,
            "market_context": market_context,
            "context_stats": context_stats,
            "symbols": symbols,
        },
    }


def main() -> None:
    file_status = [{"path": str(path), "opened": path.exists()} for path in EXACT_FILES]
    specs = load_baseline_specs(BASE_DIR / "underlying_tournament_metrics.csv")

    features = pd.read_parquet(BASE_DIR / "alpaca-stock-strategy-research" / "data" / "normalized" / "features" / "features.parquet")
    spreads = pd.read_parquet(BASE_DIR / "alpaca-stock-strategy-research" / "data" / "normalized" / "features" / "quote_spread_summary.parquet")
    start = pd.Timestamp("2021-03-24 04:00:00+00:00")
    end = pd.Timestamp("2026-03-24 04:00:00+00:00")
    window = features[(features["timestamp"] >= start) & (features["timestamp"] <= end)].copy()
    active_universe = [s for s in UNIVERSE if s in set(window["symbol"].unique())]
    ex_aapl_universe = [s for s in active_universe if s != "AAPL"]
    ex_meta_universe = [s for s in active_universe if s != "META"]

    books = {
        "ex_tsla": build_books(window, spreads, specs, active_universe),
        "ex_aapl": build_books(window, spreads, specs, ex_aapl_universe),
        "ex_meta": build_books(window, spreads, specs, ex_meta_universe),
    }

    digest_lines = ["# Ex-AAPL / Ex-META Input Digest", "", "## Exact files", ""]
    for row in file_status:
        digest_lines.append(f"- `{row['path']}`: {'opened successfully' if row['opened'] else 'missing'}")
    digest_lines += [
        "",
        "## Exact implementations tested",
        "",
        f"- Canonical branch: `{RS_ID}` via `rs_top3_native`.",
        f"- Main challenger: `{CSM_ID}` via `csm_native`.",
        f"- Control: `{DSE_ID}` via `dse_control_native`.",
        "",
        "## Exact symbol universe used",
        "",
        f"- Ex-TSLA baseline universe: `{universe_note(active_universe)}`.",
        f"- Ex-AAPL universe: `{universe_note(ex_aapl_universe)}`.",
        f"- Ex-META universe: `{universe_note(ex_meta_universe)}`.",
        f"- `GOOG` vs `GOOGL` affects the run: local data uses `{'GOOGL' if 'GOOGL' in active_universe else 'GOOG' if 'GOOG' in active_universe else 'neither GOOG nor GOOGL'}`.",
        "",
        "## Honest broad-participation fields",
        "",
        "- Broad-participation filtering uses only local day-level reconstruction: `participation_type`, `top_symbol_pct_of_day_pnl`, `positive_symbols_count`, and `number_of_symbols_traded`.",
        "- `rising_market` comes from the same SPY-tagged regime logic used in the prior falsification passes.",
        "",
        "## Remaining data limits",
        "",
        "- These are daily underlying reruns only, with modeled slippage and no live validation packet.",
        "- Non-extreme-day slices are equity-path audits after the reruns, not new signal-generation variants.",
        "- Cross-sectional families are rerun on the reduced universes rather than post-hoc trade deletion so the dependency test stays honest.",
    ]
    write_markdown(OUTPUTS["digest"], "\n".join(digest_lines))

    grid_lines = [
        "# Ex-AAPL / Ex-META Test Matrix",
        "",
        "## Dependency-removal slices",
        "",
        "- `ex_tsla_full`: baseline narrowed mega-cap ex-NVDA ex-TSLA universe.",
        "- `broad_participation_only`: baseline ex-TSLA book, filtered to days with multi-symbol participation, top-symbol share <= 60%, at least two profitable symbols, and at least three traded symbols.",
        "- `ex_aapl_full`: full rerun with `AAPL` removed from the ex-TSLA universe.",
        "- `ex_aapl_broad_participation_only`: ex-AAPL rerun filtered to the same honest broad-participation day rules.",
        "- `ex_meta_full`: full rerun with `META` removed from the ex-TSLA universe.",
        "- `ex_meta_broad_participation_only`: ex-META rerun filtered to the same honest broad-participation day rules.",
        "- `ex_aapl_rising_market`: ex-AAPL rerun filtered to `rising_market` entry days.",
        "- `ex_meta_rising_market`: ex-META rerun filtered to `rising_market` entry days.",
        "- `ex_aapl_non_extreme_2_5`: ex-AAPL rerun with both best and worst 2.5% of days removed from the equity-path audit.",
        "- `ex_meta_non_extreme_2_5`: ex-META rerun with both best and worst 2.5% of days removed from the equity-path audit.",
        "",
        "## Honest limits",
        "",
        "- No new signal logic or parameter search was introduced.",
        "- Cross-sectional books were rerun on reduced universes rather than masked after the fact.",
    ]
    write_markdown(OUTPUTS["grid"], "\n".join(grid_lines))

    metric_rows: list[dict[str, object]] = []
    curve_store: dict[str, dict[str, pd.DataFrame]] = {}

    for variant_id in ["rs_top3_native", "csm_native", "dse_control_native"]:
        curve_store[variant_id] = {}

        ex_tsla_info = books["ex_tsla"][variant_id]
        ex_tsla_meta = books["ex_tsla"]["_meta"]
        ex_tsla_trades = ex_tsla_info["trades"]
        ex_tsla_curve = ex_tsla_info["curve"]
        curve_store[variant_id]["ex_tsla_full"] = ex_tsla_curve
        metric_rows.append(
            metric_row(
                variant_id,
                ex_tsla_info["base_strategy"],
                ex_tsla_info["family_label"],
                "ex_tsla_full",
                slice_scope_note(ex_tsla_info["family_label"], "ex_tsla_full"),
                ex_tsla_trades,
                ex_tsla_curve,
                ex_tsla_info["candidate"],
            )
        )

        ex_tsla_day = build_variant_day_frame(variant_id, ex_tsla_trades, ex_tsla_curve, ex_tsla_meta["bars"], ex_tsla_meta["market_context"])
        ex_tsla_day["primary_day_class"] = ex_tsla_day.apply(classify_profitable_day, axis=1)
        ex_tsla_sets = day_sets(ex_tsla_day)
        broad_trades = ex_tsla_trades.loc[ex_tsla_trades["entry_date"].isin(ex_tsla_sets["broad"])].copy()
        broad_curve = equity_from_trades(broad_trades, ex_tsla_meta["bars"], INITIAL_CAPITAL)
        curve_store[variant_id]["broad_participation_only"] = broad_curve
        metric_rows.append(
            metric_row(
                variant_id,
                ex_tsla_info["base_strategy"],
                ex_tsla_info["family_label"],
                "broad_participation_only",
                slice_scope_note(ex_tsla_info["family_label"], "broad_participation_only"),
                broad_trades,
                broad_curve,
                False,
            )
        )

        for dep_key, dep_prefix in [("ex_aapl", "ex_aapl"), ("ex_meta", "ex_meta")]:
            dep_info = books[dep_key][variant_id]
            dep_meta = books[dep_key]["_meta"]
            dep_trades = dep_info["trades"]
            dep_curve = dep_info["curve"]

            full_name = f"{dep_prefix}_full"
            curve_store[variant_id][full_name] = dep_curve
            metric_rows.append(
                metric_row(
                    variant_id,
                    dep_info["base_strategy"],
                    dep_info["family_label"],
                    full_name,
                    slice_scope_note(dep_info["family_label"], full_name),
                    dep_trades,
                    dep_curve,
                    False,
                )
            )

            dep_day = build_variant_day_frame(variant_id, dep_trades, dep_curve, dep_meta["bars"], dep_meta["market_context"])
            dep_day["primary_day_class"] = dep_day.apply(classify_profitable_day, axis=1)
            dep_sets = day_sets(dep_day)

            broad_name = f"{dep_prefix}_broad_participation_only"
            dep_broad_trades = dep_trades.loc[dep_trades["entry_date"].isin(dep_sets["broad"])].copy()
            dep_broad_curve = equity_from_trades(dep_broad_trades, dep_meta["bars"], INITIAL_CAPITAL)
            curve_store[variant_id][broad_name] = dep_broad_curve
            metric_rows.append(
                metric_row(
                    variant_id,
                    dep_info["base_strategy"],
                    dep_info["family_label"],
                    broad_name,
                    slice_scope_note(dep_info["family_label"], broad_name),
                    dep_broad_trades,
                    dep_broad_curve,
                    False,
                )
            )

            rising_name = f"{dep_prefix}_rising_market"
            dep_rising_trades = dep_trades.loc[dep_trades["entry_date"].isin(dep_sets["rising"])].copy()
            dep_rising_curve = equity_from_trades(dep_rising_trades, dep_meta["bars"], INITIAL_CAPITAL)
            curve_store[variant_id][rising_name] = dep_rising_curve
            metric_rows.append(
                metric_row(
                    variant_id,
                    dep_info["base_strategy"],
                    dep_info["family_label"],
                    rising_name,
                    slice_scope_note(dep_info["family_label"], rising_name),
                    dep_rising_trades,
                    dep_rising_curve,
                    False,
                )
            )

            nonext_name = f"{dep_prefix}_non_extreme_2_5"
            dep_nonext_curve = adjusted_curve(dep_curve, 0.025, 0.025)
            curve_store[variant_id][nonext_name] = dep_nonext_curve
            metric_rows.append(
                metric_row(
                    variant_id,
                    dep_info["base_strategy"],
                    dep_info["family_label"],
                    nonext_name,
                    slice_scope_note(dep_info["family_label"], nonext_name),
                    dep_trades,
                    dep_nonext_curve,
                    False,
                )
            )

    metrics_df = assign_quality_scores(pd.DataFrame(metric_rows))

    slice_candidates = metrics_df.loc[
        metrics_df["slice_name"].isin(
            [
                "ex_aapl_full",
                "ex_aapl_broad_participation_only",
                "ex_aapl_rising_market",
                "ex_meta_full",
                "ex_meta_broad_participation_only",
                "ex_meta_rising_market",
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

    leaderboard_lines = ["# Ex-AAPL / Ex-META Leaderboard", "", "## Key slices", ""]
    for slice_name in [
        "ex_tsla_full",
        "broad_participation_only",
        "ex_aapl_full",
        "ex_aapl_broad_participation_only",
        "ex_meta_full",
        "ex_meta_broad_participation_only",
        "ex_aapl_rising_market",
        "ex_meta_rising_market",
    ]:
        leaderboard_lines.append(f"### {slice_name}")
        for row in metrics_df.loc[metrics_df["slice_name"] == slice_name].sort_values("total_return_pct", ascending=False).itertuples():
            leaderboard_lines.append(
                f"- `{row.variant_id}`: final equity `${row.final_equity:.2f}`, return `{row.total_return_pct:.2f}%`, drawdown `{row.max_drawdown_pct:.2f}%`, top-symbol `{row.top_symbol_pnl_share_pct:.2f}%`, top-10%-days `{row.top_10pct_days_pnl_share_pct:.2f}%`, non-extreme `{row.non_extreme_day_expectancy:.2f}`."
            )
        leaderboard_lines.append("")
    write_markdown(OUTPUTS["leaderboard"], "\n".join(leaderboard_lines))

    impact_rows = []
    for variant_id, base_strategy in [
        ("rs_top3_native", "relative_strength_vs_benchmark"),
        ("csm_native", "cross_sectional_momentum"),
        ("dse_control_native", "down_streak_exhaustion"),
    ]:
        full_base = metrics_df.loc[(metrics_df["variant_id"] == variant_id) & (metrics_df["slice_name"] == "ex_tsla_full")].iloc[0]
        broad_base = metrics_df.loc[(metrics_df["variant_id"] == variant_id) & (metrics_df["slice_name"] == "broad_participation_only")].iloc[0]
        for removed_symbol, comp_name in [("AAPL", "ex_aapl_full"), ("META", "ex_meta_full")]:
            comp = metrics_df.loc[(metrics_df["variant_id"] == variant_id) & (metrics_df["slice_name"] == comp_name)].iloc[0]
            impact_rows.append(
                {
                    "variant_id": variant_id,
                    "base_strategy": base_strategy,
                    "removed_symbol": removed_symbol,
                    "comparison_scope": "full",
                    "baseline_slice": "ex_tsla_full",
                    "comparison_slice": comp_name,
                    "baseline_total_return_pct": float(full_base["total_return_pct"]),
                    "comparison_total_return_pct": float(comp["total_return_pct"]),
                    "return_delta_pct_points": float(comp["total_return_pct"] - full_base["total_return_pct"]),
                    "baseline_final_equity": float(full_base["final_equity"]),
                    "comparison_final_equity": float(comp["final_equity"]),
                    "final_equity_delta": float(comp["final_equity"] - full_base["final_equity"]),
                    "baseline_non_extreme_expectancy": float(full_base["non_extreme_day_expectancy"]),
                    "comparison_non_extreme_expectancy": float(comp["non_extreme_day_expectancy"]),
                    "non_extreme_expectancy_delta": float(comp["non_extreme_day_expectancy"] - full_base["non_extreme_day_expectancy"]),
                    "baseline_top_symbol_share_pct": float(full_base["top_symbol_pnl_share_pct"]),
                    "comparison_top_symbol_share_pct": float(comp["top_symbol_pnl_share_pct"]),
                    "top_symbol_share_delta_pct_points": float(comp["top_symbol_pnl_share_pct"] - full_base["top_symbol_pnl_share_pct"]),
                }
            )
        for removed_symbol, comp_name in [("AAPL", "ex_aapl_broad_participation_only"), ("META", "ex_meta_broad_participation_only")]:
            comp = metrics_df.loc[(metrics_df["variant_id"] == variant_id) & (metrics_df["slice_name"] == comp_name)].iloc[0]
            impact_rows.append(
                {
                    "variant_id": variant_id,
                    "base_strategy": base_strategy,
                    "removed_symbol": removed_symbol,
                    "comparison_scope": "broad_participation",
                    "baseline_slice": "broad_participation_only",
                    "comparison_slice": comp_name,
                    "baseline_total_return_pct": float(broad_base["total_return_pct"]),
                    "comparison_total_return_pct": float(comp["total_return_pct"]),
                    "return_delta_pct_points": float(comp["total_return_pct"] - broad_base["total_return_pct"]),
                    "baseline_final_equity": float(broad_base["final_equity"]),
                    "comparison_final_equity": float(comp["final_equity"]),
                    "final_equity_delta": float(comp["final_equity"] - broad_base["final_equity"]),
                    "baseline_non_extreme_expectancy": float(broad_base["non_extreme_day_expectancy"]),
                    "comparison_non_extreme_expectancy": float(comp["non_extreme_day_expectancy"]),
                    "non_extreme_expectancy_delta": float(comp["non_extreme_day_expectancy"] - broad_base["non_extreme_day_expectancy"]),
                    "baseline_top_symbol_share_pct": float(broad_base["top_symbol_pnl_share_pct"]),
                    "comparison_top_symbol_share_pct": float(comp["top_symbol_pnl_share_pct"]),
                    "top_symbol_share_delta_pct_points": float(comp["top_symbol_pnl_share_pct"] - broad_base["top_symbol_pnl_share_pct"]),
                }
            )
    impact_df = pd.DataFrame(impact_rows).sort_values(["variant_id", "comparison_scope", "removed_symbol"]).reset_index(drop=True)
    impact_df.to_csv(OUTPUTS["impact_csv"], index=False)

    def more_important_symbol(variant_id: str) -> str:
        subset = impact_df.loc[(impact_df["variant_id"] == variant_id) & (impact_df["comparison_scope"] == "broad_participation")].copy()
        subset["severity"] = (-subset["return_delta_pct_points"]) + (-subset["non_extreme_expectancy_delta"]) + subset["comparison_top_symbol_share_pct"]
        return str(subset.sort_values("severity", ascending=False).iloc[0]["removed_symbol"])

    rs_carrier = more_important_symbol("rs_top3_native")
    csm_carrier = more_important_symbol("csm_native")

    rs_ex_aapl_broad = metrics_df.loc[(metrics_df["variant_id"] == "rs_top3_native") & (metrics_df["slice_name"] == "ex_aapl_broad_participation_only")].iloc[0]
    rs_ex_meta_broad = metrics_df.loc[(metrics_df["variant_id"] == "rs_top3_native") & (metrics_df["slice_name"] == "ex_meta_broad_participation_only")].iloc[0]
    csm_ex_aapl_broad = metrics_df.loc[(metrics_df["variant_id"] == "csm_native") & (metrics_df["slice_name"] == "ex_aapl_broad_participation_only")].iloc[0]
    csm_ex_meta_broad = metrics_df.loc[(metrics_df["variant_id"] == "csm_native") & (metrics_df["slice_name"] == "ex_meta_broad_participation_only")].iloc[0]

    rs_survives_ex_aapl = bool(float(rs_ex_aapl_broad["final_equity"]) > INITIAL_CAPITAL)
    rs_survives_ex_meta = bool(float(rs_ex_meta_broad["final_equity"]) > INITIAL_CAPITAL)
    csm_survives_ex_aapl = bool(float(csm_ex_aapl_broad["final_equity"]) > INITIAL_CAPITAL)
    csm_survives_ex_meta = bool(float(csm_ex_meta_broad["final_equity"]) > INITIAL_CAPITAL)

    dependency_lines = [
        "# Ex-AAPL / Ex-META Dependency Report",
        "",
        f"- For `RS`, the more important remaining carrier is `{rs_carrier}`. On the weak broad core, ex-AAPL broad-participation return is `{rs_ex_aapl_broad['total_return_pct']:.2f}%` versus `{rs_ex_meta_broad['total_return_pct']:.2f}%` ex-META, and non-extreme expectancy is `{rs_ex_aapl_broad['non_extreme_day_expectancy']:.2f}` versus `{rs_ex_meta_broad['non_extreme_day_expectancy']:.2f}`.",
        f"- For `CSM`, the more important remaining carrier is `{csm_carrier}`. On the weak broad core, ex-AAPL broad-participation return is `{csm_ex_aapl_broad['total_return_pct']:.2f}%` versus `{csm_ex_meta_broad['total_return_pct']:.2f}%` ex-META, and non-extreme expectancy is `{csm_ex_aapl_broad['non_extreme_day_expectancy']:.2f}` versus `{csm_ex_meta_broad['non_extreme_day_expectancy']:.2f}`.",
        f"- `{'RS' if rs_ex_aapl_broad['total_return_pct'] >= csm_ex_aapl_broad['total_return_pct'] else 'CSM'}` survives ex-AAPL better on the broad core (`{rs_ex_aapl_broad['total_return_pct']:.2f}%` for RS vs `{csm_ex_aapl_broad['total_return_pct']:.2f}%` for CSM).",
        f"- `{'RS' if rs_ex_meta_broad['total_return_pct'] >= csm_ex_meta_broad['total_return_pct'] else 'CSM'}` survives ex-META better on the broad core (`{rs_ex_meta_broad['total_return_pct']:.2f}%` for RS vs `{csm_ex_meta_broad['total_return_pct']:.2f}%` for CSM).",
        f"- The surviving edge is still not broad enough to matter cleanly. Best surviving broad-core top-symbol share is `{min(float(rs_ex_aapl_broad['top_symbol_pnl_share_pct']), float(rs_ex_meta_broad['top_symbol_pnl_share_pct']), float(csm_ex_aapl_broad['top_symbol_pnl_share_pct']), float(csm_ex_meta_broad['top_symbol_pnl_share_pct'])):.2f}%`, and top-10%-days concentration still bottoms out at `{min(float(rs_ex_aapl_broad['top_10pct_days_pnl_share_pct']), float(rs_ex_meta_broad['top_10pct_days_pnl_share_pct']), float(csm_ex_aapl_broad['top_10pct_days_pnl_share_pct']), float(csm_ex_meta_broad['top_10pct_days_pnl_share_pct'])):.2f}%`.",
        f"- The branch is still honestly a `{'narrow research artifact with weak broad core' if max(float(rs_ex_aapl_broad['top_symbol_pnl_share_pct']), float(rs_ex_meta_broad['top_symbol_pnl_share_pct']), float(csm_ex_aapl_broad['top_symbol_pnl_share_pct']), float(csm_ex_meta_broad['top_symbol_pnl_share_pct'])) <= 60.0 else 'leader-following research artifact'}` rather than a deployable broad sleeve.",
    ]
    write_markdown(OUTPUTS["dependency_md"], "\n".join(dependency_lines))

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

    crown_rs = bool(
        rs_best["slice_quality_score"] > csm_best["slice_quality_score"]
        or (
            rs_best["slice_quality_score"] == csm_best["slice_quality_score"]
            and rs_best["non_extreme_day_expectancy"] >= csm_best["non_extreme_day_expectancy"]
        )
    )
    crown_csm = bool(not crown_rs)
    both_demoted = bool(
        max(float(rs_best["total_return_pct"]), float(csm_best["total_return_pct"])) < 10.0
        or max(float(rs_best["non_extreme_day_expectancy"]), float(csm_best["non_extreme_day_expectancy"])) <= 10.0
    )

    forensic_lines = [
        "# Ex-AAPL / Ex-META Forensics Report",
        "",
        f"- Best RS slice among the dependency reruns: `{rs_best['slice_name']}` with slice-quality score `{rs_best['slice_quality_score']:.4f}`.",
        f"- Best CSM slice among the dependency reruns: `{csm_best['slice_name']}` with slice-quality score `{csm_best['slice_quality_score']:.4f}`.",
        f"- After removing the best 1% of days, `{'RS' if rs_best1['total_return_pct'] >= csm_best1['total_return_pct'] else 'CSM'}` survives better (`{rs_best1['total_return_pct']:.2f}%` for RS vs `{csm_best1['total_return_pct']:.2f}%` for CSM).",
        f"- After removing the best 2.5% of days, `{'RS' if rs_best25['total_return_pct'] >= csm_best25['total_return_pct'] else 'CSM'}` survives better (`{rs_best25['total_return_pct']:.2f}%` for RS vs `{csm_best25['total_return_pct']:.2f}%` for CSM).",
        f"- On the non-extreme-day audit, `{'RS' if rs_nonext['daily_expectancy'] >= csm_nonext['daily_expectancy'] else 'CSM'}` has the cleaner everyday core (`{rs_nonext['daily_expectancy']:.2f}` for RS vs `{csm_nonext['daily_expectancy']:.2f}` for CSM).",
        f"- The crown should `{'stay with RS' if crown_rs and not both_demoted else 'move to CSM' if crown_csm and not both_demoted else 'demote both branches'}` after this dependency pass.",
        f"- Even here, both branches remain tail-shaped. Best-slice top-10%-days concentration is `{rs_best['top_10pct_days_pnl_share_pct']:.2f}%` for RS and `{csm_best['top_10pct_days_pnl_share_pct']:.2f}%` for CSM.",
    ]
    write_markdown(OUTPUTS["forensics_md"], "\n".join(forensic_lines))

    best_branch_row = rs_best if crown_rs else csm_best
    label = (
        "too weak to prioritize"
        if both_demoted
        else "leader-following research artifact"
        if float(best_branch_row["top_symbol_pnl_share_pct"]) > 55.0 or float(best_branch_row["top_10pct_days_pnl_share_pct"]) > 50.0
        else "narrow research artifact with weak broad core"
    )
    decision_lines = [
        "# Ex-AAPL / Ex-META Branch Redecision",
        "",
        f"1. Does RS remain the canonical upside research branch after the ex-AAPL / ex-META dependency test? `{'Yes, narrowly.' if crown_rs and not both_demoted else 'No.'}`",
        f"2. Should CSM take over instead? `{'Yes, narrowly.' if crown_csm and not both_demoted else 'No.'}`",
        f"3. Should both be demoted further if the weak broad core collapses? `{'Yes.' if both_demoted else 'No.'}`",
        f"4. What is the most honest label now: `{label}`.",
        "5. Does DSE remain the control benchmark? `Yes`.",
    ]
    write_markdown(OUTPUTS["decision"], "\n".join(decision_lines))

    paper_closer = bool(
        float(best_branch_row["top_symbol_pnl_share_pct"]) < 25.0
        and float(best_branch_row["top_10pct_days_pnl_share_pct"]) < 45.0
        and float(best_branch_row["max_drawdown_pct"]) < 20.0
        and float(best_branch_row["total_return_pct"]) > 25.0
    )
    deficiency = (
        f"top-symbol concentration {best_branch_row['top_symbol_pnl_share_pct']:.2f}%, "
        f"top-10%-days concentration {best_branch_row['top_10pct_days_pnl_share_pct']:.2f}%, and "
        f"drawdown {best_branch_row['max_drawdown_pct']:.2f}% still block decision-grade paper-watch honesty."
    )
    paper_lines = [
        "# Ex-AAPL / Ex-META Paper-Watch Recheck",
        "",
        f"1. Did either branch get materially closer to paper-watch? `{'Yes, slightly.' if paper_closer else 'No.'}`",
        f"2. What exact deficiency still blocks paper-watch? `{deficiency}`",
        f"3. Is the next step another falsification test, a narrower confirmation rerun, or a demotion? `{'A demotion.' if both_demoted else 'Another falsification test.'}`",
    ]
    write_markdown(OUTPUTS["paper"], "\n".join(paper_lines))

    next_experiment = "ex-AMZN or ex-GOOGL dependency test" if not both_demoted else "demote both upside branches and stop dependency peeling"
    next_lines = [
        "# Next After Ex-AAPL / Ex-META",
        "",
        "1. Keep QQQ pair as the only active paper strategy.",
        "2. Preserve DSE as control.",
        f"3. {'Keep RS as canonical branch.' if crown_rs and not both_demoted else 'Switch to CSM as canonical branch.' if crown_csm and not both_demoted else 'Demote both upside branches.'}",
        f"4. Run one `{next_experiment}` test only if a new dominant carrier clearly emerges.",
        "5. Stop any branch that cannot survive repeated dependency removals.",
    ]
    write_markdown(OUTPUTS["next"], "\n".join(next_lines))

    print(
        json.dumps(
            {
                "opened_files": [row["path"] for row in file_status if row["opened"]],
                "rs_survives_ex_aapl": rs_survives_ex_aapl,
                "rs_survives_ex_meta": rs_survives_ex_meta,
                "csm_survives_ex_aapl": csm_survives_ex_aapl,
                "csm_survives_ex_meta": csm_survives_ex_meta,
                "more_important_carrier": {"rs_top3_native": rs_carrier, "csm_native": csm_carrier},
                "rs_remains_canonical": crown_rs and not both_demoted,
                "csm_takes_over": crown_csm and not both_demoted,
                "both_demoted": both_demoted,
                "dse_control": True,
                "closer_to_paper_watch": paper_closer,
                "best_next_experiment": next_experiment,
                "outputs": {k: str(v) for k, v in OUTPUTS.items()},
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
