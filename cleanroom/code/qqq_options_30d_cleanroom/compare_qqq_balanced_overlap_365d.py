from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from backtest_qqq_greeks_portfolio import (
    build_delta_strategies,
    build_regime_map,
    generate_candidate_trades,
    load_dense_data,
    summarize_regimes,
)
from backtest_qqq_option_strategies import (
    build_day_contexts,
    load_daily_universe,
    load_wide_data,
)
from backtest_qqq_regime_gated_portfolio import filter_candidate_trades
from evaluate_qqq_direct_greeks_readiness import run_overlay_allocator
from optimize_qqq_regime_portfolio import relabel_candidate_trades


DEFAULT_OUTPUT_DIR = Path(__file__).resolve().parent / "output"
DEFAULT_CONFIG_PATH = DEFAULT_OUTPUT_DIR / "qqq_direct_greeks_balanced_deployment_config.json"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the balanced deployment book on the 365-day cleanroom dataset and compare it with the direct-Greeks overlap window."
    )
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--config-path", default=str(DEFAULT_CONFIG_PATH))
    parser.add_argument("--wide-name", default="qqq_365d_option_1min_wide_backtest.parquet")
    parser.add_argument("--dense-name", default="qqq_365d_option_1min_dense.parquet")
    parser.add_argument("--daily-universe-name", default="qqq_365d_option_daily_universe.parquet")
    parser.add_argument("--direct-candidate-name", default="qqq_direct_greeks_candidate_trades.csv")
    parser.add_argument("--direct-day-returns-name", default="qqq_direct_greeks_day_returns.csv")
    parser.add_argument("--start-date")
    parser.add_argument("--end-date")
    parser.add_argument("--cleanroom-candidate-name", default="qqq_365d_balanced_overlap_candidate_trades.csv")
    parser.add_argument("--cleanroom-filtered-name", default="qqq_365d_balanced_overlap_filtered_candidates.csv")
    parser.add_argument("--cleanroom-day-returns-name", default="qqq_365d_balanced_overlap_day_returns.csv")
    parser.add_argument("--cleanroom-regime-summary-name", default="qqq_365d_balanced_overlap_regime_summary.csv")
    parser.add_argument("--cleanroom-trades-name", default="qqq_365d_balanced_overlap_portfolio_trades.csv")
    parser.add_argument("--cleanroom-equity-name", default="qqq_365d_balanced_overlap_equity_curve.csv")
    parser.add_argument("--cleanroom-summary-name", default="qqq_365d_balanced_overlap_summary.json")
    parser.add_argument("--direct-filtered-name", default="qqq_direct_greeks_balanced_overlap_filtered_candidates.csv")
    parser.add_argument("--direct-trades-name", default="qqq_direct_greeks_balanced_overlap_portfolio_trades.csv")
    parser.add_argument("--direct-equity-name", default="qqq_direct_greeks_balanced_overlap_equity_curve.csv")
    parser.add_argument("--direct-summary-name", default="qqq_direct_greeks_balanced_overlap_summary.json")
    parser.add_argument("--comparison-scorecard-name", default="qqq_balanced_overlap_dataset_scorecard.csv")
    parser.add_argument("--comparison-daily-name", default="qqq_balanced_overlap_daily_pnl_compare.csv")
    parser.add_argument("--comparison-candidate-diff-name", default="qqq_balanced_overlap_candidate_key_diff.csv")
    parser.add_argument("--comparison-summary-name", default="qqq_balanced_overlap_dataset_comparison_summary.json")
    parser.add_argument("--comparison-report-name", default="qqq_balanced_overlap_dataset_comparison_report.md")
    return parser


