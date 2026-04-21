from __future__ import annotations

import argparse
import csv
import json
import os
import shutil
import tempfile
import zipfile
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
DEFAULT_SECONDARY_OUTPUT = Path(r"C:\Users\rabisaab\OneDrive - First American Corporation\qqq_options_30d_cleanroom\output")
DEFAULT_REGISTRY_PATH = DEFAULT_SECONDARY_OUTPUT / "backtester_registry.csv"
DEFAULT_READY_BASE_DIR = DEFAULT_SECONDARY_OUTPUT / "backtester_ready"
DEFAULT_REPORT_DIR = ROOT / "output" / f"materialize_backtester_ready_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
DEFAULT_ARTIFACTS = ("audit", "dense", "wide", "universe")
MANIFEST_ARTIFACTS = ("audit", "dense", "wide", "universe")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Materialize selected symbols from the backtester registry into backtester_ready."
    )
    parser.add_argument("--registry-path", default=str(DEFAULT_REGISTRY_PATH))
    parser.add_argument("--ready-base-dir", default=str(DEFAULT_READY_BASE_DIR))
    parser.add_argument("--report-dir", default=str(DEFAULT_REPORT_DIR))
    parser.add_argument("--tickers", default="", help="Comma-separated ticker list to materialize.")
    parser.add_argument(
        "--ticker-file",
        default="",
        help="Optional text/CSV file containing symbols. If CSV, a 'symbol' or 'ticker' column is preferred.",
    )
    parser.add_argument("--max-tickers", type=int, default=0, help="Optional cap after filtering; 0 means no cap.")
    parser.add_argument(
        "--artifacts",
        default=",".join(DEFAULT_ARTIFACTS),
        help="Comma-separated artifact list. Defaults to audit,dense,wide,universe.",
    )
    parser.add_argument(
        "--source-kinds",
        default="live,bundle_zip,archive_zip",
        help="Comma-separated source kinds to allow. Defaults to live,bundle_zip,archive_zip.",
    )
    parser.add_argument(
        "--only-missing",
        action="store_true",
        help="Only process rows whose target path does not already exist.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing target files instead of skipping them.",
    )
    parser.add_argument(
        "--update-registry",
        action="store_true",
        help="Rewrite the registry CSV with refreshed materialized_exists flags after the run.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail the whole run if any requested row cannot be materialized.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Plan the work and emit a report without copying or extracting files.",
    )
    return parser


def parse_symbol_tokens(text: str) -> list[str]:
    return sorted({token.strip().upper() for token in text.split(",") if token.strip()})


def read_ticker_file(path: Path) -> list[str]:
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        return []
    if path.suffix.lower() == ".csv":
        rows = list(csv.DictReader(text.splitlines()))
        if rows:
            symbols = []
            for row in rows:
                symbol = (row.get("symbol") or row.get("ticker") or "").strip().upper()
                if symbol:
                    symbols.append(symbol)
            if symbols:
                return sorted(set(symbols))
    return sorted({line.strip().upper() for line in text.splitlines() if line.strip()})


