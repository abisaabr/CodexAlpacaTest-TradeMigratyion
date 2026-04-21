from __future__ import annotations

import argparse
import json
import math
import time
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from statistics import NormalDist

import pandas as pd

from backtest_qqq_option_strategies import (
    COMMISSION_PER_CONTRACT,
    MINUTES_PER_RTH_SESSION,
    STARTING_EQUITY,
    SIGNAL_DISPATCH,
    build_day_contexts,
    buy_fill,
    close_cashflow,
    combo_entry_net_premium,
    estimate_combo_bounds,
    load_daily_universe,
    load_wide_data,
    open_cashflow,
    resolve_dte,
    sell_fill,
)


RISK_FREE_RATE = 0.04
PORTFOLIO_MAX_OPEN_RISK_FRACTION = 0.25
REGIME_THRESHOLD_PCT = 0.40
RTH_START_MINUTE = 9 * 60 + 30
RTH_END_MINUTE = 15 * 60 + 59
NORM = NormalDist()


@dataclass(frozen=True)
class DeltaLegTemplate:
    option_type: str
    side: str
    target_delta: float
    min_abs_delta: float = 0.05
    max_abs_delta: float = 0.95


@dataclass(frozen=True)
class DeltaStrategy:
    name: str
    family: str
    description: str
    dte_mode: str
    legs: tuple[DeltaLegTemplate, ...]
    signal_name: str
    hard_exit_minute: int
    risk_fraction: float
    max_contracts: int
    profit_target_multiple: float
    stop_loss_multiple: float


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Second-pass QQQ options backtest with Greeks, delta-targeted entries, and a shared portfolio allocator.")
    parser.add_argument("--output-dir", default="output")
    parser.add_argument("--wide-name", default="qqq_option_1min_wide_backtest.parquet")
    parser.add_argument("--dense-name", default="qqq_option_1min_dense.parquet")
    parser.add_argument("--daily-universe-name", default="qqq_option_daily_universe.parquet")
    parser.add_argument("--candidate-trades-name", default="qqq_delta_candidate_trades.csv")
    parser.add_argument("--regime-summary-name", default="qqq_delta_regime_summary.csv")
    parser.add_argument("--portfolio-trades-name", default="qqq_delta_portfolio_trades.csv")
    parser.add_argument("--portfolio-equity-name", default="qqq_delta_portfolio_equity_curve.csv")
    parser.add_argument("--portfolio-summary-name", default="qqq_delta_portfolio_summary.json")
    parser.add_argument("--report-name", default="qqq_delta_portfolio_report.md")
    return parser


DOWN_CHOPPY_ONLY_STRATEGY_NAMES = {
    "orb_long_put_same_day",
    "orb_long_put_same_day_d40",
    "orb_long_put_same_day_d60",
    "orb_long_put_next_expiry",
    "trend_long_put_next_expiry",
    "trend_long_put_next_expiry_d50",
    "trend_long_put_next_expiry_d70",
    "bear_put_spread_next_expiry",
    "bear_put_spread_next_expiry_tight",
    "bear_put_spread_next_expiry_wide",
    "bear_call_credit_spread_same_day",
    "bear_call_credit_spread_same_day_conservative",
    "bear_call_credit_spread_same_day_aggressive",
    "bear_call_credit_spread_next_expiry",
    "bear_call_credit_spread_next_expiry_conservative",
    "put_backspread_next_expiry",
    "put_backspread_next_expiry_aggressive",
    "broken_wing_put_butterfly_next_expiry",
    "long_straddle_same_day",
    "long_straddle_next_expiry",
    "long_strangle_same_day",
    "long_strangle_next_expiry",
    "iron_condor_same_day",
    "iron_condor_same_day_conservative",
    "iron_condor_same_day_aggressive",
    "iron_butterfly_same_day",
    "call_butterfly_same_day",
    "put_butterfly_same_day",
    "call_butterfly_same_day_conservative",
    "put_butterfly_same_day_conservative",
}

CANDIDATE_TRADE_COLUMNS = (
    "strategy",
    "family",
    "description",
    "trade_date",
    "regime",
    "dte",
    "entry_minute",
    "exit_minute",
    "entry_time_et",
    "exit_time_et",
    "exit_reason",
    "entry_underlying",
    "exit_underlying",
    "leg_count",
    "entry_raw_cash_per_combo",
    "entry_cash_per_combo",
    "exit_raw_cash_per_combo",
    "exit_cash_per_combo",
    "entry_raw_net_premium",
    "abs_entry_net_premium",
    "premium_bucket",
    "is_sub_015_premium",
    "is_sub_030_premium",
    "entry_commission_per_combo",
    "exit_commission_per_combo",
    "total_commission_per_combo",
    "entry_slippage_per_combo",
    "exit_slippage_per_combo",
    "total_slippage_per_combo",
    "total_friction_per_combo",
    "friction_pct_of_entry_premium",
    "gross_pnl_per_combo",
    "net_pnl_per_combo",
    "max_loss_per_combo",
    "max_profit_per_combo",
    "gross_return_on_risk_pct",
    "return_on_risk_pct",
    "holding_minutes",
    "legs_json",
    "mark_to_market_json",
)


def empty_candidate_trades_df() -> pd.DataFrame:
    return pd.DataFrame(columns=list(CANDIDATE_TRADE_COLUMNS))


def combo_entry_raw_net_premium(legs: list[dict[str, object]]) -> float:
    premium = 0.0
    for leg in legs:
        price = float(leg["entry_price_raw"])
        if leg["side"] == "long":
            premium += price
        else:
            premium -= price
    return premium


def raw_open_cashflow(legs: list[dict[str, object]], quantity: int = 1) -> float:
    total = 0.0
    for leg in legs:
        raw_price = float(leg["entry_price_raw"])
        if leg["side"] == "long":
            total -= raw_price * 100.0 * quantity
        else:
            total += raw_price * 100.0 * quantity
    return total


def raw_close_cashflow(legs: list[dict[str, object]], exit_prices_raw: list[float], quantity: int = 1) -> float:
    total = 0.0
    for leg, raw_price in zip(legs, exit_prices_raw):
        if leg["side"] == "long":
            total += float(raw_price) * 100.0 * quantity
        else:
            total -= float(raw_price) * 100.0 * quantity
    return total


def classify_premium_bucket(abs_entry_premium: float) -> str:
    if abs_entry_premium < 0.15:
        return "<0.15"
    if abs_entry_premium < 0.30:
        return "0.15-0.30"
    if abs_entry_premium < 0.60:
        return "0.30-0.60"
    if abs_entry_premium < 1.00:
        return "0.60-1.00"
    return "1.00+"