def load_balanced_config(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return {
        "threshold_pct": float(payload["regime"]["threshold_pct"]),
        "selected": {
            "bull": list(payload["regime"]["bull_strategies"]),
            "bear": list(payload["regime"]["bear_strategies"]),
            "choppy": list(payload["regime"]["choppy_strategies"]),
        },
        "portfolio": dict(payload["portfolio"]),
        "raw": payload,
    }


def selected_strategy_objects(selected: dict[str, list[str]]) -> list:
    strategy_map = {strategy.name: strategy for strategy in build_delta_strategies()}
    names = sorted(
        {
            strategy_name
            for regime_name in ["bull", "bear", "choppy"]
            for strategy_name in selected[regime_name]
        }
    )
    return [strategy_map[name] for name in names]


def normalize_legs_json(trades: pd.DataFrame) -> pd.DataFrame:
    if trades.empty:
        return trades.copy()

    normalized_rows: list[dict[str, object]] = []
    for row in trades.itertuples(index=False):
        legs = json.loads(str(row.legs_json))
        normalized_legs: list[dict[str, object]] = []
        for leg in legs:
            leg_copy = dict(leg)
            normalized_legs.append(
                {
                    **leg_copy,
                    "dte": int(row.dte),
                    "theta_daily": float(leg_copy["theta"]) if "theta" in leg_copy else None,
                    "vega_1pct": float(leg_copy["vega"]) if "vega" in leg_copy else None,
                    "rho_1pct": None,
                    "selection_method": "cleanroom_bar_iv",
                    "calc_status": "derived_from_price",
                    "calc_quality_tier": "cleanroom_iv",
                    "entry_has_trade_bar": True,
                }
            )
        normalized_rows.append(
            {
                **row._asdict(),
                "legs_json": json.dumps(normalized_legs, sort_keys=True),
            }
        )
    normalized = pd.DataFrame(normalized_rows)
    normalized["trade_date"] = pd.to_datetime(normalized["trade_date"]).dt.date
    return normalized


def build_day_returns_from_wide(wide: pd.DataFrame, threshold: float) -> pd.DataFrame:
    daily = (
        wide.groupby("trade_date", as_index=False)
        .agg(day_open=("qqq_open", "first"), day_close=("qqq_close", "last"))
        .sort_values("trade_date")
        .reset_index(drop=True)
    )
    daily["day_ret_pct"] = (daily["day_close"] / daily["day_open"] - 1.0) * 100.0
    daily["regime"] = pd.cut(
        daily["day_ret_pct"],
        bins=[float("-inf"), -threshold, threshold, float("inf")],
        labels=["bear", "choppy", "bull"],
        right=True,
    ).astype(str)
    return daily


def run_cleanroom_overlap(
    output_dir: Path,
    config: dict[str, object],
    start_date: str,
    end_date: str,
    wide_name: str,
    dense_name: str,
    daily_universe_name: str,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, dict[str, object]]:
    wide = load_wide_data(output_dir / wide_name)
    wide = wide[
        (wide["trade_date"] >= pd.to_datetime(start_date).date())
        & (wide["trade_date"] <= pd.to_datetime(end_date).date())
    ].copy()
    if wide.empty:
        raise RuntimeError("No 365-day cleanroom rows were available inside the overlap window.")

    _, _, available_dtes = load_daily_universe(output_dir / daily_universe_name)
    day_contexts = build_day_contexts(wide=wide, available_dtes=available_dtes)
    valid_trade_dates = {ctx.trade_date for ctx in day_contexts}
    if not valid_trade_dates:
        raise RuntimeError("No full RTH sessions were available in the cleanroom overlap window.")

    chain_index, price_index = load_dense_data(
        path=output_dir / dense_name,
        valid_trade_dates=valid_trade_dates,
        wide=wide,
    )
    regime_map = build_regime_map(wide)
    strategies = selected_strategy_objects(config["selected"])
    candidate_trades = generate_candidate_trades(
        strategies=strategies,
        day_contexts=day_contexts,
        chain_index=chain_index,
        price_index=price_index,
        regime_map=regime_map,
    )
    candidate_trades = normalize_legs_json(candidate_trades)
    filtered = filter_candidate_trades(candidate_trades, config["selected"])
    day_returns = build_day_returns_from_wide(wide=wide, threshold=float(config["threshold_pct"]))
    regime_summary = summarize_regimes(candidate_trades)
    portfolio_trades, equity_curve, portfolio_summary = run_overlay_allocator(
        strategies=strategies,
        trades_df=filtered,
        risk_cap=float(config["portfolio"]["risk_cap"]),
        daily_loss_gate_pct=float(config["portfolio"]["daily_loss_gate_pct"]),
        max_open_positions=None
        if config["portfolio"]["max_open_positions"] is None
        else int(config["portfolio"]["max_open_positions"]),
        delever_drawdown_pct=float(config["portfolio"]["delever_drawdown_pct"]),
        delever_risk_scale=float(config["portfolio"]["delever_risk_scale"]),
    )
    summary = {
        "dataset": "cleanroom_365d",
        "start_date": start_date,
        "end_date": end_date,
        "candidate_trade_count": int(len(candidate_trades)),
        "filtered_trade_count": int(len(filtered)),
        "day_count": int(len(day_returns)),
        "regime_counts": day_returns["regime"].value_counts().sort_index().to_dict(),
        **portfolio_summary,
    }
    return candidate_trades, filtered, day_returns, regime_summary, portfolio_trades, equity_curve, summary


def run_direct_overlap(
    output_dir: Path,
    config: dict[str, object],
    start_date: str,
    end_date: str,
    direct_candidate_name: str,
    direct_day_returns_name: str,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict[str, object]]:
    candidate_trades = pd.read_csv(output_dir / direct_candidate_name)
    candidate_trades["trade_date"] = pd.to_datetime(candidate_trades["trade_date"]).dt.date
    mask = (
        (candidate_trades["trade_date"] >= pd.to_datetime(start_date).date())
        & (candidate_trades["trade_date"] <= pd.to_datetime(end_date).date())
    )
    candidate_trades = candidate_trades.loc[mask].copy()

    day_returns = pd.read_csv(output_dir / direct_day_returns_name)
    day_returns["trade_date"] = pd.to_datetime(day_returns["trade_date"]).dt.date
    day_returns = day_returns[
        (day_returns["trade_date"] >= pd.to_datetime(start_date).date())
        & (day_returns["trade_date"] <= pd.to_datetime(end_date).date())
    ].copy()
    day_return_map = dict(zip(day_returns["trade_date"], day_returns["day_ret_pct"]))
    candidate_trades = relabel_candidate_trades(
        candidate_trades=candidate_trades,
        day_return_map=day_return_map,
        threshold=float(config["threshold_pct"]),
    )

    filtered = filter_candidate_trades(candidate_trades, config["selected"])
    strategies = selected_strategy_objects(config["selected"])
    portfolio_trades, equity_curve, portfolio_summary = run_overlay_allocator(
        strategies=strategies,
        trades_df=filtered,
        risk_cap=float(config["portfolio"]["risk_cap"]),
        daily_loss_gate_pct=float(config["portfolio"]["daily_loss_gate_pct"]),
        max_open_positions=None
        if config["portfolio"]["max_open_positions"] is None
        else int(config["portfolio"]["max_open_positions"]),
        delever_drawdown_pct=float(config["portfolio"]["delever_drawdown_pct"]),
        delever_risk_scale=float(config["portfolio"]["delever_risk_scale"]),
    )
    summary = {
        "dataset": "direct_greeks",
        "start_date": start_date,
        "end_date": end_date,
        "candidate_trade_count": int(len(candidate_trades)),
        "filtered_trade_count": int(len(filtered)),
        "day_count": int(len(day_returns)),
        "regime_counts": day_returns["regime"].value_counts().sort_index().to_dict(),
        **portfolio_summary,
    }
    return filtered, portfolio_trades, equity_curve, summary


def compute_candidate_diff(cleanroom_filtered: pd.DataFrame, direct_filtered: pd.DataFrame) -> pd.DataFrame:
    left = cleanroom_filtered.copy()
    right = direct_filtered.copy()
    left["trade_date"] = pd.to_datetime(left["trade_date"]).dt.date
    right["trade_date"] = pd.to_datetime(right["trade_date"]).dt.date

    left["candidate_key"] = left.apply(
        lambda row: f"{row['trade_date']}|{row['strategy']}|{int(row['entry_minute'])}|{int(row['dte'])}",
        axis=1,
    )
    right["candidate_key"] = right.apply(
        lambda row: f"{row['trade_date']}|{row['strategy']}|{int(row['entry_minute'])}|{int(row['dte'])}",
        axis=1,
    )

    left_export = left[
        [
            "candidate_key",
            "trade_date",
            "strategy",
            "regime",
            "entry_minute",
            "dte",
            "entry_cash_per_combo",
            "net_pnl_per_combo",
        ]
    ].rename(
        columns={
            "trade_date": "trade_date_cleanroom",
            "strategy": "strategy_cleanroom",
            "regime": "regime_cleanroom",
            "entry_minute": "entry_minute_cleanroom",
            "dte": "dte_cleanroom",
        }
    )
    right_export = right[
        [
            "candidate_key",
            "trade_date",
            "strategy",
            "regime",
            "entry_minute",
            "dte",
            "entry_cash_per_combo",
            "net_pnl_per_combo",
        ]
    ].rename(
        columns={
            "trade_date": "trade_date_direct",
            "strategy": "strategy_direct",
            "regime": "regime_direct",
            "entry_minute": "entry_minute_direct",
            "dte": "dte_direct",
        }
    )

    merged = left_export.merge(
        right_export,
        on="candidate_key",
        how="outer",
        suffixes=("_cleanroom", "_direct"),
        indicator=True,
    )

    merged["trade_date"] = merged["trade_date_cleanroom"].where(
        merged["trade_date_cleanroom"].notna(), merged["trade_date_direct"]
    )
    merged["strategy"] = merged["strategy_cleanroom"].where(
        merged["strategy_cleanroom"].notna(), merged["strategy_direct"]
    )
    merged["regime"] = merged["regime_cleanroom"].where(
        merged["regime_cleanroom"].notna(), merged["regime_direct"]
    )
    merged["entry_minute"] = merged["entry_minute_cleanroom"].where(
        merged["entry_minute_cleanroom"].notna(), merged["entry_minute_direct"]
    )
    merged["dte"] = merged["dte_cleanroom"].where(
        merged["dte_cleanroom"].notna(), merged["dte_direct"]
    )
    merged["entry_cash_diff"] = merged["entry_cash_per_combo_cleanroom"] - merged["entry_cash_per_combo_direct"]
    merged["net_pnl_diff"] = merged["net_pnl_per_combo_cleanroom"] - merged["net_pnl_per_combo_direct"]
    return merged.sort_values(["trade_date", "strategy", "entry_minute"], na_position="last").reset_index(drop=True)


def portfolio_daily_pnl(trades: pd.DataFrame, label: str) -> pd.DataFrame:
    if trades.empty:
        return pd.DataFrame(columns=["trade_date", f"{label}_daily_pnl"])
    daily = (
        trades.groupby("trade_date", as_index=False)["portfolio_net_pnl"]
        .sum()
        .rename(columns={"portfolio_net_pnl": f"{label}_daily_pnl"})
    )
    daily["trade_date"] = pd.to_datetime(daily["trade_date"]).dt.date
    return daily


def build_scorecard(cleanroom_summary: dict[str, object], direct_summary: dict[str, object]) -> pd.DataFrame:
    return pd.DataFrame([cleanroom_summary, direct_summary])[
        [
            "dataset",
            "start_date",
            "end_date",
            "day_count",
            "candidate_trade_count",
            "filtered_trade_count",
            "trade_count",
            "win_rate_pct",
            "final_equity",
            "total_return_pct",
            "max_drawdown_pct",
            "calmar_like",
        ]
    ]


def build_comparison_summary(
    cleanroom_summary: dict[str, object],
    direct_summary: dict[str, object],
    candidate_diff: pd.DataFrame,
    daily_compare: pd.DataFrame,
) -> dict[str, object]:
    matched = candidate_diff[candidate_diff["_merge"] == "both"].copy()
    common_days = daily_compare.dropna(subset=["cleanroom_daily_pnl", "direct_daily_pnl"]).copy()
    daily_corr = None
    if len(common_days) >= 2:
        daily_corr = float(common_days["cleanroom_daily_pnl"].corr(common_days["direct_daily_pnl"]))

    return {
        "window_start": cleanroom_summary["start_date"],
        "window_end": cleanroom_summary["end_date"],
        "cleanroom_summary": cleanroom_summary,
        "direct_summary": direct_summary,
        "candidate_overlap": {
            "matched_candidate_count": int((candidate_diff["_merge"] == "both").sum()),
            "cleanroom_only_candidate_count": int((candidate_diff["_merge"] == "left_only").sum()),
            "direct_only_candidate_count": int((candidate_diff["_merge"] == "right_only").sum()),
            "match_rate_vs_direct_pct": round(
                100.0 * int((candidate_diff["_merge"] == "both").sum()) / max(1, direct_summary["filtered_trade_count"]),
                2,
            ),
            "matched_entry_cash_mae": round(
                float(matched["entry_cash_diff"].abs().mean()) if not matched.empty else 0.0,
                4,
            ),
            "matched_net_pnl_mae": round(
                float(matched["net_pnl_diff"].abs().mean()) if not matched.empty else 0.0,
                4,
            ),
        },
        "daily_portfolio_pnl": {
            "common_days": int(len(common_days)),
            "daily_pnl_correlation": None if daily_corr is None else round(daily_corr, 4),
            "daily_pnl_mae": round(
                float((common_days["cleanroom_daily_pnl"] - common_days["direct_daily_pnl"]).abs().mean())
                if not common_days.empty
                else 0.0,
                4,
            ),
        },
        "metric_deltas": {
            "final_equity_delta": round(float(cleanroom_summary["final_equity"]) - float(direct_summary["final_equity"]), 2),
            "return_pct_delta": round(float(cleanroom_summary["total_return_pct"]) - float(direct_summary["total_return_pct"]), 2),
            "max_drawdown_pct_delta": round(float(cleanroom_summary["max_drawdown_pct"]) - float(direct_summary["max_drawdown_pct"]), 2),
            "trade_count_delta": int(cleanroom_summary["trade_count"]) - int(direct_summary["trade_count"]),
        },
    }


def write_report(
    path: Path,
    comparison_summary: dict[str, object],
    scorecard: pd.DataFrame,
) -> None:
    cleanroom = comparison_summary["cleanroom_summary"]
    direct = comparison_summary["direct_summary"]
    candidate_overlap = comparison_summary["candidate_overlap"]
    daily = comparison_summary["daily_portfolio_pnl"]
    metric_deltas = comparison_summary["metric_deltas"]

    lines: list[str] = []
    lines.append("# Balanced Book Overlap Comparison")
    lines.append("")
    lines.append(
        f"- Overlap window: {comparison_summary['window_start']} through {comparison_summary['window_end']}"
    )
    lines.append("- Strategy book: balanced deployment config with bull, bear, and choppy sleeves plus overlay risk rules.")
    lines.append("- Datasets compared: 365-day cleanroom bars with derived Greeks versus direct-Greeks candidate trades.")
    lines.append("")
    lines.append("## Scorecard")
    lines.append("")
    for row in scorecard.itertuples(index=False):
        lines.append(
            f"- `{row.dataset}`: final ${row.final_equity:.2f}, return {row.total_return_pct:.2f}%, drawdown {row.max_drawdown_pct:.2f}%, trades {int(row.trade_count)}, win rate {row.win_rate_pct:.2f}%."
        )
    lines.append("")
    lines.append("## Candidate Alignment")
    lines.append("")
    lines.append(f"- Matched filtered candidates: {candidate_overlap['matched_candidate_count']}")
    lines.append(f"- Cleanroom-only filtered candidates: {candidate_overlap['cleanroom_only_candidate_count']}")
    lines.append(f"- Direct-only filtered candidates: {candidate_overlap['direct_only_candidate_count']}")
    lines.append(f"- Match rate versus direct filtered set: {candidate_overlap['match_rate_vs_direct_pct']:.2f}%")
    lines.append(f"- Matched entry cash MAE: ${candidate_overlap['matched_entry_cash_mae']:.4f}")
    lines.append(f"- Matched net PnL per combo MAE: ${candidate_overlap['matched_net_pnl_mae']:.4f}")
    lines.append("")
    lines.append("## Portfolio Alignment")
    lines.append("")
    lines.append(f"- Final equity delta (cleanroom - direct): ${metric_deltas['final_equity_delta']:.2f}")
    lines.append(f"- Return delta: {metric_deltas['return_pct_delta']:.2f} points")
    lines.append(f"- Drawdown delta: {metric_deltas['max_drawdown_pct_delta']:.2f} points")
    lines.append(f"- Trade count delta: {metric_deltas['trade_count_delta']}")
    if daily["daily_pnl_correlation"] is None:
        lines.append("- Daily portfolio PnL correlation: not enough shared active days.")
    else:
        lines.append(f"- Daily portfolio PnL correlation: {daily['daily_pnl_correlation']:.4f}")
    lines.append(f"- Daily portfolio PnL MAE: ${daily['daily_pnl_mae']:.4f}")
    lines.append("")
    lines.append("## Read")
    lines.append("")
    if cleanroom["total_return_pct"] >= direct["total_return_pct"] * 0.8 and daily["daily_pnl_correlation"] not in (None,):
        lines.append("- The cleanroom year broadly confirms the deployment book if candidate overlap and daily PnL correlation stay reasonably tight.")
    else:
        lines.append("- The cleanroom year diverges enough that we should treat it as a reconciliation task before live automation, not just a confirmation run.")

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    args = build_parser().parse_args()
    output_dir = Path(args.output_dir).resolve()
    config = load_balanced_config(Path(args.config_path).resolve())

    direct_day_returns = pd.read_csv(output_dir / args.direct_day_returns_name)
    direct_day_returns["trade_date"] = pd.to_datetime(direct_day_returns["trade_date"]).dt.date
    cleanroom_wide = load_wide_data(output_dir / args.wide_name)
    cleanroom_dates = sorted(cleanroom_wide["trade_date"].unique().tolist())
    direct_dates = sorted(direct_day_returns["trade_date"].unique().tolist())
    common_start = max(cleanroom_dates[0], direct_dates[0])
    common_end = min(cleanroom_dates[-1], direct_dates[-1])

    start_date = args.start_date or common_start.isoformat()
    end_date = args.end_date or common_end.isoformat()

    cleanroom_candidate_trades, cleanroom_filtered, cleanroom_day_returns, cleanroom_regime_summary, cleanroom_portfolio_trades, cleanroom_equity_curve, cleanroom_summary = run_cleanroom_overlap(
        output_dir=output_dir,
        config=config,
        start_date=start_date,
        end_date=end_date,
        wide_name=args.wide_name,
        dense_name=args.dense_name,
        daily_universe_name=args.daily_universe_name,
    )
    direct_filtered, direct_portfolio_trades, direct_equity_curve, direct_summary = run_direct_overlap(
        output_dir=output_dir,
        config=config,
        start_date=start_date,
        end_date=end_date,
        direct_candidate_name=args.direct_candidate_name,
        direct_day_returns_name=args.direct_day_returns_name,
    )

    candidate_diff = compute_candidate_diff(
        cleanroom_filtered=cleanroom_filtered,
        direct_filtered=direct_filtered,
    )
    daily_compare = portfolio_daily_pnl(cleanroom_portfolio_trades, "cleanroom").merge(
        portfolio_daily_pnl(direct_portfolio_trades, "direct"),
        on="trade_date",
        how="outer",
    ).sort_values("trade_date").reset_index(drop=True)
    scorecard = build_scorecard(cleanroom_summary=cleanroom_summary, direct_summary=direct_summary)
    comparison_summary = build_comparison_summary(
        cleanroom_summary=cleanroom_summary,
        direct_summary=direct_summary,
        candidate_diff=candidate_diff,
        daily_compare=daily_compare,
    )

    cleanroom_candidate_trades.to_csv(output_dir / args.cleanroom_candidate_name, index=False)
    cleanroom_filtered.to_csv(output_dir / args.cleanroom_filtered_name, index=False)
    cleanroom_day_returns.to_csv(output_dir / args.cleanroom_day_returns_name, index=False)
    cleanroom_regime_summary.to_csv(output_dir / args.cleanroom_regime_summary_name, index=False)
    cleanroom_portfolio_trades.to_csv(output_dir / args.cleanroom_trades_name, index=False)
    cleanroom_equity_curve.to_csv(output_dir / args.cleanroom_equity_name, index=False)
    (output_dir / args.cleanroom_summary_name).write_text(json.dumps(cleanroom_summary, indent=2), encoding="utf-8")

    direct_filtered.to_csv(output_dir / args.direct_filtered_name, index=False)
    direct_portfolio_trades.to_csv(output_dir / args.direct_trades_name, index=False)
    direct_equity_curve.to_csv(output_dir / args.direct_equity_name, index=False)
    (output_dir / args.direct_summary_name).write_text(json.dumps(direct_summary, indent=2), encoding="utf-8")

    scorecard.to_csv(output_dir / args.comparison_scorecard_name, index=False)
    daily_compare.to_csv(output_dir / args.comparison_daily_name, index=False)
    candidate_diff.to_csv(output_dir / args.comparison_candidate_diff_name, index=False)
    (output_dir / args.comparison_summary_name).write_text(json.dumps(comparison_summary, indent=2), encoding="utf-8")
    write_report(
        path=output_dir / args.comparison_report_name,
        comparison_summary=comparison_summary,
        scorecard=scorecard,
    )

    print(
        json.dumps(
            {
                "window_start": start_date,
                "window_end": end_date,
                "cleanroom_summary_json": str(output_dir / args.cleanroom_summary_name),
                "direct_summary_json": str(output_dir / args.direct_summary_name),
                "comparison_summary_json": str(output_dir / args.comparison_summary_name),
                "comparison_report_md": str(output_dir / args.comparison_report_name),
                "cleanroom_final_equity": cleanroom_summary["final_equity"],
                "direct_final_equity": direct_summary["final_equity"],
            },
            indent=2,
        )
    )
