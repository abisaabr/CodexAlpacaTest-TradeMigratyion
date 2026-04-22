from __future__ import annotations

import argparse
import copy
import json
import math
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, Callable

import pandas as pd


STARTING_EQUITY = 25_000.0
COMMISSION_PER_CONTRACT = 0.65
SLIPPAGE_RATE = 0.01
MIN_SLIPPAGE = 0.02
MINUTES_PER_RTH_SESSION = 390
OPTION_CONTRACT_SHARE_EQUIVALENT = 100
ALPACA_OPTION_BROKER_COMMISSION_PER_CONTRACT = 0.0
ALPACA_OPTION_ORF_PER_CONTRACT = 0.02685
ALPACA_OPTION_OCC_CLEARING_PER_CONTRACT = 0.02
ALPACA_OPTION_OCC_CLEARING_CAP_PER_ORDER = 55.0
ALPACA_OPTION_CAT_FEE_PER_EQUIVALENT_SHARE = 0.000046
ALPACA_OPTION_CAT_FEE_PER_CONTRACT = (
    ALPACA_OPTION_CAT_FEE_PER_EQUIVALENT_SHARE * OPTION_CONTRACT_SHARE_EQUIVALENT
)
ALPACA_OPTION_TAF_PER_CONTRACT = 0.00279
ALPACA_OPTION_FEE_SCHEDULE_AS_OF = "2026-04-22"
PREMIUM_BUCKET_SLIPPAGE_MULTIPLIERS = {
    "<0.15": 2.4,
    "0.15-0.30": 1.8,
    "0.30-0.60": 1.35,
    "0.60-1.00": 1.10,
    "1.00+": 1.0,
}
EARLY_SESSION_MINUTES = 15
LATE_SESSION_MINUTES = 30
DEFAULT_EXECUTION_SLIPPAGE_CALIBRATION = {
    "enabled": False,
    "overall_execution_posture": "unavailable",
    "evidence_strength": "none",
    "entry_multiplier": 1.0,
    "exit_multiplier": 1.0,
    "source_path": None,
    "notes": ["Static slippage model; no live execution calibration overlay applied."],
}
EXECUTION_SLIPPAGE_CALIBRATION = copy.deepcopy(DEFAULT_EXECUTION_SLIPPAGE_CALIBRATION)


def step_label(step: int) -> str:
    sign = "p" if step >= 0 else "n"
    return f"{sign}{abs(int(step)):02d}"


def slot_label(dte: int, option_type: str, strike_step_distance: int) -> str:
    return f"dte{int(dte):02d}_{option_type}_step_{step_label(int(strike_step_distance))}"


def feature_column(dte: int, option_type: str, step: int, feature: str) -> str:
    return f"{slot_label(dte=dte, option_type=option_type, strike_step_distance=step)}_{feature}"


def classify_premium_bucket(price: float) -> str:
    if price < 0.15:
        return "<0.15"
    if price < 0.30:
        return "0.15-0.30"
    if price < 0.60:
        return "0.30-0.60"
    if price < 1.00:
        return "0.60-1.00"
    return "1.00+"


def get_execution_slippage_calibration() -> dict[str, object]:
    return copy.deepcopy(EXECUTION_SLIPPAGE_CALIBRATION)


def configure_execution_slippage_calibration(calibration_context: dict[str, object] | None = None) -> dict[str, object]:
    global EXECUTION_SLIPPAGE_CALIBRATION

    if not calibration_context or not bool(calibration_context.get("enabled")):
        EXECUTION_SLIPPAGE_CALIBRATION = copy.deepcopy(DEFAULT_EXECUTION_SLIPPAGE_CALIBRATION)
        return get_execution_slippage_calibration()

    policy = dict(calibration_context.get("policy", {}))
    flags = dict(calibration_context.get("flags", {}))
    notes: list[str] = []
    entry_multiplier = 1.0
    exit_multiplier = 1.0

    if calibration_context.get("overall_execution_posture") == "caution":
        entry_multiplier *= 1.03
        exit_multiplier *= 1.03
        notes.append("Applied a small global caution multiplier because live Alpaca execution posture is elevated.")
    if policy.get("entry_penalty_mode") == "raised":
        entry_multiplier *= 1.15
        notes.append("Raised entry-side slippage because the execution handoff requested stronger entry penalties.")
    if bool(flags.get("elevated_entry_friction")):
        entry_multiplier *= 1.08
        notes.append("Raised entry-side slippage because live fills show elevated adverse entry friction.")
    if bool(flags.get("high_guardrail_pressure")):
        entry_multiplier *= 1.05
        exit_multiplier *= 1.05
        notes.append("Raised both-side slippage modestly because live guardrail pressure has been elevated.")
    if bool(flags.get("sample_size_limited")):
        entry_multiplier *= 1.02
        exit_multiplier *= 1.02
        notes.append("Added a small conservatism buffer because the execution sample is still limited.")
    if policy.get("exit_model_posture") == "conservative_fallback" or bool(flags.get("exit_telemetry_gap")):
        exit_multiplier *= 1.12
        notes.append("Raised exit-side slippage because exit telemetry is incomplete and the handoff calls for conservative fallback.")

    source_path = None
    handoff_lineage = calibration_context.get("handoff_lineage")
    if isinstance(handoff_lineage, dict):
        source_path = handoff_lineage.get("path")

    EXECUTION_SLIPPAGE_CALIBRATION = {
        "enabled": True,
        "overall_execution_posture": calibration_context.get("overall_execution_posture", "unknown"),
        "evidence_strength": calibration_context.get("evidence_strength", "unknown"),
        "entry_multiplier": round(float(entry_multiplier), 4),
        "exit_multiplier": round(float(exit_multiplier), 4),
        "source_path": source_path,
        "notes": notes or ["Execution calibration enabled without additional slippage adjustments."],
    }
    return get_execution_slippage_calibration()


def estimate_execution_slippage(price: float, context: dict[str, object] | None = None) -> float:
    context = context or {}
    base_slippage = max(MIN_SLIPPAGE, price * SLIPPAGE_RATE)
    premium_multiplier = PREMIUM_BUCKET_SLIPPAGE_MULTIPLIERS[classify_premium_bucket(price)]

    trade_count = float(context.get("trade_count", 0.0) or 0.0)
    volume = float(context.get("volume", 0.0) or 0.0)
    has_trade_bar = bool(context.get("has_trade_bar", True))
    is_synthetic_bar = bool(context.get("is_synthetic_bar", False))
    session_has_any_trade = bool(context.get("session_has_any_trade", True))
    minute_index = int(context.get("minute_index", EARLY_SESSION_MINUTES))

    liquidity_multiplier = 1.0
    if trade_count <= 0:
        liquidity_multiplier *= 1.45
    elif trade_count <= 2:
        liquidity_multiplier *= 1.25
    elif trade_count >= 10:
        liquidity_multiplier *= 0.92
    if volume <= 0:
        liquidity_multiplier *= 1.35
    elif volume <= 10:
        liquidity_multiplier *= 1.15
    elif volume >= 100:
        liquidity_multiplier *= 0.95

    session_multiplier = 1.0
    if minute_index < EARLY_SESSION_MINUTES:
        session_multiplier *= 1.18
    elif minute_index >= MINUTES_PER_RTH_SESSION - LATE_SESSION_MINUTES:
        session_multiplier *= 1.12

    data_quality_multiplier = 1.0
    if not has_trade_bar:
        data_quality_multiplier *= 1.35
    if is_synthetic_bar:
        data_quality_multiplier *= 1.20
    if not session_has_any_trade:
        data_quality_multiplier *= 1.15
    execution_phase = str(context.get("execution_phase", "entry")).lower()
    calibration = EXECUTION_SLIPPAGE_CALIBRATION
    calibration_multiplier = (
        float(calibration.get("exit_multiplier", 1.0))
        if execution_phase.startswith("exit")
        else float(calibration.get("entry_multiplier", 1.0))
    )

    return (
        base_slippage
        * premium_multiplier
        * liquidity_multiplier
        * session_multiplier
        * data_quality_multiplier
        * calibration_multiplier
    )


