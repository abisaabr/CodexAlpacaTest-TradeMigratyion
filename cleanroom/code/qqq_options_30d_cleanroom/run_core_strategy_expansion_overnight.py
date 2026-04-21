from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parent
DEFAULT_TICKERS = ("qqq", "spy", "iwm", "nvda", "tsla")
DEFAULT_OUTPUT_DIR = ROOT / "output"
DEFAULT_READY_BASE_DIR = Path(
    r"C:\Users\rabisaab\OneDrive - First American Corporation\qqq_options_30d_cleanroom\output\backtester_ready"
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Download missing core-ticker inputs and rerun an expanded overnight strategy search."
    )
    parser.add_argument(
        "--tickers",
        default=",".join(DEFAULT_TICKERS),
        help="Comma-separated ticker list.",
    )
    parser.add_argument(
        "--today",
        default="2026-04-10",
        help="Reference date passed to the 365d downloader.",
    )
    parser.add_argument(
        "--lookback-days",
        type=int,
        default=365,
        help="Download lookback window in days.",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=4,
        help="Downloader worker count per ticker.",
    )
    parser.add_argument(
        "--requests-per-second",
        type=float,
        default=1.2,
        help="Rate limit for downloader requests.",
    )
    parser.add_argument(
        "--tag",
        default="365d",
        help="Output tag used for data files.",
    )
    parser.add_argument(
        "--output-dir",
        default=str(DEFAULT_OUTPUT_DIR),
        help="Output directory that stores ticker datasets.",
    )
    parser.add_argument(
        "--ready-base-dir",
        default=str(DEFAULT_READY_BASE_DIR),
        help="Optional per-ticker backtester_ready directory to source dense/wide/universe inputs from before downloading.",
    )
    parser.add_argument(
        "--research-dir",
        default=str(DEFAULT_OUTPUT_DIR / "candidate_batch_research_overnight_coreexp5"),
        help="Directory for standalone research summaries.",
    )
    parser.add_argument(
        "--strategy-set",
        choices=("standard", "family_expansion", "down_choppy_only"),
        default="standard",
        help="Strategy universe to test. 'family_expansion' adds new bull/bear/choppy family candidates, and 'down_choppy_only' runs a lean bearish/choppy tournament surface.",
    )
    parser.add_argument(
        "--selection-profile",
        choices=("balanced", "down_choppy_focus"),
        default="balanced",
        help="How strongly to bias config selection toward bearish and choppy robustness.",
    )
    parser.add_argument(
        "--force-redownload",
        action="store_true",
        help="Redownload even when all required inputs already exist.",
    )
    return parser


def make_required_paths(output_dir: Path, ticker: str) -> dict[str, Path]:
    prefix = f"{ticker.lower()}_365d"
    return {
        "wide_parquet": output_dir / f"{prefix}_option_1min_wide_backtest.parquet",
        "wide_csv": output_dir / f"{prefix}_option_1min_wide_backtest.csv.gz",
        "dense_parquet": output_dir / f"{prefix}_option_1min_dense.parquet",
        "dense_csv": output_dir / f"{prefix}_option_1min_dense.csv.gz",
        "daily_universe": output_dir / f"{prefix}_option_daily_universe.parquet",
        "audit_json": output_dir / f"{prefix}_audit_report.json",
    }


def required_inputs_present(paths: dict[str, Path]) -> bool:
    required = ("wide_parquet", "dense_parquet", "daily_universe")
    return all(paths[name].exists() for name in required)


def stage_ready_file(source: Path, target: Path) -> bool:
    if not source.exists():
        return False
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        return True
    try:
        os.link(source, target)
    except OSError:
        shutil.copy2(source, target)
    return True


def stage_ready_ticker(*, ready_base_dir: Path, ticker: str, paths: dict[str, Path]) -> list[str]:
    ticker_dir = ready_base_dir / ticker.lower()
    if not ticker_dir.exists():
        return []
    staged: list[str] = []
    names = {
        "wide_parquet": ticker_dir / f"{ticker.lower()}_365d_option_1min_wide_backtest.parquet",
        "dense_parquet": ticker_dir / f"{ticker.lower()}_365d_option_1min_dense.parquet",
        "daily_universe": ticker_dir / f"{ticker.lower()}_365d_option_daily_universe.parquet",
        "audit_json": ticker_dir / f"{ticker.lower()}_365d_audit_report.json",
    }
    for key, source in names.items():
        if stage_ready_file(source, paths[key]):
            staged.append(key)
    return staged


def run_command(command: list[str], *, env: dict[str, str], log_path: Path) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write("$ " + " ".join(command) + "\n")
        handle.flush()
        subprocess.run(command, cwd=ROOT, env=env, check=True, stdout=handle, stderr=handle, text=True)


