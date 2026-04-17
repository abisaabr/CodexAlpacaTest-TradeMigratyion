from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from time import perf_counter

import numpy as np
import pandas as pd

from qqq_fvg_backtest_runner import (
    BASE,
    INITIAL_CAPITAL,
    SOURCE,
    STOP_LOSS_PCTS,
    TAKE_PROFIT_PCTS,
    TIMEFRAMES,
    load_minute_data,
    markdown_table,
    resample_intraday,
)
from qqq_fvg_extended_runner import (
    compute_fvg_components,
    run_backtest_detailed_with_cost,
    run_backtest_metrics_with_cost,
)


COST_BPS_PER_SIDE = [0.0, 2.0]
REALISTIC_COST_BPS = 2.0

SELECTORS = [
    "latest",
    "uncontested",
    "dominant_count",
    "dominant_width",
    "nearest_mid",
]
PERSISTENCE_MODES = ["carry", "session_reset"]
EVENT_BASELINE = "event_baseline"

OUTPUTS = {
    "grid": BASE / "qqq_fvg_active_variants_grid_results.csv",
    "summary": BASE / "qqq_fvg_active_variants_summary.md",
    "best_by_variant": BASE / "qqq_fvg_active_variants_best_by_variant.csv",
    "best_realistic_trades": BASE / "qqq_fvg_active_variants_best_realistic_trades.csv",
    "best_realistic_equity": BASE / "qqq_fvg_active_variants_best_realistic_daily_equity.csv",
}


@dataclass(frozen=True)
class PreparedVariantSignals:
    minutes: int
    bars: pd.DataFrame
    session_ids: np.ndarray
    signals: dict[str, np.ndarray]
    signal_counts: dict[str, tuple[int, int]]
    bullish_event_count: int
    bearish_event_count: int


def variant_name(selector: str, persistence: str) -> str:
    return f"active_{selector}_{persistence}"


def parse_variant(variant: str) -> tuple[str, str]:
    if variant == EVENT_BASELINE:
        return "event", "na"

    for persistence in PERSISTENCE_MODES:
        suffix = f"_{persistence}"
        if variant.endswith(suffix):
            selector = variant[len("active_") : -len(suffix)]
            return selector, persistence

    raise ValueError(f"Could not parse variant: {variant}")


def choose_bias(
    active: list[tuple[int, float, float, float, float, int]],
    close_price: float,
    selector: str,
) -> int:
    if not active:
        return 0

    bull_count = 0
    bear_count = 0
    bull_width = 0.0
    bear_width = 0.0

    if selector == "latest":
        return active[-1][0]

    if selector == "nearest_mid":
        best_bias = 0
        best_distance = np.inf
        best_created = -1
        for bias, _lower, _upper, midpoint, _width, created_index in active:
            distance = abs(midpoint - close_price)
            if distance < best_distance or (distance == best_distance and created_index > best_created):
                best_distance = distance
                best_bias = bias
                best_created = created_index
        return best_bias

    for bias, _lower, _upper, _midpoint, width, _created_index in active:
        if bias == 1:
            bull_count += 1
            bull_width += width
        else:
            bear_count += 1
            bear_width += width

    if selector == "uncontested":
        if bull_count > 0 and bear_count == 0:
            return 1
        if bear_count > 0 and bull_count == 0:
            return -1
        return 0

    if selector == "dominant_count":
        if bull_count > bear_count:
            return 1
        if bear_count > bull_count:
            return -1
        return 0

    if selector == "dominant_width":
        if bull_width > bear_width:
            return 1
        if bear_width > bull_width:
            return -1
        return 0

    raise ValueError(f"Unknown selector: {selector}")


def build_active_variant_signal(
    bars: pd.DataFrame,
    session_ids: np.ndarray,
    bullish_event: np.ndarray,
    bearish_event: np.ndarray,
    bullish_bottom: np.ndarray,
    bearish_top: np.ndarray,
    selector: str,
    reset_each_session: bool,
) -> np.ndarray:
    high = bars["high"].to_numpy(dtype=np.float64)
    low = bars["low"].to_numpy(dtype=np.float64)
    close = bars["close"].to_numpy(dtype=np.float64)
    signal = np.zeros(len(bars), dtype=np.int8)
    active: list[tuple[int, float, float, float, float, int]] = []

    for i in range(len(bars)):
        new_session = i == 0 or session_ids[i] != session_ids[i - 1]
        if reset_each_session and new_session:
            active = []

        if active:
            survivors: list[tuple[int, float, float, float, float, int]] = []
            for bias, lower, upper, midpoint, width, created_index in active:
                if bias == 1:
                    if not (low[i] < lower):
                        survivors.append((bias, lower, upper, midpoint, width, created_index))
                else:
                    if not (high[i] > lower):
                        survivors.append((bias, lower, upper, midpoint, width, created_index))
            active = survivors

        if bullish_event[i]:
            lower = float(bullish_bottom[i])
            upper = float(low[i])
            midpoint = 0.5 * (lower + upper)
            width = upper - lower
            active.append((1, lower, upper, midpoint, width, i))

        if bearish_event[i]:
            lower = float(high[i])
            upper = float(low[i - 2])
            midpoint = 0.5 * (lower + upper)
            width = upper - lower
            active.append((-1, lower, upper, midpoint, width, i))

        signal[i] = choose_bias(active, close[i], selector)

    return signal


