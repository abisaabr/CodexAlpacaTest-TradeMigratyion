from __future__ import annotations

import argparse
import csv
import json
import zipfile
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path, PurePosixPath
from typing import Any


ROOT = Path(__file__).resolve().parent
DEFAULT_REPORT_DIR = ROOT / "output" / f"bundle_registry_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
DEFAULT_REQUIRED_ARTIFACTS = ("dense", "wide", "universe")
DEFAULT_OPTIONAL_ARTIFACTS = ("audit",)

ARTIFACT_CANDIDATE_NAMES = {
    "dense": ("{ticker}_365d_option_1min_dense.parquet",),
    "wide": ("{ticker}_365d_option_1min_wide_backtest.parquet",),
    "universe": ("{ticker}_365d_option_daily_universe.parquet",),
    "audit": ("{ticker}_365d_audit_report.json",),
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build a backtester registry that points backtester_ready materialization at archived bundle zips."
    )
    parser.add_argument("--bundle-dir", required=True, help="Directory holding *_365d_bundle.zip archives.")
    parser.add_argument("--registry-path", required=True, help="Output CSV path for backtester_registry.csv.")
    parser.add_argument("--ready-base-dir", required=True, help="Target backtester_ready directory used for materialized_path values.")
    parser.add_argument("--report-dir", default=str(DEFAULT_REPORT_DIR), help="Directory for summary artifacts.")
    parser.add_argument("--tickers", default="", help="Optional comma-separated ticker filter.")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail if any requested symbol is missing a required dense/wide/universe artifact.",
    )
    return parser


def parse_tickers(text: str) -> set[str]:
    return {token.strip().upper() for token in text.split(",") if token.strip()}


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def find_bundle_paths(bundle_dir: Path, allowed_symbols: set[str] | None) -> list[Path]:
    bundle_paths = sorted(bundle_dir.glob("*_365d_bundle.zip"))
    if not allowed_symbols:
        return bundle_paths
    filtered: list[Path] = []
    for path in bundle_paths:
        symbol = path.name.replace("_365d_bundle.zip", "").upper()
        if symbol in allowed_symbols:
            filtered.append(path)
    return filtered


def zip_entry_lookup(bundle_path: Path) -> dict[str, list[str]]:
    with zipfile.ZipFile(bundle_path) as archive:
        lookup: dict[str, list[str]] = defaultdict(list)
        for name in archive.namelist():
            lookup[PurePosixPath(name).name].append(name)
    return lookup


def resolve_entry(entry_lookup: dict[str, list[str]], *, symbol: str, artifact: str) -> str:
    candidates = ARTIFACT_CANDIDATE_NAMES[artifact]
    for candidate in candidates:
        file_name = candidate.format(ticker=symbol.lower())
        matches = entry_lookup.get(file_name, [])
        if matches:
            return matches[0]
    return ""


def build_registry_row(
    *,
    symbol: str,
    artifact: str,
    file_name: str,
    source_kind: str,
    source_path: Path,
    zip_entry: str,
    ready_base_dir: Path,
) -> dict[str, str]:
    materialized_path = ready_base_dir / symbol.lower() / file_name
    return {
        "symbol": symbol,
        "artifact": artifact,
        "file_name": file_name,
        "source_kind": source_kind,
        "source_path": str(source_path.resolve()),
        "zip_entry": zip_entry,
        "materialized_path": str(materialized_path.resolve()),
        "materialized_exists": "True" if materialized_path.exists() else "False",
    }


