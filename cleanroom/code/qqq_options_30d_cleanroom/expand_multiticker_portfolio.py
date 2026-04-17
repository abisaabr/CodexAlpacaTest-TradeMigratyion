from __future__ import annotations

import copy
import json
import sys
from pathlib import Path
from typing import Any

import pandas as pd

ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parent / "codexalpaca_repo"

sys.path.append(str(ROOT))
sys.path.append(str(REPO_ROOT))

import evaluate_qqq_direct_greeks_readiness as readiness
import run_multiticker_cleanroom_portfolio as mt
from alpaca_lab.multi_ticker_portfolio.config import load_portfolio_config


OUTPUT_DIR = ROOT / "output"
RESEARCH_DIR = OUTPUT_DIR / "multi_ticker_expansion_365d"
BATCH_SUMMARY_PATH = OUTPUT_DIR / "batch_365d_summary.csv"
BASELINE_RESEARCH_DIR = OUTPUT_DIR / "multi_ticker_365d"

CORE_TICKERS = ("qqq", "spy", "iwm", "nvda", "tsla", "msft")
FIRST_PASS_NEW_TICKER_PRIORITY = ("amd", "pltr", "bac", "gld", "xle", "arkk")

SCREEN_MIN_REQUEST_FILL = 99.9
SCREEN_MIN_DENSE_FILL_SELECTED = 97.0
SCREEN_MAX_NEIGHBOR_FILLED_EMPTY_DAYS = 600

LIVE_RISK_CAP = 0.15
LIVE_DAILY_LOSS_GATE = None
LIVE_MAX_OPEN_POSITIONS = 10
LIVE_DELEVER_DRAWDOWN_PCT = 8.0
LIVE_DELEVER_RISK_SCALE = 0.50


def load_batch_screen() -> tuple[pd.DataFrame, list[str]]:
    batch = pd.read_csv(BATCH_SUMMARY_PATH)
    batch["symbol"] = batch["symbol"].astype(str).str.upper()
    batch["is_core"] = batch["symbol"].isin({ticker.upper() for ticker in CORE_TICKERS})
    batch["passes_quality_screen"] = (
        (batch["request_fill_rate"] >= SCREEN_MIN_REQUEST_FILL)
        & (batch["dense_fill_selected_pct"] >= SCREEN_MIN_DENSE_FILL_SELECTED)
        & (batch["neighbor_filled_empty_contract_days"] <= SCREEN_MAX_NEIGHBOR_FILLED_EMPTY_DAYS)
    )
    batch["screen_reason"] = ""
    batch.loc[batch["passes_quality_screen"], "screen_reason"] = "eligible"
    batch.loc[
        (~batch["passes_quality_screen"]) & (batch["dense_fill_selected_pct"] < SCREEN_MIN_DENSE_FILL_SELECTED),
        "screen_reason",
    ] += "dense_fill_selected_pct_below_threshold;"
    batch.loc[
        (~batch["passes_quality_screen"]) & (batch["neighbor_filled_empty_contract_days"] > SCREEN_MAX_NEIGHBOR_FILLED_EMPTY_DAYS),
        "screen_reason",
    ] += "neighbor_fill_too_high;"
    batch.loc[
        (~batch["passes_quality_screen"]) & (batch["request_fill_rate"] < SCREEN_MIN_REQUEST_FILL),
        "screen_reason",
    ] += "request_fill_too_low;"
    eligible_new = batch.loc[
        (~batch["is_core"]) & batch["passes_quality_screen"],
        "symbol",
    ].sort_values().tolist()
    eligible_lower = [ticker.lower() for ticker in eligible_new]
    prioritized = [ticker for ticker in FIRST_PASS_NEW_TICKER_PRIORITY if ticker in eligible_lower]
    return batch, prioritized


