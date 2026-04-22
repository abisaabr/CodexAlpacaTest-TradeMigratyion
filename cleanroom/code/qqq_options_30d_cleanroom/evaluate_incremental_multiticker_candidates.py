from __future__ import annotations

import argparse
import itertools
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
import expand_multiticker_portfolio_round2 as round2
import run_multiticker_cleanroom_portfolio as mt


DEFAULT_OUTPUT_DIR = ROOT / "output" / "candidate_incremental_eval_365d"
INCREMENTAL_RESULT_COLUMNS = [
    "candidate",
    "common_oos_date_count",
    "baseline_final_equity",
    "trial_final_equity",
    "equity_delta",
    "baseline_total_return_pct",
    "trial_total_return_pct",
    "return_delta_pct",
    "baseline_max_drawdown_pct",
    "trial_max_drawdown_pct",
    "drawdown_delta_pct",
    "baseline_calmar_like",
    "trial_calmar_like",
    "calmar_delta",
    "improved",
]
COMBO_RESULT_COLUMNS = [
    "added_tickers",
    "added_count",
    "common_oos_date_count",
    "final_equity",
    "total_return_pct",
    "trade_count",
    "win_rate_pct",
    "max_drawdown_pct",
    "calmar_like",
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Evaluate candidate tickers incrementally against the current live shared-account book."
    )
    parser.add_argument(
        "--candidates",
        required=True,
        help="Comma-separated candidate tickers to test incrementally.",
    )
    parser.add_argument(
        "--output-dir",
        default=str(DEFAULT_OUTPUT_DIR),
        help="Directory for evaluation outputs.",
    )
    parser.add_argument(
        "--top-combo-count",
        type=int,
        default=4,
        help="Maximum number of top incremental winners to include in combo sweeps.",
    )
    parser.add_argument(
        "--candidate-source-json",
        default="",
        help="Optional JSON file describing fresh candidate research artifacts to prefer over legacy cached results.",
    )
    return parser


def _normalize_tickers(raw: str) -> list[str]:
    return [ticker.strip().lower() for ticker in raw.split(",") if ticker.strip()]