def prepare_timeframe_variants(frame: pd.DataFrame, minutes: int) -> PreparedVariantSignals:
    bars = resample_intraday(frame, minutes)
    session_ids, _ = pd.factorize(bars["session_date"], sort=True)
    event_signal, bullish_event, bearish_event, bullish_bottom, bearish_top = compute_fvg_components(bars)

    signals: dict[str, np.ndarray] = {EVENT_BASELINE: event_signal}
    signal_counts: dict[str, tuple[int, int]] = {
        EVENT_BASELINE: (int((event_signal == 1).sum()), int((event_signal == -1).sum()))
    }

    for selector in SELECTORS:
        for persistence in PERSISTENCE_MODES:
            name = variant_name(selector, persistence)
            signal = build_active_variant_signal(
                bars,
                session_ids.astype(np.int32),
                bullish_event,
                bearish_event,
                bullish_bottom,
                bearish_top,
                selector=selector,
                reset_each_session=(persistence == "session_reset"),
            )
            signals[name] = signal
            signal_counts[name] = (int((signal == 1).sum()), int((signal == -1).sum()))

    return PreparedVariantSignals(
        minutes=minutes,
        bars=bars,
        session_ids=session_ids.astype(np.int32),
        signals=signals,
        signal_counts=signal_counts,
        bullish_event_count=int(bullish_event.sum()),
        bearish_event_count=int(bearish_event.sum()),
    )


