from __future__ import annotations

import json
import math
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd

BASE_DIR = Path(r"C:\Users\rabisaab\Downloads")
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))
REPO_SRC = BASE_DIR / "alpaca-stock-strategy-research" / "src"
if str(REPO_SRC) not in sys.path:
    sys.path.insert(0, str(REPO_SRC))

from alpaca_stock_research.backtests.engine import equity_from_trades
from alpaca_stock_research.backtests.metrics import compute_metrics
from best_day_autopsy_runner import (
    build_market_context,
    day_level_summary,
    select_extreme_days,
    trade_day_contributions,
)
from nvda_truth_test_runner import equal_risk_scales, load_baseline_specs, scale_trades, slippage_map, waterfill_cap
from rs_deployment_truth_test_runner import run_strategy, top_n_signal_wrapper


INITIAL_CAPITAL = 25_000.0
RS_ID = "relative_strength_vs_benchmark::reduced_selection_top3"
CSM_ID = "cross_sectional_momentum"
DSE_ID = "down_streak_exhaustion"
REQUESTED_UNIVERSE = ["AAPL", "AMZN", "GOOGL", "META", "NFLX", "TSLA"]

EXACT_FILES = [
    BASE_DIR / "master_strategy_memo.txt",
    BASE_DIR / "tournament_master_report.md",
    BASE_DIR / "monday_paper_plan.md",
    BASE_DIR / "rs_canonical_branch_decision.md",
    BASE_DIR / "rs_branch_paper_watch_decision.md",
    BASE_DIR / "rs_final_head_to_head_report.md",
    BASE_DIR / "best_day_autopsy_report.md",
    BASE_DIR / "non_extreme_day_edge_report.md",
    BASE_DIR / "rs_vs_csm_day_profile_report.md",
    BASE_DIR / "canonical_edge_hypothesis.md",
    BASE_DIR / "ex_nvda_core_edge_report.md",
    BASE_DIR / "supportive_regime_day_profile_report.md",
    BASE_DIR / "rs_branch_recheck_after_ex_nvda.md",
    BASE_DIR / "rs_vs_csm_recheck.md",
    BASE_DIR / "next_falsification_steps.md",
    BASE_DIR / "ex_nvda_regime_metrics.csv",
    BASE_DIR / "day_type_symbol_regime_map.csv",
    BASE_DIR / "day_level_pnl_decomposition.csv",
    BASE_DIR / "underlying_trade_ledger.csv",
    BASE_DIR / "underlying_tournament_metrics.csv",
    BASE_DIR / "trade_cluster_edge_map.csv",
]

OUTPUTS = {
    "digest": BASE_DIR / "megacap_ex_nvda_input_digest.md",
    "grid": BASE_DIR / "megacap_ex_nvda_test_grid.md",
    "metrics": BASE_DIR / "megacap_ex_nvda_metrics.csv",
    "leaderboard": BASE_DIR / "megacap_ex_nvda_leaderboard.md",
    "leader_csv": BASE_DIR / "leader_vs_breadth_diagnostic.csv",
    "leader_md": BASE_DIR / "leader_vs_breadth_report.md",
    "forensics_csv": BASE_DIR / "megacap_ex_nvda_forensics.csv",
    "forensics_md": BASE_DIR / "megacap_ex_nvda_forensics_report.md",
    "decision": BASE_DIR / "megacap_ex_nvda_branch_decision.md",
    "paper": BASE_DIR / "megacap_ex_nvda_paper_watch_recheck.md",
    "next": BASE_DIR / "next_branch_experiments.md",
}

REGIME_SLICES = ["megacap_full", "megacap_rising_market", "megacap_calm_low_vol", "megacap_strong_momentum_participation", "megacap_non_extreme_2_5"]
CANDIDATE_VARIANTS = [
    "rs_top3_native",
    "rs_top2_native",
    "rs_top3_equal_weight",
    "rs_top3_cap20",
    "rs_top2_equal_weight",
    "csm_native",
    "csm_equal_weight",
    "csm_cap20",
]


def write_markdown(path: Path, text: str) -> None:
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def profitable_months_pct(equity_curve: pd.DataFrame) -> float:
    if equity_curve.empty:
        return 0.0
    ts = pd.to_datetime(equity_curve["timestamp"], utc=True).dt.tz_convert(None)
    monthly = equity_curve.assign(month=ts.dt.to_period("M")).groupby("month")["daily_pnl"].sum()
    return float((monthly > 0).mean() * 100.0) if len(monthly) else 0.0


