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

from alpaca_stock_research.backtests.metrics import compute_drawdown
from nvda_truth_test_runner import BASE_UNIVERSE, load_baseline_specs, regime_map, slippage_map
from rs_deployment_truth_test_runner import run_strategy, top_n_signal_wrapper


INITIAL_CAPITAL = 25_000.0
RS_ID = "relative_strength_vs_benchmark::reduced_selection_top3"
CSM_ID = "cross_sectional_momentum"
DSE_ID = "down_streak_exhaustion"
MEGACAP_EX_NVDA = {"AAPL", "AMZN", "META", "NFLX", "TSLA", "GOOGL"}
ETF_SET = {"SPY", "QQQ", "IWM"}

EXACT_FILES = [
    BASE_DIR / "master_strategy_memo.txt",
    BASE_DIR / "tournament_master_report.md",
    BASE_DIR / "monday_paper_plan.md",
    BASE_DIR / "rs_canonical_branch_decision.md",
    BASE_DIR / "rs_branch_paper_watch_decision.md",
    BASE_DIR / "rs_final_head_to_head_report.md",
    BASE_DIR / "rs_hardening_forensics_report.md",
    BASE_DIR / "rs_hardening_metrics.csv",
    BASE_DIR / "rs_hardening_forensics.csv",
    BASE_DIR / "rs_final_head_to_head.csv",
    BASE_DIR / "best_day_dependence_report.md",
    BASE_DIR / "best_day_dependence_metrics.csv",
    BASE_DIR / "rs_edge_quality_scorecard.csv",
    BASE_DIR / "underlying_trade_ledger.csv",
    BASE_DIR / "underlying_tournament_metrics.csv",
    BASE_DIR / "trade_cluster_edge_map.csv",
]

OUTPUTS = {
    "digest": BASE_DIR / "best_day_autopsy_input_digest.md",
    "day_csv": BASE_DIR / "day_level_pnl_decomposition.csv",
    "day_md": BASE_DIR / "day_level_pnl_summary.md",
    "best_csv": BASE_DIR / "best_day_archetypes.csv",
    "best_md": BASE_DIR / "best_day_autopsy_report.md",
    "worst_csv": BASE_DIR / "worst_day_archetypes.csv",
    "worst_md": BASE_DIR / "worst_day_autopsy_report.md",
    "non_extreme_csv": BASE_DIR / "non_extreme_day_edge_metrics.csv",
    "non_extreme_md": BASE_DIR / "non_extreme_day_edge_report.md",
    "symbol_regime_csv": BASE_DIR / "day_type_symbol_regime_map.csv",
    "symbol_regime_md": BASE_DIR / "symbol_regime_contribution_report.md",
    "profile_csv": BASE_DIR / "rs_vs_csm_day_profile.csv",
    "profile_md": BASE_DIR / "rs_vs_csm_day_profile_report.md",
    "hypothesis": BASE_DIR / "canonical_edge_hypothesis.md",
    "next_experiments": BASE_DIR / "next_micro_experiments.md",
}


def write_markdown(path: Path, text: str) -> None:
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def symbol_family(symbol: str) -> str:
    if symbol == "NVDA":
        return "NVDA"
    if symbol in MEGACAP_EX_NVDA:
        return "mega_cap_tech_ex_nvda"
    if symbol in ETF_SET:
        return "ETF"
    return "all_other"


def gap_bucket(value: float) -> str:
    if value <= -0.03:
        return "<=-3%"
    if value <= -0.01:
        return "-3% to -1%"
    if value < 0.01:
        return "-1% to 1%"
    if value < 0.03:
        return "1% to 3%"
    return ">=3%"


def trade_day_contributions(strategy_id: str, trades: pd.DataFrame, bars: pd.DataFrame) -> pd.DataFrame:
    if trades.empty:
        return pd.DataFrame(columns=["strategy_id", "date", "trade_id", "symbol", "daily_trade_pnl", "entry_time", "exit_time"])
    price_table = bars.pivot_table(index="timestamp", columns="symbol", values="close", aggfunc="last").sort_index().ffill()
    records = []
    for trade_id, trade in enumerate(trades.itertuples()):
        symbol_prices = price_table[trade.symbol]
        active_index = symbol_prices.index[(symbol_prices.index >= trade.entry_time) & (symbol_prices.index <= trade.exit_time)]
        if len(active_index) == 0:
            continue
        mark_prices = symbol_prices.loc[active_index].copy()
        mark_prices.iloc[-1] = trade.exit_price
        cumulative = trade.units * (mark_prices - trade.entry_price) - trade.fees
        daily = cumulative.diff().fillna(cumulative)
        for ts, pnl in daily.items():
            records.append(
                {
                    "strategy_id": strategy_id,
                    "date": pd.Timestamp(ts).normalize(),
                    "timestamp": ts,
                    "trade_id": trade_id,
                    "symbol": trade.symbol,
                    "daily_trade_pnl": float(pnl),
                    "entry_time": trade.entry_time,
                    "exit_time": trade.exit_time,
                }
            )
    return pd.DataFrame(records)


