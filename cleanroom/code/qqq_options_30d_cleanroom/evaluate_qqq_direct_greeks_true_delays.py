from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from backtest_qqq_direct_greeks_dataset import (
    DEFAULT_DATASET_ROOT,
    assign_regime,
    build_context_from_stock,
    load_option_day,
    load_stock_day,
    prepare_option_day,
    select_leg,
)
from backtest_qqq_greeks_portfolio import build_delta_strategies
from backtest_qqq_option_strategies import (
    COMMISSION_PER_CONTRACT,
    SIGNAL_DISPATCH,
    close_cashflow,
    combo_entry_net_premium,
    estimate_combo_bounds,
    open_cashflow,
    resolve_dte,
)
from evaluate_qqq_direct_greeks_readiness import annotate_trades, build_strategy_objects, run_overlay_allocator


DEFAULT_OUTPUT_DIR = Path(__file__).resolve().parent / "output"
DEFAULT_CONFIG_PATH = DEFAULT_OUTPUT_DIR / "qqq_direct_greeks_balanced_deployment_config.json"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="True delayed execution regeneration tests for the direct-Greeks deployment book.")
    parser.add_argument("--dataset-root")
    parser.add_argument("--config-path", default=str(DEFAULT_CONFIG_PATH))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--scorecard-name", default="qqq_direct_greeks_true_delay_scorecard.csv")
    parser.add_argument("--summary-name", default="qqq_direct_greeks_true_delay_summary.json")
    parser.add_argument("--report-name", default="qqq_direct_greeks_true_delay_report.md")
    return parser