def build_delta_strategies(
    *,
    include_family_expansion: bool = False,
    strategy_set: str | None = None,
) -> list[DeltaStrategy]:
    if strategy_set is None:
        strategy_set = "family_expansion" if include_family_expansion else "standard"
    include_family_expansion = strategy_set in {"family_expansion", "down_choppy_only"}

    def make_strategy(
        *,
        name: str,
        family: str,
        description: str,
        dte_mode: str,
        legs: tuple[DeltaLegTemplate, ...],
        signal_name: str,
        hard_exit_minute: int,
        risk_fraction: float,
        max_contracts: int,
        profit_target_multiple: float,
        stop_loss_multiple: float,
    ) -> DeltaStrategy:
        return DeltaStrategy(
            name=name,
            family=family,
            description=description,
            dte_mode=dte_mode,
            legs=legs,
            signal_name=signal_name,
            hard_exit_minute=hard_exit_minute,
            risk_fraction=risk_fraction,
            max_contracts=max_contracts,
            profit_target_multiple=profit_target_multiple,
            stop_loss_multiple=stop_loss_multiple,
        )

    strategies = [
        make_strategy(
            name="orb_long_call_same_day",
            family="Single-leg long call",
            description="Buy the same-day call closest to +0.50 delta on an opening range breakout.",
            dte_mode="same_day",
            legs=(DeltaLegTemplate(option_type="call", side="long", target_delta=0.50),),
            signal_name="orb_call",
            hard_exit_minute=375,
            risk_fraction=0.05,
            max_contracts=8,
            profit_target_multiple=0.50,
            stop_loss_multiple=0.35,
        ),
        make_strategy(
            name="orb_long_put_same_day",
            family="Single-leg long put",
            description="Buy the same-day put closest to -0.50 delta on an opening range breakdown.",
            dte_mode="same_day",
            legs=(DeltaLegTemplate(option_type="put", side="long", target_delta=-0.50),),
            signal_name="orb_put",
            hard_exit_minute=375,
            risk_fraction=0.05,
            max_contracts=8,
            profit_target_multiple=0.50,
            stop_loss_multiple=0.35,
        ),
        make_strategy(
            name="trend_long_call_next_expiry",
            family="Single-leg long call",
            description="Buy the next-expiry call closest to +0.60 delta on upside trend continuation.",
            dte_mode="next_expiry",
            legs=(DeltaLegTemplate(option_type="call", side="long", target_delta=0.60),),
            signal_name="trend_call",
            hard_exit_minute=360,
            risk_fraction=0.05,
            max_contracts=6,
            profit_target_multiple=0.45,
            stop_loss_multiple=0.30,
        ),
        make_strategy(
            name="trend_long_put_next_expiry",
            family="Single-leg long put",
            description="Buy the next-expiry put closest to -0.60 delta on downside trend continuation.",
            dte_mode="next_expiry",
            legs=(DeltaLegTemplate(option_type="put", side="long", target_delta=-0.60),),
            signal_name="trend_put",
            hard_exit_minute=360,
            risk_fraction=0.05,
            max_contracts=6,
            profit_target_multiple=0.45,
            stop_loss_multiple=0.30,
        ),
        make_strategy(
            name="bull_call_spread_next_expiry",
            family="Debit call spread",
            description="Buy a next-expiry bull call spread targeting +0.55 and +0.30 deltas.",
            dte_mode="next_expiry",
            legs=(
                DeltaLegTemplate(option_type="call", side="long", target_delta=0.55),
                DeltaLegTemplate(option_type="call", side="short", target_delta=0.30),
            ),
            signal_name="trend_call",
            hard_exit_minute=360,
            risk_fraction=0.06,
            max_contracts=8,
            profit_target_multiple=0.40,
            stop_loss_multiple=0.28,
        ),
        make_strategy(
            name="bear_put_spread_next_expiry",
            family="Debit put spread",
            description="Buy a next-expiry bear put spread targeting -0.55 and -0.30 deltas.",
            dte_mode="next_expiry",
            legs=(
                DeltaLegTemplate(option_type="put", side="long", target_delta=-0.55),
                DeltaLegTemplate(option_type="put", side="short", target_delta=-0.30),
            ),
            signal_name="trend_put",
            hard_exit_minute=360,
            risk_fraction=0.06,
            max_contracts=8,
            profit_target_multiple=0.40,
            stop_loss_multiple=0.28,
        ),
        make_strategy(
            name="bull_put_credit_spread_same_day",
            family="Credit put spread",
            description="Sell a same-day bull put spread targeting -0.35 and -0.15 deltas.",
            dte_mode="same_day",
            legs=(
                DeltaLegTemplate(option_type="put", side="short", target_delta=-0.35),
                DeltaLegTemplate(option_type="put", side="long", target_delta=-0.15),
            ),
            signal_name="credit_bull",
            hard_exit_minute=380,
            risk_fraction=0.05,
            max_contracts=10,
            profit_target_multiple=0.50,
            stop_loss_multiple=1.00,
        ),
        make_strategy(
            name="bear_call_credit_spread_same_day",
            family="Credit call spread",
            description="Sell a same-day bear call spread targeting +0.35 and +0.15 deltas.",
            dte_mode="same_day",
            legs=(
                DeltaLegTemplate(option_type="call", side="short", target_delta=0.35),
                DeltaLegTemplate(option_type="call", side="long", target_delta=0.15),
            ),
            signal_name="credit_bear",
            hard_exit_minute=380,
            risk_fraction=0.05,
            max_contracts=10,
            profit_target_multiple=0.50,
            stop_loss_multiple=1.00,
        ),
        make_strategy(
            name="long_straddle_same_day",
            family="Long straddle",
            description="Buy a same-day straddle targeting +0.50 and -0.50 deltas.",
            dte_mode="same_day",
            legs=(
                DeltaLegTemplate(option_type="call", side="long", target_delta=0.50),
                DeltaLegTemplate(option_type="put", side="long", target_delta=-0.50),
            ),
            signal_name="long_straddle",
            hard_exit_minute=210,
            risk_fraction=0.04,
            max_contracts=5,
            profit_target_multiple=0.35,
            stop_loss_multiple=0.25,
        ),
        make_strategy(
            name="iron_condor_same_day",
            family="Iron condor",
            description="Sell a same-day iron condor targeting +/-0.25 shorts and +/-0.10 wings.",
            dte_mode="same_day",
            legs=(
                DeltaLegTemplate(option_type="call", side="short", target_delta=0.25),
                DeltaLegTemplate(option_type="call", side="long", target_delta=0.10),
                DeltaLegTemplate(option_type="put", side="short", target_delta=-0.25),
                DeltaLegTemplate(option_type="put", side="long", target_delta=-0.10),
            ),
            signal_name="iron_condor",
            hard_exit_minute=375,
            risk_fraction=0.04,
            max_contracts=6,
            profit_target_multiple=0.40,
            stop_loss_multiple=1.25,
        ),
    ]

    for delta in (0.40, 0.60):
        delta_label = f"{int(round(delta * 100)):02d}"
        strategies.append(
            make_strategy(
                name=f"orb_long_call_same_day_d{delta_label}",
                family="Single-leg long call",
                description=f"Buy the same-day call closest to +{delta:.2f} delta on an opening range breakout.",
                dte_mode="same_day",
                legs=(DeltaLegTemplate(option_type="call", side="long", target_delta=delta),),
                signal_name="orb_call",
                hard_exit_minute=375,
                risk_fraction=0.05,
                max_contracts=8,
                profit_target_multiple=0.50,
                stop_loss_multiple=0.35,
            )
        )
        strategies.append(
            make_strategy(
                name=f"orb_long_put_same_day_d{delta_label}",
                family="Single-leg long put",
                description=f"Buy the same-day put closest to -{delta:.2f} delta on an opening range breakdown.",
                dte_mode="same_day",
                legs=(DeltaLegTemplate(option_type="put", side="long", target_delta=-delta),),
                signal_name="orb_put",
                hard_exit_minute=375,
                risk_fraction=0.05,
                max_contracts=8,
                profit_target_multiple=0.50,
                stop_loss_multiple=0.35,
            )
        )

    strategies.extend(
        [
            make_strategy(
                name="orb_long_call_next_expiry",
                family="Single-leg long call",
                description="Buy the next-expiry call closest to +0.50 delta on an opening range breakout.",
                dte_mode="next_expiry",
                legs=(DeltaLegTemplate(option_type="call", side="long", target_delta=0.50),),
                signal_name="orb_call",
                hard_exit_minute=360,
                risk_fraction=0.05,
                max_contracts=6,
                profit_target_multiple=0.45,
                stop_loss_multiple=0.30,
            ),
            make_strategy(
                name="orb_long_put_next_expiry",
                family="Single-leg long put",
                description="Buy the next-expiry put closest to -0.50 delta on an opening range breakdown.",
                dte_mode="next_expiry",
                legs=(DeltaLegTemplate(option_type="put", side="long", target_delta=-0.50),),
                signal_name="orb_put",
                hard_exit_minute=360,
                risk_fraction=0.05,
                max_contracts=6,
                profit_target_multiple=0.45,
                stop_loss_multiple=0.30,
            ),
        ]
    )

    for delta in (0.50, 0.70):
        delta_label = f"{int(round(delta * 100)):02d}"
        strategies.append(
            make_strategy(
                name=f"trend_long_call_next_expiry_d{delta_label}",
                family="Single-leg long call",
                description=f"Buy the next-expiry call closest to +{delta:.2f} delta on upside trend continuation.",
                dte_mode="next_expiry",
                legs=(DeltaLegTemplate(option_type="call", side="long", target_delta=delta),),
                signal_name="trend_call",
                hard_exit_minute=360,
                risk_fraction=0.05,
                max_contracts=6,
                profit_target_multiple=0.45,
                stop_loss_multiple=0.30,
            )
        )
        strategies.append(
            make_strategy(
                name=f"trend_long_put_next_expiry_d{delta_label}",
                family="Single-leg long put",
                description=f"Buy the next-expiry put closest to -{delta:.2f} delta on downside trend continuation.",
                dte_mode="next_expiry",
                legs=(DeltaLegTemplate(option_type="put", side="long", target_delta=-delta),),
                signal_name="trend_put",
                hard_exit_minute=360,
                risk_fraction=0.05,
                max_contracts=6,
                profit_target_multiple=0.45,
                stop_loss_multiple=0.30,
            )
        )

    for suffix, long_delta, short_delta in (("tight", 0.50, 0.35), ("wide", 0.60, 0.20)):
        strategies.append(
            make_strategy(
                name=f"bull_call_spread_next_expiry_{suffix}",
                family="Debit call spread",
                description=f"Buy a next-expiry bull call spread targeting +{long_delta:.2f} and +{short_delta:.2f} deltas.",
                dte_mode="next_expiry",
                legs=(
                    DeltaLegTemplate(option_type="call", side="long", target_delta=long_delta),
                    DeltaLegTemplate(option_type="call", side="short", target_delta=short_delta),
                ),
                signal_name="trend_call",
                hard_exit_minute=360,
                risk_fraction=0.06,
                max_contracts=8,
                profit_target_multiple=0.40,
                stop_loss_multiple=0.28,
            )
        )
        strategies.append(
            make_strategy(
                name=f"bear_put_spread_next_expiry_{suffix}",
                family="Debit put spread",
                description=f"Buy a next-expiry bear put spread targeting -{long_delta:.2f} and -{short_delta:.2f} deltas.",
                dte_mode="next_expiry",
                legs=(
                    DeltaLegTemplate(option_type="put", side="long", target_delta=-long_delta),
                    DeltaLegTemplate(option_type="put", side="short", target_delta=-short_delta),
                ),
                signal_name="trend_put",
                hard_exit_minute=360,
                risk_fraction=0.06,
                max_contracts=8,
                profit_target_multiple=0.40,
                stop_loss_multiple=0.28,
            )
        )

    for suffix, short_delta, wing_delta in (("conservative", 0.25, 0.10), ("aggressive", 0.45, 0.20)):
        strategies.append(
            make_strategy(
                name=f"bull_put_credit_spread_same_day_{suffix}",
                family="Credit put spread",
                description=f"Sell a same-day bull put spread targeting -{short_delta:.2f} and -{wing_delta:.2f} deltas.",
                dte_mode="same_day",
                legs=(
                    DeltaLegTemplate(option_type="put", side="short", target_delta=-short_delta),
                    DeltaLegTemplate(option_type="put", side="long", target_delta=-wing_delta),
                ),
                signal_name="credit_bull",
                hard_exit_minute=380,
                risk_fraction=0.05,
                max_contracts=10,
                profit_target_multiple=0.50,
                stop_loss_multiple=1.00,
            )
        )
        strategies.append(
            make_strategy(
                name=f"bear_call_credit_spread_same_day_{suffix}",
                family="Credit call spread",
                description=f"Sell a same-day bear call spread targeting +{short_delta:.2f} and +{wing_delta:.2f} deltas.",
                dte_mode="same_day",
                legs=(
                    DeltaLegTemplate(option_type="call", side="short", target_delta=short_delta),
                    DeltaLegTemplate(option_type="call", side="long", target_delta=wing_delta),
                ),
                signal_name="credit_bear",
                hard_exit_minute=380,
                risk_fraction=0.05,
                max_contracts=10,
                profit_target_multiple=0.50,
                stop_loss_multiple=1.00,
            )
        )

    strategies.extend(
        [
            make_strategy(
                name="long_straddle_next_expiry",
                family="Long straddle",
                description="Buy a next-expiry straddle targeting +0.50 and -0.50 deltas.",
                dte_mode="next_expiry",
                legs=(
                    DeltaLegTemplate(option_type="call", side="long", target_delta=0.50),
                    DeltaLegTemplate(option_type="put", side="long", target_delta=-0.50),
                ),
                signal_name="long_straddle",
                hard_exit_minute=300,
                risk_fraction=0.04,
                max_contracts=4,
                profit_target_multiple=0.30,
                stop_loss_multiple=0.22,
            ),
            make_strategy(
                name="long_strangle_same_day",
                family="Long strangle",
                description="Buy a same-day strangle targeting +0.35 and -0.35 deltas.",
                dte_mode="same_day",
                legs=(
                    DeltaLegTemplate(option_type="call", side="long", target_delta=0.35),
                    DeltaLegTemplate(option_type="put", side="long", target_delta=-0.35),
                ),
                signal_name="long_straddle",
                hard_exit_minute=240,
                risk_fraction=0.04,
                max_contracts=5,
                profit_target_multiple=0.38,
                stop_loss_multiple=0.24,
            ),
            make_strategy(
                name="long_strangle_next_expiry",
                family="Long strangle",
                description="Buy a next-expiry strangle targeting +0.35 and -0.35 deltas.",
                dte_mode="next_expiry",
                legs=(
                    DeltaLegTemplate(option_type="call", side="long", target_delta=0.35),
                    DeltaLegTemplate(option_type="put", side="long", target_delta=-0.35),
                ),
                signal_name="long_straddle",
                hard_exit_minute=300,
                risk_fraction=0.04,
                max_contracts=4,
                profit_target_multiple=0.32,
                stop_loss_multiple=0.22,
            ),
        ]
    )

    for suffix, short_delta, wing_delta in (("conservative", 0.20, 0.08), ("aggressive", 0.30, 0.12)):
        strategies.append(
            make_strategy(
                name=f"iron_condor_same_day_{suffix}",
                family="Iron condor",
                description=f"Sell a same-day iron condor targeting +/-{short_delta:.2f} shorts and +/-{wing_delta:.2f} wings.",
                dte_mode="same_day",
                legs=(
                    DeltaLegTemplate(option_type="call", side="short", target_delta=short_delta),
                    DeltaLegTemplate(option_type="call", side="long", target_delta=wing_delta),
                    DeltaLegTemplate(option_type="put", side="short", target_delta=-short_delta),
                    DeltaLegTemplate(option_type="put", side="long", target_delta=-wing_delta),
                ),
                signal_name="iron_condor",
                hard_exit_minute=375,
                risk_fraction=0.04,
                max_contracts=6,
                profit_target_multiple=0.40,
                stop_loss_multiple=1.25,
            )
        )

    strategies.append(
        make_strategy(
            name="iron_butterfly_same_day",
            family="Iron butterfly",
            description="Sell a same-day iron butterfly targeting +/-0.50 shorts and +/-0.20 wings.",
            dte_mode="same_day",
            legs=(
                DeltaLegTemplate(option_type="call", side="short", target_delta=0.50),
                DeltaLegTemplate(option_type="call", side="long", target_delta=0.20),
                DeltaLegTemplate(option_type="put", side="short", target_delta=-0.50),
                DeltaLegTemplate(option_type="put", side="long", target_delta=-0.20),
            ),
            signal_name="iron_condor",
            hard_exit_minute=360,
            risk_fraction=0.04,
            max_contracts=5,
            profit_target_multiple=0.35,
            stop_loss_multiple=1.10,
        )
    )

    if include_family_expansion:
        strategies.extend(
            [
                make_strategy(
                    name="bull_put_credit_spread_next_expiry",
                    family="Credit put spread",
                    description="Sell a next-expiry bull put spread targeting -0.30 and -0.12 deltas.",
                    dte_mode="next_expiry",
                    legs=(
                        DeltaLegTemplate(option_type="put", side="short", target_delta=-0.30),
                        DeltaLegTemplate(option_type="put", side="long", target_delta=-0.12),
                    ),
                    signal_name="credit_bull",
                    hard_exit_minute=360,
                    risk_fraction=0.05,
                    max_contracts=8,
                    profit_target_multiple=0.45,
                    stop_loss_multiple=0.90,
                ),
                make_strategy(
                    name="bear_call_credit_spread_next_expiry",
                    family="Credit call spread",
                    description="Sell a next-expiry bear call spread targeting +0.30 and +0.12 deltas.",
                    dte_mode="next_expiry",
                    legs=(
                        DeltaLegTemplate(option_type="call", side="short", target_delta=0.30),
                        DeltaLegTemplate(option_type="call", side="long", target_delta=0.12),
                    ),
                    signal_name="credit_bear",
                    hard_exit_minute=360,
                    risk_fraction=0.05,
                    max_contracts=8,
                    profit_target_multiple=0.45,
                    stop_loss_multiple=0.90,
                ),
                make_strategy(
                    name="bull_put_credit_spread_next_expiry_conservative",
                    family="Credit put spread",
                    description="Sell a next-expiry conservative bull put spread targeting -0.22 and -0.10 deltas.",
                    dte_mode="next_expiry",
                    legs=(
                        DeltaLegTemplate(option_type="put", side="short", target_delta=-0.22),
                        DeltaLegTemplate(option_type="put", side="long", target_delta=-0.10),
                    ),
                    signal_name="credit_bull",
                    hard_exit_minute=360,
                    risk_fraction=0.05,
                    max_contracts=7,
                    profit_target_multiple=0.42,
                    stop_loss_multiple=0.85,
                ),
                make_strategy(
                    name="bear_call_credit_spread_next_expiry_conservative",
                    family="Credit call spread",
                    description="Sell a next-expiry conservative bear call spread targeting +0.22 and +0.10 deltas.",
                    dte_mode="next_expiry",
                    legs=(
                        DeltaLegTemplate(option_type="call", side="short", target_delta=0.22),
                        DeltaLegTemplate(option_type="call", side="long", target_delta=0.10),
                    ),
                    signal_name="credit_bear",
                    hard_exit_minute=360,
                    risk_fraction=0.05,
                    max_contracts=7,
                    profit_target_multiple=0.42,
                    stop_loss_multiple=0.85,
                ),
                make_strategy(
                    name="call_backspread_next_expiry",
                    family="Call backspread",
                    description="Buy a next-expiry call backspread with one short +0.35 call against two long +0.55 calls.",
                    dte_mode="next_expiry",
                    legs=(
                        DeltaLegTemplate(option_type="call", side="short", target_delta=0.35),
                        DeltaLegTemplate(option_type="call", side="long", target_delta=0.55),
                        DeltaLegTemplate(option_type="call", side="long", target_delta=0.55),
                    ),
                    signal_name="trend_call",
                    hard_exit_minute=360,
                    risk_fraction=0.04,
                    max_contracts=4,
                    profit_target_multiple=0.60,
                    stop_loss_multiple=0.28,
                ),
                make_strategy(
                    name="put_backspread_next_expiry",
                    family="Put backspread",
                    description="Buy a next-expiry put backspread with one short -0.35 put against two long -0.55 puts.",
                    dte_mode="next_expiry",
                    legs=(
                        DeltaLegTemplate(option_type="put", side="short", target_delta=-0.35),
                        DeltaLegTemplate(option_type="put", side="long", target_delta=-0.55),
                        DeltaLegTemplate(option_type="put", side="long", target_delta=-0.55),
                    ),
                    signal_name="trend_put",
                    hard_exit_minute=360,
                    risk_fraction=0.04,
                    max_contracts=4,
                    profit_target_multiple=0.60,
                    stop_loss_multiple=0.28,
                ),
                make_strategy(
                    name="call_backspread_next_expiry_aggressive",
                    family="Call backspread",
                    description="Buy an aggressive next-expiry call backspread with one short +0.25 call against two long +0.50 calls.",
                    dte_mode="next_expiry",
                    legs=(
                        DeltaLegTemplate(option_type="call", side="short", target_delta=0.25),
                        DeltaLegTemplate(option_type="call", side="long", target_delta=0.50),
                        DeltaLegTemplate(option_type="call", side="long", target_delta=0.50),
                    ),
                    signal_name="trend_call",
                    hard_exit_minute=360,
                    risk_fraction=0.04,
                    max_contracts=4,
                    profit_target_multiple=0.65,
                    stop_loss_multiple=0.30,
                ),
                make_strategy(
                    name="put_backspread_next_expiry_aggressive",
                    family="Put backspread",
                    description="Buy an aggressive next-expiry put backspread with one short -0.25 put against two long -0.50 puts.",
                    dte_mode="next_expiry",
                    legs=(
                        DeltaLegTemplate(option_type="put", side="short", target_delta=-0.25),
                        DeltaLegTemplate(option_type="put", side="long", target_delta=-0.50),
                        DeltaLegTemplate(option_type="put", side="long", target_delta=-0.50),
                    ),
                    signal_name="trend_put",
                    hard_exit_minute=360,
                    risk_fraction=0.04,
                    max_contracts=4,
                    profit_target_multiple=0.65,
                    stop_loss_multiple=0.30,
                ),
                make_strategy(
                    name="call_butterfly_same_day",
                    family="Call butterfly",
                    description="Sell a same-day call butterfly targeting +0.20, +0.35, and +0.50 deltas.",
                    dte_mode="same_day",
                    legs=(
                        DeltaLegTemplate(option_type="call", side="long", target_delta=0.20),
                        DeltaLegTemplate(option_type="call", side="short", target_delta=0.35),
                        DeltaLegTemplate(option_type="call", side="short", target_delta=0.35),
                        DeltaLegTemplate(option_type="call", side="long", target_delta=0.50),
                    ),
                    signal_name="iron_condor",
                    hard_exit_minute=360,
                    risk_fraction=0.04,
                    max_contracts=5,
                    profit_target_multiple=0.38,
                    stop_loss_multiple=0.95,
                ),
                make_strategy(
                    name="put_butterfly_same_day",
                    family="Put butterfly",
                    description="Sell a same-day put butterfly targeting -0.20, -0.35, and -0.50 deltas.",
                    dte_mode="same_day",
                    legs=(
                        DeltaLegTemplate(option_type="put", side="long", target_delta=-0.20),
                        DeltaLegTemplate(option_type="put", side="short", target_delta=-0.35),
                        DeltaLegTemplate(option_type="put", side="short", target_delta=-0.35),
                        DeltaLegTemplate(option_type="put", side="long", target_delta=-0.50),
                    ),
                    signal_name="iron_condor",
                    hard_exit_minute=360,
                    risk_fraction=0.04,
                    max_contracts=5,
                    profit_target_multiple=0.38,
                    stop_loss_multiple=0.95,
                ),
                make_strategy(
                    name="call_butterfly_same_day_conservative",
                    family="Call butterfly",
                    description="Sell a conservative same-day call butterfly targeting +0.15, +0.28, and +0.42 deltas.",
                    dte_mode="same_day",
                    legs=(
                        DeltaLegTemplate(option_type="call", side="long", target_delta=0.15),
                        DeltaLegTemplate(option_type="call", side="short", target_delta=0.28),
                        DeltaLegTemplate(option_type="call", side="short", target_delta=0.28),
                        DeltaLegTemplate(option_type="call", side="long", target_delta=0.42),
                    ),
                    signal_name="iron_condor",
                    hard_exit_minute=360,
                    risk_fraction=0.04,
                    max_contracts=5,
                    profit_target_multiple=0.35,
                    stop_loss_multiple=0.90,
                ),
                make_strategy(
                    name="put_butterfly_same_day_conservative",
                    family="Put butterfly",
                    description="Sell a conservative same-day put butterfly targeting -0.15, -0.28, and -0.42 deltas.",
                    dte_mode="same_day",
                    legs=(
                        DeltaLegTemplate(option_type="put", side="long", target_delta=-0.15),
                        DeltaLegTemplate(option_type="put", side="short", target_delta=-0.28),
                        DeltaLegTemplate(option_type="put", side="short", target_delta=-0.28),
                        DeltaLegTemplate(option_type="put", side="long", target_delta=-0.42),
                    ),
                    signal_name="iron_condor",
                    hard_exit_minute=360,
                    risk_fraction=0.04,
                    max_contracts=5,
                    profit_target_multiple=0.35,
                    stop_loss_multiple=0.90,
                ),
                make_strategy(
                    name="broken_wing_call_butterfly_next_expiry",
                    family="Broken-wing call butterfly",
                    description="Trade a next-expiry broken-wing call butterfly targeting +0.15, +0.35, and +0.60 deltas.",
                    dte_mode="next_expiry",
                    legs=(
                        DeltaLegTemplate(option_type="call", side="long", target_delta=0.15),
                        DeltaLegTemplate(option_type="call", side="short", target_delta=0.35),
                        DeltaLegTemplate(option_type="call", side="short", target_delta=0.35),
                        DeltaLegTemplate(option_type="call", side="long", target_delta=0.60),
                    ),
                    signal_name="trend_call",
                    hard_exit_minute=360,
                    risk_fraction=0.04,
                    max_contracts=5,
                    profit_target_multiple=0.45,
                    stop_loss_multiple=0.55,
                ),
                make_strategy(
                    name="broken_wing_put_butterfly_next_expiry",
                    family="Broken-wing put butterfly",
                    description="Trade a next-expiry broken-wing put butterfly targeting -0.15, -0.35, and -0.60 deltas.",
                    dte_mode="next_expiry",
                    legs=(
                        DeltaLegTemplate(option_type="put", side="long", target_delta=-0.15),
                        DeltaLegTemplate(option_type="put", side="short", target_delta=-0.35),
                        DeltaLegTemplate(option_type="put", side="short", target_delta=-0.35),
                        DeltaLegTemplate(option_type="put", side="long", target_delta=-0.60),
                    ),
                    signal_name="trend_put",
                    hard_exit_minute=360,
                    risk_fraction=0.04,
                    max_contracts=5,
                    profit_target_multiple=0.45,
                    stop_loss_multiple=0.55,
                ),
            ]
        )

    if strategy_set == "down_choppy_exhaustive":
        strategies = [
            strategy for strategy in strategies if strategy.name in DOWN_CHOPPY_ONLY_STRATEGY_NAMES
        ]

        for delta in (0.35, 0.45, 0.55, 0.65):
            label = int(round(delta * 100))
            strategies.append(
                make_strategy(
                    name=f"orb_long_put_same_day_d{label}",
                    family="Single-leg long put",
                    description=f"Buy the same-day put closest to -{delta:.2f} delta on an opening range breakdown.",
                    dte_mode="same_day",
                    legs=(DeltaLegTemplate(option_type="put", side="long", target_delta=-delta),),
                    signal_name="orb_put",
                    hard_exit_minute=375,
                    risk_fraction=0.05,
                    max_contracts=8,
                    profit_target_multiple=0.50,
                    stop_loss_multiple=0.35,
                )
            )

        for delta in (0.40, 0.60):
            label = int(round(delta * 100))
            strategies.append(
                make_strategy(
                    name=f"orb_long_put_next_expiry_d{label}",
                    family="Single-leg long put",
                    description=f"Buy the next-expiry put closest to -{delta:.2f} delta on an opening range breakdown.",
                    dte_mode="next_expiry",
                    legs=(DeltaLegTemplate(option_type="put", side="long", target_delta=-delta),),
                    signal_name="orb_put",
                    hard_exit_minute=360,
                    risk_fraction=0.05,
                    max_contracts=6,
                    profit_target_multiple=0.45,
                    stop_loss_multiple=0.30,
                )
            )

        for delta in (0.45, 0.55, 0.65, 0.75):
            label = int(round(delta * 100))
            strategies.append(
                make_strategy(
                    name=f"trend_long_put_next_expiry_d{label}",
                    family="Single-leg long put",
                    description=f"Buy the next-expiry put closest to -{delta:.2f} delta on downside trend continuation.",
                    dte_mode="next_expiry",
                    legs=(DeltaLegTemplate(option_type="put", side="long", target_delta=-delta),),
                    signal_name="trend_put",
                    hard_exit_minute=360,
                    risk_fraction=0.05,
                    max_contracts=6,
                    profit_target_multiple=0.45,
                    stop_loss_multiple=0.30,
                )
            )

        for name, long_delta, short_delta in (
            ("bear_put_spread_next_expiry_d45_20", 0.45, 0.20),
            ("bear_put_spread_next_expiry_d50_25", 0.50, 0.25),
            ("bear_put_spread_next_expiry_d60_25", 0.60, 0.25),
            ("bear_put_spread_next_expiry_d65_35", 0.65, 0.35),
        ):
            strategies.append(
                make_strategy(
                    name=name,
                    family="Debit put spread",
                    description=f"Buy a next-expiry bear put spread targeting -{long_delta:.2f} and -{short_delta:.2f} deltas.",
                    dte_mode="next_expiry",
                    legs=(
                        DeltaLegTemplate(option_type="put", side="long", target_delta=-long_delta),
                        DeltaLegTemplate(option_type="put", side="short", target_delta=-short_delta),
                    ),
                    signal_name="trend_put",
                    hard_exit_minute=360,
                    risk_fraction=0.06,
                    max_contracts=8,
                    profit_target_multiple=0.40,
                    stop_loss_multiple=0.28,
                )
            )

        for name, short_delta, wing_delta, dte_mode in (
            ("bear_call_credit_spread_same_day_d18_08", 0.18, 0.08, "same_day"),
            ("bear_call_credit_spread_same_day_d22_10", 0.22, 0.10, "same_day"),
            ("bear_call_credit_spread_same_day_d26_12", 0.26, 0.12, "same_day"),
            ("bear_call_credit_spread_same_day_d30_15", 0.30, 0.15, "same_day"),
            ("bear_call_credit_spread_same_day_d40_20", 0.40, 0.20, "same_day"),
            ("bear_call_credit_spread_next_expiry_d18_08", 0.18, 0.08, "next_expiry"),
            ("bear_call_credit_spread_next_expiry_d26_12", 0.26, 0.12, "next_expiry"),
            ("bear_call_credit_spread_next_expiry_d34_15", 0.34, 0.15, "next_expiry"),
        ):
            strategies.append(
                make_strategy(
                    name=name,
                    family="Credit call spread",
                    description=f"Sell a {dte_mode.replace('_', '-')} bear call spread targeting +{short_delta:.2f} and +{wing_delta:.2f} deltas.",
                    dte_mode=dte_mode,
                    legs=(
                        DeltaLegTemplate(option_type="call", side="short", target_delta=short_delta),
                        DeltaLegTemplate(option_type="call", side="long", target_delta=wing_delta),
                    ),
                    signal_name="credit_bear",
                    hard_exit_minute=360 if dte_mode == "next_expiry" else 380,
                    risk_fraction=0.05,
                    max_contracts=8 if dte_mode == "next_expiry" else 10,
                    profit_target_multiple=0.45 if dte_mode == "next_expiry" else 0.50,
                    stop_loss_multiple=0.90 if dte_mode == "next_expiry" else 1.00,
                )
            )

        for name, short_delta, long_delta in (
            ("put_backspread_next_expiry_d20_45", 0.20, 0.45),
            ("put_backspread_next_expiry_d30_55", 0.30, 0.55),
            ("put_backspread_next_expiry_d40_65", 0.40, 0.65),
        ):
            strategies.append(
                make_strategy(
                    name=name,
                    family="Put backspread",
                    description=f"Buy a next-expiry put backspread with one short -{short_delta:.2f} put against two long -{long_delta:.2f} puts.",
                    dte_mode="next_expiry",
                    legs=(
                        DeltaLegTemplate(option_type="put", side="short", target_delta=-short_delta),
                        DeltaLegTemplate(option_type="put", side="long", target_delta=-long_delta),
                        DeltaLegTemplate(option_type="put", side="long", target_delta=-long_delta),
                    ),
                    signal_name="trend_put",
                    hard_exit_minute=360,
                    risk_fraction=0.04,
                    max_contracts=4,
                    profit_target_multiple=0.65,
                    stop_loss_multiple=0.30,
                )
            )

        for name, short_delta, wing_delta in (
            ("iron_condor_same_day_d15_06", 0.15, 0.06),
            ("iron_condor_same_day_d18_08", 0.18, 0.08),
            ("iron_condor_same_day_d30_12", 0.30, 0.12),
        ):
            strategies.append(
                make_strategy(
                    name=name,
                    family="Iron condor",
                    description=f"Sell a same-day iron condor targeting +/-{short_delta:.2f} shorts and +/-{wing_delta:.2f} wings.",
                    dte_mode="same_day",
                    legs=(
                        DeltaLegTemplate(option_type="call", side="short", target_delta=short_delta),
                        DeltaLegTemplate(option_type="call", side="long", target_delta=wing_delta),
                        DeltaLegTemplate(option_type="put", side="short", target_delta=-short_delta),
                        DeltaLegTemplate(option_type="put", side="long", target_delta=-wing_delta),
                    ),
                    signal_name="iron_condor",
                    hard_exit_minute=375,
                    risk_fraction=0.04,
                    max_contracts=6,
                    profit_target_multiple=0.40,
                    stop_loss_multiple=1.25,
                )
            )

        for name, short_delta, wing_delta in (
            ("iron_butterfly_same_day_d40_15", 0.40, 0.15),
            ("iron_butterfly_same_day_d60_25", 0.60, 0.25),
        ):
            strategies.append(
                make_strategy(
                    name=name,
                    family="Iron butterfly",
                    description=f"Sell a same-day iron butterfly targeting +/-{short_delta:.2f} shorts and +/-{wing_delta:.2f} wings.",
                    dte_mode="same_day",
                    legs=(
                        DeltaLegTemplate(option_type="call", side="short", target_delta=short_delta),
                        DeltaLegTemplate(option_type="call", side="long", target_delta=wing_delta),
                        DeltaLegTemplate(option_type="put", side="short", target_delta=-short_delta),
                        DeltaLegTemplate(option_type="put", side="long", target_delta=-wing_delta),
                    ),
                    signal_name="iron_condor",
                    hard_exit_minute=360,
                    risk_fraction=0.04,
                    max_contracts=5,
                    profit_target_multiple=0.35,
                    stop_loss_multiple=1.10,
                )
            )

        for name, family, left_delta, body_delta, right_delta in (
            ("call_butterfly_same_day_d12_24_36", "Call butterfly", 0.12, 0.24, 0.36),
            ("call_butterfly_same_day_d25_40_55", "Call butterfly", 0.25, 0.40, 0.55),
            ("put_butterfly_same_day_d12_24_36", "Put butterfly", -0.12, -0.24, -0.36),
            ("put_butterfly_same_day_d25_40_55", "Put butterfly", -0.25, -0.40, -0.55),
        ):
            option_type = "call" if family.startswith("Call") else "put"
            strategies.append(
                make_strategy(
                    name=name,
                    family=family,
                    description=f"Sell a same-day {family.lower()} targeting {left_delta:+.2f}, {body_delta:+.2f}, and {right_delta:+.2f} deltas.",
                    dte_mode="same_day",
                    legs=(
                        DeltaLegTemplate(option_type=option_type, side="long", target_delta=left_delta),
                        DeltaLegTemplate(option_type=option_type, side="short", target_delta=body_delta),
                        DeltaLegTemplate(option_type=option_type, side="short", target_delta=body_delta),
                        DeltaLegTemplate(option_type=option_type, side="long", target_delta=right_delta),
                    ),
                    signal_name="iron_condor",
                    hard_exit_minute=360,
                    risk_fraction=0.04,
                    max_contracts=5,
                    profit_target_multiple=0.36,
                    stop_loss_multiple=0.92,
                )
            )

        for name, family, left_delta, body_delta, right_delta, signal_name in (
            ("broken_wing_put_butterfly_next_expiry_d12_30_55", "Broken-wing put butterfly", -0.12, -0.30, -0.55, "trend_put"),
            ("broken_wing_put_butterfly_next_expiry_d18_40_65", "Broken-wing put butterfly", -0.18, -0.40, -0.65, "trend_put"),
            ("broken_wing_call_butterfly_next_expiry_d12_30_55", "Broken-wing call butterfly", 0.12, 0.30, 0.55, "trend_call"),
            ("broken_wing_call_butterfly_next_expiry_d18_40_65", "Broken-wing call butterfly", 0.18, 0.40, 0.65, "trend_call"),
        ):
            option_type = "put" if "put" in family.lower() else "call"
            strategies.append(
                make_strategy(
                    name=name,
                    family=family,
                    description=f"Trade a next-expiry {family.lower()} targeting {left_delta:+.2f}, {body_delta:+.2f}, and {right_delta:+.2f} deltas.",
                    dte_mode="next_expiry",
                    legs=(
                        DeltaLegTemplate(option_type=option_type, side="long", target_delta=left_delta),
                        DeltaLegTemplate(option_type=option_type, side="short", target_delta=body_delta),
                        DeltaLegTemplate(option_type=option_type, side="short", target_delta=body_delta),
                        DeltaLegTemplate(option_type=option_type, side="long", target_delta=right_delta),
                    ),
                    signal_name=signal_name,
                    hard_exit_minute=360,
                    risk_fraction=0.04,
                    max_contracts=5,
                    profit_target_multiple=0.45,
                    stop_loss_multiple=0.55,
                )
            )

        for name, dte_mode, call_delta, put_delta, profit_target, stop_loss in (
            ("long_straddle_same_day_d45", "same_day", 0.45, -0.45, 0.35, 0.25),
            ("long_straddle_same_day_d55", "same_day", 0.55, -0.55, 0.35, 0.25),
            ("long_straddle_next_expiry_d45", "next_expiry", 0.45, -0.45, 0.30, 0.22),
            ("long_strangle_same_day_d30", "same_day", 0.30, -0.30, 0.38, 0.24),
            ("long_strangle_same_day_d40", "same_day", 0.40, -0.40, 0.38, 0.24),
            ("long_strangle_next_expiry_d30", "next_expiry", 0.30, -0.30, 0.32, 0.22),
        ):
            family = "Long straddle" if "straddle" in name else "Long strangle"
            strategies.append(
                make_strategy(
                    name=name,
                    family=family,
                    description=f"Buy a {dte_mode.replace('_', '-')} {family.lower()} targeting {call_delta:+.2f} and {put_delta:+.2f} deltas.",
                    dte_mode=dte_mode,
                    legs=(
                        DeltaLegTemplate(option_type="call", side="long", target_delta=call_delta),
                        DeltaLegTemplate(option_type="put", side="long", target_delta=put_delta),
                    ),
                    signal_name="long_straddle",
                    hard_exit_minute=210 if dte_mode == "same_day" and family == "Long straddle" else (240 if dte_mode == "same_day" else 300),
                    risk_fraction=0.04,
                    max_contracts=5 if dte_mode == "same_day" else 4,
                    profit_target_multiple=profit_target,
                    stop_loss_multiple=stop_loss,
                )
            )

    if strategy_set == "down_choppy_only":
        strategies = [
            strategy for strategy in strategies if strategy.name in DOWN_CHOPPY_ONLY_STRATEGY_NAMES
        ]

    deduped: dict[str, DeltaStrategy] = {}
    for strategy in strategies:
        deduped[strategy.name] = strategy
    return list(deduped.values())