def buy_fill(price: float, context: dict[str, object] | None = None) -> float:
    slippage = estimate_execution_slippage(price, context=context)
    return max(0.01, price + slippage)


def sell_fill(price: float, context: dict[str, object] | None = None) -> float:
    slippage = estimate_execution_slippage(price, context=context)
    return max(0.01, price - slippage)


def intrinsic_value(option_type: str, strike: float, spot: float) -> float:
    if option_type == "call":
        return max(spot - strike, 0.0)
    return max(strike - spot, 0.0)


@dataclass(frozen=True)
class LegTemplate:
    option_type: str
    step: int
    side: str


@dataclass(frozen=True)
class Strategy:
    name: str
    family: str
    description: str
    dte_mode: str
    legs: tuple[LegTemplate, ...]
    signal_name: str
    hard_exit_minute: int
    risk_fraction: float
    max_contracts: int
    profit_target_multiple: float
    stop_loss_multiple: float
    require_trade_bar_on_entry: bool = True


@dataclass
class DayContext:
    trade_date: date
    frame: pd.DataFrame
    available_dtes: tuple[int, ...]
    day_open: float
    prev_close: float | None
    opening_range_high: float
    opening_range_low: float
    first15_range_pct: float
    first30_range_pct: float
    ret_15_pct: float
    ret_30_pct: float


@dataclass(frozen=True)
class OptionFeeBreakdown:
    contract_count: int
    sell_contract_count: int
    broker_commission: float
    regulatory_fees: float
    orf_fee: float
    occ_clearing_fee: float
    cat_fee: float
    taf_fee: float
    total_fees: float


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Backtest QQQ option strategy families on the clean-room 1-minute dataset.")
    parser.add_argument("--output-dir", default="output")
    parser.add_argument("--wide-name", default="qqq_option_1min_wide_backtest.parquet")
    parser.add_argument("--daily-universe-name", default="qqq_option_daily_universe.parquet")
    parser.add_argument("--summary-name", default="qqq_strategy_backtest_summary.csv")
    parser.add_argument("--trades-name", default="qqq_strategy_backtest_trades.csv")
    parser.add_argument("--equity-name", default="qqq_strategy_backtest_equity_curve.csv")
    parser.add_argument("--report-name", default="qqq_strategy_backtest_report.md")
    parser.add_argument("--assumptions-name", default="qqq_strategy_backtest_assumptions.json")
    return parser


def estimate_alpaca_option_fee_components(
    *,
    contract_count: int,
    sell_contract_count: int,
) -> OptionFeeBreakdown:
    contract_count = max(0, int(contract_count))
    sell_contract_count = max(0, min(contract_count, int(sell_contract_count)))
    if contract_count == 0:
        return OptionFeeBreakdown(
            contract_count=0,
            sell_contract_count=0,
            broker_commission=0.0,
            regulatory_fees=0.0,
            orf_fee=0.0,
            occ_clearing_fee=0.0,
            cat_fee=0.0,
            taf_fee=0.0,
            total_fees=0.0,
        )

    broker_commission = contract_count * ALPACA_OPTION_BROKER_COMMISSION_PER_CONTRACT
    orf_fee = contract_count * ALPACA_OPTION_ORF_PER_CONTRACT
    occ_clearing_fee = min(
        contract_count * ALPACA_OPTION_OCC_CLEARING_PER_CONTRACT,
        ALPACA_OPTION_OCC_CLEARING_CAP_PER_ORDER,
    )
    cat_fee = contract_count * ALPACA_OPTION_CAT_FEE_PER_CONTRACT
    taf_fee = sell_contract_count * ALPACA_OPTION_TAF_PER_CONTRACT
    regulatory_fees = orf_fee + occ_clearing_fee + cat_fee + taf_fee
    return OptionFeeBreakdown(
        contract_count=contract_count,
        sell_contract_count=sell_contract_count,
        broker_commission=broker_commission,
        regulatory_fees=regulatory_fees,
        orf_fee=orf_fee,
        occ_clearing_fee=occ_clearing_fee,
        cat_fee=cat_fee,
        taf_fee=taf_fee,
        total_fees=broker_commission + regulatory_fees,
    )


def estimate_alpaca_option_order_fees(
    *,
    legs: list[dict[str, object]],
    quantity: int,
    closing: bool,
) -> OptionFeeBreakdown:
    quantity = max(0, int(quantity))
    if quantity == 0 or not legs:
        return estimate_alpaca_option_fee_components(contract_count=0, sell_contract_count=0)

    sell_leg_count = 0
    for leg in legs:
        side = str(leg.get("side", ""))
        is_sell = (side == "short" and not closing) or (side == "long" and closing)
        if is_sell:
            sell_leg_count += 1

    return estimate_alpaca_option_fee_components(
        contract_count=len(legs) * quantity,
        sell_contract_count=sell_leg_count * quantity,
    )


def load_wide_data(path: Path) -> pd.DataFrame:
    wide = pd.read_parquet(path).copy()
    wide["timestamp_et"] = pd.to_datetime(wide["timestamp_et"])
    wide["trade_date"] = pd.to_datetime(wide["trade_date"]).dt.date
    wide = wide.sort_values(["trade_date", "timestamp_et"]).reset_index(drop=True)
    wide["minute_index"] = wide.groupby("trade_date").cumcount()

    qqq_vwap = wide["qqq_vwap"].where(wide["qqq_vwap"].notna(), wide["qqq_close"])
    notional = qqq_vwap.fillna(wide["qqq_close"]).fillna(0.0) * wide["qqq_volume"].fillna(0.0)
    wide["cum_notional"] = notional.groupby(wide["trade_date"]).cumsum()
    wide["cum_volume"] = wide["qqq_volume"].fillna(0.0).groupby(wide["trade_date"]).cumsum()
    wide["intraday_vwap"] = wide["cum_notional"] / wide["cum_volume"].replace(0.0, pd.NA)
    wide["intraday_vwap"] = wide.groupby("trade_date")["intraday_vwap"].ffill().fillna(wide["qqq_close"])
    wide["ema_fast"] = wide.groupby("trade_date")["qqq_close"].transform(
        lambda series: series.ewm(span=15, adjust=False).mean()
    )
    wide["ema_slow"] = wide.groupby("trade_date")["qqq_close"].transform(
        lambda series: series.ewm(span=60, adjust=False).mean()
    )

    full_session_dates: list[date] = []
    for trade_date, frame in wide.groupby("trade_date", sort=True):
        if len(frame) != MINUTES_PER_RTH_SESSION:
            continue
        if frame["qqq_close"].isna().any():
            continue
        full_session_dates.append(trade_date)

    return wide[wide["trade_date"].isin(full_session_dates)].reset_index(drop=True)


