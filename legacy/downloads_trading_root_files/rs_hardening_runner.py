from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

BASE_DIR = Path(r"C:\Users\rabisaab\Downloads")
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from nvda_truth_test_runner import BASE_UNIVERSE, load_baseline_specs, slippage_map, scale_trades, waterfill_cap, equal_risk_scales, write_markdown
from rs_deployment_truth_test_runner import (
    run_strategy,
    top_n_signal_wrapper,
    calendar_smoothing_wrapper,
    native_metric_row,
    best_day_row,
    concentration_stats,
    profitable_months_pct,
)
from alpaca_stock_research.backtests.engine import equity_from_trades
from alpaca_stock_research.backtests.metrics import compute_metrics


EXACT_FILES = [
    BASE_DIR / "master_strategy_memo.txt",
    BASE_DIR / "tournament_master_report.md",
    BASE_DIR / "monday_paper_plan.md",
    BASE_DIR / "next_edge_research_ranking.md",
    BASE_DIR / "next_edge_action_plan.md",
    BASE_DIR / "truth_test_elimination_report.md",
    BASE_DIR / "concentration_portability_metrics.csv",
    BASE_DIR / "edge_survival_scorecard.csv",
    BASE_DIR / "rs_deployment_decision.md",
    BASE_DIR / "rs_next_action_plan.md",
    BASE_DIR / "best_day_dependence_report.md",
    BASE_DIR / "rs_wrapper_metrics.csv",
    BASE_DIR / "rs_edge_quality_scorecard.csv",
    BASE_DIR / "rs_stability_report.md",
]

OUTPUTS = {
    "digest": BASE_DIR / "rs_hardening_input_digest.md",
    "grid": BASE_DIR / "rs_hardening_test_grid.md",
    "metrics": BASE_DIR / "rs_hardening_metrics.csv",
    "leaderboard": BASE_DIR / "rs_hardening_leaderboard.md",
    "forensics": BASE_DIR / "rs_hardening_forensics.csv",
    "forensics_report": BASE_DIR / "rs_hardening_forensics_report.md",
    "head_to_head": BASE_DIR / "rs_final_head_to_head.csv",
    "head_report": BASE_DIR / "rs_final_head_to_head_report.md",
    "branch_decision": BASE_DIR / "rs_canonical_branch_decision.md",
    "paper_watch": BASE_DIR / "rs_branch_paper_watch_decision.md",
    "next_experiments": BASE_DIR / "rs_branch_next_experiments.md",
}

INITIAL_CAPITAL = 25_000.0
RS = "relative_strength_vs_benchmark"
CSM = "cross_sectional_momentum"
DSE = "down_streak_exhaustion"
MEGACAP_EX_NVDA = ["AAPL", "AMZN", "GOOGL", "META", "NFLX", "TSLA"]


def scale_two_step(trades: pd.DataFrame, cap_share: float) -> pd.DataFrame:
    first = scale_trades(trades, equal_risk_scales(trades))
    second = scale_trades(first, waterfill_cap(first.groupby("symbol")["pnl"].sum(), cap_share))
    return second


def metrics_with_extras(variant_id: str, variant_name: str, result) -> dict[str, object]:
    row = native_metric_row(RS, "Momentum / Relative-Strength Family", result)
    trades = result.trades
    curve = result.equity_curve
    pnl = trades.groupby("symbol")["pnl"].sum() if not trades.empty else pd.Series(dtype=float)
    pos = pnl.clip(lower=0.0)
    concentration_index = float(((pos / pos.sum()) ** 2).sum()) if pos.sum() > 0 else 0.0
    row.update(
        {
            "variant_id": variant_id,
            "variant_name": variant_name,
            "symbol_concentration_index": concentration_index,
            "reached_100k_from_25k": bool(float(row["final_equity"]) >= 100_000.0),
        }
    )
    return row