def norm_pdf(value: float) -> float:
    return math.exp(-0.5 * value * value) / math.sqrt(2.0 * math.pi)


def bs_price(spot: float, strike: float, years: float, rate: float, sigma: float, option_type: str) -> float:
    if years <= 0.0 or sigma <= 0.0:
        return max(spot - strike, 0.0) if option_type == "call" else max(strike - spot, 0.0)
    sqrt_t = math.sqrt(years)
    d1 = (math.log(spot / strike) + (rate + 0.5 * sigma * sigma) * years) / (sigma * sqrt_t)
    d2 = d1 - sigma * sqrt_t
    if option_type == "call":
        return spot * NORM.cdf(d1) - strike * math.exp(-rate * years) * NORM.cdf(d2)
    return strike * math.exp(-rate * years) * NORM.cdf(-d2) - spot * NORM.cdf(-d1)


def implied_volatility(spot: float, strike: float, years: float, rate: float, market_price: float, option_type: str) -> float | None:
    intrinsic = max(spot - strike, 0.0) if option_type == "call" else max(strike - spot, 0.0)
    target_price = max(market_price, intrinsic + 0.01)
    if years <= 0.0 or spot <= 0.0 or strike <= 0.0:
        return None

    low = 0.01
    high = 5.0
    low_price = bs_price(spot=spot, strike=strike, years=years, rate=rate, sigma=low, option_type=option_type)
    high_price = bs_price(spot=spot, strike=strike, years=years, rate=rate, sigma=high, option_type=option_type)
    if target_price < low_price - 1e-6 or target_price > high_price + 1e-6:
        return None

    for _ in range(60):
        mid = 0.5 * (low + high)
        price = bs_price(spot=spot, strike=strike, years=years, rate=rate, sigma=mid, option_type=option_type)
        if abs(price - target_price) <= 1e-4:
            return mid
        if price < target_price:
            low = mid
        else:
            high = mid
    return 0.5 * (low + high)


