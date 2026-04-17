from __future__ import annotations

import argparse
import json
from itertools import product
from pathlib import Path

import pandas as pd

from backtest_qqq_greeks_portfolio import build_delta_strategies, run_portfolio_allocator, summarize_regimes
from backtest_qqq_regime_gated_portfolio import filter_candidate_trades, select_regime_strategies
from optimize_qqq_regime_portfolio import relabel_candidate_trades, score_drawdown


DEFAULT_OUTPUT_DIR = Path(__file__).resolve().parent / "output"
DEFAULT_STARTING_EQUITY = 25_000.0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Walk-forward validation for the direct-Greeks QQQ regime portfolio.")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--candidate-trades-name", default="qqq_direct_greeks_candidate_trades.csv")
    parser.add_argument("--day-returns-name", default="qqq_direct_greeks_day_returns.csv")
    parser.add_argument("--folds-name", default="qqq_direct_greeks_walkforward_folds.csv")
    parser.add_argument("--reopt-trades-name", default="qqq_direct_greeks_walkforward_reopt_trades.csv")
    parser.add_argument("--reopt-equity-name", default="qqq_direct_greeks_walkforward_reopt_equity_curve.csv")
    parser.add_argument("--frozen-trades-name", default="qqq_direct_greeks_walkforward_frozen_trades.csv")
    parser.add_argument("--frozen-equity-name", default="qqq_direct_greeks_walkforward_frozen_equity_curve.csv")
    parser.add_argument("--summary-name", default="qqq_direct_greeks_walkforward_summary.json")
    parser.add_argument("--report-name", default="qqq_direct_greeks_walkforward_report.md")
    parser.add_argument("--initial-train-days", type=int, default=126)
    parser.add_argument("--test-days", type=int, default=21)
    parser.add_argument("--step-days", type=int, default=21)
    return parser


def build_folds(
    trade_dates: list[object],
    initial_train_days: int,
    test_days: int,
    step_days: int,
) -> list[dict[str, object]]:
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


def load_day_return_map(day_returns: pd.DataFrame) -> tuple[list[object], dict[object, float]]:
    ordered = day_returns.copy()
    ordered["trade_date"] = pd.to_datetime(ordered["trade_date"]).dt.date
    ordered = ordered.sort_values("trade_date").reset_index(drop=True)
    return ordered["trade_date"].tolist(), dict(zip(ordered["trade_date"], ordered["day_ret_pct"]))


def empty_summary(starting_equity: float, risk_cap: float) -> dict[str, object]:
    return {
        "starting_equity": starting_equity,
        "final_equity": starting_equity,
        "total_return_pct": 0.0,
        "trade_count": 0,
        "win_rate_pct": 0.0,
        "max_drawdown_pct": 0.0,
        "portfolio_max_open_risk_fraction": risk_cap,
        "strategy_contributions": [],
    }


def subset_trades(trades: pd.DataFrame, dates: set[object]) -> pd.DataFrame:
    if trades.empty or not dates:
        return trades.iloc[0:0].copy()
    trade_date_values = pd.to_datetime(trades["trade_date"]).dt.date
    return trades.loc[trade_date_values.isin(dates)].copy()


def build_strategy_objects(selected: dict[str, list[str]]) -> list:
    strategy_map = {strategy.name: strategy for strategy in build_delta_strategies()}
    selected_names = {
        strategy_name
        for regime in ["bull", "bear", "choppy"]
        for strategy_name in selected[regime]
    }
    return [strategy_map[name] for name in sorted(selected_names)]


