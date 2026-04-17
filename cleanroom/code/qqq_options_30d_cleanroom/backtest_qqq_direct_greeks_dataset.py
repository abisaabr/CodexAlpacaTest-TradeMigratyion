from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path

import pandas as pd

from backtest_qqq_greeks_portfolio import (
    DeltaLegTemplate,
    DeltaStrategy,
    build_delta_strategies,
    run_portfolio_allocator,
    summarize_regimes,
)
from backtest_qqq_option_strategies import (
    COMMISSION_PER_CONTRACT,
    DayContext,
    SIGNAL_DISPATCH,
    STARTING_EQUITY,
    buy_fill,
    close_cashflow,
    combo_entry_net_premium,
    estimate_combo_bounds,
    open_cashflow,
    resolve_dte,
    sell_fill,
)


DEFAULT_DATASET_ROOT = Path(
    r"C:\Users\rabisaab\Downloads\qqq_alpaca_atm_0_7dte_backfill_with_greeks_clean_rerun"
)
DEFAULT_CONFIG_PATH = Path(
    r"C:\Users\rabisaab\Downloads\qqq_options_30d_cleanroom\output\qqq_regime_portfolio_best_config.json"
)
DEFAULT_OUTPUT_DIR = Path(__file__).resolve().parent / "output"
STOCK_ROOT_REL = Path("data") / "raw" / "qqq_stock_1m"
OPTION_ROOT_REL = Path("data") / "processed" / "selected_daily"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the optimized QQQ regime-gated portfolio on the larger direct-Greeks dataset.")
    parser.add_argument("--dataset-root", default=str(DEFAULT_DATASET_ROOT))
    parser.add_argument("--config-path", default=str(DEFAULT_CONFIG_PATH))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--start-date")
    parser.add_argument("--end-date")
    parser.add_argument("--candidate-name", default="qqq_direct_greeks_candidate_trades.csv")
    parser.add_argument("--filtered-candidates-name", default="qqq_direct_greeks_filtered_candidates.csv")
    parser.add_argument("--regime-summary-name", default="qqq_direct_greeks_regime_summary.csv")
    parser.add_argument("--day-returns-name", default="qqq_direct_greeks_day_returns.csv")
    parser.add_argument("--portfolio-trades-name", default="qqq_direct_greeks_portfolio_trades.csv")
    parser.add_argument("--equity-name", default="qqq_direct_greeks_portfolio_equity_curve.csv")
    parser.add_argument("--summary-name", default="qqq_direct_greeks_portfolio_summary.json")
    parser.add_argument("--report-name", default="qqq_direct_greeks_portfolio_report.md")
    return parser


def parse_selected_strategies(raw_value: object) -> list[str]:
    if isinstance(raw_value, list):
        return [str(value) for value in raw_value]
    if raw_value in (None, ""):
        return []
    return [str(value) for value in json.loads(str(raw_value))]


def assign_regime(day_ret_pct: float, threshold: float) -> str:
    if day_ret_pct >= threshold:
        return "bull"
    if day_ret_pct <= -threshold:
        return "bear"
    return "choppy"


def maybe_float(value: object) -> float | None:
    if value is None or pd.isna(value):
        return None
    return float(value)


