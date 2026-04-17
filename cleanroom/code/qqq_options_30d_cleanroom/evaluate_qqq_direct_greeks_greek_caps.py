from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from backtest_qqq_greeks_portfolio import MINUTES_PER_RTH_SESSION, current_portfolio_equity
from evaluate_qqq_direct_greeks_readiness import (
    STARTING_EQUITY,
    annotate_trades,
    build_strategy_objects,
    load_day_return_map,
    summarize_results,
)
from optimize_qqq_regime_portfolio import relabel_candidate_trades
from backtest_qqq_regime_gated_portfolio import filter_candidate_trades


DEFAULT_OUTPUT_DIR = Path(__file__).resolve().parent / "output"
DEFAULT_CONFIG_PATH = DEFAULT_OUTPUT_DIR / "qqq_direct_greeks_balanced_deployment_config.json"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Greek-cap sweep for the balanced direct-Greeks deployment candidate.")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--config-path", default=str(DEFAULT_CONFIG_PATH))
    parser.add_argument("--candidate-trades-name", default="qqq_direct_greeks_candidate_trades.csv")
    parser.add_argument("--day-returns-name", default="qqq_direct_greeks_day_returns.csv")
    parser.add_argument("--scorecard-name", default="qqq_direct_greeks_greek_cap_scorecard.csv")
    parser.add_argument("--summary-name", default="qqq_direct_greeks_greek_cap_summary.json")
    parser.add_argument("--report-name", default="qqq_direct_greeks_greek_cap_report.md")
    return parser