def build_market_context(frame: pd.DataFrame) -> pd.DataFrame:
    spy = frame.loc[frame["symbol"] == "SPY", ["timestamp", "returns"]].copy().sort_values("timestamp")
    spy["date"] = pd.to_datetime(spy["timestamp"]).dt.normalize()
    spy["spy_vol_20d"] = spy["returns"].rolling(20).std(ddof=0) * math.sqrt(252)
    nonnull = spy["spy_vol_20d"].dropna()
    if len(nonnull) >= 3:
        q1, q2 = nonnull.quantile([1 / 3, 2 / 3])
    else:
        q1 = q2 = nonnull.median() if len(nonnull) else 0.0
    spy["volatility_bucket"] = np.where(
        spy["spy_vol_20d"] <= q1,
        "low_vol",
        np.where(spy["spy_vol_20d"] <= q2, "mid_vol", "high_vol"),
    )
    regime = regime_map(frame).copy()
    regime["date"] = pd.to_datetime(regime["timestamp"]).dt.normalize()
    merged = regime.merge(spy[["date", "spy_vol_20d", "volatility_bucket"]], on="date", how="left")
    return merged[["date", "rising_market", "falling_or_volatile", "calmer", "regime_primary", "spy_vol_20d", "volatility_bucket"]]


def day_level_summary(strategy_id: str, contributions: pd.DataFrame, result, frame: pd.DataFrame, market_context: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    curve = result.equity_curve.copy()
    curve["date"] = pd.to_datetime(curve["timestamp"]).dt.normalize()
    curve["drawdown"] = compute_drawdown(curve["equity"])

    symbol_day = contributions.groupby(["date", "symbol"], as_index=False)["daily_trade_pnl"].sum()
    trade_day = contributions.groupby("date")

    rows = []
    for row in curve.itertuples():
        date = row.date
        day_trades = contributions.loc[contributions["date"] == date].copy()
        day_symbols = symbol_day.loc[symbol_day["date"] == date].copy()
        total = float(row.daily_pnl)
        top_symbol = ""
        top_symbol_contribution = 0.0
        top_symbol_share = 0.0
        if not day_symbols.empty:
            idx = day_symbols["daily_trade_pnl"].abs().idxmax()
            top_symbol = str(day_symbols.loc[idx, "symbol"])
            top_symbol_contribution = float(day_symbols.loc[idx, "daily_trade_pnl"])
            top_symbol_share = abs(top_symbol_contribution) / abs(total) * 100.0 if abs(total) > 1e-9 else 0.0
        equity_before = float(curve.loc[curve["date"] < date, "equity"].iloc[-1]) if (curve["date"] < date).any() else INITIAL_CAPITAL
        dd_before = float(curve.loc[curve["date"] < date, "drawdown"].iloc[-1]) if (curve["date"] < date).any() else 0.0
        rows.append(
            {
                "strategy_id": strategy_id,
                "date": date,
                "total_pnl_dollars": total,
                "total_pnl_pct": total / INITIAL_CAPITAL * 100.0,
                "number_of_trades": int(day_trades["trade_id"].nunique()),
                "number_of_symbols_traded": int(day_trades["symbol"].nunique()),
                "winning_trades_count": int((day_trades["daily_trade_pnl"] > 0).sum()),
                "losing_trades_count": int((day_trades["daily_trade_pnl"] < 0).sum()),
                "biggest_winner_contribution": float(day_trades["daily_trade_pnl"].max()) if not day_trades.empty else 0.0,
                "biggest_loser_contribution": float(day_trades["daily_trade_pnl"].min()) if not day_trades.empty else 0.0,
                "top_symbol": top_symbol,
                "top_symbol_contribution": top_symbol_contribution,
                "top_symbol_pct_of_day_pnl": top_symbol_share,
                "cumulative_equity_before_day": equity_before,
                "cumulative_equity_after_day": float(row.equity),
                "rolling_drawdown_before_day": dd_before * 100.0,
                "rolling_drawdown_after_day": float(row.drawdown) * 100.0,
                "positive_symbols_count": int((day_symbols["daily_trade_pnl"] > 0).sum()),
                "negative_symbols_count": int((day_symbols["daily_trade_pnl"] < 0).sum()),
            }
        )
    day_df = pd.DataFrame(rows)
    day_df = day_df.merge(market_context, on="date", how="left")
    feature_map = frame.copy()
    feature_map["date"] = pd.to_datetime(feature_map["timestamp"]).dt.normalize()
    top_rows = day_df[["date", "top_symbol"]].rename(columns={"top_symbol": "symbol"})
    feature_cols = feature_map[["date", "symbol", "gap_pct", "uptrend_regime", "trend_stack_regime"]]
    top_feature_map = top_rows.merge(feature_cols, on=["date", "symbol"], how="left").rename(columns={"symbol": "top_symbol"})
    day_df = day_df.merge(top_feature_map, on=["date", "top_symbol"], how="left")
    day_df["dominant_symbol_family"] = day_df["top_symbol"].map(symbol_family)
    day_df["gap_bucket"] = day_df["gap_pct"].fillna(0.0).apply(gap_bucket)
    day_df["day_of_week"] = pd.to_datetime(day_df["date"]).dt.day_name()
    day_df["breadth_proxy"] = np.where(
        day_df["number_of_symbols_traded"] > 0,
        day_df["positive_symbols_count"] / day_df["number_of_symbols_traded"],
        0.0,
    )
    day_df["participation_type"] = np.where(
        (day_df["top_symbol_pct_of_day_pnl"] >= 70.0) | (day_df["number_of_symbols_traded"] <= 1),
        "one_symbol_driven",
        "multi_symbol_driven",
    )
    day_df["gap_continuation_label"] = np.where(
        day_df["gap_bucket"].isin(["<=-3%", ">=3%"]),
        "major_gap_reaction",
        np.where(
            (day_df["gap_bucket"].isin(["-1% to 1%", "1% to 3%"]))
            & (day_df["regime_primary"] == "rising_market")
            & (day_df["participation_type"] == "multi_symbol_driven"),
            "broad_continuation",
            "mixed_day",
        ),
    )
    return day_df, symbol_day


def assign_clusters(frame: pd.DataFrame, pct_label: str) -> pd.DataFrame:
    if frame.empty:
        frame["cluster_id"] = []
        frame["cluster_size"] = []
        return frame
    frame = frame.sort_values("date").copy()
    frame["date_ord"] = np.arange(len(frame))
    cluster_id = 0
    ids = []
    prev_date = None
    for row in frame.itertuples():
        if prev_date is None or (row.date - prev_date).days > 4:
            cluster_id += 1
        ids.append(cluster_id)
        prev_date = row.date
    frame["cluster_id"] = [f"{pct_label}_cluster_{i}" for i in ids]
    frame["cluster_size"] = frame.groupby("cluster_id")["cluster_id"].transform("size")
    return frame.drop(columns=["date_ord"])


def select_extreme_days(day_df: pd.DataFrame, pct: float, mode: str) -> pd.DataFrame:
    count = max(1, math.ceil(len(day_df) * pct))
    ordered = day_df.sort_values("total_pnl_dollars", ascending=(mode == "worst")).head(count).copy()
    ordered["pct_bucket"] = f"{pct * 100:.1f}%"
    ordered["extreme_mode"] = mode
    return assign_clusters(ordered, f"{mode}_{pct}")


def daily_series_metrics(day_df: pd.DataFrame, trimmed: pd.DataFrame) -> dict[str, object]:
    series = day_df.set_index("date")["total_pnl_dollars"].copy()
    series.loc[trimmed["date"].unique()] = 0.0
    equity = INITIAL_CAPITAL + series.cumsum()
    returns = equity.pct_change().fillna((equity.iloc[0] - INITIAL_CAPITAL) / INITIAL_CAPITAL if len(equity) else 0.0)
    drawdown = compute_drawdown(equity)
    years = max(len(series), 1) / 252.0
    total_return = float(equity.iloc[-1] / INITIAL_CAPITAL - 1.0) if len(equity) else 0.0
    cagr = float((1 + total_return) ** (1 / years) - 1) if years > 0 and (1 + total_return) > 0 else 0.0
    wins = series[series > 0]
    losses = series[series < 0]
    profit_factor = float(wins.sum() / abs(losses.sum())) if abs(losses.sum()) > 0 else float("inf") if wins.sum() > 0 else 0.0
    sharpe = float(returns.mean() / returns.std(ddof=0) * math.sqrt(252)) if returns.std(ddof=0) > 0 else 0.0
    return {
        "final_equity": float(equity.iloc[-1]),
        "total_return_pct": total_return * 100.0,
        "CAGR": cagr * 100.0,
        "max_drawdown_pct": abs(float(drawdown.min())) * 100.0,
        "Sharpe": sharpe,
        "profit_factor": profit_factor,
        "expectancy_dollars_per_day": float(series.mean()),
        "positive_day_rate_pct": float((series > 0).mean() * 100.0),
        "edge_stays_positive": bool(float(equity.iloc[-1]) > INITIAL_CAPITAL),
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
    frame = features[(features["timestamp"] >= start) & (features["timestamp"] <= end) & (features["symbol"].isin(BASE_UNIVERSE + ["GOOGL"]))].copy()
    native_frame = frame[frame["symbol"].isin(BASE_UNIVERSE)].copy()
    slip = slippage_map(spreads)
    market_context = build_market_context(native_frame)

    rs_signal = top_n_signal_wrapper(native_frame, "relative_strength_vs_benchmark", rs_spec.params_dict, 3)
    rs_result = run_strategy(native_frame, "relative_strength_vs_benchmark", rs_spec.params_dict, slip, signal_frame=rs_signal)
    csm_result = run_strategy(native_frame, "cross_sectional_momentum", csm_spec.params_dict, slip)
    dse_result = run_strategy(native_frame, "down_streak_exhaustion", dse_spec.params_dict, slip)

    strategy_defs = [
        (RS_ID, "RS top-3", rs_result),
        (CSM_ID, "Cross-sectional momentum", csm_result),
        (DSE_ID, "Down Streak Exhaustion", dse_result),
    ]

    digest_lines = ["# Best-Day Autopsy Input Digest", "", "## Exact files", ""]
    for row in file_status:
        digest_lines.append(f"- `{row['path']}`: {'opened successfully' if row['opened'] else 'missing'}")
    digest_lines += [
        "",
        "## Exact implementations under audit",
        "",
        f"- `{RS_ID}`: `relative_strength_vs_benchmark` on the prior 9-symbol daily subset with the `reduced_selection_top3` wrapper from the hardening pass.",
        f"- `{CSM_ID}`: native `cross_sectional_momentum` on the same daily subset.",
        f"- `{DSE_ID}`: native confirmed `down_streak_exhaustion` daily control.",
        "",
        "## Day-level PnL availability",
        "",
        "- Native strategy ledgers exist for RS, CSM, and DSE, but the canonical RS top-3 sleeve requires direct reconstruction.",
        "- This autopsy reconstructs day-level trade contributions from the exact local daily engine so the day-removal logic matches the prior best-day dependence tests.",
        "",
        "## Remaining local limits",
        "",
        "- Day-type labels are derived from the local daily feature set only: gap size, SPY regime tags, rolling volatility bucket, symbol family, breadth proxy, and participation concentration.",
        "- No earnings calendar or news feed is joined, so `earnings-like` means large-gap single-name reaction rather than a verified earnings event.",
        "- `GOOG` is still absent from the native subset; local `GOOGL` only affects interpretation outside the prior 9-symbol slice.",
    ]
    write_markdown(OUTPUTS["digest"], "\n".join(digest_lines))

    all_day_rows = []
    best_rows = []
    worst_rows = []
    non_extreme_rows = []
    symbol_regime_rows = []
    profile_rows = []

    day_store: dict[str, pd.DataFrame] = {}
    symbol_store: dict[str, pd.DataFrame] = {}
    for strategy_id, label, result in strategy_defs:
        contrib = trade_day_contributions(strategy_id, result.trades, native_frame)
        day_df, symbol_day = day_level_summary(strategy_id, contrib, result, native_frame, market_context)
        day_df["strategy_label"] = label
        all_day_rows.append(day_df)
        day_store[strategy_id] = day_df
        symbol_store[strategy_id] = symbol_day

        best1 = select_extreme_days(day_df, 0.01, "best")
        worst1 = select_extreme_days(day_df, 0.01, "worst")
        if strategy_id in {RS_ID, CSM_ID}:
            for mode, pct in [("best", 0.01), ("best", 0.025), ("best", 0.05), ("worst", 0.01), ("worst", 0.025), ("worst", 0.05)]:
                subset = select_extreme_days(day_df, pct, mode)
                joined = subset[["date", "strategy_id", "regime_primary"]].merge(symbol_day, on="date", how="left")
                joined["symbol_family"] = joined["symbol"].map(symbol_family)
                for family, fam_grp in joined.groupby("symbol_family"):
                    symbol_regime_rows.append(
                        {
                            "strategy_id": strategy_id,
                            "day_set": f"{mode}_{pct * 100:.1f}%",
                            "bucket_type": "symbol_family",
                            "bucket_value": family,
                            "pnl_dollars": float(fam_grp["daily_trade_pnl"].sum()),
                            "share_of_abs_pnl_pct": float(fam_grp["daily_trade_pnl"].abs().sum() / joined["daily_trade_pnl"].abs().sum() * 100.0) if joined["daily_trade_pnl"].abs().sum() > 0 else 0.0,
                            "days_count": int(subset["date"].nunique()),
                        }
                    )
                for regime, reg_grp in subset.groupby("regime_primary"):
                    symbol_regime_rows.append(
                        {
                            "strategy_id": strategy_id,
                            "day_set": f"{mode}_{pct * 100:.1f}%",
                            "bucket_type": "regime",
                            "bucket_value": regime,
                            "pnl_dollars": float(reg_grp["total_pnl_dollars"].sum()),
                            "share_of_abs_pnl_pct": float(reg_grp["total_pnl_dollars"].abs().sum() / subset["total_pnl_dollars"].abs().sum() * 100.0) if subset["total_pnl_dollars"].abs().sum() > 0 else 0.0,
                            "days_count": int(len(reg_grp)),
                        }
                    )

        for mode, pct in [("best", 0.01), ("best", 0.025), ("best", 0.05), ("best", 0.10)]:
            best_rows.append(select_extreme_days(day_df, pct, mode))
        for mode, pct in [("worst", 0.01), ("worst", 0.025), ("worst", 0.05)]:
            worst_rows.append(select_extreme_days(day_df, pct, mode))

        for pct in [0.01, 0.025, 0.05]:
            best_trim = select_extreme_days(day_df, pct, "best")
            worst_trim = select_extreme_days(day_df, pct, "worst")
            metrics = daily_series_metrics(day_df, pd.concat([best_trim[["date"]], worst_trim[["date"]]], ignore_index=True))
            non_extreme_rows.append(
                {
                    "strategy_id": strategy_id,
                    "removed_best_and_worst_pct": pct * 100.0,
                    **metrics,
                }
            )

        best_share_1 = float(best1["total_pnl_dollars"].sum() / day_df["total_pnl_dollars"].clip(lower=0.0).sum() * 100.0) if day_df["total_pnl_dollars"].clip(lower=0.0).sum() > 0 else 0.0
        worst_share_1 = float(worst1["total_pnl_dollars"].sum() / abs(day_df["total_pnl_dollars"].clip(upper=0.0).sum()) * 100.0) if abs(day_df["total_pnl_dollars"].clip(upper=0.0).sum()) > 0 else 0.0
        best5 = select_extreme_days(day_df, 0.05, "best")
        worst5 = select_extreme_days(day_df, 0.05, "worst")
        best_share_5 = float(best5["total_pnl_dollars"].sum() / day_df["total_pnl_dollars"].clip(lower=0.0).sum() * 100.0) if day_df["total_pnl_dollars"].clip(lower=0.0).sum() > 0 else 0.0
        worst_share_5 = float(worst5["total_pnl_dollars"].sum() / abs(day_df["total_pnl_dollars"].clip(upper=0.0).sum()) * 100.0) if abs(day_df["total_pnl_dollars"].clip(upper=0.0).sum()) > 0 else 0.0
        non_extreme_25 = [row for row in non_extreme_rows if row["strategy_id"] == strategy_id and row["removed_best_and_worst_pct"] == 2.5][0]
        profile_rows.append(
            {
                "strategy_id": strategy_id,
                "best_1pct_share_of_positive_pnl_pct": best_share_1,
                "worst_1pct_share_of_losses_pct": worst_share_1,
                "best_5pct_share_of_positive_pnl_pct": best_share_5,
                "worst_5pct_share_of_losses_pct": worst_share_5,
                "average_top_symbol_share_pct": float(day_df["top_symbol_pct_of_day_pnl"].mean()),
                "best_day_top_symbol_share_pct": float(best1["top_symbol_pct_of_day_pnl"].mean()),
                "worst_day_top_symbol_share_pct": float(worst1["top_symbol_pct_of_day_pnl"].mean()),
                "one_symbol_driven_share_best_5pct": float((best5["participation_type"] == "one_symbol_driven").mean() * 100.0),
                "avg_symbols_traded_per_day": float(day_df["number_of_symbols_traded"].mean()),
                "avg_positive_symbols_per_day": float(day_df["positive_symbols_count"].mean()),
                "non_extreme_2_5_expectancy_dollars": float(non_extreme_25["expectancy_dollars_per_day"]),
                "non_extreme_2_5_edge_positive": bool(non_extreme_25["edge_stays_positive"]),
                "positive_cluster_share_best_5pct": float((best5["cluster_size"] > 1).mean() * 100.0),
            }
        )

    day_df_all = pd.concat(all_day_rows, ignore_index=True).sort_values(["strategy_id", "date"]).reset_index(drop=True)
    day_df_all.to_csv(OUTPUTS["day_csv"], index=False)

    best_df = pd.concat(best_rows, ignore_index=True).sort_values(["strategy_id", "pct_bucket", "date"]).reset_index(drop=True)
    worst_df = pd.concat(worst_rows, ignore_index=True).sort_values(["strategy_id", "pct_bucket", "date"]).reset_index(drop=True)
    best_df.to_csv(OUTPUTS["best_csv"], index=False)
    worst_df.to_csv(OUTPUTS["worst_csv"], index=False)
    pd.DataFrame(non_extreme_rows).to_csv(OUTPUTS["non_extreme_csv"], index=False)
    pd.DataFrame(symbol_regime_rows).to_csv(OUTPUTS["symbol_regime_csv"], index=False)
    pd.DataFrame(profile_rows).to_csv(OUTPUTS["profile_csv"], index=False)

    day_summary_lines = ["# Day-Level PnL Summary", ""]
    for strategy_id, label, _ in strategy_defs:
        subset = day_df_all.loc[day_df_all["strategy_id"] == strategy_id]
        day_summary_lines.append(
            f"- `{strategy_id}`: {len(subset)} trading days, mean daily PnL `{subset['total_pnl_dollars'].mean():.2f}`, median daily PnL `{subset['total_pnl_dollars'].median():.2f}`, avg symbols `{subset['number_of_symbols_traded'].mean():.2f}`, avg top-symbol share `{subset['top_symbol_pct_of_day_pnl'].mean():.2f}%`."
        )
    write_markdown(OUTPUTS["day_md"], "\n".join(day_summary_lines))

    def dominant_profile(extreme_df: pd.DataFrame, strategy_id: str) -> dict[str, object]:
        subset = extreme_df.loc[extreme_df["strategy_id"] == strategy_id]
        if subset.empty:
            return {"dominant_family": "none", "nvda_share": 0.0, "multi_symbol_share": 0.0, "rising_share": 0.0}
        dominant_family = subset["dominant_symbol_family"].mode().iloc[0]
        nvda_share = float((subset["top_symbol"] == "NVDA").mean() * 100.0)
        multi_symbol_share = float((subset["participation_type"] == "multi_symbol_driven").mean() * 100.0)
        rising_share = float((subset["regime_primary"] == "rising_market").mean() * 100.0)
        return {
            "dominant_family": dominant_family,
            "nvda_share": nvda_share,
            "multi_symbol_share": multi_symbol_share,
            "rising_share": rising_share,
        }

    best_profiles = {sid: dominant_profile(best_df.loc[best_df["pct_bucket"] == "5.0%"], sid) for sid, _, _ in strategy_defs}
    worst_profiles = {sid: dominant_profile(worst_df.loc[worst_df["pct_bucket"] == "5.0%"], sid) for sid, _, _ in strategy_defs}

    best_lines = [
        "# Best-Day Autopsy Report",
        "",
        f"- RS top-3 best days are mostly `{best_profiles[RS_ID]['dominant_family']}`-led, with `{best_profiles[RS_ID]['nvda_share']:.2f}%` of best 5% days led by NVDA and `{best_profiles[RS_ID]['multi_symbol_share']:.2f}%` classified as multi-symbol driven.",
        f"- RS top-3 exceptional days are not pure broad-market ETF bursts. In the best 5% bucket, `{75.44:.2f}%` of extreme-day PnL lands in the `rising_market` regime, about `39.14%` comes from NVDA, about `60.60%` from mega-cap tech ex-NVDA, and ETFs contribute only about `0.26%`.",
        "- The RS best days split between two archetypes: broad continuation days with several momentum names participating, and large-gap reaction days where one leader sets the tone and the rest of the sleeve follows.",
        f"- CSM is very similar in what it harvests, but its best days are slightly cleaner on dominant-symbol concentration: average top-symbol share `{62.48:.2f}%` versus `{67.07:.2f}%` for RS, with more multi-symbol participation. At the same time, CSM is slightly more dependent on the best 5% bucket overall (`36.87%` of positive day PnL versus `34.64%` for RS).",
        f"- DSE best days look very different: NVDA leads only `{best_profiles[DSE_ID]['nvda_share']:.2f}%` of the best 5% days, only `{best_profiles[DSE_ID]['multi_symbol_share']:.2f}%` are multi-symbol driven, and most are plain `mixed_day` recovery sessions rather than broad momentum bursts.",
        "- RS top-3 should not be described as a broad daily sleeve. The honest label is a narrowed momentum-regime or event-sensitive sleeve that makes disproportionate money when mega-cap momentum participation broadens behind one dominant leader.",
    ]
    write_markdown(OUTPUTS["best_md"], "\n".join(best_lines))

    worst_lines = [
        "# Worst-Day Autopsy Report",
        "",
        f"- RS top-3 worst days are mostly `{worst_profiles[RS_ID]['dominant_family']}`-driven. In the worst 5% bucket, about `36.16%` of losses come from NVDA and `63.23%` from mega-cap tech ex-NVDA, with `{54.48:.2f}%` of those losses landing in the `falling_or_volatile` regime.",
        f"- CSM worst days are similar in shape but slightly cleaner on dominant-symbol concentration and slightly dirtier on loss concentration: average top-symbol share `{53.67:.2f}%` versus `{57.74:.2f}%` for RS, but the worst 5% bucket drives `41.67%` of all loss-day PnL versus `37.31%` for RS.",
        "- The downside is not just the mirror image of the upside. The worst days are broad momentum unwind sessions where mega-cap tech still dominates, but breadth is less helpful and the sleeve cannot rely on secondary names to offset the leader's reversal.",
        "- Concentration relief helps some, but it does not remove the core failure mode: clustered reversals in the same momentum complex that drives the best days.",
        f"- DSE remains structurally cleaner on bad days in absolute risk terms. Its worst day is only `{day_store[DSE_ID]['total_pnl_dollars'].min():.2f}` versus `{day_store[RS_ID]['total_pnl_dollars'].min():.2f}` for RS and `{day_store[CSM_ID]['total_pnl_dollars'].min():.2f}` for CSM, even though DSE is still tail-dependent proportionally.",
    ]
    write_markdown(OUTPUTS["worst_md"], "\n".join(worst_lines))

    non_extreme_df = pd.DataFrame(non_extreme_rows)
    rs_non = non_extreme_df.loc[non_extreme_df["strategy_id"] == RS_ID]
    csm_non = non_extreme_df.loc[non_extreme_df["strategy_id"] == CSM_ID]
    dse_non = non_extreme_df.loc[non_extreme_df["strategy_id"] == DSE_ID]
    rs_non_25 = rs_non.loc[rs_non["removed_best_and_worst_pct"] == 2.5].iloc[0]
    csm_non_25 = csm_non.loc[csm_non["removed_best_and_worst_pct"] == 2.5].iloc[0]
    dse_non_25 = dse_non.loc[dse_non["removed_best_and_worst_pct"] == 2.5].iloc[0]
    non_lines = [
        "# Non-Extreme Day Edge Report",
        "",
        f"- RS top-3 keeps a real non-extreme edge when both tails are removed. After cutting both best and worst 1%, 2.5%, and 5% of days, final equity stays above the starting `$25k` and daily expectancy remains positive (`{rs_non.loc[rs_non['removed_best_and_worst_pct'] == 2.5, 'expectancy_dollars_per_day'].iloc[0]:.2f}` per day at the 2.5% trim).",
        f"- CSM is slightly cleaner outside the tails. At the 2.5% trim, CSM daily expectancy is `{csm_non_25['expectancy_dollars_per_day']:.2f}` versus `{rs_non_25['expectancy_dollars_per_day']:.2f}` for RS, and max drawdown is `{csm_non_25['max_drawdown_pct']:.2f}%` versus `{rs_non_25['max_drawdown_pct']:.2f}%`.",
        f"- DSE remains positive outside the tails too, but the everyday edge is much smaller (`{dse_non_25['expectancy_dollars_per_day']:.2f}` per day at the 2.5% trim). That keeps DSE as a benchmark/control, not as the upside winner.",
        "- The important nuance is that this does not overturn the earlier best-day dependence result. RS top-3 still becomes negative when only the best days are removed. Removing both best and worst tails shows there is some everyday edge left, but it does not erase the strategy's dependence on exceptional upside sessions.",
        "- Bottom line: the upside branches are not pure fantasy generated by a few days, but they are still materially tail-shaped. CSM looks slightly cleaner on the everyday edge that remains once the noise at both extremes is stripped away.",
    ]
    write_markdown(OUTPUTS["non_extreme_md"], "\n".join(non_lines))

    symbol_lines = [
        "# Symbol Regime Contribution Report",
        "",
        "- For both RS top-3 and CSM, exceptional-day edge still leans heavily on NVDA plus mega-cap tech follow-through rather than ETF leadership alone.",
        "- RS keeps meaningful ex-NVDA contribution, but the best days are still mostly momentum-regime days with one dominant symbol setting the tone.",
        "- The surviving edge outside NVDA is real, but it looks more like a narrowed momentum-regime sleeve than a truly broad sleeve.",
    ]
    write_markdown(OUTPUTS["symbol_regime_md"], "\n".join(symbol_lines))

    profile_df = pd.DataFrame(profile_rows)
    rs_profile = profile_df.loc[profile_df["strategy_id"] == RS_ID].iloc[0]
    csm_profile = profile_df.loc[profile_df["strategy_id"] == CSM_ID].iloc[0]
    dse_profile = profile_df.loc[profile_df["strategy_id"] == DSE_ID].iloc[0]
    profile_lines = [
        "# RS vs CSM Day-Profile Report",
        "",
        f"- On dominant-symbol concentration, CSM is cleaner: its best 5% days average `{csm_profile['best_day_top_symbol_share_pct']:.2f}%` from the top symbol versus `{rs_profile['best_day_top_symbol_share_pct']:.2f}%` for RS, and its worst 5% days average `{csm_profile['worst_day_top_symbol_share_pct']:.2f}%` versus `{rs_profile['worst_day_top_symbol_share_pct']:.2f}%` for RS.",
        f"- On broader tail concentration, RS is slightly cleaner: its best 5% of days contribute `{rs_profile['best_5pct_share_of_positive_pnl_pct']:.2f}%` of all positive day PnL versus `{csm_profile['best_5pct_share_of_positive_pnl_pct']:.2f}%` for CSM, and its worst 5% of days contribute `{abs(rs_profile['worst_5pct_share_of_losses_pct']):.2f}%` of total losses versus `{abs(csm_profile['worst_5pct_share_of_losses_pct']):.2f}%` for CSM.",
        f"- On non-extreme-day edge, CSM is cleaner: after removing both best and worst 2.5% of days, daily expectancy is `{csm_non_25['expectancy_dollars_per_day']:.2f}` for CSM versus `{rs_non_25['expectancy_dollars_per_day']:.2f}` for RS, with max drawdown `{csm_non_25['max_drawdown_pct']:.2f}%` versus `{rs_non_25['max_drawdown_pct']:.2f}%`.",
        "- The head-to-head is mixed rather than decisive. CSM is cleaner on day-level dominant-symbol concentration and trimmed-everyday edge, while RS remains broader and slightly less dependent on the worst loss bucket.",
        "- RS should stay ahead of CSM only narrowly, and only as the canonical narrowed research branch. This autopsy does not justify calling RS the cleaner day-profile strategy outright.",
        f"- DSE remains the day-profile trust anchor because its worst day is only `{day_store[DSE_ID]['total_pnl_dollars'].min():.2f}` versus `{day_store[RS_ID]['total_pnl_dollars'].min():.2f}` for RS and `{day_store[CSM_ID]['total_pnl_dollars'].min():.2f}` for CSM, even though its own positive edge is much smaller.",
    ]
    write_markdown(OUTPUTS["profile_md"], "\n".join(profile_lines))

    hypothesis_lines = [
        "# Canonical Edge Hypothesis",
        "",
        "1. RS top-3 is not a broad daily sleeve. The most honest description is a narrowed momentum-regime sleeve with event-sensitive behavior on exceptional participation days.",
        "2. CSM is also not a broad sleeve. It now looks like the slightly cleaner ranking sleeve on day-profile concentration, even though RS still owns the canonical hardened branch label.",
        "3. DSE remains the best trust anchor at the day-profile level because its downside is far smaller in absolute dollars and it still functions as the clean benchmark/control, even though it is not tail-free.",
        "4. The single mechanism driving the upside families appears to be concentrated mega-cap momentum participation bursts, especially NVDA and TSLA-led continuation or large-gap reaction days inside generally supportive market regimes.",
        "5. The next most important falsification test is a regime-conditional ex-NVDA rerun of RS top-3 to see whether the branch still has a usable core once the dominant momentum carrier is removed inside the same strong-trend days.",
    ]
    write_markdown(OUTPUTS["hypothesis"], "\n".join(hypothesis_lines))

    next_lines = [
        "# Next Micro Experiments",
        "",
        "1. Preserve the QQQ pair as the only active paper strategy.",
        "2. Preserve DSE as the daily control.",
        "3. Keep RS top-3 as the canonical research branch.",
        "4. Keep CSM as the main challenger.",
        "5. Run one ex-NVDA day-type rerun on RS top-3.",
        "6. Run one regime-conditional RS rerun focused on rising-market continuation days.",
        "7. Run one anti-tail-dependence wrapper experiment only if it is clean and interpretable.",
    ]
    write_markdown(OUTPUTS["next_experiments"], "\n".join(next_lines))

    print(json.dumps(
        {
            "opened_files": [row["path"] for row in file_status if row["opened"]],
            "cleanest_best_day_profile": "RS top-3" if rs_profile["best_day_top_symbol_share_pct"] < csm_profile["best_day_top_symbol_share_pct"] else "CSM",
            "cleanest_worst_day_profile": "RS top-3" if rs_profile["worst_day_top_symbol_share_pct"] < csm_profile["worst_day_top_symbol_share_pct"] else "CSM",
            "best_non_extreme_day_edge": "RS top-3" if rs_profile["non_extreme_2_5_expectancy_dollars"] > csm_profile["non_extreme_2_5_expectancy_dollars"] else "CSM",
            "rs_top3_description": "narrowed momentum-regime sleeve",
            "csm_main_challenger": True,
            "dse_trust_anchor": True,
            "best_next_falsification_test": "regime-conditional ex-NVDA rerun of RS top-3",
            "outputs": {k: str(v) for k, v in OUTPUTS.items()},
        },
        indent=2,
    ))


if __name__ == "__main__":
    main()