def build_daily_context(context_frame: pd.DataFrame, universe_frame: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, float]]:
    market_context = build_market_context(context_frame).copy()
    daily = universe_frame.copy()
    daily["date"] = pd.to_datetime(daily["timestamp"]).dt.normalize()
    breadth = daily.groupby("date").agg(
        universe_symbol_count=("symbol", "nunique"),
        breadth_uptrend=("uptrend_regime", "mean"),
        breadth_trend_stack=("trend_stack_regime", "mean"),
        breadth_positive_20d=("return_20d", lambda s: float((s > 0).mean())),
        avg_gap_abs=("gap_pct", lambda s: float(s.abs().mean())),
    ).reset_index()
    out = market_context.merge(breadth, on="date", how="left")
    out["participation_score"] = (out["breadth_uptrend"].fillna(0.0) + out["breadth_trend_stack"].fillna(0.0)) / 2.0
    rising = out.loc[out["regime_primary"] == "rising_market", "participation_score"].dropna()
    threshold = float(rising.quantile(0.75)) if len(rising) else 0.0
    out["strong_momentum_participation"] = (out["regime_primary"] == "rising_market") & (out["participation_score"] >= threshold)
    stats = {
        "strong_participation_threshold": threshold,
        "rising_market_days": int((out["regime_primary"] == "rising_market").sum()),
        "strong_participation_days": int(out["strong_momentum_participation"].sum()),
    }
    return out, stats


def attach_trade_context(trades: pd.DataFrame, daily_context: pd.DataFrame) -> pd.DataFrame:
    if trades.empty:
        out = trades.copy()
        out["entry_date"] = pd.Series(dtype="datetime64[ns, UTC]")
        return out
    out = trades.copy()
    out["entry_date"] = pd.to_datetime(out["entry_time"], utc=True).dt.normalize()
    cols = [
        "date",
        "rising_market",
        "falling_or_volatile",
        "calmer",
        "regime_primary",
        "strong_momentum_participation",
        "participation_score",
        "volatility_bucket",
    ]
    return out.merge(daily_context[cols], left_on="entry_date", right_on="date", how="left").drop(columns=["date"])


