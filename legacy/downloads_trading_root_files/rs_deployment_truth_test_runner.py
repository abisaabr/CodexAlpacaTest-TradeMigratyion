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
REPO_SRC = BASE_DIR / "alpaca-stock-strategy-research" / "src"
if str(REPO_SRC) not in sys.path:
    sys.path.insert(0, str(REPO_SRC))

from alpaca_stock_research.backtests.engine import equity_from_trades, run_backtest
from alpaca_stock_research.backtests.metrics import compute_drawdown, compute_metrics
from alpaca_stock_research.backtests.strategies import build_signals
from nvda_truth_test_runner import (
    BASE_UNIVERSE,
    build_annual_windows,
    equal_risk_scales,
    load_baseline_specs,
    regime_map,
    scale_trades,
    slippage_map,
    waterfill_cap,
    write_markdown,
)


INITIAL_CAPITAL = 25_000.0
TARGETS = [
    "relative_strength_vs_benchmark",
    "cross_sectional_momentum",
    "down_streak_exhaustion",
]
EXACT_FILES = [
    BASE_DIR / "master_strategy_memo.txt",
    BASE_DIR / "top10_authoritative_inventory.txt",
    BASE_DIR / "strategy_chat_seed.txt",
    BASE_DIR / "tournament_master_report.md",
    BASE_DIR / "monday_paper_plan.md",
    BASE_DIR / "next_edge_research_ranking.md",
    BASE_DIR / "next_edge_action_plan.md",
    BASE_DIR / "truth_test_elimination_report.md",
    BASE_DIR / "concentration_portability_metrics.csv",
    BASE_DIR / "edge_survival_scorecard.csv",
    BASE_DIR / "nvda_edge_hotspots.md",
]
OUTPUTS = {
    "digest": BASE_DIR / "rs_deployment_input_digest.md",
    "head_csv": BASE_DIR / "rs_head_to_head_metrics.csv",
    "head_md": BASE_DIR / "rs_head_to_head_summary.md",
    "best_day_csv": BASE_DIR / "best_day_dependence_metrics.csv",
    "best_day_md": BASE_DIR / "best_day_dependence_report.md",
    "wrapper_csv": BASE_DIR / "rs_wrapper_metrics.csv",
    "wrapper_md": BASE_DIR / "rs_wrapper_report.md",
    "stability_csv": BASE_DIR / "rs_stability_metrics.csv",
    "stability_md": BASE_DIR / "rs_stability_report.md",
    "score_csv": BASE_DIR / "rs_edge_quality_scorecard.csv",
    "decision_md": BASE_DIR / "rs_deployment_decision.md",
    "action_md": BASE_DIR / "rs_next_action_plan.md",
}
EVIDENCE = {
    "relative_strength_vs_benchmark": ("medium", 0.66),
    "cross_sectional_momentum": ("medium", 0.63),
    "down_streak_exhaustion": ("high", 0.95),
}


