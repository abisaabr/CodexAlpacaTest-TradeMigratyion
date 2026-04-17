from __future__ import annotations

import argparse
import gzip
import json
import os
import shutil
import subprocess
import sys
import time
import zipfile
from dataclasses import dataclass
from pathlib import Path


SIZE_HINTS = {
    "TLT": 19888,
    "GLD": 19756,
    "SLV": 19834,
    "XLF": 7194,
    "XLE": 7190,
    "EEM": 7458,
    "FXI": 7186,
    "HYG": 6688,
    "KRE": 7194,
    "GDX": 6688,
    "ARKK": 6688,
    "XBI": 6688,
    "PLTR": 6688,
    "BAC": 6688,
    "PFE": 6688,
    "INTC": 6688,
    "SOFI": 6686,
    "SNAP": 6686,
    "HOOD": 6688,
    "F": 6688,
    "LCID": 6336,
    "RIVN": 6688,
    "T": 6688,
    "C": 6688,
    "WFC": 6688,
    "AMD": 6688,
    "VALE": 6688,
}


@dataclass
class RunningJob:
    symbol: str
    process: subprocess.Popen[str]
    log_path: Path
    err_path: Path
    stdout_handle: object
    stderr_handle: object


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run 365-day options downloads for a batch of symbols.")
    parser.add_argument("--symbols", required=True, help="Comma-separated symbol list.")
    parser.add_argument("--today", default="2026-04-10")
    parser.add_argument("--lookback-days", type=int, default=365)
    parser.add_argument("--concurrency", type=int, default=6)
    parser.add_argument("--job-workers", type=int, default=4)
    parser.add_argument("--requests-per-second", type=float, default=1.6)
    parser.add_argument("--tag", default="365d")
    parser.add_argument("--output-dir", default="output")
    return parser.parse_args()


def make_audit_path(output_dir: Path, symbol: str, tag: str) -> Path:
    return output_dir / f"{symbol.lower()}_{tag}_audit_report.json"


def make_gz_paths(output_dir: Path, symbol: str, tag: str) -> tuple[Path, Path]:
    dense = output_dir / f"{symbol.lower()}_{tag}_option_1min_dense.csv.gz"
    wide = output_dir / f"{symbol.lower()}_{tag}_option_1min_wide_backtest.csv.gz"
    return dense, wide


def make_bundle_path(output_dir: Path, symbol: str, tag: str) -> Path:
    return output_dir / f"{symbol.lower()}_{tag}_bundle.zip"


def expand_gzip(src: Path, dst: Path) -> None:
    with gzip.open(src, "rb") as fin, open(dst, "wb") as fout:
        shutil.copyfileobj(fin, fout, length=1024 * 1024)


def expand_plain_csvs(output_dir: Path, symbol: str, tag: str) -> None:
    dense_gz, wide_gz = make_gz_paths(output_dir, symbol, tag)
    dense_csv = output_dir / f"{symbol.lower()}_{tag}_option_1min_dense.csv"
    wide_csv = output_dir / f"{symbol.lower()}_{tag}_option_1min_wide_backtest.csv"
    if dense_gz.exists() and not dense_csv.exists():
        expand_gzip(dense_gz, dense_csv)
    if wide_gz.exists() and not wide_csv.exists():
        expand_gzip(wide_gz, wide_csv)


def archive_symbol_outputs(output_dir: Path, symbol: str, tag: str) -> Path | None:
    prefix = f"{symbol.lower()}_{tag}_"
    audit_path = make_audit_path(output_dir, symbol, tag)
    bundle_path = make_bundle_path(output_dir, symbol, tag)
    candidates = [
        path
        for path in sorted(output_dir.iterdir())
        if path.is_file()
        and path.name.startswith(prefix)
        and path != audit_path
        and path != bundle_path
    ]
    if not candidates:
        return bundle_path if bundle_path.exists() else None

    temp_bundle = bundle_path.with_suffix(".zip.tmp")
    if temp_bundle.exists():
        temp_bundle.unlink()

    with zipfile.ZipFile(temp_bundle, mode="w") as archive:
        for path in candidates:
            compress_type = zipfile.ZIP_STORED if path.suffix in {".parquet", ".gz", ".zip"} else zipfile.ZIP_DEFLATED
            archive.write(path, arcname=path.name, compress_type=compress_type)

    temp_bundle.replace(bundle_path)

    for path in candidates:
        if path.exists():
            path.unlink()

    return bundle_path


def maybe_neighbor_fill(symbol: str, tag: str, output_dir: Path, env: dict[str, str]) -> dict:
    audit_path = make_audit_path(output_dir, symbol, tag)
    audit = json.loads(audit_path.read_text())
    dense_fill = float(audit["dense_minute_fill_pct_on_selected_contract_days"])
    if dense_fill >= 98.0:
        return audit
    cmd = [
        sys.executable,
        "neighbor_fill_empty_days.py",
        "--underlying",
        symbol,
        "--tag",
        tag,
        "--output-dir",
        str(output_dir),
    ]
    result = subprocess.run(cmd, cwd=Path.cwd(), env=env, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"neighbor fill failed for {symbol}: {result.stderr or result.stdout}")
    audit = json.loads(audit_path.read_text())
    return audit


