from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from backtest_qqq_greeks_portfolio import (
    MINUTES_PER_RTH_SESSION,
    build_delta_strategies,
    current_portfolio_equity,
    run_portfolio_allocator,
)
from backtest_qqq_regime_gated_portfolio import filter_candidate_trades
from optimize_qqq_regime_portfolio import relabel_candidate_trades


DEFAULT_OUTPUT_DIR = Path(__file__).resolve().parent / "output"
BASE_COMMISSION_PER_CONTRACT = 0.65
STARTING_EQUITY = 25_000.0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Deployment-readiness scorecard for the direct-Greeks QQQ portfolio.")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--candidate-trades-name", default="qqq_direct_greeks_candidate_trades.csv")
    parser.add_argument("--day-returns-name", default="qqq_direct_greeks_day_returns.csv")
    parser.add_argument("--walkforward-summary-name", default="qqq_direct_greeks_walkforward_summary.json")
    parser.add_argument("--scorecard-name", default="qqq_direct_greeks_deployment_readiness_scorecard.csv")
    parser.add_argument("--summary-name", default="qqq_direct_greeks_deployment_readiness_summary.json")
    parser.add_argument("--report-name", default="qqq_direct_greeks_deployment_readiness_report.md")
    return parser


def load_deployment_context(output_dir: Path, walkforward_summary_name: str) -> tuple[dict[str, object], str, str]:
    summary = json.loads((output_dir / walkforward_summary_name).read_text(encoding="utf-8"))
    config = dict(summary["frozen_initial_config"])
    return config, str(summary["oos_start_date"]), str(summary["oos_end_date"])


def load_day_return_map(output_dir: Path, day_returns_name: str) -> dict[object, float]:
    day_returns = pd.read_csv(output_dir / day_returns_name)
    day_returns["trade_date"] = pd.to_datetime(day_returns["trade_date"]).dt.date
    return dict(zip(day_returns["trade_date"], day_returns["day_ret_pct"]))


def parse_legs(raw: str) -> list[dict[str, object]]:
    return list(json.loads(raw))


def prepare_selected_trades(
    output_dir: Path,
    candidate_trades_name: str,
    day_returns_name: str,
    config: dict[str, object],
    oos_start_date: str,
    oos_end_date: str,
) -> tuple[pd.DataFrame, dict[str, list[str]]]:
    candidate_trades = pd.read_csv(output_dir / candidate_trades_name)
    candidate_trades["trade_date"] = pd.to_datetime(candidate_trades["trade_date"]).dt.date
    day_return_map = load_day_return_map(output_dir=output_dir, day_returns_name=day_returns_name)

    oos_mask = (
        (candidate_trades["trade_date"] >= pd.to_datetime(oos_start_date).date())
        & (candidate_trades["trade_date"] <= pd.to_datetime(oos_end_date).date())
    )
    oos_trades = candidate_trades.loc[oos_mask].copy()
    relabeled = relabel_candidate_trades(
        candidate_trades=oos_trades,
        day_return_map=day_return_map,
        threshold=float(config["regime_threshold_pct"]),
    )
    selected = {
        "bull": list(config["selected_bull"]),
        "bear": list(config["selected_bear"]),
        "choppy": list(config["selected_choppy"]),
    }
    filtered = filter_candidate_trades(trades=relabeled, selected=selected)
    return annotate_trades(filtered), selected


def annotate_trades(trades: pd.DataFrame) -> pd.DataFrame:
    if trades.empty:
        annotated = trades.copy()
        annotated["leg_count"] = pd.Series(dtype=int)
        return annotated

    rows: list[dict[str, object]] = []
    for row in trades.itertuples(index=False):
        legs = parse_legs(str(row.legs_json))
        statuses = [str(leg.get("calc_status", "")) for leg in legs]
        quality_tiers = [str(leg.get("calc_quality_tier", "")) for leg in legs]
        rows.append(
            {
                **row._asdict(),
                "leg_count": len(legs),
                "all_status_ok": all(status == "ok" for status in statuses),
                "all_status_ok_or_carried": all(status in {"ok", "ok_carried_iv"} for status in statuses),
                "all_quality_on_row": all(tier == "on_row_iv" for tier in quality_tiers),
                "all_quality_on_row_or_carried": all(tier in {"on_row_iv", "carried_iv"} for tier in quality_tiers),
                "has_intrinsic_clip": any(
                    status == "ok_intrinsic_clip" or tier == "intrinsic_clip"
                    for status, tier in zip(statuses, quality_tiers)
                ),
            }
        )
    annotated = pd.DataFrame(rows)
    annotated["trade_date"] = pd.to_datetime(annotated["trade_date"]).dt.date
    return annotated


