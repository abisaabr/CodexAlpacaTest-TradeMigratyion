from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import time
import zipfile
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parent
RUN_REGISTRY_REPORTER = ROOT / "build_run_registry_report.py"
DEFAULT_OUTPUT_ROOT = ROOT / "output"
DEFAULT_RUN_REGISTRY_PATH = DEFAULT_OUTPUT_ROOT / "run_registry.jsonl"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Wait for an existing tournament to finish, then stage bundle zips into a clean workspace and launch a new candidate batch."
    )
    parser.add_argument("--tickers", required=True, help="Comma-separated ticker list.")
    parser.add_argument("--bundle-output-dir", required=True, help="Directory holding *_365d_bundle.zip files.")
    parser.add_argument("--research-dir", required=True, help="Directory for the follow-on research batch.")
    parser.add_argument(
        "--wait-for-pid",
        type=int,
        required=True,
        help="PID to wait for before launching the next batch.",
    )
    parser.add_argument(
        "--poll-seconds",
        type=int,
        default=60,
        help="Polling interval while waiting for the prior batch to finish.",
    )
    parser.add_argument(
        "--wait-for-success-file",
        default="",
        help="Optional file path that must exist after the prior PID exits before launching the next batch.",
    )
    return parser


def pid_is_running(pid: int) -> bool:
    result = subprocess.run(
        ["tasklist", "/FI", f"PID eq {pid}", "/FO", "CSV", "/NH"],
        capture_output=True,
        text=True,
        check=True,
    )
    return f'"{pid}"' in result.stdout


def stage_bundle_member(
    *,
    bundle_path: Path,
    member_name: str,
    target_path: Path,
) -> None:
    target_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(bundle_path) as archive:
        with archive.open(member_name) as source, target_path.open("wb") as target:
            shutil.copyfileobj(source, target)


def stage_ticker_bundle(
    *,
    ticker: str,
    bundle_output_dir: Path,
    workspace_dir: Path,
) -> dict[str, object]:
    ticker_lower = ticker.lower()
    bundle_path = bundle_output_dir / f"{ticker_lower}_365d_bundle.zip"
    if not bundle_path.exists():
        raise FileNotFoundError(f"missing bundle zip for {ticker.upper()}: {bundle_path}")

    required = {
        f"{ticker_lower}_365d_option_1min_wide_backtest.parquet": workspace_dir
        / f"{ticker_lower}_365d_option_1min_wide_backtest.parquet",
        f"{ticker_lower}_365d_option_1min_dense.parquet": workspace_dir
        / f"{ticker_lower}_365d_option_1min_dense.parquet",
        f"{ticker_lower}_365d_option_daily_universe.parquet": workspace_dir
        / f"{ticker_lower}_365d_option_daily_universe.parquet",
    }
    for member_name, target_path in required.items():
        stage_bundle_member(bundle_path=bundle_path, member_name=member_name, target_path=target_path)
        pd.read_parquet(target_path)

    audit_path = bundle_output_dir / f"{ticker_lower}_365d_audit_report.json"
    if audit_path.exists():
        shutil.copy2(audit_path, workspace_dir / audit_path.name)

    return {
        "ticker": ticker.upper(),
        "bundle_path": str(bundle_path),
        "workspace_files": [str(path) for path in required.values()],
        "audit_json": str(workspace_dir / audit_path.name) if audit_path.exists() else "",
    }


def invoke_run_registry_report(*, research_dir: Path) -> None:
    if not RUN_REGISTRY_REPORTER.exists():
        return
    report_dir = research_dir / "run_registry_report"
    subprocess.run(
        [
            sys.executable,
            str(RUN_REGISTRY_REPORTER),
            "--output-root",
            str(DEFAULT_OUTPUT_ROOT),
            "--registry-path",
            str(DEFAULT_RUN_REGISTRY_PATH),
            "--report-dir",
            str(report_dir),
            "--manifest-root",
            str(research_dir),
        ],
        cwd=ROOT,
        check=True,
    )


def main() -> None:
    args = build_parser().parse_args()
    tickers = [ticker.strip().lower() for ticker in args.tickers.split(",") if ticker.strip()]
    research_dir = Path(args.research_dir).resolve()
    bundle_output_dir = Path(args.bundle_output_dir).resolve()
    workspace_dir = research_dir / "input_workspace"
    logs_dir = research_dir / "logs"
    research_dir.mkdir(parents=True, exist_ok=True)
    logs_dir.mkdir(parents=True, exist_ok=True)
    status_path = research_dir / "followon_status.json"
    log_path = logs_dir / "followon_launcher.log"
    wait_for_success_file = Path(args.wait_for_success_file).resolve() if args.wait_for_success_file else None

    while pid_is_running(args.wait_for_pid):
        payload = {
            "phase": "waiting",
            "wait_for_pid": args.wait_for_pid,
            "timestamp_epoch": time.time(),
            "tickers": [ticker.upper() for ticker in tickers],
            "wait_for_success_file": str(wait_for_success_file) if wait_for_success_file else "",
        }
        status_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        log_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        time.sleep(args.poll_seconds)

    if wait_for_success_file is not None and not wait_for_success_file.exists():
        payload = {
            "phase": "blocked",
            "wait_for_pid": args.wait_for_pid,
            "tickers": [ticker.upper() for ticker in tickers],
            "wait_for_success_file": str(wait_for_success_file),
            "message": "Prior batch exited without writing the required success file.",
            "timestamp_epoch": time.time(),
        }
        status_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        with log_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, indent=2) + "\n")
        invoke_run_registry_report(research_dir=research_dir)
        raise SystemExit(2)

    if workspace_dir.exists():
        shutil.rmtree(workspace_dir)
    workspace_dir.mkdir(parents=True, exist_ok=True)

    staged_rows = [
        stage_ticker_bundle(ticker=ticker, bundle_output_dir=bundle_output_dir, workspace_dir=workspace_dir)
        for ticker in tickers
    ]
    (research_dir / "followon_staged_inputs.json").write_text(
        json.dumps(staged_rows, indent=2),
        encoding="utf-8",
    )

    command = [
        sys.executable,
        str(ROOT / "run_multiticker_cleanroom_portfolio.py"),
        "--tickers",
        ",".join(tickers),
        "--output-dir",
        str(workspace_dir),
        "--research-dir",
        str(research_dir),
        "--continue-on-error",
    ]
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write("$ " + " ".join(command) + "\n")
        handle.flush()
        subprocess.run(command, cwd=ROOT, check=True, stdout=handle, stderr=handle, text=True)

    payload = {
        "phase": "completed",
        "wait_for_pid": args.wait_for_pid,
        "tickers": [ticker.upper() for ticker in tickers],
        "research_dir": str(research_dir),
        "completed_at_epoch": time.time(),
    }
    status_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, indent=2) + "\n")
    invoke_run_registry_report(research_dir=research_dir)


if __name__ == "__main__":
    main()
