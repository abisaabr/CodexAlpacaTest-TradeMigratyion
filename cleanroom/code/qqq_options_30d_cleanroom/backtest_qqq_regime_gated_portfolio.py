from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from backtest_qqq_greeks_portfolio import (
    PORTFOLIO_MAX_OPEN_RISK_FRACTION,
    REGIME_THRESHOLD_PCT,
    STARTING_EQUITY,
    build_delta_strategies,
    run_portfolio_allocator,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Third-pass regime-gated QQQ options portfolio backtest.")
    parser.add_argument("--output-dir", default="output")
    parser.add_argument("--candidate-trades-name", default="qqq_delta_candidate_trades.csv")
    parser.add_argument("--regime-summary-name", default="qqq_delta_regime_summary.csv")
    parser.add_argument("--selected-strategies-name", default="qqq_regime_gated_selected_strategies.json")
    parser.add_argument("--filtered-trades-name", default="qqq_regime_gated_candidate_trades.csv")
    parser.add_argument("--portfolio-trades-name", default="qqq_regime_gated_portfolio_trades.csv")
    parser.add_argument("--portfolio-equity-name", default="qqq_regime_gated_portfolio_equity_curve.csv")
    parser.add_argument("--portfolio-summary-name", default="qqq_regime_gated_portfolio_summary.json")
    parser.add_argument("--report-name", default="qqq_regime_gated_portfolio_report.md")
    parser.add_argument("--top-per-regime", type=int, default=3)
    parser.add_argument("--top-bull", type=int)
    parser.add_argument("--top-bear", type=int)
    parser.add_argument("--top-choppy", type=int, default=0)
    parser.add_argument("--min-regime-trades", type=int, default=2)
    parser.add_argument("--risk-cap", type=float, default=PORTFOLIO_MAX_OPEN_RISK_FRACTION)
    return parser


def select_regime_strategies(
    regime_summary: pd.DataFrame,
    top_bull: int,
    top_bear: int,
    min_regime_trades: int,
    top_choppy: int = 0,
) -> tuple[dict[str, list[str]], pd.DataFrame]:
    selected: dict[str, list[str]] = {"bull": [], "bear": [], "choppy": []}
    rows: list[pd.DataFrame] = []

    regime_top_map = {"bull": top_bull, "bear": top_bear, "choppy": top_choppy}
    for regime in ["bull", "bear", "choppy"]:
        subset = regime_summary[regime_summary["regime"] == regime].copy()
        subset = subset[subset["trade_count"] >= min_regime_trades].copy()
        subset = subset[subset["total_net_pnl_1x"] > 0.0].copy()
        subset = subset.sort_values(
            ["total_net_pnl_1x", "avg_return_on_risk_pct", "win_rate_pct"],
            ascending=[False, False, False],
        ).head(regime_top_map[regime])
        selected[regime] = subset["strategy"].tolist()
        rows.append(subset)

    selected_rows = (
        pd.concat(rows, ignore_index=True)
        if rows
        else pd.DataFrame(columns=list(regime_summary.columns))
    )
    return selected, selected_rows


def filter_candidate_trades(trades: pd.DataFrame, selected: dict[str, list[str]]) -> pd.DataFrame:
    allowed_pairs = {
        (regime, strategy)
        for regime, strategies in selected.items()
        for strategy in strategies
    }
    mask = [(row.regime, row.strategy) in allowed_pairs for row in trades.itertuples(index=False)]
    filtered = trades.loc[mask].copy()
    if not filtered.empty:
        filtered = filtered.sort_values(["trade_date", "entry_minute", "strategy"]).reset_index(drop=True)
    return filtered


def write_report(
    path: Path,
    selected: dict[str, list[str]],
    portfolio_summary: dict[str, object],
    filtered_trades: pd.DataFrame,
    risk_cap: float,
) -> None:
    lines: list[str] = []
    lines.append("# QQQ Regime-Gated Portfolio Backtest")
    lines.append("")
    lines.append(f"- Regime threshold: bull >= +{REGIME_THRESHOLD_PCT:.2f}% RTH return, bear <= -{REGIME_THRESHOLD_PCT:.2f}%, otherwise choppy.")
    lines.append(f"- Shared starting equity: ${STARTING_EQUITY:,.0f}")
    lines.append(f"- Max concurrent open risk: {risk_cap * 100:.0f}% of current equity")
    if selected["choppy"]:
        lines.append(f"- Choppy sessions: trade {len(selected['choppy'])} selected family{'ies' if len(selected['choppy']) != 1 else ''}.")
    else:
        lines.append("- Choppy sessions: no new entries")
    lines.append("")
    lines.append("## Selected Strategies")
    lines.append("")
    lines.append(f"- Bull: {', '.join(f'`{name}`' for name in selected['bull']) if selected['bull'] else 'none'}")
    lines.append(f"- Bear: {', '.join(f'`{name}`' for name in selected['bear']) if selected['bear'] else 'none'}")
    lines.append(f"- Choppy: {', '.join(f'`{name}`' for name in selected['choppy']) if selected['choppy'] else 'flat'}")
    lines.append("")
    lines.append("## Trade Counts")
    lines.append("")
    if filtered_trades.empty:
        lines.append("- No trades passed the regime gate.")
    else:
        by_regime = filtered_trades.groupby("regime").size().to_dict()
        for regime in ["bull", "bear", "choppy"]:
            lines.append(f"- {regime.title()}: {int(by_regime.get(regime, 0))} trades")
    lines.append("")
    lines.append("## Portfolio Summary")
    lines.append("")
    lines.append(f"- Final equity: ${portfolio_summary['final_equity']:.2f}")
    lines.append(f"- Total return: {portfolio_summary['total_return_pct']:.2f}%")
    lines.append(f"- Trades executed: {portfolio_summary['trade_count']}")
    lines.append(f"- Win rate: {portfolio_summary['win_rate_pct']:.2f}%")
    lines.append(f"- Max drawdown: {portfolio_summary['max_drawdown_pct']:.2f}%")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = build_parser().parse_args()
    output_dir = Path(args.output_dir).resolve()

    candidate_trades = pd.read_csv(output_dir / args.candidate_trades_name)
    regime_summary = pd.read_csv(output_dir / args.regime_summary_name)
    top_bull = args.top_bull if args.top_bull is not None else args.top_per_regime
    top_bear = args.top_bear if args.top_bear is not None else args.top_per_regime

    selected, selected_rows = select_regime_strategies(
        regime_summary=regime_summary,
        top_bull=top_bull,
        top_bear=top_bear,
        top_choppy=args.top_choppy,
        min_regime_trades=args.min_regime_trades,
    )
    filtered_trades = filter_candidate_trades(trades=candidate_trades, selected=selected)

    strategy_map = {strategy.name: strategy for strategy in build_delta_strategies()}
    selected_strategies = {
        strategy_name
        for regime in ["bull", "bear", "choppy"]
        for strategy_name in selected[regime]
    }
    strategies = [strategy_map[name] for name in selected_strategies]

    portfolio_trades, portfolio_equity, portfolio_summary = run_portfolio_allocator(
        strategies=strategies,
        trades_df=filtered_trades,
        portfolio_max_open_risk_fraction=args.risk_cap,
    )

    selected_payload = {
        "selection_rules": {
            "top_per_regime": args.top_per_regime,
            "top_bull": top_bull,
            "top_bear": top_bear,
            "top_choppy": args.top_choppy,
            "min_regime_trades": args.min_regime_trades,
            "require_positive_total_pnl": True,
            "choppy_policy": "selected" if args.top_choppy > 0 else "flat",
            "risk_cap": args.risk_cap,
        },
        "selected": selected,
        "selected_summary_rows": selected_rows.to_dict(orient="records"),
    }

    (output_dir / args.selected_strategies_name).write_text(json.dumps(selected_payload, indent=2), encoding="utf-8")
    filtered_trades.to_csv(output_dir / args.filtered_trades_name, index=False)
    portfolio_trades.to_csv(output_dir / args.portfolio_trades_name, index=False)
    portfolio_equity.to_csv(output_dir / args.portfolio_equity_name, index=False)
    (output_dir / args.portfolio_summary_name).write_text(json.dumps(portfolio_summary, indent=2), encoding="utf-8")
    write_report(
        path=output_dir / args.report_name,
        selected=selected,
        portfolio_summary=portfolio_summary,
        filtered_trades=filtered_trades,
        risk_cap=args.risk_cap,
    )

    print(
        json.dumps(
            {
                "selected_strategies_json": str(output_dir / args.selected_strategies_name),
                "filtered_trades_csv": str(output_dir / args.filtered_trades_name),
                "portfolio_trades_csv": str(output_dir / args.portfolio_trades_name),
                "portfolio_equity_curve_csv": str(output_dir / args.portfolio_equity_name),
                "portfolio_summary_json": str(output_dir / args.portfolio_summary_name),
                "report_md": str(output_dir / args.report_name),
                "selected_bull": selected["bull"],
                "selected_bear": selected["bear"],
                "filtered_trade_count": int(len(filtered_trades)),
                "portfolio_trade_count": int(len(portfolio_trades)),
                "portfolio_final_equity": portfolio_summary["final_equity"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