def load_config(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def scenario_specs() -> list[dict[str, object]]:
    return [
        {"scenario": "delay_0m_entry_0m_exit", "entry_delay_minutes": 0, "exit_delay_minutes": 0},
        {"scenario": "delay_1m_entry_0m_exit", "entry_delay_minutes": 1, "exit_delay_minutes": 0},
        {"scenario": "delay_0m_entry_1m_exit", "entry_delay_minutes": 0, "exit_delay_minutes": 1},
        {"scenario": "delay_1m_entry_1m_exit", "entry_delay_minutes": 1, "exit_delay_minutes": 1},
        {"scenario": "delay_2m_entry_2m_exit", "entry_delay_minutes": 2, "exit_delay_minutes": 2},
    ]


def selected_for_regime(config: dict[str, object], regime: str) -> list[str]:
    regime_config = dict(config["regime"])
    mapping = {
        "bull": list(regime_config["bull_strategies"]),
        "bear": list(regime_config["bear_strategies"]),
        "choppy": list(regime_config["choppy_strategies"]),
    }
    return mapping.get(regime, [])


def get_exit_prices_for_minute(
    legs: list[dict[str, object]],
    price_series_by_symbol: dict[str, pd.Series],
    minute_index: int,
    session_last_minute: int,
) -> list[float] | None:
    current_prices: list[float] = []
    for leg in legs:
        series = price_series_by_symbol.get(str(leg["symbol"]))
        if series is None:
            return None
        raw_price = None
        for idx in range(minute_index, session_last_minute + 1):
            candidate = series.get(idx)
            if candidate is not None and not pd.isna(candidate):
                raw_price = float(candidate)
                break
        if raw_price is None:
            return None
        current_prices.append(raw_price)
    return current_prices


def mark_to_market_for_minute(
    legs: list[dict[str, object]],
    price_series_by_symbol: dict[str, pd.Series],
    minute_index: int,
    session_last_minute: int,
    exit_commission_per_combo: float,
) -> float | None:
    prices = get_exit_prices_for_minute(
        legs=legs,
        price_series_by_symbol=price_series_by_symbol,
        minute_index=minute_index,
        session_last_minute=session_last_minute,
    )
    if prices is None:
        return None
    return close_cashflow(legs=legs, exit_prices_raw=prices, quantity=1) - exit_commission_per_combo


def generate_trade_for_day(
    strategy,
    ctx,
    chain_groups: dict[tuple[int, int, str], pd.DataFrame],
    price_series_by_symbol: dict[str, pd.Series],
    regime: str,
    entry_delay_minutes: int,
    exit_delay_minutes: int,
) -> dict[str, object] | None:
    dte = resolve_dte(available_dtes=ctx.available_dtes, mode=strategy.dte_mode)
    if dte is None:
        return None

    signal_idx = SIGNAL_DISPATCH[strategy.signal_name](ctx)
    if signal_idx is None:
        return None

    session_last_minute = len(ctx.frame) - 1
    hard_exit_idx = min(strategy.hard_exit_minute, session_last_minute)
    entry_idx = signal_idx + entry_delay_minutes
    if entry_idx >= hard_exit_idx:
        return None

    used_symbols: set[str] = set()
    legs: list[dict[str, object]] = []
    for leg_template in strategy.legs:
        selected = select_leg(
            chain_groups=chain_groups,
            minute_index=entry_idx,
            dte=dte,
            leg=leg_template,
            used_symbols=used_symbols,
        )
        if selected is None:
            return None
        used_symbols.add(str(selected["symbol"]))
        legs.append(selected)

    entry_cash_per_combo = open_cashflow(legs=legs, quantity=1)
    entry_commission_per_combo = COMMISSION_PER_CONTRACT * len(legs)
    exit_commission_per_combo = COMMISSION_PER_CONTRACT * len(legs)
    entry_net_premium = combo_entry_net_premium(legs)
    max_loss_per_combo, max_profit_per_combo = estimate_combo_bounds(legs=legs, entry_net_premium=entry_net_premium)
    target_dollars = abs(entry_net_premium) * 100.0 * strategy.profit_target_multiple
    stop_dollars = abs(entry_net_premium) * 100.0 * strategy.stop_loss_multiple

    mark_to_market: dict[int, float] = {}
    trigger_idx: int | None = None
    trigger_reason = "time_exit"

    for idx in range(entry_idx + 1, hard_exit_idx + 1):
        mtm_value = mark_to_market_for_minute(
            legs=legs,
            price_series_by_symbol=price_series_by_symbol,
            minute_index=idx,
            session_last_minute=session_last_minute,
            exit_commission_per_combo=exit_commission_per_combo,
        )
        if mtm_value is None:
            continue
        mark_to_market[idx] = mtm_value
        current_net_pnl = entry_cash_per_combo + mtm_value - entry_commission_per_combo
        if current_net_pnl >= target_dollars:
            trigger_idx = idx
            trigger_reason = "profit_target"
            break
        if current_net_pnl <= -stop_dollars:
            trigger_idx = idx
            trigger_reason = "stop_loss"
            break

    if trigger_idx is None:
        trigger_idx = hard_exit_idx

    exit_idx = min(trigger_idx + exit_delay_minutes, session_last_minute)
    if exit_idx <= entry_idx:
        return None

    for idx in range(trigger_idx + 1, exit_idx + 1):
        mtm_value = mark_to_market_for_minute(
            legs=legs,
            price_series_by_symbol=price_series_by_symbol,
            minute_index=idx,
            session_last_minute=session_last_minute,
            exit_commission_per_combo=exit_commission_per_combo,
        )
        if mtm_value is not None:
            mark_to_market[idx] = mtm_value

    exit_prices = get_exit_prices_for_minute(
        legs=legs,
        price_series_by_symbol=price_series_by_symbol,
        minute_index=exit_idx,
        session_last_minute=session_last_minute,
    )
    if exit_prices is None:
        return None

    exit_cash_per_combo = close_cashflow(legs=legs, exit_prices_raw=exit_prices, quantity=1)
    net_pnl_per_combo = entry_cash_per_combo + exit_cash_per_combo - entry_commission_per_combo - exit_commission_per_combo
    signal_time = ctx.frame.loc[signal_idx, "timestamp_et"]
    entry_time = ctx.frame.loc[entry_idx, "timestamp_et"]
    exit_time = ctx.frame.loc[exit_idx, "timestamp_et"]

    return {
        "strategy": strategy.name,
        "family": strategy.family,
        "description": strategy.description,
        "trade_date": ctx.trade_date.isoformat(),
        "regime": regime,
        "dte": dte,
        "signal_minute": int(signal_idx),
        "entry_minute": int(entry_idx),
        "trigger_exit_minute": int(trigger_idx),
        "exit_minute": int(exit_idx),
        "entry_delay_minutes": int(entry_delay_minutes),
        "exit_delay_minutes": int(exit_delay_minutes),
        "signal_time_et": signal_time.isoformat(),
        "entry_time_et": entry_time.isoformat(),
        "exit_time_et": exit_time.isoformat(),
        "exit_reason": trigger_reason,
        "entry_underlying": round(float(ctx.frame.loc[entry_idx, "qqq_close"]), 4),
        "exit_underlying": round(float(ctx.frame.loc[exit_idx, "qqq_close"]), 4),
        "entry_cash_per_combo": round(entry_cash_per_combo, 4),
        "exit_cash_per_combo": round(exit_cash_per_combo, 4),
        "entry_commission_per_combo": round(entry_commission_per_combo, 4),
        "exit_commission_per_combo": round(exit_commission_per_combo, 4),
        "net_pnl_per_combo": round(net_pnl_per_combo, 4),
        "max_loss_per_combo": round(max_loss_per_combo, 4),
        "max_profit_per_combo": round(max_profit_per_combo, 4),
        "return_on_risk_pct": round((net_pnl_per_combo / max_loss_per_combo) * 100.0, 4) if max_loss_per_combo > 0.0 else 0.0,
        "holding_minutes": int(exit_idx - entry_idx),
        "legs_json": json.dumps(legs, sort_keys=True),
        "mark_to_market_json": json.dumps(mark_to_market, sort_keys=True),
    }


def evaluate_delay_scenarios(dataset_root: Path, config: dict[str, object]) -> dict[str, pd.DataFrame]:
    scenario_trade_rows = {spec["scenario"]: [] for spec in scenario_specs()}
    strategy_map = {strategy.name: strategy for strategy in build_delta_strategies()}
    start_date = str(config["oos_validation_window"]["start_date"])
    end_date = str(config["oos_validation_window"]["end_date"])

    stock_root = dataset_root / "data" / "raw" / "qqq_stock_1m"
    option_root = dataset_root / "data" / "processed" / "selected_daily"
    trade_date_values = sorted(
        path.name.split("=", 1)[1]
        for path in stock_root.iterdir()
        if path.is_dir()
        and path.name.startswith("trade_date=")
        and start_date <= path.name.split("=", 1)[1] <= end_date
        and (option_root / path.name / "dense.parquet").exists()
    )

    prev_close: float | None = None
    for position, trade_date in enumerate(trade_date_values, start=1):
        stock = load_stock_day(dataset_root=dataset_root, trade_date=trade_date)
        options = load_option_day(dataset_root=dataset_root, trade_date=trade_date)
        if stock.empty or options.empty:
            continue

        available_dtes, chain_groups, price_series_by_symbol = prepare_option_day(options=options)
        if not available_dtes:
            prev_close = float(stock["close"].iloc[-1])
            continue

        ctx = build_context_from_stock(stock=stock, available_dtes=available_dtes, prev_close=prev_close)
        day_open = float(stock["open"].iloc[0])
        day_close = float(stock["close"].iloc[-1])
        regime = assign_regime(
            day_ret_pct=((day_close / day_open) - 1.0) * 100.0,
            threshold=float(config["regime"]["threshold_pct"]),
        )
        allowed_strategies = [strategy_map[name] for name in selected_for_regime(config=config, regime=regime) if name in strategy_map]

        for spec in scenario_specs():
            for strategy in allowed_strategies:
                trade = generate_trade_for_day(
                    strategy=strategy,
                    ctx=ctx,
                    chain_groups=chain_groups,
                    price_series_by_symbol=price_series_by_symbol,
                    regime=regime,
                    entry_delay_minutes=int(spec["entry_delay_minutes"]),
                    exit_delay_minutes=int(spec["exit_delay_minutes"]),
                )
                if trade is not None:
                    scenario_trade_rows[str(spec["scenario"])].append(trade)

        prev_close = day_close
        if position % 25 == 0 or position == len(trade_date_values):
            print(f"Processed {position}/{len(trade_date_values)} OOS days through {trade_date}", flush=True)

    scenario_frames: dict[str, pd.DataFrame] = {}
    for scenario_name, rows in scenario_trade_rows.items():
        frame = pd.DataFrame(rows)
        if not frame.empty:
            frame = frame.sort_values(["trade_date", "entry_minute", "strategy"]).reset_index(drop=True)
        scenario_frames[scenario_name] = annotate_trades(frame)
    return scenario_frames


def write_report(path: Path, results: pd.DataFrame, config: dict[str, object]) -> None:
    baseline = results[results["scenario"] == "delay_0m_entry_0m_exit"].iloc[0]
    lines: list[str] = []
    lines.append("# QQQ Direct-Greeks True Delay Test")
    lines.append("")
    lines.append(f"- Deployment config: `{config['name']}`")
    lines.append(f"- OOS window: {config['oos_validation_window']['start_date']} through {config['oos_validation_window']['end_date']}")
    lines.append("")
    lines.append("## Baseline Regenerated")
    lines.append("")
    lines.append(f"- Final equity: ${baseline['final_equity']:.2f}")
    lines.append(f"- Return: {baseline['total_return_pct']:.2f}%")
    lines.append(f"- Drawdown: {baseline['max_drawdown_pct']:.2f}%")
    lines.append("")
    lines.append("## Delay Scenarios")
    lines.append("")
    for row in results.itertuples(index=False):
        lines.append(
            f"- `{row.scenario}`: final ${row.final_equity:.2f}, return {row.total_return_pct:.2f}%, drawdown {row.max_drawdown_pct:.2f}%, return retention {row.return_retention_pct:.1f}%."
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = build_parser().parse_args()
    config = load_config(Path(args.config_path).resolve())
    dataset_root = Path(args.dataset_root or str(config.get("dataset_root", DEFAULT_DATASET_ROOT))).resolve()
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    scenario_frames = evaluate_delay_scenarios(dataset_root=dataset_root, config=config)
    selected = {
        "bull": list(config["regime"]["bull_strategies"]),
        "bear": list(config["regime"]["bear_strategies"]),
        "choppy": list(config["regime"]["choppy_strategies"]),
    }
    strategies = build_strategy_objects(selected=selected)
    portfolio_cfg = dict(config["portfolio"])

    summary_rows: list[dict[str, object]] = []
    for scenario_name, frame in scenario_frames.items():
        _, _, summary = run_overlay_allocator(
            strategies=strategies,
            trades_df=frame,
            risk_cap=float(portfolio_cfg["risk_cap"]),
            daily_loss_gate_pct=float(portfolio_cfg["daily_loss_gate_pct"]),
            max_open_positions=portfolio_cfg["max_open_positions"],
            delever_drawdown_pct=float(portfolio_cfg["delever_drawdown_pct"]),
            delever_risk_scale=float(portfolio_cfg["delever_risk_scale"]),
        )
        summary_rows.append({"scenario": scenario_name, "candidate_trade_count": int(len(frame)), **summary})

    results = pd.DataFrame(summary_rows).sort_values("scenario").reset_index(drop=True)
    baseline = results[results["scenario"] == "delay_0m_entry_0m_exit"].iloc[0]
    results["return_retention_pct"] = (results["total_return_pct"] / float(baseline["total_return_pct"])) * 100.0
    results["drawdown_delta_pct"] = results["max_drawdown_pct"] - float(baseline["max_drawdown_pct"])

    summary_payload = {
        "deployment_config": config,
        "baseline": baseline.to_dict(),
        "rows": results.to_dict(orient="records"),
    }
    results.to_csv(output_dir / args.scorecard_name, index=False)
    (output_dir / args.summary_name).write_text(json.dumps(summary_payload, indent=2), encoding="utf-8")
    write_report(path=output_dir / args.report_name, results=results, config=config)

    print(
        json.dumps(
            {
                "scorecard_csv": str(output_dir / args.scorecard_name),
                "summary_json": str(output_dir / args.summary_name),
                "report_md": str(output_dir / args.report_name)
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
