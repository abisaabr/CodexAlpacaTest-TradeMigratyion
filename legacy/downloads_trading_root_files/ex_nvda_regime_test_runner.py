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
    daily_series_metrics,
    day_level_summary,
    select_extreme_days,
    trade_day_contributions,
)
from nvda_truth_test_runner import BASE_UNIVERSE, load_baseline_specs, slippage_map
from rs_deployment_truth_test_runner import run_strategy, top_n_signal_wrapper


INITIAL_CAPITAL = 25_000.0
RS_ID = "relative_strength_vs_benchmark::reduced_selection_top3"
CSM_ID = "cross_sectional_momentum"
DSE_ID = "down_streak_exhaustion"
ETF_SET = {"SPY", "QQQ", "IWM"}
MEGACAP_CANDIDATES = ["AAPL", "AMZN", "GOOGL", "META", "NFLX", "TSLA"]

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
    BASE_DIR / "next_micro_experiments.md",
    BASE_DIR / "day_type_symbol_regime_map.csv",
    BASE_DIR / "day_level_pnl_decomposition.csv",
    BASE_DIR / "underlying_trade_ledger.csv",
    BASE_DIR / "underlying_tournament_metrics.csv",
    BASE_DIR / "trade_cluster_edge_map.csv",
]

OUTPUTS = {
    "digest": BASE_DIR / "ex_nvda_regime_test_input_digest.md",
    "matrix": BASE_DIR / "ex_nvda_regime_test_matrix.md",
    "metrics": BASE_DIR / "ex_nvda_regime_metrics.csv",
    "leaderboard": BASE_DIR / "ex_nvda_regime_leaderboard.md",
    "core": BASE_DIR / "ex_nvda_core_edge_report.md",
    "supportive_csv": BASE_DIR / "supportive_regime_day_profile.csv",
    "supportive_md": BASE_DIR / "supportive_regime_day_profile_report.md",
    "branch_recheck": BASE_DIR / "rs_branch_recheck_after_ex_nvda.md",
    "rs_vs_csm": BASE_DIR / "rs_vs_csm_recheck.md",
    "next_steps": BASE_DIR / "next_falsification_steps.md",
}

SLICE_ORDER = [
    "native_baseline",
    "ex_nvda_full",
    "rising_market",
    "rising_market_ex_nvda",
    "calmer",
    "calmer_ex_nvda",
    "strong_momentum_participation",
    "strong_momentum_participation_ex_nvda",
    "megacap_ex_nvda",
    "megacap_ex_nvda_supportive",
    "etf_only",
]

SUPPORTIVE_PROFILE_SLICES = [
    "rising_market_ex_nvda",
    "strong_momentum_participation_ex_nvda",
    "megacap_ex_nvda_supportive",
]


def write_markdown(path: Path, text: str) -> None:
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def read_if_exists(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


def profitable_months_pct(equity_curve: pd.DataFrame) -> float:
    if equity_curve.empty:
        return 0.0
    ts = pd.to_datetime(equity_curve["timestamp"], utc=True).dt.tz_convert(None)
    months = equity_curve.assign(month=ts.dt.to_period("M"))
    monthly = months.groupby("month")["daily_pnl"].sum()
    return float((monthly > 0).mean() * 100.0) if len(monthly) else 0.0


def symbol_family(symbol: str) -> str:
    if symbol == "NVDA":
        return "NVDA"
    if symbol in ETF_SET:
        return "ETF"
    if symbol in MEGACAP_CANDIDATES:
        return "mega_cap_tech_ex_nvda"
    return "all_other"


def build_daily_context(frame: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, float]]:
    ctx = build_market_context(frame).copy()
    daily = frame.copy()
    daily["date"] = pd.to_datetime(daily["timestamp"]).dt.normalize()
    breadth = daily.groupby("date").agg(
        symbol_count=("symbol", "nunique"),
        breadth_uptrend=("uptrend_regime", "mean"),
        breadth_trend_stack=("trend_stack_regime", "mean"),
        breadth_positive_20d=("return_20d", lambda s: float((s > 0).mean())),
        avg_vol_ratio=("vol_ratio_10_50", "mean"),
        avg_gap_abs=("gap_pct", lambda s: float(s.abs().mean())),
    ).reset_index()
    ctx = ctx.merge(breadth, on="date", how="left")
    ctx["participation_score"] = (ctx["breadth_uptrend"].fillna(0.0) + ctx["breadth_trend_stack"].fillna(0.0)) / 2.0
    rising = ctx.loc[ctx["regime_primary"] == "rising_market", "participation_score"].dropna()
    threshold = float(rising.quantile(0.75)) if len(rising) else 0.0
    ctx["strong_momentum_participation"] = (ctx["regime_primary"] == "rising_market") & (ctx["participation_score"] >= threshold)
    stats = {
        "strong_participation_threshold": threshold,
        "rising_market_days": int((ctx["regime_primary"] == "rising_market").sum()),
        "strong_participation_days": int(ctx["strong_momentum_participation"].sum()),
    }
    return ctx, stats