def select_train_config(
    candidate_trades: pd.DataFrame,
    day_return_map: dict[object, float],
) -> dict[str, object]:
    regime_thresholds = [0.40]
    top_bull_values = [3]
    top_bear_values = [3]
    top_choppy_values = [1]
    min_trade_values = [20]
    risk_caps = [0.15]

    best_row: dict[str, object] | None = None
    relabel_cache: dict[float, tuple[pd.DataFrame, pd.DataFrame]] = {}

    for regime_threshold, top_bull, top_bear, top_choppy, min_regime_trades, risk_cap in product(
        regime_thresholds,
        top_bull_values,
        top_bear_values,
        top_choppy_values,
        min_trade_values,
        risk_caps,
    ):
        if regime_threshold not in relabel_cache:
            relabeled = relabel_candidate_trades(
                candidate_trades=candidate_trades,
                day_return_map=day_return_map,
                threshold=regime_threshold,
            )
            relabel_cache[regime_threshold] = (relabeled, summarize_regimes(relabeled))
        relabeled, regime_summary = relabel_cache[regime_threshold]

        selected, _ = select_regime_strategies(
            regime_summary=regime_summary,
            top_bull=top_bull,
            top_bear=top_bear,
            min_regime_trades=min_regime_trades,
            top_choppy=top_choppy,
        )
        strategies = build_strategy_objects(selected=selected)
        filtered = filter_candidate_trades(trades=relabeled, selected=selected)
        if filtered.empty or not strategies:
            summary = empty_summary(starting_equity=DEFAULT_STARTING_EQUITY, risk_cap=risk_cap)
        else:
            _, _, summary = run_portfolio_allocator(
                strategies=strategies,
                trades_df=filtered,
                portfolio_max_open_risk_fraction=risk_cap,
                starting_equity=DEFAULT_STARTING_EQUITY,
            )

        row = {
            "regime_threshold_pct": regime_threshold,
            "top_bull": top_bull,
            "top_bear": top_bear,
            "top_choppy": top_choppy,
            "min_regime_trades": min_regime_trades,
            "risk_cap": risk_cap,
            "selected_bull": list(selected["bull"]),
            "selected_bear": list(selected["bear"]),
            "selected_choppy": list(selected["choppy"]),
            "portfolio_trade_count": int(summary["trade_count"]),
            "final_equity": float(summary["final_equity"]),
            "total_return_pct": float(summary["total_return_pct"]),
            "max_drawdown_pct": float(summary["max_drawdown_pct"]),
            "calmar_like": score_drawdown(
                total_return_pct=float(summary["total_return_pct"]),
                max_drawdown_pct=float(summary["max_drawdown_pct"]),
            ),
        }
        if best_row is None:
            best_row = row
            continue

        current_tuple = (
            row["total_return_pct"] > 0.0,
            row["portfolio_trade_count"] >= 10,
            row["calmar_like"],
            row["final_equity"],
            row["portfolio_trade_count"],
        )
        best_tuple = (
            best_row["total_return_pct"] > 0.0,
            best_row["portfolio_trade_count"] >= 10,
            best_row["calmar_like"],
            best_row["final_equity"],
            best_row["portfolio_trade_count"],
        )
        if current_tuple > best_tuple:
            best_row = row

    if best_row is None:
        raise RuntimeError("no training config selected")
    return best_row


def evaluate_config(
    candidate_trades: pd.DataFrame,
    day_return_map: dict[object, float],
    test_dates: set[object],
    config: dict[str, object],
    starting_equity: float,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, object], pd.DataFrame]:
    test_trades_full = subset_trades(trades=candidate_trades, dates=test_dates)
    relabeled = relabel_candidate_trades(
        candidate_trades=test_trades_full,
        day_return_map=day_return_map,
        threshold=float(config["regime_threshold_pct"]),
    )
    selected = {
        "bull": list(config["selected_bull"]),
        "bear": list(config["selected_bear"]),
        "choppy": list(config["selected_choppy"]),
    }
    filtered = filter_candidate_trades(trades=relabeled, selected=selected)
    strategies = build_strategy_objects(selected=selected)
    if filtered.empty or not strategies:
        return pd.DataFrame(), pd.DataFrame(), empty_summary(starting_equity=starting_equity, risk_cap=float(config["risk_cap"])), filtered

    portfolio_trades, equity_curve, summary = run_portfolio_allocator(
        strategies=strategies,
        trades_df=filtered,
        portfolio_max_open_risk_fraction=float(config["risk_cap"]),
        starting_equity=starting_equity,
    )
    return portfolio_trades, equity_curve, summary, filtered


