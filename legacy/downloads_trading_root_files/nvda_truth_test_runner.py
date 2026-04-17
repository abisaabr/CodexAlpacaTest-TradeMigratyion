from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

BASE_DIR = Path(r"C:\Users\rabisaab\Downloads")
REPO_SRC = BASE_DIR / "alpaca-stock-strategy-research" / "src"
if str(REPO_SRC) not in sys.path:
    sys.path.insert(0, str(REPO_SRC))

from alpaca_stock_research.backtests.engine import equity_from_trades, run_backtest
from alpaca_stock_research.backtests.metrics import compute_drawdown, compute_metrics
from alpaca_stock_research.backtests.strategies import build_signals


INITIAL_CAPITAL = 25_000.0
BASE_UNIVERSE = ["SPY", "QQQ", "IWM", "NVDA", "META", "AAPL", "AMZN", "NFLX", "TSLA"]
MEGACAP_EX_NVDA = ["AAPL", "AMZN", "GOOGL", "META", "NFLX", "TSLA"]
ETF_ONLY = ["SPY", "QQQ", "IWM"]
TARGET_TEMPLATES = [
    "relative_strength_vs_benchmark",
    "cross_sectional_momentum",
    "breakout_consolidation",
    "volatility_contraction_breakout",
    "pullback_in_trend",
]
CONTROL_TEMPLATES = ["down_streak_exhaustion"]
ALL_DAILY_TEMPLATES = TARGET_TEMPLATES + CONTROL_TEMPLATES

EXACT_FILES = [
    BASE_DIR / "master_strategy_memo.txt",
    BASE_DIR / "top10_authoritative_inventory.txt",
    BASE_DIR / "strategy_chat_seed.txt",
    BASE_DIR / "tournament_master_report.md",
    BASE_DIR / "monday_paper_plan.md",
]

OUTPUTS = {
    "digest": BASE_DIR / "nvda_truth_test_input_digest.md",
    "matrix": BASE_DIR / "nvda_truth_test_matrix.md",
    "metrics": BASE_DIR / "concentration_portability_metrics.csv",
    "leaderboard": BASE_DIR / "concentration_portability_leaderboard.md",
    "scorecard": BASE_DIR / "edge_survival_scorecard.csv",
    "clusters": BASE_DIR / "nvda_cluster_truth_map.csv",
    "hotspots": BASE_DIR / "nvda_edge_hotspots.md",
    "elimination": BASE_DIR / "truth_test_elimination_report.md",
    "controls": BASE_DIR / "control_comparison_summary.md",
    "ranking": BASE_DIR / "next_edge_research_ranking.md",
    "actions": BASE_DIR / "next_edge_action_plan.md",
}

EVIDENCE = {
    "relative_strength_vs_benchmark": ("medium", 0.65),
    "cross_sectional_momentum": ("medium", 0.65),
    "breakout_consolidation": ("medium", 0.60),
    "volatility_contraction_breakout": ("medium", 0.60),
    "pullback_in_trend": ("medium", 0.45),
    "down_streak_exhaustion": ("high", 0.95),
}