def build_strategy_objects(selected: dict[str, list[str]]) -> list:
    strategy_map = {strategy.name: strategy for strategy in build_delta_strategies()}
    selected_names = {
        strategy_name
        for regime in ["bull", "bear", "choppy"]
        for strategy_name in selected[regime]
    }
    return [strategy_map[name] for name in sorted(selected_names)]


def transform_execution(
    trades: pd.DataFrame,
    extra_slippage_per_leg: float,
    commission_per_contract: float,
) -> pd.DataFrame:
    if trades.empty:
        return trades.copy()

    transformed = trades.copy()
    adjusted_rows: list[dict[str, object]] = []
    for row in transformed.itertuples(index=False):
        leg_count = int(row.leg_count)
        entry_slippage_dollars = extra_slippage_per_leg * 100.0 * leg_count
        exit_slippage_dollars = extra_slippage_per_leg * 100.0 * leg_count
        new_entry_commission = commission_per_contract * leg_count
        new_exit_commission = commission_per_contract * leg_count

        entry_cash = float(row.entry_cash_per_combo) - entry_slippage_dollars
        exit_cash = float(row.exit_cash_per_combo) - exit_slippage_dollars
        max_loss = float(row.max_loss_per_combo) + (
            entry_slippage_dollars
            + exit_slippage_dollars
            + (new_entry_commission - float(row.entry_commission_per_combo))
            + (new_exit_commission - float(row.exit_commission_per_combo))
        )
        max_profit = float(row.max_profit_per_combo) - (
            entry_slippage_dollars
            + exit_slippage_dollars
            + (new_entry_commission - float(row.entry_commission_per_combo))
            + (new_exit_commission - float(row.exit_commission_per_combo))
        )
        net_pnl = entry_cash + exit_cash - new_entry_commission - new_exit_commission
        mtm_adjustment = exit_slippage_dollars + (new_exit_commission - float(row.exit_commission_per_combo))
        mark_to_market = {
            int(key): float(value) - mtm_adjustment
            for key, value in json.loads(str(row.mark_to_market_json)).items()
        }
        adjusted_rows.append(
            {
                **row._asdict(),
                "entry_cash_per_combo": round(entry_cash, 4),
                "exit_cash_per_combo": round(exit_cash, 4),
                "entry_commission_per_combo": round(new_entry_commission, 4),
                "exit_commission_per_combo": round(new_exit_commission, 4),
                "net_pnl_per_combo": round(net_pnl, 4),
                "max_loss_per_combo": round(max_loss, 4),
                "max_profit_per_combo": round(max_profit, 4),
                "return_on_risk_pct": round((net_pnl / max_loss) * 100.0, 4) if max_loss > 0.0 else 0.0,
                "mark_to_market_json": json.dumps(mark_to_market, sort_keys=True),
            }
        )
    adjusted = pd.DataFrame(adjusted_rows)
    adjusted["trade_date"] = pd.to_datetime(adjusted["trade_date"]).dt.date
    return adjusted


def summarize_results(trades_df: pd.DataFrame, equity_curve_df: pd.DataFrame, risk_cap: float) -> dict[str, object]:
    if equity_curve_df.empty:
        final_equity = STARTING_EQUITY
        max_drawdown_pct = 0.0
    else:
        final_equity = float(equity_curve_df["equity"].iloc[-1])
        peak = equity_curve_df["equity"].cummax()
        drawdown = (equity_curve_df["equity"] / peak) - 1.0
        max_drawdown_pct = float(drawdown.min()) * 100.0

    trade_count = int(len(trades_df))
    win_rate_pct = float((trades_df["portfolio_net_pnl"] > 0).mean() * 100.0) if trade_count > 0 else 0.0
    calmar_like = 0.0
    if max_drawdown_pct < 0.0:
        calmar_like = (((final_equity / STARTING_EQUITY) - 1.0) * 100.0) / abs(max_drawdown_pct)
    summary = {
        "starting_equity": STARTING_EQUITY,
        "final_equity": round(final_equity, 2),
        "total_return_pct": round(((final_equity / STARTING_EQUITY) - 1.0) * 100.0, 2),
        "trade_count": trade_count,
        "win_rate_pct": round(win_rate_pct, 2),
        "max_drawdown_pct": round(max_drawdown_pct, 2),
        "portfolio_max_open_risk_fraction": risk_cap,
        "calmar_like": round(calmar_like, 4),
    }
    if trade_count > 0 and "strategy" in trades_df.columns and "portfolio_net_pnl" in trades_df.columns:
        contributions = (
            trades_df.groupby("strategy", as_index=False)["portfolio_net_pnl"]
            .sum()
            .sort_values("portfolio_net_pnl", ascending=False)
        )
        summary["strategy_contributions"] = contributions.to_dict(orient="records")
    else:
        summary["strategy_contributions"] = []
    return summary