def _load_candidate_source_map(path: Path | None) -> dict[str, dict[str, Any]]:
    if path is None or not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, dict):
        rows = payload.values()
    elif isinstance(payload, list):
        rows = payload
    else:
        return {}

    source_map: dict[str, dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        ticker = str(row.get("ticker", "")).strip().lower()
        if not ticker:
            continue
        source_map[ticker] = row
    return source_map


def _profiles_for_summary(summary: dict[str, Any]) -> tuple[mt.TimingProfile, ...]:
    strategy_set = str(summary.get("strategy_set", "standard") or "standard")
    available_profiles = {profile.name: profile for profile in mt.build_timing_profiles(strategy_set=strategy_set)}
    requested = [str(name).strip() for name in (summary.get("timing_profiles") or []) if str(name).strip()]
    if not requested:
        return tuple(available_profiles.values())
    selected = [available_profiles[name] for name in requested if name in available_profiles]
    return tuple(selected or available_profiles.values())


def _wide_path_candidates(ticker: str, source_row: dict[str, Any], research_dir: Path) -> list[Path]:
    ticker_lower = ticker.lower()
    candidates: list[Path] = []
    explicit = str(source_row.get("wide_parquet_path", "")).strip()
    if explicit:
        candidates.append(Path(explicit))
    input_workspace = research_dir / "input_workspace"
    candidates.append(input_workspace / f"{ticker_lower}_365d_option_1min_wide_backtest.parquet")
    candidates.append(ROOT / "output" / "backtester_ready" / f"{ticker_lower}" / f"{ticker_lower}_365d_option_1min_wide_backtest.parquet")
    candidates.append(ROOT / "output" / f"{ticker_lower}_365d_option_1min_wide_backtest.parquet")
    return candidates


def _load_result_from_source_row(ticker: str, source_row: dict[str, Any]) -> dict[str, Any]:
    ticker_lower = ticker.lower()
    ticker_upper = ticker.upper()
    research_dir = Path(str(source_row.get("research_dir", "")).strip()).resolve()
    if not research_dir.exists():
        raise FileNotFoundError(f"research_dir not found for {ticker_upper}: {research_dir}")

    summary_path_raw = str(source_row.get("summary_path", "")).strip()
    summary_path = Path(summary_path_raw).resolve() if summary_path_raw else (research_dir / f"{ticker_lower}_summary.json")

    if not summary_path.exists():
        raise FileNotFoundError(f"summary_path not found for {ticker.upper()}: {summary_path}")

    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    profiles = _profiles_for_summary(summary)
    strategy_set = str(summary.get("strategy_set", "standard") or "standard")
    selection_profile = str(summary.get("selection_profile", mt.DEFAULT_SELECTION_PROFILE) or mt.DEFAULT_SELECTION_PROFILE)
    family_include_filters = [str(item).strip() for item in (summary.get("family_include_filters") or []) if str(item).strip()]
    family_exclude_filters = [str(item).strip() for item in (summary.get("family_exclude_filters") or []) if str(item).strip()]

    wide_path = next((path for path in _wide_path_candidates(ticker_lower, source_row, research_dir) if path.exists()), None)
    if wide_path is None:
        raise FileNotFoundError(f"wide parquet not found for {ticker.upper()} under {research_dir}")
    result = mt.try_load_existing_ticker_result(
        ticker=ticker_lower,
        output_dir=wide_path.parent,
        research_dir=research_dir,
        profiles=profiles,
        strategy_set=strategy_set,
        selection_profile=selection_profile,
        family_include_filters=family_include_filters,
        family_exclude_filters=family_exclude_filters,
    )
    if result is None:
        raise RuntimeError(
            f"could not rehydrate {ticker_upper} from fresh research artifacts under {research_dir}"
        )
    return result


def _load_result_map(
    tickers: list[str],
    *,
    candidate_source_map: dict[str, dict[str, Any]] | None = None,
) -> dict[str, dict[str, Any]]:
    profiles = mt.build_timing_profiles()
    result_map: dict[str, dict[str, Any]] = {}
    source_map = candidate_source_map or {}
    for ticker in tickers:
        source_row = source_map.get(ticker)
        if source_row is not None:
            result_map[ticker] = _load_result_from_source_row(ticker=ticker, source_row=source_row)
            continue
        result_map[ticker] = round2.load_or_run_result(ticker=ticker, profiles=profiles)
    return result_map


def _common_oos_dates_for(selected_tickers: list[str], result_map: dict[str, dict[str, Any]]) -> set[object]:
    post_train_sets = [
        set(result_map[ticker]["ordered_trade_dates"][mt.DEFAULT_INITIAL_TRAIN_DAYS :])
        for ticker in selected_tickers
    ]
    return set.intersection(*post_train_sets) if post_train_sets else set()


def _run_overlay(
    selected_tickers: list[str],
    result_map: dict[str, dict[str, Any]],
    common_oos_dates: set[object],
) -> tuple[dict[str, Any], pd.DataFrame, pd.DataFrame]:
    candidates, strategy_map = exp.combined_for_tickers(
        selected_tickers=selected_tickers,
        result_map=result_map,
        common_oos_dates=common_oos_dates,
    )
    return exp.summarize_overlay(candidate_trades=candidates, strategy_map=strategy_map)


def _score(summary: dict[str, Any]) -> tuple[float, float, float]:
    return (
        float(summary["calmar_like"]),
        float(summary["final_equity"]),
        float(summary["total_return_pct"]),
    )


def main() -> None:
    args = build_parser().parse_args()
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    live_tickers = round2.load_current_live_tickers()
    candidate_source_map = _load_candidate_source_map(
        Path(args.candidate_source_json).resolve() if args.candidate_source_json else None
    )
    candidates = [ticker for ticker in _normalize_tickers(args.candidates) if ticker not in live_tickers]
    all_tickers = sorted(set(live_tickers + candidates))
    result_map = _load_result_map(all_tickers, candidate_source_map=candidate_source_map)

    incremental_rows: list[dict[str, Any]] = []
    positive_candidates: list[str] = []

    for candidate in candidates:
        overlap_tickers = live_tickers + [candidate]
        common_oos_dates = _common_oos_dates_for(overlap_tickers, result_map)
        if not common_oos_dates:
            incremental_rows.append(
                {
                    "candidate": candidate.upper(),
                    "common_oos_date_count": 0,
                    "baseline_final_equity": None,
                    "trial_final_equity": None,
                    "equity_delta": None,
                    "baseline_total_return_pct": None,
                    "trial_total_return_pct": None,
                    "return_delta_pct": None,
                    "baseline_max_drawdown_pct": None,
                    "trial_max_drawdown_pct": None,
                    "drawdown_delta_pct": None,
                    "baseline_calmar_like": None,
                    "trial_calmar_like": None,
                    "calmar_delta": None,
                    "improved": False,
                }
            )
            continue

        baseline_summary, _baseline_trades, _baseline_equity = _run_overlay(
            selected_tickers=live_tickers,
            result_map=result_map,
            common_oos_dates=common_oos_dates,
        )
        trial_summary, trial_trades, trial_equity = _run_overlay(
            selected_tickers=overlap_tickers,
            result_map=result_map,
            common_oos_dates=common_oos_dates,
        )

        baseline_score = _score(baseline_summary)
        trial_score = _score(trial_summary)
        improved = trial_score > baseline_score and float(trial_summary["final_equity"]) > float(
            baseline_summary["final_equity"]
        )

        if improved:
            positive_candidates.append(candidate)

        safe_label = candidate.lower()
        trial_trades.to_csv(output_dir / f"{safe_label}_trial_trades.csv", index=False)
        trial_equity.to_csv(output_dir / f"{safe_label}_trial_equity.csv", index=False)

        incremental_rows.append(
            {
                "candidate": candidate.upper(),
                "common_oos_date_count": len(common_oos_dates),
                "baseline_final_equity": float(baseline_summary["final_equity"]),
                "trial_final_equity": float(trial_summary["final_equity"]),
                "equity_delta": float(trial_summary["final_equity"]) - float(baseline_summary["final_equity"]),
                "baseline_total_return_pct": float(baseline_summary["total_return_pct"]),
                "trial_total_return_pct": float(trial_summary["total_return_pct"]),
                "return_delta_pct": float(trial_summary["total_return_pct"])
                - float(baseline_summary["total_return_pct"]),
                "baseline_max_drawdown_pct": float(baseline_summary["max_drawdown_pct"]),
                "trial_max_drawdown_pct": float(trial_summary["max_drawdown_pct"]),
                "drawdown_delta_pct": float(trial_summary["max_drawdown_pct"])
                - float(baseline_summary["max_drawdown_pct"]),
                "baseline_calmar_like": float(baseline_summary["calmar_like"]),
                "trial_calmar_like": float(trial_summary["calmar_like"]),
                "calmar_delta": float(trial_summary["calmar_like"]) - float(baseline_summary["calmar_like"]),
                "improved": improved,
            }
        )

    incremental_df = pd.DataFrame(incremental_rows)
    if incremental_df.empty:
        incremental_df = pd.DataFrame(columns=INCREMENTAL_RESULT_COLUMNS)
    else:
        incremental_df = incremental_df.sort_values(
            ["improved", "calmar_delta", "equity_delta"],
            ascending=[False, False, False],
        )
    incremental_df.to_csv(output_dir / "incremental_results.csv", index=False)

    combo_pool = (
        incremental_df.loc[incremental_df["improved"], "candidate"]
        .astype(str)
        .str.lower()
        .head(args.top_combo_count)
        .tolist()
    )
    combo_rows: list[dict[str, Any]] = []
    for subset_size in range(1, len(combo_pool) + 1):
        for subset in itertools.combinations(combo_pool, subset_size):
            selected = live_tickers + list(subset)
            common_oos_dates = _common_oos_dates_for(selected, result_map)
            if not common_oos_dates:
                continue
            summary, trades, equity = _run_overlay(
                selected_tickers=selected,
                result_map=result_map,
                common_oos_dates=common_oos_dates,
            )
            safe_label = "_".join(subset)
            trades.to_csv(output_dir / f"combo_{safe_label}_trades.csv", index=False)
            equity.to_csv(output_dir / f"combo_{safe_label}_equity.csv", index=False)
            combo_rows.append(
                {
                    "added_tickers": ",".join(ticker.upper() for ticker in subset),
                    "added_count": len(subset),
                    "common_oos_date_count": len(common_oos_dates),
                    "final_equity": float(summary["final_equity"]),
                    "total_return_pct": float(summary["total_return_pct"]),
                    "trade_count": int(summary["trade_count"]),
                    "win_rate_pct": float(summary["win_rate_pct"]),
                    "max_drawdown_pct": float(summary["max_drawdown_pct"]),
                    "calmar_like": float(summary["calmar_like"]),
                }
            )

    combo_df = pd.DataFrame(combo_rows)
    if combo_df.empty:
        combo_df = pd.DataFrame(columns=COMBO_RESULT_COLUMNS)
    else:
        combo_df = combo_df.sort_values(
            ["calmar_like", "final_equity", "total_return_pct"],
            ascending=[False, False, False],
        )
    combo_df.to_csv(output_dir / "combo_results.csv", index=False)

    payload = {
        "live_tickers": [ticker.upper() for ticker in live_tickers],
        "candidate_tickers": [ticker.upper() for ticker in candidates],
        "candidate_source_json": str(Path(args.candidate_source_json).resolve()) if args.candidate_source_json else "",
        "improving_candidates": [ticker.upper() for ticker in combo_pool],
        "best_incremental": incremental_df.iloc[0].to_dict() if not incremental_df.empty else None,
        "best_combo": combo_df.iloc[0].to_dict() if not combo_df.empty else None,
    }
    (output_dir / "summary.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