def load_cached_result(
    *,
    ticker: str,
    output_dir: Path,
    research_dir: Path,
    profiles: tuple[mt.TimingProfile, ...],
) -> dict[str, Any] | None:
    ticker_lower = ticker.lower()
    candidate_path = research_dir / f"{ticker_lower}_candidate_trades.csv"
    summary_path = research_dir / f"{ticker_lower}_summary.json"
    if not candidate_path.exists() or not summary_path.exists():
        return None

    wide_path = output_dir / f"{ticker_lower}_365d_option_1min_wide_backtest.parquet"
    wide = mt.load_wide_data_for_ticker(wide_path, ticker_lower)
    ordered_trade_dates, day_return_map = mt.build_day_return_map(wide=wide)
    strategy_variants = mt.build_strategy_variants(ticker_lower, profiles)
    strategy_map = {strategy.name: strategy for strategy in strategy_variants}
    candidate_trades = pd.read_csv(candidate_path)
    regime_summary_path = research_dir / f"{ticker_lower}_regime_summary.csv"
    regime_summary = pd.read_csv(regime_summary_path) if regime_summary_path.exists() else mt.summarize_regimes(candidate_trades)
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    return {
        "ticker": ticker.upper(),
        "candidate_trades": candidate_trades,
        "day_return_map": day_return_map,
        "ordered_trade_dates": ordered_trade_dates,
        "strategy_map": strategy_map,
        "regime_summary": regime_summary,
        "summary": summary,
    }


def apply_live_core_promotions(result_map: dict[str, dict[str, Any]]) -> None:
    config = load_portfolio_config(REPO_ROOT / "config" / "multi_ticker_paper_portfolio.yaml")
    grouped: dict[str, dict[str, list[str]]] = {
        ticker.upper(): {"bull": [], "bear": [], "choppy": []}
        for ticker in CORE_TICKERS
    }
    for strategy in config.strategies:
        symbol = strategy.underlying_symbol.upper()
        if symbol not in grouped:
            continue
        grouped[symbol][strategy.regime].append(strategy.name)
    for ticker in CORE_TICKERS:
        result_map[ticker]["summary"]["promoted"] = {
            "ticker": ticker.upper(),
            "regime_threshold_pct": float(result_map[ticker]["summary"]["promoted"]["regime_threshold_pct"]),
            "risk_cap": LIVE_RISK_CAP,
            "selected_bull": grouped[ticker.upper()]["bull"],
            "selected_bear": grouped[ticker.upper()]["bear"],
            "selected_choppy": grouped[ticker.upper()]["choppy"],
        }


def score_row(summary: dict[str, Any]) -> tuple[bool, float, float, float]:
    total_return = float(summary["total_return_pct"])
    max_drawdown = float(summary["max_drawdown_pct"])
    calmar_like = mt.score_drawdown(total_return_pct=total_return, max_drawdown_pct=max_drawdown)
    return (
        total_return > 0.0,
        calmar_like,
        total_return,
        float(summary["final_equity"]),
    )


def summarize_overlay(
    *,
    candidate_trades: pd.DataFrame,
    strategy_map: dict[str, mt.DeltaStrategy],
) -> tuple[dict[str, Any], pd.DataFrame, pd.DataFrame]:
    strategies = mt.strategy_objects_from_names(candidate_trades["strategy"].tolist(), strategy_map)
    if candidate_trades.empty or not strategies:
        summary = mt.empty_summary(mt.DEFAULT_STARTING_EQUITY, LIVE_RISK_CAP)
        summary["calmar_like"] = 0.0
        return summary, pd.DataFrame(), pd.DataFrame()
    trades, equity, summary = readiness.run_overlay_allocator(
        strategies=strategies,
        trades_df=candidate_trades,
        risk_cap=LIVE_RISK_CAP,
        daily_loss_gate_pct=LIVE_DAILY_LOSS_GATE,
        max_open_positions=LIVE_MAX_OPEN_POSITIONS,
        delever_drawdown_pct=LIVE_DELEVER_DRAWDOWN_PCT,
        delever_risk_scale=LIVE_DELEVER_RISK_SCALE,
    )
    summary["calmar_like"] = round(
        mt.score_drawdown(
            total_return_pct=float(summary["total_return_pct"]),
            max_drawdown_pct=float(summary["max_drawdown_pct"]),
        ),
        4,
    )
    return summary, trades, equity