def load_config(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def prepare_trades_for_config(
    output_dir: Path,
    candidate_trades_name: str,
    day_returns_name: str,
    config: dict[str, object],
) -> tuple[pd.DataFrame, dict[str, list[str]]]:
    trades = pd.read_csv(output_dir / candidate_trades_name)
    trades["trade_date"] = pd.to_datetime(trades["trade_date"]).dt.date
    oos_start = pd.to_datetime(config["oos_validation_window"]["start_date"]).date()
    oos_end = pd.to_datetime(config["oos_validation_window"]["end_date"]).date()
    trades = trades[(trades["trade_date"] >= oos_start) & (trades["trade_date"] <= oos_end)].copy()

    day_return_map = load_day_return_map(output_dir=output_dir, day_returns_name=day_returns_name)
    relabeled = relabel_candidate_trades(
        candidate_trades=trades,
        day_return_map=day_return_map,
        threshold=float(config["regime"]["threshold_pct"]),
    )
    selected = {
        "bull": list(config["regime"]["bull_strategies"]),
        "bear": list(config["regime"]["bear_strategies"]),
        "choppy": list(config["regime"]["choppy_strategies"]),
    }
    filtered = filter_candidate_trades(trades=relabeled, selected=selected)
    return annotate_trades(filtered), selected


def trade_exposure_per_combo(row) -> tuple[float, float]:
    legs = json.loads(str(row.legs_json))
    delta_shares = 0.0
    vega_dollars_1pct = 0.0
    for leg in legs:
        side_sign = 1.0 if str(leg["side"]) == "long" else -1.0
        delta_shares += side_sign * float(leg.get("delta", 0.0) or 0.0) * 100.0
        vega_dollars_1pct += side_sign * float(leg.get("vega_1pct", 0.0) or 0.0) * 100.0
    return delta_shares, vega_dollars_1pct


def portfolio_exposure(open_positions: list[dict[str, object]]) -> tuple[float, float]:
    net_delta = 0.0
    net_vega = 0.0
    for position in open_positions:
        quantity = int(position["quantity"])
        net_delta += float(position["delta_shares_per_combo"]) * quantity
        net_vega += float(position["vega_dollars_per_combo"]) * quantity
    return net_delta, net_vega


def run_overlay_allocator_with_greek_caps(
    strategies: list,
    trades_df: pd.DataFrame,
    risk_cap: float,
    daily_loss_gate_pct: float,
    delever_drawdown_pct: float,
    delever_risk_scale: float,
    max_open_positions: int | None = None,
    max_abs_delta_shares: float | None = None,
    max_abs_vega_dollars_1pct: float | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, object], pd.DataFrame]:
    strategy_map = {strategy.name: strategy for strategy in strategies}
    cash = STARTING_EQUITY
    open_positions: list[dict[str, object]] = []
    portfolio_trades: list[dict[str, object]] = []
    equity_curve: list[dict[str, object]] = []
    exposure_curve: list[dict[str, object]] = []
    peak_equity = STARTING_EQUITY

    if trades_df.empty:
        summary = summarize_results(pd.DataFrame(), pd.DataFrame(), risk_cap=risk_cap)
        return pd.DataFrame(), pd.DataFrame(), summary, pd.DataFrame()

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
            if current_equity <= day_start_equity * (1.0 - daily_loss_gate_pct):
                entries_blocked = True

            drawdown_pct = ((current_equity / peak_equity) - 1.0) * 100.0 if peak_equity > 0.0 else 0.0
            risk_scale = delever_risk_scale if drawdown_pct <= -delever_drawdown_pct else 1.0

            entries = trades_by_day_minute.get((trade_date, minute_index))
            if entries is not None and not entries_blocked:
                for row in entries.itertuples(index=False):
                    if max_open_positions is not None and len(open_positions) >= max_open_positions:
                        continue

                    strategy = strategy_map[str(row.strategy)]
                    current_equity = current_portfolio_equity(cash=cash, open_positions=open_positions, minute_index=minute_index)
                    peak_equity = max(peak_equity, current_equity)
                    drawdown_pct = ((current_equity / peak_equity) - 1.0) * 100.0 if peak_equity > 0.0 else 0.0
                    risk_scale = delever_risk_scale if drawdown_pct <= -delever_drawdown_pct else 1.0

                    reserved_risk = sum(float(position["max_loss_per_combo"]) * int(position["quantity"]) for position in open_positions)
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

                    delta_per_combo, vega_per_combo = trade_exposure_per_combo(row)
                    quantity = min(strategy.max_contracts, quantity_by_risk, quantity_by_cash)
                    if quantity < 1:
                        continue

                    if max_abs_delta_shares is not None or max_abs_vega_dollars_1pct is not None:
                        open_delta, open_vega = portfolio_exposure(open_positions)
                        while quantity >= 1:
                            projected_delta = open_delta + delta_per_combo * quantity
                            projected_vega = open_vega + vega_per_combo * quantity
                            delta_ok = True if max_abs_delta_shares is None else abs(projected_delta) <= max_abs_delta_shares
                            vega_ok = True if max_abs_vega_dollars_1pct is None else abs(projected_vega) <= max_abs_vega_dollars_1pct
                            if delta_ok and vega_ok:
                                break
                            quantity -= 1
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
                            "delta_shares_per_combo": delta_per_combo,
                            "vega_dollars_per_combo": vega_per_combo,
                        }
                    )

            current_equity = current_portfolio_equity(cash=cash, open_positions=open_positions, minute_index=minute_index)
            peak_equity = max(peak_equity, current_equity)
            net_delta, net_vega = portfolio_exposure(open_positions)
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
            exposure_curve.append(
                {
                    "trade_date": trade_date.isoformat(),
                    "minute_index": minute_index,
                    "net_delta_shares": round(net_delta, 4),
                    "net_vega_dollars_1pct": round(net_vega, 4),
                    "abs_net_delta_shares": round(abs(net_delta), 4),
                    "abs_net_vega_dollars_1pct": round(abs(net_vega), 4),
                }
            )

        if open_positions:
            raise RuntimeError(f"Open positions remained after end of day {trade_date}")

    portfolio_trades_df = pd.DataFrame(portfolio_trades)
    equity_curve_df = pd.DataFrame(equity_curve)
    exposure_curve_df = pd.DataFrame(exposure_curve)
    summary = summarize_results(portfolio_trades_df, equity_curve_df, risk_cap=risk_cap)
    if not exposure_curve_df.empty:
        summary["max_abs_delta_shares_observed"] = float(exposure_curve_df["abs_net_delta_shares"].max())
        summary["max_abs_vega_dollars_1pct_observed"] = float(exposure_curve_df["abs_net_vega_dollars_1pct"].max())
        summary["p95_abs_delta_shares_observed"] = float(exposure_curve_df["abs_net_delta_shares"].quantile(0.95))
        summary["p95_abs_vega_dollars_1pct_observed"] = float(exposure_curve_df["abs_net_vega_dollars_1pct"].quantile(0.95))
    else:
        summary["max_abs_delta_shares_observed"] = 0.0
        summary["max_abs_vega_dollars_1pct_observed"] = 0.0
        summary["p95_abs_delta_shares_observed"] = 0.0
        summary["p95_abs_vega_dollars_1pct_observed"] = 0.0
    return portfolio_trades_df, equity_curve_df, summary, exposure_curve_df