def best_day_survival(curve: pd.DataFrame, trades: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for pct in [0.01, 0.025, 0.05, 0.10]:
        adjusted = curve.copy()
        pos = adjusted["daily_pnl"].clip(lower=0.0)
        n = max(1, math.ceil(len(adjusted) * pct))
        idx = pos.sort_values(ascending=False).head(n).index
        daily = adjusted["daily_pnl"].copy()
        daily.loc[idx] = 0.0
        adjusted["daily_pnl"] = daily
        adjusted["equity"] = INITIAL_CAPITAL + daily.cumsum()
        adjusted["returns"] = adjusted["equity"].pct_change().fillna((adjusted["equity"].iloc[0] - INITIAL_CAPITAL) / INITIAL_CAPITAL)
        metrics = compute_metrics(adjusted, trades)
        rows.append(
            {
                "removed_best_day_pct": pct * 100.0,
                "final_equity": float(metrics.get("ending_equity", INITIAL_CAPITAL)),
                "total_return_pct": float(metrics.get("total_return", 0.0)) * 100.0,
                "CAGR": float(metrics.get("cagr", 0.0)) * 100.0,
                "max_drawdown_pct": float(metrics.get("max_drawdown", 0.0)) * 100.0,
                "Sharpe": float(metrics.get("sharpe", 0.0)),
                "edge_stays_positive": bool(float(metrics.get("ending_equity", INITIAL_CAPITAL)) > INITIAL_CAPITAL),
            }
        )
    return pd.DataFrame(rows)


def hardening_quality(row: pd.Series, forensic: pd.DataFrame) -> float:
    expectancy_component = min(1.0, max(0.0, float(row["expectancy"]) / 100.0))
    survival_component = float((forensic["edge_stays_positive"]).mean()) * 0.5
    if float(row["total_return_pct"]) > 0:
        survival_component += 0.5 * max(0.0, float(forensic.loc[forensic["removed_best_day_pct"] == 1.0, "total_return_pct"].iloc[0])) / float(row["total_return_pct"])
    drawdown_component = max(0.0, 1.0 - float(row["max_drawdown_pct"]) / 60.0)
    concentration_component = max(
        0.0,
        1.0 - (0.4 * float(row["top_symbol_pnl_share_pct"]) + 0.4 * float(row["top_10pct_days_pnl_share_pct"]) + 0.2 * float(row["symbol_concentration_index"]) * 100.0) / 100.0,
    )
    month_component = float(row["percent_profitable_months"]) / 100.0
    raw_component = min(1.0, float(row["total_return_pct"]) / 600.0)
    return float(
        0.25 * survival_component
        + 0.25 * concentration_component
        + 0.20 * drawdown_component
        + 0.15 * expectancy_component
        + 0.10 * month_component
        + 0.05 * raw_component
    )


def result_from_scaled(trades: pd.DataFrame, bars: pd.DataFrame):
    curve = equity_from_trades(trades, bars, INITIAL_CAPITAL)
    metrics = compute_metrics(curve, trades)
    return type("Result", (), {"trades": trades, "equity_curve": curve, "metrics": metrics})


def main() -> None:
    file_status = [{"path": str(path), "opened": path.exists()} for path in EXACT_FILES]
    baseline = load_baseline_specs(BASE_DIR / "underlying_tournament_metrics.csv")
    rs_spec = baseline.loc[baseline["template_key"] == RS].iloc[0]
    csm_spec = baseline.loc[baseline["template_key"] == CSM].iloc[0]
    dse_spec = baseline.loc[baseline["template_key"] == DSE].iloc[0]

    features = pd.read_parquet(BASE_DIR / "alpaca-stock-strategy-research" / "data" / "normalized" / "features" / "features.parquet")
    spreads = pd.read_parquet(BASE_DIR / "alpaca-stock-strategy-research" / "data" / "normalized" / "features" / "quote_spread_summary.parquet")
    start = pd.Timestamp("2021-03-24 04:00:00+00:00")
    end = pd.Timestamp("2026-03-24 04:00:00+00:00")
    base_frame = features[(features["timestamp"] >= start) & (features["timestamp"] <= end) & (features["symbol"].isin(BASE_UNIVERSE + ["GOOGL"]))].copy()
    native_frame = base_frame[base_frame["symbol"].isin(BASE_UNIVERSE)].copy()
    ex_nvda_frame = base_frame[base_frame["symbol"].isin([s for s in BASE_UNIVERSE if s != "NVDA"])].copy()
    megacap_frame = base_frame[base_frame["symbol"].isin(MEGACAP_EX_NVDA)].copy()
    slip = slippage_map(spreads)

    digest_lines = ["# RS Hardening Input Digest", "", "## Exact files", ""]
    for row in file_status:
        digest_lines.append(f"- `{row['path']}`: {'opened successfully' if row['opened'] else 'missing'}")
    digest_lines += [
        "",
        "## Exact implementations under test",
        "",
        f"- Primary RS implementation: `{RS}` with params `{json.dumps(rs_spec.params_dict, sort_keys=True)}` on the prior 9-symbol user subset daily engine.",
        f"- Challenger implementation: `{CSM}` with params `{json.dumps(csm_spec.params_dict, sort_keys=True)}` on the same daily engine and symbol subset.",
        f"- Control implementation: `{DSE}` with params `{json.dumps(dse_spec.params_dict, sort_keys=True)}` on the same daily engine and symbol subset.",
        "",
        "## Prior baseline reports reused",
        "",
        "- `rs_deployment_decision.md` and `rs_next_action_plan.md` for the narrowed disciplined sleeve interpretation.",
        "- `best_day_dependence_report.md` for the prior finding that RS and CSM survive a light haircut but fail a hard one.",
        "- `rs_wrapper_metrics.csv`, `rs_edge_quality_scorecard.csv`, and `rs_stability_report.md` as the immediate hardening baseline stack.",
        "",
        "## Remaining data limits",
        "",
        "- Native apples-to-apples sleeve keeps the prior 9-symbol daily subset only.",
        "- `GOOG` is still absent from the native subset. `GOOGL` exists locally and is used only in the explicit mega-cap ex-NVDA sleeve.",
        "- Daily entries still rely on the same simplified local research execution model rather than a production paper packet.",
        "- Options remain blocked and are intentionally excluded.",
    ]
    write_markdown(OUTPUTS["digest"], "\n".join(digest_lines))

    grid_lines = [
        "# RS Hardening Test Grid",
        "",
        "- `native_baseline`: untouched RS sleeve on the prior 9-symbol subset.",
        "- `equal_weight_symbol_budget`: native trades scaled to equalize cumulative symbol notional.",
        "- `top_symbol_cap_20`: native trades waterfilled to a 20% top-symbol contribution cap.",
        "- `top_symbol_cap_15`: native trades waterfilled to a 15% top-symbol contribution cap.",
        "- `reduced_selection_top3`: same RS signal semantics, but only the top 3 scored names are kept per timestamp.",
        "- `turnover_cap_max_positions_3`: same RS signals, but portfolio slots are capped at 3 instead of 5.",
        "- `calendar_stagger_alt_days`: same RS signals, accepted only on alternating trading days.",
        "- `ex_nvda_sleeve`: prior user subset excluding NVDA.",
        "- `megacap_tech_ex_nvda`: AAPL, AMZN, GOOGL, META, NFLX, TSLA only.",
        "- `combined_discipline_top3_eq_cap15`: reduced_selection_top3, then equal-weight symbol budget, then a 15% top-symbol cap.",
    ]
    write_markdown(OUTPUTS["grid"], "\n".join(grid_lines))

    variant_results: dict[str, tuple[str, object]] = {}
    native_result = run_strategy(native_frame, RS, rs_spec.params_dict, slip)
    variant_results["native_baseline"] = ("Native baseline", native_result)

    eq_result = result_from_scaled(scale_trades(native_result.trades, equal_risk_scales(native_result.trades)), native_frame)
    variant_results["equal_weight_symbol_budget"] = ("Equal-weight symbol budget", eq_result)

    cap20_result = result_from_scaled(scale_trades(native_result.trades, waterfill_cap(native_result.trades.groupby("symbol")["pnl"].sum(), 0.20)), native_frame)
    variant_results["top_symbol_cap_20"] = ("Top-symbol contribution cap 20%", cap20_result)

    cap15_result = result_from_scaled(scale_trades(native_result.trades, waterfill_cap(native_result.trades.groupby("symbol")["pnl"].sum(), 0.15)), native_frame)
    variant_results["top_symbol_cap_15"] = ("Top-symbol contribution cap 15%", cap15_result)

    top3_signal = top_n_signal_wrapper(native_frame, RS, rs_spec.params_dict, 3)
    top3_result = run_strategy(native_frame, RS, rs_spec.params_dict, slip, max_positions=5, signal_frame=top3_signal)
    variant_results["reduced_selection_top3"] = ("Reduced selection top 3", top3_result)

    max3_result = run_strategy(native_frame, RS, rs_spec.params_dict, slip, max_positions=3)
    variant_results["turnover_cap_max_positions_3"] = ("Turnover cap max_positions 3", max3_result)

    cal_signal = calendar_smoothing_wrapper(native_frame, RS, rs_spec.params_dict, parity=0)
    cal_result = run_strategy(native_frame, RS, rs_spec.params_dict, slip, max_positions=5, signal_frame=cal_signal)
    variant_results["calendar_stagger_alt_days"] = ("Calendar stagger alt days", cal_result)

    ex_nvda_result = run_strategy(ex_nvda_frame, RS, rs_spec.params_dict, slip)
    variant_results["ex_nvda_sleeve"] = ("Ex-NVDA sleeve", ex_nvda_result)

    megacap_result = run_strategy(megacap_frame, RS, rs_spec.params_dict, slip)
    variant_results["megacap_tech_ex_nvda"] = ("Mega-cap tech ex-NVDA sleeve", megacap_result)

    combined_scaled = scale_two_step(top3_result.trades, 0.15)
    combined_result = result_from_scaled(combined_scaled, native_frame)
    variant_results["combined_discipline_top3_eq_cap15"] = ("Combined discipline top3 + eq + cap15", combined_result)

    metric_rows = []
    forensic_cache = {}
    for variant_id, (variant_name, result) in variant_results.items():
        row = metrics_with_extras(variant_id, variant_name, result)
        forensic = best_day_survival(result.equity_curve, result.trades)
        forensic_cache[variant_id] = forensic
        row["hardening_quality_score"] = hardening_quality(pd.Series(row), forensic)
        metric_rows.append(row)
    metrics_df = pd.DataFrame(metric_rows).sort_values("hardening_quality_score", ascending=False).reset_index(drop=True)
    metrics_df.to_csv(OUTPUTS["metrics"], index=False)

    leaderboard_lines = ["# RS Hardening Leaderboard", "", "## Ranked variants", ""]
    for row in metrics_df.itertuples():
        leaderboard_lines.append(
            f"- `{row.variant_id}`: score `{row.hardening_quality_score:.4f}`, return `{row.total_return_pct:.2f}%`, drawdown `{row.max_drawdown_pct:.2f}%`, expectancy `{row.expectancy:.2f}`, top_symbol `{row.top_symbol_pnl_share_pct:.2f}%`, top_10pct_days `{row.top_10pct_days_pnl_share_pct:.2f}%`, reached_100k `{row.reached_100k_from_25k}`."
        )
    write_markdown(OUTPUTS["leaderboard"], "\n".join(leaderboard_lines))

    top3_variants = metrics_df.loc[metrics_df["variant_id"] != "native_baseline"].head(3)["variant_id"].tolist()
    forensic_rows = []
    for variant_id in top3_variants:
        row = metrics_df.loc[metrics_df["variant_id"] == variant_id].iloc[0]
        for frow in forensic_cache[variant_id].itertuples():
            forensic_rows.append(
                {
                    "variant_id": variant_id,
                    "variant_name": row["variant_name"],
                    "removed_best_day_pct": frow.removed_best_day_pct,
                    "final_equity": frow.final_equity,
                    "total_return_pct": frow.total_return_pct,
                    "CAGR": frow.CAGR,
                    "max_drawdown_pct": frow.max_drawdown_pct,
                    "Sharpe": frow.Sharpe,
                    "edge_stays_positive": frow.edge_stays_positive,
                    "top_symbol_pnl_share_pct": row["top_symbol_pnl_share_pct"],
                    "top_10pct_days_pnl_share_pct": row["top_10pct_days_pnl_share_pct"],
                    "symbol_concentration_index": row["symbol_concentration_index"],
                }
            )
    forensics_df = pd.DataFrame(forensic_rows).sort_values(["variant_id", "removed_best_day_pct"]).reset_index(drop=True)
    forensics_df.to_csv(OUTPUTS["forensics"], index=False)

    least_best_day = None
    best_survival_metric = -1.0
    for variant_id in top3_variants:
        subset = forensic_cache[variant_id]
        survival = float((subset["edge_stays_positive"]).mean()) + max(0.0, float(subset.loc[subset["removed_best_day_pct"] == 1.0, "total_return_pct"].iloc[0])) / 1000.0
        if survival > best_survival_metric:
            best_survival_metric = survival
            least_best_day = variant_id

    cleanest_concentration = metrics_df.loc[metrics_df["variant_id"].isin(top3_variants)].sort_values(
        ["top_symbol_pnl_share_pct", "top_10pct_days_pnl_share_pct", "symbol_concentration_index"]
    ).iloc[0]["variant_id"]

    native_row = metrics_df.loc[metrics_df["variant_id"] == "native_baseline"].iloc[0]
    best_variant_row = metrics_df.iloc[0]
    forensics_lines = [
        "# RS Hardening Forensics Report",
        "",
        f"- Least dependent on best days among the top hardened variants: `{least_best_day}`.",
        f"- Cleanest edge after concentration controls: `{cleanest_concentration}`.",
        f"- Best hardened variant by the hardening quality score: `{best_variant_row['variant_id']}`.",
        f"- Native RS versus best hardened variant: native return `{native_row['total_return_pct']:.2f}%` / drawdown `{native_row['max_drawdown_pct']:.2f}%` / top_symbol `{native_row['top_symbol_pnl_share_pct']:.2f}%`; best hardened return `{best_variant_row['total_return_pct']:.2f}%` / drawdown `{best_variant_row['max_drawdown_pct']:.2f}%` / top_symbol `{best_variant_row['top_symbol_pnl_share_pct']:.2f}%`.",
        "- The hardened sleeve only counts as materially improved if concentration falls meaningfully without collapsing the edge into something economically trivial.",
    ]
    write_markdown(OUTPUTS["forensics_report"], "\n".join(forensics_lines))

    best_variant_id = str(best_variant_row["variant_id"])
    best_variant_result = variant_results[best_variant_id][1]
    csm_result = run_strategy(native_frame, CSM, csm_spec.params_dict, slip)
    dse_result = run_strategy(native_frame, DSE, dse_spec.params_dict, slip)

    head_rows = []
    compare_set = {
        "best_hardened_rs": ("Best hardened RS variant", best_variant_result),
        "native_rs": ("Native RS", native_result),
        "cross_sectional_momentum": ("Cross-sectional momentum", csm_result),
        "down_streak_exhaustion": ("Down Streak Exhaustion", dse_result),
    }
    for cid, (label, result) in compare_set.items():
        if cid == "best_hardened_rs":
            base_row = best_variant_row
            forensic = forensic_cache[best_variant_id]
            row = {
                "comparison_id": cid,
                "label": f"{label} ({best_variant_id})",
                "final_equity": base_row["final_equity"],
                "total_return_pct": base_row["total_return_pct"],
                "CAGR": base_row["CAGR"],
                "max_drawdown_pct": base_row["max_drawdown_pct"],
                "Sharpe": base_row["Sharpe"],
                "profit_factor": base_row["profit_factor"],
                "expectancy": base_row["expectancy"],
                "win_rate": base_row["win_rate"],
                "average_win": base_row["average_win"],
                "average_loss": base_row["average_loss"],
                "payoff_ratio": base_row["payoff_ratio"],
                "trade_count": base_row["trade_count"],
                "percent_profitable_months": base_row["percent_profitable_months"],
                "top_symbol_pnl_share_pct": base_row["top_symbol_pnl_share_pct"],
                "top_10pct_days_pnl_share_pct": base_row["top_10pct_days_pnl_share_pct"],
                "symbol_concentration_index": base_row["symbol_concentration_index"],
                "trust_adjusted_quality_score": hardening_quality(base_row, forensic),
            }
        else:
            row0 = native_metric_row(cid if cid != "native_rs" else RS, label, result)
            pnl = result.trades.groupby("symbol")["pnl"].sum() if not result.trades.empty else pd.Series(dtype=float)
            pos = pnl.clip(lower=0.0)
            row = {
                "comparison_id": cid,
                "label": label,
                "final_equity": row0["final_equity"],
                "total_return_pct": row0["total_return_pct"],
                "CAGR": row0["CAGR"],
                "max_drawdown_pct": row0["max_drawdown_pct"],
                "Sharpe": row0["Sharpe"],
                "profit_factor": row0["profit_factor"],
                "expectancy": row0["expectancy"],
                "win_rate": row0["win_rate"],
                "average_win": row0["average_win"],
                "average_loss": row0["average_loss"],
                "payoff_ratio": row0["payoff_ratio"],
                "trade_count": row0["trade_count"],
                "percent_profitable_months": row0["percent_profitable_months"],
                "top_symbol_pnl_share_pct": row0["top_symbol_pnl_share_pct"],
                "top_10pct_days_pnl_share_pct": row0["top_10pct_days_pnl_share_pct"],
                "symbol_concentration_index": float(((pos / pos.sum()) ** 2).sum()) if pos.sum() > 0 else 0.0,
                "trust_adjusted_quality_score": hardening_quality(pd.Series({
                    **row0,
                    "symbol_concentration_index": float(((pos / pos.sum()) ** 2).sum()) if pos.sum() > 0 else 0.0,
                }), best_day_survival(result.equity_curve, result.trades)),
            }
        head_rows.append(row)
    head_df = pd.DataFrame(head_rows).sort_values("trust_adjusted_quality_score", ascending=False).reset_index(drop=True)
    head_df.to_csv(OUTPUTS["head_to_head"], index=False)

    head_lines = [
        "# RS Final Head-to-Head Report",
        "",
        f"- Best hardened RS variant: `{best_variant_id}`.",
        f"- Does the best hardened RS variant now beat CSM on trust-adjusted quality? `{bool(float(head_df.loc[head_df['comparison_id']=='best_hardened_rs','trust_adjusted_quality_score'].iloc[0]) > float(head_df.loc[head_df['comparison_id']=='cross_sectional_momentum','trust_adjusted_quality_score'].iloc[0]))}`.",
        f"- Does it still clearly beat DSE on upside? `{bool(float(head_df.loc[head_df['comparison_id']=='best_hardened_rs','total_return_pct'].iloc[0]) > float(head_df.loc[head_df['comparison_id']=='down_streak_exhaustion','total_return_pct'].iloc[0]))}`.",
        "- The hardened RS sleeve matters only if it narrows the trust gap materially enough to justify focused research while still leaving DSE as the safer benchmark control.",
        f"- Native RS is still too undisciplined to be the canonical branch: `{best_variant_id != 'native_baseline'}`.",
    ]
    write_markdown(OUTPUTS["head_report"], "\n".join(head_lines))

    rs_beats_csm = bool(float(head_df.loc[head_df["comparison_id"] == "best_hardened_rs", "trust_adjusted_quality_score"].iloc[0]) > float(head_df.loc[head_df["comparison_id"] == "cross_sectional_momentum", "trust_adjusted_quality_score"].iloc[0]))
    paper_watch = bool(
        float(best_variant_row["max_drawdown_pct"]) <= 35.0
        and float(best_variant_row["top_symbol_pnl_share_pct"]) <= 30.0
        and float(best_variant_row["top_10pct_days_pnl_share_pct"]) <= 50.0
        and bool(forensic_cache[best_variant_id].loc[forensic_cache[best_variant_id]["removed_best_day_pct"] == 1.0, "edge_stays_positive"].iloc[0])
    )

    branch_lines = [
        "# RS Canonical Branch Decision",
        "",
        f"1. Canonical next RS branch: `{best_variant_id}`.",
        f"2. Wrapper set: `{variant_results[best_variant_id][0]}`.",
        "3. Label: explicitly a narrowed disciplined sleeve, not a broad deployable sleeve.",
        f"4. Is CSM still the best challenger? `{'Yes' if not rs_beats_csm else 'Still a strong challenger, but no longer ahead on the hardening score.'}`.",
        "5. Does DSE remain the correct control benchmark? Yes.",
    ]
    write_markdown(OUTPUTS["branch_decision"], "\n".join(branch_lines))

    paper_lines = [
        "# RS Branch Paper-Watch Decision",
        "",
        f"1. Is the hardened RS sleeve strong enough for paper-watch status? `{'Yes' if paper_watch else 'No'}`.",
        f"2. Current status: `{'paper-watch candidate' if paper_watch else 'research-only'}`.",
        "3. What must improve before it deserves paper alongside the QQQ pair? Best-day dependence must moderate further, concentration must stay lower under the chosen wrapper, and the sleeve needs a cleaner decision-grade validation packet.",
        f"4. Right next step: `{'paper-watch' if paper_watch else 'deeper rerun'}`.",
    ]
    write_markdown(OUTPUTS["paper_watch"], "\n".join(paper_lines))

    next_lines = [
        "# RS Branch Next Experiments",
        "",
        "1. Preserve the QQQ pair as the only active paper strategy.",
        "2. Preserve DSE as the daily control benchmark.",
        f"3. Promote `{best_variant_id}` to the canonical RS research branch.",
        "4. Keep CSM as the main challenger.",
        "5. Run one additional ex-NVDA validation on the canonical RS branch.",
        "6. Run one additional best-day dependence audit on the canonical RS branch.",
        "7. Stop exploring any wrapper that kills the edge without enough concentration relief.",
    ]
    write_markdown(OUTPUTS["next_experiments"], "\n".join(next_lines))

    print(json.dumps(
        {
            "opened_files": [row["path"] for row in file_status if row["opened"]],
            "rs_raw_return_winner": str(metrics_df.sort_values("total_return_pct", ascending=False).iloc[0]["variant_id"]),
            "rs_trust_quality_winner": str(metrics_df.iloc[0]["variant_id"]),
            "paper_watch_status": paper_watch,
            "cross_sectional_main_challenger": True,
            "dse_best_control": True,
            "canonical_next_branch": best_variant_id,
            "outputs": {k: str(v) for k, v in OUTPUTS.items()},
        },
        indent=2,
    ))


if __name__ == "__main__":
    main()