def bs_greeks(spot: float, strike: float, years: float, rate: float, sigma: float, option_type: str) -> dict[str, float]:
    if years <= 0.0 or sigma <= 0.0 or spot <= 0.0 or strike <= 0.0:
        delta = 1.0 if option_type == "call" and spot > strike else 0.0
        if option_type == "put":
            delta = -1.0 if spot < strike else 0.0
        return {"delta": delta, "gamma": 0.0, "theta": 0.0, "vega": 0.0}

    sqrt_t = math.sqrt(years)
    d1 = (math.log(spot / strike) + (rate + 0.5 * sigma * sigma) * years) / (sigma * sqrt_t)
    d2 = d1 - sigma * sqrt_t
    pdf_d1 = norm_pdf(d1)
    if option_type == "call":
        delta = NORM.cdf(d1)
        theta = (
            -(spot * pdf_d1 * sigma) / (2.0 * sqrt_t)
            - rate * strike * math.exp(-rate * years) * NORM.cdf(d2)
        ) / 365.0
    else:
        delta = NORM.cdf(d1) - 1.0
        theta = (
            -(spot * pdf_d1 * sigma) / (2.0 * sqrt_t)
            + rate * strike * math.exp(-rate * years) * NORM.cdf(-d2)
        ) / 365.0
    gamma = pdf_d1 / (spot * sigma * sqrt_t)
    vega = (spot * pdf_d1 * sqrt_t) / 100.0
    return {"delta": delta, "gamma": gamma, "theta": theta, "vega": vega}