def summarize_run(
    trades_df: pd.DataFrame,
    equity_df: pd.DataFrame,
    starting_equity: float,
) -> dict[str, object]:
    if equity_df.empty:
        final_equity = starting_equity
        max_drawdown_pct = 0.0
    else:
        final_equity = float(equity_df["equity"].iloc[-1])
        peak = equity_df["equity"].cummax()
        drawdown = (equity_df["equity"] / peak) - 1.0
        max_drawdown_pct = float(drawdown.min()) * 100.0

    trade_count = int(len(trades_df))
    win_rate_pct = float((trades_df["portfolio_net_pnl"] > 0).mean() * 100.0) if trade_count > 0 else 0.0
    summary = {
        "starting_equity": starting_equity,
        "final_equity": round(final_equity, 2),
        "total_return_pct": round(((final_equity / starting_equity) - 1.0) * 100.0, 2),
        "trade_count": trade_count,
        "win_rate_pct": round(win_rate_pct, 2),
        "max_drawdown_pct": round(max_drawdown_pct, 2),
    }
    if trade_count > 0:
        contributions = (
            trades_df.groupby("strategy", as_index=False)["portfolio_net_pnl"]
            .sum()
            .sort_values("portfolio_net_pnl", ascending=False)
        )
        summary["strategy_contributions"] = contributions.to_dict(orient="records")
    else:
        summary["strategy_contributions"] = []
    return summary