def launch_job(symbol: str, args: argparse.Namespace, env: dict[str, str]) -> RunningJob:
    log_path = Path.cwd() / f"{symbol.lower()}_{args.tag}_run.log"
    err_path = Path.cwd() / f"{symbol.lower()}_{args.tag}_run.err"
    if log_path.exists():
        log_path.unlink()
    if err_path.exists():
        err_path.unlink()
    stdout = open(log_path, "w", encoding="utf-8")
    stderr = open(err_path, "w", encoding="utf-8")
    cmd = [
        sys.executable,
        "-u",
        "download_qqq_options_365d_streaming.py",
        "--underlying",
        symbol,
        "--today",
        args.today,
        "--lookback-days",
        str(args.lookback_days),
        "--workers",
        str(args.job_workers),
        "--requests-per-second",
        str(args.requests_per_second),
        "--tag",
        args.tag,
        "--output-dir",
        str(Path(args.output_dir).resolve()),
    ]
    process = subprocess.Popen(cmd, cwd=Path.cwd(), env=env, stdout=stdout, stderr=stderr, text=True)
    return RunningJob(
        symbol=symbol,
        process=process,
        log_path=log_path,
        err_path=err_path,
        stdout_handle=stdout,
        stderr_handle=stderr,
    )


def collect_summary(output_dir: Path, symbols: list[str], tag: str) -> list[dict]:
    rows = []
    for symbol in symbols:
        audit_path = make_audit_path(output_dir, symbol, tag)
        if not audit_path.exists():
            continue
        audit = json.loads(audit_path.read_text())
        rows.append(
            {
                "symbol": symbol,
                "selected_contract_days": audit["selected_contract_days"],
                "unique_contracts": audit["unique_contracts"],
                "request_fill_rate": audit["request_fill_rate"],
                "dense_fill_selected_pct": audit["dense_minute_fill_pct_on_selected_contract_days"],
                "dense_fill_nonempty_pct": audit["dense_minute_fill_pct_on_nonempty_contract_days"],
                "neighbor_filled_empty_contract_days": audit.get("neighbor_filled_empty_contract_days", 0),
            }
        )
    return rows


def main() -> None:
    args = parse_args()
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    symbols = [part.strip().upper() for part in args.symbols.split(",") if part.strip()]
    symbols = sorted(symbols, key=lambda s: SIZE_HINTS.get(s, 0), reverse=True)

    pending: list[str] = []
    skipped: list[str] = []
    for symbol in symbols:
        audit_path = make_audit_path(output_dir, symbol, args.tag)
        if audit_path.exists():
            skipped.append(symbol)
        else:
            pending.append(symbol)

    print(json.dumps({"phase": "start", "pending": pending, "skipped": skipped}))

    env = os.environ.copy()
    required = ["ALPACA_API_KEY", "ALPACA_SECRET_KEY", "ALPACA_API_BASE_URL"]
    missing = [name for name in required if not env.get(name)]
    if missing:
        raise RuntimeError(f"missing environment variables: {missing}")

    running: list[RunningJob] = []
    completed: list[str] = []
    failed: list[dict] = []

    while pending or running:
        while pending and len(running) < args.concurrency:
            symbol = pending.pop(0)
            job = launch_job(symbol, args, env)
            running.append(job)
            print(json.dumps({"phase": "launched", "symbol": symbol, "pid": job.process.pid}))

        time.sleep(30)
        still_running: list[RunningJob] = []
        for job in running:
            rc = job.process.poll()
            if rc is None:
                still_running.append(job)
                continue
            job.stdout_handle.close()
            job.stderr_handle.close()
            if rc != 0:
                stderr = job.err_path.read_text(encoding="utf-8", errors="ignore") if job.err_path.exists() else ""
                failed.append({"symbol": job.symbol, "returncode": rc, "stderr_tail": stderr[-4000:]})
                print(json.dumps({"phase": "failed", "symbol": job.symbol, "returncode": rc}))
                continue
            try:
                audit = maybe_neighbor_fill(job.symbol, args.tag, output_dir, env)
                expand_plain_csvs(output_dir, job.symbol, args.tag)
                bundle_path = archive_symbol_outputs(output_dir, job.symbol, args.tag)
                completed.append(job.symbol)
                print(
                    json.dumps(
                        {
                            "phase": "completed",
                            "symbol": job.symbol,
                            "dense_fill_selected_pct": audit["dense_minute_fill_pct_on_selected_contract_days"],
                            "neighbor_filled_empty_contract_days": audit.get("neighbor_filled_empty_contract_days", 0),
                            "bundle_path": str(bundle_path) if bundle_path else "",
                        }
                    )
                )
            except Exception as exc:
                failed.append({"symbol": job.symbol, "returncode": 0, "postprocess_error": str(exc)})
                print(json.dumps({"phase": "postprocess_failed", "symbol": job.symbol, "error": str(exc)}))
        running = still_running
        print(json.dumps({"phase": "heartbeat", "pending": pending, "running": [job.symbol for job in running], "completed": completed}))

    summary = collect_summary(output_dir, symbols, args.tag)
    summary_path = output_dir / f"batch_{args.tag}_summary.csv"
    import csv

    with open(summary_path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(summary[0].keys()) if summary else ["symbol"])
        writer.writeheader()
        for row in summary:
            writer.writerow(row)

    result = {"phase": "done", "completed": completed, "skipped": skipped, "failed": failed, "summary_path": str(summary_path)}
    print(json.dumps(result))
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
