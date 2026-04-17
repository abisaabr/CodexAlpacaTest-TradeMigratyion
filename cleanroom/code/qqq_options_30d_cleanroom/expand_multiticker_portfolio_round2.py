from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import pandas as pd

ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parent / "codexalpaca_repo"

sys.path.append(str(ROOT))
sys.path.append(str(REPO_ROOT))

import expand_multiticker_portfolio as exp
import run_multiticker_cleanroom_portfolio as mt
from alpaca_lab.multi_ticker_portfolio.config import load_portfolio_config


OUTPUT_DIR = ROOT / "output"
RESEARCH_DIR = OUTPUT_DIR / "multi_ticker_expansion_round2_365d"
PREVIOUS_RESEARCH_DIR = OUTPUT_DIR / "multi_ticker_expansion_365d"
BATCH_SUMMARY_PATH = OUTPUT_DIR / "batch_365d_summary.csv"
SECOND_CHANCE_TICKERS = ("tlt", "slv")


def load_current_live_tickers() -> list[str]:
    config = load_portfolio_config(REPO_ROOT / "config" / "multi_ticker_paper_portfolio.yaml")
    tickers = sorted({strategy.underlying_symbol.lower() for strategy in config.strategies})
    if not tickers:
        raise RuntimeError("current live portfolio has no strategies configured")
    return tickers


def load_batch_summary() -> pd.DataFrame:
    batch = pd.read_csv(BATCH_SUMMARY_PATH).copy()
    batch["symbol"] = batch["symbol"].astype(str).str.upper()
    numeric_cols = [
        "selected_contract_days",
        "unique_contracts",
        "request_fill_rate",
        "dense_fill_selected_pct",
        "dense_fill_nonempty_pct",
        "neighbor_filled_empty_contract_days",
    ]
    for column in numeric_cols:
        batch[column] = pd.to_numeric(batch[column], errors="coerce")
    batch["ticker"] = batch["symbol"].str.lower()
    return batch


def load_cached_universe() -> set[str]:
    tickers = set()
    for path in OUTPUT_DIR.glob("*_365d_audit_report.json"):
        tickers.add(path.name.replace("_365d_audit_report.json", "").lower())
    return tickers


def select_round2_candidates(
    *,
    batch: pd.DataFrame,
    live_tickers: list[str],
    cached_tickers: set[str],
) -> tuple[pd.DataFrame, list[str]]:
    live_set = set(live_tickers)
    screen = batch.copy()
    screen["is_live"] = screen["ticker"].isin(live_set)
    screen["is_cached"] = screen["ticker"].isin(cached_tickers)
    screen["passes_primary_screen"] = (
        (screen["request_fill_rate"] >= exp.SCREEN_MIN_REQUEST_FILL)
        & (screen["dense_fill_selected_pct"] >= exp.SCREEN_MIN_DENSE_FILL_SELECTED)
        & (screen["neighbor_filled_empty_contract_days"] <= exp.SCREEN_MAX_NEIGHBOR_FILLED_EMPTY_DAYS)
    )
    screen["is_second_chance"] = screen["ticker"].isin(SECOND_CHANCE_TICKERS)
    screen["selected_for_round2"] = (
        screen["is_cached"]
        & (~screen["is_live"])
        & (screen["passes_primary_screen"] | screen["is_second_chance"])
    )
    screen["candidate_tier"] = "excluded"
    screen.loc[screen["selected_for_round2"] & screen["passes_primary_screen"], "candidate_tier"] = "primary"
    screen.loc[screen["selected_for_round2"] & screen["is_second_chance"], "candidate_tier"] = "second_chance"

    primary = (
        screen.loc[screen["candidate_tier"] == "primary", "ticker"]
        .sort_values()
        .tolist()
    )
    second = [ticker for ticker in SECOND_CHANCE_TICKERS if ticker in screen.loc[screen["candidate_tier"] == "second_chance", "ticker"].tolist()]
    return screen, primary + [ticker for ticker in second if ticker not in primary]