def load_daily_universe(path: Path) -> tuple[pd.DataFrame, dict[tuple[date, int, str, int], dict[str, object]], dict[date, tuple[int, ...]]]:
    universe = pd.read_parquet(path).copy()
    universe["trade_date"] = pd.to_datetime(universe["trade_date"]).dt.date

    slot_metadata: dict[tuple[date, int, str, int], dict[str, object]] = {}
    for row in universe.itertuples(index=False):
        key = (row.trade_date, int(row.dte), row.option_type, int(row.strike_step_distance))
        slot_metadata[key] = {
            "symbol": row.symbol,
            "strike_price": float(row.strike_price),
            "spot_reference": float(row.spot_reference),
        }

    available_dtes = (
        universe.groupby("trade_date")["dte"]
        .apply(lambda series: tuple(sorted(int(value) for value in series.dropna().unique())))
        .to_dict()
    )
    return universe, slot_metadata, available_dtes


def build_day_contexts(
    wide: pd.DataFrame,
    available_dtes: dict[date, tuple[int, ...]],
) -> list[DayContext]:
    day_closes = wide.groupby("trade_date")["qqq_close"].last()
    previous_close_map = day_closes.shift(1).to_dict()
    contexts: list[DayContext] = []

    for trade_date, frame in wide.groupby("trade_date", sort=True):
        day_frame = frame.reset_index(drop=True).copy()
        day_open = float(day_frame.loc[0, "qqq_open"]) if pd.notna(day_frame.loc[0, "qqq_open"]) else float(day_frame.loc[0, "qqq_close"])
        opening_range_high = float(day_frame.loc[:14, "qqq_high"].max())
        opening_range_low = float(day_frame.loc[:14, "qqq_low"].min())
        first15_close = float(day_frame.loc[14, "qqq_close"])
        first30_close = float(day_frame.loc[29, "qqq_close"])
        first30_high = float(day_frame.loc[:29, "qqq_high"].max())
        first30_low = float(day_frame.loc[:29, "qqq_low"].min())
        contexts.append(
            DayContext(
                trade_date=trade_date,
                frame=day_frame,
                available_dtes=available_dtes.get(trade_date, tuple()),
                day_open=day_open,
                prev_close=previous_close_map.get(trade_date),
                opening_range_high=opening_range_high,
                opening_range_low=opening_range_low,
                first15_range_pct=(opening_range_high - opening_range_low) / day_open,
                first30_range_pct=(first30_high - first30_low) / day_open,
                ret_15_pct=(first15_close / day_open) - 1.0,
                ret_30_pct=(first30_close / day_open) - 1.0,
            )
        )

    return contexts


def resolve_dte(available_dtes: tuple[int, ...], mode: str) -> int | None:
    if mode == "same_day":
        return 0 if 0 in available_dtes else None
    if mode == "next_expiry":
        positive = [value for value in available_dtes if value > 0]
        return min(positive) if positive else None
    raise ValueError(f"unsupported dte mode: {mode}")


def entry_orb(ctx: DayContext, bullish: bool) -> int | None:
    search_end = min(120, len(ctx.frame) - 1)
    for idx in range(15, search_end + 1):
        row = ctx.frame.iloc[idx]
        if bullish:
            if (
                row["qqq_close"] > ctx.opening_range_high * 1.0002
                and row["qqq_close"] > row["intraday_vwap"]
                and row["ema_fast"] > row["ema_slow"]
            ):
                return idx
        else:
            if (
                row["qqq_close"] < ctx.opening_range_low * 0.9998
                and row["qqq_close"] < row["intraday_vwap"]
                and row["ema_fast"] < row["ema_slow"]
            ):
                return idx
    return None


def entry_trend(ctx: DayContext, bullish: bool) -> int | None:
    search_end = min(150, len(ctx.frame) - 1)
    for idx in range(45, search_end + 1):
        row = ctx.frame.iloc[idx]
        move_from_open = (row["qqq_close"] / ctx.day_open) - 1.0
        distance_from_vwap = (row["qqq_close"] / row["intraday_vwap"]) - 1.0
        if bullish:
            prev_close_ok = True if ctx.prev_close is None else row["qqq_close"] >= ctx.prev_close * 0.9995
            if (
                move_from_open >= 0.0015
                and distance_from_vwap >= 0.0007
                and row["ema_fast"] > row["ema_slow"]
                and prev_close_ok
            ):
                return idx
        else:
            prev_close_ok = True if ctx.prev_close is None else row["qqq_close"] <= ctx.prev_close * 1.0005
            if (
                move_from_open <= -0.0015
                and distance_from_vwap <= -0.0007
                and row["ema_fast"] < row["ema_slow"]
                and prev_close_ok
            ):
                return idx
    return None


def entry_credit(ctx: DayContext, bullish: bool) -> int | None:
    idx = 90
    if idx >= len(ctx.frame):
        return None
    row = ctx.frame.iloc[idx]
    if bullish:
        if (
            ctx.first30_range_pct <= 0.0085
            and row["qqq_close"] > row["intraday_vwap"]
            and row["ema_fast"] > row["ema_slow"]
            and row["qqq_close"] > ctx.day_open
        ):
            return idx
    else:
        if (
            ctx.first30_range_pct <= 0.0085
            and row["qqq_close"] < row["intraday_vwap"]
            and row["ema_fast"] < row["ema_slow"]
            and row["qqq_close"] < ctx.day_open
        ):
            return idx
    return None


def entry_long_straddle(ctx: DayContext) -> int | None:
    idx = 15
    if idx >= len(ctx.frame):
        return None
    if ctx.first15_range_pct >= 0.0055 or abs(ctx.ret_15_pct) >= 0.0035:
        return idx
    return None


def entry_iron_condor(ctx: DayContext) -> int | None:
    idx = 30
    if idx >= len(ctx.frame):
        return None
    row = ctx.frame.iloc[idx]
    close_to_vwap = abs((row["qqq_close"] / row["intraday_vwap"]) - 1.0)
    if ctx.first30_range_pct <= 0.0062 and abs(ctx.ret_30_pct) <= 0.0045 and close_to_vwap <= 0.0020:
        return idx
    return None


SIGNAL_DISPATCH: dict[str, Callable[[DayContext], int | None]] = {
    "orb_call": lambda ctx: entry_orb(ctx, bullish=True),
    "orb_put": lambda ctx: entry_orb(ctx, bullish=False),
    "trend_call": lambda ctx: entry_trend(ctx, bullish=True),
    "trend_put": lambda ctx: entry_trend(ctx, bullish=False),
    "credit_bull": lambda ctx: entry_credit(ctx, bullish=True),
    "credit_bear": lambda ctx: entry_credit(ctx, bullish=False),
    "long_straddle": entry_long_straddle,
    "iron_condor": entry_iron_condor,
}