def load_dense_data(path: Path, valid_trade_dates: set[date], wide: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    dense = pd.read_parquet(path).copy()
    dense["timestamp_et"] = pd.to_datetime(dense["timestamp_et"])
    dense["trade_date"] = pd.to_datetime(dense["trade_date"]).dt.date
    dense["expiration_date"] = pd.to_datetime(dense["expiration_date"]).dt.date
    minute_of_day = dense["timestamp_et"].dt.hour * 60 + dense["timestamp_et"].dt.minute
    dense = dense[dense["trade_date"].isin(valid_trade_dates)].copy()
    minute_of_day = dense["timestamp_et"].dt.hour * 60 + dense["timestamp_et"].dt.minute
    dense = dense[(minute_of_day >= RTH_START_MINUTE) & (minute_of_day <= RTH_END_MINUTE)].copy()
    dense["minute_index"] = minute_of_day.loc[dense.index] - RTH_START_MINUTE

    underlying = wide[["trade_date", "minute_index", "qqq_close"]].rename(columns={"qqq_close": "spot_price"})
    dense = dense.merge(underlying, on=["trade_date", "minute_index"], how="inner")
    expiry_ts = pd.to_datetime(dense["expiration_date"].astype(str) + " 16:00:00").dt.tz_localize("America/New_York")
    dense["years_to_expiry"] = ((expiry_ts - dense["timestamp_et"]).dt.total_seconds().clip(lower=60.0)) / (365.0 * 24.0 * 3600.0)
    dense = dense.sort_values(["trade_date", "symbol", "minute_index"]).reset_index(drop=True)

    chain_index = dense.set_index(["trade_date", "minute_index", "dte", "option_type"]).sort_index()
    price_index = dense.set_index(["trade_date", "symbol", "minute_index"]).sort_index()
    return chain_index, price_index


def build_regime_map(wide: pd.DataFrame) -> dict[date, str]:
    daily = (
        wide.groupby("trade_date")
        .agg(day_open=("qqq_open", "first"), day_close=("qqq_close", "last"))
        .reset_index()
    )
    daily["day_ret_pct"] = (daily["day_close"] / daily["day_open"] - 1.0) * 100.0
    regimes: dict[date, str] = {}
    for row in daily.itertuples(index=False):
        if row.day_ret_pct >= REGIME_THRESHOLD_PCT:
            regimes[row.trade_date] = "bull"
        elif row.day_ret_pct <= -REGIME_THRESHOLD_PCT:
            regimes[row.trade_date] = "bear"
        else:
            regimes[row.trade_date] = "choppy"
    return regimes


def chain_slice(
    chain_index: pd.DataFrame,
    trade_date: date,
    minute_index: int,
    dte: int,
    option_type: str,
) -> pd.DataFrame:
    try:
        frame = chain_index.loc[(trade_date, minute_index, dte, option_type)].reset_index()
    except KeyError:
        return pd.DataFrame()
    if isinstance(frame, pd.Series):
        frame = frame.to_frame().T
    return frame.copy()


def enrich_chain_with_greeks(chain: pd.DataFrame) -> pd.DataFrame:
    enriched_rows: list[dict[str, object]] = []
    for row in chain.itertuples(index=False):
        iv = implied_volatility(
            spot=float(row.spot_price),
            strike=float(row.strike_price),
            years=float(row.years_to_expiry),
            rate=RISK_FREE_RATE,
            market_price=float(row.close),
            option_type=str(row.option_type),
        )
        if iv is None:
            continue
        greeks = bs_greeks(
            spot=float(row.spot_price),
            strike=float(row.strike_price),
            years=float(row.years_to_expiry),
            rate=RISK_FREE_RATE,
            sigma=iv,
            option_type=str(row.option_type),
        )
        enriched_rows.append(
            {
                **row._asdict(),
                "implied_vol": iv,
                "delta": greeks["delta"],
                "gamma": greeks["gamma"],
                "theta": greeks["theta"],
                "vega": greeks["vega"],
            }
        )
    return pd.DataFrame(enriched_rows)


def select_leg(
    chain_index: pd.DataFrame,
    trade_date: date,
    minute_index: int,
    dte: int,
    leg: DeltaLegTemplate,
    used_symbols: set[str],
) -> dict[str, object] | None:
    chain = chain_slice(
        chain_index=chain_index,
        trade_date=trade_date,
        minute_index=minute_index,
        dte=dte,
        option_type=leg.option_type,
    )
    if chain.empty:
        return None

    chain = chain[(chain["has_trade_bar"] == True) & (chain["close"] > 0.0)].copy()
    chain = chain[~chain["symbol"].isin(used_symbols)].copy()
    if chain.empty:
        return None

    enriched = enrich_chain_with_greeks(chain=chain)
    if enriched.empty:
        return None

    enriched = enriched[(enriched["delta"].abs() >= leg.min_abs_delta) & (enriched["delta"].abs() <= leg.max_abs_delta)].copy()
    if enriched.empty:
        return None

    enriched["delta_distance"] = (enriched["delta"] - leg.target_delta).abs()
    enriched = enriched.sort_values(["delta_distance", "trade_count", "volume"], ascending=[True, False, False]).reset_index(drop=True)
    chosen = enriched.iloc[0]
    execution_context = {
        "trade_count": float(chosen["trade_count"]) if pd.notna(chosen["trade_count"]) else 0.0,
        "volume": float(chosen["volume"]) if pd.notna(chosen["volume"]) else 0.0,
        "has_trade_bar": bool(chosen["has_trade_bar"]),
        "is_synthetic_bar": bool(chosen["is_synthetic_bar"]),
        "session_has_any_trade": bool(chosen["session_has_any_trade"]),
        "minute_index": int(minute_index),
        "vwap": float(chosen["vwap"]) if pd.notna(chosen["vwap"]) else float(chosen["close"]),
    }
    fill_price = (
        buy_fill(float(chosen["close"]), context=execution_context)
        if leg.side == "long"
        else sell_fill(float(chosen["close"]), context=execution_context)
    )
    return {
        "symbol": str(chosen["symbol"]),
        "option_type": leg.option_type,
        "side": leg.side,
        "target_delta": leg.target_delta,
        "entry_price_raw": float(chosen["close"]),
        "entry_price_fill": fill_price,
        "strike_price": float(chosen["strike_price"]),
        "spot_price": float(chosen["spot_price"]),
        "implied_vol": float(chosen["implied_vol"]),
        "delta": float(chosen["delta"]),
        "gamma": float(chosen["gamma"]),
        "theta": float(chosen["theta"]),
        "vega": float(chosen["vega"]),
        "entry_trade_count": execution_context["trade_count"],
        "entry_volume": execution_context["volume"],
        "entry_has_trade_bar": execution_context["has_trade_bar"],
        "entry_is_synthetic_bar": execution_context["is_synthetic_bar"],
        "entry_session_has_any_trade": execution_context["session_has_any_trade"],
        "entry_vwap": execution_context["vwap"],
        "entry_minute_index": execution_context["minute_index"],
    }


def price_frame(price_index: pd.DataFrame, trade_date: date, symbol: str) -> pd.DataFrame | None:
    try:
        frame = price_index.loc[(trade_date, symbol)]
    except KeyError:
        return None
    if isinstance(frame, pd.Series):
        frame = frame.to_frame().T
    frame = frame.reset_index(drop=True)
    if "minute_index" not in frame.columns:
        return None
    frame = frame.sort_values("minute_index").reset_index(drop=True)
    return frame.set_index("minute_index", drop=False)


def generate_candidate_trades(
    strategies: list[DeltaStrategy],
    day_contexts: list,
    chain_index: pd.DataFrame,
    price_index: pd.DataFrame,
    regime_map: dict[date, str],
    progress_callback=None,
) -> pd.DataFrame:
    trades: list[dict[str, object]] = []
    started_at = time.perf_counter()

    for strategy_index, strategy in enumerate(strategies, start=1):
        trade_count_before = len(trades)
        for ctx in day_contexts:
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
                    chain_index=chain_index,
                    trade_date=ctx.trade_date,
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

            entry_cash_per_combo = open_cashflow(legs=legs, quantity=1)
            entry_raw_cash_per_combo = raw_open_cashflow(legs=legs, quantity=1)
            entry_commission_per_combo = COMMISSION_PER_CONTRACT * len(legs)
            exit_commission_per_combo = COMMISSION_PER_CONTRACT * len(legs)
            entry_net_premium = combo_entry_net_premium(legs)
            entry_raw_net_premium = combo_entry_raw_net_premium(legs)
            max_loss_per_combo, max_profit_per_combo = estimate_combo_bounds(legs=legs, entry_net_premium=entry_net_premium)

            symbol_frames: dict[str, pd.DataFrame] = {}
            for leg in legs:
                frame = price_frame(price_index=price_index, trade_date=ctx.trade_date, symbol=str(leg["symbol"]))
                if frame is None or frame.empty:
                    symbol_frames = {}
                    break
                symbol_frames[str(leg["symbol"])] = frame
            if not symbol_frames:
                continue

            target_dollars = abs(entry_net_premium) * 100.0 * strategy.profit_target_multiple
            stop_dollars = abs(entry_net_premium) * 100.0 * strategy.stop_loss_multiple
            mark_to_market: dict[int, float] = {}
            exit_idx: int | None = None
            exit_reason = "time_exit"
            exit_cash_per_combo = 0.0
            exit_raw_cash_per_combo = 0.0
            net_pnl_per_combo = 0.0
            exit_prices_raw: list[float] | None = None
            exit_contexts: list[dict[str, object]] | None = None

            for idx in range(entry_idx + 1, hard_exit_idx + 1):
                current_prices: list[float] = []
                current_exit_contexts: list[dict[str, object]] = []
                available = True
                for leg in legs:
                    symbol_frame = symbol_frames[str(leg["symbol"])]
                    if idx not in symbol_frame.index:
                        available = False
                        break
                    bar = symbol_frame.loc[idx]
                    if isinstance(bar, pd.DataFrame):
                        bar = bar.iloc[0]
                    raw_price = bar.get("close")
                    if pd.isna(raw_price):
                        available = False
                        break
                    current_prices.append(float(raw_price))
                    current_exit_contexts.append(
                        {
                            "trade_count": float(bar["trade_count"]) if pd.notna(bar.get("trade_count")) else 0.0,
                            "volume": float(bar["volume"]) if pd.notna(bar.get("volume")) else 0.0,
                            "has_trade_bar": bool(bar.get("has_trade_bar", False)),
                            "is_synthetic_bar": bool(bar.get("is_synthetic_bar", False)),
                            "session_has_any_trade": bool(bar.get("session_has_any_trade", False)),
                            "minute_index": int(idx),
                            "vwap": float(bar["vwap"]) if pd.notna(bar.get("vwap")) else float(raw_price),
                        }
                    )
                if not available:
                    continue

                current_exit_cash = close_cashflow(
                    legs=legs,
                    exit_prices_raw=current_prices,
                    quantity=1,
                    exit_contexts=current_exit_contexts,
                )
                current_exit_raw_cash = raw_close_cashflow(legs=legs, exit_prices_raw=current_prices, quantity=1)
                current_net_pnl = entry_cash_per_combo + current_exit_cash - entry_commission_per_combo - exit_commission_per_combo
                mark_to_market[idx] = current_exit_cash - exit_commission_per_combo

                if current_net_pnl >= target_dollars:
                    exit_idx = idx
                    exit_reason = "profit_target"
                    exit_cash_per_combo = current_exit_cash
                    exit_raw_cash_per_combo = current_exit_raw_cash
                    net_pnl_per_combo = current_net_pnl
                    exit_prices_raw = list(current_prices)
                    exit_contexts = list(current_exit_contexts)
                    break
                if current_net_pnl <= -stop_dollars:
                    exit_idx = idx
                    exit_reason = "stop_loss"
                    exit_cash_per_combo = current_exit_cash
                    exit_raw_cash_per_combo = current_exit_raw_cash
                    net_pnl_per_combo = current_net_pnl
                    exit_prices_raw = list(current_prices)
                    exit_contexts = list(current_exit_contexts)
                    break

                exit_idx = idx
                exit_cash_per_combo = current_exit_cash
                exit_raw_cash_per_combo = current_exit_raw_cash
                net_pnl_per_combo = current_net_pnl
                exit_prices_raw = list(current_prices)
                exit_contexts = list(current_exit_contexts)

            if exit_idx is None or exit_prices_raw is None or exit_contexts is None:
                continue

            entry_time = ctx.frame.loc[entry_idx, "timestamp_et"]
            exit_time = ctx.frame.loc[exit_idx, "timestamp_et"]
            abs_entry_net_premium = abs(entry_net_premium)
            entry_slippage_per_combo = abs(entry_cash_per_combo - entry_raw_cash_per_combo)
            exit_slippage_per_combo = abs(exit_cash_per_combo - exit_raw_cash_per_combo)
            total_slippage_per_combo = entry_slippage_per_combo + exit_slippage_per_combo
            total_commission_per_combo = entry_commission_per_combo + exit_commission_per_combo
            total_friction_per_combo = total_slippage_per_combo + total_commission_per_combo
            gross_pnl_per_combo = entry_raw_cash_per_combo + exit_raw_cash_per_combo
            friction_pct_of_entry_premium = (
                (total_friction_per_combo / (abs_entry_net_premium * 100.0)) * 100.0
                if abs_entry_net_premium > 0.0
                else 0.0
            )
            gross_return_on_risk_pct = (
                (gross_pnl_per_combo / max_loss_per_combo) * 100.0
                if max_loss_per_combo > 0
                else 0.0
            )
            leg_payload: list[dict[str, object]] = []
            for leg, exit_price_raw, exit_context in zip(legs, exit_prices_raw, exit_contexts):
                exit_fill = (
                    sell_fill(float(exit_price_raw), context=exit_context)
                    if leg["side"] == "long"
                    else buy_fill(float(exit_price_raw), context=exit_context)
                )
                leg_payload.append(
                    {
                        **leg,
                        "entry_price_raw": round(float(leg["entry_price_raw"]), 4),
                        "entry_price_fill": round(float(leg["entry_price_fill"]), 4),
                        "exit_price_raw": round(float(exit_price_raw), 4),
                        "exit_price_fill": round(float(exit_fill), 4),
                        "exit_trade_count": round(float(exit_context["trade_count"]), 4),
                        "exit_volume": round(float(exit_context["volume"]), 4),
                        "exit_has_trade_bar": bool(exit_context["has_trade_bar"]),
                        "exit_is_synthetic_bar": bool(exit_context["is_synthetic_bar"]),
                        "exit_session_has_any_trade": bool(exit_context["session_has_any_trade"]),
                        "exit_vwap": round(float(exit_context["vwap"]), 4),
                        "exit_minute_index": int(exit_context["minute_index"]),
                    }
                )
            trades.append(
                {
                    "strategy": strategy.name,
                    "family": strategy.family,
                    "description": strategy.description,
                    "trade_date": ctx.trade_date.isoformat(),
                    "regime": regime_map[ctx.trade_date],
                    "dte": dte,
                    "entry_minute": int(entry_idx),
                    "exit_minute": int(exit_idx),
                    "entry_time_et": entry_time.isoformat(),
                    "exit_time_et": exit_time.isoformat(),
                    "exit_reason": exit_reason,
                    "entry_underlying": round(float(ctx.frame.loc[entry_idx, "qqq_close"]), 4),
                    "exit_underlying": round(float(ctx.frame.loc[exit_idx, "qqq_close"]), 4),
                    "leg_count": len(legs),
                    "entry_raw_cash_per_combo": round(entry_raw_cash_per_combo, 4),
                    "entry_cash_per_combo": round(entry_cash_per_combo, 4),
                    "exit_raw_cash_per_combo": round(exit_raw_cash_per_combo, 4),
                    "exit_cash_per_combo": round(exit_cash_per_combo, 4),
                    "entry_raw_net_premium": round(entry_raw_net_premium, 4),
                    "abs_entry_net_premium": round(abs_entry_net_premium, 4),
                    "premium_bucket": classify_premium_bucket(abs_entry_net_premium),
                    "is_sub_015_premium": abs_entry_net_premium < 0.15,
                    "is_sub_030_premium": abs_entry_net_premium < 0.30,
                    "entry_commission_per_combo": round(entry_commission_per_combo, 4),
                    "exit_commission_per_combo": round(exit_commission_per_combo, 4),
                    "total_commission_per_combo": round(total_commission_per_combo, 4),
                    "entry_slippage_per_combo": round(entry_slippage_per_combo, 4),
                    "exit_slippage_per_combo": round(exit_slippage_per_combo, 4),
                    "total_slippage_per_combo": round(total_slippage_per_combo, 4),
                    "total_friction_per_combo": round(total_friction_per_combo, 4),
                    "friction_pct_of_entry_premium": round(friction_pct_of_entry_premium, 4),
                    "gross_pnl_per_combo": round(gross_pnl_per_combo, 4),
                    "net_pnl_per_combo": round(net_pnl_per_combo, 4),
                    "max_loss_per_combo": round(max_loss_per_combo, 4),
                    "max_profit_per_combo": round(max_profit_per_combo, 4),
                    "gross_return_on_risk_pct": round(gross_return_on_risk_pct, 4),
                    "return_on_risk_pct": round((net_pnl_per_combo / max_loss_per_combo) * 100.0, 4) if max_loss_per_combo > 0 else 0.0,
                    "holding_minutes": int(exit_idx - entry_idx),
                    "legs_json": json.dumps(leg_payload, sort_keys=True),
                    "mark_to_market_json": json.dumps(mark_to_market, sort_keys=True),
                }
            )
        if progress_callback is not None:
            progress_callback(
                {
                    "strategy_index": strategy_index,
                    "strategy_count": len(strategies),
                    "strategy_name": strategy.name,
                    "trade_count": len(trades),
                    "new_trade_count": len(trades) - trade_count_before,
                    "elapsed_seconds": time.perf_counter() - started_at,
                }
            )

    trades_df = pd.DataFrame(trades, columns=list(CANDIDATE_TRADE_COLUMNS))
    if not trades_df.empty:
        trades_df = trades_df.sort_values(["trade_date", "entry_minute", "strategy"]).reset_index(drop=True)
    return trades_df


def summarize_regimes(trades_df: pd.DataFrame) -> pd.DataFrame:
    if trades_df.empty:
        return pd.DataFrame(
            columns=[
                "regime",
                "strategy",
                "family",
                "trade_count",
                "win_rate_pct",
                "total_net_pnl_1x",
                "total_gross_pnl_1x",
                "total_friction_1x",
                "avg_net_pnl_1x",
                "avg_total_friction_1x",
                "avg_friction_pct_of_entry_premium",
                "avg_entry_premium",
                "median_entry_premium",
                "sub_015_trade_share_pct",
                "sub_030_trade_share_pct",
                "avg_return_on_risk_pct",
            ]
        )

    grouped = (
        trades_df.groupby(["regime", "strategy", "family"], as_index=False)
        .agg(
            trade_count=("net_pnl_per_combo", "size"),
            wins=("net_pnl_per_combo", lambda series: int((series > 0).sum())),
            total_net_pnl_1x=("net_pnl_per_combo", "sum"),
            total_gross_pnl_1x=("gross_pnl_per_combo", "sum"),
            total_friction_1x=("total_friction_per_combo", "sum"),
            avg_net_pnl_1x=("net_pnl_per_combo", "mean"),
            avg_total_friction_1x=("total_friction_per_combo", "mean"),
            avg_friction_pct_of_entry_premium=("friction_pct_of_entry_premium", "mean"),
            avg_entry_premium=("abs_entry_net_premium", "mean"),
            median_entry_premium=("abs_entry_net_premium", "median"),
            sub_015_trades=("is_sub_015_premium", "sum"),
            sub_030_trades=("is_sub_030_premium", "sum"),
            avg_return_on_risk_pct=("return_on_risk_pct", "mean"),
        )
    )
    grouped["win_rate_pct"] = (grouped["wins"] / grouped["trade_count"]) * 100.0
    grouped["sub_015_trade_share_pct"] = (grouped["sub_015_trades"] / grouped["trade_count"]) * 100.0
    grouped["sub_030_trade_share_pct"] = (grouped["sub_030_trades"] / grouped["trade_count"]) * 100.0
    grouped = grouped.drop(columns=["wins", "sub_015_trades", "sub_030_trades"])
    grouped = grouped.sort_values(["regime", "total_net_pnl_1x", "avg_return_on_risk_pct"], ascending=[True, False, False]).reset_index(drop=True)
    return grouped


def current_portfolio_equity(cash: float, open_positions: list[dict[str, object]], minute_index: int) -> float:
    equity = cash
    for position in open_positions:
        mtm = position["mark_to_market"].get(minute_index)
        if mtm is None:
            continue
        equity += float(mtm) * int(position["quantity"])
    return equity


def run_portfolio_allocator(
    strategies: list[DeltaStrategy],
    trades_df: pd.DataFrame,
    portfolio_max_open_risk_fraction: float = PORTFOLIO_MAX_OPEN_RISK_FRACTION,
    starting_equity: float = STARTING_EQUITY,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, object]]:
    strategy_map = {strategy.name: strategy for strategy in strategies}
    cash = starting_equity
    open_positions: list[dict[str, object]] = []
    portfolio_trades: list[dict[str, object]] = []
    equity_curve: list[dict[str, object]] = []

    if trades_df.empty:
        return empty_candidate_trades_df(), pd.DataFrame([{"trade_date": None, "minute_index": None, "equity": starting_equity}]), {
            "starting_equity": starting_equity,
            "final_equity": starting_equity,
            "total_return_pct": 0.0,
            "trade_count": 0,
            "win_rate_pct": 0.0,
            "max_drawdown_pct": 0.0,
            "portfolio_max_open_risk_fraction": portfolio_max_open_risk_fraction,
        }

    trades_df = trades_df.copy()
    trades_df["trade_date"] = pd.to_datetime(trades_df["trade_date"]).dt.date
    trades_by_day_minute = {
        key: frame.reset_index(drop=True)
        for key, frame in trades_df.groupby(["trade_date", "entry_minute"], sort=True)
    }
    ordered_days = sorted(trades_df["trade_date"].unique())

    for trade_date in ordered_days:
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
            reserved_risk = sum(float(position["max_loss_per_combo"]) * int(position["quantity"]) for position in open_positions)
            entries = trades_by_day_minute.get((trade_date, minute_index))
            if entries is not None:
                for row in entries.itertuples(index=False):
                    strategy = strategy_map[str(row.strategy)]
                    current_equity = current_portfolio_equity(cash=cash, open_positions=open_positions, minute_index=minute_index)
                    reserved_risk = sum(float(position["max_loss_per_combo"]) * int(position["quantity"]) for position in open_positions)
                    remaining_risk_capacity = max(0.0, current_equity * portfolio_max_open_risk_fraction - reserved_risk)
                    per_trade_risk_budget = current_equity * strategy.risk_fraction
                    allocatable_risk = min(per_trade_risk_budget, remaining_risk_capacity)

                    max_loss_per_combo = float(row.max_loss_per_combo)
                    if max_loss_per_combo <= 0.0:
                        continue
                    quantity_by_risk = math.floor(allocatable_risk / max_loss_per_combo)
                    if quantity_by_risk < 1:
                        continue

                    entry_outflow_per_combo = max(0.0, -(float(row.entry_cash_per_combo) - float(row.entry_commission_per_combo)))
                    if entry_outflow_per_combo > 0.0:
                        quantity_by_cash = math.floor(max(0.0, cash) / entry_outflow_per_combo)
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
                            "mark_to_market": {int(key): float(value) for key, value in json.loads(row.mark_to_market_json).items()},
                        }
                    )

            current_equity = current_portfolio_equity(cash=cash, open_positions=open_positions, minute_index=minute_index)
            equity_curve.append(
                {
                    "trade_date": trade_date.isoformat(),
                    "minute_index": minute_index,
                    "equity": round(current_equity, 4),
                    "cash": round(cash, 4),
                    "open_positions": len(open_positions),
                    "reserved_risk": round(sum(float(position["max_loss_per_combo"]) * int(position["quantity"]) for position in open_positions), 4),
                }
            )

        if open_positions:
            raise RuntimeError(f"open positions remained after end of day {trade_date}")

    portfolio_trades_df = pd.DataFrame(portfolio_trades)
    equity_curve_df = pd.DataFrame(equity_curve)
    if equity_curve_df.empty:
        final_equity = starting_equity
        max_drawdown_pct = 0.0
    else:
        final_equity = float(equity_curve_df["equity"].iloc[-1])
        peak = equity_curve_df["equity"].cummax()
        drawdown = (equity_curve_df["equity"] / peak) - 1.0
        max_drawdown_pct = float(drawdown.min()) * 100.0

    trade_count = int(len(portfolio_trades_df))
    win_rate_pct = (
        float((portfolio_trades_df["portfolio_net_pnl"] > 0).mean() * 100.0)
        if trade_count > 0
        else 0.0
    )
    summary = {
        "starting_equity": starting_equity,
        "final_equity": round(final_equity, 2),
        "total_return_pct": round(((final_equity / starting_equity) - 1.0) * 100.0, 2),
        "trade_count": trade_count,
        "win_rate_pct": round(win_rate_pct, 2),
        "max_drawdown_pct": round(max_drawdown_pct, 2),
        "portfolio_max_open_risk_fraction": portfolio_max_open_risk_fraction,
    }
    if trade_count > 0:
        contributions = (
            portfolio_trades_df.groupby("strategy", as_index=False)["portfolio_net_pnl"]
            .sum()
            .sort_values("portfolio_net_pnl", ascending=False)
        )
        summary["strategy_contributions"] = contributions.to_dict(orient="records")
    else:
        summary["strategy_contributions"] = []
    return portfolio_trades_df, equity_curve_df, summary