def run_overlay_allocator(
    strategies: list,
    trades_df: pd.DataFrame,
    risk_cap: float,
    daily_loss_gate_pct: float | None = None,
    max_open_positions: int | None = None,
    delever_drawdown_pct: float | None = None,
    delever_risk_scale: float = 1.0,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, object]]:
    strategy_map = {strategy.name: strategy for strategy in strategies}
    cash = STARTING_EQUITY
    open_positions: list[dict[str, object]] = []
    portfolio_trades: list[dict[str, object]] = []
    equity_curve: list[dict[str, object]] = []
    peak_equity = STARTING_EQUITY

    if trades_df.empty:
        summary = summarize_results(pd.DataFrame(), pd.DataFrame(), risk_cap=risk_cap)
        return pd.DataFrame(), pd.DataFrame(), summary

    trades = trades_df.copy()
    trades["trade_date"] = pd.to_datetime(trades["trade_date"]).dt.date
    trades_by_day_minute = {
        key: frame.reset_index(drop=True)
        for key, frame in trades.groupby(["trade_date", "entry_minute"], sort=True)
    }
    ordered_days = sorted(trades["trade_date"].unique())

    for trade_date in ordered_days:
        day_start_equity: float | None = None
        entries_blocked = False

        for minute_index in range(MINUTES_PER_RTH_SESSION):
            remaining_positions: list[dict[str, object]] = []
            for position in open_positions:
                if position["exit_minute"] == minute_index:
                    quantity = int(position["quantity"])
                    cash += quantity * (
                        float(position["exit_cash_per_combo"]) - float(position["exit_commission_per_combo"])
                    )
                    realized_net = quantity * float(position["net_pnl_per_combo"])
                    portfolio_trades.append(
                        {
                            **position["trade"],
                            "quantity": quantity,
                            "portfolio_net_pnl": round(realized_net, 4),
                            "equity_after_exit": round(cash, 4),
                        }
                    )
                else:
                    remaining_positions.append(position)
            open_positions = remaining_positions

            current_equity = current_portfolio_equity(cash=cash, open_positions=open_positions, minute_index=minute_index)
            peak_equity = max(peak_equity, current_equity)
            if day_start_equity is None:
                day_start_equity = current_equity
            if daily_loss_gate_pct is not None and current_equity <= day_start_equity * (1.0 - daily_loss_gate_pct):
                entries_blocked = True

            drawdown_pct = ((current_equity / peak_equity) - 1.0) * 100.0 if peak_equity > 0.0 else 0.0
            risk_scale = 1.0
            if delever_drawdown_pct is not None and drawdown_pct <= -delever_drawdown_pct:
                risk_scale = delever_risk_scale

            reserved_risk = sum(float(position["max_loss_per_combo"]) * int(position["quantity"]) for position in open_positions)
            entries = trades_by_day_minute.get((trade_date, minute_index))
            if entries is not None and not entries_blocked:
                for row in entries.itertuples(index=False):
                    if max_open_positions is not None and len(open_positions) >= max_open_positions:
                        continue
                    strategy = strategy_map[str(row.strategy)]
                    current_equity = current_portfolio_equity(cash=cash, open_positions=open_positions, minute_index=minute_index)
                    peak_equity = max(peak_equity, current_equity)
                    reserved_risk = sum(float(position["max_loss_per_combo"]) * int(position["quantity"]) for position in open_positions)
                    drawdown_pct = ((current_equity / peak_equity) - 1.0) * 100.0 if peak_equity > 0.0 else 0.0
                    risk_scale = 1.0
                    if delever_drawdown_pct is not None and drawdown_pct <= -delever_drawdown_pct:
                        risk_scale = delever_risk_scale

                    remaining_risk_capacity = max(0.0, current_equity * risk_cap * risk_scale - reserved_risk)
                    per_trade_risk_budget = current_equity * strategy.risk_fraction * risk_scale
                    allocatable_risk = min(per_trade_risk_budget, remaining_risk_capacity)

                    max_loss_per_combo = float(row.max_loss_per_combo)
                    if max_loss_per_combo <= 0.0:
                        continue
                    quantity_by_risk = int(allocatable_risk // max_loss_per_combo)
                    if quantity_by_risk < 1:
                        continue

                    entry_outflow_per_combo = max(
                        0.0,
                        -(float(row.entry_cash_per_combo) - float(row.entry_commission_per_combo)),
                    )
                    if entry_outflow_per_combo > 0.0:
                        quantity_by_cash = int(max(0.0, cash) // entry_outflow_per_combo)
                    else:
                        quantity_by_cash = strategy.max_contracts

                    quantity = min(strategy.max_contracts, quantity_by_risk, quantity_by_cash)
                    if quantity < 1:
                        continue

                    cash += quantity * (float(row.entry_cash_per_combo) - float(row.entry_commission_per_combo))
                    open_positions.append(
                        {
                            "trade": row._asdict(),
                            "quantity": quantity,
                            "exit_minute": int(row.exit_minute),
                            "entry_cash_per_combo": float(row.entry_cash_per_combo),
                            "exit_cash_per_combo": float(row.exit_cash_per_combo),
                            "entry_commission_per_combo": float(row.entry_commission_per_combo),
                            "exit_commission_per_combo": float(row.exit_commission_per_combo),
                            "net_pnl_per_combo": float(row.net_pnl_per_combo),
                            "max_loss_per_combo": max_loss_per_combo,
                            "mark_to_market": {int(key): float(value) for key, value in json.loads(str(row.mark_to_market_json)).items()},
                        }
                    )

            current_equity = current_portfolio_equity(cash=cash, open_positions=open_positions, minute_index=minute_index)
            peak_equity = max(peak_equity, current_equity)
            equity_curve.append(
                {
                    "trade_date": trade_date.isoformat(),
                    "minute_index": minute_index,
                    "equity": round(current_equity, 4),
                    "cash": round(cash, 4),
                    "open_positions": len(open_positions),
                    "entries_blocked": entries_blocked,
                    "risk_scale": risk_scale,
                }
            )

        if open_positions:
            raise RuntimeError(f"Open positions remained after end of day {trade_date}")

    portfolio_trades_df = pd.DataFrame(portfolio_trades)
    equity_curve_df = pd.DataFrame(equity_curve)
    summary = summarize_results(portfolio_trades_df, equity_curve_df, risk_cap=risk_cap)
    return portfolio_trades_df, equity_curve_df, summary


def evaluate_scenario(
    category: str,
    scenario: str,
    trades: pd.DataFrame,
    strategies: list,
    risk_cap: float,
    use_overlay_allocator: bool = False,
    daily_loss_gate_pct: float | None = None,
    max_open_positions: int | None = None,
    delever_drawdown_pct: float | None = None,
    delever_risk_scale: float = 1.0,
) -> dict[str, object]:
    if use_overlay_allocator:
        _, _, summary = run_overlay_allocator(
            strategies=strategies,
            trades_df=trades,
            risk_cap=risk_cap,
            daily_loss_gate_pct=daily_loss_gate_pct,
            max_open_positions=max_open_positions,
            delever_drawdown_pct=delever_drawdown_pct,
            delever_risk_scale=delever_risk_scale,
        )
    else:
        _, _, summary = run_portfolio_allocator(
            strategies=strategies,
            trades_df=trades,
            portfolio_max_open_risk_fraction=risk_cap,
            starting_equity=STARTING_EQUITY,
        )
        summary["calmar_like"] = round(
            (summary["total_return_pct"] / abs(summary["max_drawdown_pct"]))
            if summary["max_drawdown_pct"] < 0.0
            else 0.0,
            4,
        )

    return {
        "category": category,
        "scenario": scenario,
        "trade_count_input": int(len(trades)),
        **summary,
    }


def pick_defensive_candidate(results: pd.DataFrame, baseline: pd.Series) -> pd.Series:
    candidates = results.copy()
    candidates = candidates[candidates["scenario"] != "baseline"]
    candidates = candidates[candidates["total_return_pct"] >= float(baseline["total_return_pct"]) * 0.75]
    if candidates.empty:
        return baseline
    candidates = candidates.sort_values(
        ["max_drawdown_pct", "final_equity"],
        ascending=[False, False],
    ).reset_index(drop=True)
    return candidates.iloc[0]


def write_report(
    path: Path,
    baseline: pd.Series,
    results: pd.DataFrame,
    config: dict[str, object],
    oos_start_date: str,
    oos_end_date: str,
    defensive_candidate: pd.Series,
) -> None:
    lines: list[str] = []
    lines.append("# QQQ Direct-Greeks Deployment Readiness")
    lines.append("")
    lines.append(f"- OOS validation window: {oos_start_date} through {oos_end_date}")
    lines.append(f"- Deployment threshold: {float(config['regime_threshold_pct']):.2f}%")
    lines.append(f"- Bull: {', '.join(f'`{name}`' for name in config['selected_bull'])}")
    lines.append(f"- Bear: {', '.join(f'`{name}`' for name in config['selected_bear'])}")
    lines.append(f"- Choppy: {', '.join(f'`{name}`' for name in config['selected_choppy'])}")
    lines.append("")
    lines.append("## Baseline")
    lines.append("")
    lines.append(f"- Final equity: ${baseline['final_equity']:.2f}")
    lines.append(f"- Return: {baseline['total_return_pct']:.2f}%")
    lines.append(f"- Trades: {int(baseline['trade_count'])}")
    lines.append(f"- Win rate: {baseline['win_rate_pct']:.2f}%")
    lines.append(f"- Max drawdown: {baseline['max_drawdown_pct']:.2f}%")
    lines.append("")
    lines.append("## Execution Stress")
    lines.append("")
    for row in results[results["category"] == "execution"].itertuples(index=False):
        lines.append(
            f"- `{row.scenario}`: final ${row.final_equity:.2f}, return {row.total_return_pct:.2f}%, drawdown {row.max_drawdown_pct:.2f}%, retention {row.return_retention_pct:.1f}%."
        )
    lines.append("")
    lines.append("## Quality Filters")
    lines.append("")
    for row in results[results["category"] == "quality"].itertuples(index=False):
        lines.append(
            f"- `{row.scenario}`: {int(row.trade_count_input)} candidate trades, final ${row.final_equity:.2f}, return {row.total_return_pct:.2f}%, drawdown {row.max_drawdown_pct:.2f}%."
        )
    lines.append("")
    lines.append("## Risk Overlays")
    lines.append("")
    for row in results[results["category"] == "risk_overlay"].itertuples(index=False):
        lines.append(
            f"- `{row.scenario}`: final ${row.final_equity:.2f}, return {row.total_return_pct:.2f}%, drawdown {row.max_drawdown_pct:.2f}%, calmar-like {row.calmar_like:.2f}."
        )
    lines.append("")
    lines.append("## Defensive Candidate")
    lines.append("")
    lines.append(
        f"- Best safety-first variant with at least 75% of baseline return: `{defensive_candidate['scenario']}` -> ${defensive_candidate['final_equity']:.2f}, {defensive_candidate['total_return_pct']:.2f}%, drawdown {defensive_candidate['max_drawdown_pct']:.2f}%."
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = build_parser().parse_args()
    output_dir = Path(args.output_dir).resolve()

    config, oos_start_date, oos_end_date = load_deployment_context(
        output_dir=output_dir,
        walkforward_summary_name=args.walkforward_summary_name,
    )
    selected_trades, selected = prepare_selected_trades(
        output_dir=output_dir,
        candidate_trades_name=args.candidate_trades_name,
        day_returns_name=args.day_returns_name,
        config=config,
        oos_start_date=oos_start_date,
        oos_end_date=oos_end_date,
    )
    strategies = build_strategy_objects(selected=selected)
    risk_cap = float(config["risk_cap"])

    baseline_result = evaluate_scenario(
        category="baseline",
        scenario="baseline",
        trades=selected_trades,
        strategies=strategies,
        risk_cap=risk_cap,
    )

    score_rows: list[dict[str, object]] = [baseline_result]

    execution_scenarios = [
        ("mild_fill_stress", 0.02, 0.75),
        ("heavy_fill_stress", 0.05, 1.00),
        ("extreme_fill_stress", 0.10, 1.25),
    ]
    for scenario_name, extra_slippage, commission in execution_scenarios:
        stressed_trades = transform_execution(
            trades=selected_trades,
            extra_slippage_per_leg=extra_slippage,
            commission_per_contract=commission,
        )
        score_rows.append(
            evaluate_scenario(
                category="execution",
                scenario=scenario_name,
                trades=stressed_trades,
                strategies=strategies,
                risk_cap=risk_cap,
            )
        )

    quality_variants = {
        "strict_ok_on_row_iv": selected_trades[
            selected_trades["all_status_ok"] & selected_trades["all_quality_on_row"]
        ].copy(),
        "ok_or_carried_iv_only": selected_trades[
            selected_trades["all_status_ok_or_carried"] & selected_trades["all_quality_on_row_or_carried"]
        ].copy(),
        "exclude_intrinsic_clip": selected_trades[~selected_trades["has_intrinsic_clip"]].copy(),
    }
    for scenario_name, trades_variant in quality_variants.items():
        score_rows.append(
            evaluate_scenario(
                category="quality",
                scenario=scenario_name,
                trades=trades_variant,
                strategies=strategies,
                risk_cap=risk_cap,
            )
        )

    overlay_scenarios = [
        ("daily_loss_gate_2pct", {"daily_loss_gate_pct": 0.02}),
        ("max_2_open_positions", {"max_open_positions": 2}),
        ("delever_after_10pct_dd", {"delever_drawdown_pct": 10.0, "delever_risk_scale": 0.5}),
        (
            "guardrails_combo",
            {
                "daily_loss_gate_pct": 0.02,
                "max_open_positions": 2,
                "delever_drawdown_pct": 10.0,
                "delever_risk_scale": 0.5,
            },
        ),
    ]
    for scenario_name, overlay_kwargs in overlay_scenarios:
        score_rows.append(
            evaluate_scenario(
                category="risk_overlay",
                scenario=scenario_name,
                trades=selected_trades,
                strategies=strategies,
                risk_cap=risk_cap,
                use_overlay_allocator=True,
                **overlay_kwargs,
            )
        )

    scorecard = pd.DataFrame(score_rows)
    baseline = scorecard.loc[scorecard["scenario"] == "baseline"].iloc[0]
    scorecard["return_retention_pct"] = (scorecard["total_return_pct"] / float(baseline["total_return_pct"])) * 100.0
    scorecard["drawdown_delta_pct"] = scorecard["max_drawdown_pct"] - float(baseline["max_drawdown_pct"])
    scorecard["trade_retention_pct"] = (scorecard["trade_count"] / float(baseline["trade_count"])) * 100.0
    scorecard = scorecard.sort_values(["category", "scenario"]).reset_index(drop=True)

    defensive_candidate = pick_defensive_candidate(results=scorecard, baseline=baseline)

    summary_payload = {
        "baseline": baseline.to_dict(),
        "deployment_config": config,
        "oos_start_date": oos_start_date,
        "oos_end_date": oos_end_date,
        "defensive_candidate": defensive_candidate.to_dict(),
        "scorecard_rows": scorecard.to_dict(orient="records"),
    }

    scorecard.to_csv(output_dir / args.scorecard_name, index=False)
    (output_dir / args.summary_name).write_text(json.dumps(summary_payload, indent=2), encoding="utf-8")
    write_report(
        path=output_dir / args.report_name,
        baseline=baseline,
        results=scorecard,
        config=config,
        oos_start_date=oos_start_date,
        oos_end_date=oos_end_date,
        defensive_candidate=defensive_candidate,
    )

    print(
        json.dumps(
            {
                "scorecard_csv": str(output_dir / args.scorecard_name),
                "summary_json": str(output_dir / args.summary_name),
                "report_md": str(output_dir / args.report_name),
                "baseline_final_equity": float(baseline["final_equity"]),
                "defensive_candidate": str(defensive_candidate["scenario"]),
                "defensive_candidate_final_equity": float(defensive_candidate["final_equity"]),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