def build_strategies() -> list[Strategy]:
    return [
        Strategy(
            name="orb_long_call_same_day",
            family="Single-leg long call",
            description="Buy the near-ATM same-day call on a 15-minute opening range breakout.",
            dte_mode="same_day",
            legs=(LegTemplate(option_type="call", step=0, side="long"),),
            signal_name="orb_call",
            hard_exit_minute=375,
            risk_fraction=0.05,
            max_contracts=8,
            profit_target_multiple=0.50,
            stop_loss_multiple=0.35,
        ),
        Strategy(
            name="orb_long_put_same_day",
            family="Single-leg long put",
            description="Buy the near-ATM same-day put on a 15-minute opening range breakdown.",
            dte_mode="same_day",
            legs=(LegTemplate(option_type="put", step=0, side="long"),),
            signal_name="orb_put",
            hard_exit_minute=375,
            risk_fraction=0.05,
            max_contracts=8,
            profit_target_multiple=0.50,
            stop_loss_multiple=0.35,
        ),
        Strategy(
            name="trend_long_call_next_expiry",
            family="Single-leg long call",
            description="Buy the slightly ITM next-expiry call when QQQ trends above VWAP after the open.",
            dte_mode="next_expiry",
            legs=(LegTemplate(option_type="call", step=-1, side="long"),),
            signal_name="trend_call",
            hard_exit_minute=360,
            risk_fraction=0.05,
            max_contracts=6,
            profit_target_multiple=0.45,
            stop_loss_multiple=0.30,
        ),
        Strategy(
            name="trend_long_put_next_expiry",
            family="Single-leg long put",
            description="Buy the slightly ITM next-expiry put when QQQ trends below VWAP after the open.",
            dte_mode="next_expiry",
            legs=(LegTemplate(option_type="put", step=1, side="long"),),
            signal_name="trend_put",
            hard_exit_minute=360,
            risk_fraction=0.05,
            max_contracts=6,
            profit_target_multiple=0.45,
            stop_loss_multiple=0.30,
        ),
        Strategy(
            name="bull_call_spread_next_expiry",
            family="Debit call spread",
            description="Buy the near-ATM next-expiry bull call spread on sustained upside trend.",
            dte_mode="next_expiry",
            legs=(
                LegTemplate(option_type="call", step=0, side="long"),
                LegTemplate(option_type="call", step=2, side="short"),
            ),
            signal_name="trend_call",
            hard_exit_minute=360,
            risk_fraction=0.06,
            max_contracts=8,
            profit_target_multiple=0.40,
            stop_loss_multiple=0.28,
        ),
        Strategy(
            name="bear_put_spread_next_expiry",
            family="Debit put spread",
            description="Buy the near-ATM next-expiry bear put spread on sustained downside trend.",
            dte_mode="next_expiry",
            legs=(
                LegTemplate(option_type="put", step=0, side="long"),
                LegTemplate(option_type="put", step=-2, side="short"),
            ),
            signal_name="trend_put",
            hard_exit_minute=360,
            risk_fraction=0.06,
            max_contracts=8,
            profit_target_multiple=0.40,
            stop_loss_multiple=0.28,
        ),
        Strategy(
            name="bull_put_credit_spread_same_day",
            family="Credit put spread",
            description="Sell the same-day bull put spread after the morning stabilizes above VWAP.",
            dte_mode="same_day",
            legs=(
                LegTemplate(option_type="put", step=-1, side="short"),
                LegTemplate(option_type="put", step=-3, side="long"),
            ),
            signal_name="credit_bull",
            hard_exit_minute=380,
            risk_fraction=0.05,
            max_contracts=10,
            profit_target_multiple=0.50,
            stop_loss_multiple=1.00,
        ),
        Strategy(
            name="bear_call_credit_spread_same_day",
            family="Credit call spread",
            description="Sell the same-day bear call spread after the morning stabilizes below VWAP.",
            dte_mode="same_day",
            legs=(
                LegTemplate(option_type="call", step=1, side="short"),
                LegTemplate(option_type="call", step=3, side="long"),
            ),
            signal_name="credit_bear",
            hard_exit_minute=380,
            risk_fraction=0.05,
            max_contracts=10,
            profit_target_multiple=0.50,
            stop_loss_multiple=1.00,
        ),
        Strategy(
            name="long_straddle_same_day",
            family="Long straddle",
            description="Buy the same-day ATM straddle on outsized opening-range volatility.",
            dte_mode="same_day",
            legs=(
                LegTemplate(option_type="call", step=0, side="long"),
                LegTemplate(option_type="put", step=0, side="long"),
            ),
            signal_name="long_straddle",
            hard_exit_minute=210,
            risk_fraction=0.04,
            max_contracts=5,
            profit_target_multiple=0.35,
            stop_loss_multiple=0.25,
        ),
        Strategy(
            name="iron_condor_same_day",
            family="Iron condor",
            description="Sell a same-day iron condor when the first 30 minutes are narrow and mean-reverting.",
            dte_mode="same_day",
            legs=(
                LegTemplate(option_type="call", step=2, side="short"),
                LegTemplate(option_type="call", step=4, side="long"),
                LegTemplate(option_type="put", step=-2, side="short"),
                LegTemplate(option_type="put", step=-4, side="long"),
            ),
            signal_name="iron_condor",
            hard_exit_minute=375,
            risk_fraction=0.04,
            max_contracts=6,
            profit_target_multiple=0.40,
            stop_loss_multiple=1.25,
        ),
    ]


def get_leg_entry_snapshot(
    ctx: DayContext,
    dte: int,
    leg: LegTemplate,
    entry_idx: int,
    slot_metadata: dict[tuple[date, int, str, int], dict[str, object]],
) -> dict[str, object] | None:
    close_col = feature_column(dte=dte, option_type=leg.option_type, step=leg.step, feature="close")
    trade_bar_col = feature_column(dte=dte, option_type=leg.option_type, step=leg.step, feature="has_trade_bar")
    synthetic_col = feature_column(dte=dte, option_type=leg.option_type, step=leg.step, feature="is_synthetic_bar")
    trade_count_col = feature_column(dte=dte, option_type=leg.option_type, step=leg.step, feature="trade_count")
    volume_col = feature_column(dte=dte, option_type=leg.option_type, step=leg.step, feature="volume")
    vwap_col = feature_column(dte=dte, option_type=leg.option_type, step=leg.step, feature="vwap")
    if close_col not in ctx.frame.columns or trade_bar_col not in ctx.frame.columns:
        return None
    close_price = ctx.frame.loc[entry_idx, close_col]
    has_trade_bar = ctx.frame.loc[entry_idx, trade_bar_col]
    if pd.isna(close_price):
        return None
    metadata = slot_metadata.get((ctx.trade_date, dte, leg.option_type, leg.step))
    if metadata is None:
        return None
    return {
        "option_type": leg.option_type,
        "step": leg.step,
        "side": leg.side,
        "close_col": close_col,
        "symbol": metadata["symbol"],
        "strike_price": float(metadata["strike_price"]),
        "spot_reference": float(metadata["spot_reference"]),
        "entry_price_raw": float(close_price),
        "entry_has_trade_bar": bool(has_trade_bar),
        "entry_is_synthetic_bar": bool(ctx.frame.loc[entry_idx, synthetic_col]) if synthetic_col in ctx.frame.columns else False,
        "entry_trade_count": float(ctx.frame.loc[entry_idx, trade_count_col]) if trade_count_col in ctx.frame.columns and pd.notna(ctx.frame.loc[entry_idx, trade_count_col]) else 0.0,
        "entry_volume": float(ctx.frame.loc[entry_idx, volume_col]) if volume_col in ctx.frame.columns and pd.notna(ctx.frame.loc[entry_idx, volume_col]) else 0.0,
        "entry_vwap": float(ctx.frame.loc[entry_idx, vwap_col]) if vwap_col in ctx.frame.columns and pd.notna(ctx.frame.loc[entry_idx, vwap_col]) else float(close_price),
        "entry_minute_index": int(entry_idx),
        "session_has_any_trade": bool(ctx.frame[trade_bar_col].fillna(False).any()),
    }


