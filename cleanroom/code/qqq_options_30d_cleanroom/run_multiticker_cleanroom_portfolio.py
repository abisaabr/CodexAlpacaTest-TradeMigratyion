from __future__ import annotations

import argparse
import json
import time
from dataclasses import dataclass, replace
from itertools import product
from pathlib import Path
from typing import Any

import pandas as pd

import backtest_qqq_greeks_portfolio as bqp
from backtest_qqq_greeks_portfolio import (
    DeltaStrategy,
    build_delta_strategies,
    generate_candidate_trades,
    load_dense_data,
    run_portfolio_allocator,
    summarize_regimes,
)
from backtest_qqq_option_strategies import MINUTES_PER_RTH_SESSION, build_day_contexts, load_daily_universe
from backtest_qqq_regime_gated_portfolio import filter_candidate_trades, select_regime_strategies


DEFAULT_OUTPUT_DIR = Path(__file__).resolve().parent / "output"
DEFAULT_RESEARCH_DIR = DEFAULT_OUTPUT_DIR / "multi_ticker"
DEFAULT_TICKERS = ("qqq", "spy", "iwm", "nvda", "tsla", "msft")
DEFAULT_STARTING_EQUITY = 25_000.0
DEFAULT_INITIAL_TRAIN_DAYS = 126
DEFAULT_TEST_DAYS = 21
DEFAULT_STEP_DAYS = 21
REGIME_THRESHOLD_GRID = [0.30, 0.35, 0.40, 0.45, 0.50, 0.55]
TOP_BULL_GRID = [1, 2, 3, 4]
TOP_BEAR_GRID = [1, 2, 3, 4]
TOP_CHOPPY_GRID = [0, 1, 2]
MIN_TRADE_GRID = [2, 3, 5, 8, 10]
RISK_CAP_GRID = [0.08, 0.10, 0.12, 0.15, 0.18, 0.20]


@dataclass(frozen=True)
class TimingProfile:
    name: str
    orb_window: int
    trend_start: int
    credit_minute: int
    straddle_minute: int
    condor_minute: int


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the phased cleanroom multi-ticker options tournament and portfolio promotion."
    )
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--research-dir", default=str(DEFAULT_RESEARCH_DIR))
    parser.add_argument("--tickers", default=",".join(DEFAULT_TICKERS))
    parser.add_argument("--initial-train-days", type=int, default=DEFAULT_INITIAL_TRAIN_DAYS)
    parser.add_argument("--test-days", type=int, default=DEFAULT_TEST_DAYS)
    parser.add_argument("--step-days", type=int, default=DEFAULT_STEP_DAYS)
    parser.add_argument(
        "--strategy-set",
        choices=("standard", "family_expansion"),
        default="standard",
        help="Strategy universe to test. 'family_expansion' adds new bull/bear/choppy family candidates.",
    )
    parser.add_argument(
        "--continue-on-error",
        action="store_true",
        help="Continue the batch when a ticker fails research and record it in the master summary.",
    )
    parser.add_argument(
        "--reuse-completed-tickers",
        action="store_true",
        help="Reuse existing per-ticker artifacts in the research directory when they match the requested strategy/timing setup.",
    )
    return parser


def build_timing_profiles() -> tuple[TimingProfile, ...]:
    return (
        TimingProfile(
            name="reactive",
            orb_window=5,
            trend_start=20,
            credit_minute=45,
            straddle_minute=5,
            condor_minute=15,
        ),
        TimingProfile(
            name="fast",
            orb_window=10,
            trend_start=30,
            credit_minute=60,
            straddle_minute=10,
            condor_minute=20,
        ),
        TimingProfile(
            name="base",
            orb_window=15,
            trend_start=45,
            credit_minute=90,
            straddle_minute=15,
            condor_minute=30,
        ),
        TimingProfile(
            name="slow",
            orb_window=20,
            trend_start=60,
            credit_minute=120,
            straddle_minute=20,
            condor_minute=45,
        ),
        TimingProfile(
            name="patient",
            orb_window=25,
            trend_start=75,
            credit_minute=150,
            straddle_minute=25,
            condor_minute=60,
        ),
    )


def step_label(step: int) -> str:
    sign = "p" if step >= 0 else "n"
    return f"{sign}{abs(int(step)):02d}"


def load_wide_data_for_ticker(path: Path, ticker: str) -> pd.DataFrame:
    prefix = ticker.lower()
    rename_map = {
        f"{prefix}_open": "qqq_open",
        f"{prefix}_high": "qqq_high",
        f"{prefix}_low": "qqq_low",
        f"{prefix}_close": "qqq_close",
        f"{prefix}_volume": "qqq_volume",
        f"{prefix}_trade_count": "qqq_trade_count",
        f"{prefix}_vwap": "qqq_vwap",
    }
    wide = pd.read_parquet(path).copy()
    missing = [column for column in rename_map if column not in wide.columns]
    if missing:
        raise KeyError(f"missing expected underlying columns for {ticker.upper()}: {missing}")
    wide = wide.rename(columns=rename_map)
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

    full_session_dates: list[object] = []
    for trade_date, frame in wide.groupby("trade_date", sort=True):
        if len(frame) != MINUTES_PER_RTH_SESSION:
            continue
        if frame["qqq_close"].isna().any():
            continue
        full_session_dates.append(trade_date)
    return wide[wide["trade_date"].isin(full_session_dates)].reset_index(drop=True)


def build_day_return_map(wide: pd.DataFrame) -> tuple[list[object], dict[object, float]]:
    daily = (
        wide.groupby("trade_date")
        .agg(day_open=("qqq_open", "first"), day_close=("qqq_close", "last"))
        .reset_index()
    )
    daily["day_ret_pct"] = (daily["day_close"] / daily["day_open"] - 1.0) * 100.0
    return daily["trade_date"].tolist(), dict(zip(daily["trade_date"], daily["day_ret_pct"]))


def assign_regime(day_ret_pct: float, threshold: float) -> str:
    if day_ret_pct >= threshold:
        return "bull"
    if day_ret_pct <= -threshold:
        return "bear"
    return "choppy"


def relabel_candidate_trades(
    candidate_trades: pd.DataFrame,
    day_return_map: dict[object, float],
    threshold: float,
) -> pd.DataFrame:
    relabeled = candidate_trades.copy()
    relabeled["trade_date"] = pd.to_datetime(relabeled["trade_date"]).dt.date
    relabeled["regime"] = [
        assign_regime(day_return_map[row.trade_date], threshold=threshold)
        for row in relabeled.itertuples(index=False)
    ]
    return relabeled


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


def subset_trades(trades: pd.DataFrame, dates: set[object]) -> pd.DataFrame:
    if trades.empty or not dates:
        return trades.iloc[0:0].copy()
    trade_dates = pd.to_datetime(trades["trade_date"]).dt.date
    return trades.loc[trade_dates.isin(dates)].copy()


