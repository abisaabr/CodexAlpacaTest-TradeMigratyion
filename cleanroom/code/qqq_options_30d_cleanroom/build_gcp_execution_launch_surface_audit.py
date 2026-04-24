from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[2]
DEFAULT_REPORT_DIR = REPO_ROOT / "docs" / "gcp_foundation"
DEFAULT_PROJECT_ID = "codexalpaca"
DEFAULT_VM_NAME = "vm-execution-paper-01"
DEFAULT_ZONE = "us-east1-b"
DEFAULT_EXPECTED_RUNNER_COMMIT = "f0080066c68d883286f4cb1b9c9e0edc601adf8d"
WINDOWS_DISABLED_TASK_STATE = 1
WINDOWS_READY_TASK_STATE = 3
PROJECT_TASK_MATCH_TOKENS = (
    "Alpaca",
    "Codex",
    "Ticker",
    "Portfolio",
    "Stage27",
    "Governed",
    "QQQ",
    "Trader",
    "Trade",
)
KNOWN_OS_TASKS = {
    ("GovernedFeatureUsageProcessing", "\\Microsoft\\Windows\\Flighting\\FeatureConfig\\"),
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build the local launch-surface audit packet for the sanctioned VM paper session."
    )
    parser.add_argument("--report-dir", default=str(DEFAULT_REPORT_DIR))
    parser.add_argument("--project-id", default=DEFAULT_PROJECT_ID)
    parser.add_argument("--vm-name", default=DEFAULT_VM_NAME)
    parser.add_argument("--zone", default=DEFAULT_ZONE)
    parser.add_argument("--expected-runner-commit", default=DEFAULT_EXPECTED_RUNNER_COMMIT)
    parser.add_argument("--broker-position-count", type=int, required=True)
    parser.add_argument("--broker-open-order-count", type=int, required=True)
    parser.add_argument("--watch-duration-seconds", type=int, required=True)
    parser.add_argument("--watch-start-utc", default="")
    parser.add_argument("--watch-end-utc", default="")
    parser.add_argument("--watch-samples", type=int, default=0)
    parser.add_argument("--watch-sample-interval-seconds", type=int, default=0)
    parser.add_argument("--watch-position-count-all-samples", type=int, required=True)
    parser.add_argument("--watch-open-order-count-all-samples", type=int, required=True)
    parser.add_argument("--watch-newest-order-created-at", default="")
    parser.add_argument("--scheduled-task-json", default="")
    parser.add_argument("--local-process-count", type=int, default=0)
    parser.add_argument("--local-process-note", default="")
    parser.add_argument("--vm-process-clear", action="store_true")
    parser.add_argument("--vm-process-note", default="")
    parser.add_argument("--vm-runner-commit", default="")
    parser.add_argument("--vm-runner-branch", default="codex/qqq-paper-portfolio")
    parser.add_argument("--vm-source-stamp-json", default="")
    parser.add_argument("--unattributed-order-source-status", default="not_fully_attributed")
    parser.add_argument("--incident-date", default="2026-04-24")
    return parser


def read_json(path: Path) -> Any:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _issue(severity: str, code: str, message: str) -> dict[str, str]:
    return {"severity": severity, "code": code, "message": message}


def _task_name(row: dict[str, Any]) -> str:
    return str(row.get("TaskName") or row.get("task_name") or "")


def _task_path(row: dict[str, Any]) -> str:
    return str(row.get("TaskPath") or row.get("task_path") or "\\")


def _task_state(row: dict[str, Any]) -> int | str | None:
    state = row.get("State", row.get("state"))
    if isinstance(state, int):
        return state
    text = str(state or "").strip()
    if text.isdigit():
        return int(text)
    if text.lower() == "disabled":
        return WINDOWS_DISABLED_TASK_STATE
    if text.lower() == "ready":
        return WINDOWS_READY_TASK_STATE
    return text or None


def _is_known_os_task(row: dict[str, Any]) -> bool:
    return (_task_name(row), _task_path(row)) in KNOWN_OS_TASKS


def _looks_project_related(row: dict[str, Any]) -> bool:
    haystack = f"{_task_name(row)} {_task_path(row)}"
    return any(token.lower() in haystack.lower() for token in PROJECT_TASK_MATCH_TOKENS)


