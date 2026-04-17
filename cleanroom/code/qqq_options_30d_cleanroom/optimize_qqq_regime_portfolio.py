from __future__ import annotations

import argparse
import json
import math
from itertools import product
from pathlib import Path

import pandas as pd

from backtest_qqq_greeks_portfolio import (
    PORTFOLIO_MAX_OPEN_RISK_FRACTION,
    build_delta_strategies,
    load_wide_data,
    run_portfolio_allocator,
    summarize_regimes,
)
from backtest_qqq_regime_gated_portfolio import (
    filter_candidate_trades,
    select_regime_strategies,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Optimize the regime-gated QQQ options portfolio.")
    parser.add_argument("--output-dir", default="output")
    parser.add_argument("--candidate-trades-name", default="qqq_delta_candidate_trades.csv")
    parser.add_argument("--wide-name", default="qqq_option_1min_wide_backtest.parquet")
    parser.add_argument("--results-name", default="qqq_regime_portfolio_optimization_results.csv")
    parser.add_argument("--best-name", default="qqq_regime_portfolio_best_config.json")
    parser.add_argument("--conservative-name", default="qqq_regime_portfolio_conservative_config.json")
    parser.add_argument("--best-trades-name", default="qqq_regime_portfolio_best_trades.csv")
    parser.add_argument("--best-equity-name", default="qqq_regime_portfolio_best_equity_curve.csv")
    parser.add_argument("--best-filtered-trades-name", default="qqq_regime_portfolio_best_filtered_candidates.csv")
    parser.add_argument("--report-name", default="qqq_regime_portfolio_optimization_report.md")
    return parser


def parse_json_columns(trades: pd.DataFrame) -> pd.DataFrame:
    parsed = trades.copy()
    parsed["legs_json"] = parsed["legs_json"].astype(str)
    parsed["mark_to_market_json"] = parsed["mark_to_market_json"].astype(str)
    return parsed


def build_day_return_map(wide: pd.DataFrame) -> dict[object, float]:
    daily = (
        wide.groupby("trade_date")
        .agg(day_open=("qqq_open", "first"), day_close=("qqq_close", "last"))
        .reset_index()
    )
    daily["day_ret_pct"] = (daily["day_close"] / daily["day_open"] - 1.0) * 100.0
    return dict(zip(daily["trade_date"], daily["day_ret_pct"]))


def assign_regime(day_ret_pct: float, threshold: float) -> str:
    if day_ret_pct >= threshold:
        return "bull"
    if day_ret_pct <= -threshold:
        return "bear"
    return "choppy"


def relabel_candidate_trades(
    candidate_trades: pd.DataFrame,
    day_return_map: dict[object, float],
    threshold: float,
) -> pd.DataFrame:
    relabeled = candidate_trades.copy()
    relabeled["trade_date"] = pd.to_datetime(relabeled["trade_date"]).dt.date
    relabeled["regime"] = [
        assign_regime(day_return_map[row.trade_date], threshold=threshold)
        for row in relabeled.itertuples(index=False)
    ]
    return relabeled


def score_drawdown(total_return_pct: float, max_drawdown_pct: float) -> float:
    if max_drawdown_pct >= 0.0:
        return total_return_pct if total_return_pct > 0 else 0.0
    return total_return_pct / abs(max_drawdown_pct)


def to_serializable_row(row: pd.Series) -> dict[str, object]:
    payload = row.to_dict()
    for key, value in list(payload.items()):
        if isinstance(value, (pd.Timestamp,)):
            payload[key] = value.isoformat()
    return payload


def write_report(
    path: Path,
    results: pd.DataFrame,
    best_config: dict[str, object],
    conservative_config: dict[str, object],
) -> None:
    lines: list[str] = []
    lines.append("# QQQ Regime Portfolio Optimization")
    lines.append("")
    lines.append(f"- Configurations tested: {len(results)}")
    lines.append("- Search dimensions: regime threshold, bull strategy count, bear strategy count, minimum regime trade support, and portfolio risk cap.")
    lines.append("")
    lines.append("## Best Return")
    lines.append("")
    lines.append(f"- Regime threshold: {best_config['regime_threshold_pct']:.2f}%")
    lines.append(f"- Bull strategy count: {int(best_config['top_bull'])}")
    lines.append(f"- Bear strategy count: {int(best_config['top_bear'])}")
    lines.append(f"- Min regime trades: {int(best_config['min_regime_trades'])}")
    lines.append(f"- Risk cap: {best_config['risk_cap'] * 100:.0f}%")
    lines.append(f"- Selected bull: {best_config['selected_bull']}")
    lines.append(f"- Selected bear: {best_config['selected_bear']}")
    lines.append(f"- Final equity: ${best_config['final_equity']:.2f}")
    lines.append(f"- Return: {best_config['total_return_pct']:.2f}%")
    lines.append(f"- Max drawdown: {best_config['max_drawdown_pct']:.2f}%")
    lines.append(f"- Trades: {int(best_config['portfolio_trade_count'])}")
    lines.append("")
    lines.append("## Conservative")
    lines.append("")
    lines.append(f"- Regime threshold: {conservative_config['regime_threshold_pct']:.2f}%")
    lines.append(f"- Bull strategy count: {int(conservative_config['top_bull'])}")
    lines.append(f"- Bear strategy count: {int(conservative_config['top_bear'])}")
    lines.append(f"- Min regime trades: {int(conservative_config['min_regime_trades'])}")
    lines.append(f"- Risk cap: {conservative_config['risk_cap'] * 100:.0f}%")
    lines.append(f"- Selected bull: {conservative_config['selected_bull']}")
    lines.append(f"- Selected bear: {conservative_config['selected_bear']}")
    lines.append(f"- Final equity: ${conservative_config['final_equity']:.2f}")
    lines.append(f"- Return: {conservative_config['total_return_pct']:.2f}%")
    lines.append(f"- Max drawdown: {conservative_config['max_drawdown_pct']:.2f}%")
    lines.append(f"- Trades: {int(conservative_config['portfolio_trade_count'])}")
    lines.append("")
    lines.append("## Top 10")
    lines.append("")
    top = results.sort_values(["final_equity", "calmar_like"], ascending=[False, False]).head(10)
    for row in top.itertuples(index=False):
        lines.append(
            f"- threshold {row.regime_threshold_pct:.2f}, bull {int(row.top_bull)}, bear {int(row.top_bear)}, min trades {int(row.min_regime_trades)}, risk cap {row.risk_cap * 100:.0f}% -> final ${row.final_equity:.2f}, return {row.total_return_pct:.2f}%, drawdown {row.max_drawdown_pct:.2f}%."
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = build_parser().parse_args()
    output_dir = Path(args.output_dir).resolve()

    candidate_trades = parse_json_columns(pd.read_csv(output_dir / args.candidate_trades_name))
    wide = load_wide_data(path=output_dir / args.wide_name)
    day_return_map = build_day_return_map(wide=wide)
    strategy_map = {strategy.name: strategy for strategy in build_delta_strategies()}

    regime_thresholds = [0.30, 0.35, 0.40, 0.45, 0.50, 0.60]
    top_bull_values = [1, 2, 3, 4]
    top_bear_values = [1, 2, 3, 4]
    min_trade_values = [1, 2, 3]
    risk_caps = [0.10, 0.15, 0.20, 0.25, 0.30, 0.35]

    optimization_rows: list[dict[str, object]] = []
    cache_by_threshold: dict[float, tuple[pd.DataFrame, pd.DataFrame]] = {}

    for regime_threshold, top_bull, top_bear, min_regime_trades, risk_cap in product(
        regime_thresholds,
        top_bull_values,
        top_bear_values,
        min_trade_values,
        risk_caps,
    ):
        if regime_threshold not in cache_by_threshold:
            relabeled_trades = relabel_candidate_trades(
                candidate_trades=candidate_trades,
                day_return_map=day_return_map,
                threshold=regime_threshold,
            )
            regime_summary = summarize_regimes(relabeled_trades)
            cache_by_threshold[regime_threshold] = (relabeled_trades, regime_summary)
        relabeled_trades, regime_summary = cache_by_threshold[regime_threshold]

        selected, selected_rows = select_regime_strategies(
            regime_summary=regime_summary,
            top_bull=top_bull,
            top_bear=top_bear,
            min_regime_trades=min_regime_trades,
        )
        filtered_trades = filter_candidate_trades(trades=relabeled_trades, selected=selected)
        selected_names = {
            strategy_name
            for regime in ["bull", "bear"]
            for strategy_name in selected[regime]
        }
        strategies = [strategy_map[name] for name in sorted(selected_names)]
        portfolio_trades, _, portfolio_summary = run_portfolio_allocator(
            strategies=strategies,
            trades_df=filtered_trades,
            portfolio_max_open_risk_fraction=risk_cap,
        )

        optimization_rows.append(
            {
                "regime_threshold_pct": regime_threshold,
                "top_bull": top_bull,
                "top_bear": top_bear,
                "min_regime_trades": min_regime_trades,
                "risk_cap": risk_cap,
                "selected_bull": json.dumps(selected["bull"]),
                "selected_bear": json.dumps(selected["bear"]),
                "selected_count": len(selected_names),
                "filtered_trade_count": int(len(filtered_trades)),
                "portfolio_trade_count": int(len(portfolio_trades)),
                "final_equity": portfolio_summary["final_equity"],
                "total_return_pct": portfolio_summary["total_return_pct"],
                "win_rate_pct": portfolio_summary["win_rate_pct"],
                "max_drawdown_pct": portfolio_summary["max_drawdown_pct"],
                "calmar_like": round(
                    score_drawdown(
                        total_return_pct=float(portfolio_summary["total_return_pct"]),
                        max_drawdown_pct=float(portfolio_summary["max_drawdown_pct"]),
                    ),
                    4,
                ),
                "strategy_contributions": json.dumps(portfolio_summary.get("strategy_contributions", [])),
                "selected_summary_rows": json.dumps(selected_rows.to_dict(orient="records")),
            }
        )

    results = pd.DataFrame(optimization_rows).sort_values(
        ["final_equity", "calmar_like", "portfolio_trade_count"],
        ascending=[False, False, False],
    ).reset_index(drop=True)

    best_row = results.iloc[0]
    conservative_pool = results[
        (results["total_return_pct"] > 0.0)
        & (results["portfolio_trade_count"] >= 10)
    ].copy()
    if conservative_pool.empty:
        conservative_row = best_row
    else:
        conservative_row = conservative_pool.sort_values(
            ["calmar_like", "final_equity", "portfolio_trade_count"],
            ascending=[False, False, False],
        ).iloc[0]

    best_config = to_serializable_row(best_row)
    conservative_config = to_serializable_row(conservative_row)

    best_threshold = float(best_row["regime_threshold_pct"])
    best_top_bull = int(best_row["top_bull"])
    best_top_bear = int(best_row["top_bear"])
    best_min_trades = int(best_row["min_regime_trades"])
    best_risk_cap = float(best_row["risk_cap"])
    best_trades, best_regime_summary = cache_by_threshold[best_threshold]
    best_selected, _ = select_regime_strategies(
        regime_summary=best_regime_summary,
        top_bull=best_top_bull,
        top_bear=best_top_bear,
        min_regime_trades=best_min_trades,
    )
    best_filtered_trades = filter_candidate_trades(trades=best_trades, selected=best_selected)
    best_strategy_names = {
        strategy_name
        for regime in ["bull", "bear"]
        for strategy_name in best_selected[regime]
    }
    best_strategies = [strategy_map[name] for name in sorted(best_strategy_names)]
    best_portfolio_trades, best_equity_curve, best_portfolio_summary = run_portfolio_allocator(
        strategies=best_strategies,
        trades_df=best_filtered_trades,
        portfolio_max_open_risk_fraction=best_risk_cap,
    )

    results.to_csv(output_dir / args.results_name, index=False)
    (output_dir / args.best_name).write_text(json.dumps(best_config, indent=2), encoding="utf-8")
    (output_dir / args.conservative_name).write_text(json.dumps(conservative_config, indent=2), encoding="utf-8")
    best_filtered_trades.to_csv(output_dir / args.best_filtered_trades_name, index=False)
    best_portfolio_trades.to_csv(output_dir / args.best_trades_name, index=False)
    best_equity_curve.to_csv(output_dir / args.best_equity_name, index=False)
    write_report(
        path=output_dir / args.report_name,
        results=results,
        best_config=best_config,
        conservative_config=conservative_config,
    )

    print(
        json.dumps(
            {
                "results_csv": str(output_dir / args.results_name),
                "best_config_json": str(output_dir / args.best_name),
                "conservative_config_json": str(output_dir / args.conservative_name),
                "best_filtered_candidates_csv": str(output_dir / args.best_filtered_trades_name),
                "best_trades_csv": str(output_dir / args.best_trades_name),
                "best_equity_curve_csv": str(output_dir / args.best_equity_name),
                "report_md": str(output_dir / args.report_name),
                "configurations_tested": int(len(results)),
                "best_final_equity": best_portfolio_summary["final_equity"],
                "best_total_return_pct": best_portfolio_summary["total_return_pct"],
                "best_max_drawdown_pct": best_portfolio_summary["max_drawdown_pct"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