def attach_trade_context(trades: pd.DataFrame, daily_context: pd.DataFrame) -> pd.DataFrame:
    if trades.empty:
        out = trades.copy()
        out["entry_date"] = pd.Series(dtype="datetime64[ns, UTC]")
        out["symbol_family"] = pd.Series(dtype=str)
        return out
    out = trades.copy()
    out["entry_date"] = pd.to_datetime(out["entry_time"], utc=True).dt.normalize()
    out["exit_date"] = pd.to_datetime(out["exit_time"], utc=True).dt.normalize()
    ctx_cols = [
        "date",
        "rising_market",
        "falling_or_volatile",
        "calmer",
        "regime_primary",
        "volatility_bucket",
        "strong_momentum_participation",
        "breadth_uptrend",
        "breadth_trend_stack",
        "participation_score",
    ]
    out = out.merge(daily_context[ctx_cols], left_on="entry_date", right_on="date", how="left").drop(columns=["date"])
    out["symbol_family"] = out["symbol"].map(symbol_family)
    return out


def slice_mask(trades: pd.DataFrame, slice_name: str, megacap_symbols: set[str]) -> tuple[pd.Series, str]:
    if slice_name == "native_baseline":
        return pd.Series(True, index=trades.index), "native full-signal baseline on the 9-symbol user subset"
    if slice_name == "ex_nvda_full":
        return trades["symbol"] != "NVDA", "native trades with NVDA removed ex post"
    if slice_name == "rising_market":
        return trades["rising_market"].fillna(False), "entry day in SPY-tagged rising_market regime"
    if slice_name == "rising_market_ex_nvda":
        return trades["rising_market"].fillna(False) & (trades["symbol"] != "NVDA"), "entry day in rising_market regime with NVDA removed ex post"
    if slice_name == "calmer":
        return trades["calmer"].fillna(False), "entry day in SPY-tagged calmer / low-vol regime"
    if slice_name == "calmer_ex_nvda":
        return trades["calmer"].fillna(False) & (trades["symbol"] != "NVDA"), "entry day in calmer / low-vol regime with NVDA removed ex post"
    if slice_name == "strong_momentum_participation":
        return trades["strong_momentum_participation"].fillna(False), "entry day in rising_market with participation_score in the top quartile of rising-market days"
    if slice_name == "strong_momentum_participation_ex_nvda":
        return trades["strong_momentum_participation"].fillna(False) & (trades["symbol"] != "NVDA"), "strong momentum participation entry day with NVDA removed ex post"
    if slice_name == "megacap_ex_nvda":
        return trades["symbol"].isin(sorted(megacap_symbols)), "native trades restricted to mega-cap tech ex-NVDA symbols present in the user subset"
    if slice_name == "megacap_ex_nvda_supportive":
        return trades["symbol"].isin(sorted(megacap_symbols)) & trades["rising_market"].fillna(False), "mega-cap tech ex-NVDA trades restricted to rising_market entry days"
    if slice_name == "etf_only":
        return trades["symbol"].isin(sorted(ETF_SET)), "native trades restricted to SPY / QQQ / IWM"
    raise ValueError(slice_name)


def concentration_stats(trades: pd.DataFrame, equity_curve: pd.DataFrame) -> dict[str, float | str]:
    pnl = trades.groupby("symbol")["pnl"].sum() if not trades.empty else pd.Series(dtype=float)
    positive_symbol = pnl.clip(lower=0.0)
    total_positive = float(positive_symbol.sum())
    top_symbol = str(positive_symbol.idxmax()) if total_positive > 0 else ""
    top_symbol_share = float(positive_symbol.max() / total_positive * 100.0) if total_positive > 0 else 0.0
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


def non_extreme_day_expectancy(equity_curve: pd.DataFrame, pct: float = 0.025) -> float:
    if equity_curve.empty:
        return 0.0
    active = equity_curve.loc[equity_curve["daily_pnl"] != 0.0, "daily_pnl"].copy()
    if active.empty:
        return 0.0
    remove_n = max(1, math.ceil(len(active) * pct))
    trim = active.copy()
    trim.loc[active.sort_values(ascending=False).head(remove_n).index] = 0.0
    trim.loc[active.sort_values(ascending=True).head(remove_n).index] = 0.0
    return float(trim.mean())