def classify_scheduled_tasks(task_rows: list[dict[str, Any]]) -> dict[str, Any]:
    disabled_project_or_legacy_tasks: list[str] = []
    remaining_ready_matches: list[dict[str, str]] = []
    blocking_ready_tasks: list[dict[str, str]] = []
    ignored_rows: list[str] = []

    for row in task_rows:
        if not _looks_project_related(row):
            ignored_rows.append(_task_name(row))
            continue
        state = _task_state(row)
        if state == WINDOWS_DISABLED_TASK_STATE:
            disabled_project_or_legacy_tasks.append(_task_name(row))
            continue
        if state == WINDOWS_READY_TASK_STATE and _is_known_os_task(row):
            remaining_ready_matches.append(
                {
                    "task_name": _task_name(row),
                    "task_path": _task_path(row),
                    "classification": "Windows OS feature task, not project launch surface",
                }
            )
            continue
        if state == WINDOWS_READY_TASK_STATE:
            blocking_ready_tasks.append(
                {
                    "task_name": _task_name(row),
                    "task_path": _task_path(row),
                    "state": str(state),
                }
            )
            continue
        blocking_ready_tasks.append(
            {
                "task_name": _task_name(row),
                "task_path": _task_path(row),
                "state": str(state),
            }
        )

    return {
        "project_task_state_meaning": {
            "1": "Disabled",
            "3": "Ready",
        },
        "disabled_project_or_legacy_tasks": sorted(disabled_project_or_legacy_tasks),
        "remaining_ready_matches": remaining_ready_matches,
        "blocking_ready_tasks": blocking_ready_tasks,
        "ignored_non_project_matches": sorted(name for name in ignored_rows if name),
    }