def score_drawdown(total_return_pct: float, max_drawdown_pct: float) -> float:
    if max_drawdown_pct >= 0.0:
        return total_return_pct if total_return_pct > 0.0 else 0.0
    return total_return_pct / abs(max_drawdown_pct)


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


def entry_orb_profile(ctx, *, bullish: bool, window: int) -> int | None:
    if len(ctx.frame) <= window:
        return None
    opening_end = window - 1
    opening_range_high = float(ctx.frame.loc[:opening_end, "qqq_high"].max())
    opening_range_low = float(ctx.frame.loc[:opening_end, "qqq_low"].min())
    search_end = min(window + 105, len(ctx.frame) - 1)
    for idx in range(window, search_end + 1):
        row = ctx.frame.iloc[idx]
        if bullish:
            if (
                row["qqq_close"] > opening_range_high * 1.0002
                and row["qqq_close"] > row["intraday_vwap"]
                and row["ema_fast"] > row["ema_slow"]
            ):
                return idx
        else:
            if (
                row["qqq_close"] < opening_range_low * 0.9998
                and row["qqq_close"] < row["intraday_vwap"]
                and row["ema_fast"] < row["ema_slow"]
            ):
                return idx
    return None


def entry_trend_profile(ctx, *, bullish: bool, start_minute: int) -> int | None:
    if len(ctx.frame) <= start_minute:
        return None
    search_end = min(start_minute + 105, len(ctx.frame) - 1)
    for idx in range(start_minute, search_end + 1):
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


def entry_credit_profile(ctx, *, bullish: bool, minute_index: int) -> int | None:
    if minute_index >= len(ctx.frame):
        return None
    row = ctx.frame.iloc[minute_index]
    session_range_pct = (
        float(ctx.frame.loc[:minute_index, "qqq_high"].max()) - float(ctx.frame.loc[:minute_index, "qqq_low"].min())
    ) / ctx.day_open
    if bullish:
        if (
            session_range_pct <= 0.0085
            and row["qqq_close"] > row["intraday_vwap"]
            and row["ema_fast"] > row["ema_slow"]
            and row["qqq_close"] > ctx.day_open
        ):
            return minute_index
    else:
        if (
            session_range_pct <= 0.0085
            and row["qqq_close"] < row["intraday_vwap"]
            and row["ema_fast"] < row["ema_slow"]
            and row["qqq_close"] < ctx.day_open
        ):
            return minute_index
    return None


def entry_straddle_profile(ctx, *, minute_index: int) -> int | None:
    if minute_index >= len(ctx.frame):
        return None
    range_pct = (
        float(ctx.frame.loc[:minute_index, "qqq_high"].max()) - float(ctx.frame.loc[:minute_index, "qqq_low"].min())
    ) / ctx.day_open
    ret_pct = (float(ctx.frame.loc[minute_index, "qqq_close"]) / ctx.day_open) - 1.0
    if range_pct >= 0.0055 or abs(ret_pct) >= 0.0035:
        return minute_index
    return None


def entry_condor_profile(ctx, *, minute_index: int) -> int | None:
    if minute_index >= len(ctx.frame):
        return None
    row = ctx.frame.iloc[minute_index]
    range_pct = (
        float(ctx.frame.loc[:minute_index, "qqq_high"].max()) - float(ctx.frame.loc[:minute_index, "qqq_low"].min())
    ) / ctx.day_open
    ret_pct = (float(row["qqq_close"]) / ctx.day_open) - 1.0
    close_to_vwap = abs((row["qqq_close"] / row["intraday_vwap"]) - 1.0)
    if range_pct <= 0.0062 and abs(ret_pct) <= 0.0045 and close_to_vwap <= 0.0020:
        return minute_index
    return None


def build_signal_dispatch(profiles: tuple[TimingProfile, ...]) -> dict[str, Any]:
    dispatch: dict[str, Any] = {}
    for profile in profiles:
        dispatch[f"{profile.name}__orb_call"] = (
            lambda ctx, window=profile.orb_window: entry_orb_profile(ctx, bullish=True, window=window)
        )
        dispatch[f"{profile.name}__orb_put"] = (
            lambda ctx, window=profile.orb_window: entry_orb_profile(ctx, bullish=False, window=window)
        )
        dispatch[f"{profile.name}__trend_call"] = (
            lambda ctx, start=profile.trend_start: entry_trend_profile(ctx, bullish=True, start_minute=start)
        )
        dispatch[f"{profile.name}__trend_put"] = (
            lambda ctx, start=profile.trend_start: entry_trend_profile(ctx, bullish=False, start_minute=start)
        )
        dispatch[f"{profile.name}__credit_bull"] = (
            lambda ctx, minute_index=profile.credit_minute: entry_credit_profile(ctx, bullish=True, minute_index=minute_index)
        )
        dispatch[f"{profile.name}__credit_bear"] = (
            lambda ctx, minute_index=profile.credit_minute: entry_credit_profile(ctx, bullish=False, minute_index=minute_index)
        )
        dispatch[f"{profile.name}__long_straddle"] = (
            lambda ctx, minute_index=profile.straddle_minute: entry_straddle_profile(ctx, minute_index=minute_index)
        )
        dispatch[f"{profile.name}__iron_condor"] = (
            lambda ctx, minute_index=profile.condor_minute: entry_condor_profile(ctx, minute_index=minute_index)
        )
    return dispatch


def build_strategy_variants(
    ticker: str,
    profiles: tuple[TimingProfile, ...],
    *,
    strategy_set: str = "standard",
) -> list[DeltaStrategy]:
    variants: list[DeltaStrategy] = []
    for base_strategy in build_delta_strategies(include_family_expansion=(strategy_set == "family_expansion")):
        for profile in profiles:
            variants.append(
                replace(
                    base_strategy,
                    name=f"{ticker.lower()}__{profile.name}__{base_strategy.name}",
                    description=f"{ticker.upper()} [{profile.name}] {base_strategy.description}",
                    signal_name=f"{profile.name}__{base_strategy.signal_name}",
                )
            )
    return variants


def parse_strategy_metadata(strategy_name: str) -> tuple[str, str, str]:
    ticker, profile, base_name = strategy_name.split("__", 2)
    return ticker.upper(), profile, base_name


def enrich_candidate_trades(trades: pd.DataFrame) -> pd.DataFrame:
    if trades.empty:
        return trades
    enriched = trades.copy()
    metadata = [parse_strategy_metadata(name) for name in enriched["strategy"].astype(str)]
    enriched["ticker"] = [item[0] for item in metadata]
    enriched["timing_profile"] = [item[1] for item in metadata]
    enriched["base_strategy"] = [item[2] for item in metadata]
    return enriched