def combined_for_tickers(
    *,
    selected_tickers: list[str],
    result_map: dict[str, dict[str, Any]],
    common_oos_dates: set[object],
) -> tuple[pd.DataFrame, dict[str, mt.DeltaStrategy]]:
    results = [result_map[ticker] for ticker in selected_tickers]
    return mt.build_combined_promoted_candidates(
        ticker_results=results,
        oos_dates=common_oos_dates,
    )


def greedy_expand(
    *,
    baseline_tickers: list[str],
    candidate_tickers: list[str],
    result_map: dict[str, dict[str, Any]],
    common_oos_dates: set[object],
) -> tuple[list[str], list[dict[str, Any]], dict[str, Any], pd.DataFrame, pd.DataFrame]:
    selected = list(baseline_tickers)
    remaining = [ticker for ticker in candidate_tickers if ticker not in selected]
    baseline_candidates, baseline_strategy_map = combined_for_tickers(
        selected_tickers=selected,
        result_map=result_map,
        common_oos_dates=common_oos_dates,
    )
    current_summary, current_trades, current_equity = summarize_overlay(
        candidate_trades=baseline_candidates,
        strategy_map=baseline_strategy_map,
    )
    current_summary["selected_tickers"] = [ticker.upper() for ticker in selected]

    add_rows: list[dict[str, Any]] = []
    improved = True
    while remaining and improved:
        improved = False
        best_trial: dict[str, Any] | None = None
        for ticker in remaining:
            trial_selected = selected + [ticker]
            trial_candidates, trial_strategy_map = combined_for_tickers(
                selected_tickers=trial_selected,
                result_map=result_map,
                common_oos_dates=common_oos_dates,
            )
            trial_summary, _, _ = summarize_overlay(
                candidate_trades=trial_candidates,
                strategy_map=trial_strategy_map,
            )
            row = {
                "base_tickers": ",".join(item.upper() for item in selected),
                "trial_add": ticker.upper(),
                "trial_tickers": ",".join(item.upper() for item in trial_selected),
                "final_equity": float(trial_summary["final_equity"]),
                "total_return_pct": float(trial_summary["total_return_pct"]),
                "trade_count": int(trial_summary["trade_count"]),
                "win_rate_pct": float(trial_summary["win_rate_pct"]),
                "max_drawdown_pct": float(trial_summary["max_drawdown_pct"]),
                "calmar_like": float(trial_summary["calmar_like"]),
                "return_delta_pct": float(trial_summary["total_return_pct"]) - float(current_summary["total_return_pct"]),
                "drawdown_delta_pct": float(trial_summary["max_drawdown_pct"]) - float(current_summary["max_drawdown_pct"]),
            }
            add_rows.append(row)
            trial_score = score_row(trial_summary)
            current_score = score_row(current_summary)
            if trial_score <= current_score:
                continue
            if float(trial_summary["final_equity"]) <= float(current_summary["final_equity"]):
                continue
            if best_trial is None or trial_score > score_row(best_trial["summary"]):
                best_trial = {
                    "ticker": ticker,
                    "summary": trial_summary,
                }
        if best_trial is None:
            break
        selected.append(best_trial["ticker"])
        remaining.remove(best_trial["ticker"])
        combined_candidates, combined_strategy_map = combined_for_tickers(
            selected_tickers=selected,
            result_map=result_map,
            common_oos_dates=common_oos_dates,
        )
        current_summary, current_trades, current_equity = summarize_overlay(
            candidate_trades=combined_candidates,
            strategy_map=combined_strategy_map,
        )
        current_summary["selected_tickers"] = [ticker.upper() for ticker in selected]
        improved = True

    return selected, add_rows, current_summary, current_trades, current_equity