def build_context_from_stock(
    stock: pd.DataFrame,
    available_dtes: tuple[int, ...],
    prev_close: float | None,
) -> DayContext:
    frame = stock.copy().reset_index(drop=True)
    frame["trade_date"] = pd.to_datetime(frame["trade_date"]).dt.date
    frame["timestamp_et"] = pd.to_datetime(frame["timestamp_et"])
    frame["qqq_open"] = frame["open"]
    frame["qqq_high"] = frame["high"]
    frame["qqq_low"] = frame["low"]
    frame["qqq_close"] = frame["close"]
    frame["qqq_volume"] = frame["volume"]
    frame["qqq_vwap"] = frame["vwap"]
    frame["cum_notional"] = (frame["vwap"].fillna(frame["close"]) * frame["volume"].fillna(0.0)).cumsum()
    frame["cum_volume"] = frame["volume"].fillna(0.0).cumsum()
    frame["intraday_vwap"] = frame["cum_notional"] / frame["cum_volume"].replace(0.0, pd.NA)
    frame["intraday_vwap"] = frame["intraday_vwap"].ffill().fillna(frame["close"])
    frame["ema_fast"] = frame["close"].ewm(span=15, adjust=False).mean()
    frame["ema_slow"] = frame["close"].ewm(span=60, adjust=False).mean()
    frame["minute_index"] = range(len(frame))

    first15_end = min(14, len(frame) - 1)
    first30_end = min(29, len(frame) - 1)
    day_open = float(frame.loc[0, "open"])
    opening_range_high = float(frame.loc[:first15_end, "high"].max())
    opening_range_low = float(frame.loc[:first15_end, "low"].min())
    first15_close = float(frame.loc[first15_end, "close"])
    first30_close = float(frame.loc[first30_end, "close"])
    first30_high = float(frame.loc[:first30_end, "high"].max())
    first30_low = float(frame.loc[:first30_end, "low"].min())
    trade_date = frame.loc[0, "trade_date"]
    return DayContext(
        trade_date=trade_date,
        frame=frame,
        available_dtes=available_dtes,
        day_open=day_open,
        prev_close=prev_close,
        opening_range_high=opening_range_high,
        opening_range_low=opening_range_low,
        first15_range_pct=(opening_range_high - opening_range_low) / day_open,
        first30_range_pct=(first30_high - first30_low) / day_open,
        ret_15_pct=(first15_close / day_open) - 1.0,
        ret_30_pct=(first30_close / day_open) - 1.0,
    )


def list_trade_dates(dataset_root: Path, start_date: str | None, end_date: str | None) -> list[str]:
    stock_root = dataset_root / STOCK_ROOT_REL
    option_root = dataset_root / OPTION_ROOT_REL
    stock_dates = {
        path.name.split("=", 1)[1]
        for path in stock_root.iterdir()
        if path.is_dir() and path.name.startswith("trade_date=")
    }
    option_dates = {
        path.name.split("=", 1)[1]
        for path in option_root.iterdir()
        if path.is_dir() and path.name.startswith("trade_date=")
    }
    dates = sorted(stock_dates & option_dates)
    if start_date:
        dates = [trade_date for trade_date in dates if trade_date >= start_date]
    if end_date:
        dates = [trade_date for trade_date in dates if trade_date <= end_date]
    return dates


def load_stock_day(dataset_root: Path, trade_date: str) -> pd.DataFrame:
    path = dataset_root / STOCK_ROOT_REL / f"trade_date={trade_date}" / "qqq_stock_1m.parquet"
    stock = pd.read_parquet(path).sort_values("timestamp_et").reset_index(drop=True)
    return stock


def load_option_day(dataset_root: Path, trade_date: str) -> pd.DataFrame:
    path = dataset_root / OPTION_ROOT_REL / f"trade_date={trade_date}" / "dense.parquet"
    options = pd.read_parquet(path).sort_values(
        ["timestamp_et", "dte_calendar", "option_type", "strike_price", "contract_symbol"]
    ).reset_index(drop=True)
    return options


def prepare_option_day(
    options: pd.DataFrame,
) -> tuple[tuple[int, ...], dict[tuple[int, int, str], pd.DataFrame], dict[str, pd.Series]]:
    frame = options.copy()
    frame["timestamp_et"] = pd.to_datetime(frame["timestamp_et"])
    # Keep option rows aligned to the stock signal minute even if the option universe
    # is filtered down and some timestamps disappear entirely from the option frame.
    frame["minute_index"] = (
        frame["timestamp_et"].dt.hour * 60 + frame["timestamp_et"].dt.minute - (9 * 60 + 30)
    ).astype(int)
    frame["exit_price"] = frame["option_close"].where(frame["option_close"].notna(), frame["option_close_ffill"])
    frame["dte_calendar"] = frame["dte_calendar"].astype(int)

    available_dtes = tuple(sorted(frame["dte_calendar"].dropna().astype(int).unique().tolist()))

    entryable = frame[
        (frame["has_trade_bar"] == True)
        & frame["option_close"].notna()
        & (frame["option_close"] > 0.0)
        & frame["calc_delta"].notna()
    ].copy()
    chain_groups = {
        (int(minute_index), int(dte), str(option_type)): group.reset_index(drop=True)
        for (minute_index, dte, option_type), group in entryable.groupby(
            ["minute_index", "dte_calendar", "option_type"],
            sort=False,
        )
    }

    priced = frame[frame["exit_price"].notna() & (frame["exit_price"] > 0.0)].copy()
    price_series_by_symbol: dict[str, pd.Series] = {}
    for symbol, group in priced.groupby("contract_symbol", sort=False):
        deduped = group.drop_duplicates(subset=["minute_index"], keep="last")
        price_series_by_symbol[str(symbol)] = deduped.set_index("minute_index")["exit_price"].astype(float)

    return available_dtes, chain_groups, price_series_by_symbol