def build_summary(results: pd.DataFrame, runtime_seconds: float) -> str:
    realistic = results[results["cost_bps_per_side"] == REALISTIC_COST_BPS].copy()

    best_realistic = realistic.sort_values(
        ["total_return_pct", "sharpe", "profit_factor"],
        ascending=[False, False, False],
    ).iloc[0]
    best_by_variant = (
        results.sort_values(
            ["variant", "cost_bps_per_side", "total_return_pct", "sharpe"],
            ascending=[True, True, False, False],
        )
        .groupby(["variant", "cost_bps_per_side"], as_index=False)
        .head(1)
        .reset_index(drop=True)
    )
    top_realistic = realistic.sort_values(
        ["total_return_pct", "sharpe", "profit_factor"],
        ascending=[False, False, False],
    ).head(15)
    robustness = (
        realistic.groupby("variant")
        .agg(
            positive=("total_return_pct", lambda s: int((s > 0).sum())),
            combos=("variant", "size"),
            median_return=("total_return_pct", "median"),
            best_return=("total_return_pct", "max"),
            median_dd=("max_drawdown_pct", "median"),
            best_sharpe=("sharpe", "max"),
        )
        .reset_index()
        .sort_values(["best_return", "best_sharpe"], ascending=[False, False])
    )

    summary_by_selector = realistic[realistic["variant"] != EVENT_BASELINE].copy()
    selector_persistence = (
        summary_by_selector.groupby(["selector", "persistence"])
        .agg(
            positive=("total_return_pct", lambda s: int((s > 0).sum())),
            combos=("selector", "size"),
            median_return=("total_return_pct", "median"),
            best_return=("total_return_pct", "max"),
            median_dd=("max_drawdown_pct", "median"),
        )
        .reset_index()
        .sort_values(["best_return", "median_return"], ascending=[False, False])
    )

    cost_view = best_by_variant[
        [
            "variant",
            "cost_bps_per_side",
            "timeframe_label",
            "stop_loss_pct",
            "take_profit_pct",
            "total_return_pct",
            "max_drawdown_pct",
            "sharpe",
            "trade_count",
        ]
    ].copy()
    cost_view["cost_bps_per_side"] = cost_view["cost_bps_per_side"].map(lambda x: f"{x:.1f}")
    for column in ["stop_loss_pct", "take_profit_pct", "total_return_pct", "max_drawdown_pct"]:
        cost_view[column] = cost_view[column].map(lambda x: f"{x:.2f}%")
    cost_view["sharpe"] = cost_view["sharpe"].map(lambda x: f"{x:.2f}")
    cost_view["trade_count"] = cost_view["trade_count"].map(lambda x: f"{int(x)}")

    realistic_view = top_realistic[
        [
            "variant",
            "timeframe_label",
            "stop_loss_pct",
            "take_profit_pct",
            "total_return_pct",
            "max_drawdown_pct",
            "sharpe",
            "profit_factor",
            "trade_count",
            "win_rate_pct",
            "exposure_pct",
        ]
    ].copy()
    for column in [
        "stop_loss_pct",
        "take_profit_pct",
        "total_return_pct",
        "max_drawdown_pct",
        "win_rate_pct",
        "exposure_pct",
    ]:
        realistic_view[column] = realistic_view[column].map(lambda x: f"{x:.2f}%")
    realistic_view["sharpe"] = realistic_view["sharpe"].map(lambda x: f"{x:.2f}")
    realistic_view["profit_factor"] = realistic_view["profit_factor"].map(lambda x: f"{x:.2f}")
    realistic_view["trade_count"] = realistic_view["trade_count"].map(lambda x: f"{int(x)}")

    robustness_view = robustness[
        ["variant", "positive", "combos", "median_return", "best_return", "median_dd", "best_sharpe"]
    ].copy()
    robustness_view["positive"] = robustness_view.apply(
        lambda row: f"{int(row['positive'])}/{int(row['combos'])}",
        axis=1,
    )
    robustness_view = robustness_view.drop(columns=["combos"])
    for column in ["median_return", "best_return", "median_dd"]:
        robustness_view[column] = robustness_view[column].map(lambda x: f"{x:.2f}%")
    robustness_view["best_sharpe"] = robustness_view["best_sharpe"].map(lambda x: f"{x:.2f}")

    selector_view = selector_persistence.copy()
    selector_view["positive"] = selector_view.apply(
        lambda row: f"{int(row['positive'])}/{int(row['combos'])}",
        axis=1,
    )
    selector_view = selector_view.drop(columns=["combos"])
    for column in ["median_return", "best_return", "median_dd"]:
        selector_view[column] = selector_view[column].map(lambda x: f"{x:.2f}%")

    lines = [
        "# QQQ Active FVG Variant Study",
        "",
        "## Variants Tested",
        "",
        "- `event_baseline`: only trade the new FVG formation event.",
        "- `active_latest_*`: follow the newest still-active gap bias.",
        "- `active_uncontested_*`: only trade if all currently active gaps point the same way.",
        "- `active_dominant_count_*`: trade the side with more active gaps.",
        "- `active_dominant_width_*`: trade the side with the larger summed active-gap width.",
        "- `active_nearest_mid_*`: trade the active gap whose midpoint is closest to current price.",
        "- `*_carry`: gaps stay active across sessions until invalidated.",
        "- `*_session_reset`: clear the active gap stack at each new trading session.",
        "",
        "## Best Realistic Variant (`2.0` Bps Per Side)",
        "",
        f"- Variant: `{best_realistic['variant']}`.",
        f"- Timeframe: `{best_realistic['timeframe_label']}`.",
        f"- Stop loss: `{best_realistic['stop_loss_pct']:.2f}%`.",
        f"- Take profit: `{best_realistic['take_profit_pct']:.2f}%`.",
        f"- Total return: `{best_realistic['total_return_pct']:.2f}%`.",
        f"- CAGR: `{best_realistic['cagr_pct']:.2f}%`.",
        f"- Max drawdown: `{best_realistic['max_drawdown_pct']:.2f}%`.",
        f"- Sharpe: `{best_realistic['sharpe']:.2f}`.",
        f"- Profit factor: `{best_realistic['profit_factor']:.2f}`.",
        f"- Trades: `{int(best_realistic['trade_count'])}` with win rate `{best_realistic['win_rate_pct']:.2f}%`.",
        "",
        "## Best Setting By Variant And Cost",
        "",
        markdown_table(cost_view),
        "",
        "## Top 15 Under `2.0` Bps Per Side",
        "",
        markdown_table(realistic_view),
        "",
        "## Robustness By Variant At `2.0` Bps",
        "",
        markdown_table(robustness_view),
        "",
        "## Selector And Persistence Comparison At `2.0` Bps",
        "",
        markdown_table(selector_view),
        "",
        "## Output Files",
        "",
        f"- Full grid: `{OUTPUTS['grid']}`.",
        f"- Best-by-variant leaderboard: `{OUTPUTS['best_by_variant']}`.",
        f"- Best realistic trades: `{OUTPUTS['best_realistic_trades']}`.",
        f"- Best realistic daily equity: `{OUTPUTS['best_realistic_equity']}`.",
        f"- Runtime: `{runtime_seconds:.2f}` seconds.",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    start = perf_counter()
    minute_frame = load_minute_data(SOURCE)
    prepared = {minutes: prepare_timeframe_variants(minute_frame, minutes) for minutes in TIMEFRAMES}

    rows: list[dict[str, float | int | str]] = []
    for minutes, tf_data in prepared.items():
        open_ = tf_data.bars["open"].to_numpy(dtype=np.float64)
        high = tf_data.bars["high"].to_numpy(dtype=np.float64)
        low = tf_data.bars["low"].to_numpy(dtype=np.float64)
        close = tf_data.bars["close"].to_numpy(dtype=np.float64)

        for variant, signal in tf_data.signals.items():
            selector, persistence = parse_variant(variant)
            bullish_signal_count, bearish_signal_count = tf_data.signal_counts[variant]
            for cost_bps_per_side in COST_BPS_PER_SIDE:
                for stop_loss_pct in STOP_LOSS_PCTS:
                    for take_profit_pct in TAKE_PROFIT_PCTS:
                        (
                            ending_equity,
                            total_return_pct,
                            cagr_pct,
                            max_drawdown_pct,
                            sharpe,
                            profit_factor,
                            trade_count,
                            win_count,
                            long_trades,
                            short_trades,
                            session_count,
                            avg_trade_return_pct,
                            avg_holding_bars,
                            exposure_pct,
                        ) = run_backtest_metrics_with_cost(
                            open_,
                            high,
                            low,
                            close,
                            signal,
                            tf_data.session_ids,
                            stop_loss_pct / 100.0,
                            take_profit_pct / 100.0,
                            cost_bps_per_side,
                        )

                        rows.append(
                            {
                                "variant": variant,
                                "selector": selector,
                                "persistence": persistence,
                                "timeframe_min": minutes,
                                "timeframe_label": f"{minutes}m",
                                "cost_bps_per_side": cost_bps_per_side,
                                "stop_loss_pct": stop_loss_pct,
                                "take_profit_pct": take_profit_pct,
                                "ending_equity": ending_equity,
                                "total_return_pct": total_return_pct,
                                "cagr_pct": cagr_pct,
                                "max_drawdown_pct": max_drawdown_pct,
                                "sharpe": sharpe,
                                "profit_factor": profit_factor,
                                "trade_count": trade_count,
                                "win_count": win_count,
                                "win_rate_pct": (win_count / trade_count * 100.0) if trade_count else 0.0,
                                "long_trades": long_trades,
                                "short_trades": short_trades,
                                "session_count": session_count,
                                "avg_trade_return_pct": avg_trade_return_pct,
                                "avg_holding_bars": avg_holding_bars,
                                "avg_holding_minutes": avg_holding_bars * minutes,
                                "exposure_pct": exposure_pct,
                                "bullish_signal_count": bullish_signal_count,
                                "bearish_signal_count": bearish_signal_count,
                                "bullish_event_count": tf_data.bullish_event_count,
                                "bearish_event_count": tf_data.bearish_event_count,
                                "bar_count": len(tf_data.bars),
                            }
                        )

    results = pd.DataFrame(rows).sort_values(
        ["cost_bps_per_side", "total_return_pct", "sharpe", "profit_factor"],
        ascending=[True, False, False, False],
    ).reset_index(drop=True)
    results.to_csv(OUTPUTS["grid"], index=False)

    best_by_variant = (
        results.sort_values(
            ["variant", "cost_bps_per_side", "total_return_pct", "sharpe"],
            ascending=[True, True, False, False],
        )
        .groupby(["variant", "cost_bps_per_side"], as_index=False)
        .head(1)
        .reset_index(drop=True)
    )
    best_by_variant.to_csv(OUTPUTS["best_by_variant"], index=False)

    realistic = results[results["cost_bps_per_side"] == REALISTIC_COST_BPS].copy()
    best_realistic = realistic.sort_values(
        ["total_return_pct", "sharpe", "profit_factor"],
        ascending=[False, False, False],
    ).iloc[0]
    best_tf = prepared[int(best_realistic["timeframe_min"])]
    best_signal = best_tf.signals[str(best_realistic["variant"])]
    trades_df, equity_df = run_backtest_detailed_with_cost(
        best_tf.bars,
        best_signal,
        float(best_realistic["stop_loss_pct"]) / 100.0,
        float(best_realistic["take_profit_pct"]) / 100.0,
        float(best_realistic["cost_bps_per_side"]),
        str(best_realistic["variant"]),
    )
    trades_df.to_csv(OUTPUTS["best_realistic_trades"], index=False)
    equity_df.to_csv(OUTPUTS["best_realistic_equity"], index=False)

    runtime_seconds = perf_counter() - start
    summary = build_summary(results, runtime_seconds)
    OUTPUTS["summary"].write_text(summary + "\n", encoding="utf-8")
    print(summary)


if __name__ == "__main__":
    main()