def open_cashflow(legs: list[dict[str, object]], quantity: int) -> float:
    total = 0.0
    for leg in legs:
        price = float(leg["entry_price_fill"])
        if leg["side"] == "long":
            total -= price * 100.0 * quantity
        else:
            total += price * 100.0 * quantity
    return total


def close_cashflow(
    legs: list[dict[str, object]],
    exit_prices_raw: list[float],
    quantity: int,
    exit_contexts: list[dict[str, object]] | None = None,
) -> float:
    total = 0.0
    if exit_contexts is None:
        exit_contexts = [None] * len(legs)
    for leg, raw_price, context in zip(legs, exit_prices_raw, exit_contexts):
        if leg["side"] == "long":
            total += sell_fill(raw_price, context=context) * 100.0 * quantity
        else:
            total -= buy_fill(raw_price, context=context) * 100.0 * quantity
    return total


def combo_entry_net_premium(legs: list[dict[str, object]]) -> float:
    premium = 0.0
    for leg in legs:
        price = float(leg["entry_price_fill"])
        if leg["side"] == "long":
            premium += price
        else:
            premium -= price
    return premium


def combo_payoff_at_expiry(legs: list[dict[str, object]], spot: float) -> float:
    payoff = 0.0
    for leg in legs:
        sign = 1.0 if leg["side"] == "long" else -1.0
        payoff += sign * intrinsic_value(option_type=str(leg["option_type"]), strike=float(leg["strike_price"]), spot=spot)
    return payoff


def estimate_combo_bounds(legs: list[dict[str, object]], entry_net_premium: float) -> tuple[float, float]:
    strikes = sorted({float(leg["strike_price"]) for leg in legs})
    if not strikes:
        max_loss = max(entry_net_premium, 0.01) * 100.0
        return max_loss, max_loss

    spread = max(1.0, strikes[-1] - strikes[0])
    scenario_points = [0.0, max(0.0, strikes[0] - spread * 4.0)]
    scenario_points.extend(strikes)
    scenario_points.append(strikes[-1] + spread * 4.0)

    pnl_values: list[float] = []
    for spot in scenario_points:
        payout = combo_payoff_at_expiry(legs=legs, spot=spot)
        pnl_values.append((payout - entry_net_premium) * 100.0)

    return max(0.01, -min(pnl_values)), max(pnl_values)