def select_leg(
    chain_groups: dict[tuple[int, int, str], pd.DataFrame],
    minute_index: int,
    dte: int,
    leg: DeltaLegTemplate,
    used_symbols: set[str],
) -> dict[str, object] | None:
    chain = chain_groups.get((minute_index, dte, leg.option_type))
    if chain is None or chain.empty:
        return None

    eligible = chain[~chain["contract_symbol"].isin(used_symbols)].copy()
    eligible = eligible[
        (eligible["calc_delta"].abs() >= leg.min_abs_delta)
        & (eligible["calc_delta"].abs() <= leg.max_abs_delta)
    ].copy()
    if eligible.empty:
        return None

    eligible["delta_distance"] = (eligible["calc_delta"] - leg.target_delta).abs()
    eligible = eligible.sort_values(
        ["delta_distance", "option_trade_count", "option_volume"],
        ascending=[True, False, False],
    ).reset_index(drop=True)
    chosen = eligible.iloc[0]
    entry_price_raw = float(chosen["option_close"])
    entry_price_fill = buy_fill(entry_price_raw) if leg.side == "long" else sell_fill(entry_price_raw)
    return {
        "symbol": str(chosen["contract_symbol"]),
        "option_type": str(chosen["option_type"]),
        "side": leg.side,
        "target_delta": leg.target_delta,
        "entry_price_raw": entry_price_raw,
        "entry_price_fill": entry_price_fill,
        "strike_price": float(chosen["strike_price"]),
        "spot_price": float(chosen["underlying_close"]),
        "implied_vol": maybe_float(chosen["calc_iv"]),
        "delta": maybe_float(chosen["calc_delta"]),
        "gamma": maybe_float(chosen["calc_gamma"]),
        "theta_daily": maybe_float(chosen["calc_theta_daily"]),
        "vega_1pct": maybe_float(chosen["calc_vega_1pct"]),
        "rho_1pct": maybe_float(chosen["calc_rho_1pct"]),
        "dte": int(chosen["dte_calendar"]),
        "selection_method": None if pd.isna(chosen["selection_method"]) else str(chosen["selection_method"]),
        "calc_status": None if pd.isna(chosen["calc_status"]) else str(chosen["calc_status"]),
        "calc_quality_tier": None if pd.isna(chosen["calc_quality_tier"]) else str(chosen["calc_quality_tier"]),
        "entry_has_trade_bar": bool(chosen["has_trade_bar"]),
    }


