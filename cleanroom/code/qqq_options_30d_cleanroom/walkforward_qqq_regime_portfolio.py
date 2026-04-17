from __future__ import annotations

import argparse
import json
from itertools import product
from pathlib import Path

import pandas as pd

from backtest_qqq_greeks_portfolio import build_delta_strategies, load_wide_data, run_portfolio_allocator
from backtest_qqq_regime_gated_portfolio import filter_candidate_trades, select_regime_strategies
from optimize_qqq_regime_portfolio import (
    build_day_return_map,
    parse_json_columns,
    relabel_candidate_trades,
    score_drawdown,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Walk-forward validation for the regime-gated QQQ options portfolio.")
    parser.add_argument("--output-dir", default="output")
    parser.add_argument("--candidate-trades-name", default="qqq_delta_candidate_trades.csv")
    parser.add_argument("--wide-name", default="qqq_option_1min_wide_backtest.parquet")
    parser.add_argument("--folds-name", default="qqq_regime_portfolio_walkforward_folds.csv")
    parser.add_argument("--trades-name", default="qqq_regime_portfolio_walkforward_trades.csv")
    parser.add_argument("--equity-name", default="qqq_regime_portfolio_walkforward_equity_curve.csv")
    parser.add_argument("--summary-name", default="qqq_regime_portfolio_walkforward_summary.json")
    parser.add_argument("--report-name", default="qqq_regime_portfolio_walkforward_report.md")
    parser.add_argument("--initial-train-days", type=int, default=9)
    parser.add_argument("--test-days", type=int, default=3)
    parser.add_argument("--step-days", type=int, default=3)
    return parser


def build_folds(trade_dates: list[object], initial_train_days: int, test_days: int, step_days: int) -> list[dict[str, object]]:
    folds: list[dict[str, object]] = []
    train_end = initial_train_days
    fold_id = 1
    while train_end < len(trade_dates):
        test_end = min(train_end + test_days, len(trade_dates))
        folds.append(
            {
                "fold": fold_id,
                "train_dates": trade_dates[:train_end],
                "test_dates": trade_dates[train_end:test_end],
            }
        )
        if test_end >= len(trade_dates):
            break
        train_end += step_days
        fold_id += 1
    return folds


def select_train_config(
    candidate_trades: pd.DataFrame,
    day_return_map: dict[object, float],
) -> dict[str, object]:
    strategy_map = {strategy.name: strategy for strategy in build_delta_strategies()}
    regime_thresholds = [0.35, 0.40, 0.45, 0.50]
    top_bull_values = [2, 3, 4]
    top_bear_values = [1, 2, 3]
    min_trade_values = [1, 2]
    risk_caps = [0.10, 0.15, 0.20, 0.25]

    best_row: dict[str, object] | None = None
    relabel_cache: dict[float, pd.DataFrame] = {}

    for regime_threshold, top_bull, top_bear, min_regime_trades, risk_cap in product(
        regime_thresholds,
        top_bull_values,
        top_bear_values,
        min_trade_values,
        risk_caps,
    ):
        if regime_threshold not in relabel_cache:
            relabel_cache[regime_threshold] = relabel_candidate_trades(
                candidate_trades=candidate_trades,
                day_return_map=day_return_map,
                threshold=regime_threshold,
            )
        relabeled = relabel_cache[regime_threshold]
        regime_summary = (
            relabeled.groupby(["regime", "strategy", "family"], as_index=False)
            .agg(
                trade_count=("net_pnl_per_combo", "size"),
                wins=("net_pnl_per_combo", lambda series: int((series > 0).sum())),
                total_net_pnl_1x=("net_pnl_per_combo", "sum"),
                avg_net_pnl_1x=("net_pnl_per_combo", "mean"),
                avg_return_on_risk_pct=("return_on_risk_pct", "mean"),
            )
        )
        regime_summary["win_rate_pct"] = (regime_summary["wins"] / regime_summary["trade_count"]) * 100.0
        regime_summary = regime_summary.drop(columns=["wins"])
        regime_summary = regime_summary.sort_values(
            ["regime", "total_net_pnl_1x", "avg_return_on_risk_pct"],
            ascending=[True, False, False],
        ).reset_index(drop=True)

        selected, _ = select_regime_strategies(
            regime_summary=regime_summary,
            top_bull=top_bull,
            top_bear=top_bear,
            min_regime_trades=min_regime_trades,
        )
        filtered = filter_candidate_trades(trades=relabel_cache[regime_threshold], selected=selected)
        selected_names = {
            strategy_name
            for regime in ["bull", "bear"]
            for strategy_name in selected[regime]
        }
        strategies = [strategy_map[name] for name in sorted(selected_names)]
        _, _, summary = run_portfolio_allocator(
            strategies=strategies,
            trades_df=filtered,
            portfolio_max_open_risk_fraction=risk_cap,
        )
        calmar_like = score_drawdown(
            total_return_pct=float(summary["total_return_pct"]),
            max_drawdown_pct=float(summary["max_drawdown_pct"]),
        )
        row = {
            "regime_threshold_pct": regime_threshold,
            "top_bull": top_bull,
            "top_bear": top_bear,
            "min_regime_trades": min_regime_trades,
            "risk_cap": risk_cap,
            "selected_bull": selected["bull"],
            "selected_bear": selected["bear"],
            "portfolio_trade_count": int(summary["trade_count"]),
            "final_equity": float(summary["final_equity"]),
            "total_return_pct": float(summary["total_return_pct"]),
            "max_drawdown_pct": float(summary["max_drawdown_pct"]),
            "calmar_like": calmar_like,
        }
        if best_row is None:
            best_row = row
            continue

        current_tuple = (
            row["total_return_pct"] > 0.0,
            row["portfolio_trade_count"] >= 5,
            row["calmar_like"],
            row["final_equity"],
            row["portfolio_trade_count"],
        )
        best_tuple = (
            best_row["total_return_pct"] > 0.0,
            best_row["portfolio_trade_count"] >= 5,
            best_row["calmar_like"],
            best_row["final_equity"],
            best_row["portfolio_trade_count"],
        )
        if current_tuple > best_tuple:
            best_row = row

    if best_row is None:
        raise RuntimeError("no training config selected")
    return best_row


def write_report(path: Path, folds_df: pd.DataFrame, summary: dict[str, object]) -> None:
    lines: list[str] = []
    lines.append("# QQQ Regime Portfolio Walk-Forward")
    lines.append("")
    lines.append(f"- Folds: {int(summary['fold_count'])}")
    lines.append(f"- Starting equity: ${summary['starting_equity']:.2f}")
    lines.append(f"- Final walk-forward equity: ${summary['final_equity']:.2f}")
    lines.append(f"- Total compounded return: {summary['total_return_pct']:.2f}%")
    lines.append(f"- Walk-forward max drawdown: {summary['max_drawdown_pct']:.2f}%")
    lines.append(f"- Walk-forward trades: {int(summary['trade_count'])}")
    lines.append("")
    lines.append("## Fold Results")
    lines.append("")
    for row in folds_df.itertuples(index=False):
        lines.append(
            f"- Fold {int(row.fold)} train {row.train_start} to {row.train_end}, test {row.test_start} to {row.test_end}: final ${row.test_final_equity:.2f}, return {row.test_return_pct:.2f}%, drawdown {row.test_max_drawdown_pct:.2f}%, bull {row.selected_bull}, bear {row.selected_bear}."
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = build_parser().parse_args()
    output_dir = Path(args.output_dir).resolve()

    candidate_trades = parse_json_columns(pd.read_csv(output_dir / args.candidate_trades_name))
    wide = load_wide_data(path=output_dir / args.wide_name)
    valid_trade_dates = list(pd.to_datetime(wide["trade_date"]).dt.date.drop_duplicates())
    day_return_map = build_day_return_map(wide=wide)
    folds = build_folds(
        trade_dates=valid_trade_dates,
        initial_train_days=args.initial_train_days,
        test_days=args.test_days,
        step_days=args.step_days,
    )
    strategy_map = {strategy.name: strategy for strategy in build_delta_strategies()}

    fold_rows: list[dict[str, object]] = []
    all_portfolio_trades: list[pd.DataFrame] = []
    all_equity_curves: list[pd.DataFrame] = []
    current_equity = 25_000.0

    for fold in folds:
        train_dates = set(fold["train_dates"])
        test_dates = set(fold["test_dates"])
        train_trades = candidate_trades[pd.to_datetime(candidate_trades["trade_date"]).dt.date.isin(train_dates)].copy()
        test_trades_full = candidate_trades[pd.to_datetime(candidate_trades["trade_date"]).dt.date.isin(test_dates)].copy()

        selected_config = select_train_config(
            candidate_trades=train_trades,
            day_return_map=day_return_map,
        )
        test_relabeled = relabel_candidate_trades(
            candidate_trades=test_trades_full,
            day_return_map=day_return_map,
            threshold=float(selected_config["regime_threshold_pct"]),
        )
        selected = {
            "bull": list(selected_config["selected_bull"]),
            "bear": list(selected_config["selected_bear"]),
            "choppy": [],
        }
        filtered_test_trades = filter_candidate_trades(trades=test_relabeled, selected=selected)
        selected_names = {
            strategy_name
            for regime in ["bull", "bear"]
            for strategy_name in selected[regime]
        }
        strategies = [strategy_map[name] for name in sorted(selected_names)]

        if filtered_test_trades.empty:
            portfolio_trades = pd.DataFrame()
            portfolio_equity = pd.DataFrame()
            portfolio_summary = {
                "starting_equity": current_equity,
                "final_equity": current_equity,
                "total_return_pct": 0.0,
                "trade_count": 0,
                "win_rate_pct": 0.0,
                "max_drawdown_pct": 0.0,
            }
        else:
            portfolio_trades, portfolio_equity, portfolio_summary = run_portfolio_allocator(
                strategies=strategies,
                trades_df=filtered_test_trades,
                portfolio_max_open_risk_fraction=float(selected_config["risk_cap"]),
                starting_equity=current_equity,
            )

        fold_rows.append(
            {
                "fold": fold["fold"],
                "train_start": fold["train_dates"][0].isoformat(),
                "train_end": fold["train_dates"][-1].isoformat(),
                "test_start": fold["test_dates"][0].isoformat(),
                "test_end": fold["test_dates"][-1].isoformat(),
                "train_days": len(fold["train_dates"]),
                "test_days": len(fold["test_dates"]),
                "regime_threshold_pct": selected_config["regime_threshold_pct"],
                "top_bull": selected_config["top_bull"],
                "top_bear": selected_config["top_bear"],
                "min_regime_trades": selected_config["min_regime_trades"],
                "risk_cap": selected_config["risk_cap"],
                "selected_bull": json.dumps(selected["bull"]),
                "selected_bear": json.dumps(selected["bear"]),
                "test_trade_count": int(portfolio_summary["trade_count"]),
                "test_starting_equity": round(current_equity, 2),
                "test_final_equity": round(float(portfolio_summary["final_equity"]), 2),
                "test_return_pct": round(float(portfolio_summary["total_return_pct"]), 2),
                "test_max_drawdown_pct": round(float(portfolio_summary["max_drawdown_pct"]), 2),
                "test_win_rate_pct": round(float(portfolio_summary["win_rate_pct"]), 2),
            }
        )

        if not portfolio_trades.empty:
            portfolio_trades = portfolio_trades.copy()
            portfolio_trades["fold"] = fold["fold"]
            all_portfolio_trades.append(portfolio_trades)
        if not portfolio_equity.empty:
            portfolio_equity = portfolio_equity.copy()
            portfolio_equity["fold"] = fold["fold"]
            all_equity_curves.append(portfolio_equity)

        current_equity = float(portfolio_summary["final_equity"])

    folds_df = pd.DataFrame(fold_rows)
    trades_df = pd.concat(all_portfolio_trades, ignore_index=True) if all_portfolio_trades else pd.DataFrame()
    equity_df = pd.concat(all_equity_curves, ignore_index=True) if all_equity_curves else pd.DataFrame()

    if equity_df.empty:
        final_equity = 25_000.0
        max_drawdown_pct = 0.0
    else:
        final_equity = float(equity_df["equity"].iloc[-1])
        peak = equity_df["equity"].cummax()
        drawdown = (equity_df["equity"] / peak) - 1.0
        max_drawdown_pct = float(drawdown.min()) * 100.0

    trade_count = int(len(trades_df))
    win_rate_pct = float((trades_df["portfolio_net_pnl"] > 0).mean() * 100.0) if trade_count > 0 else 0.0
    summary = {
        "fold_count": len(folds_df),
        "starting_equity": 25_000.0,
        "final_equity": round(final_equity, 2),
        "total_return_pct": round(((final_equity / 25_000.0) - 1.0) * 100.0, 2),
        "trade_count": trade_count,
        "win_rate_pct": round(win_rate_pct, 2),
        "max_drawdown_pct": round(max_drawdown_pct, 2),
    }

    folds_df.to_csv(output_dir / args.folds_name, index=False)
    trades_df.to_csv(output_dir / args.trades_name, index=False)
    equity_df.to_csv(output_dir / args.equity_name, index=False)
    (output_dir / args.summary_name).write_text(json.dumps(summary, indent=2), encoding="utf-8")
    write_report(path=output_dir / args.report_name, folds_df=folds_df, summary=summary)

    print(
        json.dumps(
            {
                "folds_csv": str(output_dir / args.folds_name),
                "trades_csv": str(output_dir / args.trades_name),
                "equity_curve_csv": str(output_dir / args.equity_name),
                "summary_json": str(output_dir / args.summary_name),
                "report_md": str(output_dir / args.report_name),
                "folds": int(len(folds_df)),
                "walkforward_final_equity": summary["final_equity"],
                "walkforward_total_return_pct": summary["total_return_pct"],
                "walkforward_max_drawdown_pct": summary["max_drawdown_pct"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