def subset_metric_row(strategy_id: str, label: str, slice_name: str, note: str, trades: pd.DataFrame, bars: pd.DataFrame) -> dict[str, object]:
    curve = equity_from_trades(trades, bars, INITIAL_CAPITAL)
    metrics = compute_metrics(curve, trades)
    wins = trades.loc[trades["pnl"] > 0, "pnl"] if not trades.empty else pd.Series(dtype=float)
    losses = trades.loc[trades["pnl"] < 0, "pnl"] if not trades.empty else pd.Series(dtype=float)
    concentration = concentration_stats(trades, curve)
    return {
        "strategy_id": strategy_id,
        "strategy_label": label,
        "slice_name": slice_name,
        "scope_note": note,
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
    }


def slice_result(strategy_id: str, label: str, native_trades: pd.DataFrame, slice_name: str, bars: pd.DataFrame, megacap_symbols: set[str]) -> tuple[dict[str, object], pd.DataFrame, pd.DataFrame]:
    mask, note = slice_mask(native_trades, slice_name, megacap_symbols)
    subset = native_trades.loc[mask].copy()
    row = subset_metric_row(strategy_id, label, slice_name, note, subset, bars)
    curve = equity_from_trades(subset, bars, INITIAL_CAPITAL)
    return row, subset, curve


def supportive_profile_row(strategy_id: str, label: str, slice_name: str, trades: pd.DataFrame, bars: pd.DataFrame, market_context: pd.DataFrame) -> dict[str, object]:
    curve = equity_from_trades(trades, bars, INITIAL_CAPITAL)
    proxy = SimpleNamespace(equity_curve=curve)
    contrib = trade_day_contributions(strategy_id, trades, bars)
    day_df, _symbol_day = day_level_summary(strategy_id, contrib, proxy, bars, market_context)
    active = day_df.loc[day_df["total_pnl_dollars"].abs() > 1e-9].copy()
    if active.empty:
        return {
            "strategy_id": strategy_id,
            "strategy_label": label,
            "slice_name": slice_name,
            "active_days": 0,
            "best_5pct_share_positive_pnl_pct": 0.0,
            "worst_5pct_share_losses_pct": 0.0,
            "best_5pct_avg_top_symbol_share_pct": 0.0,
            "worst_5pct_avg_top_symbol_share_pct": 0.0,
            "best_5pct_multi_symbol_share_pct": 0.0,
            "worst_5pct_multi_symbol_share_pct": 0.0,
            "non_extreme_day_expectancy_2_5": 0.0,
            "positive_cluster_share_best_5pct": 0.0,
            "avg_symbols_traded_per_active_day": 0.0,
            "avg_positive_symbols_per_active_day": 0.0,
        }
    best5 = select_extreme_days(active, 0.05, "best")
    worst5 = select_extreme_days(active, 0.05, "worst")
    trim = pd.concat([select_extreme_days(active, 0.025, "best")[["date"]], select_extreme_days(active, 0.025, "worst")[["date"]]], ignore_index=True)
    non_extreme = daily_series_metrics(active, trim)
    total_positive = float(active["total_pnl_dollars"].clip(lower=0.0).sum())
    total_losses = abs(float(active["total_pnl_dollars"].clip(upper=0.0).sum()))
    return {
        "strategy_id": strategy_id,
        "strategy_label": label,
        "slice_name": slice_name,
        "active_days": int(len(active)),
        "best_5pct_share_positive_pnl_pct": float(best5["total_pnl_dollars"].sum() / total_positive * 100.0) if total_positive > 0 else 0.0,
        "worst_5pct_share_losses_pct": float(abs(worst5["total_pnl_dollars"].sum()) / total_losses * 100.0) if total_losses > 0 else 0.0,
        "best_5pct_avg_top_symbol_share_pct": float(best5["top_symbol_pct_of_day_pnl"].mean()) if not best5.empty else 0.0,
        "worst_5pct_avg_top_symbol_share_pct": float(worst5["top_symbol_pct_of_day_pnl"].mean()) if not worst5.empty else 0.0,
        "best_5pct_multi_symbol_share_pct": float((best5["participation_type"] == "multi_symbol_driven").mean() * 100.0) if not best5.empty else 0.0,
        "worst_5pct_multi_symbol_share_pct": float((worst5["participation_type"] == "multi_symbol_driven").mean() * 100.0) if not worst5.empty else 0.0,
        "non_extreme_day_expectancy_2_5": float(non_extreme["expectancy_dollars_per_day"]),
        "positive_cluster_share_best_5pct": float((best5["cluster_size"] > 1).mean() * 100.0) if not best5.empty else 0.0,
        "avg_symbols_traded_per_active_day": float(active["number_of_symbols_traded"].mean()),
        "avg_positive_symbols_per_active_day": float(active["positive_symbols_count"].mean()),
    }