def generate_trades_for_day(
    strategies: list[DeltaStrategy],
    ctx: DayContext,
    chain_groups: dict[tuple[int, int, str], pd.DataFrame],
    price_series_by_symbol: dict[str, pd.Series],
    regime: str,
) -> list[dict[str, object]]:
    trades: list[dict[str, object]] = []

    for strategy in strategies:
        dte = resolve_dte(available_dtes=ctx.available_dtes, mode=strategy.dte_mode)
        if dte is None:
            continue

        entry_idx = SIGNAL_DISPATCH[strategy.signal_name](ctx)
        if entry_idx is None:
            continue
        hard_exit_idx = min(strategy.hard_exit_minute, len(ctx.frame) - 1)
        if entry_idx >= hard_exit_idx:
            continue

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
                legs = []
                break
            used_symbols.add(str(selected["symbol"]))
            legs.append(selected)
        if not legs:
            continue

        symbol_paths: dict[str, pd.Series] = {}
        for leg in legs:
            series = price_series_by_symbol.get(str(leg["symbol"]))
            if series is None:
                symbol_paths = {}
                break
            symbol_paths[str(leg["symbol"])] = series
        if not symbol_paths:
            continue

        entry_cash_per_combo = open_cashflow(legs=legs, quantity=1)
        entry_commission_per_combo = COMMISSION_PER_CONTRACT * len(legs)
        exit_commission_per_combo = COMMISSION_PER_CONTRACT * len(legs)
        entry_net_premium = combo_entry_net_premium(legs)
        max_loss_per_combo, max_profit_per_combo = estimate_combo_bounds(
            legs=legs,
            entry_net_premium=entry_net_premium,
        )

        target_dollars = abs(entry_net_premium) * 100.0 * strategy.profit_target_multiple
        stop_dollars = abs(entry_net_premium) * 100.0 * strategy.stop_loss_multiple
        mark_to_market: dict[int, float] = {}
        exit_idx: int | None = None
        exit_reason = "time_exit"
        exit_cash_per_combo = 0.0
        net_pnl_per_combo = 0.0

        for idx in range(entry_idx + 1, hard_exit_idx + 1):
            current_prices: list[float] = []
            available = True
            for leg in legs:
                raw_price = symbol_paths[str(leg["symbol"])].get(idx)
                if raw_price is None or pd.isna(raw_price):
                    available = False
                    break
                current_prices.append(float(raw_price))
            if not available:
                continue

            current_exit_cash = close_cashflow(legs=legs, exit_prices_raw=current_prices, quantity=1)
            current_net_pnl = (
                entry_cash_per_combo
                + current_exit_cash
                - entry_commission_per_combo
                - exit_commission_per_combo
            )
            mark_to_market[idx] = current_exit_cash - exit_commission_per_combo

            if current_net_pnl >= target_dollars:
                exit_idx = idx
                exit_reason = "profit_target"
                exit_cash_per_combo = current_exit_cash
                net_pnl_per_combo = current_net_pnl
                break
            if current_net_pnl <= -stop_dollars:
                exit_idx = idx
                exit_reason = "stop_loss"
                exit_cash_per_combo = current_exit_cash
                net_pnl_per_combo = current_net_pnl
                break

            exit_idx = idx
            exit_cash_per_combo = current_exit_cash
            net_pnl_per_combo = current_net_pnl

        if exit_idx is None:
            continue

        entry_time = ctx.frame.loc[entry_idx, "timestamp_et"]
        exit_time = ctx.frame.loc[exit_idx, "timestamp_et"]
        trades.append(
            {
                "strategy": strategy.name,
                "family": strategy.family,
                "description": strategy.description,
                "trade_date": ctx.trade_date.isoformat(),
                "regime": regime,
                "dte": dte,
                "entry_minute": int(entry_idx),
                "exit_minute": int(exit_idx),
                "entry_time_et": entry_time.isoformat(),
                "exit_time_et": exit_time.isoformat(),
                "exit_reason": exit_reason,
                "entry_underlying": round(float(ctx.frame.loc[entry_idx, "qqq_close"]), 4),
                "exit_underlying": round(float(ctx.frame.loc[exit_idx, "qqq_close"]), 4),
                "entry_cash_per_combo": round(entry_cash_per_combo, 4),
                "exit_cash_per_combo": round(exit_cash_per_combo, 4),
                "entry_commission_per_combo": round(entry_commission_per_combo, 4),
                "exit_commission_per_combo": round(exit_commission_per_combo, 4),
                "net_pnl_per_combo": round(net_pnl_per_combo, 4),
                "max_loss_per_combo": round(max_loss_per_combo, 4),
                "max_profit_per_combo": round(max_profit_per_combo, 4),
                "return_on_risk_pct": round((net_pnl_per_combo / max_loss_per_combo) * 100.0, 4)
                if max_loss_per_combo > 0.0
                else 0.0,
                "holding_minutes": int(exit_idx - entry_idx),
                "legs_json": json.dumps(legs, sort_keys=True),
                "mark_to_market_json": json.dumps(mark_to_market, sort_keys=True),
            }
        )

    return trades


def filter_trades_for_selection(
    trades: pd.DataFrame,
    selected_bull: list[str],
    selected_bear: list[str],
) -> pd.DataFrame:
    allowed_pairs = {
        ("bull", strategy_name) for strategy_name in selected_bull
    } | {
        ("bear", strategy_name) for strategy_name in selected_bear
    }
    filtered = trades[
        [
            (row.regime, row.strategy) in allowed_pairs
            for row in trades.itertuples(index=False)
        ]
    ].copy()
    if not filtered.empty:
        filtered = filtered.sort_values(["trade_date", "entry_minute", "strategy"]).reset_index(drop=True)
    return filtered