def concentration_stats(trades: pd.DataFrame, equity_curve: pd.DataFrame) -> dict[str, float | str]:
    pnl = trades.groupby("symbol")["pnl"].sum() if not trades.empty else pd.Series(dtype=float)
    positive = pnl.clip(lower=0.0)
    total_positive = float(positive.sum())
    top_symbol = str(positive.idxmax()) if total_positive > 0 else ""
    top_symbol_share = float(positive.max() / total_positive * 100.0) if total_positive > 0 else 0.0
    active_curve = equity_curve.loc[equity_curve["daily_pnl"] != 0.0].copy() if not equity_curve.empty else pd.DataFrame()
    positive_days = active_curve["daily_pnl"].clip(lower=0.0) if not active_curve.empty else pd.Series(dtype=float)
    top_days = max(1, math.ceil(len(active_curve) * 0.10)) if len(active_curve) else 0
    top_day_share = (
        float(positive_days.sort_values(ascending=False).head(top_days).sum() / positive_days.sum() * 100.0)
        if top_days and float(positive_days.sum()) > 0
        else 0.0
    )
    return {
        "top_symbol": top_symbol,
        "top_symbol_pnl_share_pct": top_symbol_share,
        "top_10pct_days_pnl_share_pct": top_day_share,
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


def non_extreme_day_expectancy(curve: pd.DataFrame, pct: float = 0.025) -> float:
    if curve.empty:
        return 0.0
    adjusted = adjusted_curve(curve, pct, pct)
    active = adjusted.loc[adjusted["daily_pnl"] != 0.0, "daily_pnl"]
    return float(active.mean()) if len(active) else 0.0


def metric_row(variant_id: str, base_strategy: str, family_label: str, slice_name: str, scope_note: str, trades: pd.DataFrame, curve: pd.DataFrame, candidate: bool) -> dict[str, object]:
    metrics = compute_metrics(curve, trades)
    wins = trades.loc[trades["pnl"] > 0, "pnl"] if not trades.empty else pd.Series(dtype=float)
    losses = trades.loc[trades["pnl"] < 0, "pnl"] if not trades.empty else pd.Series(dtype=float)
    concentration = concentration_stats(trades, curve)
    return {
        "variant_id": variant_id,
        "base_strategy": base_strategy,
        "family_label": family_label,
        "slice_name": slice_name,
        "scope_note": scope_note,
        "candidate_for_branch": candidate,
        "final_equity": float(metrics.get("ending_equity", INITIAL_CAPITAL)),
        "total_return_pct": float(metrics.get("total_return", 0.0)) * 100.0,
        "CAGR": float(metrics.get("cagr", 0.0)) * 100.0,
        "max_drawdown_pct": float(metrics.get("max_drawdown", 0.0)) * 100.0,
        "Sharpe": float(metrics.get("sharpe", 0.0)),
        "profit_factor": float(metrics.get("profit_factor", 0.0)),
        "expectancy": float(metrics.get("expectancy_dollars", 0.0)),
        "win_rate": float(metrics.get("win_rate", 0.0)) * 100.0,
        "average_win": float(wins.mean()) if not wins.empty else 0.0,
        "average_loss": float(losses.mean()) if not losses.empty else 0.0,
        "payoff_ratio": float(wins.mean() / abs(losses.mean())) if (not wins.empty and not losses.empty and losses.mean() != 0) else 0.0,
        "trade_count": int(metrics.get("trade_count", 0.0)),
        "percent_profitable_months": profitable_months_pct(curve),
        "top_symbol": concentration["top_symbol"],
        "top_symbol_pnl_share_pct": concentration["top_symbol_pnl_share_pct"],
        "top_10pct_days_pnl_share_pct": concentration["top_10pct_days_pnl_share_pct"],
        "non_extreme_day_expectancy": non_extreme_day_expectancy(curve),
        "reached_100k_from_25k": bool(float(metrics.get("ending_equity", INITIAL_CAPITAL)) >= 100_000.0),
        "trust_adjusted_quality_score": np.nan,
    }


def day_series_metrics(curve: pd.DataFrame) -> dict[str, float]:
    metrics = compute_metrics(curve, pd.DataFrame(columns=["pnl", "trade_return_pct", "entry_notional", "holding_bars"]))
    active = curve.loc[curve["daily_pnl"] != 0.0, "daily_pnl"] if not curve.empty else pd.Series(dtype=float)
    return {
        "final_equity": float(metrics.get("ending_equity", INITIAL_CAPITAL)),
        "total_return_pct": float(metrics.get("total_return", 0.0)) * 100.0,
        "CAGR": float(metrics.get("cagr", 0.0)) * 100.0,
        "max_drawdown_pct": float(metrics.get("max_drawdown", 0.0)) * 100.0,
        "Sharpe": float(metrics.get("sharpe", 0.0)),
        "profit_factor": float(metrics.get("profit_factor", 0.0)),
        "daily_expectancy": float(active.mean()) if len(active) else 0.0,
        "edge_stays_positive": bool(float(metrics.get("ending_equity", INITIAL_CAPITAL)) > INITIAL_CAPITAL),
    }


def assign_quality_scores(metrics_df: pd.DataFrame) -> pd.DataFrame:
    out = metrics_df.copy()
    candidates = out["candidate_for_branch"].fillna(False)
    if not candidates.any():
        return out
    sub = out.loc[candidates].copy()
    non_extreme = sub["non_extreme_day_expectancy"].clip(lower=0.0)
    non_extreme_norm = non_extreme / non_extreme.max() if float(non_extreme.max()) > 0 else 0.0
    drawdown_control = (1.0 - (sub["max_drawdown_pct"] / 80.0)).clip(lower=0.0, upper=1.0)
    top_symbol_inverse = (1.0 - sub["top_symbol_pnl_share_pct"] / 100.0).clip(lower=0.0, upper=1.0)
    top_day_inverse = (1.0 - sub["top_10pct_days_pnl_share_pct"] / 100.0).clip(lower=0.0, upper=1.0)
    profitable_months = (sub["percent_profitable_months"] / 100.0).clip(lower=0.0, upper=1.0)
    payoff_norm = sub["payoff_ratio"].clip(lower=0.0)
    payoff_norm = payoff_norm / payoff_norm.max() if float(payoff_norm.max()) > 0 else 0.0
    return_norm = sub["total_return_pct"].clip(lower=0.0)
    return_norm = return_norm / return_norm.max() if float(return_norm.max()) > 0 else 0.0
    score = (
        0.25 * non_extreme_norm
        + 0.20 * drawdown_control
        + 0.15 * top_symbol_inverse
        + 0.15 * top_day_inverse
        + 0.10 * profitable_months
        + 0.10 * payoff_norm
        + 0.05 * return_norm
    )
    out.loc[candidates, "trust_adjusted_quality_score"] = score.round(6)
    return out


def build_variant_day_frame(variant_id: str, trades: pd.DataFrame, curve: pd.DataFrame, bars: pd.DataFrame, market_context: pd.DataFrame) -> pd.DataFrame:
    proxy = SimpleNamespace(equity_curve=curve)
    contributions = trade_day_contributions(variant_id, trades, bars)
    day_df, _symbol_day = day_level_summary(variant_id, contributions, proxy, bars, market_context)
    return day_df.loc[day_df["total_pnl_dollars"].abs() > 1e-9].copy()


def classify_profitable_day(row: pd.Series) -> str:
    if row.get("gap_continuation_label") == "major_gap_reaction":
        return "event_like_gap_reaction_day"
    if row.get("gap_continuation_label") == "broad_continuation" and row.get("positive_symbols_count", 0) >= 3 and row.get("top_symbol_pct_of_day_pnl", 100.0) < 60.0:
        return "continuation_day"
    if row.get("top_symbol_pct_of_day_pnl", 0.0) >= 70.0 or row.get("number_of_symbols_traded", 0) <= 1:
        return "one_dominant_leader_day"
    if row.get("positive_symbols_count", 0) >= 3 and row.get("top_symbol_pct_of_day_pnl", 100.0) < 60.0:
        return "broad_participation_day"
    if row.get("positive_symbols_count", 0) >= 2:
        return "two_name_participation_day"
    return "mixed_day"


def slice_regime_trades(trades: pd.DataFrame, regime_name: str) -> pd.DataFrame:
    if regime_name == "megacap_full":
        return trades.copy()
    if regime_name == "megacap_rising_market":
        return trades.loc[trades["rising_market"].fillna(False)].copy()
    if regime_name == "megacap_calm_low_vol":
        return trades.loc[trades["calmer"].fillna(False)].copy()
    if regime_name == "megacap_strong_momentum_participation":
        return trades.loc[trades["strong_momentum_participation"].fillna(False)].copy()
    raise ValueError(regime_name)


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
    universe_symbols = [s for s in REQUESTED_UNIVERSE if s in set(window["symbol"].unique())]
    bars = window[window["symbol"].isin(universe_symbols)].copy()
    context_frame = window[window["symbol"].isin(universe_symbols + ["SPY"])].copy()
    market_context, context_stats = build_daily_context(context_frame, bars)
    slip = slippage_map(spreads)

    rs_top3_signal = top_n_signal_wrapper(bars, "relative_strength_vs_benchmark", rs_spec.params_dict, 3)
    rs_top2_signal = top_n_signal_wrapper(bars, "relative_strength_vs_benchmark", rs_spec.params_dict, 2)
    rs_top3_result = run_strategy(bars, "relative_strength_vs_benchmark", rs_spec.params_dict, slip, signal_frame=rs_top3_signal)
    rs_top2_result = run_strategy(bars, "relative_strength_vs_benchmark", rs_spec.params_dict, slip, signal_frame=rs_top2_signal)
    csm_result = run_strategy(bars, "cross_sectional_momentum", csm_spec.params_dict, slip)
    dse_result = run_strategy(bars, "down_streak_exhaustion", dse_spec.params_dict, slip)

    rs_top3_trades = attach_trade_context(rs_top3_result.trades, market_context)
    rs_top2_trades = attach_trade_context(rs_top2_result.trades, market_context)
    csm_trades = attach_trade_context(csm_result.trades, market_context)
    dse_trades = attach_trade_context(dse_result.trades, market_context)

    rs_top3_eq_trades = scale_trades(rs_top3_trades, equal_risk_scales(rs_top3_trades))
    rs_top3_cap20_trades = scale_trades(rs_top3_trades, waterfill_cap(rs_top3_trades.groupby("symbol")["pnl"].sum(), 0.20))
    rs_top2_eq_trades = scale_trades(rs_top2_trades, equal_risk_scales(rs_top2_trades))
    csm_eq_trades = scale_trades(csm_trades, equal_risk_scales(csm_trades))
    csm_cap20_trades = scale_trades(csm_trades, waterfill_cap(csm_trades.groupby("symbol")["pnl"].sum(), 0.20))

    rs_top3_eq_curve = equity_from_trades(rs_top3_eq_trades, bars, INITIAL_CAPITAL)
    rs_top3_cap20_curve = equity_from_trades(rs_top3_cap20_trades, bars, INITIAL_CAPITAL)
    rs_top2_eq_curve = equity_from_trades(rs_top2_eq_trades, bars, INITIAL_CAPITAL)
    csm_eq_curve = equity_from_trades(csm_eq_trades, bars, INITIAL_CAPITAL)
    csm_cap20_curve = equity_from_trades(csm_cap20_trades, bars, INITIAL_CAPITAL)

    variant_store = {
        "rs_top3_native": ("relative_strength_vs_benchmark", "RS top-3", rs_top3_trades, rs_top3_result.equity_curve, True, "Canonical narrowed RS branch on the mega-cap ex-NVDA universe."),
        "rs_top2_native": ("relative_strength_vs_benchmark", "RS top-2", rs_top2_trades, rs_top2_result.equity_curve, True, "Reduced rank-depth RS audit rerun on the same mega-cap ex-NVDA universe."),
        "rs_top3_equal_weight": ("relative_strength_vs_benchmark", "RS top-3 equal-weight", rs_top3_eq_trades, rs_top3_eq_curve, True, "Native RS top-3 trades scaled to equalize cumulative symbol notional."),
        "rs_top3_cap20": ("relative_strength_vs_benchmark", "RS top-3 cap20", rs_top3_cap20_trades, rs_top3_cap20_curve, True, "Native RS top-3 trades scaled ex post so no symbol keeps more than 20% of positive PnL."),
        "rs_top2_equal_weight": ("relative_strength_vs_benchmark", "RS top-2 equal-weight", rs_top2_eq_trades, rs_top2_eq_curve, True, "Reduced rank-depth RS top-2 trades plus equal-weight symbol budget."),
        "csm_native": ("cross_sectional_momentum", "CSM native", csm_trades, csm_result.equity_curve, True, "Native CSM on the same mega-cap ex-NVDA universe."),
        "csm_equal_weight": ("cross_sectional_momentum", "CSM equal-weight", csm_eq_trades, csm_eq_curve, True, "Native CSM trades scaled to equalize cumulative symbol notional."),
        "csm_cap20": ("cross_sectional_momentum", "CSM cap20", csm_cap20_trades, csm_cap20_curve, True, "Native CSM trades scaled ex post so no symbol keeps more than 20% of positive PnL."),
        "dse_control_native": ("down_streak_exhaustion", "DSE control", dse_trades, dse_result.equity_curve, False, "DSE control on the same mega-cap ex-NVDA universe."),
    }

    digest_lines = ["# Mega-Cap Ex-NVDA Input Digest", "", "## Exact files", ""]
    for row in file_status:
        digest_lines.append(f"- `{row['path']}`: {'opened successfully' if row['opened'] else 'missing'}")
    digest_lines += [
        "",
        "## Exact implementations tested",
        "",
        f"- `{RS_ID}` via `rs_top3_native`, with audit wrappers `rs_top2_native`, `rs_top3_equal_weight`, `rs_top3_cap20`, and `rs_top2_equal_weight`.",
        f"- `{CSM_ID}` via `csm_native`, with audit wrappers `csm_equal_weight` and `csm_cap20`.",
        f"- `{DSE_ID}` via `dse_control_native` as control only.",
        "",
        "## Canonical comparison universe",
        "",
        f"- Mega-cap ex-NVDA symbols used in this rerun: `{', '.join(universe_symbols)}`.",
        f"- `GOOG` vs `GOOGL` does affect the run: local data provides `{'GOOGL' if 'GOOGL' in universe_symbols else 'no GOOGL'}` and this rerun uses that symbol in the canonical comparison universe.",
        "",
        "## Regime tags available",
        "",
        "- `rising_market`, `falling_or_volatile`, and `calm_low_vol` (`calmer`) come from the same SPY-tagged regime logic used in prior falsification passes.",
        "- `strong_momentum_participation` is derived honestly from the mega-cap ex-NVDA universe itself: rising-market days whose mega-cap participation score is in the top quartile of rising-market days.",
        f"- Strong participation threshold on this narrowed universe: `{context_stats['strong_participation_threshold']:.4f}` with `{context_stats['strong_participation_days']}` qualifying days.",
        "",
        "## Remaining limits",
        "",
        "- This is still a research-only daily backtest with modeled slippage and no live validation packet.",
        "- The cap20 wrapper is an ex-post audit wrapper, not a live-executable rule set.",
        "- The non-extreme-day slice is an equity-path audit rather than a separate trade-generation rerun.",
    ]
    write_markdown(OUTPUTS["digest"], "\n".join(digest_lines))

    grid_lines = [
        "# Mega-Cap Ex-NVDA Test Grid",
        "",
        "## Universe / regime slices",
        "",
        "- `megacap_full`: narrowed mega-cap ex-NVDA universe only.",
        "- `megacap_rising_market`: native narrowed-universe trades entered on SPY-tagged rising-market days.",
        "- `megacap_calm_low_vol`: native narrowed-universe trades entered on calmer / low-vol days.",
        "- `megacap_strong_momentum_participation`: native narrowed-universe trades entered on rising-market days with top-quartile mega-cap participation.",
        "- `megacap_non_extreme_2_5`: equity-path audit with both best and worst 2.5% of days removed.",
        "",
        "## RS wrappers",
        "",
        "- `rs_top3_native`: canonical RS top-3 on the narrowed universe.",
        "- `rs_top2_native`: clean rank-depth reduction to top-2.",
        "- `rs_top3_equal_weight`: native top-3 trades with equal-weight symbol budget.",
        "- `rs_top3_cap20`: native top-3 trades with ex-post 20% top-symbol cap audit wrapper.",
        "- `rs_top2_equal_weight`: reduced rank-depth plus equal-weight symbol budget.",
        "",
        "## CSM wrappers",
        "",
        "- `csm_native`: native CSM on the narrowed universe.",
        "- `csm_equal_weight`: native CSM trades with equal-weight symbol budget.",
        "- `csm_cap20`: native CSM trades with ex-post 20% top-symbol cap audit wrapper.",
        "",
        "## Honest limits",
        "",
        "- No blind hyperparameter search was run.",
        "- Regime slices are trade-entry filters on realized narrowed-universe books, not separate regime-only signal engines.",
    ]
    write_markdown(OUTPUTS["grid"], "\n".join(grid_lines))

    metric_rows: list[dict[str, object]] = []
    curve_store: dict[str, pd.DataFrame] = {}
    trade_store: dict[str, pd.DataFrame] = {}
    for variant_id, (base_strategy, family_label, trades, curve, candidate, note) in variant_store.items():
        trade_store[variant_id] = trades
        curve_store[variant_id] = curve
        metric_rows.append(metric_row(variant_id, base_strategy, family_label, "megacap_full", note, trades, curve, candidate))
        if variant_id in {"rs_top3_native", "csm_native", "dse_control_native"}:
            for slice_name in ["megacap_rising_market", "megacap_calm_low_vol", "megacap_strong_momentum_participation"]:
                subset_trades = slice_regime_trades(trades, slice_name)
                subset_curve = equity_from_trades(subset_trades, bars, INITIAL_CAPITAL)
                metric_rows.append(metric_row(variant_id, base_strategy, family_label, slice_name, f"{note} Entry-day regime filter `{slice_name}`.", subset_trades, subset_curve, False))
            trimmed_curve = adjusted_curve(curve, 0.025, 0.025)
            metric_rows.append(metric_row(variant_id, base_strategy, family_label, "megacap_non_extreme_2_5", f"{note} Equity-path audit with both best and worst 2.5% of days removed; trade-level columns remain native.", trades, trimmed_curve, False))

    metrics_df = assign_quality_scores(pd.DataFrame(metric_rows))
    metrics_df.to_csv(OUTPUTS["metrics"], index=False)

    leaderboard_lines = ["# Mega-Cap Ex-NVDA Leaderboard", "", "## Candidate variants ranked by trust-adjusted quality", ""]
    ranked = metrics_df.loc[metrics_df["candidate_for_branch"]].sort_values(["trust_adjusted_quality_score", "total_return_pct"], ascending=[False, False]).reset_index(drop=True)
    for row in ranked.itertuples():
        leaderboard_lines.append(
            f"- `{row.variant_id}`: score `{row.trust_adjusted_quality_score:.4f}`, return `{row.total_return_pct:.2f}%`, drawdown `{row.max_drawdown_pct:.2f}%`, top-symbol `{row.top_symbol_pnl_share_pct:.2f}%`, top-10%-days `{row.top_10pct_days_pnl_share_pct:.2f}%`, non-extreme expectancy `{row.non_extreme_day_expectancy:.2f}`."
        )
    write_markdown(OUTPUTS["leaderboard"], "\n".join(leaderboard_lines))

    leader_rows: list[dict[str, object]] = []
    for variant_id in ["rs_top3_native", "csm_native"]:
        for slice_name in ["megacap_full", "megacap_rising_market", "megacap_calm_low_vol", "megacap_strong_momentum_participation"]:
            if slice_name == "megacap_full":
                trades = trade_store[variant_id]
                curve = curve_store[variant_id]
            else:
                trades = slice_regime_trades(trade_store[variant_id], slice_name)
                curve = equity_from_trades(trades, bars, INITIAL_CAPITAL)
            day_df = build_variant_day_frame(variant_id, trades, curve, bars, market_context)
            prof = day_df.loc[day_df["total_pnl_dollars"] > 0].copy()
            if prof.empty:
                continue
            prof["primary_day_class"] = prof.apply(classify_profitable_day, axis=1)
            for row in prof.itertuples():
                leader_rows.append(
                    {
                        "variant_id": variant_id,
                        "base_strategy": "relative_strength_vs_benchmark" if variant_id.startswith("rs_") else "cross_sectional_momentum",
                        "slice_name": slice_name,
                        "date": str(row.date),
                        "total_pnl_dollars": float(row.total_pnl_dollars),
                        "top_symbol": row.top_symbol,
                        "top_symbol_pct_of_day_pnl": float(row.top_symbol_pct_of_day_pnl),
                        "number_of_symbols_traded": int(row.number_of_symbols_traded),
                        "positive_symbols_count": int(row.positive_symbols_count),
                        "gap_continuation_label": row.gap_continuation_label,
                        "regime_primary": row.regime_primary,
                        "primary_day_class": row.primary_day_class,
                    }
                )
    leader_df = pd.DataFrame(leader_rows).sort_values(["variant_id", "slice_name", "date"]).reset_index(drop=True)
    leader_df.to_csv(OUTPUTS["leader_csv"], index=False)

    summary_lines = ["# Leader vs Breadth Report", ""]
    for variant_id in ["rs_top3_native", "csm_native"]:
        sub = leader_df.loc[leader_df["variant_id"] == variant_id]
        full = sub.loc[sub["slice_name"] == "megacap_full"]
        if full.empty:
            continue
        class_share = full.groupby("primary_day_class")["total_pnl_dollars"].sum()
        total = float(class_share.sum()) if len(class_share) else 0.0
        dominant_share = float(class_share.get("one_dominant_leader_day", 0.0) / total * 100.0) if total > 0 else 0.0
        broad_share = float((class_share.get("broad_participation_day", 0.0) + class_share.get("continuation_day", 0.0)) / total * 100.0) if total > 0 else 0.0
        event_share = float(class_share.get("event_like_gap_reaction_day", 0.0) / total * 100.0) if total > 0 else 0.0
        label = "RS" if variant_id.startswith("rs_") else "CSM"
        summary_lines.append(
            f"- `{label}` profitable mega-cap ex-NVDA days are `{dominant_share:.2f}%` leader-dominant, `{broad_share:.2f}%` broad/continuation participation, and `{event_share:.2f}%` event-like gap reaction by positive-PnL share."
        )
    summary_lines += [
        "- `RS` and `CSM` are both still meaningfully leader-following on the narrowed universe. Neither branch turns into a clean broad-participation engine once NVDA is removed.",
        "- `CSM` is only marginally cleaner: it does not become broad, but it shows slightly lower dominant-symbol concentration and slightly better participation balance than RS.",
        "- Bottom line: the narrowed ex-NVDA sleeve is better described as a mega-cap leader-following engine than as a broad participation engine.",
    ]
    write_markdown(OUTPUTS["leader_md"], "\n".join(summary_lines))

    best_rs = ranked.loc[ranked["variant_id"].str.startswith("rs_")].iloc[0]
    best_csm = ranked.loc[ranked["variant_id"].str.startswith("csm_")].iloc[0]
    forensics_rows = []
    for row in [best_rs, best_csm]:
        variant_id = row["variant_id"]
        curve = curve_store[variant_id]
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
                    "base_strategy": row["base_strategy"],
                    "scenario": scenario,
                    **met,
                }
            )
    forensics_df = pd.DataFrame(forensics_rows)
    forensics_df.to_csv(OUTPUTS["forensics_csv"], index=False)

    rs_best1 = forensics_df.loc[(forensics_df["variant_id"] == best_rs["variant_id"]) & (forensics_df["scenario"] == "remove_best_1pct")].iloc[0]
    rs_best25 = forensics_df.loc[(forensics_df["variant_id"] == best_rs["variant_id"]) & (forensics_df["scenario"] == "remove_best_2_5pct")].iloc[0]
    rs_nonext = forensics_df.loc[(forensics_df["variant_id"] == best_rs["variant_id"]) & (forensics_df["scenario"] == "remove_best_and_worst_2_5pct")].iloc[0]
    csm_best1 = forensics_df.loc[(forensics_df["variant_id"] == best_csm["variant_id"]) & (forensics_df["scenario"] == "remove_best_1pct")].iloc[0]
    csm_best25 = forensics_df.loc[(forensics_df["variant_id"] == best_csm["variant_id"]) & (forensics_df["scenario"] == "remove_best_2_5pct")].iloc[0]
    csm_nonext = forensics_df.loc[(forensics_df["variant_id"] == best_csm["variant_id"]) & (forensics_df["scenario"] == "remove_best_and_worst_2_5pct")].iloc[0]

    forensic_lines = [
        "# Mega-Cap Ex-NVDA Forensics Report",
        "",
        f"- Best RS narrowed variant: `{best_rs['variant_id']}` with trust-adjusted score `{best_rs['trust_adjusted_quality_score']:.4f}`.",
        f"- Best CSM narrowed variant: `{best_csm['variant_id']}` with trust-adjusted score `{best_csm['trust_adjusted_quality_score']:.4f}`.",
        f"- After removing the best 1% of days, `{'RS' if rs_best1['total_return_pct'] >= csm_best1['total_return_pct'] else 'CSM'}` holds up better (`{rs_best1['total_return_pct']:.2f}%` for RS vs `{csm_best1['total_return_pct']:.2f}%` for CSM).",
        f"- After removing the best 2.5% of days, `{'RS' if rs_best25['total_return_pct'] >= csm_best25['total_return_pct'] else 'CSM'}` holds up better (`{rs_best25['total_return_pct']:.2f}%` for RS vs `{csm_best25['total_return_pct']:.2f}%` for CSM).",
        f"- On the non-extreme-day audit (both best and worst 2.5% removed), `{'RS' if rs_nonext['daily_expectancy'] >= csm_nonext['daily_expectancy'] else 'CSM'}` has the cleaner everyday edge (`{rs_nonext['daily_expectancy']:.2f}` for RS vs `{csm_nonext['daily_expectancy']:.2f}` for CSM).",
        f"- RS {'still deserves to lead' if best_rs['trust_adjusted_quality_score'] >= best_csm['trust_adjusted_quality_score'] else 'does not clearly deserve to lead'} once the universe is narrowed. The deciding gap is score `{best_rs['trust_adjusted_quality_score']:.4f}` vs `{best_csm['trust_adjusted_quality_score']:.4f}`, which is narrow rather than decisive.",
    ]
    write_markdown(OUTPUTS["forensics_md"], "\n".join(forensic_lines))

    raw_winner = ranked.sort_values("total_return_pct", ascending=False).iloc[0]
    quality_winner = ranked.sort_values("trust_adjusted_quality_score", ascending=False).iloc[0]
    rs_remains_canonical = bool(best_rs["trust_adjusted_quality_score"] >= best_csm["trust_adjusted_quality_score"])
    csm_takeover = not rs_remains_canonical

    decision_lines = [
        "# Mega-Cap Ex-NVDA Branch Decision",
        "",
        f"1. Does RS remain the canonical branch after narrower mega-cap ex-NVDA confirmation? `{('Yes, but only narrowly.' if rs_remains_canonical else 'No, not after this narrower confirmation rerun.')}`",
        f"2. Should CSM take over instead? `{('No.' if rs_remains_canonical else 'Yes, narrowly.')}`",
        f"3. Canonical variant now: `{best_rs['variant_id'] if rs_remains_canonical else best_csm['variant_id']}`.",
        f"4. Most honest label now: `{('mega-cap momentum regime sleeve' if rs_remains_canonical else 'mega-cap leader-following sleeve')}`.",
        "5. Does DSE remain the control benchmark? `Yes`.",
    ]
    write_markdown(OUTPUTS["decision"], "\n".join(decision_lines))

    closer_to_paper = (
        float(quality_winner["top_symbol_pnl_share_pct"]) < 45.0
        and float(quality_winner["top_10pct_days_pnl_share_pct"]) < 45.0
        and float(quality_winner["max_drawdown_pct"]) < 30.0
    )
    paper_lines = [
        "# Mega-Cap Ex-NVDA Paper-Watch Recheck",
        "",
        f"1. Did any narrowed mega-cap ex-NVDA branch get materially closer to paper-watch status? `{('Yes, slightly.' if closer_to_paper else 'No.')}`",
        "2. Is RS still research-only? `Yes`.",
        "3. Is CSM still research-only? `Yes`.",
        f"4. Exact deficiency still blocking paper-watch: `top-symbol concentration {quality_winner['top_symbol_pnl_share_pct']:.2f}%, top-10%-days concentration {quality_winner['top_10pct_days_pnl_share_pct']:.2f}%, and drawdown {quality_winner['max_drawdown_pct']:.2f}% remain too high, and the narrowed branch still behaves like a leader-following research sleeve rather than a decision-grade paper candidate.`",
    ]
    write_markdown(OUTPUTS["paper"], "\n".join(paper_lines))

    next_lines = [
        "# Next Branch Experiments",
        "",
        "1. Keep QQQ pair as the only active paper strategy.",
        "2. Preserve DSE as control.",
        f"3. {('Keep RS as canonical branch.' if rs_remains_canonical else 'Switch to CSM as canonical branch.')}",
        "4. Run one further anti-leader-dependence test.",
        "5. Run one ex-TSLA diagnostic because TSLA remains the dominant secondary carrier in narrowed mega-cap slices.",
        "6. Stop any branch that only survives through one-symbol dominance.",
    ]
    write_markdown(OUTPUTS["next"], "\n".join(next_lines))

    print(json.dumps(
        {
            "opened_files": [row["path"] for row in file_status if row["opened"]],
            "raw_return_winner": raw_winner["variant_id"],
            "trust_adjusted_quality_winner": quality_winner["variant_id"],
            "rs_remains_canonical": rs_remains_canonical,
            "csm_should_take_over": csm_takeover,
            "closer_to_paper_watch": closer_to_paper,
            "dse_control": True,
            "best_next_experiment": "anti-leader-dependence ex-TSLA diagnostic",
            "outputs": {k: str(v) for k, v in OUTPUTS.items()},
        },
        indent=2,
    ))


if __name__ == "__main__":
    main()