def family_bucket_for_strategy_family(family: str) -> str:
    if family in {"Single-leg long call", "Single-leg long put"}:
        return "Single-leg"
    if family in {"Debit call spread", "Debit put spread"}:
        return "Debit spread"
    if family in {"Credit put spread", "Credit call spread"}:
        return "Credit spread"
    if family in {
        "Iron condor",
        "Iron butterfly",
        "Call butterfly",
        "Put butterfly",
        "Broken-wing call butterfly",
        "Broken-wing put butterfly",
    }:
        return "Neutral premium"
    if family in {"Long straddle", "Long strangle", "Call backspread", "Put backspread"}:
        return "Long-vol"
    return family


def summarize_strategy_group_contributions(
    *,
    trades_df: pd.DataFrame,
    strategy_map: dict[str, DeltaStrategy] | None,
    group_column: str,
    group_resolver,
) -> list[dict[str, object]]:
    if trades_df.empty or not strategy_map:
        return []
    enriched = trades_df.copy()
    enriched[group_column] = [
        group_resolver(strategy_map.get(str(name))) if strategy_map.get(str(name)) is not None else "Unknown"
        for name in enriched["strategy"].astype(str)
    ]
    grouped = (
        enriched.groupby(group_column, as_index=False)
        .agg(
            portfolio_net_pnl=("portfolio_net_pnl", "sum"),
            trade_count=("portfolio_net_pnl", "size"),
            win_rate_pct=("portfolio_net_pnl", lambda values: (values > 0).mean() * 100.0),
            avg_trade_pnl=("portfolio_net_pnl", "mean"),
        )
        .sort_values(["portfolio_net_pnl", "trade_count"], ascending=[False, False])
        .reset_index(drop=True)
    )
    grouped["portfolio_net_pnl"] = grouped["portfolio_net_pnl"].round(2)
    grouped["win_rate_pct"] = grouped["win_rate_pct"].round(2)
    grouped["avg_trade_pnl"] = grouped["avg_trade_pnl"].round(2)
    return grouped.to_dict(orient="records")


def attach_family_contributions(
    *,
    summary: dict[str, object],
    trades_df: pd.DataFrame,
    strategy_map: dict[str, DeltaStrategy] | None,
) -> dict[str, object]:
    enriched = dict(summary)
    enriched["family_contributions"] = summarize_strategy_group_contributions(
        trades_df=trades_df,
        strategy_map=strategy_map,
        group_column="family",
        group_resolver=lambda strategy: strategy.family,
    )
    enriched["family_bucket_contributions"] = summarize_strategy_group_contributions(
        trades_df=trades_df,
        strategy_map=strategy_map,
        group_column="family_bucket",
        group_resolver=lambda strategy: family_bucket_for_strategy_family(strategy.family),
    )
    return enriched


def contribution_rows_to_frame(rows: list[dict[str, object]], label_column: str) -> pd.DataFrame:
    frame = pd.DataFrame(rows)
    if frame.empty:
        return pd.DataFrame(
            columns=[label_column, "portfolio_net_pnl", "trade_count", "win_rate_pct", "avg_trade_pnl"]
        )
    return frame