def build_payload(
    *,
    report_dir: Path,
    project_id: str,
    vm_name: str,
    zone: str,
    expected_runner_commit: str,
    broker_position_count: int,
    broker_open_order_count: int,
    watch_duration_seconds: int,
    watch_start_utc: str,
    watch_end_utc: str,
    watch_samples: int,
    watch_sample_interval_seconds: int,
    watch_position_count_all_samples: int,
    watch_open_order_count_all_samples: int,
    watch_newest_order_created_at: str,
    scheduled_task_rows: list[dict[str, Any]],
    local_process_count: int,
    local_process_note: str,
    vm_process_clear: bool,
    vm_process_note: str,
    vm_runner_commit: str,
    vm_runner_branch: str,
    vm_source_stamp: dict[str, Any] | None = None,
    unattributed_order_source_status: str = "not_fully_attributed",
    incident_date: str = "2026-04-24",
    now: datetime | None = None,
) -> dict[str, Any]:
    now = now or datetime.now().astimezone()
    vm_source_stamp = vm_source_stamp or {}
    observed_vm_runner_commit = vm_runner_commit or str(vm_source_stamp.get("runner_commit") or "")
    observed_vm_runner_branch = vm_runner_branch or str(vm_source_stamp.get("runner_branch") or "")
    task_classification = classify_scheduled_tasks(scheduled_task_rows)

    broker_flat = broker_position_count == 0 and broker_open_order_count == 0
    watch_clean = (
        watch_duration_seconds >= 180
        and watch_position_count_all_samples == 0
        and watch_open_order_count_all_samples == 0
    )
    local_process_clear = local_process_count == 0
    vm_runner_commit_matches = (
        bool(expected_runner_commit)
        and observed_vm_runner_commit == expected_runner_commit
    )

    issues: list[dict[str, str]] = []
    if not broker_flat:
        issues.append(
            _issue(
                "error",
                "broker_not_flat",
                "Broker positions and open orders must both be zero before arming.",
            )
        )
    if not watch_clean:
        issues.append(
            _issue(
                "error",
                "no_new_order_watch_not_clean",
                "Post-fencing no-new-order watch must run at least 180 seconds with zero positions and zero open orders in every sample.",
            )
        )
    if task_classification["blocking_ready_tasks"]:
        issues.append(
            _issue(
                "error",
                "local_scheduled_launch_surface_ready",
                "One or more local project-related scheduled tasks are still ready or in an unknown state.",
            )
        )
    if not local_process_clear:
        issues.append(
            _issue(
                "error",
                "local_broker_capable_process_observed",
                "One or more local project-related broker-capable processes were observed.",
            )
        )
    if not vm_process_clear:
        issues.append(
            _issue(
                "error",
                "vm_runner_process_observed",
                "The sanctioned VM must not already have a runner process active before arming.",
            )
        )
    if not vm_runner_commit_matches:
        issues.append(
            _issue(
                "error",
                "vm_runner_commit_mismatch",
                "The sanctioned VM runner commit must match the expected patched commit before arming.",
            )
        )

    status = "local_broker_capable_surfaces_fenced_broker_flat"
    if any(issue["severity"] == "error" for issue in issues):
        status = "blocked_launch_surface_audit"

    return {
        "packet": "gcp_execution_launch_surface_audit",
        "as_of": now.isoformat(),
        "generated_at": now.isoformat(),
        "status": status,
        "scope": (
            "Repeatable local and sanctioned-VM launch-surface audit before the "
            "bounded sanctioned paper session."
        ),
        "report_dir": str(report_dir),
        "broker_facing": False,
        "live_manifest_effect": "none",
        "risk_policy_effect": "none",
        "incident_date": incident_date,
        "broker_state": {
            "read_only_check_after_fencing": (
                f"position_count={broker_position_count}, "
                f"open_order_count={broker_open_order_count}"
            ),
            "broker_flat": broker_flat,
            "post_fencing_no_new_order_watch": {
                "duration_seconds": watch_duration_seconds,
                "start_utc": watch_start_utc,
                "end_utc": watch_end_utc,
                "samples": watch_samples,
                "sample_interval_seconds": watch_sample_interval_seconds,
                "position_count_all_samples": watch_position_count_all_samples,
                "open_order_count_all_samples": watch_open_order_count_all_samples,
                "newest_order_created_at_all_samples": watch_newest_order_created_at,
                "watch_clean": watch_clean,
            },
        },
        "local_windows_task_scheduler": {
            **task_classification,
            "material_change": (
                "Project and legacy local scheduled tasks must remain disabled; "
                "the sanctioned execution path is the VM only."
            ),
        },
        "local_process_audit": {
            "status": "no_active_project_broker_capable_process_observed"
            if local_process_clear
            else "blocked_local_project_process_observed",
            "observed_process_count": local_process_count,
            "note": local_process_note
            or "Matching local processes must be limited to inspection commands only.",
        },
        "sanctioned_vm_audit": {
            "vm_name": vm_name,
            "gcp_project": project_id,
            "zone": zone,
            "process_check": "no active runner process observed"
            if vm_process_clear
            else "blocked_active_runner_process_observed",
            "process_note": vm_process_note,
            "source_stamp": {
                **vm_source_stamp,
                "runner_commit": observed_vm_runner_commit,
                "runner_branch": observed_vm_runner_branch,
            },
            "expected_runner_commit": expected_runner_commit,
            "runner_commit_matches_expected": vm_runner_commit_matches,
        },
        "unattributed_order_source": {
            "status": unattributed_order_source_status,
            "evidence": [
                "The unattributed-order incident is cleared for arming only when the broker is flat, local launch surfaces are fenced, the VM is idle, and the no-new-order watch is clean.",
                "If a new broker order appears without explicit operator launch, do not arm the window.",
            ],
            "governance_treatment": (
                "Keep this as a pre-arm review gate until repeated clean checks "
                "show no autonomous order source remains."
            ),
        },
        "issues": issues,
        "hard_rules_preserved": [
            "No trading session was started.",
            "No exclusive execution window was armed.",
            "No live manifest was modified.",
            "No strategy selection or risk policy was changed.",
            "No raw session exhaust or raw trade log was committed.",
        ],
        "next_safe_operator_gate": [
            "Immediately before any exclusive-window arm, re-run broker flat/open-order check.",
            "Re-run local scheduled task and process launch-surface checks.",
            "Re-run VM process/source-stamp check.",
            "Run a short no-new-order watch; if a new broker order appears without an explicit operator launch, stop and investigate instead of arming.",
        ],
    }


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    broker_state = payload["broker_state"]
    watch = broker_state["post_fencing_no_new_order_watch"]
    scheduler = payload["local_windows_task_scheduler"]
    vm_audit = payload["sanctioned_vm_audit"]
    lines = [
        "# GCP Execution Launch Surface Audit",
        "",
        f"As of: {payload['as_of']}",
        "",
        f"Status: {payload['status']}",
        "",
        "## Summary",
        "",
        "This packet is the repeatable pre-arm launch-surface gate for the sanctioned VM paper session.",
        "",
        f"Broker flat: `{broker_state['broker_flat']}`",
        f"No-new-order watch clean: `{watch['watch_clean']}`",
        f"Local blocking scheduled tasks: `{len(scheduler['blocking_ready_tasks'])}`",
        f"Local project process count: `{payload['local_process_audit']['observed_process_count']}`",
        f"VM runner process clear: `{vm_audit['process_check']}`",
        f"VM runner commit matches expected: `{vm_audit['runner_commit_matches_expected']}`",
        "",
        "## Broker State",
        "",
        f"- Read-only check: `{broker_state['read_only_check_after_fencing']}`",
        f"- Watch duration seconds: `{watch['duration_seconds']}`",
        f"- Watch samples: `{watch['samples']}`",
        f"- Watch position count all samples: `{watch['position_count_all_samples']}`",
        f"- Watch open order count all samples: `{watch['open_order_count_all_samples']}`",
        f"- Newest order timestamp all samples: `{watch['newest_order_created_at_all_samples']}`",
        "",
        "## Local Task Scheduler",
        "",
    ]
    if scheduler["disabled_project_or_legacy_tasks"]:
        for task_name in scheduler["disabled_project_or_legacy_tasks"]:
            lines.append(f"- disabled: `{task_name}`")
    else:
        lines.append("- no disabled project tasks supplied")
    if scheduler["remaining_ready_matches"]:
        lines.extend(["", "Remaining non-project ready matches:", ""])
        for task in scheduler["remaining_ready_matches"]:
            lines.append(f"- `{task['task_name']}`: {task['classification']}")
    if scheduler["blocking_ready_tasks"]:
        lines.extend(["", "Blocking ready tasks:", ""])
        for task in scheduler["blocking_ready_tasks"]:
            lines.append(f"- `{task['task_name']}` state `{task['state']}` path `{task['task_path']}`")
    lines.extend(["", "## Issues", ""])
    if payload["issues"]:
        for issue in payload["issues"]:
            lines.append(f"- `{issue['severity']}` `{issue['code']}`: {issue['message']}")
    else:
        lines.append("- none")
    lines.extend(["", "## Next Safe Operator Gate", ""])
    for item in payload["next_safe_operator_gate"]:
        lines.append(f"- {item}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_handoff(path: Path, payload: dict[str, Any]) -> None:
    broker_state = payload["broker_state"]
    watch = broker_state["post_fencing_no_new_order_watch"]
    scheduler = payload["local_windows_task_scheduler"]
    vm_audit = payload["sanctioned_vm_audit"]
    lines = [
        "# GCP Execution Launch Surface Audit Handoff",
        "",
        f"As of: {payload['as_of']}",
        "",
        f"Status: `{payload['status']}`",
        f"Broker flat: `{broker_state['broker_flat']}`",
        f"No-new-order watch clean: `{watch['watch_clean']}`",
        f"Local blocking scheduled tasks: `{len(scheduler['blocking_ready_tasks'])}`",
        f"Local project process count: `{payload['local_process_audit']['observed_process_count']}`",
        f"VM runner process clear: `{vm_audit['process_check']}`",
        f"VM runner commit matches expected: `{vm_audit['runner_commit_matches_expected']}`",
        "",
        "## Operator Rule",
        "",
        "- This is a non-broker-facing gate; it must not start trading or arm the window.",
        "- If status is `blocked_launch_surface_audit`, do not arm the exclusive window.",
        "- If any broker order appears without an explicit operator launch, stop and investigate.",
        "- If status is `local_broker_capable_surfaces_fenced_broker_flat`, continue to pre-arm preflight and launch authorization.",
    ]
    if payload["issues"]:
        lines.extend(["", "## Blocking Issues", ""])
        for issue in payload["issues"]:
            lines.append(f"- `{issue['code']}`: {issue['message']}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _load_task_rows(path_text: str) -> list[dict[str, Any]]:
    if not path_text:
        return []
    payload = read_json(Path(path_text))
    if payload is None:
        return []
    if isinstance(payload, dict):
        rows = payload.get("tasks") or payload.get("value") or []
    else:
        rows = payload
    if not isinstance(rows, list):
        return []
    return [row for row in rows if isinstance(row, dict)]


def main() -> None:
    args = build_parser().parse_args()
    report_dir = Path(args.report_dir).resolve()
    vm_source_stamp = read_json(Path(args.vm_source_stamp_json)) if args.vm_source_stamp_json else None
    if vm_source_stamp is not None and not isinstance(vm_source_stamp, dict):
        vm_source_stamp = {}
    payload = build_payload(
        report_dir=report_dir,
        project_id=args.project_id,
        vm_name=args.vm_name,
        zone=args.zone,
        expected_runner_commit=args.expected_runner_commit,
        broker_position_count=args.broker_position_count,
        broker_open_order_count=args.broker_open_order_count,
        watch_duration_seconds=args.watch_duration_seconds,
        watch_start_utc=args.watch_start_utc,
        watch_end_utc=args.watch_end_utc,
        watch_samples=args.watch_samples,
        watch_sample_interval_seconds=args.watch_sample_interval_seconds,
        watch_position_count_all_samples=args.watch_position_count_all_samples,
        watch_open_order_count_all_samples=args.watch_open_order_count_all_samples,
        watch_newest_order_created_at=args.watch_newest_order_created_at,
        scheduled_task_rows=_load_task_rows(args.scheduled_task_json),
        local_process_count=args.local_process_count,
        local_process_note=args.local_process_note,
        vm_process_clear=args.vm_process_clear,
        vm_process_note=args.vm_process_note,
        vm_runner_commit=args.vm_runner_commit,
        vm_runner_branch=args.vm_runner_branch,
        vm_source_stamp=vm_source_stamp,
        unattributed_order_source_status=args.unattributed_order_source_status,
        incident_date=args.incident_date,
    )
    write_json(report_dir / "gcp_execution_launch_surface_audit.json", payload)
    write_markdown(report_dir / "gcp_execution_launch_surface_audit.md", payload)
    write_handoff(report_dir / "gcp_execution_launch_surface_audit_handoff.md", payload)
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