def build_symbol_rows(bundle_path: Path, ready_base_dir: Path) -> tuple[list[dict[str, str]], dict[str, Any]]:
    symbol = bundle_path.name.replace("_365d_bundle.zip", "").upper()
    entry_lookup = zip_entry_lookup(bundle_path)
    rows: list[dict[str, str]] = []
    available_artifacts: list[str] = []
    missing_required: list[str] = []
    missing_optional: list[str] = []

    for artifact in (*DEFAULT_REQUIRED_ARTIFACTS, *DEFAULT_OPTIONAL_ARTIFACTS):
        file_name = ARTIFACT_CANDIDATE_NAMES[artifact][0].format(ticker=symbol.lower())
        entry_name = resolve_entry(entry_lookup, symbol=symbol, artifact=artifact)
        if entry_name:
            rows.append(
                build_registry_row(
                    symbol=symbol,
                    artifact=artifact,
                    file_name=file_name,
                    source_kind="bundle_zip",
                    source_path=bundle_path,
                    zip_entry=entry_name,
                    ready_base_dir=ready_base_dir,
                )
            )
            available_artifacts.append(artifact)
            continue

        sidecar_path = bundle_path.parent / file_name
        if sidecar_path.exists():
            rows.append(
                build_registry_row(
                    symbol=symbol,
                    artifact=artifact,
                    file_name=file_name,
                    source_kind="live",
                    source_path=sidecar_path,
                    zip_entry="",
                    ready_base_dir=ready_base_dir,
                )
            )
            available_artifacts.append(artifact)
            continue

        if artifact in DEFAULT_REQUIRED_ARTIFACTS:
            missing_required.append(artifact)
        else:
            missing_optional.append(artifact)

    summary = {
        "symbol": symbol,
        "bundle_path": str(bundle_path.resolve()),
        "row_count": len(rows),
        "available_artifacts": sorted(available_artifacts),
        "missing_required_artifacts": sorted(missing_required),
        "missing_optional_artifacts": sorted(missing_optional),
        "source_kinds": dict(Counter(row["source_kind"] for row in rows)),
    }
    return rows, summary


def write_registry(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
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


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "# Bundle Registry Build",
        "",
        f"- Bundle directory: `{payload['bundle_dir']}`",
        f"- Registry path: `{payload['registry_path']}`",
        f"- Ready base dir: `{payload['ready_base_dir']}`",
        f"- Bundles scanned: `{payload['bundle_count']}`",
        f"- Registry rows written: `{payload['row_count']}`",
        f"- Symbols with missing required artifacts: `{payload['symbols_missing_required_count']}`",
        "",
        "## Symbols",
        "",
    ]
    for row in payload["symbols"]:
        lines.append(
            f"- `{row['symbol']}`: available=`{','.join(row['available_artifacts']) or 'none'}`, "
            f"missing_required=`{','.join(row['missing_required_artifacts']) or 'none'}`, "
            f"missing_optional=`{','.join(row['missing_optional_artifacts']) or 'none'}`"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = build_parser().parse_args()
    bundle_dir = Path(args.bundle_dir).resolve()
    registry_path = Path(args.registry_path).resolve()
    ready_base_dir = Path(args.ready_base_dir).resolve()
    report_dir = Path(args.report_dir).resolve()
    allowed_symbols = parse_tickers(args.tickers) if args.tickers else None

    if not bundle_dir.exists():
        raise FileNotFoundError(f"bundle directory not found: {bundle_dir}")

    bundle_paths = find_bundle_paths(bundle_dir, allowed_symbols)
    symbol_rows: list[dict[str, str]] = []
    symbol_summaries: list[dict[str, Any]] = []

    for bundle_path in bundle_paths:
        rows, summary = build_symbol_rows(bundle_path, ready_base_dir)
        symbol_rows.extend(rows)
        symbol_summaries.append(summary)

    symbol_rows.sort(key=lambda row: (row["symbol"], row["artifact"], row["file_name"]))
    symbol_summaries.sort(key=lambda row: row["symbol"])
    write_registry(registry_path, symbol_rows)

    missing_required_symbols = [
        row["symbol"]
        for row in symbol_summaries
        if row["missing_required_artifacts"]
    ]
    payload = {
        "generated_at": datetime.now().isoformat(),
        "bundle_dir": str(bundle_dir),
        "registry_path": str(registry_path),
        "ready_base_dir": str(ready_base_dir),
        "bundle_count": len(bundle_paths),
        "row_count": len(symbol_rows),
        "symbol_count": len(symbol_summaries),
        "symbols_missing_required_count": len(missing_required_symbols),
        "symbols_missing_required": missing_required_symbols,
        "symbols": symbol_summaries,
    }

    report_dir.mkdir(parents=True, exist_ok=True)
    write_json(report_dir / "bundle_registry_summary.json", payload)
    write_markdown(report_dir / "bundle_registry_summary.md", payload)

    print(json.dumps(
        {
            "registry_path": str(registry_path),
            "bundle_count": len(bundle_paths),
            "row_count": len(symbol_rows),
            "symbols_missing_required_count": len(missing_required_symbols),
        },
        indent=2,
    ))
    if args.strict and missing_required_symbols:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