def build_cap_scenarios(baseline_summary: dict[str, object]) -> list[dict[str, object]]:
    delta_max = float(baseline_summary["max_abs_delta_shares_observed"])
    vega_max = float(baseline_summary["max_abs_vega_dollars_1pct_observed"])
    scenarios: list[dict[str, object]] = [
        {"scenario": "baseline_no_caps", "max_abs_delta_shares": None, "max_abs_vega_dollars_1pct": None}
    ]
    for scale in [0.8, 0.65, 0.5]:
        scenarios.append(
            {
                "scenario": f"delta_cap_{int(scale * 100)}pct",
                "max_abs_delta_shares": round(delta_max * scale, 2),
                "max_abs_vega_dollars_1pct": None,
            }
        )
        scenarios.append(
            {
                "scenario": f"vega_cap_{int(scale * 100)}pct",
                "max_abs_delta_shares": None,
                "max_abs_vega_dollars_1pct": round(vega_max * scale, 2),
            }
        )
    for scale in [0.8, 0.65, 0.5]:
        scenarios.append(
            {
                "scenario": f"delta_vega_cap_{int(scale * 100)}pct",
                "max_abs_delta_shares": round(delta_max * scale, 2),
                "max_abs_vega_dollars_1pct": round(vega_max * scale, 2),
            }
        )
    return scenarios


def pick_best_cap_variant(results: pd.DataFrame, baseline: pd.Series) -> pd.Series:
    candidates = results[results["scenario"] != "baseline_no_caps"].copy()
    candidates = candidates[candidates["total_return_pct"] >= float(baseline["total_return_pct"]) * 0.95]
    if candidates.empty:
        return baseline
    return candidates.sort_values(
        ["max_drawdown_pct", "calmar_like", "final_equity"],
        ascending=[False, False, False],
    ).iloc[0]