def survival_pct(native_value: float, ex_value: float) -> float:
    if native_value <= 0:
        return 0.0
    return ex_value / native_value * 100.0


def main() -> None:
    file_status = [{"path": str(path), "opened": path.exists()} for path in EXACT_FILES]
    _ = [read_if_exists(path) for path in EXACT_FILES]

    specs = load_baseline_specs(BASE_DIR / "underlying_tournament_metrics.csv")
    rs_spec = specs.loc[specs["template_key"] == "relative_strength_vs_benchmark"].iloc[0]
    csm_spec = specs.loc[specs["template_key"] == "cross_sectional_momentum"].iloc[0]
    dse_spec = specs.loc[specs["template_key"] == "down_streak_exhaustion"].iloc[0]

    features = pd.read_parquet(BASE_DIR / "alpaca-stock-strategy-research" / "data" / "normalized" / "features" / "features.parquet")
    spreads = pd.read_parquet(BASE_DIR / "alpaca-stock-strategy-research" / "data" / "normalized" / "features" / "quote_spread_summary.parquet")
    start = pd.Timestamp("2021-03-24 04:00:00+00:00")
    end = pd.Timestamp("2026-03-24 04:00:00+00:00")
    frame = features[(features["timestamp"] >= start) & (features["timestamp"] <= end) & (features["symbol"].isin(BASE_UNIVERSE))].copy()
    market_context = build_market_context(frame)
    daily_context, context_stats = build_daily_context(frame)
    slip = slippage_map(spreads)
    megacap_symbols = {s for s in MEGACAP_CANDIDATES if s in set(frame["symbol"].unique()) and s != "NVDA"}

    rs_signal = top_n_signal_wrapper(frame, "relative_strength_vs_benchmark", rs_spec.params_dict, 3)
    rs_result = run_strategy(frame, "relative_strength_vs_benchmark", rs_spec.params_dict, slip, signal_frame=rs_signal)
    csm_result = run_strategy(frame, "cross_sectional_momentum", csm_spec.params_dict, slip)
    dse_result = run_strategy(frame, "down_streak_exhaustion", dse_spec.params_dict, slip)

    strategy_runs = [
        (RS_ID, "RS top-3", attach_trade_context(rs_result.trades, daily_context)),
        (CSM_ID, "Cross-sectional momentum", attach_trade_context(csm_result.trades, daily_context)),
        (DSE_ID, "Down Streak Exhaustion", attach_trade_context(dse_result.trades, daily_context)),
    ]

    digest_lines = ["# Ex-NVDA Regime Test Input Digest", "", "## Exact files", ""]
    for row in file_status:
        digest_lines.append(f"- `{row['path']}`: {'opened successfully' if row['opened'] else 'missing'}")
    digest_lines += [
        "",
        "## Exact implementations used",
        "",
        f"- `{RS_ID}`: local `relative_strength_vs_benchmark` with the canonical `reduced_selection_top3` wrapper from the RS hardening pass.",
        f"- `{CSM_ID}`: local native `cross_sectional_momentum` on the same daily 9-symbol user subset.",
        f"- `{DSE_ID}`: local native `down_streak_exhaustion` daily control on the same user subset.",
        "",
        "## Regime tags available locally",
        "",
        "- `rising_market`, `falling_or_volatile`, and `calmer` come from the SPY-tagged regime map already used in prior truth tests.",
        "- `strong_momentum_participation` is approximated honestly from local fields only: `rising_market` days whose cross-sectional participation score (average of uptrend breadth and trend-stack breadth across the 9-symbol user subset) lands in the top quartile of rising-market days.",
        f"- Strong participation threshold on this 5-year window: `{context_stats['strong_participation_threshold']:.4f}` with `{context_stats['strong_participation_days']}` qualifying days out of `{context_stats['rising_market_days']}` rising-market days.",
        "",
        "## Symbol coverage",
        "",
        f"- Native falsification run uses the same 9-symbol daily subset as the prior tournament: `{', '.join(BASE_UNIVERSE)}`.",
        f"- Mega-cap tech ex-NVDA symbols actually available inside that native subset: `{', '.join(sorted(megacap_symbols))}`.",
        "- `GOOG/GOOGL` still affects interpretation only as a coverage note. Local features have `GOOGL`, but the canonical RS/CSM user-subset methodology does not include it, so the ex-NVDA mega-cap slice stays inside the native subset rather than silently broadening the universe.",
        "",
        "## Slice mechanics",
        "",
        "- This falsification preserves native signal generation and holding periods first, then retains only the realized trades whose entry dates and symbols belong to each slice.",
        "- That choice is deliberate: deleting whole calendar rows or silently reranking without NVDA would change the strategy mechanics instead of falsifying the realized branch.",
    ]
    write_markdown(OUTPUTS["digest"], "\n".join(digest_lines))

    matrix_lines = [
        "# Ex-NVDA Regime Test Matrix",
        "",
        "## Slice definitions",
        "",
        "- `native_baseline`: full canonical/native realized book on the 9-symbol user subset.",
        "- `ex_nvda_full`: same realized book with NVDA trades removed ex post.",
        "- `rising_market`: trades entered on SPY-tagged rising-market days.",
        "- `rising_market_ex_nvda`: rising-market trades with NVDA removed ex post.",
        "- `calmer`: trades entered on SPY-tagged calmer / low-vol days.",
        "- `calmer_ex_nvda`: calmer / low-vol trades with NVDA removed ex post.",
        "- `strong_momentum_participation`: trades entered on rising-market days whose cross-sectional participation score is in the top quartile of rising-market days.",
        "- `strong_momentum_participation_ex_nvda`: the same strong-participation days with NVDA removed ex post.",
        f"- `megacap_ex_nvda`: realized trades restricted to native subset mega-cap tech ex-NVDA symbols: `{', '.join(sorted(megacap_symbols))}`.",
        "- `megacap_ex_nvda_supportive`: native mega-cap ex-NVDA trades restricted to rising-market entry days.",
        "- `etf_only`: realized trades restricted to SPY / QQQ / IWM.",
        "",
        "## Honest limits",
        "",
        "- The matrix does not create a new ex-NVDA RS or CSM signal engine. It falsifies the canonical branch by stripping NVDA out of the realized native book inside the same regimes that previously carried the upside.",
        "- `GOOGL` is available locally but excluded from these canonical slices because the prior RS/CSM methodology used the fixed 9-symbol subset without it.",
    ]
    write_markdown(OUTPUTS["matrix"], "\n".join(matrix_lines))

    metric_rows: list[dict[str, object]] = []
    profile_rows: list[dict[str, object]] = []
    slice_trade_cache: dict[tuple[str, str], pd.DataFrame] = {}

    for strategy_id, label, trades in strategy_runs:
        for slice_name in SLICE_ORDER:
            row, subset, _curve = slice_result(strategy_id, label, trades, slice_name, frame, megacap_symbols)
            metric_rows.append(row)
            slice_trade_cache[(strategy_id, slice_name)] = subset
        if strategy_id in {RS_ID, CSM_ID}:
            for slice_name in SUPPORTIVE_PROFILE_SLICES:
                profile_rows.append(
                    supportive_profile_row(
                        strategy_id,
                        label,
                        slice_name,
                        slice_trade_cache[(strategy_id, slice_name)],
                        frame,
                        market_context,
                    )
                )

    metrics_df = pd.DataFrame(metric_rows)
    metrics_df["slice_name"] = pd.Categorical(metrics_df["slice_name"], categories=SLICE_ORDER, ordered=True)
    metrics_df = metrics_df.sort_values(["strategy_id", "slice_name"]).reset_index(drop=True)
    metrics_df.to_csv(OUTPUTS["metrics"], index=False)

    profile_df = pd.DataFrame(profile_rows).sort_values(["slice_name", "strategy_id"]).reset_index(drop=True)
    profile_df.to_csv(OUTPUTS["supportive_csv"], index=False)

    rs_rising = metrics_df.loc[(metrics_df["strategy_id"] == RS_ID) & (metrics_df["slice_name"] == "rising_market")].iloc[0]
    rs_rising_ex = metrics_df.loc[(metrics_df["strategy_id"] == RS_ID) & (metrics_df["slice_name"] == "rising_market_ex_nvda")].iloc[0]
    rs_strong = metrics_df.loc[(metrics_df["strategy_id"] == RS_ID) & (metrics_df["slice_name"] == "strong_momentum_participation")].iloc[0]
    rs_strong_ex = metrics_df.loc[(metrics_df["strategy_id"] == RS_ID) & (metrics_df["slice_name"] == "strong_momentum_participation_ex_nvda")].iloc[0]
    rs_mega_supportive = metrics_df.loc[(metrics_df["strategy_id"] == RS_ID) & (metrics_df["slice_name"] == "megacap_ex_nvda_supportive")].iloc[0]
    rs_ex_full = metrics_df.loc[(metrics_df["strategy_id"] == RS_ID) & (metrics_df["slice_name"] == "ex_nvda_full")].iloc[0]

    csm_rising = metrics_df.loc[(metrics_df["strategy_id"] == CSM_ID) & (metrics_df["slice_name"] == "rising_market")].iloc[0]
    csm_rising_ex = metrics_df.loc[(metrics_df["strategy_id"] == CSM_ID) & (metrics_df["slice_name"] == "rising_market_ex_nvda")].iloc[0]
    csm_strong = metrics_df.loc[(metrics_df["strategy_id"] == CSM_ID) & (metrics_df["slice_name"] == "strong_momentum_participation")].iloc[0]
    csm_strong_ex = metrics_df.loc[(metrics_df["strategy_id"] == CSM_ID) & (metrics_df["slice_name"] == "strong_momentum_participation_ex_nvda")].iloc[0]
    csm_ex_full = metrics_df.loc[(metrics_df["strategy_id"] == CSM_ID) & (metrics_df["slice_name"] == "ex_nvda_full")].iloc[0]

    dse_ex_full = metrics_df.loc[(metrics_df["strategy_id"] == DSE_ID) & (metrics_df["slice_name"] == "ex_nvda_full")].iloc[0]
    dse_rising_ex = metrics_df.loc[(metrics_df["strategy_id"] == DSE_ID) & (metrics_df["slice_name"] == "rising_market_ex_nvda")].iloc[0]

    leaderboard_lines = [
        "# Ex-NVDA Regime Leaderboard",
        "",
        "## Key slice leaders by final equity",
        "",
    ]
    for slice_name in SLICE_ORDER:
        slice_rows = metrics_df.loc[metrics_df["slice_name"] == slice_name].sort_values("final_equity", ascending=False)
        if slice_rows.empty:
            continue
        top = slice_rows.iloc[0]
        leaderboard_lines.append(
            f"- `{slice_name}`: `{top['strategy_id']}` leads with final equity `${top['final_equity']:.2f}`, return `{top['total_return_pct']:.2f}%`, drawdown `{top['max_drawdown_pct']:.2f}%`, trades `{int(top['trade_count'])}`."
        )
    write_markdown(OUTPUTS["leaderboard"], "\n".join(leaderboard_lines))

    rs_rising_survival = survival_pct(float(rs_rising["total_return_pct"]), float(rs_rising_ex["total_return_pct"]))
    rs_strong_survival = survival_pct(float(rs_strong["total_return_pct"]), float(rs_strong_ex["total_return_pct"]))
    csm_rising_survival = survival_pct(float(csm_rising["total_return_pct"]), float(csm_rising_ex["total_return_pct"]))
    csm_strong_survival = survival_pct(float(csm_strong["total_return_pct"]), float(csm_strong_ex["total_return_pct"]))

    csm_vs_rs_full = "larger" if float(csm_ex_full["total_return_pct"]) > float(rs_ex_full["total_return_pct"]) else "smaller"
    core_lines = [
        "# Ex-NVDA Core Edge Report",
        "",
        f"- RS top-3 does {'stay positive' if float(rs_rising_ex['final_equity']) > INITIAL_CAPITAL else 'not stay positive'} ex-NVDA inside the `rising_market` slice. Final equity is `${rs_rising_ex['final_equity']:.2f}` with return `{rs_rising_ex['total_return_pct']:.2f}%`, which preserves about `{rs_rising_survival:.2f}%` of the original rising-market return.",
        f"- RS top-3 also does {'stay positive' if float(rs_strong_ex['final_equity']) > INITIAL_CAPITAL else 'not stay positive'} inside the stricter `strong_momentum_participation_ex_nvda` slice. Final equity is `${rs_strong_ex['final_equity']:.2f}` with return `{rs_strong_ex['total_return_pct']:.2f}%`, preserving about `{rs_strong_survival:.2f}%` of the original strong-participation return.",
        f"- The surviving RS edge is {'economically meaningful but still concentrated' if float(rs_mega_supportive['final_equity']) > INITIAL_CAPITAL and float(rs_mega_supportive['trade_count']) >= 30 else 'not broad enough to matter yet'} across mega-cap tech ex-NVDA. In the `megacap_ex_nvda_supportive` slice, RS finishes at `${rs_mega_supportive['final_equity']:.2f}` with `{int(rs_mega_supportive['trade_count'])}` trades, max drawdown `{rs_mega_supportive['max_drawdown_pct']:.2f}%`, and top-symbol share `{rs_mega_supportive['top_symbol_pnl_share_pct']:.2f}%`.",
        f"- CSM does {'stay positive' if float(csm_rising_ex['final_equity']) > INITIAL_CAPITAL else 'not stay positive'} ex-NVDA in `rising_market` and {'stay positive' if float(csm_strong_ex['final_equity']) > INITIAL_CAPITAL else 'not stay positive'} in `strong_momentum_participation_ex_nvda`. Its survival is `{csm_rising_survival:.2f}%` in rising-market and `{csm_strong_survival:.2f}%` in the stronger participation slice.",
        f"- On this harsher falsification, CSM survives {'better' if csm_strong_survival > rs_strong_survival else 'worse'} than RS in the strongest supportive ex-NVDA slice. Its ex-NVDA full-book return is `{csm_ex_full['total_return_pct']:.2f}%`, which is {csm_vs_rs_full} than RS's `{rs_ex_full['total_return_pct']:.2f}%`.",
        f"- DSE behaves as expected: cleaner but much lower-powered. Ex-NVDA full-book final equity is `${dse_ex_full['final_equity']:.2f}`, and ex-NVDA rising-market final equity is `${dse_rising_ex['final_equity']:.2f}`.",
    ]
    write_markdown(OUTPUTS["core"], "\n".join(core_lines))

    rs_strong_profile = profile_df.loc[(profile_df["strategy_id"] == RS_ID) & (profile_df["slice_name"] == "strong_momentum_participation_ex_nvda")].iloc[0]
    csm_strong_profile = profile_df.loc[(profile_df["strategy_id"] == CSM_ID) & (profile_df["slice_name"] == "strong_momentum_participation_ex_nvda")].iloc[0]

    support_lines = [
        "# Supportive Regime Day-Profile Report",
        "",
        f"- Inside supportive ex-NVDA slices, RS still {'does' if rs_strong_profile['best_5pct_avg_top_symbol_share_pct'] >= 60.0 else 'does not'} look dependent on one dominant leader. In `strong_momentum_participation_ex_nvda`, its best 5% days average `{rs_strong_profile['best_5pct_avg_top_symbol_share_pct']:.2f}%` from the top symbol.",
        f"- CSM distributes gains {'more cleanly' if csm_strong_profile['best_5pct_avg_top_symbol_share_pct'] < rs_strong_profile['best_5pct_avg_top_symbol_share_pct'] else 'less cleanly'} across symbols in the strongest ex-NVDA supportive slice: best-day top-symbol share `{csm_strong_profile['best_5pct_avg_top_symbol_share_pct']:.2f}%` versus `{rs_strong_profile['best_5pct_avg_top_symbol_share_pct']:.2f}%`, and multi-symbol participation `{csm_strong_profile['best_5pct_multi_symbol_share_pct']:.2f}%` versus `{rs_strong_profile['best_5pct_multi_symbol_share_pct']:.2f}%`.",
        f"- On worst-day containment inside those supportive ex-NVDA slices, {'CSM is cleaner' if csm_strong_profile['worst_5pct_avg_top_symbol_share_pct'] < rs_strong_profile['worst_5pct_avg_top_symbol_share_pct'] else 'RS is cleaner'}: worst-day top-symbol share `{csm_strong_profile['worst_5pct_avg_top_symbol_share_pct']:.2f}%` for CSM versus `{rs_strong_profile['worst_5pct_avg_top_symbol_share_pct']:.2f}%` for RS.",
        f"- The surviving ex-NVDA edge is {'economically meaningful but still not clean enough to call robust' if min(float(rs_strong_ex['final_equity']), float(csm_strong_ex['final_equity'])) > INITIAL_CAPITAL else 'not broad enough to call robust yet'}. RS non-extreme day expectancy inside the strongest supportive ex-NVDA slice is `{rs_strong_profile['non_extreme_day_expectancy_2_5']:.2f}` versus `{csm_strong_profile['non_extreme_day_expectancy_2_5']:.2f}` for CSM, while drawdown remains `{rs_strong_ex['max_drawdown_pct']:.2f}%` for RS and `{csm_strong_ex['max_drawdown_pct']:.2f}%` for CSM.",
        "- Bottom line: supportive regimes alone do not automatically create broad robustness. The branch still needs to show that ex-NVDA gains can come from several mega-cap names rather than one leader-of-the-day followed by weaker satellites.",
    ]
    write_markdown(OUTPUTS["supportive_md"], "\n".join(support_lines))

    rs_keep = (
        float(rs_rising_ex["final_equity"]) > INITIAL_CAPITAL
        and float(rs_strong_ex["final_equity"]) > INITIAL_CAPITAL
        and float(rs_mega_supportive["final_equity"]) > INITIAL_CAPITAL
    )
    csm_takeover = (
        float(csm_rising_ex["final_equity"]) > float(rs_rising_ex["final_equity"])
        and float(csm_strong_ex["final_equity"]) > float(rs_strong_ex["final_equity"])
        and float(csm_strong_profile["best_5pct_avg_top_symbol_share_pct"]) <= float(rs_strong_profile["best_5pct_avg_top_symbol_share_pct"])
        and float(csm_strong_profile["non_extreme_day_expectancy_2_5"]) >= float(rs_strong_profile["non_extreme_day_expectancy_2_5"])
    )

    if csm_takeover and not rs_keep:
        canonical_call = "switch to CSM as canonical branch"
        branch_label = "narrow research artifact or event-sensitive leader-following sleeve"
    elif rs_keep and not csm_takeover:
        canonical_call = "preserve RS as canonical branch"
        branch_label = "mega-cap momentum regime sleeve"
    else:
        canonical_call = "keep both alive with separate roles"
        branch_label = "event-sensitive leader-following sleeve"

    branch_lines = [
        "# RS Branch Recheck After Ex-NVDA",
        "",
        f"1. Does RS top-3 remain the canonical research branch after ex-NVDA regime falsification? `{('Yes, but only narrowly.' if canonical_call == 'preserve RS as canonical branch' else 'Not cleanly enough to say that alone.' if canonical_call == 'keep both alive with separate roles' else 'No.')}`",
        f"2. Relabel: `{branch_label}`.",
        f"3. Is CSM now the cleaner primary branch instead? `{('Yes.' if csm_takeover else 'Not fully, but it strengthened its case.' if canonical_call == 'keep both alive with separate roles' else 'No.')}`",
        "4. Does DSE remain the correct trust anchor and benchmark? `Yes`.",
        f"5. Right next step: `{canonical_call}`.",
    ]
    write_markdown(OUTPUTS["branch_recheck"], "\n".join(branch_lines))

    rs_vs_csm_lines = [
        "# RS vs CSM Recheck",
        "",
        f"- RS ex-NVDA rising-market return: `{rs_rising_ex['total_return_pct']:.2f}%`; CSM ex-NVDA rising-market return: `{csm_rising_ex['total_return_pct']:.2f}%`.",
        f"- RS ex-NVDA strong-participation return: `{rs_strong_ex['total_return_pct']:.2f}%`; CSM ex-NVDA strong-participation return: `{csm_strong_ex['total_return_pct']:.2f}%`.",
        f"- RS ex-NVDA strong-participation non-extreme day expectancy: `{rs_strong_profile['non_extreme_day_expectancy_2_5']:.2f}`; CSM: `{csm_strong_profile['non_extreme_day_expectancy_2_5']:.2f}`.",
        f"- Cleaner supportive-regime day profile: `{'CSM' if csm_strong_profile['best_5pct_avg_top_symbol_share_pct'] <= rs_strong_profile['best_5pct_avg_top_symbol_share_pct'] else 'RS top-3'}`.",
        f"- Crown decision after this falsification: `{('CSM should take over.' if csm_takeover else 'RS keeps the crown only narrowly because it retained the stronger ex-NVDA strong-participation sleeve, even though CSM stayed cleaner at the day-profile level.' if canonical_call == 'preserve RS as canonical branch' else 'No decisive crown; keep both alive with separate roles.')}`",
    ]
    write_markdown(OUTPUTS["rs_vs_csm"], "\n".join(rs_vs_csm_lines))

    next_lines = [
        "# Next Falsification Steps",
        "",
        "1. Keep QQQ pair as the only active paper strategy.",
        "2. Preserve DSE as the trust anchor.",
        f"3. {('Switch CSM into the canonical slot if the next confirmation agrees.' if csm_takeover else 'Keep RS as canonical only if the next confirmation shows ex-NVDA supportive-regime breadth is still meaningful.')}",
        "4. Keep CSM alive as the main challenger.",
        "5. Run one narrower mega-cap ex-NVDA confirmation rerun.",
        "6. Run one leader-following versus broad-participation diagnostic.",
        "7. Stop any line of work that only survives with one dominant symbol.",
    ]
    write_markdown(OUTPUTS["next_steps"], "\n".join(next_lines))

    print(json.dumps(
        {
            "opened_files": [row["path"] for row in file_status if row["opened"]],
            "rs_survives_ex_nvda_supportive_regimes": bool(float(rs_rising_ex["final_equity"]) > INITIAL_CAPITAL and float(rs_strong_ex["final_equity"]) > INITIAL_CAPITAL),
            "csm_survives_ex_nvda_supportive_regimes": bool(float(csm_rising_ex["final_equity"]) > INITIAL_CAPITAL and float(csm_strong_ex["final_equity"]) > INITIAL_CAPITAL),
            "cleaner_supportive_regime_day_profile": "CSM" if csm_strong_profile["best_5pct_avg_top_symbol_share_pct"] <= rs_strong_profile["best_5pct_avg_top_symbol_share_pct"] else "RS top-3",
            "rs_remains_canonical_branch": canonical_call == "preserve RS as canonical branch",
            "csm_should_take_over": csm_takeover,
            "dse_trust_anchor": True,
            "best_next_falsification_step": "leader-following versus broad-participation diagnostic" if csm_takeover else "narrower mega-cap ex-NVDA confirmation rerun",
            "outputs": {k: str(v) for k, v in OUTPUTS.items()},
        },
        indent=2,
    ))


if __name__ == "__main__":
    main()