def simulate_strategy(
    strategy: Strategy,
    day_contexts: list[DayContext],
    slot_metadata: dict[tuple[date, int, str, int], dict[str, object]],
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, object]]:
    equity = STARTING_EQUITY
    trades: list[dict[str, object]] = []
    equity_curve: list[dict[str, object]] = []
    skipped_counts = {
        "missing_dte": 0,
        "no_signal": 0,
        "late_signal": 0,
        "missing_leg": 0,
        "synthetic_entry": 0,
        "sizing": 0,
        "missing_exit_prices": 0,
    }

    for ctx in day_contexts:
        dte = resolve_dte(available_dtes=ctx.available_dtes, mode=strategy.dte_mode)
        if dte is None:
            skipped_counts["missing_dte"] += 1
            equity_curve.append({"strategy": strategy.name, "trade_date": ctx.trade_date, "equity": equity})
            continue

        entry_idx = SIGNAL_DISPATCH[strategy.signal_name](ctx)
        if entry_idx is None:
            skipped_counts["no_signal"] += 1
            equity_curve.append({"strategy": strategy.name, "trade_date": ctx.trade_date, "equity": equity})
            continue

        hard_exit_idx = min(strategy.hard_exit_minute, len(ctx.frame) - 1)
        if entry_idx >= hard_exit_idx:
            skipped_counts["late_signal"] += 1
            equity_curve.append({"strategy": strategy.name, "trade_date": ctx.trade_date, "equity": equity})
            continue

        legs: list[dict[str, object]] = []
        for leg_template in strategy.legs:
            snapshot = get_leg_entry_snapshot(
                ctx=ctx,
                dte=dte,
                leg=leg_template,
                entry_idx=entry_idx,
                slot_metadata=slot_metadata,
            )
            if snapshot is None:
                skipped_counts["missing_leg"] += 1
                legs = []
                break
            if strategy.require_trade_bar_on_entry and not snapshot["entry_has_trade_bar"]:
                skipped_counts["synthetic_entry"] += 1
                legs = []
                break
            entry_execution_context = {
                "trade_count": snapshot.get("entry_trade_count", 0.0),
                "volume": snapshot.get("entry_volume", 0.0),
                "has_trade_bar": snapshot.get("entry_has_trade_bar", True),
                "is_synthetic_bar": snapshot.get("entry_is_synthetic_bar", False),
                "session_has_any_trade": snapshot.get("session_has_any_trade", True),
                "minute_index": snapshot.get("entry_minute_index", entry_idx),
                "execution_phase": "entry",
            }
            fill_price = (
                buy_fill(snapshot["entry_price_raw"], context=entry_execution_context)
                if snapshot["side"] == "long"
                else sell_fill(snapshot["entry_price_raw"], context=entry_execution_context)
            )
            snapshot["entry_price_fill"] = fill_price
            legs.append(snapshot)

        if not legs:
            equity_curve.append({"strategy": strategy.name, "trade_date": ctx.trade_date, "equity": equity})
            continue

        entry_net_premium = combo_entry_net_premium(legs)
        max_loss_per_combo, max_profit_per_combo = estimate_combo_bounds(legs=legs, entry_net_premium=entry_net_premium)
        if max_loss_per_combo <= 0.0:
            skipped_counts["sizing"] += 1
            equity_curve.append({"strategy": strategy.name, "trade_date": ctx.trade_date, "equity": equity})
            continue

        risk_budget = equity * strategy.risk_fraction
        quantity = min(strategy.max_contracts, math.floor(risk_budget / max_loss_per_combo))
        if quantity < 1:
            skipped_counts["sizing"] += 1
            equity_curve.append({"strategy": strategy.name, "trade_date": ctx.trade_date, "equity": equity})
            continue

        entry_cash = open_cashflow(legs=legs, quantity=quantity)
        entry_fee_breakdown = estimate_alpaca_option_order_fees(legs=legs, quantity=quantity, closing=False)
        exit_fee_breakdown = estimate_alpaca_option_order_fees(legs=legs, quantity=quantity, closing=True)
        fee_total = entry_fee_breakdown.total_fees + exit_fee_breakdown.total_fees
        target_dollars = abs(entry_net_premium) * 100.0 * quantity * strategy.profit_target_multiple
        stop_dollars = abs(entry_net_premium) * 100.0 * quantity * strategy.stop_loss_multiple

        exit_idx: int | None = None
        exit_reason = "time_exit"
        exit_prices_raw: list[float] | None = None
        exit_contexts: list[dict[str, object]] | None = None
        exit_cash = 0.0
        net_pnl = 0.0

        for idx in range(entry_idx + 1, hard_exit_idx + 1):
            current_prices: list[float] = []
            current_exit_contexts: list[dict[str, object]] = []
            all_available = True
            for leg in legs:
                raw_price = ctx.frame.loc[idx, str(leg["close_col"])]
                if pd.isna(raw_price):
                    all_available = False
                    break
                current_prices.append(float(raw_price))
                trade_bar_col = str(leg["close_col"]).replace("_close", "_has_trade_bar")
                synthetic_col = str(leg["close_col"]).replace("_close", "_is_synthetic_bar")
                trade_count_col = str(leg["close_col"]).replace("_close", "_trade_count")
                volume_col = str(leg["close_col"]).replace("_close", "_volume")
                vwap_col = str(leg["close_col"]).replace("_close", "_vwap")
                current_exit_contexts.append(
                    {
                        "trade_count": float(ctx.frame.loc[idx, trade_count_col]) if trade_count_col in ctx.frame.columns and pd.notna(ctx.frame.loc[idx, trade_count_col]) else 0.0,
                        "volume": float(ctx.frame.loc[idx, volume_col]) if volume_col in ctx.frame.columns and pd.notna(ctx.frame.loc[idx, volume_col]) else 0.0,
                        "has_trade_bar": bool(ctx.frame.loc[idx, trade_bar_col]) if trade_bar_col in ctx.frame.columns else True,
                        "is_synthetic_bar": bool(ctx.frame.loc[idx, synthetic_col]) if synthetic_col in ctx.frame.columns else False,
                        "session_has_any_trade": bool(ctx.frame[trade_bar_col].fillna(False).any()) if trade_bar_col in ctx.frame.columns else True,
                        "minute_index": int(idx),
                        "vwap": float(ctx.frame.loc[idx, vwap_col]) if vwap_col in ctx.frame.columns and pd.notna(ctx.frame.loc[idx, vwap_col]) else float(raw_price),
                        "execution_phase": "exit",
                    }
                )
            if not all_available:
                continue

            current_exit_cash = close_cashflow(
                legs=legs,
                exit_prices_raw=current_prices,
                quantity=quantity,
                exit_contexts=current_exit_contexts,
            )
            current_net_pnl = entry_cash + current_exit_cash - fee_total

            if current_net_pnl >= target_dollars:
                exit_idx = idx
                exit_reason = "profit_target"
                exit_prices_raw = current_prices
                exit_contexts = current_exit_contexts
                exit_cash = current_exit_cash
                net_pnl = current_net_pnl
                break

            if current_net_pnl <= -stop_dollars:
                exit_idx = idx
                exit_reason = "stop_loss"
                exit_prices_raw = current_prices
                exit_contexts = current_exit_contexts
                exit_cash = current_exit_cash
                net_pnl = current_net_pnl
                break

            exit_idx = idx
            exit_prices_raw = current_prices
            exit_contexts = current_exit_contexts
            exit_cash = current_exit_cash
            net_pnl = current_net_pnl

        if exit_idx is None or exit_prices_raw is None or exit_contexts is None:
            skipped_counts["missing_exit_prices"] += 1
            equity_curve.append({"strategy": strategy.name, "trade_date": ctx.trade_date, "equity": equity})
            continue

        equity_before = equity
        equity += net_pnl
        entry_timestamp = ctx.frame.loc[entry_idx, "timestamp_et"]
        exit_timestamp = ctx.frame.loc[exit_idx, "timestamp_et"]

        leg_strings: list[str] = []
        for leg, exit_price, exit_context in zip(legs, exit_prices_raw, exit_contexts):
            leg_strings.append(
                json.dumps(
                    {
                        "symbol": leg["symbol"],
                        "side": leg["side"],
                        "option_type": leg["option_type"],
                        "step": leg["step"],
                        "strike_price": leg["strike_price"],
                        "entry_price_raw": round(float(leg["entry_price_raw"]), 4),
                        "entry_price_fill": round(float(leg["entry_price_fill"]), 4),
                        "exit_price_raw": round(float(exit_price), 4),
                        "exit_price_fill": round(
                            float(
                                sell_fill(exit_price, context=exit_context)
                                if leg["side"] == "long"
                                else buy_fill(exit_price, context=exit_context)
                            ),
                            4,
                        ),
                    },
                    sort_keys=True,
                )
            )

        trades.append(
            {
                "strategy": strategy.name,
                "family": strategy.family,
                "description": strategy.description,
                "trade_date": ctx.trade_date.isoformat(),
                "dte": dte,
                "entry_time_et": entry_timestamp.isoformat(),
                "exit_time_et": exit_timestamp.isoformat(),
                "exit_reason": exit_reason,
                "quantity": quantity,
                "legs": " | ".join(leg_strings),
                "entry_underlying": round(float(ctx.frame.loc[entry_idx, "qqq_close"]), 4),
                "exit_underlying": round(float(ctx.frame.loc[exit_idx, "qqq_close"]), 4),
                "entry_net_premium": round(entry_net_premium, 4),
                "entry_cashflow": round(entry_cash, 2),
                "exit_cashflow": round(exit_cash, 2),
                "gross_pnl": round(entry_cash + exit_cash, 2),
                "entry_broker_commission": round(entry_fee_breakdown.broker_commission, 4),
                "exit_broker_commission": round(exit_fee_breakdown.broker_commission, 4),
                "broker_commission_total": round(
                    entry_fee_breakdown.broker_commission + exit_fee_breakdown.broker_commission,
                    4,
                ),
                "entry_regulatory_fees": round(entry_fee_breakdown.regulatory_fees, 4),
                "exit_regulatory_fees": round(exit_fee_breakdown.regulatory_fees, 4),
                "regulatory_fee_total": round(
                    entry_fee_breakdown.regulatory_fees + exit_fee_breakdown.regulatory_fees,
                    4,
                ),
                "entry_orf_fees": round(entry_fee_breakdown.orf_fee, 4),
                "exit_orf_fees": round(exit_fee_breakdown.orf_fee, 4),
                "orf_fee_total": round(entry_fee_breakdown.orf_fee + exit_fee_breakdown.orf_fee, 4),
                "entry_occ_clearing_fees": round(entry_fee_breakdown.occ_clearing_fee, 4),
                "exit_occ_clearing_fees": round(exit_fee_breakdown.occ_clearing_fee, 4),
                "occ_clearing_fee_total": round(
                    entry_fee_breakdown.occ_clearing_fee + exit_fee_breakdown.occ_clearing_fee,
                    4,
                ),
                "entry_cat_fees": round(entry_fee_breakdown.cat_fee, 4),
                "exit_cat_fees": round(exit_fee_breakdown.cat_fee, 4),
                "cat_fee_total": round(entry_fee_breakdown.cat_fee + exit_fee_breakdown.cat_fee, 4),
                "entry_taf_fees": round(entry_fee_breakdown.taf_fee, 4),
                "exit_taf_fees": round(exit_fee_breakdown.taf_fee, 4),
                "taf_fee_total": round(entry_fee_breakdown.taf_fee + exit_fee_breakdown.taf_fee, 4),
                "entry_total_fees": round(entry_fee_breakdown.total_fees, 4),
                "exit_total_fees": round(exit_fee_breakdown.total_fees, 4),
                "commission_total": round(fee_total, 2),
                "net_pnl": round(net_pnl, 2),
                "max_loss_per_combo": round(max_loss_per_combo, 2),
                "max_profit_per_combo": round(max_profit_per_combo, 2),
                "return_on_risk_pct": round((net_pnl / (max_loss_per_combo * quantity)) * 100.0, 2),
                "holding_minutes": int(exit_idx - entry_idx),
                "equity_before": round(equity_before, 2),
                "equity_after": round(equity, 2),
                "risk_budget": round(risk_budget, 2),
                "signal_name": strategy.signal_name,
                "entry_minute": int(entry_idx),
                "exit_minute": int(exit_idx),
            }
        )
        equity_curve.append({"strategy": strategy.name, "trade_date": ctx.trade_date, "equity": round(equity, 2)})

    trades_df = pd.DataFrame(trades)
    equity_df = pd.DataFrame(equity_curve)
    summary = summarize_strategy(strategy=strategy, trades_df=trades_df, equity_df=equity_df, skipped_counts=skipped_counts)
    return trades_df, equity_df, summary