def write_report(path: Path, results: pd.DataFrame, baseline: pd.Series, best_variant: pd.Series, config: dict[str, object]) -> None:
    lines: list[str] = []
    lines.append("# QQQ Direct-Greeks Greek Cap Sweep")
    lines.append("")
    lines.append(f"- Deployment config: `{config['name']}`")
    lines.append(f"- OOS window: {config['oos_validation_window']['start_date']} through {config['oos_validation_window']['end_date']}")
    lines.append("")
    lines.append("## Baseline Exposure")
    lines.append("")
    lines.append(f"- Final equity: ${baseline['final_equity']:.2f}")
    lines.append(f"- Return: {baseline['total_return_pct']:.2f}%")
    lines.append(f"- Drawdown: {baseline['max_drawdown_pct']:.2f}%")
    lines.append(f"- Max abs net delta: {baseline['max_abs_delta_shares_observed']:.2f} shares")
    lines.append(f"- Max abs net vega: {baseline['max_abs_vega_dollars_1pct_observed']:.2f} dollars per 1 vol point")
    lines.append("")
    lines.append("## Top Variants")
    lines.append("")
    for row in results.head(10).itertuples(index=False):
        lines.append(
            f"- `{row.scenario}`: final ${row.final_equity:.2f}, return {row.total_return_pct:.2f}%, drawdown {row.max_drawdown_pct:.2f}%, delta cap {row.max_abs_delta_shares}, vega cap {row.max_abs_vega_dollars_1pct}."
        )
    lines.append("")
    lines.append("## Best Risk-Aware Variant")
    lines.append("")
    lines.append(
        f"- `{best_variant['scenario']}` -> ${best_variant['final_equity']:.2f}, {best_variant['total_return_pct']:.2f}%, drawdown {best_variant['max_drawdown_pct']:.2f}%."
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = build_parser().parse_args()
    output_dir = Path(args.output_dir).resolve()
    config = load_config(Path(args.config_path).resolve())
    trades, selected = prepare_trades_for_config(
        output_dir=output_dir,
        candidate_trades_name=args.candidate_trades_name,
        day_returns_name=args.day_returns_name,
        config=config,
    )
    strategies = build_strategy_objects(selected=selected)
    portfolio_cfg = dict(config["portfolio"])

    _, _, baseline_summary, baseline_exposures = run_overlay_allocator_with_greek_caps(
        strategies=strategies,
        trades_df=trades,
        risk_cap=float(portfolio_cfg["risk_cap"]),
        daily_loss_gate_pct=float(portfolio_cfg["daily_loss_gate_pct"]),
        delever_drawdown_pct=float(portfolio_cfg["delever_drawdown_pct"]),
        delever_risk_scale=float(portfolio_cfg["delever_risk_scale"]),
        max_open_positions=portfolio_cfg["max_open_positions"],
    )

    rows: list[dict[str, object]] = []
    for spec in build_cap_scenarios(baseline_summary=baseline_summary):
        _, _, summary, _ = run_overlay_allocator_with_greek_caps(
            strategies=strategies,
            trades_df=trades,
            risk_cap=float(portfolio_cfg["risk_cap"]),
            daily_loss_gate_pct=float(portfolio_cfg["daily_loss_gate_pct"]),
            delever_drawdown_pct=float(portfolio_cfg["delever_drawdown_pct"]),
            delever_risk_scale=float(portfolio_cfg["delever_risk_scale"]),
            max_open_positions=portfolio_cfg["max_open_positions"],
            max_abs_delta_shares=spec["max_abs_delta_shares"],
            max_abs_vega_dollars_1pct=spec["max_abs_vega_dollars_1pct"],
        )
        rows.append(
            {
                "scenario": spec["scenario"],
                "max_abs_delta_shares": spec["max_abs_delta_shares"],
                "max_abs_vega_dollars_1pct": spec["max_abs_vega_dollars_1pct"],
                **summary,
            }
        )

    results = pd.DataFrame(rows)
    baseline = results[results["scenario"] == "baseline_no_caps"].iloc[0]
    results["return_retention_pct"] = (results["total_return_pct"] / float(baseline["total_return_pct"])) * 100.0
    results["drawdown_delta_pct"] = results["max_drawdown_pct"] - float(baseline["max_drawdown_pct"])
    results = results.sort_values(["calmar_like", "final_equity"], ascending=[False, False]).reset_index(drop=True)

    best_variant = pick_best_cap_variant(results=results, baseline=baseline)
    summary_payload = {
        "deployment_config": config,
        "baseline": baseline.to_dict(),
        "best_variant": best_variant.to_dict(),
        "baseline_exposure_curve_stats": {
            "rows": int(len(baseline_exposures)),
            "max_abs_delta_shares": baseline_summary["max_abs_delta_shares_observed"],
            "max_abs_vega_dollars_1pct": baseline_summary["max_abs_vega_dollars_1pct_observed"],
            "p95_abs_delta_shares": baseline_summary["p95_abs_delta_shares_observed"],
            "p95_abs_vega_dollars_1pct": baseline_summary["p95_abs_vega_dollars_1pct_observed"],
        },
        "rows": results.to_dict(orient="records"),
    }

    results.to_csv(output_dir / args.scorecard_name, index=False)
    (output_dir / args.summary_name).write_text(json.dumps(summary_payload, indent=2), encoding="utf-8")
    write_report(path=output_dir / args.report_name, results=results, baseline=baseline, best_variant=best_variant, config=config)

    print(
        json.dumps(
            {
                "scorecard_csv": str(output_dir / args.scorecard_name),
                "summary_json": str(output_dir / args.summary_name),
                "report_md": str(output_dir / args.report_name),
                "best_variant": str(best_variant["scenario"]),
                "best_variant_final_equity": float(best_variant["final_equity"]),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