def write_report(path: Path, regime_summary: pd.DataFrame, portfolio_summary: dict[str, object]) -> None:
    lines: list[str] = []
    lines.append("# QQQ Delta-Targeted Greeks Portfolio Backtest")
    lines.append("")
    lines.append(f"- Regime split: bull if daily RTH return >= +{REGIME_THRESHOLD_PCT:.2f}%, bear if <= -{REGIME_THRESHOLD_PCT:.2f}%, otherwise choppy.")
    lines.append(f"- Shared starting equity: ${STARTING_EQUITY:,.0f}")
    lines.append(f"- Max concurrent open risk: {PORTFOLIO_MAX_OPEN_RISK_FRACTION * 100:.0f}% of current portfolio equity")
    lines.append(f"- Flat risk-free rate for Greeks: {RISK_FREE_RATE * 100:.2f}%")
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
    lines.append(f"- Final equity: ${portfolio_summary['final_equity']:.2f}")
    lines.append(f"- Total return: {portfolio_summary['total_return_pct']:.2f}%")
    lines.append(f"- Trades executed: {portfolio_summary['trade_count']}")
    lines.append(f"- Win rate: {portfolio_summary['win_rate_pct']:.2f}%")
    lines.append(f"- Max drawdown: {portfolio_summary['max_drawdown_pct']:.2f}%")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = build_parser().parse_args()
    output_dir = Path(args.output_dir).resolve()

    wide = load_wide_data(path=output_dir / args.wide_name)
    _, _, available_dtes = load_daily_universe(path=output_dir / args.daily_universe_name)
    day_contexts = build_day_contexts(wide=wide, available_dtes=available_dtes)
    valid_trade_dates = {ctx.trade_date for ctx in day_contexts}
    chain_index, price_index = load_dense_data(path=output_dir / args.dense_name, valid_trade_dates=valid_trade_dates, wide=wide)
    regime_map = build_regime_map(wide=wide)
    strategies = build_delta_strategies()

    candidate_trades_df = generate_candidate_trades(
        strategies=strategies,
        day_contexts=day_contexts,
        chain_index=chain_index,
        price_index=price_index,
        regime_map=regime_map,
    )
    regime_summary_df = summarize_regimes(candidate_trades_df)
    portfolio_trades_df, portfolio_equity_df, portfolio_summary = run_portfolio_allocator(
        strategies=strategies,
        trades_df=candidate_trades_df,
    )

    candidate_trades_df.to_csv(output_dir / args.candidate_trades_name, index=False)
    regime_summary_df.to_csv(output_dir / args.regime_summary_name, index=False)
    portfolio_trades_df.to_csv(output_dir / args.portfolio_trades_name, index=False)
    portfolio_equity_df.to_csv(output_dir / args.portfolio_equity_name, index=False)
    (output_dir / args.portfolio_summary_name).write_text(json.dumps(portfolio_summary, indent=2), encoding="utf-8")
    write_report(path=output_dir / args.report_name, regime_summary=regime_summary_df, portfolio_summary=portfolio_summary)

    print(
        json.dumps(
            {
                "candidate_trades_csv": str(output_dir / args.candidate_trades_name),
                "regime_summary_csv": str(output_dir / args.regime_summary_name),
                "portfolio_trades_csv": str(output_dir / args.portfolio_trades_name),
                "portfolio_equity_curve_csv": str(output_dir / args.portfolio_equity_name),
                "portfolio_summary_json": str(output_dir / args.portfolio_summary_name),
                "report_md": str(output_dir / args.report_name),
                "candidate_trade_count": int(len(candidate_trades_df)),
                "portfolio_trade_count": int(len(portfolio_trades_df)),
                "portfolio_final_equity": portfolio_summary["final_equity"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