def try_prune(
    *,
    selected_tickers: list[str],
    baseline_core: list[str],
    result_map: dict[str, dict[str, Any]],
    common_oos_dates: set[object],
    current_summary: dict[str, Any],
) -> tuple[list[str], dict[str, Any], pd.DataFrame, pd.DataFrame]:
    selected = list(selected_tickers)
    improved = True
    best_summary = current_summary
    best_trades = pd.DataFrame()
    best_equity = pd.DataFrame()
    while improved:
        improved = False
        added = [ticker for ticker in selected if ticker not in baseline_core]
        for ticker in added:
            trial_selected = [item for item in selected if item != ticker]
            trial_candidates, trial_strategy_map = combined_for_tickers(
                selected_tickers=trial_selected,
                result_map=result_map,
                common_oos_dates=common_oos_dates,
            )
            trial_summary, trial_trades, trial_equity = summarize_overlay(
                candidate_trades=trial_candidates,
                strategy_map=trial_strategy_map,
            )
            if score_row(trial_summary) > score_row(best_summary):
                selected = trial_selected
                best_summary = trial_summary
                best_trades = trial_trades
                best_equity = trial_equity
                improved = True
                break
    if best_trades.empty:
        combined_candidates, combined_strategy_map = combined_for_tickers(
            selected_tickers=selected,
            result_map=result_map,
            common_oos_dates=common_oos_dates,
        )
        best_summary, best_trades, best_equity = summarize_overlay(
            candidate_trades=combined_candidates,
            strategy_map=combined_strategy_map,
        )
    best_summary["selected_tickers"] = [ticker.upper() for ticker in selected]
    return selected, best_summary, best_trades, best_equity


def prune_selected_strategies(
    *,
    selected_tickers: list[str],
    result_map: dict[str, dict[str, Any]],
    common_oos_dates: set[object],
    current_summary: dict[str, Any],
) -> tuple[list[str], dict[str, Any], pd.DataFrame, pd.DataFrame, list[dict[str, Any]]]:
    selected = list(selected_tickers)
    current_state = copy.deepcopy(result_map)
    best_summary = current_summary
    best_trades = pd.DataFrame()
    best_equity = pd.DataFrame()
    prune_rows: list[dict[str, Any]] = []

    improved = True
    while improved:
        improved = False
        best_trial: dict[str, Any] | None = None
        for ticker in selected:
            promoted = current_state[ticker]["summary"]["promoted"]
            for regime_key in ["selected_bull", "selected_bear", "selected_choppy"]:
                current_names = list(promoted[regime_key])
                if len(current_names) <= 1:
                    continue
                for name in current_names:
                    trial_state = copy.deepcopy(current_state)
                    trial_state[ticker]["summary"]["promoted"][regime_key] = [
                        item for item in current_names if item != name
                    ]
                    trial_candidates, trial_strategy_map = combined_for_tickers(
                        selected_tickers=selected,
                        result_map=trial_state,
                        common_oos_dates=common_oos_dates,
                    )
                    trial_summary, trial_trades, trial_equity = summarize_overlay(
                        candidate_trades=trial_candidates,
                        strategy_map=trial_strategy_map,
                    )
                    row = {
                        "ticker": ticker.upper(),
                        "regime_key": regime_key,
                        "removed_strategy": name,
                        "final_equity": float(trial_summary["final_equity"]),
                        "total_return_pct": float(trial_summary["total_return_pct"]),
                        "trade_count": int(trial_summary["trade_count"]),
                        "win_rate_pct": float(trial_summary["win_rate_pct"]),
                        "max_drawdown_pct": float(trial_summary["max_drawdown_pct"]),
                        "calmar_like": float(trial_summary["calmar_like"]),
                        "return_delta_pct": float(trial_summary["total_return_pct"]) - float(best_summary["total_return_pct"]),
                        "drawdown_delta_pct": float(trial_summary["max_drawdown_pct"]) - float(best_summary["max_drawdown_pct"]),
                    }
                    prune_rows.append(row)
                    if score_row(trial_summary) <= score_row(best_summary):
                        continue
                    if best_trial is None or score_row(trial_summary) > score_row(best_trial["summary"]):
                        best_trial = {
                            "ticker": ticker,
                            "regime_key": regime_key,
                            "removed_strategy": name,
                            "summary": trial_summary,
                            "trades": trial_trades,
                            "equity": trial_equity,
                            "state": trial_state,
                        }
        if best_trial is None:
            break
        current_state = best_trial["state"]
        best_summary = best_trial["summary"]
        best_trades = best_trial["trades"]
        best_equity = best_trial["equity"]
        improved = True

    selected = [
        ticker
        for ticker in selected
        if any(
            current_state[ticker]["summary"]["promoted"][regime_key]
            for regime_key in ["selected_bull", "selected_bear", "selected_choppy"]
        )
    ]
    if best_trades.empty:
        final_candidates, final_strategy_map = combined_for_tickers(
            selected_tickers=selected,
            result_map=current_state,
            common_oos_dates=common_oos_dates,
        )
        best_summary, best_trades, best_equity = summarize_overlay(
            candidate_trades=final_candidates,
            strategy_map=final_strategy_map,
        )
    best_summary["selected_tickers"] = [ticker.upper() for ticker in selected]
    for ticker in selected:
        result_map[ticker]["summary"]["promoted"] = current_state[ticker]["summary"]["promoted"]
    return selected, best_summary, best_trades, best_equity, prune_rows