def write_report(
    path: Path,
    dataset_root: Path,
    day_returns: pd.DataFrame,
    regime_summary: pd.DataFrame,
    selected_bull: list[str],
    selected_bear: list[str],
    portfolio_summary: dict[str, object],
    filtered_trades: pd.DataFrame,
    threshold: float,
    risk_cap: float,
) -> None:
    lines: list[str] = []
    lines.append("# QQQ Direct-Greeks Dataset Portfolio Backtest")
    lines.append("")
    lines.append(f"- Dataset root: `{dataset_root}`")
    if not day_returns.empty:
        lines.append(
            f"- Trading days tested: {len(day_returns)} from {day_returns['trade_date'].iloc[0]} through {day_returns['trade_date'].iloc[-1]}"
        )
    lines.append(f"- Regime threshold: bull >= +{threshold:.2f}% RTH return, bear <= -{threshold:.2f}%, otherwise choppy.")
    lines.append(f"- Shared starting equity: ${STARTING_EQUITY:,.0f}")
    lines.append(f"- Max concurrent open risk: {risk_cap * 100:.0f}% of current equity")
    lines.append("")
    lines.append("## Selected Strategies")
    lines.append("")
    lines.append(f"- Bull: {', '.join(f'`{name}`' for name in selected_bull) if selected_bull else 'none'}")
    lines.append(f"- Bear: {', '.join(f'`{name}`' for name in selected_bear) if selected_bear else 'none'}")
    lines.append("- Choppy: flat")
    lines.append("")
    lines.append("## Top Strategies By Regime")
    lines.append("")
    for regime in ["bull", "bear", "choppy"]:
        lines.append(f"### {regime.title()}")
        subset = regime_summary[regime_summary["regime"] == regime].head(3)
        if subset.empty:
            lines.append("- No qualifying trades.")
        else:
            for row in subset.itertuples(index=False):
                lines.append(
                    f"- `{row.strategy}`: {row.trade_count} trades, ${row.total_net_pnl_1x:.2f} total 1x PnL, {row.win_rate_pct:.1f}% win rate."
                )
        lines.append("")
    lines.append("## Portfolio Summary")
    lines.append("")
    lines.append(f"- Filtered candidate trades: {len(filtered_trades)}")
    lines.append(f"- Final equity: ${portfolio_summary['final_equity']:.2f}")
    lines.append(f"- Total return: {portfolio_summary['total_return_pct']:.2f}%")
    lines.append(f"- Trades executed: {portfolio_summary['trade_count']}")
    lines.append(f"- Win rate: {portfolio_summary['win_rate_pct']:.2f}%")
    lines.append(f"- Max drawdown: {portfolio_summary['max_drawdown_pct']:.2f}%")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = build_parser().parse_args()
    dataset_root = Path(args.dataset_root).resolve()
    config_path = Path(args.config_path).resolve()
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    config = json.loads(config_path.read_text(encoding="utf-8"))
    threshold = float(config["regime_threshold_pct"])
    risk_cap = float(config["risk_cap"])
    selected_bull = parse_selected_strategies(config.get("selected_bull"))
    selected_bear = parse_selected_strategies(config.get("selected_bear"))

    strategies = build_delta_strategies()
    strategy_map = {strategy.name: strategy for strategy in strategies}
    selected_strategy_names = sorted(set(selected_bull) | set(selected_bear))
    selected_strategies = [strategy_map[name] for name in selected_strategy_names]

    trade_dates = list_trade_dates(
        dataset_root=dataset_root,
        start_date=args.start_date,
        end_date=args.end_date,
    )
    if not trade_dates:
        raise RuntimeError("No overlapping stock and options trade dates were found for the requested range.")

    candidate_trade_rows: list[dict[str, object]] = []
    day_return_rows: list[dict[str, object]] = []
    prev_close: float | None = None

    for idx, trade_date in enumerate(trade_dates, start=1):
        stock = load_stock_day(dataset_root=dataset_root, trade_date=trade_date)
        options = load_option_day(dataset_root=dataset_root, trade_date=trade_date)
        if stock.empty or options.empty:
            continue

        available_dtes, chain_groups, price_series_by_symbol = prepare_option_day(options=options)
        if not available_dtes:
            prev_close = float(stock["close"].iloc[-1])
            continue

        ctx = build_context_from_stock(
            stock=stock,
            available_dtes=available_dtes,
            prev_close=prev_close,
        )
        day_open = float(stock["open"].iloc[0])
        day_close = float(stock["close"].iloc[-1])
        day_ret_pct = (day_close / day_open - 1.0) * 100.0
        regime = assign_regime(day_ret_pct=day_ret_pct, threshold=threshold)

        day_return_rows.append(
            {
                "trade_date": trade_date,
                "day_open": round(day_open, 4),
                "day_close": round(day_close, 4),
                "day_ret_pct": round(day_ret_pct, 4),
                "regime": regime,
                "available_dtes": json.dumps(list(available_dtes)),
                "session_minutes": int(len(stock)),
            }
        )
        candidate_trade_rows.extend(
            generate_trades_for_day(
                strategies=strategies,
                ctx=ctx,
                chain_groups=chain_groups,
                price_series_by_symbol=price_series_by_symbol,
                regime=regime,
            )
        )
        prev_close = day_close

        if idx % 25 == 0 or idx == len(trade_dates):
            print(f"Processed {idx}/{len(trade_dates)} days through {trade_date}", flush=True)

    candidate_trades = pd.DataFrame(candidate_trade_rows)
    if not candidate_trades.empty:
        candidate_trades = candidate_trades.sort_values(["trade_date", "entry_minute", "strategy"]).reset_index(drop=True)

    day_returns = pd.DataFrame(day_return_rows)
    regime_summary = summarize_regimes(candidate_trades) if not candidate_trades.empty else pd.DataFrame(
        columns=[
            "regime",
            "strategy",
            "family",
            "trade_count",
            "win_rate_pct",
            "total_net_pnl_1x",
            "avg_net_pnl_1x",
            "avg_return_on_risk_pct",
        ]
    )
    filtered_trades = filter_trades_for_selection(
        trades=candidate_trades,
        selected_bull=selected_bull,
        selected_bear=selected_bear,
    )
    portfolio_trades, equity_curve, portfolio_summary = run_portfolio_allocator(
        strategies=selected_strategies,
        trades_df=filtered_trades,
        portfolio_max_open_risk_fraction=risk_cap,
    )

    summary_payload = {
        "dataset_root": str(dataset_root),
        "config_path": str(config_path),
        "start_date": trade_dates[0],
        "end_date": trade_dates[-1],
        "trade_date_count": len(trade_dates),
        "regime_threshold_pct": threshold,
        "risk_cap": risk_cap,
        "selected_bull": selected_bull,
        "selected_bear": selected_bear,
        "candidate_trade_count": int(len(candidate_trades)),
        "filtered_trade_count": int(len(filtered_trades)),
        "day_regime_counts": day_returns["regime"].value_counts().sort_index().to_dict() if not day_returns.empty else {},
        **portfolio_summary,
    }

    candidate_trades.to_csv(output_dir / args.candidate_name, index=False)
    filtered_trades.to_csv(output_dir / args.filtered_candidates_name, index=False)
    regime_summary.to_csv(output_dir / args.regime_summary_name, index=False)
    day_returns.to_csv(output_dir / args.day_returns_name, index=False)
    portfolio_trades.to_csv(output_dir / args.portfolio_trades_name, index=False)
    equity_curve.to_csv(output_dir / args.equity_name, index=False)
    (output_dir / args.summary_name).write_text(json.dumps(summary_payload, indent=2), encoding="utf-8")
    write_report(
        path=output_dir / args.report_name,
        dataset_root=dataset_root,
        day_returns=day_returns,
        regime_summary=regime_summary,
        selected_bull=selected_bull,
        selected_bear=selected_bear,
        portfolio_summary=portfolio_summary,
        filtered_trades=filtered_trades,
        threshold=threshold,
        risk_cap=risk_cap,
    )

    print(
        json.dumps(
            {
                "candidate_trades_csv": str(output_dir / args.candidate_name),
                "filtered_candidates_csv": str(output_dir / args.filtered_candidates_name),
                "regime_summary_csv": str(output_dir / args.regime_summary_name),
                "day_returns_csv": str(output_dir / args.day_returns_name),
                "portfolio_trades_csv": str(output_dir / args.portfolio_trades_name),
                "portfolio_equity_curve_csv": str(output_dir / args.equity_name),
                "portfolio_summary_json": str(output_dir / args.summary_name),
                "report_md": str(output_dir / args.report_name),
                "candidate_trade_count": int(len(candidate_trades)),
                "filtered_trade_count": int(len(filtered_trades)),
                "portfolio_trade_count": int(len(portfolio_trades)),
                "portfolio_final_equity": portfolio_summary["final_equity"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