def summarize_strategy(
    strategy: Strategy,
    trades_df: pd.DataFrame,
    equity_df: pd.DataFrame,
    skipped_counts: dict[str, int],
) -> dict[str, object]:
    trade_count = int(len(trades_df))
    final_equity = float(equity_df["equity"].iloc[-1]) if not equity_df.empty else STARTING_EQUITY
    total_return_pct = ((final_equity / STARTING_EQUITY) - 1.0) * 100.0

    if trade_count == 0:
        max_drawdown_pct = 0.0
        win_rate_pct = 0.0
        avg_trade_net = 0.0
        median_trade_net = 0.0
        gross_profit = 0.0
        gross_loss = 0.0
        profit_factor = 0.0
        best_trade = 0.0
        worst_trade = 0.0
        avg_hold = 0.0
        avg_return_on_risk = 0.0
    else:
        equity_peak = equity_df["equity"].cummax()
        drawdowns = (equity_df["equity"] / equity_peak) - 1.0
        max_drawdown_pct = float(drawdowns.min()) * 100.0
        wins = trades_df[trades_df["net_pnl"] > 0]
        losses = trades_df[trades_df["net_pnl"] < 0]
        win_rate_pct = (len(wins) / trade_count) * 100.0
        avg_trade_net = float(trades_df["net_pnl"].mean())
        median_trade_net = float(trades_df["net_pnl"].median())
        gross_profit = float(wins["net_pnl"].sum())
        gross_loss = float(losses["net_pnl"].sum())
        profit_factor = gross_profit / abs(gross_loss) if gross_loss < 0 else float("inf")
        best_trade = float(trades_df["net_pnl"].max())
        worst_trade = float(trades_df["net_pnl"].min())
        avg_hold = float(trades_df["holding_minutes"].mean())
        avg_return_on_risk = float(trades_df["return_on_risk_pct"].mean())

    summary = {
        "strategy": strategy.name,
        "family": strategy.family,
        "description": strategy.description,
        "trade_count": trade_count,
        "final_equity": round(final_equity, 2),
        "total_return_pct": round(total_return_pct, 2),
        "win_rate_pct": round(win_rate_pct, 2),
        "avg_trade_net": round(avg_trade_net, 2),
        "median_trade_net": round(median_trade_net, 2),
        "gross_profit": round(gross_profit, 2),
        "gross_loss": round(gross_loss, 2),
        "profit_factor": round(profit_factor, 2) if math.isfinite(profit_factor) else "inf",
        "max_drawdown_pct": round(max_drawdown_pct, 2),
        "best_trade_net": round(best_trade, 2),
        "worst_trade_net": round(worst_trade, 2),
        "avg_hold_minutes": round(avg_hold, 1),
        "avg_return_on_risk_pct": round(avg_return_on_risk, 2),
        "days_considered": int(len(equity_df)),
        "days_missing_dte": skipped_counts["missing_dte"],
        "days_no_signal": skipped_counts["no_signal"],
        "days_late_signal": skipped_counts["late_signal"],
        "days_missing_leg": skipped_counts["missing_leg"],
        "days_synthetic_entry": skipped_counts["synthetic_entry"],
        "days_sizing_skip": skipped_counts["sizing"],
        "days_missing_exit_prices": skipped_counts["missing_exit_prices"],
    }
    return summary


def markdown_table(df: pd.DataFrame, columns: list[str]) -> list[str]:
    header = "| " + " | ".join(columns) + " |"
    separator = "| " + " | ".join(["---"] * len(columns)) + " |"
    rows = [header, separator]
    for _, row in df[columns].iterrows():
        rows.append("| " + " | ".join(str(row[column]) for column in columns) + " |")
    return rows