def write_report(
    path: Path,
    folds_df: pd.DataFrame,
    summary: dict[str, object],
) -> None:
    reopt = summary["reoptimized"]
    frozen = summary["frozen_initial"]
    frozen_config = summary["frozen_initial_config"]

    lines: list[str] = []
    lines.append("# QQQ Direct-Greeks Walk-Forward Validation")
    lines.append("")
    lines.append(
        f"- Folds: {int(summary['fold_count'])} using {int(summary['initial_train_days'])} train days, {int(summary['test_days'])} test days, and {int(summary['step_days'])} day steps."
    )
    lines.append(
        f"- OOS date range: {summary['oos_start_date']} through {summary['oos_end_date']}"
    )
    lines.append("")
    lines.append("## Re-Selected Each Fold")
    lines.append("")
    lines.append(f"- Final equity: ${reopt['final_equity']:.2f}")
    lines.append(f"- Total return: {reopt['total_return_pct']:.2f}%")
    lines.append(f"- Trades: {int(reopt['trade_count'])}")
    lines.append(f"- Win rate: {reopt['win_rate_pct']:.2f}%")
    lines.append(f"- Max drawdown: {reopt['max_drawdown_pct']:.2f}%")
    lines.append("- Selection rule: threshold 0.40%, top bull 3, top bear 3, top choppy 1, min 20 training trades, risk cap 15%.")
    lines.append("")
    lines.append("## Frozen Initial-Train Book")
    lines.append("")
    lines.append(f"- Final equity: ${frozen['final_equity']:.2f}")
    lines.append(f"- Total return: {frozen['total_return_pct']:.2f}%")
    lines.append(f"- Trades: {int(frozen['trade_count'])}")
    lines.append(f"- Win rate: {frozen['win_rate_pct']:.2f}%")
    lines.append(f"- Max drawdown: {frozen['max_drawdown_pct']:.2f}%")
    lines.append("")
    lines.append("## Frozen Initial Config")
    lines.append("")
    lines.append(f"- Threshold: {float(frozen_config['regime_threshold_pct']):.2f}%")
    lines.append(f"- Bull: {', '.join(f'`{name}`' for name in frozen_config['selected_bull']) if frozen_config['selected_bull'] else 'none'}")
    lines.append(f"- Bear: {', '.join(f'`{name}`' for name in frozen_config['selected_bear']) if frozen_config['selected_bear'] else 'none'}")
    lines.append(f"- Choppy: {', '.join(f'`{name}`' for name in frozen_config['selected_choppy']) if frozen_config['selected_choppy'] else 'flat'}")
    lines.append(f"- Risk cap: {float(frozen_config['risk_cap']) * 100:.0f}%")
    lines.append("")
    lines.append("## Fold Results")
    lines.append("")
    for row in folds_df.itertuples(index=False):
        lines.append(
            f"- Fold {int(row.fold)} test {row.test_start} to {row.test_end}: reopt {row.reopt_test_return_pct:.2f}% to ${row.reopt_test_final_equity:.2f}, frozen {row.frozen_test_return_pct:.2f}% to ${row.frozen_test_final_equity:.2f}."
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = build_parser().parse_args()
    output_dir = Path(args.output_dir).resolve()

    candidate_trades = pd.read_csv(output_dir / args.candidate_trades_name)
    day_returns = pd.read_csv(output_dir / args.day_returns_name)
    ordered_trade_dates, day_return_map = load_day_return_map(day_returns=day_returns)

    folds = build_folds(
        trade_dates=ordered_trade_dates,
        initial_train_days=args.initial_train_days,
        test_days=args.test_days,
        step_days=args.step_days,
    )
    if not folds:
        raise RuntimeError("No folds could be built. Reduce initial train days or test days.")

    first_train_dates = set(folds[0]["train_dates"])
    frozen_initial_config = select_train_config(
        candidate_trades=subset_trades(trades=candidate_trades, dates=first_train_dates),
        day_return_map=day_return_map,
    )

    fold_rows: list[dict[str, object]] = []
    reopt_trade_frames: list[pd.DataFrame] = []
    reopt_equity_frames: list[pd.DataFrame] = []
    frozen_trade_frames: list[pd.DataFrame] = []
    frozen_equity_frames: list[pd.DataFrame] = []
    reopt_current_equity = DEFAULT_STARTING_EQUITY
    frozen_current_equity = DEFAULT_STARTING_EQUITY

    for fold in folds:
        train_dates = set(fold["train_dates"])
        test_dates = set(fold["test_dates"])
        train_trades = subset_trades(trades=candidate_trades, dates=train_dates)

        reopt_config = select_train_config(
            candidate_trades=train_trades,
            day_return_map=day_return_map,
        )
        reopt_trades, reopt_equity, reopt_summary, _ = evaluate_config(
            candidate_trades=candidate_trades,
            day_return_map=day_return_map,
            test_dates=test_dates,
            config=reopt_config,
            starting_equity=reopt_current_equity,
        )
        frozen_trades, frozen_equity, frozen_summary, _ = evaluate_config(
            candidate_trades=candidate_trades,
            day_return_map=day_return_map,
            test_dates=test_dates,
            config=frozen_initial_config,
            starting_equity=frozen_current_equity,
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
                "reopt_threshold_pct": reopt_config["regime_threshold_pct"],
                "reopt_top_bull": reopt_config["top_bull"],
                "reopt_top_bear": reopt_config["top_bear"],
                "reopt_top_choppy": reopt_config["top_choppy"],
                "reopt_min_regime_trades": reopt_config["min_regime_trades"],
                "reopt_risk_cap": reopt_config["risk_cap"],
                "reopt_selected_bull": json.dumps(reopt_config["selected_bull"]),
                "reopt_selected_bear": json.dumps(reopt_config["selected_bear"]),
                "reopt_selected_choppy": json.dumps(reopt_config["selected_choppy"]),
                "reopt_test_trade_count": int(reopt_summary["trade_count"]),
                "reopt_test_starting_equity": round(reopt_current_equity, 2),
                "reopt_test_final_equity": round(float(reopt_summary["final_equity"]), 2),
                "reopt_test_return_pct": round(float(reopt_summary["total_return_pct"]), 2),
                "reopt_test_max_drawdown_pct": round(float(reopt_summary["max_drawdown_pct"]), 2),
                "reopt_test_win_rate_pct": round(float(reopt_summary["win_rate_pct"]), 2),
                "frozen_threshold_pct": frozen_initial_config["regime_threshold_pct"],
                "frozen_top_bull": frozen_initial_config["top_bull"],
                "frozen_top_bear": frozen_initial_config["top_bear"],
                "frozen_top_choppy": frozen_initial_config["top_choppy"],
                "frozen_min_regime_trades": frozen_initial_config["min_regime_trades"],
                "frozen_risk_cap": frozen_initial_config["risk_cap"],
                "frozen_selected_bull": json.dumps(frozen_initial_config["selected_bull"]),
                "frozen_selected_bear": json.dumps(frozen_initial_config["selected_bear"]),
                "frozen_selected_choppy": json.dumps(frozen_initial_config["selected_choppy"]),
                "frozen_test_trade_count": int(frozen_summary["trade_count"]),
                "frozen_test_starting_equity": round(frozen_current_equity, 2),
                "frozen_test_final_equity": round(float(frozen_summary["final_equity"]), 2),
                "frozen_test_return_pct": round(float(frozen_summary["total_return_pct"]), 2),
                "frozen_test_max_drawdown_pct": round(float(frozen_summary["max_drawdown_pct"]), 2),
                "frozen_test_win_rate_pct": round(float(frozen_summary["win_rate_pct"]), 2),
            }
        )

        if not reopt_trades.empty:
            tagged = reopt_trades.copy()
            tagged["fold"] = fold["fold"]
            reopt_trade_frames.append(tagged)
        if not reopt_equity.empty:
            tagged = reopt_equity.copy()
            tagged["fold"] = fold["fold"]
            reopt_equity_frames.append(tagged)
        if not frozen_trades.empty:
            tagged = frozen_trades.copy()
            tagged["fold"] = fold["fold"]
            frozen_trade_frames.append(tagged)
        if not frozen_equity.empty:
            tagged = frozen_equity.copy()
            tagged["fold"] = fold["fold"]
            frozen_equity_frames.append(tagged)

        reopt_current_equity = float(reopt_summary["final_equity"])
        frozen_current_equity = float(frozen_summary["final_equity"])
        print(
            f"Fold {fold['fold']}/{len(folds)} complete: reopt ${reopt_current_equity:,.2f}, frozen ${frozen_current_equity:,.2f}",
            flush=True,
        )

    folds_df = pd.DataFrame(fold_rows)
    reopt_trades_df = pd.concat(reopt_trade_frames, ignore_index=True) if reopt_trade_frames else pd.DataFrame()
    reopt_equity_df = pd.concat(reopt_equity_frames, ignore_index=True) if reopt_equity_frames else pd.DataFrame()
    frozen_trades_df = pd.concat(frozen_trade_frames, ignore_index=True) if frozen_trade_frames else pd.DataFrame()
    frozen_equity_df = pd.concat(frozen_equity_frames, ignore_index=True) if frozen_equity_frames else pd.DataFrame()

    summary = {
        "fold_count": len(folds_df),
        "initial_train_days": args.initial_train_days,
        "test_days": args.test_days,
        "step_days": args.step_days,
        "oos_start_date": folds[0]["test_dates"][0].isoformat(),
        "oos_end_date": folds[-1]["test_dates"][-1].isoformat(),
        "frozen_initial_config": frozen_initial_config,
        "reoptimized": summarize_run(
            trades_df=reopt_trades_df,
            equity_df=reopt_equity_df,
            starting_equity=DEFAULT_STARTING_EQUITY,
        ),
        "frozen_initial": summarize_run(
            trades_df=frozen_trades_df,
            equity_df=frozen_equity_df,
            starting_equity=DEFAULT_STARTING_EQUITY,
        ),
        "reopt_better_fold_count": int((folds_df["reopt_test_return_pct"] > folds_df["frozen_test_return_pct"]).sum()),
        "frozen_better_fold_count": int((folds_df["frozen_test_return_pct"] > folds_df["reopt_test_return_pct"]).sum()),
        "tie_fold_count": int((folds_df["reopt_test_return_pct"] == folds_df["frozen_test_return_pct"]).sum()),
    }

    folds_df.to_csv(output_dir / args.folds_name, index=False)
    reopt_trades_df.to_csv(output_dir / args.reopt_trades_name, index=False)
    reopt_equity_df.to_csv(output_dir / args.reopt_equity_name, index=False)
    frozen_trades_df.to_csv(output_dir / args.frozen_trades_name, index=False)
    frozen_equity_df.to_csv(output_dir / args.frozen_equity_name, index=False)
    (output_dir / args.summary_name).write_text(json.dumps(summary, indent=2), encoding="utf-8")
    write_report(path=output_dir / args.report_name, folds_df=folds_df, summary=summary)

    print(
        json.dumps(
            {
                "folds_csv": str(output_dir / args.folds_name),
                "reopt_trades_csv": str(output_dir / args.reopt_trades_name),
                "reopt_equity_curve_csv": str(output_dir / args.reopt_equity_name),
                "frozen_trades_csv": str(output_dir / args.frozen_trades_name),
                "frozen_equity_curve_csv": str(output_dir / args.frozen_equity_name),
                "summary_json": str(output_dir / args.summary_name),
                "report_md": str(output_dir / args.report_name),
                "fold_count": int(len(folds_df)),
                "reoptimized_final_equity": summary["reoptimized"]["final_equity"],
                "frozen_initial_final_equity": summary["frozen_initial"]["final_equity"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