def load_registry(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_registry(path: Path, rows: list[dict[str, str]]) -> None:
    fieldnames = list(rows[0].keys()) if rows else [
        "symbol",
        "artifact",
        "file_name",
        "source_kind",
        "source_path",
        "zip_entry",
        "materialized_path",
        "materialized_exists",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def normalize_rows(
    rows: list[dict[str, str]],
    *,
    allowed_symbols: set[str] | None,
    allowed_artifacts: set[str],
    allowed_source_kinds: set[str],
    only_missing: bool,
) -> list[dict[str, str]]:
    selected: list[dict[str, str]] = []
    for row in rows:
        symbol = (row.get("symbol") or "").strip().upper()
        artifact = (row.get("artifact") or "").strip().lower()
        source_kind = (row.get("source_kind") or "").strip()
        target_path = Path((row.get("materialized_path") or "").strip()) if (row.get("materialized_path") or "").strip() else None
        if allowed_symbols and symbol not in allowed_symbols:
            continue
        if artifact not in allowed_artifacts:
            continue
        if source_kind not in allowed_source_kinds:
            continue
        if only_missing and target_path is not None and target_path.exists():
            continue
        selected.append(row)
    return selected


def safe_link_or_copy(source: Path, target: Path, *, overwrite: bool) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        if not overwrite:
            return
        target.unlink()
    try:
        if source.resolve() != target.resolve():
            os.link(source, target)
        else:
            return
    except OSError:
        shutil.copy2(source, target)


def extract_zip_member(zip_handle: zipfile.ZipFile, member: str, target: Path, *, overwrite: bool) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists() and not overwrite:
        return
    with zip_handle.open(member) as src, tempfile.NamedTemporaryFile(delete=False, dir=str(target.parent)) as tmp:
        shutil.copyfileobj(src, tmp)
        temp_path = Path(tmp.name)
    if target.exists():
        target.unlink()
    temp_path.replace(target)


def materialize_row(
    row: dict[str, str],
    *,
    overwrite: bool,
    dry_run: bool,
    zip_cache: dict[str, zipfile.ZipFile],
) -> tuple[str, str]:
    source_kind = (row.get("source_kind") or "").strip()
    source_path = Path((row.get("source_path") or "").strip())
    zip_entry = (row.get("zip_entry") or "").strip()
    target_path = Path((row.get("materialized_path") or "").strip())
    artifact = (row.get("artifact") or "").strip().lower()

    if target_path.exists() and not overwrite:
        return "exists", f"{artifact}: target already present"
    if dry_run:
        return "would_materialize", f"{artifact}: {source_kind}"
    if not source_path.exists():
        return "missing_source", f"{artifact}: missing source {source_path}"

    try:
        if source_kind == "live":
            safe_link_or_copy(source_path, target_path, overwrite=overwrite)
        elif source_kind in {"bundle_zip", "archive_zip"}:
            if not zip_entry:
                return "missing_zip_entry", f"{artifact}: missing zip entry"
            cache_key = str(source_path.resolve())
            zip_handle = zip_cache.get(cache_key)
            if zip_handle is None:
                zip_handle = zipfile.ZipFile(source_path)
                zip_cache[cache_key] = zip_handle
            extract_zip_member(zip_handle, zip_entry, target_path, overwrite=overwrite)
        else:
            return "unsupported_source_kind", f"{artifact}: unsupported source kind {source_kind}"
    except KeyError:
        return "missing_zip_entry", f"{artifact}: zip entry not found {zip_entry}"
    except Exception as exc:
        return "error", f"{artifact}: {exc}"
    return "materialized", f"{artifact}: ok"


def write_manifest(symbol: str, rows: list[dict[str, str]], ready_base_dir: Path, *, dry_run: bool) -> None:
    target_dir = ready_base_dir / symbol.lower()
    manifest = {
        "symbol": symbol.upper(),
        "paths": {
            row["artifact"]: row["materialized_path"]
            for row in rows
            if row.get("artifact") in MANIFEST_ARTIFACTS
        },
    }
    if dry_run:
        return
    target_dir.mkdir(parents=True, exist_ok=True)
    (target_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def summarize_ticker(symbol: str, rows: list[dict[str, str]], status_rows: list[dict[str, Any]]) -> dict[str, Any]:
    artifact_status = {row["artifact"]: row["status"] for row in status_rows}
    required_ok = all(artifact_status.get(artifact) in {"materialized", "exists", "would_materialize"} for artifact in DEFAULT_ARTIFACTS)
    return {
        "symbol": symbol,
        "requested_artifact_count": len(rows),
        "materialized_artifact_count": sum(1 for row in status_rows if row["status"] == "materialized"),
        "existing_artifact_count": sum(1 for row in status_rows if row["status"] == "exists"),
        "planned_artifact_count": sum(1 for row in status_rows if row["status"] == "would_materialize"),
        "failed_artifact_count": sum(1 for row in status_rows if row["status"] not in {"materialized", "exists", "would_materialize"}),
        "is_ready_complete": required_ok,
        "statuses": dict(Counter(row["status"] for row in status_rows)),
    }


def main() -> None:
    args = build_parser().parse_args()
    registry_path = Path(args.registry_path).resolve()
    ready_base_dir = Path(args.ready_base_dir).resolve()
    report_dir = Path(args.report_dir).resolve()
    report_dir.mkdir(parents=True, exist_ok=True)

    allowed_symbols = set(parse_symbol_tokens(args.tickers))
    if args.ticker_file:
        allowed_symbols.update(read_ticker_file(Path(args.ticker_file).resolve()))
    if not allowed_symbols:
        allowed_symbols = None

    allowed_artifacts = {token.strip().lower() for token in args.artifacts.split(",") if token.strip()}
    allowed_source_kinds = {token.strip() for token in args.source_kinds.split(",") if token.strip()}

    registry_rows = load_registry(registry_path)
    selected_rows = normalize_rows(
        registry_rows,
        allowed_symbols=allowed_symbols,
        allowed_artifacts=allowed_artifacts,
        allowed_source_kinds=allowed_source_kinds,
        only_missing=bool(args.only_missing),
    )
    if args.max_tickers and args.max_tickers > 0:
        keep_symbols: list[str] = []
        for row in selected_rows:
            symbol = row["symbol"].upper()
            if symbol not in keep_symbols:
                keep_symbols.append(symbol)
            if len(keep_symbols) >= args.max_tickers:
                break
        keep_set = set(keep_symbols)
        selected_rows = [row for row in selected_rows if row["symbol"].upper() in keep_set]

    rows_by_symbol: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in selected_rows:
        rows_by_symbol[row["symbol"].upper()].append(row)

    status_rows: list[dict[str, Any]] = []
    ticker_summary: list[dict[str, Any]] = []
    zip_cache: dict[str, zipfile.ZipFile] = {}
    failure_count = 0

    try:
        for symbol in sorted(rows_by_symbol):
            symbol_rows = sorted(rows_by_symbol[symbol], key=lambda row: (row.get("artifact") or "", row.get("file_name") or ""))
            symbol_status_rows: list[dict[str, Any]] = []
            for row in symbol_rows:
                status, detail = materialize_row(row, overwrite=bool(args.overwrite), dry_run=bool(args.dry_run), zip_cache=zip_cache)
                target_path = Path((row.get("materialized_path") or "").strip())
                exists_after = target_path.exists()
                result = {
                    "symbol": symbol,
                    "artifact": row.get("artifact", ""),
                    "source_kind": row.get("source_kind", ""),
                    "source_path": row.get("source_path", ""),
                    "zip_entry": row.get("zip_entry", ""),
                    "materialized_path": str(target_path),
                    "status": status,
                    "detail": detail,
                    "exists_after": exists_after,
                }
                status_rows.append(result)
                symbol_status_rows.append(result)
                if status not in {"materialized", "exists", "would_materialize"}:
                    failure_count += 1
            if symbol_status_rows:
                write_manifest(symbol, symbol_rows, ready_base_dir, dry_run=bool(args.dry_run))
                ticker_summary.append(summarize_ticker(symbol, symbol_rows, symbol_status_rows))
    finally:
        for zip_handle in zip_cache.values():
            zip_handle.close()

    if args.update_registry:
        for row in registry_rows:
            target = Path((row.get("materialized_path") or "").strip())
            row["materialized_exists"] = "True" if target.exists() else "False"
        if not args.dry_run:
            write_registry(registry_path, registry_rows)

    summary = {
        "generated_at": datetime.now().isoformat(),
        "registry_path": str(registry_path),
        "ready_base_dir": str(ready_base_dir),
        "dry_run": bool(args.dry_run),
        "requested_symbol_count": len(rows_by_symbol),
        "requested_row_count": len(selected_rows),
        "status_counts": dict(Counter(row["status"] for row in status_rows)),
        "ticker_summary": ticker_summary,
        "materialized_ticker_count": sum(1 for row in ticker_summary if row["materialized_artifact_count"] > 0),
        "ready_complete_ticker_count": sum(1 for row in ticker_summary if row["is_ready_complete"]),
        "failure_count": failure_count,
    }

    (report_dir / "materialization_status.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    if status_rows:
        fieldnames = [
            "symbol",
            "artifact",
            "source_kind",
            "source_path",
            "zip_entry",
            "materialized_path",
            "status",
            "detail",
            "exists_after",
        ]
        with (report_dir / "materialization_status.csv").open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(status_rows)

    lines = [
        "# Backtester Ready Materialization",
        "",
        f"- Dry run: `{summary['dry_run']}`",
        f"- Requested symbols: `{summary['requested_symbol_count']}`",
        f"- Requested rows: `{summary['requested_row_count']}`",
        f"- Materialized tickers: `{summary['materialized_ticker_count']}`",
        f"- Ready-complete tickers: `{summary['ready_complete_ticker_count']}`",
        f"- Failure count: `{summary['failure_count']}`",
        "",
        "## Status Counts",
        "",
    ]
    for status, count in sorted(summary["status_counts"].items()):
        lines.append(f"- `{status}`: `{count}`")
    lines.append("")
    lines.append("## Ticker Summary")
    lines.append("")
    for row in ticker_summary[:40]:
        lines.append(
            f"- `{row['symbol']}`: ready_complete=`{row['is_ready_complete']}`, "
            f"materialized=`{row['materialized_artifact_count']}`, "
            f"existing=`{row['existing_artifact_count']}`, "
            f"failed=`{row['failed_artifact_count']}`"
        )
    (report_dir / "materialization_status.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(json.dumps({"report_dir": str(report_dir), "requested_symbol_count": len(rows_by_symbol), "failure_count": failure_count}, indent=2))
    if args.strict and failure_count:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