def repair_parquet_from_csv(parquet_path: Path, csv_path: Path) -> bool:
    if not csv_path.exists():
        return False
    try:
        pd.read_parquet(parquet_path)
        return False
    except Exception:
        backup_path = parquet_path.with_name(parquet_path.stem + ".broken_20260417" + parquet_path.suffix)
        if parquet_path.exists() and not backup_path.exists():
            shutil.copy2(parquet_path, backup_path)
        frame = pd.read_csv(csv_path, low_memory=False)
        frame.to_parquet(parquet_path, index=False)
        pd.read_parquet(parquet_path)
        return True


def ensure_ticker_inputs(
    *,
    ticker: str,
    args: argparse.Namespace,
    env: dict[str, str],
    log_dir: Path,
) -> dict[str, object]:
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = make_required_paths(output_dir, ticker)
    ticker_log = log_dir / f"{ticker.lower()}_prep.log"
    repaired: list[str] = []
    staged: list[str] = []

    ready_base_dir = Path(args.ready_base_dir).resolve() if args.ready_base_dir else None
    if ready_base_dir is not None and ready_base_dir.exists():
        staged = stage_ready_ticker(ready_base_dir=ready_base_dir, ticker=ticker, paths=paths)

    if args.force_redownload or not required_inputs_present(paths):
        run_command(
            [
                sys.executable,
                str(ROOT / "download_qqq_options_365d_streaming.py"),
                "--underlying",
                ticker.upper(),
                "--today",
                args.today,
                "--lookback-days",
                str(args.lookback_days),
                "--workers",
                str(args.workers),
                "--requests-per-second",
                str(args.requests_per_second),
                "--tag",
                "365d",
                "--output-dir",
                str(output_dir),
            ],
            env=env,
            log_path=ticker_log,
        )
        run_command(
            [
                sys.executable,
                str(ROOT / "neighbor_fill_empty_days.py"),
                "--underlying",
                ticker.upper(),
                "--tag",
                "365d",
                "--output-dir",
                str(output_dir),
            ],
            env=env,
            log_path=ticker_log,
        )

    for parquet_key, csv_key in (("wide_parquet", "wide_csv"), ("dense_parquet", "dense_csv")):
        if repair_parquet_from_csv(paths[parquet_key], paths[csv_key]):
            repaired.append(parquet_key)

    return {
        "ticker": ticker.upper(),
        "required_inputs_present": required_inputs_present(paths),
        "staged": staged,
        "repaired": repaired,
        "paths": {name: str(path) for name, path in paths.items()},
    }


def main() -> None:
    args = build_parser().parse_args()
    tickers = [ticker.strip().lower() for ticker in args.tickers.split(",") if ticker.strip()]
    env = os.environ.copy()
    env["PYTHONPATH"] = os.pathsep.join(
        [
            str(ROOT),
            str(ROOT.parent / "codexalpaca_repo"),
            env.get("PYTHONPATH", ""),
        ]
    ).rstrip(os.pathsep)

    required_env = ["ALPACA_API_KEY", "ALPACA_SECRET_KEY", "ALPACA_API_BASE_URL"]
    missing = [name for name in required_env if not env.get(name)]
    if missing:
        raise RuntimeError(f"missing environment variables: {missing}")

    research_dir = Path(args.research_dir).resolve()
    research_dir.mkdir(parents=True, exist_ok=True)
    log_dir = research_dir / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    workspace_output_dir = research_dir / "input_workspace"
    if workspace_output_dir.exists():
        shutil.rmtree(workspace_output_dir)
    workspace_output_dir.mkdir(parents=True, exist_ok=True)
    args.output_dir = str(workspace_output_dir)

    prep_rows: list[dict[str, object]] = []
    for ticker in tickers:
        prep = ensure_ticker_inputs(ticker=ticker, args=args, env=env, log_dir=log_dir)
        prep_rows.append(prep)
        print(json.dumps({"phase": "prepared", **prep}), flush=True)

    prep_path = research_dir / "prep_summary.json"
    prep_path.write_text(json.dumps(prep_rows, indent=2), encoding="utf-8")

    research_log = log_dir / "research.log"
    run_command(
        [
            sys.executable,
            str(ROOT / "run_multiticker_cleanroom_portfolio.py"),
            "--tickers",
            ",".join(tickers),
            "--output-dir",
            str(workspace_output_dir),
            "--research-dir",
            str(research_dir),
            "--strategy-set",
            str(args.strategy_set),
            "--selection-profile",
            str(args.selection_profile),
            "--continue-on-error",
        ],
        env=env,
        log_path=research_log,
    )

    summary_path = research_dir / "master_summary.json"
    payload = {
        "tickers": [ticker.upper() for ticker in tickers],
        "strategy_set": str(args.strategy_set),
        "selection_profile": str(args.selection_profile),
        "research_dir": str(research_dir),
        "summary_path": str(summary_path),
        "report_path": str(research_dir / "master_report.md"),
        "family_rankings_path": str(research_dir / "family_rankings.csv"),
        "family_bucket_rankings_path": str(research_dir / "family_bucket_rankings.csv"),
        "workspace_output_dir": str(workspace_output_dir),
        "prep_summary_path": str(prep_path),
        "completed_at_epoch": time.time(),
    }
    (research_dir / "overnight_run_summary.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()