def write_report(
    *,
    path: Path,
    screen_df: pd.DataFrame,
    candidate_summary_df: pd.DataFrame,
    baseline_summary: dict[str, Any],
    final_summary: dict[str, Any],
    full_union_summary: dict[str, Any],
    added_tickers: list[str],
) -> None:
    lines: list[str] = []
    lines.append("# Multi-Ticker Expansion Report")
    lines.append("")
    lines.append("## Screening")
    lines.append("")
    eligible_new = screen_df.loc[(~screen_df["is_core"]) & screen_df["passes_quality_screen"], "symbol"].tolist()
    deferred = screen_df.loc[(~screen_df["is_core"]) & (~screen_df["passes_quality_screen"]), "symbol"].tolist()
    lines.append(f"- Eligible new tickers: {', '.join(f'`{ticker}`' for ticker in eligible_new) if eligible_new else 'none'}")
    lines.append(f"- Deferred for later due to data quality: {', '.join(f'`{ticker}`' for ticker in deferred) if deferred else 'none'}")
    lines.append("")
    lines.append("## Baseline")
    lines.append("")
    lines.append(
        f"- Current core set (`{', '.join(CORE_TICKERS).upper()}`): ${baseline_summary['final_equity']:.2f}, {baseline_summary['total_return_pct']:.2f}%, drawdown {baseline_summary['max_drawdown_pct']:.2f}%."
    )
    lines.append(
        f"- Full screened union: ${full_union_summary['final_equity']:.2f}, {full_union_summary['total_return_pct']:.2f}%, drawdown {full_union_summary['max_drawdown_pct']:.2f}%."
    )
    lines.append(
        f"- Final promoted expansion after strategy pruning: ${final_summary['final_equity']:.2f}, {final_summary['total_return_pct']:.2f}%, drawdown {final_summary['max_drawdown_pct']:.2f}%."
    )
    lines.append("")
    lines.append("## Added Tickers")
    lines.append("")
    lines.append(
        f"- {', '.join(f'`{ticker.upper()}`' for ticker in added_tickers) if added_tickers else 'No new tickers improved the live shared-account score.'}"
    )
    lines.append("")
    lines.append("## New Ticker Standalone OOS Results")
    lines.append("")
    for row in candidate_summary_df.itertuples(index=False):
        lines.append(
            f"- `{row.ticker}`: {row.frozen_total_return_pct:.2f}% standalone OOS return, drawdown {row.frozen_max_drawdown_pct:.2f}%, promoted bull {row.selected_bull_count}, bear {row.selected_bear_count}, choppy {row.selected_choppy_count}."
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    RESEARCH_DIR.mkdir(parents=True, exist_ok=True)
    screen_df, screened_new_tickers = load_batch_screen()
    screen_df.to_csv(RESEARCH_DIR / "screening_summary.csv", index=False)

    profiles = mt.build_timing_profiles()
    all_tickers = list(CORE_TICKERS) + screened_new_tickers
    result_map: dict[str, dict[str, Any]] = {}
    standalone_rows: list[dict[str, Any]] = []

    for ticker in all_tickers:
        cached = load_cached_result(
            ticker=ticker,
            output_dir=OUTPUT_DIR,
            research_dir=RESEARCH_DIR,
            profiles=profiles,
        )
        if cached is None and ticker in CORE_TICKERS:
            cached = load_cached_result(
                ticker=ticker,
                output_dir=OUTPUT_DIR,
                research_dir=BASELINE_RESEARCH_DIR,
                profiles=profiles,
            )
        if cached is not None:
            print(f"Loaded cached research for {ticker.upper()}.", flush=True)
            result = cached
        else:
            print(f"Running expansion research for {ticker.upper()}...", flush=True)
            result = mt.run_single_ticker_research(
                ticker=ticker,
                output_dir=OUTPUT_DIR,
                research_dir=RESEARCH_DIR,
                initial_train_days=mt.DEFAULT_INITIAL_TRAIN_DAYS,
                test_days=mt.DEFAULT_TEST_DAYS,
                step_days=mt.DEFAULT_STEP_DAYS,
                profiles=profiles,
            )
        result_map[ticker] = result
        summary = result["summary"]
        promoted = summary["promoted"]
        standalone_rows.append(
            {
                "ticker": ticker.upper(),
                "is_core": ticker in CORE_TICKERS,
                "frozen_final_equity": float(summary["frozen_initial"]["final_equity"]),
                "frozen_total_return_pct": float(summary["frozen_initial"]["total_return_pct"]),
                "frozen_max_drawdown_pct": float(summary["frozen_initial"]["max_drawdown_pct"]),
                "selected_bull_count": len(promoted["selected_bull"]),
                "selected_bear_count": len(promoted["selected_bear"]),
                "selected_choppy_count": len(promoted["selected_choppy"]),
                "selected_bull": ",".join(promoted["selected_bull"]),
                "selected_bear": ",".join(promoted["selected_bear"]),
                "selected_choppy": ",".join(promoted["selected_choppy"]),
                "regime_threshold_pct": float(promoted["regime_threshold_pct"]),
            }
        )

    apply_live_core_promotions(result_map)

    post_train_sets = [
        set(result["ordered_trade_dates"][mt.DEFAULT_INITIAL_TRAIN_DAYS :])
        for result in result_map.values()
    ]
    common_oos_dates = set.intersection(*post_train_sets) if post_train_sets else set()
    if not common_oos_dates:
        raise RuntimeError("no common OOS dates across expansion universe")

    baseline_candidates, baseline_strategy_map = combined_for_tickers(
        selected_tickers=list(CORE_TICKERS),
        result_map=result_map,
        common_oos_dates=common_oos_dates,
    )
    baseline_summary, baseline_trades, baseline_equity = summarize_overlay(
        candidate_trades=baseline_candidates,
        strategy_map=baseline_strategy_map,
    )
    baseline_summary["selected_tickers"] = [ticker.upper() for ticker in CORE_TICKERS]

    full_union_candidates, full_union_strategy_map = combined_for_tickers(
        selected_tickers=all_tickers,
        result_map=result_map,
        common_oos_dates=common_oos_dates,
    )
    full_union_summary, full_union_trades, full_union_equity = summarize_overlay(
        candidate_trades=full_union_candidates,
        strategy_map=full_union_strategy_map,
    )
    full_union_summary["selected_tickers"] = [ticker.upper() for ticker in all_tickers]

    selected_tickers, add_rows, greedy_summary, greedy_trades, greedy_equity = greedy_expand(
        baseline_tickers=list(CORE_TICKERS),
        candidate_tickers=screened_new_tickers,
        result_map=result_map,
        common_oos_dates=common_oos_dates,
    )
    selected_tickers, final_summary, final_trades, final_equity = try_prune(
        selected_tickers=selected_tickers,
        baseline_core=list(CORE_TICKERS),
        result_map=result_map,
        common_oos_dates=common_oos_dates,
        current_summary=greedy_summary,
    )
    selected_tickers, final_summary, final_trades, final_equity, prune_rows = prune_selected_strategies(
        selected_tickers=selected_tickers,
        result_map=result_map,
        common_oos_dates=common_oos_dates,
        current_summary=final_summary,
    )

    standalone_df = pd.DataFrame(standalone_rows).sort_values(
        ["is_core", "frozen_total_return_pct", "frozen_final_equity"],
        ascending=[False, False, False],
    )
    add_df = pd.DataFrame(add_rows).sort_values(
        ["calmar_like", "final_equity", "total_return_pct"],
        ascending=[False, False, False],
    )
    prune_df = pd.DataFrame(prune_rows).sort_values(
        ["calmar_like", "final_equity", "total_return_pct"],
        ascending=[False, False, False],
    )

    added_tickers = [ticker for ticker in selected_tickers if ticker not in CORE_TICKERS]
    final_results = [result_map[ticker] for ticker in selected_tickers]
    final_promotions: list[dict[str, Any]] = []
    for result in final_results:
        promoted = result["summary"]["promoted"]
        final_promotions.append(
            {
                "ticker": result["ticker"],
                "selected_bull": list(promoted["selected_bull"]),
                "selected_bear": list(promoted["selected_bear"]),
                "selected_choppy": list(promoted["selected_choppy"]),
                "regime_threshold_pct": float(promoted["regime_threshold_pct"]),
            }
        )

    payload = {
        "core_tickers": [ticker.upper() for ticker in CORE_TICKERS],
        "screened_new_tickers": [ticker.upper() for ticker in screened_new_tickers],
        "common_oos_date_count": len(common_oos_dates),
        "baseline_live_overlay": baseline_summary,
        "full_screened_union": full_union_summary,
        "selected_tickers": [ticker.upper() for ticker in selected_tickers],
        "added_tickers": [ticker.upper() for ticker in added_tickers],
        "final_live_overlay": final_summary,
        "final_promotions": final_promotions,
    }

    standalone_df.to_csv(RESEARCH_DIR / "candidate_standalone_summary.csv", index=False)
    add_df.to_csv(RESEARCH_DIR / "greedy_addition_trials.csv", index=False)
    prune_df.to_csv(RESEARCH_DIR / "strategy_prune_trials.csv", index=False)
    baseline_trades.to_csv(RESEARCH_DIR / "baseline_portfolio_trades.csv", index=False)
    baseline_equity.to_csv(RESEARCH_DIR / "baseline_portfolio_equity.csv", index=False)
    full_union_trades.to_csv(RESEARCH_DIR / "full_union_portfolio_trades.csv", index=False)
    full_union_equity.to_csv(RESEARCH_DIR / "full_union_portfolio_equity.csv", index=False)
    final_trades.to_csv(RESEARCH_DIR / "final_portfolio_trades.csv", index=False)
    final_equity.to_csv(RESEARCH_DIR / "final_portfolio_equity.csv", index=False)
    (RESEARCH_DIR / "expansion_summary.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    write_report(
        path=RESEARCH_DIR / "expansion_report.md",
        screen_df=screen_df,
        candidate_summary_df=standalone_df.loc[~standalone_df["is_core"]].reset_index(drop=True),
        baseline_summary=baseline_summary,
        final_summary=final_summary,
        full_union_summary=full_union_summary,
        added_tickers=added_tickers,
    )
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