def read_if_exists(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


def load_baseline_specs(metrics_path: Path) -> pd.DataFrame:
    metrics = pd.read_csv(metrics_path)
    wanted = {
        "relative_strength_vs_benchmark": "relative_strength_vs_benchmark_rep_user_subset_5y",
        "cross_sectional_momentum": "cross_sectional_momentum_rep_user_subset_5y",
        "breakout_consolidation": "breakout_consolidation_rep_user_subset_5y",
        "volatility_contraction_breakout": "volatility_contraction_breakout_rep_user_subset_5y",
        "pullback_in_trend": "pullback_in_trend_rep_user_subset_5y",
        "down_streak_exhaustion": "dse_exact_user_subset_5y",
    }
    rows = []
    for template, strategy_id in wanted.items():
        row = metrics.loc[metrics["strategy_id"] == strategy_id].iloc[0].copy()
        row["template_key"] = template
        row["params_dict"] = json.loads(row["params"])
        rows.append(row)
    return pd.DataFrame(rows)


def regime_map(frame: pd.DataFrame) -> pd.DataFrame:
    spy = frame.loc[frame["symbol"] == "SPY", ["timestamp", "return_20d", "uptrend_regime", "returns"]].copy()
    spy = spy.sort_values("timestamp")
    spy["spy_vol_20d"] = spy["returns"].rolling(20).std(ddof=0) * math.sqrt(252)
    vol_median = float(spy["spy_vol_20d"].dropna().median()) if spy["spy_vol_20d"].notna().any() else 0.0
    spy["rising_market"] = (spy["return_20d"] > 0) & spy["uptrend_regime"].fillna(False)
    spy["falling_or_volatile"] = (spy["return_20d"] <= 0) | (spy["spy_vol_20d"] >= vol_median)
    spy["calmer"] = spy["spy_vol_20d"] <= vol_median
    spy["regime_primary"] = np.where(
        spy["rising_market"],
        "rising_market",
        np.where(spy["falling_or_volatile"], "falling_or_volatile", "calmer"),
    )
    return spy[["timestamp", "rising_market", "falling_or_volatile", "calmer", "regime_primary"]]


def slippage_map(spread_summary: pd.DataFrame) -> dict[str, float]:
    return {
        str(row.symbol): float(max(2.0, 0.5 * float(row.median_spread_bps)))
        for row in spread_summary.itertuples()
    }


def run_template(frame: pd.DataFrame, template: str, params: dict[str, object], slippage: dict[str, float]):
    signal_frame = build_signals(frame, template, params)
    return run_backtest(
        bars=frame,
        signal_frame=signal_frame,
        strategy_name=template,
        sample="truth_test",
        params=params,
        holding_bars=int(params["holding_bars"]),
        initial_capital=INITIAL_CAPITAL,
        effective_slippage_bps=slippage,
        fee_per_trade=0.0,
        max_positions=5,
        max_portfolio_heat=0.50,
        max_daily_loss=0.03,
        profit_target_pct=float(params["profit_target_pct"]) if float(params.get("profit_target_pct", 0.0)) > 0 else None,
    )


def waterfill_cap(values: pd.Series, cap_share: float = 0.25) -> dict[str, float]:
    pos = values.clip(lower=0.0)
    if pos.sum() <= 0:
        return {k: 1.0 for k in values.index}
    threshold = float(pos.max())
    for _ in range(100):
        retained = pos.clip(upper=threshold)
        new_threshold = cap_share * float(retained.sum())
        if abs(new_threshold - threshold) < 1e-8:
            break
        threshold = new_threshold
    return {
        symbol: (min(1.0, threshold / pnl) if pnl > 0 else 1.0)
        for symbol, pnl in pos.items()
    }


def scale_trades(trades: pd.DataFrame, scales: dict[str, float]) -> pd.DataFrame:
    if trades.empty:
        return trades.copy()
    scaled = trades.copy()
    for col in ["pnl", "pnl_pct", "trade_return_pct", "entry_notional", "heat", "units"]:
        scaled[col] = scaled[col] * scaled["symbol"].map(scales).fillna(1.0)
    return scaled


def equal_risk_scales(trades: pd.DataFrame) -> dict[str, float]:
    gross = trades.groupby("symbol")["entry_notional"].sum()
    if gross.empty:
        return {}
    target = float(gross.mean())
    return {symbol: min(1.0, target / value) if value > 0 else 1.0 for symbol, value in gross.items()}


def metric_row(template: str, family: str, slice_name: str, scope_note: str, result, trades: pd.DataFrame, equity_curve: pd.DataFrame | None = None) -> dict[str, object]:
    pnl = trades.groupby("symbol")["pnl"].sum() if not trades.empty else pd.Series(dtype=float)
    gross_positive = pnl.clip(lower=0.0)
    top_symbol = gross_positive.idxmax() if not gross_positive.empty and gross_positive.max() > 0 else ""
    total_positive = float(gross_positive.sum())
    top_symbol_share = float(gross_positive.max() / total_positive) if total_positive > 0 else 0.0
    nvda_share = float(gross_positive.get("NVDA", 0.0) / total_positive) if total_positive > 0 else 0.0
    curve = equity_curve if equity_curve is not None else getattr(result, "equity_curve", pd.DataFrame())
    day_pnl = curve["daily_pnl"] if not curve.empty and "daily_pnl" in curve.columns else pd.Series(dtype=float)
    active_days = len(day_pnl)
    top_days = max(1, math.ceil(active_days * 0.10)) if active_days else 0
    positive_day_pnl = day_pnl.clip(lower=0.0)
    top_day_share = float(positive_day_pnl.sort_values(ascending=False).head(top_days).sum() / positive_day_pnl.sum()) if positive_day_pnl.sum() > 0 and top_days else 0.0
    base = gross_positive if total_positive > 0 else pnl.abs()
    concentration_index = float(((base / base.sum()) ** 2).sum()) if not base.empty and base.sum() > 0 else 0.0
    wins = trades.loc[trades["pnl"] > 0, "pnl"]
    losses = trades.loc[trades["pnl"] < 0, "pnl"]
    metrics = result.metrics
    return {
        "template_key": template,
        "family": family,
        "slice_name": slice_name,
        "scope_note": scope_note,
        "final_equity": float(metrics.get("ending_equity", INITIAL_CAPITAL)),
        "total_return_pct": float(metrics.get("total_return", 0.0)) * 100.0,
        "CAGR": float(metrics.get("cagr", 0.0)) * 100.0,
        "max_drawdown_pct": float(metrics.get("max_drawdown", 0.0)) * 100.0,
        "Sharpe": float(metrics.get("sharpe", 0.0)),
        "profit_factor": float(metrics.get("profit_factor", 0.0)),
        "expectancy": float(metrics.get("expectancy_dollars", 0.0)),
        "win_rate": float(metrics.get("win_rate", 0.0)) * 100.0,
        "trade_count": int(metrics.get("trade_count", 0.0)),
        "average_win": float(wins.mean()) if not wins.empty else 0.0,
        "average_loss": float(losses.mean()) if not losses.empty else 0.0,
        "payoff_ratio": float((wins.mean() / abs(losses.mean()))) if (not wins.empty and not losses.empty and losses.mean() != 0) else 0.0,
        "top_symbol": top_symbol,
        "top_symbol_pnl_share_pct": top_symbol_share * 100.0,
        "nvda_pnl_share_pct": nvda_share * 100.0,
        "top_10pct_days_pnl_share_pct": top_day_share * 100.0,
        "symbol_concentration_index": concentration_index,
        "active_symbol_count": int((pnl != 0).sum()) if not pnl.empty else 0,
        "positive_symbol_count": int((pnl > 0).sum()) if not pnl.empty else 0,
        "reached_100k_from_25k": bool(float(metrics.get("ending_equity", INITIAL_CAPITAL)) >= 100_000.0),
        "above_60pct_winrate": bool(float(metrics.get("win_rate", 0.0)) >= 0.60),
    }


def add_trade_features(trades: pd.DataFrame, frame: pd.DataFrame, regimes: pd.DataFrame) -> pd.DataFrame:
    if trades.empty:
        return trades.copy()
    enriched = trades.copy()
    lookup = frame.merge(regimes, on="timestamp", how="left").set_index(["symbol", "timestamp"]).sort_index()
    by_symbol = {symbol: grp.set_index("timestamp").sort_index() for symbol, grp in frame.groupby("symbol")}
    rows = []
    for trade in enriched.itertuples():
        key = (trade.symbol, trade.entry_time)
        row = lookup.loc[key] if key in lookup.index else None
        symbol_path = by_symbol[trade.symbol].loc[trade.entry_time : trade.exit_time]
        mfe = float(symbol_path["high"].max() / trade.entry_price - 1.0) if not symbol_path.empty else 0.0
        mae = float(symbol_path["low"].min() / trade.entry_price - 1.0) if not symbol_path.empty else 0.0
        gap = float(row["gap_pct"]) if row is not None else 0.0
        vol_ratio = float(row["vol_ratio_10_50"]) if row is not None and pd.notna(row["vol_ratio_10_50"]) else np.nan
        rows.append(
            {
                "mfe_pct": mfe,
                "mae_pct": mae,
                "side": "long",
                "day_of_week": pd.Timestamp(trade.entry_time).day_name(),
                "holding_bucket": "short" if trade.holding_bars <= 5 else ("medium" if trade.holding_bars <= 20 else "long"),
                "gap_bucket": "gap_down" if gap <= -0.01 else ("gap_up" if gap >= 0.01 else "flat_gap"),
                "trend_alignment": (
                    "stacked_uptrend"
                    if row is not None and bool(row["trend_stack_regime"])
                    else ("uptrend" if row is not None and bool(row["uptrend_regime"]) else "non_uptrend")
                ),
                "volatility_bucket": "compressed" if pd.notna(vol_ratio) and vol_ratio <= 0.85 else ("expanded" if pd.notna(vol_ratio) and vol_ratio > 1.15 else "neutral"),
                "regime_bucket": (str(row["regime_primary"]) if row is not None and pd.notna(row["regime_primary"]) else "unknown"),
            }
        )
    return pd.concat([enriched.reset_index(drop=True), pd.DataFrame(rows)], axis=1)


def slice_frame(frame: pd.DataFrame, slice_name: str, start: pd.Timestamp, end: pd.Timestamp, regimes: pd.DataFrame) -> tuple[pd.DataFrame, str]:
    if slice_name == "native_prior_tournament_slice":
        return frame[frame["symbol"].isin(BASE_UNIVERSE)].copy(), "same 9-symbol user subset as prior tournament"
    if slice_name == "nvda_only":
        return frame[frame["symbol"] == "NVDA"].copy(), "NVDA retained alone"
    if slice_name == "megacap_tech_ex_nvda":
        return frame[frame["symbol"].isin([s for s in MEGACAP_EX_NVDA if s in frame["symbol"].unique()])].copy(), "AAPL/AMZN/GOOGL/META/NFLX/TSLA ex-NVDA"
    if slice_name == "broad_basket_ex_nvda":
        return frame[frame["symbol"].isin([s for s in BASE_UNIVERSE if s != "NVDA"])].copy(), "prior user subset excluding NVDA"
    if slice_name == "etf_only":
        return frame[frame["symbol"].isin(ETF_ONLY)].copy(), "SPY/QQQ/IWM only"
    if slice_name == "first_half":
        midpoint = start + (end - start) / 2
        return frame[(frame["timestamp"] >= start) & (frame["timestamp"] < midpoint)].copy(), "first half of the 5-year window"
    if slice_name == "second_half":
        midpoint = start + (end - start) / 2
        return frame[(frame["timestamp"] >= midpoint) & (frame["timestamp"] <= end)].copy(), "second half of the 5-year window"
    if slice_name in {"rising_market", "falling_or_volatile", "calmer"}:
        keep = set(regimes.loc[regimes[slice_name], "timestamp"])
        return frame[frame["timestamp"].isin(keep)].copy(), f"regime slice from SPY tagging: {slice_name}"
    raise ValueError(slice_name)


def build_annual_windows(start: pd.Timestamp, end: pd.Timestamp) -> list[tuple[str, pd.Timestamp, pd.Timestamp]]:
    windows = []
    current = start
    idx = 1
    while current < end:
        nxt = min(current + pd.DateOffset(years=1), end)
        windows.append((f"annual_window_{idx}", current, nxt))
        current = nxt
        idx += 1
    return windows


def write_markdown(path: Path, text: str) -> None:
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def score_family(metrics_df: pd.DataFrame, template: str) -> dict[str, object]:
    family_rows = metrics_df.loc[metrics_df["template_key"] == template].copy()
    native = family_rows.loc[family_rows["slice_name"] == "native_prior_tournament_slice"].iloc[0]
    ex_nvda = family_rows.loc[family_rows["slice_name"] == "broad_basket_ex_nvda"].iloc[0]
    capped = family_rows.loc[family_rows["slice_name"] == "top_3_symbol_concentration_capped"].iloc[0]
    equal_risk = family_rows.loc[family_rows["slice_name"] == "equal_risk_symbol_capped"].iloc[0]
    second_half = family_rows.loc[family_rows["slice_name"] == "second_half"].iloc[0]
    annual = family_rows.loc[family_rows["slice_name"].str.startswith("annual_window_")]

    native_return = max(float(native["total_return_pct"]), 0.0)
    ex_nvda_survival = 0.0 if float(ex_nvda["expectancy"]) <= 0 else min(1.0, max(float(ex_nvda["total_return_pct"]), 0.0) / native_return) if native_return > 0 else 0.0
    cap_survival = np.mean([
        0.0 if float(capped["expectancy"]) <= 0 else min(1.0, max(float(capped["total_return_pct"]), 0.0) / native_return) if native_return > 0 else 0.0,
        0.0 if float(equal_risk["expectancy"]) <= 0 else min(1.0, max(float(equal_risk["total_return_pct"]), 0.0) / native_return) if native_return > 0 else 0.0,
    ])
    drawdown_control = max(0.0, 1.0 - float(native["max_drawdown_pct"]) / 80.0)
    expectancy_quality = min(1.0, max(0.0, float(native["expectancy"]) / 100.0)) * 0.5 + min(1.0, max(0.0, float(native["payoff_ratio"]) / 2.0)) * 0.5
    time_stability = 0.5 * (1.0 if float(second_half["expectancy"]) > 0 else 0.0) + 0.5 * float((annual["expectancy"] > 0).mean()) if not annual.empty else 0.0
    breadth = min(1.0, float(ex_nvda["positive_symbol_count"]) / 4.0)
    evidence_label, evidence_score = EVIDENCE[template]
    raw_return_score = min(1.0, native_return / 400.0)
    total = (
        0.20 * ex_nvda_survival
        + 0.20 * cap_survival
        + 0.15 * drawdown_control
        + 0.15 * expectancy_quality
        + 0.10 * time_stability
        + 0.10 * breadth
        + 0.05 * evidence_score
        + 0.05 * raw_return_score
    )
    if template in TARGET_TEMPLATES:
        total -= (1.0 - evidence_score) * 0.10
    return {
        "template_key": template,
        "family": str(native["family"]),
        "edge_survival_score": round(float(total), 6),
        "ex_nvda_survival_component": round(float(ex_nvda_survival), 6),
        "concentration_control_component": round(float(cap_survival), 6),
        "drawdown_control_component": round(float(drawdown_control), 6),
        "expectancy_payoff_component": round(float(expectancy_quality), 6),
        "time_stability_component": round(float(time_stability), 6),
        "breadth_component": round(float(breadth), 6),
        "evidence_quality": evidence_label,
        "evidence_component": evidence_score,
        "raw_return_component": round(float(raw_return_score), 6),
    }


def classify_family(metrics_df: pd.DataFrame, template: str) -> tuple[str, list[str]]:
    rows = metrics_df.loc[metrics_df["template_key"] == template]
    native = rows.loc[rows["slice_name"] == "native_prior_tournament_slice"].iloc[0]
    ex_nvda = rows.loc[rows["slice_name"] == "broad_basket_ex_nvda"].iloc[0]
    capped = rows.loc[rows["slice_name"] == "top_3_symbol_concentration_capped"].iloc[0]
    second_half = rows.loc[rows["slice_name"] == "second_half"].iloc[0]
    reasons = []
    if float(native["nvda_pnl_share_pct"]) > 50.0:
        reasons.append("More than half of positive PnL comes from NVDA.")
    if float(ex_nvda["expectancy"]) <= 0:
        reasons.append("Expectancy turns non-positive when NVDA is removed.")
    if float(capped["expectancy"]) <= 0 or float(capped["final_equity"]) <= INITIAL_CAPITAL:
        reasons.append("The edge collapses under the concentration-capped wrapper.")
    if float(second_half["expectancy"]) <= 0 or float(second_half["final_equity"]) <= INITIAL_CAPITAL:
        reasons.append("The second half of the window is not economically positive.")
    if float(native["positive_symbol_count"]) <= 2:
        reasons.append("Positive contribution is concentrated in one or two symbols.")
    if float(native["top_10pct_days_pnl_share_pct"]) > 40.0:
        reasons.append("Top 10% of days drive more than 40% of positive PnL.")
    if float(native["max_drawdown_pct"]) > 60.0:
        reasons.append("Drawdown is too large for a realistic $25k sleeve.")
    elif float(native["max_drawdown_pct"]) > 45.0 and float(native["total_return_pct"]) < 150.0:
        reasons.append("Drawdown is too large relative to retained edge.")

    if not reasons:
        return "survives broadly", ["No hard elimination rule fired."]
    if (
        "Expectancy turns non-positive when NVDA is removed." in reasons
        or "The edge collapses under the concentration-capped wrapper." in reasons
        or "The second half of the window is not economically positive." in reasons
        or "Drawdown is too large for a realistic $25k sleeve." in reasons
    ):
        return "fails and should be deprioritized", reasons
    if "More than half of positive PnL comes from NVDA." in reasons and float(ex_nvda["expectancy"]) > 0 and float(capped["expectancy"]) > 0:
        return "survives but mostly as NVDA-specific", reasons
    if float(ex_nvda["expectancy"]) > 0 or float(capped["expectancy"]) > 0:
        return "survives only as niche research", reasons
    return "fails and should be deprioritized", reasons


def main() -> None:
    exact_status = [{"path": str(path), "opened": path.exists(), "role": "authoritative context"} for path in EXACT_FILES]
    memo_text = read_if_exists(BASE_DIR / "master_strategy_memo.txt")
    top10_text = read_if_exists(BASE_DIR / "top10_authoritative_inventory.txt")
    report_text = read_if_exists(BASE_DIR / "tournament_master_report.md")
    monday_text = read_if_exists(BASE_DIR / "monday_paper_plan.md")

    baseline_specs = load_baseline_specs(BASE_DIR / "underlying_tournament_metrics.csv")
    features = pd.read_parquet(BASE_DIR / "alpaca-stock-strategy-research" / "data" / "normalized" / "features" / "features.parquet")
    spreads = pd.read_parquet(BASE_DIR / "alpaca-stock-strategy-research" / "data" / "normalized" / "features" / "quote_spread_summary.parquet")
    start = pd.Timestamp("2021-03-24 04:00:00+00:00")
    end = pd.Timestamp("2026-03-24 04:00:00+00:00")
    window_frame = features[(features["timestamp"] >= start) & (features["timestamp"] <= end)].copy()
    regimes = regime_map(window_frame)
    slip = slippage_map(spreads)

    digest_lines = ["# NVDA Truth-Test Input Digest", "", "## Exact files", ""]
    for row in exact_status:
        digest_lines.append(f"- `{row['path']}`: {'opened successfully' if row['opened'] else 'missing'}")
    digest_lines += [
        "",
        "## Family implementations used",
        "",
        "- Daily reruns use the local `alpaca_stock_research` engine and `build_signals` templates that reproduced the prior tournament rows exactly.",
        "- `qqq_led_tqqq_sqqq_pair_opening_range_intraday_system` stays a control/reference from the prior report and Monday plan rather than a new daily rerun.",
        "",
        "## Baseline references",
        "",
    ]
    for row in baseline_specs.itertuples():
        digest_lines.append(
            f"- `{row.template_key}`: strategy_id `{row.strategy_id}`, family `{row.family}`, final_equity `{row.final_equity:.2f}`, return `{row.total_return_pct:.2f}%`, max_dd `{row.max_drawdown_pct:.2f}%`, win_rate `{row.win_rate:.2f}%`."
        )
    digest_lines += [
        "",
        "## Data coverage limits",
        "",
        "- Daily truth test uses the same 5-year window as the prior tournament: 2021-03-24 through 2026-03-24 UTC.",
        "- Local daily feature data extends beyond the user subset, but the native benchmark slice preserves the prior 9-symbol subset.",
        "- `GOOG` is still absent from the prior user-subset run; local features carry `GOOGL`, which is used only where the test matrix explicitly allows `GOOG or GOOGL, whichever exists locally`.",
        "- Historical options replay remains blocked and is intentionally out of scope for this task.",
        "",
        "## Conflicts or trust notes",
        "",
        f"- Memo says Momentum / Relative-Strength and Breakout / Trend-Continuation remain promising but unconfirmed. Top-10 inventory and tournament report preserve upside, but both still carry concentration and trust warnings.",
        f"- Memo keeps Down Streak Exhaustion as the best confirmed daily control. Monday plan keeps the QQQ pair as the best current paper candidate.",
    ]
    write_markdown(OUTPUTS["digest"], "\n".join(digest_lines))

    matrix_lines = [
        "# NVDA Truth-Test Matrix",
        "",
        "## Tested daily families",
        "",
    ]
    for row in baseline_specs.itertuples():
        matrix_lines.append(f"- `{row.template_key}` -> `{row.family}`")
    matrix_lines += [
        "",
        "## Reference-only operational control",
        "",
        "- `qqq_led_tqqq_sqqq_pair_opening_range_intraday_system` is kept for role comparison only; no new daily rerun is forced onto it.",
        "",
        "## Slice definitions",
        "",
        "- `native_prior_tournament_slice`: same 9-symbol user subset as the prior tournament.",
        "- `nvda_only`: NVDA retained alone.",
        "- `megacap_tech_ex_nvda`: AAPL, AMZN, GOOGL, META, NFLX, TSLA.",
        "- `broad_basket_ex_nvda`: prior user subset excluding NVDA.",
        "- `etf_only`: SPY, QQQ, IWM.",
        "- `top_3_symbol_concentration_capped`: native trades scaled so no symbol keeps more than 25% of positive PnL.",
        "- `equal_risk_symbol_capped`: native trades scaled so high-turnover symbols do not dominate cumulative entry notional.",
        "- `first_half` and `second_half`: split the same 5-year window in half.",
        "- `annual_window_n`: sequential 1-year windows across the same 5-year span.",
        "- `rising_market`, `falling_or_volatile`, `calmer`: SPY-tagged diagnostic regime slices from the local confirmation logic.",
    ]
    write_markdown(OUTPUTS["matrix"], "\n".join(matrix_lines))

    result_rows: list[dict[str, object]] = []
    cluster_rows: list[dict[str, object]] = []

    for spec in baseline_specs.itertuples():
        template = spec.template_key
        params = spec.params_dict
        family = spec.family
        base_frame = window_frame[window_frame["symbol"].isin(BASE_UNIVERSE + ["GOOGL"])].copy()
        native_frame, native_note = slice_frame(base_frame, "native_prior_tournament_slice", start, end, regimes)
        native_result = run_template(native_frame, template, params, slip)
        native_trades = add_trade_features(native_result.trades, native_frame, regimes)
        result_rows.append(metric_row(template, family, "native_prior_tournament_slice", native_note, native_result, native_trades, native_result.equity_curve))

        pos_pnl = native_trades.groupby("symbol")["pnl"].sum() if not native_trades.empty else pd.Series(dtype=float)
        capped_scales = waterfill_cap(pos_pnl, 0.25) if not pos_pnl.empty else {}
        equal_scales = equal_risk_scales(native_trades) if not native_trades.empty else {}
        capped_trades = scale_trades(native_trades, capped_scales)
        equal_trades = scale_trades(native_trades, equal_scales)
        capped_curve = equity_from_trades(capped_trades, native_frame, INITIAL_CAPITAL)
        equal_curve = equity_from_trades(equal_trades, native_frame, INITIAL_CAPITAL)
        capped_result = type("obj", (), {"metrics": compute_metrics(capped_curve, capped_trades)})
        equal_result = type("obj", (), {"metrics": compute_metrics(equal_curve, equal_trades)})
        result_rows.append(metric_row(template, family, "top_3_symbol_concentration_capped", "native trades scaled to a 25% positive-PnL symbol cap", capped_result, capped_trades, capped_curve))
        result_rows.append(metric_row(template, family, "equal_risk_symbol_capped", "native trades scaled to equalize cumulative symbol notional", equal_result, equal_trades, equal_curve))

        for name in ["nvda_only", "megacap_tech_ex_nvda", "broad_basket_ex_nvda", "etf_only", "first_half", "second_half", "rising_market", "falling_or_volatile", "calmer"]:
            this_frame, note = slice_frame(base_frame, name, start, end, regimes)
            result = run_template(this_frame, template, params, slip)
            trades = add_trade_features(result.trades, this_frame, regimes)
            result_rows.append(metric_row(template, family, name, note, result, trades, result.equity_curve))

        for label, ws, we in build_annual_windows(start, end):
            annual_frame = base_frame[(base_frame["timestamp"] >= ws) & (base_frame["timestamp"] <= we)].copy()
            annual_frame = annual_frame[annual_frame["symbol"].isin(BASE_UNIVERSE)].copy()
            result = run_template(annual_frame, template, params, slip)
            trades = add_trade_features(result.trades, annual_frame, regimes)
            result_rows.append(metric_row(template, family, label, f"annual window {ws.date()} to {we.date()}", result, trades, result.equity_curve))

        if template in TARGET_TEMPLATES and not native_trades.empty:
            native_trades["half_bucket"] = np.where(native_trades["entry_time"] < start + (end - start) / 2, "first_half", "second_half")
            total_positive = native_trades["pnl"].clip(lower=0.0).sum()
            loss_base = abs(native_trades.loc[native_trades["pnl"] < 0, "pnl"].sum()) or 1.0
            for dim in ["symbol", "side", "volatility_bucket", "trend_alignment", "day_of_week", "gap_bucket", "holding_bucket", "regime_bucket"]:
                for value, grp in native_trades.groupby(dim):
                    wins = grp.loc[grp["pnl"] > 0, "pnl"]
                    losses = grp.loc[grp["pnl"] < 0, "pnl"]
                    stability = float((grp.groupby("half_bucket")["pnl"].mean() > 0).mean()) if grp["half_bucket"].nunique() else 0.0
                    cluster_rows.append(
                        {
                            "template_key": template,
                            "family": family,
                            "cluster_dimension": dim,
                            "cluster_value": value,
                            "trade_count": int(len(grp)),
                            "expectancy": float(grp["pnl"].mean()),
                            "payoff_ratio": float((wins.mean() / abs(losses.mean()))) if (not wins.empty and not losses.empty and losses.mean() != 0) else 0.0,
                            "win_rate": float((grp["pnl"] > 0).mean()) * 100.0,
                            "average_MFE_pct": float(grp["mfe_pct"].mean()) * 100.0,
                            "average_MAE_pct": float(grp["mae_pct"].mean()) * 100.0,
                            "drawdown_contribution_pct": float(abs(grp.loc[grp["pnl"] < 0, "pnl"].sum()) / loss_base) * 100.0,
                            "percent_total_pnl_pct": float(grp["pnl"].clip(lower=0.0).sum() / total_positive) * 100.0 if total_positive > 0 else 0.0,
                            "stability_across_time_slices": stability,
                        }
                    )

    metrics_df = pd.DataFrame(result_rows).sort_values(["template_key", "slice_name"]).reset_index(drop=True)
    metrics_df.to_csv(OUTPUTS["metrics"], index=False)
    cluster_df = pd.DataFrame(cluster_rows).sort_values(["template_key", "cluster_dimension", "percent_total_pnl_pct"], ascending=[True, True, False])
    cluster_df.to_csv(OUTPUTS["clusters"], index=False)

    score_df = pd.DataFrame([score_family(metrics_df, template) for template in ALL_DAILY_TEMPLATES]).sort_values("edge_survival_score", ascending=False)
    score_df.to_csv(OUTPUTS["scorecard"], index=False)

    elimination_rows = []
    for template in ALL_DAILY_TEMPLATES:
        classification, reasons = classify_family(metrics_df, template)
        elimination_rows.append({"template_key": template, "classification": classification, "reasons": reasons})

    native_leaders = metrics_df.loc[metrics_df["slice_name"] == "native_prior_tournament_slice"].sort_values("total_return_pct", ascending=False)
    leaderboard_lines = ["# Concentration Portability Leaderboard", "", "## Native slice by raw return", ""]
    for row in native_leaders.itertuples():
        leaderboard_lines.append(
            f"- `{row.template_key}`: return `{row.total_return_pct:.2f}%`, final_equity `${row.final_equity:,.2f}`, max_dd `{row.max_drawdown_pct:.2f}%`, NVDA share `{row.nvda_pnl_share_pct:.2f}%`, top-day share `{row.top_10pct_days_pnl_share_pct:.2f}%`."
        )
    leaderboard_lines += ["", "## Edge survival ranking", ""]
    for row in score_df.itertuples():
        leaderboard_lines.append(f"- `{row.template_key}`: edge_survival_score `{row.edge_survival_score:.4f}`.")
    write_markdown(OUTPUTS["leaderboard"], "\n".join(leaderboard_lines))

    hotspot_lines = ["# NVDA Edge Hotspots", ""]
    for template in TARGET_TEMPLATES:
        family_clusters = cluster_df.loc[(cluster_df["template_key"] == template) & (cluster_df["cluster_dimension"] == "symbol")].sort_values("percent_total_pnl_pct", ascending=False)
        top = family_clusters.head(3)
        hotspot_lines.append(f"## {template}")
        for row in top.itertuples():
            hotspot_lines.append(
                f"- `{row.cluster_value}`: {row.percent_total_pnl_pct:.2f}% of positive PnL, expectancy `{row.expectancy:.2f}`, payoff `{row.payoff_ratio:.2f}`, stability `{row.stability_across_time_slices:.2f}`."
            )
        hotspot_lines.append("")
    write_markdown(OUTPUTS["hotspots"], "\n".join(hotspot_lines))

    elimination_lines = ["# Truth Test Elimination Report", ""]
    for row in elimination_rows:
        elimination_lines.append(f"## {row['template_key']}")
        elimination_lines.append(f"- Classification: {row['classification']}")
        for reason in row["reasons"]:
            elimination_lines.append(f"- {reason}")
        elimination_lines.append("")
    write_markdown(OUTPUTS["elimination"], "\n".join(elimination_lines))

    dse_native = metrics_df.loc[(metrics_df["template_key"] == "down_streak_exhaustion") & (metrics_df["slice_name"] == "native_prior_tournament_slice")].iloc[0]
    best_survivor = score_df.iloc[0]
    best_non_control = score_df.loc[score_df["template_key"].isin(TARGET_TEMPLATES)].iloc[0]
    control_lines = [
        "# Control Comparison Summary",
        "",
        f"- Families that beat DSE on raw return but lose on trust: {', '.join(native_leaders.loc[(native_leaders['template_key'] != 'down_streak_exhaustion') & (native_leaders['total_return_pct'] > dse_native['total_return_pct']), 'template_key'].tolist())}.",
        f"- The family keeping the most edge after hard truth tests is `{best_survivor['template_key']}` by the survival scorecard.",
        f"- The best next daily research priority after the DSE control is `{best_non_control['template_key']}`.",
        "- Even when daily returns look larger, every tested family remains less deployable than the QQQ pair because the pair already has paper workflows, slippage work, and operational packets.",
    ]
    write_markdown(OUTPUTS["controls"], "\n".join(control_lines))

    ranking_lines = ["# Next Edge Research Ranking", ""]
    for row in score_df.itertuples():
        classification = next(item["classification"] for item in elimination_rows if item["template_key"] == row.template_key)
        ranking_lines.append(f"- `{row.template_key}`: score `{row.edge_survival_score:.4f}`; {classification}.")
    write_markdown(OUTPUTS["ranking"], "\n".join(ranking_lines))

    action_lines = [
        "# Next Edge Action Plan",
        "",
        "1. Continue papering `qqq_led_tqqq_sqqq_pair_opening_range_intraday_system` now as the best current operational candidate.",
        f"2. Make `{best_non_control['template_key']}` the next daily research priority.",
        f"3. Run a focused ex-NVDA rerun and cluster drill-down on `{best_non_control['template_key']}` before any promotion talk.",
        "4. Keep `down_streak_exhaustion` preserved as the confirmed daily benchmark/control.",
    ]
    demoted = [row["template_key"] for row in elimination_rows if row["classification"] == "fails and should be deprioritized"]
    if demoted:
        action_lines.append(f"5. Demote `{', '.join(demoted)}` until new evidence overturns the concentration or stability failures.")
    write_markdown(OUTPUTS["actions"], "\n".join(action_lines))

    print(json.dumps(
        {
            "opened_files": [row for row in exact_status if row["opened"]],
            "families_tested": ALL_DAILY_TEMPLATES,
            "googl_used": "GOOGL" in window_frame["symbol"].unique(),
            "top_raw_return_family": native_leaders.iloc[0]["template_key"],
            "top_edge_survival_family": best_survivor["template_key"],
            "survives_broadly": [row["template_key"] for row in elimination_rows if row["classification"] == "survives broadly"],
            "survives_nvda_specific": [row["template_key"] for row in elimination_rows if row["classification"] == "survives but mostly as NVDA-specific"],
            "fails": demoted,
            "next_research_priority": best_non_control["template_key"],
            "best_current_paper_candidate": "qqq_led_tqqq_sqqq_pair_opening_range_intraday_system",
            "outputs": {k: str(v) for k, v in OUTPUTS.items()},
        },
        indent=2,
        default=str,
    ))


if __name__ == "__main__":
    main()
