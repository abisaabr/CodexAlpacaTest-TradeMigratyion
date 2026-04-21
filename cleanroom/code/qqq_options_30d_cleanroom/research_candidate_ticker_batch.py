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
    parser.add_argument(
        "--force-rerun",
        action="store_true",
        help="Ignore cached ticker research and rerun using the current strategy set.",
    )
    parser.add_argument(
        "--continue-on-error",
        action="store_true",
        help="Record ticker-level failures in the summary instead of stopping the whole batch.",
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
        try:
            result = round2.load_or_run_result(
                ticker=ticker,
                profiles=profiles,
                force_rerun=args.force_rerun,
            )
            summary = result["summary"]
            promoted = summary["promoted"]
            frozen_family_buckets = list(summary["frozen_initial"].get("family_bucket_contributions", []))
            reoptimized_family_buckets = list(summary["reoptimized"].get("family_bucket_contributions", []))
            frozen_premium_buckets = list(summary["frozen_initial"].get("premium_bucket_contributions", []))
            reoptimized_premium_buckets = list(summary["reoptimized"].get("premium_bucket_contributions", []))
            frozen_friction = dict(summary["frozen_initial"].get("friction_profile", {}))
            reoptimized_friction = dict(summary["reoptimized"].get("friction_profile", {}))
            top_frozen_bucket = frozen_family_buckets[0] if frozen_family_buckets else {}
            top_reoptimized_bucket = reoptimized_family_buckets[0] if reoptimized_family_buckets else {}
            top_frozen_premium_bucket = frozen_premium_buckets[0] if frozen_premium_buckets else {}
            top_reoptimized_premium_bucket = reoptimized_premium_buckets[0] if reoptimized_premium_buckets else {}
            row = {
                "ticker": ticker.upper(),
                "status": "ok",
                "error": "",
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
                "top_frozen_family_bucket": str(top_frozen_bucket.get("family_bucket", "")),
                "top_frozen_family_bucket_pnl": float(top_frozen_bucket.get("portfolio_net_pnl", 0.0)),
                "top_reoptimized_family_bucket": str(top_reoptimized_bucket.get("family_bucket", "")),
                "top_reoptimized_family_bucket_pnl": float(top_reoptimized_bucket.get("portfolio_net_pnl", 0.0)),
                "top_frozen_premium_bucket": str(top_frozen_premium_bucket.get("premium_bucket", "")),
                "top_frozen_premium_bucket_pnl": float(top_frozen_premium_bucket.get("portfolio_net_pnl", 0.0)),
                "top_reoptimized_premium_bucket": str(top_reoptimized_premium_bucket.get("premium_bucket", "")),
                "top_reoptimized_premium_bucket_pnl": float(top_reoptimized_premium_bucket.get("portfolio_net_pnl", 0.0)),
                "frozen_median_entry_premium": float(frozen_friction.get("median_entry_premium", 0.0)),
                "frozen_avg_friction_pct_of_entry_premium": float(frozen_friction.get("avg_friction_pct_of_entry_premium", 0.0)),
                "frozen_trade_share_sub_0_30_pct": float(frozen_friction.get("trade_share_sub_0_30_pct", 0.0)),
                "reoptimized_median_entry_premium": float(reoptimized_friction.get("median_entry_premium", 0.0)),
                "reoptimized_avg_friction_pct_of_entry_premium": float(reoptimized_friction.get("avg_friction_pct_of_entry_premium", 0.0)),
                "reoptimized_trade_share_sub_0_30_pct": float(reoptimized_friction.get("trade_share_sub_0_30_pct", 0.0)),
            }
            print(
                json.dumps(
                    {
                        "ticker": row["ticker"],
                        "status": row["status"],
                        "frozen_total_return_pct": row["frozen_total_return_pct"],
                        "frozen_max_drawdown_pct": row["frozen_max_drawdown_pct"],
                        "top_frozen_family_bucket": row["top_frozen_family_bucket"],
                        "top_frozen_premium_bucket": row["top_frozen_premium_bucket"],
                        "frozen_trade_share_sub_0_30_pct": row["frozen_trade_share_sub_0_30_pct"],
                        "selected_bull_count": row["selected_bull_count"],
                        "selected_bear_count": row["selected_bear_count"],
                        "selected_choppy_count": row["selected_choppy_count"],
                    }
                ),
                flush=True,
            )
        except Exception as exc:
            if not args.continue_on_error:
                raise
            row = {
                "ticker": ticker.upper(),
                "status": "error",
                "error": str(exc),
            }
            print(
                json.dumps(
                    {
                        "ticker": row["ticker"],
                        "status": row["status"],
                        "error": row["error"],
                    }
                ),
                flush=True,
            )
        rows.append(row)

    summary_df = pd.DataFrame(rows)
    for column in ("frozen_total_return_pct", "frozen_final_equity"):
        if column not in summary_df.columns:
            summary_df[column] = pd.NA
    summary_df = summary_df.sort_values(
        ["status", "frozen_total_return_pct", "frozen_final_equity"],
        ascending=[True, False, False],
        na_position="last",
    )
    summary_df.to_csv(research_dir / "standalone_summary.csv", index=False)
    (research_dir / "standalone_summary.json").write_text(
        json.dumps(summary_df.to_dict(orient="records"), indent=2),
        encoding="utf-8",
    )
    print(json.dumps({"tickers": [ticker.upper() for ticker in tickers], "summary_path": str(research_dir / 'standalone_summary.csv')}, indent=2))


if __name__ == "__main__":
    main()
