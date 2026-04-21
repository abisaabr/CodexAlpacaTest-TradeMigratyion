from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
DEFAULT_OUTPUT_ROOT = ROOT / "output"
DEFAULT_REGISTRY_PATH = DEFAULT_OUTPUT_ROOT / "run_registry.jsonl"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build an operator-friendly report from run_registry.jsonl and discovered run manifests."
    )
    parser.add_argument("--output-root", default=str(DEFAULT_OUTPUT_ROOT))
    parser.add_argument("--registry-path", default=str(DEFAULT_REGISTRY_PATH))
    parser.add_argument(
        "--report-dir",
        default=str(DEFAULT_OUTPUT_ROOT / f"run_registry_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}"),
    )
    return parser


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames = sorted({key for row in rows for key in row.keys()})
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    key: json.dumps(value) if isinstance(value, (list, dict)) else value
                    for key, value in row.items()
                }
            )


def parse_iso_timestamp(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    normalized = value.strip()
    if normalized.endswith("Z"):
        normalized = normalized[:-1] + "+00:00"
    try:
        return datetime.fromisoformat(normalized)
    except ValueError:
        return None


def iso_or_blank(moment: datetime | None) -> str:
    return moment.isoformat() if moment is not None else ""


def load_registry_events(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    events: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.lstrip("\ufeff").strip()
        if not stripped:
            continue
        try:
            payload = json.loads(stripped)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            events.append(payload)
    return events


def scan_run_manifests(output_root: Path) -> list[Path]:
    manifests: list[Path] = []
    for path in output_root.rglob("run_manifest.json"):
        manifests.append(path)
    return sorted(manifests)


def descriptor_exists(descriptor: Any) -> bool:
    if not isinstance(descriptor, dict):
        return False
    return bool(descriptor.get("exists", False))


def as_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    return []


def normalize_run(
    *,
    run_id: str,
    manifest: dict[str, Any] | None,
    manifest_path: Path | None,
    events: list[dict[str, Any]],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    parameters = manifest.get("parameters", {}) if isinstance(manifest, dict) else {}
    lineage = manifest.get("lineage", {}) if isinstance(manifest, dict) else {}
    ticker_states = manifest.get("ticker_states", {}) if isinstance(manifest, dict) else {}
    result_snapshot = manifest.get("result_snapshot", {}) if isinstance(manifest, dict) else {}
    master_outputs = manifest.get("master_outputs", {}) if isinstance(manifest, dict) else {}

    sorted_events = sorted(
        events,
        key=lambda item: (
            parse_iso_timestamp(item.get("timestamp_iso")) or datetime.min,
            str(item.get("event", "")),
        ),
    )
    latest_event = sorted_events[-1] if sorted_events else None
    latest_event_status = str(latest_event.get("status", "")) if latest_event else ""
    latest_event_type = str(latest_event.get("event", "")) if latest_event else ""
    created_at = parse_iso_timestamp(manifest.get("created_at_iso")) if isinstance(manifest, dict) else None
    updated_at = parse_iso_timestamp(manifest.get("updated_at_iso")) if isinstance(manifest, dict) else None
    latest_event_at = parse_iso_timestamp(latest_event.get("timestamp_iso")) if latest_event else None
    effective_updated_at = max(
        [moment for moment in (updated_at, latest_event_at, created_at) if moment is not None],
        default=None,
    )

    ticker_state_counts = Counter()
    ticker_rows: list[dict[str, Any]] = []
    for ticker, payload in sorted(ticker_states.items()):
        status = str(payload.get("status", "unknown")) if isinstance(payload, dict) else "unknown"
        ticker_state_counts[status] += 1
        ticker_rows.append(
            {
                "run_id": run_id,
                "ticker": ticker,
                "status": status,
                "phase": payload.get("phase", "") if isinstance(payload, dict) else "",
                "summary_path": payload.get("summary_path", "") if isinstance(payload, dict) else "",
                "message": payload.get("message", "") if isinstance(payload, dict) else "",
                "updated_at_iso": payload.get("updated_at_iso", "") if isinstance(payload, dict) else "",
            }
        )

    event_type_counts = Counter(str(item.get("event", "unknown")) for item in sorted_events)
    event_status_counts = Counter(str(item.get("status", "unknown")) for item in sorted_events)
    git_repos = as_list(lineage.get("code", {}).get("git_repositories")) if isinstance(lineage, dict) else []
    git_refs = [
        f"{repo.get('branch') or '(detached)'}@{str(repo.get('head', ''))[:12]}"
        for repo in git_repos
        if isinstance(repo, dict)
    ]
    ticker_inputs = lineage.get("ticker_inputs", {}) if isinstance(lineage, dict) else {}
    master_output_count = sum(1 for descriptor in master_outputs.values() if descriptor_exists(descriptor))
    shared_account = result_snapshot.get("shared_account") if isinstance(result_snapshot, dict) else None
    qqq_only = result_snapshot.get("qqq_only") if isinstance(result_snapshot, dict) else None

    warnings: list[str] = []
    if manifest is None:
        warnings.append("missing_manifest")
    if not sorted_events:
        warnings.append("missing_registry_events")
    if latest_event_status and isinstance(manifest, dict) and manifest.get("status") != latest_event_status:
        warnings.append("manifest_registry_status_mismatch")
    if isinstance(manifest, dict) and manifest.get("status") in {"running", "pending"}:
        warnings.append("requires_operator_attention")

    run_row = {
        "run_id": run_id,
        "status": str(manifest.get("status", latest_event_status or "unknown")) if isinstance(manifest, dict) else (latest_event_status or "unknown"),
        "manifest_status": str(manifest.get("status", "")) if isinstance(manifest, dict) else "",
        "latest_event_status": latest_event_status,
        "latest_event_type": latest_event_type,
        "created_at_iso": iso_or_blank(created_at),
        "updated_at_iso": iso_or_blank(updated_at),
        "latest_event_at_iso": iso_or_blank(latest_event_at),
        "effective_updated_at_iso": iso_or_blank(effective_updated_at),
        "research_dir": str(manifest.get("research_dir", "")) if isinstance(manifest, dict) else (str(latest_event.get("research_dir", "")) if latest_event else ""),
        "manifest_path": str(manifest_path.resolve()) if manifest_path is not None else "",
        "has_manifest": manifest is not None,
        "ticker_count": len(as_list(parameters.get("tickers"))),
        "tickers": as_list(parameters.get("tickers")),
        "strategy_set": str(parameters.get("strategy_set", "")),
        "selection_profile": str(parameters.get("selection_profile", "")),
        "timing_profiles": as_list(parameters.get("timing_profiles")),
        "family_include_filters": as_list(parameters.get("family_include_filters")),
        "family_exclude_filters": as_list(parameters.get("family_exclude_filters")),
        "continue_on_error": bool(parameters.get("continue_on_error", False)),
        "reuse_completed_tickers": bool(parameters.get("reuse_completed_tickers", False)),
        "hostname": str(lineage.get("machine", {}).get("hostname", "")) if isinstance(lineage, dict) else "",
        "platform": str(lineage.get("machine", {}).get("platform", "")) if isinstance(lineage, dict) else "",
        "python_executable": str(lineage.get("machine", {}).get("python_executable", "")) if isinstance(lineage, dict) else "",
        "git_refs": git_refs,
        "git_repo_count": len(git_refs),
        "input_ticker_count": len(ticker_inputs) if isinstance(ticker_inputs, dict) else 0,
        "master_output_count": master_output_count,
        "event_count": len(sorted_events),
        "event_type_counts": dict(sorted(event_type_counts.items())),
        "event_status_counts": dict(sorted(event_status_counts.items())),
        "ticker_state_counts": dict(sorted(ticker_state_counts.items())),
        "successful_tickers": as_list(result_snapshot.get("successful_tickers")) if isinstance(result_snapshot, dict) else [],
        "failed_tickers": as_list(result_snapshot.get("failed_tickers")) if isinstance(result_snapshot, dict) else [],
        "shared_account_final_equity": float(shared_account.get("final_equity")) if isinstance(shared_account, dict) and shared_account.get("final_equity") is not None else None,
        "shared_account_total_return_pct": float(shared_account.get("total_return_pct")) if isinstance(shared_account, dict) and shared_account.get("total_return_pct") is not None else None,
        "shared_account_max_drawdown_pct": float(shared_account.get("max_drawdown_pct")) if isinstance(shared_account, dict) and shared_account.get("max_drawdown_pct") is not None else None,
        "qqq_only_final_equity": float(qqq_only.get("final_equity")) if isinstance(qqq_only, dict) and qqq_only.get("final_equity") is not None else None,
        "message": str(manifest.get("message", "")) if isinstance(manifest, dict) else "",
        "warnings": warnings,
    }
    return run_row, ticker_rows


def build_overview(run_rows: list[dict[str, Any]], registry_events: list[dict[str, Any]]) -> dict[str, Any]:
    status_counts = Counter(str(row.get("status", "unknown")) for row in run_rows)
    strategy_set_counts = Counter(str(row.get("strategy_set", "")) for row in run_rows if row.get("strategy_set"))
    selection_profile_counts = Counter(str(row.get("selection_profile", "")) for row in run_rows if row.get("selection_profile"))
    ticker_counts = Counter()
    git_ref_counts = Counter()
    for row in run_rows:
        for ticker in row.get("tickers", []):
            ticker_counts[str(ticker)] += 1
        for git_ref in row.get("git_refs", []):
            git_ref_counts[str(git_ref)] += 1

    recent_runs = sorted(run_rows, key=lambda row: parse_iso_timestamp(row.get("effective_updated_at_iso")) or datetime.min, reverse=True)[:10]
    attention_runs = [
        row for row in recent_runs
        if row.get("status") in {"running", "pending", "failed", "cancelled"} or row.get("warnings")
    ]

    return {
        "total_runs": len(run_rows),
        "total_registry_events": len(registry_events),
        "status_counts": dict(sorted(status_counts.items())),
        "strategy_set_counts": dict(sorted(strategy_set_counts.items())),
        "selection_profile_counts": dict(sorted(selection_profile_counts.items())),
        "unique_ticker_count": len(ticker_counts),
        "ticker_coverage_counts": dict(sorted(ticker_counts.items())),
        "git_ref_counts": dict(sorted(git_ref_counts.items())),
        "recent_runs": [
            {
                "run_id": row["run_id"],
                "status": row["status"],
                "strategy_set": row["strategy_set"],
                "selection_profile": row["selection_profile"],
                "tickers": row["tickers"],
                "effective_updated_at_iso": row["effective_updated_at_iso"],
                "research_dir": row["research_dir"],
            }
            for row in recent_runs
        ],
        "attention_runs": [
            {
                "run_id": row["run_id"],
                "status": row["status"],
                "warnings": row["warnings"],
                "message": row["message"],
                "effective_updated_at_iso": row["effective_updated_at_iso"],
                "research_dir": row["research_dir"],
            }
            for row in attention_runs
        ],
    }


def render_markdown(*, overview: dict[str, Any], run_rows: list[dict[str, Any]]) -> str:
    lines = ["# Run Registry Report", ""]
    lines.append("## Overview")
    lines.append(f"- Total runs: `{overview['total_runs']}`")
    lines.append(f"- Total registry events: `{overview['total_registry_events']}`")
    lines.append(f"- Unique tickers touched by manifests: `{overview['unique_ticker_count']}`")
    lines.append(f"- Status counts: `{json.dumps(overview['status_counts'], sort_keys=True)}`")
    lines.append(f"- Strategy set counts: `{json.dumps(overview['strategy_set_counts'], sort_keys=True)}`")
    lines.append(f"- Selection profile counts: `{json.dumps(overview['selection_profile_counts'], sort_keys=True)}`")
    if overview["git_ref_counts"]:
        lines.append(f"- Observed code refs: `{json.dumps(overview['git_ref_counts'], sort_keys=True)}`")
    lines.append("")

    lines.append("## Recent Runs")
    if not overview["recent_runs"]:
        lines.append("- No runs found.")
    else:
        for row in overview["recent_runs"]:
            lines.append(
                f"- `{row['run_id']}` | `{row['status']}` | `{row['strategy_set']}` / `{row['selection_profile']}` | "
                f"{', '.join(row['tickers']) or '(no tickers)'} | `{row['effective_updated_at_iso']}`"
            )
    lines.append("")

    lines.append("## Attention Queue")
    if not overview["attention_runs"]:
        lines.append("- No runs currently need attention.")
    else:
        for row in overview["attention_runs"]:
            warning_text = ", ".join(row["warnings"]) if row["warnings"] else "none"
            message_text = row["message"] or "(no message)"
            lines.append(f"- `{row['run_id']}` | `{row['status']}` | warnings: `{warning_text}` | {message_text}")
    lines.append("")

    lines.append("## Run Details")
    if not run_rows:
        lines.append("- No run rows available.")
    else:
        for row in sorted(run_rows, key=lambda item: parse_iso_timestamp(item.get("effective_updated_at_iso")) or datetime.min, reverse=True):
            lines.append(f"### `{row['run_id']}`")
            lines.append(f"- Status: `{row['status']}`")
            lines.append(f"- Strategy set: `{row['strategy_set']}`")
            lines.append(f"- Selection profile: `{row['selection_profile']}`")
            lines.append(f"- Tickers: `{', '.join(row['tickers']) or '(none)'}`")
            lines.append(f"- Timing profiles: `{', '.join(row['timing_profiles']) or '(none)'}`")
            lines.append(f"- Research dir: `{row['research_dir']}`")
            lines.append(f"- Updated: `{row['effective_updated_at_iso']}`")
            lines.append(f"- Ticker state counts: `{json.dumps(row['ticker_state_counts'], sort_keys=True)}`")
            if row["shared_account_final_equity"] is not None:
                lines.append(
                    f"- Shared-account result: final equity `{row['shared_account_final_equity']:.2f}`, "
                    f"return `{row['shared_account_total_return_pct']:.2f}%`, "
                    f"max drawdown `{row['shared_account_max_drawdown_pct']:.2f}%`"
                )
            lines.append(f"- Git refs: `{', '.join(row['git_refs']) or '(none recorded)'}`")
            lines.append(f"- Manifest path: `{row['manifest_path'] or '(none)'}`")
            if row["warnings"]:
                lines.append(f"- Warnings: `{', '.join(row['warnings'])}`")
            if row["message"]:
                lines.append(f"- Message: {row['message']}")
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    args = build_parser().parse_args()
    output_root = Path(args.output_root).resolve()
    registry_path = Path(args.registry_path).resolve()
    report_dir = Path(args.report_dir).resolve()
    report_dir.mkdir(parents=True, exist_ok=True)

    registry_events = load_registry_events(registry_path)
    manifest_paths = scan_run_manifests(output_root)

    events_by_run: dict[str, list[dict[str, Any]]] = {}
    for payload in registry_events:
        run_id = str(payload.get("run_id", "")).strip()
        if not run_id:
            continue
        events_by_run.setdefault(run_id, []).append(payload)

    manifests_by_run: dict[str, tuple[dict[str, Any], Path]] = {}
    for path in manifest_paths:
        try:
            payload = load_json(path)
        except Exception:
            continue
        if not isinstance(payload, dict):
            continue
        run_id = str(payload.get("run_id", "")).strip()
        if not run_id:
            continue
        manifests_by_run[run_id] = (payload, path)

    all_run_ids = sorted(set(events_by_run) | set(manifests_by_run))
    run_rows: list[dict[str, Any]] = []
    ticker_rows: list[dict[str, Any]] = []
    for run_id in all_run_ids:
        manifest_payload: dict[str, Any] | None = None
        manifest_path: Path | None = None
        if run_id in manifests_by_run:
            manifest_payload, manifest_path = manifests_by_run[run_id]
        row, per_ticker_rows = normalize_run(
            run_id=run_id,
            manifest=manifest_payload,
            manifest_path=manifest_path,
            events=events_by_run.get(run_id, []),
        )
        run_rows.append(row)
        ticker_rows.extend(per_ticker_rows)

    overview = build_overview(run_rows, registry_events)
    payload = {
        "generated_at_iso": datetime.now().astimezone().isoformat(),
        "inputs": {
            "output_root": str(output_root),
            "registry_path": str(registry_path),
            "manifest_count": len(manifest_paths),
            "registry_event_count": len(registry_events),
        },
        "overview": overview,
        "runs": run_rows,
        "ticker_states": ticker_rows,
    }

    write_json(report_dir / "run_registry_report.json", payload)
    write_csv(report_dir / "run_registry_runs.csv", run_rows)
    write_csv(report_dir / "run_registry_ticker_states.csv", ticker_rows)
    (report_dir / "run_registry_report.md").write_text(
        render_markdown(overview=overview, run_rows=run_rows),
        encoding="utf-8",
    )
    print(f"wrote run-registry report to {report_dir}")


if __name__ == "__main__":
    main()