def load_or_run_result(
    *,
    ticker: str,
    profiles: tuple[mt.TimingProfile, ...],
) -> dict[str, Any]:
    for research_dir in (RESEARCH_DIR, PREVIOUS_RESEARCH_DIR, exp.BASELINE_RESEARCH_DIR):
        cached = exp.load_cached_result(
            ticker=ticker,
            output_dir=OUTPUT_DIR,
            research_dir=research_dir,
            profiles=profiles,
        )
        if cached is not None:
            print(f"Loaded cached research for {ticker.upper()} from {research_dir.name}.", flush=True)
            return cached
    print(f"Running round-two research for {ticker.upper()}...", flush=True)
    return mt.run_single_ticker_research(
        ticker=ticker,
        output_dir=OUTPUT_DIR,
        research_dir=RESEARCH_DIR,
        initial_train_days=mt.DEFAULT_INITIAL_TRAIN_DAYS,
        test_days=mt.DEFAULT_TEST_DAYS,
        step_days=mt.DEFAULT_STEP_DAYS,
        profiles=profiles,
    )


def build_standalone_rows(
    *,
    result_map: dict[str, dict[str, Any]],
    live_tickers: list[str],
    candidate_screen: pd.DataFrame,
) -> list[dict[str, Any]]:
    tier_map = dict(zip(candidate_screen["ticker"], candidate_screen["candidate_tier"]))
    rows: list[dict[str, Any]] = []
    for ticker, result in result_map.items():
        summary = result["summary"]
        promoted = summary["promoted"]
        rows.append(
            {
                "ticker": ticker.upper(),
                "is_live": ticker in live_tickers,
                "candidate_tier": tier_map.get(ticker, "live"),
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
    return rows


def write_report(
    *,
    path: Path,
    candidate_screen: pd.DataFrame,
    candidate_summary_df: pd.DataFrame,
    baseline_summary: dict[str, Any],
    final_summary: dict[str, Any],
    full_union_summary: dict[str, Any],
    live_tickers: list[str],
    added_tickers: list[str],
) -> None:
    primary = candidate_screen.loc[candidate_screen["candidate_tier"] == "primary", "symbol"].tolist()
    second_chance = candidate_screen.loc[candidate_screen["candidate_tier"] == "second_chance", "symbol"].tolist()
    lines: list[str] = []
    lines.append("# Multi-Ticker Expansion Round 2 Report")
    lines.append("")
    lines.append("## Candidate Universe")
    lines.append("")
    lines.append(f"- Current live tickers: {', '.join(f'`{ticker.upper()}`' for ticker in live_tickers)}")
    lines.append(f"- Primary cached candidates: {', '.join(f'`{ticker}`' for ticker in primary) if primary else 'none'}")
    lines.append(f"- Second-chance candidates: {', '.join(f'`{ticker}`' for ticker in second_chance) if second_chance else 'none'}")
    lines.append("")
    lines.append("## Shared Account")
    lines.append("")
    lines.append(
        f"- Current live baseline: ${baseline_summary['final_equity']:.2f}, {baseline_summary['total_return_pct']:.2f}%, drawdown {baseline_summary['max_drawdown_pct']:.2f}%."
    )
    lines.append(
        f"- Full candidate union: ${full_union_summary['final_equity']:.2f}, {full_union_summary['total_return_pct']:.2f}%, drawdown {full_union_summary['max_drawdown_pct']:.2f}%."
    )
    lines.append(
        f"- Final promoted round-two overlay: ${final_summary['final_equity']:.2f}, {final_summary['total_return_pct']:.2f}%, drawdown {final_summary['max_drawdown_pct']:.2f}%."
    )
    lines.append("")
    lines.append("## Added Tickers")
    lines.append("")
    lines.append(
        f"- {', '.join(f'`{ticker.upper()}`' for ticker in added_tickers) if added_tickers else 'No round-two ticker improved the live shared-account score.'}"
    )
    lines.append("")
    lines.append("## Standalone OOS Results")
    lines.append("")
    for row in candidate_summary_df.itertuples(index=False):
        lines.append(
            f"- `{row.ticker}` ({row.candidate_tier}): {row.frozen_total_return_pct:.2f}% return, drawdown {row.frozen_max_drawdown_pct:.2f}%, promoted bull {row.selected_bull_count}, bear {row.selected_bear_count}, choppy {row.selected_choppy_count}."
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    RESEARCH_DIR.mkdir(parents=True, exist_ok=True)
    profiles = mt.build_timing_profiles()
    live_tickers = load_current_live_tickers()
    batch = load_batch_summary()
    cached_tickers = load_cached_universe()
    candidate_screen, candidate_tickers = select_round2_candidates(
        batch=batch,
        live_tickers=live_tickers,
        cached_tickers=cached_tickers,
    )
    candidate_screen.to_csv(RESEARCH_DIR / "candidate_screening_summary.csv", index=False)

    all_tickers = live_tickers + [ticker for ticker in candidate_tickers if ticker not in live_tickers]
    result_map: dict[str, dict[str, Any]] = {}
    for ticker in all_tickers:
        result_map[ticker] = load_or_run_result(ticker=ticker, profiles=profiles)

    post_train_sets = [
        set(result["ordered_trade_dates"][mt.DEFAULT_INITIAL_TRAIN_DAYS :])
        for result in result_map.values()
    ]
    common_oos_dates = set.intersection(*post_train_sets) if post_train_sets else set()
    if not common_oos_dates:
        raise RuntimeError("no common OOS dates across round-two universe")

    baseline_candidates, baseline_strategy_map = exp.combined_for_tickers(
        selected_tickers=live_tickers,
        result_map=result_map,
        common_oos_dates=common_oos_dates,
    )
    baseline_summary, baseline_trades, baseline_equity = exp.summarize_overlay(
        candidate_trades=baseline_candidates,
        strategy_map=baseline_strategy_map,
    )
    baseline_summary["selected_tickers"] = [ticker.upper() for ticker in live_tickers]

    full_union_candidates, full_union_strategy_map = exp.combined_for_tickers(
        selected_tickers=all_tickers,
        result_map=result_map,
        common_oos_dates=common_oos_dates,
    )
    full_union_summary, full_union_trades, full_union_equity = exp.summarize_overlay(
        candidate_trades=full_union_candidates,
        strategy_map=full_union_strategy_map,
    )
    full_union_summary["selected_tickers"] = [ticker.upper() for ticker in all_tickers]

    selected_tickers, add_rows, greedy_summary, _greedy_trades, _greedy_equity = exp.greedy_expand(
        baseline_tickers=live_tickers,
        candidate_tickers=candidate_tickers,
        result_map=result_map,
        common_oos_dates=common_oos_dates,
    )
    selected_tickers, final_summary, final_trades, final_equity = exp.try_prune(
        selected_tickers=selected_tickers,
        baseline_core=live_tickers,
        result_map=result_map,
        common_oos_dates=common_oos_dates,
        current_summary=greedy_summary,
    )
    selected_tickers, final_summary, final_trades, final_equity, prune_rows = exp.prune_selected_strategies(
        selected_tickers=selected_tickers,
        result_map=result_map,
        common_oos_dates=common_oos_dates,
        current_summary=final_summary,
    )

    standalone_df = pd.DataFrame(
        build_standalone_rows(
            result_map=result_map,
            live_tickers=live_tickers,
            candidate_screen=candidate_screen,
        )
    ).sort_values(
        ["is_live", "frozen_total_return_pct", "frozen_final_equity"],
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

    added_tickers = [ticker for ticker in selected_tickers if ticker not in live_tickers]
    final_promotions: list[dict[str, Any]] = []
    for ticker in selected_tickers:
        result = result_map[ticker]
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
        "current_live_tickers": [ticker.upper() for ticker in live_tickers],
        "round2_candidate_tickers": [ticker.upper() for ticker in candidate_tickers],
        "common_oos_date_count": len(common_oos_dates),
        "baseline_live_overlay": baseline_summary,
        "full_candidate_union": full_union_summary,
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
    (RESEARCH_DIR / "round2_summary.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    write_report(
        path=RESEARCH_DIR / "round2_report.md",
        candidate_screen=candidate_screen,
        candidate_summary_df=standalone_df.loc[~standalone_df["is_live"]].reset_index(drop=True),
        baseline_summary=baseline_summary,
        final_summary=final_summary,
        full_union_summary=full_union_summary,
        live_tickers=live_tickers,
        added_tickers=added_tickers,
    )
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