def summarize_run(
    trades_df: pd.DataFrame,
    equity_df: pd.DataFrame,
    starting_equity: float,
    strategy_map: dict[str, DeltaStrategy] | None = None,
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
    return attach_family_contributions(summary=summary, trades_df=trades_df, strategy_map=strategy_map)


def strategy_objects_from_names(
    selected_names: list[str],
    strategy_map: dict[str, DeltaStrategy],
) -> list[DeltaStrategy]:
    return [strategy_map[name] for name in sorted(set(selected_names)) if name in strategy_map]


def select_best_config(
    *,
    candidate_trades: pd.DataFrame,
    day_return_map: dict[object, float],
    strategy_map: dict[str, DeltaStrategy],
    thresholds: list[float],
    top_bull_values: list[int],
    top_bear_values: list[int],
    top_choppy_values: list[int],
    min_trade_values: list[int],
    risk_caps: list[float],
) -> dict[str, object]:
    best_row: dict[str, object] | None = None
    cache_by_threshold: dict[float, tuple[pd.DataFrame, pd.DataFrame]] = {}
    for regime_threshold, top_bull, top_bear, top_choppy, min_regime_trades, risk_cap in product(
        thresholds,
        top_bull_values,
        top_bear_values,
        top_choppy_values,
        min_trade_values,
        risk_caps,
    ):
        if regime_threshold not in cache_by_threshold:
            relabeled = relabel_candidate_trades(
                candidate_trades=candidate_trades,
                day_return_map=day_return_map,
                threshold=regime_threshold,
            )
            cache_by_threshold[regime_threshold] = (relabeled, summarize_regimes(relabeled))
        relabeled, regime_summary = cache_by_threshold[regime_threshold]
        selected, selected_rows = select_regime_strategies(
            regime_summary=regime_summary,
            top_bull=top_bull,
            top_bear=top_bear,
            top_choppy=top_choppy,
            min_regime_trades=min_regime_trades,
        )
        filtered = filter_candidate_trades(trades=relabeled, selected=selected)
        selected_names = (
            list(selected["bull"]) + list(selected["bear"]) + list(selected["choppy"])
        )
        strategies = strategy_objects_from_names(selected_names, strategy_map=strategy_map)
        if filtered.empty or not strategies:
            summary = attach_family_contributions(
                summary=empty_summary(starting_equity=DEFAULT_STARTING_EQUITY, risk_cap=risk_cap),
                trades_df=pd.DataFrame(),
                strategy_map=strategy_map,
            )
        else:
            portfolio_trades, _, summary = run_portfolio_allocator(
                strategies=strategies,
                trades_df=filtered,
                portfolio_max_open_risk_fraction=risk_cap,
                starting_equity=DEFAULT_STARTING_EQUITY,
            )
            summary = attach_family_contributions(
                summary=summary,
                trades_df=portfolio_trades,
                strategy_map=strategy_map,
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
            "selected_summary_rows": selected_rows.to_dict(orient="records"),
            "portfolio_trade_count": int(summary["trade_count"]),
            "final_equity": float(summary["final_equity"]),
            "total_return_pct": float(summary["total_return_pct"]),
            "win_rate_pct": float(summary["win_rate_pct"]),
            "max_drawdown_pct": float(summary["max_drawdown_pct"]),
            "calmar_like": score_drawdown(
                total_return_pct=float(summary["total_return_pct"]),
                max_drawdown_pct=float(summary["max_drawdown_pct"]),
            ),
            "strategy_contributions": list(summary.get("strategy_contributions", [])),
            "family_contributions": list(summary.get("family_contributions", [])),
            "family_bucket_contributions": list(summary.get("family_bucket_contributions", [])),
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
        raise RuntimeError("no config selected")
    return best_row


def evaluate_config(
    *,
    candidate_trades: pd.DataFrame,
    day_return_map: dict[object, float],
    config: dict[str, object],
    strategy_map: dict[str, DeltaStrategy],
    test_dates: set[object],
    starting_equity: float,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, object], pd.DataFrame]:
    test_trades = subset_trades(trades=candidate_trades, dates=test_dates)
    relabeled = relabel_candidate_trades(
        candidate_trades=test_trades,
        day_return_map=day_return_map,
        threshold=float(config["regime_threshold_pct"]),
    )
    selected = {
        "bull": list(config["selected_bull"]),
        "bear": list(config["selected_bear"]),
        "choppy": list(config["selected_choppy"]),
    }
    filtered = filter_candidate_trades(trades=relabeled, selected=selected)
    strategies = strategy_objects_from_names(
        list(selected["bull"]) + list(selected["bear"]) + list(selected["choppy"]),
        strategy_map=strategy_map,
    )
    if filtered.empty or not strategies:
        return (
            pd.DataFrame(),
            pd.DataFrame(),
            attach_family_contributions(
                summary=empty_summary(starting_equity, float(config["risk_cap"])),
                trades_df=pd.DataFrame(),
                strategy_map=strategy_map,
            ),
            filtered,
        )
    portfolio_trades, equity_curve, summary = run_portfolio_allocator(
        strategies=strategies,
        trades_df=filtered,
        portfolio_max_open_risk_fraction=float(config["risk_cap"]),
        starting_equity=starting_equity,
    )
    summary = attach_family_contributions(
        summary=summary,
        trades_df=portfolio_trades,
        strategy_map=strategy_map,
    )
    return portfolio_trades, equity_curve, summary, filtered


def promote_config(
    *,
    ticker: str,
    frozen_config: dict[str, object],
    frozen_summary: dict[str, object],
) -> dict[str, object]:
    promoted = {
        "ticker": ticker.upper(),
        "regime_threshold_pct": float(frozen_config["regime_threshold_pct"]),
        "risk_cap": float(frozen_config["risk_cap"]),
        "selected_bull": list(frozen_config["selected_bull"]),
        "selected_bear": list(frozen_config["selected_bear"]),
        "selected_choppy": list(frozen_config["selected_choppy"]),
    }
    positive_contributors = {
        item["strategy"]
        for item in frozen_summary.get("strategy_contributions", [])
        if float(item["portfolio_net_pnl"]) > 0.0
    }
    for regime_key in ["selected_bull", "selected_bear", "selected_choppy"]:
        promoted[regime_key] = [
            name for name in promoted[regime_key] if name in positive_contributors
        ]
    if promoted["selected_bull"] or promoted["selected_bear"] or promoted["selected_choppy"]:
        return promoted
    contributions = list(frozen_summary.get("strategy_contributions", []))
    fallback_name = None
    if contributions:
        fallback_name = str(contributions[0]["strategy"])
    else:
        all_selected = (
            list(frozen_config["selected_bull"])
            + list(frozen_config["selected_bear"])
            + list(frozen_config["selected_choppy"])
        )
        if all_selected:
            fallback_name = str(all_selected[0])
    if fallback_name is not None:
        if fallback_name in frozen_config["selected_bull"]:
            promoted["selected_bull"] = [fallback_name]
        elif fallback_name in frozen_config["selected_bear"]:
            promoted["selected_bear"] = [fallback_name]
        else:
            promoted["selected_choppy"] = [fallback_name]
    return promoted


def run_single_ticker_research(
    *,
    ticker: str,
    output_dir: Path,
    research_dir: Path,
    initial_train_days: int,
    test_days: int,
    step_days: int,
    profiles: tuple[TimingProfile, ...],
    strategy_set: str,
) -> dict[str, object]:
    ticker_lower = ticker.lower()
    research_dir.mkdir(parents=True, exist_ok=True)
    wide_path = output_dir / f"{ticker_lower}_365d_option_1min_wide_backtest.parquet"
    dense_path = output_dir / f"{ticker_lower}_365d_option_1min_dense.parquet"
    universe_path = output_dir / f"{ticker_lower}_365d_option_daily_universe.parquet"

    wide = load_wide_data_for_ticker(wide_path, ticker_lower)
    _, _, available_dtes = load_daily_universe(universe_path)
    day_contexts = build_day_contexts(wide=wide, available_dtes=available_dtes)
    valid_trade_dates = {ctx.trade_date for ctx in day_contexts}
    chain_index, price_index = load_dense_data(
        path=dense_path,
        valid_trade_dates=valid_trade_dates,
        wide=wide,
    )

    strategy_variants = build_strategy_variants(
        ticker_lower,
        profiles,
        strategy_set=strategy_set,
    )
    strategy_map = {strategy.name: strategy for strategy in strategy_variants}
    original_dispatch = bqp.SIGNAL_DISPATCH
    try:
        bqp.SIGNAL_DISPATCH = build_signal_dispatch(profiles)
        ticker_started_at = time.perf_counter()

        def _progress_callback(progress: dict[str, object]) -> None:
            strategy_index = int(progress["strategy_index"])
            strategy_count = int(progress["strategy_count"])
            if strategy_index != 1 and strategy_index % 5 != 0 and strategy_index != strategy_count:
                return
            print(
                (
                    f"{ticker.upper()} candidate progress: "
                    f"{strategy_index}/{strategy_count} "
                    f"{progress['strategy_name']} "
                    f"new_trades={int(progress['new_trade_count'])} "
                    f"total_trades={int(progress['trade_count'])} "
                    f"elapsed={float(progress['elapsed_seconds']):.1f}s"
                ),
                flush=True,
            )

        candidate_trades = generate_candidate_trades(
            strategies=strategy_variants,
            day_contexts=day_contexts,
            chain_index=chain_index,
            price_index=price_index,
            regime_map=bqp.build_regime_map(wide),
            progress_callback=_progress_callback,
        )
        print(
            f"{ticker.upper()} candidate generation complete in {time.perf_counter() - ticker_started_at:.1f}s "
            f"with {len(candidate_trades)} trades.",
            flush=True,
        )
    finally:
        bqp.SIGNAL_DISPATCH = original_dispatch

    candidate_trades = enrich_candidate_trades(candidate_trades)
    ordered_trade_dates, day_return_map = build_day_return_map(wide=wide)
    folds = build_folds(
        trade_dates=ordered_trade_dates,
        initial_train_days=initial_train_days,
        test_days=test_days,
        step_days=step_days,
    )
    if not folds:
        raise RuntimeError(f"no folds built for {ticker.upper()}")
    regime_summary = summarize_regimes(candidate_trades)
    train_dates = set(folds[0]["train_dates"])
    frozen_config = select_best_config(
        candidate_trades=subset_trades(candidate_trades, train_dates),
        day_return_map=day_return_map,
        strategy_map=strategy_map,
        thresholds=REGIME_THRESHOLD_GRID,
        top_bull_values=TOP_BULL_GRID,
        top_bear_values=TOP_BEAR_GRID,
        top_choppy_values=TOP_CHOPPY_GRID,
        min_trade_values=MIN_TRADE_GRID,
        risk_caps=RISK_CAP_GRID,
    )

    reopt_trade_frames: list[pd.DataFrame] = []
    reopt_equity_frames: list[pd.DataFrame] = []
    frozen_trade_frames: list[pd.DataFrame] = []
    frozen_equity_frames: list[pd.DataFrame] = []
    fold_rows: list[dict[str, object]] = []
    reopt_current_equity = DEFAULT_STARTING_EQUITY
    frozen_current_equity = DEFAULT_STARTING_EQUITY
    for fold in folds:
        reopt_config = select_best_config(
            candidate_trades=subset_trades(candidate_trades, set(fold["train_dates"])),
            day_return_map=day_return_map,
            strategy_map=strategy_map,
            thresholds=REGIME_THRESHOLD_GRID,
            top_bull_values=TOP_BULL_GRID,
            top_bear_values=TOP_BEAR_GRID,
            top_choppy_values=TOP_CHOPPY_GRID,
            min_trade_values=MIN_TRADE_GRID,
            risk_caps=RISK_CAP_GRID,
        )
        reopt_trades, reopt_equity, reopt_summary, _ = evaluate_config(
            candidate_trades=candidate_trades,
            day_return_map=day_return_map,
            config=reopt_config,
            strategy_map=strategy_map,
            test_dates=set(fold["test_dates"]),
            starting_equity=reopt_current_equity,
        )
        frozen_trades, frozen_equity, frozen_summary, _ = evaluate_config(
            candidate_trades=candidate_trades,
            day_return_map=day_return_map,
            config=frozen_config,
            strategy_map=strategy_map,
            test_dates=set(fold["test_dates"]),
            starting_equity=frozen_current_equity,
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
        fold_rows.append(
            {
                "fold": fold["fold"],
                "train_start": fold["train_dates"][0].isoformat(),
                "train_end": fold["train_dates"][-1].isoformat(),
                "test_start": fold["test_dates"][0].isoformat(),
                "test_end": fold["test_dates"][-1].isoformat(),
                "reopt_final_equity": reopt_summary["final_equity"],
                "reopt_return_pct": reopt_summary["total_return_pct"],
                "frozen_final_equity": frozen_summary["final_equity"],
                "frozen_return_pct": frozen_summary["total_return_pct"],
            }
        )
        reopt_current_equity = float(reopt_summary["final_equity"])
        frozen_current_equity = float(frozen_summary["final_equity"])

    reopt_trades_df = pd.concat(reopt_trade_frames, ignore_index=True) if reopt_trade_frames else pd.DataFrame()
    reopt_equity_df = pd.concat(reopt_equity_frames, ignore_index=True) if reopt_equity_frames else pd.DataFrame()
    frozen_trades_df = pd.concat(frozen_trade_frames, ignore_index=True) if frozen_trade_frames else pd.DataFrame()
    frozen_equity_df = pd.concat(frozen_equity_frames, ignore_index=True) if frozen_equity_frames else pd.DataFrame()
    frozen_summary = summarize_run(
        trades_df=frozen_trades_df,
        equity_df=frozen_equity_df,
        starting_equity=DEFAULT_STARTING_EQUITY,
        strategy_map=strategy_map,
    )
    reoptimized_summary = summarize_run(
        trades_df=reopt_trades_df,
        equity_df=reopt_equity_df,
        starting_equity=DEFAULT_STARTING_EQUITY,
        strategy_map=strategy_map,
    )
    promoted = promote_config(
        ticker=ticker_lower,
        frozen_config=frozen_config,
        frozen_summary=frozen_summary,
    )

    candidate_trades.to_csv(research_dir / f"{ticker_lower}_candidate_trades.csv", index=False)
    regime_summary.to_csv(research_dir / f"{ticker_lower}_regime_summary.csv", index=False)
    pd.DataFrame(fold_rows).to_csv(research_dir / f"{ticker_lower}_walkforward_folds.csv", index=False)
    frozen_trades_df.to_csv(research_dir / f"{ticker_lower}_walkforward_frozen_trades.csv", index=False)
    frozen_equity_df.to_csv(research_dir / f"{ticker_lower}_walkforward_frozen_equity.csv", index=False)
    contribution_rows_to_frame(
        list(frozen_summary.get("family_contributions", [])),
        "family",
    ).to_csv(research_dir / f"{ticker_lower}_walkforward_frozen_family_contributions.csv", index=False)
    contribution_rows_to_frame(
        list(frozen_summary.get("family_bucket_contributions", [])),
        "family_bucket",
    ).to_csv(research_dir / f"{ticker_lower}_walkforward_frozen_family_bucket_contributions.csv", index=False)
    contribution_rows_to_frame(
        list(reoptimized_summary.get("family_contributions", [])),
        "family",
    ).to_csv(research_dir / f"{ticker_lower}_walkforward_reoptimized_family_contributions.csv", index=False)
    contribution_rows_to_frame(
        list(reoptimized_summary.get("family_bucket_contributions", [])),
        "family_bucket",
    ).to_csv(research_dir / f"{ticker_lower}_walkforward_reoptimized_family_bucket_contributions.csv", index=False)
    (research_dir / f"{ticker_lower}_frozen_config.json").write_text(
        json.dumps(frozen_config, indent=2),
        encoding="utf-8",
    )
    (research_dir / f"{ticker_lower}_promotion.json").write_text(
        json.dumps(promoted, indent=2),
        encoding="utf-8",
    )
    summary = {
        "ticker": ticker.upper(),
        "trade_date_start": ordered_trade_dates[0].isoformat(),
        "trade_date_end": ordered_trade_dates[-1].isoformat(),
        "day_count": len(ordered_trade_dates),
        "candidate_trade_count": int(len(candidate_trades)),
        "strategy_set": strategy_set,
        "timing_profiles": [profile.name for profile in profiles],
        "frozen_initial_config": frozen_config,
        "reoptimized": reoptimized_summary,
        "frozen_initial": frozen_summary,
        "promoted": promoted,
    }
    (research_dir / f"{ticker_lower}_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return {
        "ticker": ticker.upper(),
        "candidate_trades": candidate_trades,
        "day_return_map": day_return_map,
        "ordered_trade_dates": ordered_trade_dates,
        "strategy_map": strategy_map,
        "regime_summary": regime_summary,
        "summary": summary,
    }


def try_load_existing_ticker_result(
    *,
    ticker: str,
    output_dir: Path,
    research_dir: Path,
    profiles: tuple[TimingProfile, ...],
    strategy_set: str,
) -> dict[str, object] | None:
    ticker_lower = ticker.lower()
    summary_path = research_dir / f"{ticker_lower}_summary.json"
    candidate_trades_path = research_dir / f"{ticker_lower}_candidate_trades.csv"
    regime_summary_path = research_dir / f"{ticker_lower}_regime_summary.csv"
    wide_path = output_dir / f"{ticker_lower}_365d_option_1min_wide_backtest.parquet"

    if not summary_path.exists() or not candidate_trades_path.exists() or not wide_path.exists():
        return None

    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    expected_profiles = [profile.name for profile in profiles]
    if summary.get("timing_profiles") != expected_profiles:
        return None
    if summary.get("strategy_set", "standard") != strategy_set:
        return None

    strategy_variants = build_strategy_variants(
        ticker_lower,
        profiles,
        strategy_set=strategy_set,
    )
    strategy_map = {strategy.name: strategy for strategy in strategy_variants}
    promoted = summary.get("promoted", {})
    selected_names = (
        list(promoted.get("selected_bull", []))
        + list(promoted.get("selected_bear", []))
        + list(promoted.get("selected_choppy", []))
    )
    if any(name not in strategy_map for name in selected_names):
        return None

    candidate_trades = pd.read_csv(candidate_trades_path)
    regime_summary = (
        pd.read_csv(regime_summary_path)
        if regime_summary_path.exists()
        else summarize_regimes(candidate_trades)
    )
    wide = load_wide_data_for_ticker(wide_path, ticker_lower)
    ordered_trade_dates, day_return_map = build_day_return_map(wide=wide)
    return {
        "ticker": ticker.upper(),
        "candidate_trades": candidate_trades,
        "day_return_map": day_return_map,
        "ordered_trade_dates": ordered_trade_dates,
        "strategy_map": strategy_map,
        "regime_summary": regime_summary,
        "summary": summary,
        "reused_existing": True,
    }


def build_combined_promoted_candidates(
    *,
    ticker_results: list[dict[str, object]],
    oos_dates: set[object],
) -> tuple[pd.DataFrame, dict[str, DeltaStrategy]]:
    filtered_frames: list[pd.DataFrame] = []
    strategy_map: dict[str, DeltaStrategy] = {}
    for result in ticker_results:
        promoted = result["summary"]["promoted"]
        selected = {
            "bull": list(promoted["selected_bull"]),
            "bear": list(promoted["selected_bear"]),
            "choppy": list(promoted["selected_choppy"]),
        }
        candidate_trades = subset_trades(result["candidate_trades"], oos_dates)
        relabeled = relabel_candidate_trades(
            candidate_trades=candidate_trades,
            day_return_map=result["day_return_map"],
            threshold=float(promoted["regime_threshold_pct"]),
        )
        filtered = filter_candidate_trades(trades=relabeled, selected=selected)
        if not filtered.empty:
            filtered_frames.append(filtered)
        selected_names = list(selected["bull"]) + list(selected["bear"]) + list(selected["choppy"])
        for name in selected_names:
            strategy_map[name] = result["strategy_map"][name]
    combined = pd.concat(filtered_frames, ignore_index=True) if filtered_frames else pd.DataFrame()
    if not combined.empty:
        combined = combined.sort_values(["trade_date", "entry_minute", "strategy"]).reset_index(drop=True)
    return combined, strategy_map


def optimize_shared_portfolio(
    *,
    candidate_trades: pd.DataFrame,
    strategy_map: dict[str, DeltaStrategy],
    risk_caps: list[float],
) -> tuple[dict[str, object], pd.DataFrame, pd.DataFrame]:
    best_summary: dict[str, object] | None = None
    best_trades = pd.DataFrame()
    best_equity = pd.DataFrame()
    strategies = strategy_objects_from_names(candidate_trades["strategy"].tolist(), strategy_map)
    for risk_cap in risk_caps:
        if candidate_trades.empty or not strategies:
            summary = attach_family_contributions(
                summary=empty_summary(DEFAULT_STARTING_EQUITY, risk_cap),
                trades_df=pd.DataFrame(),
                strategy_map=strategy_map,
            )
            trades = pd.DataFrame()
            equity = pd.DataFrame()
        else:
            trades, equity, summary = run_portfolio_allocator(
                strategies=strategies,
                trades_df=candidate_trades,
                portfolio_max_open_risk_fraction=risk_cap,
                starting_equity=DEFAULT_STARTING_EQUITY,
            )
            summary = attach_family_contributions(
                summary=summary,
                trades_df=trades,
                strategy_map=strategy_map,
            )
        row = {
            "risk_cap": risk_cap,
            "final_equity": float(summary["final_equity"]),
            "total_return_pct": float(summary["total_return_pct"]),
            "trade_count": int(summary["trade_count"]),
            "win_rate_pct": float(summary["win_rate_pct"]),
            "max_drawdown_pct": float(summary["max_drawdown_pct"]),
            "calmar_like": score_drawdown(
                total_return_pct=float(summary["total_return_pct"]),
                max_drawdown_pct=float(summary["max_drawdown_pct"]),
            ),
            "strategy_contributions": list(summary.get("strategy_contributions", [])),
            "family_contributions": list(summary.get("family_contributions", [])),
            "family_bucket_contributions": list(summary.get("family_bucket_contributions", [])),
        }
        if best_summary is None:
            best_summary = row
            best_trades = trades
            best_equity = equity
            continue
        current_tuple = (
            row["total_return_pct"] > 0.0,
            row["calmar_like"],
            row["final_equity"],
            row["trade_count"],
        )
        best_tuple = (
            best_summary["total_return_pct"] > 0.0,
            best_summary["calmar_like"],
            best_summary["final_equity"],
            best_summary["trade_count"],
        )
        if current_tuple > best_tuple:
            best_summary = row
            best_trades = trades
            best_equity = equity
    if best_summary is None:
        raise RuntimeError("shared portfolio optimization produced no result")
    return best_summary, best_trades, best_equity


def build_family_ranking_rows(
    *,
    scope: str,
    ticker: str | None,
    summary: dict[str, object],
    contribution_key: str,
    label_key: str,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for item in summary.get(contribution_key, []):
        rows.append(
            {
                "scope": scope,
                "ticker": ticker or "",
                label_key: item.get(label_key, ""),
                "portfolio_net_pnl": float(item.get("portfolio_net_pnl", 0.0)),
                "trade_count": int(item.get("trade_count", 0)),
                "win_rate_pct": float(item.get("win_rate_pct", 0.0)),
                "avg_trade_pnl": float(item.get("avg_trade_pnl", 0.0)),
            }
        )
    return rows


def write_master_report(path: Path, payload: dict[str, object]) -> None:
    lines: list[str] = []
    failed_tickers = list(payload.get("failed_tickers", []))
    lines.append("# Multi-Ticker Cleanroom Portfolio Report")
    lines.append("")
    lines.append(
        f"- Tickers tested: {', '.join(payload['tickers'])}"
    )
    lines.append(
        f"- Training window: {payload['initial_train_days']} days, test window: {payload['test_days']} days, step: {payload['step_days']} days."
    )
    lines.append(
        f"- Successful tickers: {', '.join(payload.get('successful_tickers', [])) if payload.get('successful_tickers') else 'none'}"
    )
    lines.append(
        f"- Failed tickers: {', '.join(row['ticker'] for row in failed_tickers) if failed_tickers else 'none'}"
    )
    lines.append("")
    lines.append("## Promoted Strategies")
    lines.append("")
    for row in payload["ticker_promotions"]:
        lines.append(f"### {row['ticker']}")
        lines.append(
            f"- Bull: {', '.join(f'`{name}`' for name in row['selected_bull']) if row['selected_bull'] else 'none'}"
        )
        lines.append(
            f"- Bear: {', '.join(f'`{name}`' for name in row['selected_bear']) if row['selected_bear'] else 'none'}"
        )
        lines.append(
            f"- Choppy: {', '.join(f'`{name}`' for name in row['selected_choppy']) if row['selected_choppy'] else 'none'}"
        )
        lines.append(
            f"- OOS frozen result: ${row['frozen_final_equity']:.2f}, {row['frozen_total_return_pct']:.2f}%, drawdown {row['frozen_max_drawdown_pct']:.2f}%."
        )
        lines.append("")
    lines.append("## Shared Account")
    lines.append("")
    shared = payload["shared_account"]
    qqq_only = payload.get("qqq_only")
    lines.append(
        f"- Combined promoted book: ${shared['final_equity']:.2f}, {shared['total_return_pct']:.2f}%, drawdown {shared['max_drawdown_pct']:.2f}%, risk cap {shared['risk_cap'] * 100:.0f}%."
    )
    if qqq_only is None:
        lines.append("- QQQ-only promoted book: unavailable for this batch.")
        lines.append("- Relative lift vs QQQ-only: unavailable for this batch.")
    else:
        lines.append(
            f"- QQQ-only promoted book: ${qqq_only['final_equity']:.2f}, {qqq_only['total_return_pct']:.2f}%, drawdown {qqq_only['max_drawdown_pct']:.2f}%, risk cap {qqq_only['risk_cap'] * 100:.0f}%."
        )
        lines.append(
            f"- Relative lift vs QQQ-only: {payload['relative_return_vs_qqq_only_pct']:.2f} percentage points."
        )
    family_rankings = payload.get("family_rankings", {})
    shared_buckets = list(family_rankings.get("shared_account_buckets", []))
    qqq_buckets = list(family_rankings.get("qqq_only_buckets", []))
    per_ticker_buckets = list(family_rankings.get("per_ticker_frozen_buckets", []))
    lines.append("")
    lines.append("## Family Leaders")
    lines.append("")
    lines.append("### Shared Account Buckets")
    lines.append("")
    if shared_buckets:
        for row in shared_buckets:
            lines.append(
                f"- `{row['family_bucket']}`: ${row['portfolio_net_pnl']:.2f} across {row['trade_count']} trades, win rate {row['win_rate_pct']:.2f}%."
            )
    else:
        lines.append("- none")
    lines.append("")
    lines.append("### QQQ-Only Buckets")
    lines.append("")
    if qqq_buckets:
        for row in qqq_buckets:
            lines.append(
                f"- `{row['family_bucket']}`: ${row['portfolio_net_pnl']:.2f} across {row['trade_count']} trades, win rate {row['win_rate_pct']:.2f}%."
            )
    else:
        lines.append("- none")
    lines.append("")
    lines.append("### Per-Ticker Frozen Leaders")
    lines.append("")
    if per_ticker_buckets:
        for row in per_ticker_buckets:
            lines.append(
                f"- `{row['ticker']}` / `{row['family_bucket']}`: ${row['portfolio_net_pnl']:.2f} across {row['trade_count']} trades, win rate {row['win_rate_pct']:.2f}%."
            )
    else:
        lines.append("- none")
    if failed_tickers:
        lines.append("")
        lines.append("## Failed Tickers")
        lines.append("")
        for row in failed_tickers:
            lines.append(
                f"- `{row['ticker']}`: {row['error_type']} - {row['message']}"
            )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = build_parser().parse_args()
    output_dir = Path(args.output_dir).resolve()
    research_dir = Path(args.research_dir).resolve()
    tickers = [ticker.strip().lower() for ticker in args.tickers.split(",") if ticker.strip()]
    profiles = build_timing_profiles()

    ticker_results: list[dict[str, object]] = []
    failed_tickers: list[dict[str, object]] = []
    for ticker in tickers:
        if args.reuse_completed_tickers:
            reused = try_load_existing_ticker_result(
                ticker=ticker,
                output_dir=output_dir,
                research_dir=research_dir,
                profiles=profiles,
                strategy_set=args.strategy_set,
            )
            if reused is not None:
                ticker_results.append(reused)
                print(
                    f"Reusing {ticker.upper()} existing results from {research_dir}.",
                    flush=True,
                )
                continue
        print(f"Running {ticker.upper()} research...", flush=True)
        try:
            result = run_single_ticker_research(
                ticker=ticker,
                output_dir=output_dir,
                research_dir=research_dir,
                initial_train_days=args.initial_train_days,
                test_days=args.test_days,
                step_days=args.step_days,
                profiles=profiles,
                strategy_set=args.strategy_set,
            )
        except Exception as exc:
            error_row = {
                "ticker": ticker.upper(),
                "error_type": type(exc).__name__,
                "message": str(exc),
            }
            failed_tickers.append(error_row)
            print(
                f"{ticker.upper()} failed: {type(exc).__name__}: {exc}",
                flush=True,
            )
            if not args.continue_on_error:
                raise
            continue
        ticker_results.append(result)
        print(
            f"{ticker.upper()} complete: frozen ${result['summary']['frozen_initial']['final_equity']:.2f}",
            flush=True,
        )

    if not ticker_results:
        raise RuntimeError("all requested tickers failed research")

    common_dates = set(ticker_results[0]["ordered_trade_dates"][args.initial_train_days :])
    combined_candidates, combined_strategy_map = build_combined_promoted_candidates(
        ticker_results=ticker_results,
        oos_dates=common_dates,
    )
    combined_summary, combined_trades, combined_equity = optimize_shared_portfolio(
        candidate_trades=combined_candidates,
        strategy_map=combined_strategy_map,
        risk_caps=[0.08, 0.10, 0.12, 0.15],
    )

    qqq_result = next((result for result in ticker_results if result["ticker"] == "QQQ"), None)
    if qqq_result is None:
        qqq_candidates = pd.DataFrame()
        qqq_trades = pd.DataFrame()
        qqq_equity = pd.DataFrame()
        qqq_summary = None
    else:
        qqq_candidates, qqq_strategy_map = build_combined_promoted_candidates(
            ticker_results=[qqq_result],
            oos_dates=common_dates,
        )
        qqq_summary, qqq_trades, qqq_equity = optimize_shared_portfolio(
            candidate_trades=qqq_candidates,
            strategy_map=qqq_strategy_map,
            risk_caps=[0.08, 0.10, 0.12, 0.15],
        )

    ticker_promotions: list[dict[str, object]] = []
    family_detail_rows: list[dict[str, object]] = []
    family_bucket_rows: list[dict[str, object]] = []
    per_ticker_frozen_bucket_leaders: list[dict[str, object]] = []
    for result in ticker_results:
        summary = result["summary"]
        promoted = summary["promoted"]
        ticker_promotions.append(
            {
                "ticker": result["ticker"],
                "selected_bull": list(promoted["selected_bull"]),
                "selected_bear": list(promoted["selected_bear"]),
                "selected_choppy": list(promoted["selected_choppy"]),
                "regime_threshold_pct": float(promoted["regime_threshold_pct"]),
                "frozen_final_equity": float(summary["frozen_initial"]["final_equity"]),
                "frozen_total_return_pct": float(summary["frozen_initial"]["total_return_pct"]),
                "frozen_max_drawdown_pct": float(summary["frozen_initial"]["max_drawdown_pct"]),
            }
        )
        family_detail_rows.extend(
            build_family_ranking_rows(
                scope="ticker_frozen",
                ticker=result["ticker"],
                summary=summary["frozen_initial"],
                contribution_key="family_contributions",
                label_key="family",
            )
        )
        family_detail_rows.extend(
            build_family_ranking_rows(
                scope="ticker_reoptimized",
                ticker=result["ticker"],
                summary=summary["reoptimized"],
                contribution_key="family_contributions",
                label_key="family",
            )
        )
        family_bucket_rows.extend(
            build_family_ranking_rows(
                scope="ticker_frozen",
                ticker=result["ticker"],
                summary=summary["frozen_initial"],
                contribution_key="family_bucket_contributions",
                label_key="family_bucket",
            )
        )
        family_bucket_rows.extend(
            build_family_ranking_rows(
                scope="ticker_reoptimized",
                ticker=result["ticker"],
                summary=summary["reoptimized"],
                contribution_key="family_bucket_contributions",
                label_key="family_bucket",
            )
        )
        top_bucket = list(summary["frozen_initial"].get("family_bucket_contributions", []))
        if top_bucket:
            leader = dict(top_bucket[0])
            leader["ticker"] = result["ticker"]
            per_ticker_frozen_bucket_leaders.append(leader)

    family_detail_rows.extend(
        build_family_ranking_rows(
            scope="shared_account",
            ticker=None,
            summary=combined_summary,
            contribution_key="family_contributions",
            label_key="family",
        )
    )
    if qqq_summary is not None:
        family_detail_rows.extend(
            build_family_ranking_rows(
                scope="qqq_only",
                ticker="QQQ",
                summary=qqq_summary,
                contribution_key="family_contributions",
                label_key="family",
            )
        )
    family_bucket_rows.extend(
        build_family_ranking_rows(
            scope="shared_account",
            ticker=None,
            summary=combined_summary,
            contribution_key="family_bucket_contributions",
            label_key="family_bucket",
        )
    )
    if qqq_summary is not None:
        family_bucket_rows.extend(
            build_family_ranking_rows(
                scope="qqq_only",
                ticker="QQQ",
                summary=qqq_summary,
                contribution_key="family_bucket_contributions",
                label_key="family_bucket",
            )
        )

    family_detail_rows = sorted(
        family_detail_rows,
        key=lambda row: (row["scope"], -row["portfolio_net_pnl"], -row["trade_count"]),
    )
    family_bucket_rows = sorted(
        family_bucket_rows,
        key=lambda row: (row["scope"], -row["portfolio_net_pnl"], -row["trade_count"]),
    )
    per_ticker_frozen_bucket_leaders = sorted(
        per_ticker_frozen_bucket_leaders,
        key=lambda row: (-float(row["portfolio_net_pnl"]), -int(row["trade_count"])),
    )

    master_payload = {
        "tickers": [ticker.upper() for ticker in tickers],
        "strategy_set": args.strategy_set,
        "successful_tickers": [result["ticker"] for result in ticker_results],
        "failed_tickers": failed_tickers,
        "initial_train_days": args.initial_train_days,
        "test_days": args.test_days,
        "step_days": args.step_days,
        "ticker_promotions": ticker_promotions,
        "shared_account": combined_summary,
        "qqq_only": qqq_summary,
        "relative_return_vs_qqq_only_pct": round(
            float(combined_summary["total_return_pct"]) - float(qqq_summary["total_return_pct"]),
            2,
        ) if qqq_summary is not None else None,
        "family_rankings": {
            "shared_account_families": list(combined_summary.get("family_contributions", [])),
            "shared_account_buckets": list(combined_summary.get("family_bucket_contributions", [])),
            "qqq_only_families": list(qqq_summary.get("family_contributions", [])) if qqq_summary is not None else [],
            "qqq_only_buckets": list(qqq_summary.get("family_bucket_contributions", [])) if qqq_summary is not None else [],
            "per_ticker_frozen_buckets": per_ticker_frozen_bucket_leaders,
        },
    }

    combined_candidates.to_csv(research_dir / "combined_promoted_candidates.csv", index=False)
    combined_trades.to_csv(research_dir / "combined_promoted_portfolio_trades.csv", index=False)
    combined_equity.to_csv(research_dir / "combined_promoted_portfolio_equity.csv", index=False)
    if qqq_summary is not None:
        qqq_candidates.to_csv(research_dir / "qqq_only_promoted_candidates.csv", index=False)
        qqq_trades.to_csv(research_dir / "qqq_only_promoted_portfolio_trades.csv", index=False)
        qqq_equity.to_csv(research_dir / "qqq_only_promoted_portfolio_equity.csv", index=False)
    contribution_rows_to_frame(
        list(combined_summary.get("family_contributions", [])),
        "family",
    ).to_csv(research_dir / "shared_account_family_contributions.csv", index=False)
    contribution_rows_to_frame(
        list(combined_summary.get("family_bucket_contributions", [])),
        "family_bucket",
    ).to_csv(research_dir / "shared_account_family_bucket_contributions.csv", index=False)
    if qqq_summary is not None:
        contribution_rows_to_frame(
            list(qqq_summary.get("family_contributions", [])),
            "family",
        ).to_csv(research_dir / "qqq_only_family_contributions.csv", index=False)
        contribution_rows_to_frame(
            list(qqq_summary.get("family_bucket_contributions", [])),
            "family_bucket",
        ).to_csv(research_dir / "qqq_only_family_bucket_contributions.csv", index=False)
    pd.DataFrame(family_detail_rows).to_csv(research_dir / "family_rankings.csv", index=False)
    pd.DataFrame(family_bucket_rows).to_csv(research_dir / "family_bucket_rankings.csv", index=False)
    (research_dir / "master_summary.json").write_text(json.dumps(master_payload, indent=2), encoding="utf-8")
    write_master_report(research_dir / "master_report.md", master_payload)
    print(json.dumps(master_payload, indent=2))


if __name__ == "__main__":
    main()