def write_report(
    path: Path,
    summary_df: pd.DataFrame,
    trades_df: pd.DataFrame,
    day_contexts: list[DayContext],
    assumptions_path: Path,
) -> None:
    complete_days = [ctx.trade_date.isoformat() for ctx in day_contexts]
    top_rows = summary_df.sort_values("final_equity", ascending=False).reset_index(drop=True)
    lines: list[str] = []
    lines.append("# QQQ Option Strategy Backtest")
    lines.append("")
    lines.append(f"Complete RTH sessions used: {len(day_contexts)}")
    lines.append(f"Window: {complete_days[0]} to {complete_days[-1]}")
    lines.append("")
    lines.append("## Assumptions")
    lines.append("")
    lines.append(f"- Starting equity per strategy: ${STARTING_EQUITY:,.0f}")
    lines.append("- RTH only: 09:30 to 15:59 America/New_York")
    lines.append("- Incomplete session filtering removes partial days such as 2026-04-10")
    lines.append("- Alpaca option model assumes commission-free contracts with regulatory fees layered on each order.")
    lines.append(
        "- Fee schedule snapshot: ORF $0.02685/contract, OCC $0.02/contract capped at $55/order, "
        f"CAT ${ALPACA_OPTION_CAT_FEE_PER_CONTRACT:.4f}/contract, and TAF ${ALPACA_OPTION_TAF_PER_CONTRACT:.5f}/sold contract "
        f"(as of {ALPACA_OPTION_FEE_SCHEDULE_AS_OF})."
    )
    lines.append(
        f"- Slippage model: {SLIPPAGE_RATE * 100:.1f}% adverse with a ${MIN_SLIPPAGE:.2f} base minimum per option leg, scaled by premium bucket, trade count, volume, synthetic bars, and time of day."
    )
    execution_calibration = get_execution_slippage_calibration()
    if execution_calibration.get("enabled"):
        lines.append(
            f"- Execution slippage calibration: `{execution_calibration.get('overall_execution_posture', 'unknown')}` posture with `{execution_calibration.get('evidence_strength', 'unknown')}` evidence; entry multiplier {execution_calibration.get('entry_multiplier', 1.0):.2f}, exit multiplier {execution_calibration.get('exit_multiplier', 1.0):.2f}."
        )
    else:
        lines.append("- Execution slippage calibration: unavailable; static fill penalties were used.")
    lines.append(f"- Assumptions JSON: `{assumptions_path.name}`")
    lines.append("")
    lines.append("## Strategy Summary")
    lines.append("")
    summary_display = top_rows[
        [
            "strategy",
            "family",
            "trade_count",
            "final_equity",
            "total_return_pct",
            "win_rate_pct",
            "max_drawdown_pct",
            "profit_factor",
        ]
    ].copy()
    summary_display["final_equity"] = summary_display["final_equity"].map(lambda value: f"${value:,.2f}")
    summary_display["total_return_pct"] = summary_display["total_return_pct"].map(lambda value: f"{value:.2f}%")
    summary_display["win_rate_pct"] = summary_display["win_rate_pct"].map(lambda value: f"{value:.2f}%")
    summary_display["max_drawdown_pct"] = summary_display["max_drawdown_pct"].map(lambda value: f"{value:.2f}%")
    lines.extend(markdown_table(summary_display, list(summary_display.columns)))
    lines.append("")
    lines.append("## Best And Worst Trades")
    lines.append("")
    if trades_df.empty:
        lines.append("No trades were generated.")
    else:
        best_trade = trades_df.sort_values("net_pnl", ascending=False).iloc[0]
        worst_trade = trades_df.sort_values("net_pnl", ascending=True).iloc[0]
        lines.append(
            f"- Best trade: `{best_trade['strategy']}` on `{best_trade['trade_date']}` with `${best_trade['net_pnl']:.2f}` net PnL."
        )
        lines.append(
            f"- Worst trade: `{worst_trade['strategy']}` on `{worst_trade['trade_date']}` with `${worst_trade['net_pnl']:.2f}` net PnL."
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = build_parser().parse_args()
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    wide_path = output_dir / args.wide_name
    daily_universe_path = output_dir / args.daily_universe_name
    if not wide_path.exists():
        raise FileNotFoundError(f"missing wide panel: {wide_path}")
    if not daily_universe_path.exists():
        raise FileNotFoundError(f"missing daily universe: {daily_universe_path}")

    wide = load_wide_data(path=wide_path)
    _, slot_metadata, available_dtes = load_daily_universe(path=daily_universe_path)
    day_contexts = build_day_contexts(wide=wide, available_dtes=available_dtes)

    all_trades: list[pd.DataFrame] = []
    all_equity_curves: list[pd.DataFrame] = []
    summaries: list[dict[str, object]] = []
    for strategy in build_strategies():
        trades_df, equity_df, summary = simulate_strategy(
            strategy=strategy,
            day_contexts=day_contexts,
            slot_metadata=slot_metadata,
        )
        all_trades.append(trades_df)
        all_equity_curves.append(equity_df)
        summaries.append(summary)

    summary_df = pd.DataFrame(summaries).sort_values("final_equity", ascending=False).reset_index(drop=True)
    trades_df = (
        pd.concat([df for df in all_trades if not df.empty], ignore_index=True)
        if any(not df.empty for df in all_trades)
        else pd.DataFrame()
    )
    equity_df = pd.concat(all_equity_curves, ignore_index=True)

    summary_path = output_dir / args.summary_name
    trades_path = output_dir / args.trades_name
    equity_path = output_dir / args.equity_name
    report_path = output_dir / args.report_name
    assumptions_path = output_dir / args.assumptions_name

    summary_df.to_csv(summary_path, index=False)
    if trades_df.empty:
        pd.DataFrame(
            columns=[
                "strategy",
                "family",
                "description",
                "trade_date",
                "dte",
                "entry_time_et",
                "exit_time_et",
                "exit_reason",
                "quantity",
                "legs",
                "entry_underlying",
                "exit_underlying",
                "entry_net_premium",
                "entry_cashflow",
                "exit_cashflow",
                "gross_pnl",
                "entry_broker_commission",
                "exit_broker_commission",
                "broker_commission_total",
                "entry_regulatory_fees",
                "exit_regulatory_fees",
                "regulatory_fee_total",
                "entry_orf_fees",
                "exit_orf_fees",
                "orf_fee_total",
                "entry_occ_clearing_fees",
                "exit_occ_clearing_fees",
                "occ_clearing_fee_total",
                "entry_cat_fees",
                "exit_cat_fees",
                "cat_fee_total",
                "entry_taf_fees",
                "exit_taf_fees",
                "taf_fee_total",
                "entry_total_fees",
                "exit_total_fees",
                "commission_total",
                "net_pnl",
                "max_loss_per_combo",
                "max_profit_per_combo",
                "return_on_risk_pct",
                "holding_minutes",
                "equity_before",
                "equity_after",
                "risk_budget",
                "signal_name",
                "entry_minute",
                "exit_minute",
            ]
        ).to_csv(trades_path, index=False)
    else:
        trades_df.to_csv(trades_path, index=False)
    equity_df.to_csv(equity_path, index=False)

    assumptions = {
        "starting_equity_per_strategy": STARTING_EQUITY,
        "rth_only": True,
        "minutes_per_session": MINUTES_PER_RTH_SESSION,
        "legacy_commission_per_contract_each_side": COMMISSION_PER_CONTRACT,
        "alpaca_option_fee_schedule": {
            "as_of": ALPACA_OPTION_FEE_SCHEDULE_AS_OF,
            "broker_commission_per_contract": ALPACA_OPTION_BROKER_COMMISSION_PER_CONTRACT,
            "orf_per_contract": ALPACA_OPTION_ORF_PER_CONTRACT,
            "occ_clearing_per_contract": ALPACA_OPTION_OCC_CLEARING_PER_CONTRACT,
            "occ_clearing_cap_per_order": ALPACA_OPTION_OCC_CLEARING_CAP_PER_ORDER,
            "cat_fee_per_equivalent_share": ALPACA_OPTION_CAT_FEE_PER_EQUIVALENT_SHARE,
            "cat_fee_per_contract": ALPACA_OPTION_CAT_FEE_PER_CONTRACT,
            "taf_per_sold_contract": ALPACA_OPTION_TAF_PER_CONTRACT,
        },
        "slippage_rate": SLIPPAGE_RATE,
        "minimum_slippage_per_option": MIN_SLIPPAGE,
        "premium_bucket_slippage_multipliers": PREMIUM_BUCKET_SLIPPAGE_MULTIPLIERS,
        "execution_slippage_calibration": get_execution_slippage_calibration(),
        "early_session_minutes": EARLY_SESSION_MINUTES,
        "late_session_minutes": LATE_SESSION_MINUTES,
        "execution_model": "liquidity_aware_phase1",
        "complete_trade_dates": [ctx.trade_date.isoformat() for ctx in day_contexts],
        "strategies": [
            {
                "name": strategy.name,
                "family": strategy.family,
                "description": strategy.description,
                "dte_mode": strategy.dte_mode,
                "legs": [
                    {"option_type": leg.option_type, "step": leg.step, "side": leg.side}
                    for leg in strategy.legs
                ],
                "signal_name": strategy.signal_name,
                "hard_exit_minute": strategy.hard_exit_minute,
                "risk_fraction": strategy.risk_fraction,
                "max_contracts": strategy.max_contracts,
                "profit_target_multiple": strategy.profit_target_multiple,
                "stop_loss_multiple": strategy.stop_loss_multiple,
            }
            for strategy in build_strategies()
        ],
    }
    assumptions_path.write_text(json.dumps(assumptions, indent=2), encoding="utf-8")
    write_report(
        path=report_path,
        summary_df=summary_df,
        trades_df=trades_df,
        day_contexts=day_contexts,
        assumptions_path=assumptions_path,
    )

    print(
        json.dumps(
            {
                "summary_csv": str(summary_path),
                "trades_csv": str(trades_path),
                "equity_curve_csv": str(equity_path),
                "report_md": str(report_path),
                "assumptions_json": str(assumptions_path),
                "complete_sessions_used": len(day_contexts),
                "strategies": len(summary_df),
                "trades": int(len(trades_df)),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
