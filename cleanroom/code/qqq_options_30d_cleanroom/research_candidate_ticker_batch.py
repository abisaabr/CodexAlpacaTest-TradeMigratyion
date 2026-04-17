from __future__ import annotations

import argparse
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


DEFAULT_OUTPUT_DIR = ROOT / "output"
DEFAULT_RESEARCH_DIR = DEFAULT_OUTPUT_DIR / "candidate_batch_research_365d"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run standalone cleanroom research for a batch of candidate tickers."
    )
    parser.add_argument(
        "--tickers",
        required=True,
        help="Comma-separated ticker list, for example: aapl,amzn,meta",
    )
    parser.add_argument(
        "--research-dir",
        default=str(DEFAULT_RESEARCH_DIR),
        help="Directory to store candidate research outputs.",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    research_dir = Path(args.research_dir).resolve()
    research_dir.mkdir(parents=True, exist_ok=True)

    tickers = [ticker.strip().lower() for ticker in args.tickers.split(",") if ticker.strip()]
    profiles = mt.build_timing_profiles()

    rows: list[dict[str, Any]] = []
    for ticker in tickers:
        result = round2.load_or_run_result(ticker=ticker, profiles=profiles)
        summary = result["summary"]
        promoted = summary["promoted"]
        rows.append(
            {
                "ticker": ticker.upper(),
                "trade_date_start": summary["trade_date_start"],
                "trade_date_end": summary["trade_date_end"],
                "day_count": int(summary["day_count"]),
                "candidate_trade_count": int(summary["candidate_trade_count"]),
                "frozen_final_equity": float(summary["frozen_initial"]["final_equity"]),
                "frozen_total_return_pct": float(summary["frozen_initial"]["total_return_pct"]),
                "frozen_trade_count": int(summary["frozen_initial"]["trade_count"]),
                "frozen_win_rate_pct": float(summary["frozen_initial"]["win_rate_pct"]),
                "frozen_max_drawdown_pct": float(summary["frozen_initial"]["max_drawdown_pct"]),
                "reoptimized_final_equity": float(summary["reoptimized"]["final_equity"]),
                "reoptimized_total_return_pct": float(summary["reoptimized"]["total_return_pct"]),
                "reoptimized_trade_count": int(summary["reoptimized"]["trade_count"]),
                "reoptimized_win_rate_pct": float(summary["reoptimized"]["win_rate_pct"]),
                "reoptimized_max_drawdown_pct": float(summary["reoptimized"]["max_drawdown_pct"]),
                "regime_threshold_pct": float(promoted["regime_threshold_pct"]),
                "selected_bull_count": len(promoted["selected_bull"]),
                "selected_bear_count": len(promoted["selected_bear"]),
                "selected_choppy_count": len(promoted["selected_choppy"]),
                "selected_bull": ",".join(promoted["selected_bull"]),
                "selected_bear": ",".join(promoted["selected_bear"]),
                "selected_choppy": ",".join(promoted["selected_choppy"]),
            }
        )
        print(
            json.dumps(
                {
                    "ticker": ticker.upper(),
                    "frozen_total_return_pct": rows[-1]["frozen_total_return_pct"],
                    "frozen_max_drawdown_pct": rows[-1]["frozen_max_drawdown_pct"],
                    "selected_bull_count": rows[-1]["selected_bull_count"],
                    "selected_bear_count": rows[-1]["selected_bear_count"],
                    "selected_choppy_count": rows[-1]["selected_choppy_count"],
                }
            ),
            flush=True,
        )

    summary_df = pd.DataFrame(rows).sort_values(
        ["frozen_total_return_pct", "frozen_final_equity"],
        ascending=[False, False],
    )
    summary_df.to_csv(research_dir / "standalone_summary.csv", index=False)
    (research_dir / "standalone_summary.json").write_text(
        json.dumps(summary_df.to_dict(orient="records"), indent=2),
        encoding="utf-8",
    )
    print(json.dumps({"tickers": [ticker.upper() for ticker in tickers], "summary_path": str(research_dir / 'standalone_summary.csv')}, indent=2))


if __name__ == "__main__":
    main()
