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


DEFAULT_OUTPUT_PATH = ROOT / "output" / "candidate_combo_eval_365d"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Evaluate candidate ticker combinations against the current live multi-ticker book."
    )
    parser.add_argument(
        "--candidates",
        required=True,
        help="Comma-separated candidate tickers to test, for example: gdx,tlt,slv",
    )
    parser.add_argument(
        "--output-dir",
        default=str(DEFAULT_OUTPUT_PATH),
        help="Directory for the combo evaluation outputs.",
    )
    return parser


def load_result_map(tickers: list[str]) -> dict[str, dict[str, Any]]:
    profiles = mt.build_timing_profiles()
    result_map: dict[str, dict[str, Any]] = {}
    for ticker in tickers:
        result_map[ticker] = round2.load_or_run_result(ticker=ticker, profiles=profiles)
    return result_map


def sort_candidate_frame(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return frame
    return frame.sort_values(["trade_date", "entry_minute", "strategy"]).reset_index(drop=True)


def main() -> None:
    args = build_parser().parse_args()
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    live_tickers = round2.load_current_live_tickers()
    candidates = [ticker.strip().lower() for ticker in args.candidates.split(",") if ticker.strip()]
    candidate_set = [ticker for ticker in candidates if ticker not in live_tickers]
    all_tickers = live_tickers + candidate_set

    result_map = load_result_map(all_tickers)
    post_train_sets = [
        set(result["ordered_trade_dates"][mt.DEFAULT_INITIAL_TRAIN_DAYS :])
        for result in result_map.values()
    ]
    common_oos_dates = set.intersection(*post_train_sets) if post_train_sets else set()
    if not common_oos_dates:
        raise RuntimeError("no common OOS dates across selected universe")

    baseline_candidates, baseline_strategy_map = exp.combined_for_tickers(
        selected_tickers=live_tickers,
        result_map=result_map,
        common_oos_dates=common_oos_dates,
    )
    baseline_candidates = sort_candidate_frame(baseline_candidates)

    candidate_frames: dict[str, pd.DataFrame] = {}
    candidate_strategy_maps: dict[str, dict[str, mt.DeltaStrategy]] = {}
    for ticker in candidate_set:
        frame, strategy_map = exp.combined_for_tickers(
            selected_tickers=[ticker],
            result_map=result_map,
            common_oos_dates=common_oos_dates,
        )
        candidate_frames[ticker] = sort_candidate_frame(frame)
        candidate_strategy_maps[ticker] = strategy_map

    rows: list[dict[str, Any]] = []
    for subset_size in range(0, len(candidate_set) + 1):
        for subset in itertools.combinations(candidate_set, subset_size):
            frames = [baseline_candidates]
            strategy_map = dict(baseline_strategy_map)
            for ticker in subset:
                frames.append(candidate_frames[ticker])
                strategy_map.update(candidate_strategy_maps[ticker])
            combined = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
            combined = sort_candidate_frame(combined)
            summary, trades, equity = exp.summarize_overlay(
                candidate_trades=combined,
                strategy_map=strategy_map,
            )
            label = ",".join(ticker.upper() for ticker in subset) if subset else "(none)"
            rows.append(
                {
                    "added_tickers": label,
                    "added_count": len(subset),
                    "final_equity": float(summary["final_equity"]),
                    "total_return_pct": float(summary["total_return_pct"]),
                    "trade_count": int(summary["trade_count"]),
                    "win_rate_pct": float(summary["win_rate_pct"]),
                    "max_drawdown_pct": float(summary["max_drawdown_pct"]),
                    "calmar_like": float(summary["calmar_like"]),
                }
            )
            safe_label = "baseline" if not subset else "_".join(ticker for ticker in subset)
            trades.to_csv(output_dir / f"{safe_label}_portfolio_trades.csv", index=False)
            equity.to_csv(output_dir / f"{safe_label}_portfolio_equity.csv", index=False)

    result_df = pd.DataFrame(rows).sort_values(
        ["calmar_like", "final_equity", "total_return_pct"],
        ascending=[False, False, False],
    ).reset_index(drop=True)
    result_df.to_csv(output_dir / "combo_results.csv", index=False)

    payload = {
        "live_tickers": [ticker.upper() for ticker in live_tickers],
        "candidate_tickers": [ticker.upper() for ticker in candidate_set],
        "common_oos_date_count": len(common_oos_dates),
        "best_result": result_df.iloc[0].to_dict() if not result_df.empty else None,
    }
    (output_dir / "combo_summary.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