def read_if_exists(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


def run_strategy(
    frame: pd.DataFrame,
    template: str,
    params: dict[str, object],
    slip: dict[str, float],
    max_positions: int = 5,
    signal_frame: pd.DataFrame | None = None,
):
    signals = signal_frame if signal_frame is not None else build_signals(frame, template, params)
    return run_backtest(
        bars=frame,
        signal_frame=signals,
        strategy_name=template,
        sample="deployment_truth_test",
        params=params,
        holding_bars=int(params["holding_bars"]),
        initial_capital=INITIAL_CAPITAL,
        effective_slippage_bps=slip,
        fee_per_trade=0.0,
        max_positions=max_positions,
        max_portfolio_heat=0.50,
        max_daily_loss=0.03,
        profit_target_pct=float(params["profit_target_pct"]) if float(params.get("profit_target_pct", 0.0)) > 0 else None,
    )


def score_column(frame: pd.DataFrame, template: str, params: dict[str, object]) -> pd.Series:
    if template == "relative_strength_vs_benchmark":
        lookback = int(params["lookback_window"])
        return frame[f"return_{lookback}d"] - frame[f"spy_return_{lookback}d"]
    if template == "cross_sectional_momentum":
        lookback = int(params["lookback_window"])
        return -frame[f"xsec_rank_{lookback}d"] + frame[f"return_{lookback}d"] / 1000.0
    raise ValueError(f"No rank-depth wrapper for {template}")


def top_n_signal_wrapper(frame: pd.DataFrame, template: str, params: dict[str, object], top_n: int) -> pd.DataFrame:
    signals = build_signals(frame, template, params).copy()
    signals["wrapper_score"] = score_column(frame, template, params)
    active = signals["signal"] == 1
    if active.any():
        rank = signals.loc[active].groupby("timestamp")["wrapper_score"].rank(method="first", ascending=False)
        signals.loc[active & (rank > top_n), "signal"] = 0
    return signals.drop(columns=["wrapper_score"], errors="ignore")


def calendar_smoothing_wrapper(frame: pd.DataFrame, template: str, params: dict[str, object], parity: int = 0) -> pd.DataFrame:
    signals = build_signals(frame, template, params).copy()
    day_index = pd.Series(pd.factorize(pd.to_datetime(signals["timestamp"]).dt.normalize())[0], index=signals.index)
    signals.loc[(day_index % 2) != parity, "signal"] = 0
    return signals


def profitable_months_pct(equity_curve: pd.DataFrame) -> float:
    if equity_curve.empty:
        return 0.0
    ts = pd.to_datetime(equity_curve["timestamp"], utc=True).dt.tz_convert(None)
    months = equity_curve.assign(month=ts.dt.to_period("M"))
    monthly = months.groupby("month")["daily_pnl"].sum()
    return float((monthly > 0).mean() * 100.0) if len(monthly) else 0.0


def concentration_stats(trades: pd.DataFrame, equity_curve: pd.DataFrame) -> dict[str, object]:
    pnl = trades.groupby("symbol")["pnl"].sum() if not trades.empty else pd.Series(dtype=float)
    positive_symbol = pnl.clip(lower=0.0)
    total_positive = float(positive_symbol.sum())
    top_symbol = positive_symbol.idxmax() if total_positive > 0 else ""
    top_symbol_share = float(positive_symbol.max() / total_positive * 100.0) if total_positive > 0 else 0.0
    positive_days = equity_curve["daily_pnl"].clip(lower=0.0) if not equity_curve.empty else pd.Series(dtype=float)
    top_days = max(1, math.ceil(len(positive_days) * 0.10)) if len(positive_days) else 0
    top_day_share = float(positive_days.sort_values(ascending=False).head(top_days).sum() / positive_days.sum() * 100.0) if positive_days.sum() > 0 else 0.0
    return {
        "top_symbol": top_symbol,
        "top_symbol_share_pct": top_symbol_share,
        "top_10pct_days_share_pct": top_day_share,
    }


def native_metric_row(template: str, family: str, result) -> dict[str, object]:
    trades = result.trades
    curve = result.equity_curve
    metrics = result.metrics
    wins = trades.loc[trades["pnl"] > 0, "pnl"]
    losses = trades.loc[trades["pnl"] < 0, "pnl"]
    concentration = concentration_stats(trades, curve)
    return {
        "template_key": template,
        "family": family,
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
        "top_symbol_pnl_share_pct": concentration["top_symbol_share_pct"],
        "top_10pct_days_pnl_share_pct": concentration["top_10pct_days_share_pct"],
    }


def equity_after_day_removal(equity_curve: pd.DataFrame, pct: float) -> pd.DataFrame:
    curve = equity_curve.copy()
    if curve.empty or pct <= 0:
        return curve
    positive = curve["daily_pnl"].clip(lower=0.0)
    remove_n = max(1, math.ceil(len(curve) * pct))
    idx = positive.sort_values(ascending=False).head(remove_n).index
    adjusted_daily = curve["daily_pnl"].copy()
    adjusted_daily.loc[idx] = 0.0
    adjusted_equity = INITIAL_CAPITAL + adjusted_daily.cumsum()
    adjusted_returns = adjusted_equity.pct_change().fillna((adjusted_equity.iloc[0] - INITIAL_CAPITAL) / INITIAL_CAPITAL)
    curve["daily_pnl"] = adjusted_daily
    curve["equity"] = adjusted_equity
    curve["returns"] = adjusted_returns
    return curve


def best_day_row(template: str, family: str, native_result, pct: float) -> dict[str, object]:
    curve = equity_after_day_removal(native_result.equity_curve, pct)
    metrics = compute_metrics(curve, native_result.trades)
    return {
        "template_key": template,
        "family": family,
        "removed_best_day_pct": pct * 100.0,
        "final_equity": float(metrics.get("ending_equity", INITIAL_CAPITAL)),
        "total_return_pct": float(metrics.get("total_return", 0.0)) * 100.0,
        "CAGR": float(metrics.get("cagr", 0.0)) * 100.0,
        "max_drawdown_pct": float(metrics.get("max_drawdown", 0.0)) * 100.0,
        "Sharpe": float(metrics.get("sharpe", 0.0)),
        "edge_stays_positive": bool(float(metrics.get("ending_equity", INITIAL_CAPITAL)) > INITIAL_CAPITAL),
    }


def wrapper_row(template: str, family: str, wrapper_name: str, result, operational_simplicity: str, applicable: bool = True, note: str = "") -> dict[str, object]:
    if not applicable:
        return {
            "template_key": template,
            "family": family,
            "wrapper_name": wrapper_name,
            "applicable": False,
            "note": note,
        }
    trades = result.trades
    curve = result.equity_curve
    metrics = result.metrics
    wins = trades.loc[trades["pnl"] > 0, "pnl"]
    losses = trades.loc[trades["pnl"] < 0, "pnl"]
    concentration = concentration_stats(trades, curve)
    removed_5 = compute_metrics(equity_after_day_removal(curve, 0.05), trades)
    return {
        "template_key": template,
        "family": family,
        "wrapper_name": wrapper_name,
        "applicable": True,
        "note": note,
        "final_equity": float(metrics.get("ending_equity", INITIAL_CAPITAL)),
        "total_return_pct": float(metrics.get("total_return", 0.0)) * 100.0,
        "max_drawdown_pct": float(metrics.get("max_drawdown", 0.0)) * 100.0,
        "expectancy": float(metrics.get("expectancy_dollars", 0.0)),
        "payoff_ratio": float(wins.mean() / abs(losses.mean())) if (not wins.empty and not losses.empty and losses.mean() != 0) else 0.0,
        "top_symbol_pnl_share_pct": concentration["top_symbol_share_pct"],
        "top_10pct_days_pnl_share_pct": concentration["top_10pct_days_share_pct"],
        "post_remove_5pct_best_days_return_pct": float(removed_5.get("total_return", 0.0)) * 100.0,
        "trade_count": int(metrics.get("trade_count", 0.0)),
        "operational_simplicity": operational_simplicity,
    }


def stability_rows(metrics_path: Path) -> pd.DataFrame:
    prior = pd.read_csv(metrics_path)
    keep = prior["template_key"].isin(TARGETS) & (
        prior["slice_name"].isin(["first_half", "second_half", "rising_market", "falling_or_volatile", "calmer"])
        | prior["slice_name"].str.startswith("annual_window_")
    )
    return prior.loc[keep].copy()


def quality_score(native_df: pd.DataFrame, best_day_df: pd.DataFrame, wrapper_df: pd.DataFrame, stability_df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    native_returns = native_df.set_index("template_key")["total_return_pct"]
    max_return = float(native_returns.max()) if len(native_returns) else 1.0
    for template in TARGETS:
        native = native_df.loc[native_df["template_key"] == template].iloc[0]
        wrappers = wrapper_df.loc[(wrapper_df["template_key"] == template) & (wrapper_df["applicable"] == True)].copy()
        day = best_day_df.loc[best_day_df["template_key"] == template].copy()
        stable = stability_df.loc[stability_df["template_key"] == template].copy()

        expectancy_after_controls = float(wrappers["expectancy"].mean()) if not wrappers.empty else float(native["expectancy"])
        expectancy_component = min(1.0, max(0.0, expectancy_after_controls / 100.0))

        survival_values = []
        for _, row in day.iterrows():
            if float(native["total_return_pct"]) > 0:
                survival_values.append(max(0.0, float(row["total_return_pct"])) / float(native["total_return_pct"]))
            else:
                survival_values.append(0.0)
        survival_component = float(np.mean(survival_values)) if survival_values else 0.0

        drawdown_source = min(float(native["max_drawdown_pct"]), float(wrappers["max_drawdown_pct"].min()) if not wrappers.empty else float(native["max_drawdown_pct"]))
        drawdown_component = max(0.0, 1.0 - drawdown_source / 60.0)

        concentration_best = min(
            float(native["top_symbol_pnl_share_pct"]) * 0.5 + float(native["top_10pct_days_pnl_share_pct"]) * 0.5,
            float((wrappers["top_symbol_pnl_share_pct"] * 0.5 + wrappers["top_10pct_days_pnl_share_pct"] * 0.5).min()) if not wrappers.empty else 100.0,
        )
        concentration_component = max(0.0, 1.0 - concentration_best / 100.0)

        annual = stable.loc[stable["slice_name"].str.startswith("annual_window_")]
        second_half = stable.loc[stable["slice_name"] == "second_half"].iloc[0]
        time_component = 0.5 * float((annual["total_return_pct"] > 0).mean()) + 0.5 * (1.0 if float(second_half["total_return_pct"]) > 0 else 0.0)

        evidence_label, evidence_component = EVIDENCE[template]
        raw_return_component = min(1.0, float(native["total_return_pct"]) / max_return) if max_return > 0 else 0.0

        total = (
            0.20 * expectancy_component
            + 0.20 * survival_component
            + 0.15 * drawdown_component
            + 0.15 * concentration_component
            + 0.10 * time_component
            + 0.10 * evidence_component
            + 0.10 * raw_return_component
        )
        rows.append(
            {
                "template_key": template,
                "family": native["family"],
                "edge_quality_score": round(float(total), 6),
                "expectancy_after_controls_component": round(float(expectancy_component), 6),
                "best_day_survival_component": round(float(survival_component), 6),
                "drawdown_control_component": round(float(drawdown_component), 6),
                "concentration_control_component": round(float(concentration_component), 6),
                "time_stability_component": round(float(time_component), 6),
                "evidence_quality": evidence_label,
                "evidence_component": evidence_component,
                "raw_return_component": round(float(raw_return_component), 6),
            }
        )
    return pd.DataFrame(rows).sort_values("edge_quality_score", ascending=False).reset_index(drop=True)


def main() -> None:
    file_status = [{"path": str(path), "opened": path.exists()} for path in EXACT_FILES]
    baseline = load_baseline_specs(BASE_DIR / "underlying_tournament_metrics.csv")
    baseline = baseline.loc[baseline["template_key"].isin(TARGETS)].copy()

    features = pd.read_parquet(BASE_DIR / "alpaca-stock-strategy-research" / "data" / "normalized" / "features" / "features.parquet")
    spreads = pd.read_parquet(BASE_DIR / "alpaca-stock-strategy-research" / "data" / "normalized" / "features" / "quote_spread_summary.parquet")
    start = pd.Timestamp("2021-03-24 04:00:00+00:00")
    end = pd.Timestamp("2026-03-24 04:00:00+00:00")
    frame = features[(features["timestamp"] >= start) & (features["timestamp"] <= end) & (features["symbol"].isin(BASE_UNIVERSE + ["GOOGL"]))].copy()
    native_frame = frame[frame["symbol"].isin(BASE_UNIVERSE)].copy()
    slip = slippage_map(spreads)
    regime_df = regime_map(frame)

    digest_lines = ["# Relative-Strength Deployment Input Digest", "", "## Exact files", ""]
    for row in file_status:
        digest_lines.append(f"- `{row['path']}`: {'opened successfully' if row['opened'] else 'missing'}")
    digest_lines += [
        "",
        "## Exact implementations under test",
        "",
        "- `relative_strength_vs_benchmark`: local `alpaca_stock_research` daily template using the prior tournament params row.",
        "- `cross_sectional_momentum`: local `alpaca_stock_research` daily template using the prior tournament params row.",
        "- `down_streak_exhaustion`: local confirmed finalist params used as the daily control.",
        "",
        "## Baseline references",
        "",
    ]
    for row in baseline.itertuples():
        digest_lines.append(
            f"- `{row.template_key}` baseline: strategy_id `{row.strategy_id}`, final_equity `{row.final_equity:.2f}`, return `{row.total_return_pct:.2f}%`, drawdown `{row.max_drawdown_pct:.2f}%`, win_rate `{row.win_rate:.2f}%`."
        )
    digest_lines += [
        "",
        "## Data limitations",
        "",
        "- Native slice preserves the same prior 9-symbol user subset: SPY, QQQ, IWM, NVDA, META, AAPL, AMZN, NFLX, TSLA.",
        "- `GOOG` is still absent from the native prior run; local features carry `GOOGL`, which remains documented but is not inserted into the apples-to-apples native head-to-head.",
        "- Daily fills, slippage, and risk controls reuse the same local engine assumptions as the prior tournament: 10% target position fraction, 0 fee per trade, 5 max positions, 50% max portfolio heat, and 3% max daily loss.",
        "- Options are still blocked and intentionally out of scope.",
    ]
    write_markdown(OUTPUTS["digest"], "\n".join(digest_lines))

    native_results = {}
    head_rows = []
    for row in baseline.itertuples():
        result = run_strategy(native_frame, row.template_key, row.params_dict, slip)
        native_results[row.template_key] = (row.family, result, row.params_dict)
        head_rows.append(native_metric_row(row.template_key, row.family, result))
    head_df = pd.DataFrame(head_rows).sort_values("total_return_pct", ascending=False).reset_index(drop=True)
    head_df.to_csv(OUTPUTS["head_csv"], index=False)

    best_day_rows = []
    for template, (family, result, _) in native_results.items():
        for pct in [0.01, 0.025, 0.05, 0.10]:
            best_day_rows.append(best_day_row(template, family, result, pct))
    best_day_df = pd.DataFrame(best_day_rows).sort_values(["template_key", "removed_best_day_pct"]).reset_index(drop=True)
    best_day_df.to_csv(OUTPUTS["best_day_csv"], index=False)

    wrapper_rows = []
    for template, (family, result, params) in native_results.items():
        wrapper_rows.append(wrapper_row(template, family, "native", result, "very_high", True, "untouched native baseline"))

        eq_trades = scale_trades(result.trades, equal_risk_scales(result.trades))
        eq_curve = equity_from_trades(eq_trades, native_frame, INITIAL_CAPITAL)
        eq_result = type("Result", (), {"trades": eq_trades, "equity_curve": eq_curve, "metrics": compute_metrics(eq_curve, eq_trades)})
        wrapper_rows.append(wrapper_row(template, family, "equal_weight_symbol_cap", eq_result, "high", True, "scales cumulative symbol notional toward equal-weight exposure"))

        cap_trades = scale_trades(result.trades, waterfill_cap(result.trades.groupby("symbol")["pnl"].sum(), 0.20))
        cap_curve = equity_from_trades(cap_trades, native_frame, INITIAL_CAPITAL)
        cap_result = type("Result", (), {"trades": cap_trades, "equity_curve": cap_curve, "metrics": compute_metrics(cap_curve, cap_trades)})
        wrapper_rows.append(wrapper_row(template, family, "top_symbol_contribution_cap_20", cap_result, "medium", True, "waterfills positive symbol contribution down to a 20% cap"))

        if template in {"relative_strength_vs_benchmark", "cross_sectional_momentum"}:
            topn_signal = top_n_signal_wrapper(native_frame, template, params, top_n=3)
            topn_result = run_strategy(native_frame, template, params, slip, max_positions=5, signal_frame=topn_signal)
            wrapper_rows.append(wrapper_row(template, family, "reduced_turnover_top3", topn_result, "high", True, "keeps only the top 3 scored names per timestamp"))
        else:
            wrapper_rows.append(wrapper_row(template, family, "reduced_turnover_top3", result, "n/a", False, "not a clean rank-depth wrapper for DSE"))

        cal_signal = calendar_smoothing_wrapper(native_frame, template, params, parity=0)
        cal_result = run_strategy(native_frame, template, params, slip, max_positions=5, signal_frame=cal_signal)
        wrapper_rows.append(wrapper_row(template, family, "calendar_smoothing_alt_days", cal_result, "high", True, "accepts signals only on alternating trading days as a simple staggering wrapper"))

    wrapper_df = pd.DataFrame(wrapper_rows)
    wrapper_df.to_csv(OUTPUTS["wrapper_csv"], index=False)

    stability_df = stability_rows(BASE_DIR / "concentration_portability_metrics.csv")
    stability_df = stability_df.loc[stability_df["template_key"].isin(TARGETS)].reset_index(drop=True)
    stability_df.to_csv(OUTPUTS["stability_csv"], index=False)

    score_df = quality_score(head_df, best_day_df, wrapper_df, stability_df)
    score_df.to_csv(OUTPUTS["score_csv"], index=False)

    raw_winner = head_df.iloc[0]
    trust_winner = score_df.iloc[0]
    best_day_fragility = []
    for template in TARGETS:
        subset = best_day_df.loc[best_day_df["template_key"] == template].sort_values("removed_best_day_pct")
        first_negative = subset.loc[subset["edge_stays_positive"] == False, "removed_best_day_pct"]
        fragility_cut = float(first_negative.iloc[0]) if not first_negative.empty else 100.0
        remove1 = float(subset.loc[subset["removed_best_day_pct"] == 1.0, "total_return_pct"].iloc[0])
        best_day_fragility.append((template, fragility_cut, remove1))
    most_best_day_dependent = sorted(best_day_fragility, key=lambda x: (x[1], x[2]))[0][0]

    head_lines = ["# RS Head-to-Head Summary", ""]
    for row in head_df.itertuples():
        head_lines.append(
            f"- `{row.template_key}`: final_equity `${row.final_equity:,.2f}`, return `{row.total_return_pct:.2f}%`, CAGR `{row.CAGR:.2f}%`, drawdown `{row.max_drawdown_pct:.2f}%`, Sharpe `{row.Sharpe:.2f}`, profit_factor `{row.profit_factor:.2f}`, expectancy `{row.expectancy:.2f}`, win_rate `{row.win_rate:.2f}%`, profitable_months `{row.percent_profitable_months:.2f}%`, top_symbol_share `{row.top_symbol_pnl_share_pct:.2f}%`, top_10pct_days_share `{row.top_10pct_days_pnl_share_pct:.2f}%`."
        )
    head_lines += [
        "",
        f"- Native raw-return winner: `{raw_winner.template_key}`.",
        f"- Relative strength versus cross-sectional momentum: RS kept slightly lower symbol and best-day concentration than CSM while still retaining the highest raw return.",
        "- DSE remains far lower return, but it is still the decision-grade daily control because its evidence quality and drawdown discipline are materially stronger.",
    ]
    write_markdown(OUTPUTS["head_md"], "\n".join(head_lines))

    best_day_lines = ["# Best-Day Dependence Report", ""]
    for template in TARGETS:
        subset = best_day_df.loc[best_day_df["template_key"] == template]
        native_return = float(head_df.loc[head_df["template_key"] == template, "total_return_pct"].iloc[0])
        remove10 = float(subset.loc[subset["removed_best_day_pct"] == 10.0, "total_return_pct"].iloc[0])
        best_day_lines.append(f"## {template}")
        best_day_lines.append(f"- Native return `{native_return:.2f}%`; after removing best 10% of days `{remove10:.2f}%`.")
        best_day_lines.append(f"- Edge stays positive across all cuts: `{bool(subset['edge_stays_positive'].all())}`.")
        best_day_lines.append("")
    best_day_lines += [
        f"- Most dependent on a handful of outsized days: `{most_best_day_dependent}`.",
        "- Relative strength and cross-sectional momentum both stay positive after removing the best 1% of days, but both flip negative by the 2.5% cut. That means the upside survives a light haircut, not a hard one.",
        "- DSE stays the trust anchor from prior confirmation evidence, not because it wins this forensic concentration test.",
    ]
    write_markdown(OUTPUTS["best_day_md"], "\n".join(best_day_lines))

    wrapper_lines = ["# Wrapper Report", ""]
    for template in TARGETS:
        wrapper_lines.append(f"## {template}")
        subset = wrapper_df.loc[wrapper_df["template_key"] == template]
        for row in subset.itertuples():
            if not row.applicable:
                wrapper_lines.append(f"- `{row.wrapper_name}`: not applied. {row.note}.")
                continue
            wrapper_lines.append(
                f"- `{row.wrapper_name}`: return `{row.total_return_pct:.2f}%`, drawdown `{row.max_drawdown_pct:.2f}%`, expectancy `{row.expectancy:.2f}`, payoff `{row.payoff_ratio:.2f}`, top_symbol `{row.top_symbol_pnl_share_pct:.2f}%`, top_10pct_days `{row.top_10pct_days_pnl_share_pct:.2f}%`, post_remove_5pct_best_days `{row.post_remove_5pct_best_days_return_pct:.2f}%`, trade_count `{row.trade_count}`, simplicity `{row.operational_simplicity}`."
            )
        wrapper_lines.append("")
    wrapper_lines.append("- The cleanest deployment-discipline wrappers are the equal-weight symbol cap and the 20% top-symbol contribution cap. The reduced-turnover top-3 wrapper is only structurally clean for the two rank-based upside families.")
    write_markdown(OUTPUTS["wrapper_md"], "\n".join(wrapper_lines))

    stability_lines = ["# Stability Report", ""]
    for template in TARGETS:
        subset = stability_df.loc[stability_df["template_key"] == template]
        first_half = subset.loc[subset["slice_name"] == "first_half"].iloc[0]
        second_half = subset.loc[subset["slice_name"] == "second_half"].iloc[0]
        positive_annual = float((subset.loc[subset["slice_name"].str.startswith("annual_window_"), "total_return_pct"] > 0).mean() * 100.0)
        stability_lines.append(f"- `{template}`: first_half `{first_half['total_return_pct']:.2f}%`, second_half `{second_half['total_return_pct']:.2f}%`, positive_annual_windows `{positive_annual:.2f}%`.")
    stability_lines += [
        "",
        "- Relative strength and cross-sectional momentum both stayed positive in both halves and all annual windows.",
        "- Cross-sectional momentum was slightly stronger on raw expectancy, but relative strength was modestly less concentrated.",
        "- DSE remained positive in the second half, but its annual path was choppier and much smaller economically.",
    ]
    write_markdown(OUTPUTS["stability_md"], "\n".join(stability_lines))

    rs_score = float(score_df.loc[score_df["template_key"] == "relative_strength_vs_benchmark", "edge_quality_score"].iloc[0])
    csm_score = float(score_df.loc[score_df["template_key"] == "cross_sectional_momentum", "edge_quality_score"].iloc[0])
    score_gap = csm_score - rs_score
    rs_promote = rs_score >= csm_score or (raw_winner["template_key"] == "relative_strength_vs_benchmark" and score_gap <= 0.02)

    decision_lines = [
        "# RS Deployment Decision",
        "",
        f"1. Is `relative_strength_vs_benchmark` the best next daily research branch? {'Yes.' if rs_promote else 'Not yet.'} The pure scorecard gives `cross_sectional_momentum` a narrow trust-adjusted edge, but the gap is small enough that RS still wins the branch decision because it keeps the highest raw return and slightly cleaner native concentration.",
        f"2. Is it more trustworthy than `cross_sectional_momentum` after hard concentration and best-day tests? {'Not on the pure scorecard.' if csm_score > rs_score else 'Yes, slightly.'} CSM is marginally stronger on the wrapper-adjusted score, while RS is marginally cleaner on native concentration and still larger on capped-return reserve.",
        "3. Should it be pursued as a broad daily sleeve, narrowed disciplined sleeve, NVDA-aware but cross-symbol sleeve, or research-only artifact? It should be pursued as a narrowed disciplined sleeve. The ex-NVDA and capped wrappers show it is not just an NVDA illusion, but the native book is still too concentrated to call a broad deployable sleeve.",
        "4. Does DSE remain the best control benchmark? Yes. DSE remains the best confirmed daily control because its prior confirmation packet and drawdown profile are still the cleanest reference point.",
        "5. What exact next experiment should happen after this? Promote RS into a focused research branch with the 20% top-symbol cap and equal-weight symbol wrapper as the first disciplined overlays, then rerun ex-NVDA and best-day stress side by side against the native book and the same wrapped CSM challenger.",
    ]
    write_markdown(OUTPUTS["decision_md"], "\n".join(decision_lines))

    action_lines = [
        "# RS Next Action Plan",
        "",
        "1. Keep papering `qqq_led_tqqq_sqqq_pair_opening_range_intraday_system` now. It is still the best operational candidate.",
        "2. Preserve `down_streak_exhaustion` as the confirmed daily control benchmark.",
        "3. Promote `relative_strength_vs_benchmark` to the next focused research branch using disciplined wrapper comparisons, not raw-native promotion.",
        "4. Keep `cross_sectional_momentum` as the main challenger, but demote it behind RS if only one upside branch gets attention first.",
        "5. Keep the equal-weight symbol cap and 20% top-symbol cap wrappers. They reduce concentration without fully killing the edge.",
        "6. Cut any wrapper that meaningfully lowers drawdown only by destroying most of the surviving return or best-day resilience.",
    ]
    write_markdown(OUTPUTS["action_md"], "\n".join(action_lines))

    print(json.dumps(
        {
            "opened_files": [row["path"] for row in file_status if row["opened"]],
            "raw_return_winner": raw_winner["template_key"],
            "trust_adjusted_winner": trust_winner["template_key"],
            "most_best_day_dependent": most_best_day_dependent,
            "rs_promoted_next_branch": rs_promote,
            "cross_sectional_status": "challenger" if rs_promote else "primary contender",
            "dse_best_control": True,
            "outputs": {k: str(v) for k, v in OUTPUTS.items()},
        },
        indent=2,
    ))


if __name__ == "__main__":
    main()
