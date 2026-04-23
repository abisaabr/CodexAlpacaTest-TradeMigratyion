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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build the exclusive execution-window packet for the first sanctioned GCP trusted validation session."
    )
    parser.add_argument("--project-id", default=DEFAULT_PROJECT_ID)
    parser.add_argument("--vm-name", default=DEFAULT_VM_NAME)
    parser.add_argument("--report-dir", default=str(DEFAULT_REPORT_DIR))
    return parser


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    lines: list[str] = []
    lines.append("# GCP Execution Exclusive Window Status")
    lines.append("")
    lines.append("## Snapshot")
    lines.append("")
    lines.append(f"- Generated at: `{payload['generated_at']}`")
    lines.append(f"- Project ID: `{payload['project_id']}`")
    lines.append(f"- VM name: `{payload['vm_name']}`")
    lines.append(f"- Window state: `{payload['exclusive_window_state']}`")
    lines.append(f"- Parallel runtime exception: `{payload['parallel_runtime_exception_state']}`")
    lines.append(f"- Attestation path: `{payload['attestation_json_path']}`")
    lines.append("")
    if payload.get("attestation_summary"):
        summary = payload["attestation_summary"]
        lines.append("## Current Attestation")
        lines.append("")
        lines.append(f"- Confirmed by: `{summary.get('confirmed_by')}`")
        lines.append(f"- Confirmed at: `{summary.get('confirmed_at')}`")
        lines.append(f"- Window starts at: `{summary.get('window_starts_at')}`")
        lines.append(f"- Window expires at: `{summary.get('window_expires_at')}`")
        lines.append(f"- Scope: `{summary.get('scope')}`")
        lines.append("")
    lines.append("## Required Assertions")
    lines.append("")
    for row in list(payload.get("required_assertions") or []):
        lines.append(f"- `{row}`")
    lines.append("")
    lines.append("## Guardrails")
    lines.append("")
    for row in list(payload.get("guardrails") or []):
        lines.append(f"- {row}")
    lines.append("")
    lines.append("## Attestation Template")
    lines.append("")
    lines.append("```json")
    lines.append(json.dumps(payload["attestation_template"], indent=2))
    lines.append("```")
    lines.append("")
    lines.append("## Next Actions")
    lines.append("")
    for row in list(payload.get("next_actions") or []):
        lines.append(f"- {row}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_handoff(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "# GCP Execution Exclusive Window Handoff",
        "",
        f"- Window state: `{payload['exclusive_window_state']}`",
        f"- VM name: `{payload['vm_name']}`",
        f"- Attestation path: `{payload['attestation_json_path']}`",
        "",
        "## Operator Rule",
        "",
        "- Do not start the first trusted validation paper session unless this packet says `confirmed_active_window`.",
        "- Keep the window bounded to a single sanctioned writer on `vm-execution-paper-01`.",
        "- Run governed post-session assimilation immediately after the session ends.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def normalize_attestation(attestation: dict[str, Any], vm_name: str) -> tuple[str, dict[str, Any], list[str]]:
    required_assertions = [
        "no_other_machine_active",
        "parallel_exception_path_not_running_broker_session",
        "session_starts_only_on_sanctioned_vm",
        "post_session_assimilation_reserved",
    ]
    errors: list[str] = []
    summary: dict[str, Any] = {}
    if not attestation:
        return "awaiting_operator_attestation", summary, errors

    confirmed_by = str(attestation.get("confirmed_by") or "").strip()
    confirmed_at = str(attestation.get("confirmed_at") or "").strip()
    window_starts_at = str(attestation.get("window_starts_at") or "").strip()
    window_expires_at = str(attestation.get("window_expires_at") or "").strip()
    scope = str(attestation.get("scope") or "").strip()
    target_vm_name = str(attestation.get("target_vm_name") or "").strip()
    assertions = attestation.get("assertions") or {}
    summary = {
        "confirmed_by": confirmed_by,
        "confirmed_at": confirmed_at,
        "window_starts_at": window_starts_at,
        "window_expires_at": window_expires_at,
        "scope": scope,
        "target_vm_name": target_vm_name,
    }

    if not confirmed_by:
        errors.append("`confirmed_by` is required.")
    if not confirmed_at:
        errors.append("`confirmed_at` is required.")
    if not window_starts_at:
        errors.append("`window_starts_at` is required.")
    if not window_expires_at:
        errors.append("`window_expires_at` is required.")
    if scope != "paper_account_single_writer":
        errors.append("`scope` must be `paper_account_single_writer`.")
    if target_vm_name != vm_name:
        errors.append(f"`target_vm_name` must be `{vm_name}`.")

    starts_at_dt = None
    expires_at_dt = None
    if confirmed_at:
        try:
            datetime.fromisoformat(confirmed_at)
        except ValueError:
            errors.append("`confirmed_at` must be an ISO 8601 timestamp.")
    if window_starts_at:
        try:
            starts_at_dt = datetime.fromisoformat(window_starts_at)
        except ValueError:
            errors.append("`window_starts_at` must be an ISO 8601 timestamp.")
    if window_expires_at:
        try:
            expires_at_dt = datetime.fromisoformat(window_expires_at)
        except ValueError:
            errors.append("`window_expires_at` must be an ISO 8601 timestamp.")
    if starts_at_dt is not None and expires_at_dt is not None and expires_at_dt <= starts_at_dt:
        errors.append("`window_expires_at` must be later than `window_starts_at`.")

    for key in required_assertions:
        if assertions.get(key) is not True:
            errors.append(f"`assertions.{key}` must be `true`.")

    if errors:
        return "invalid_attestation", summary, errors

    now = datetime.now().astimezone()
    assert starts_at_dt is not None
    assert expires_at_dt is not None
    if starts_at_dt.tzinfo is None:
        starts_at_dt = starts_at_dt.replace(tzinfo=now.tzinfo)
    if expires_at_dt.tzinfo is None:
        expires_at_dt = expires_at_dt.replace(tzinfo=now.tzinfo)
    if now < starts_at_dt:
        return "confirmed_future_window", summary, errors
    if now >= expires_at_dt:
        return "expired_window", summary, errors
    return "confirmed_active_window", summary, errors


def main() -> None:
    args = build_parser().parse_args()
    report_dir = Path(args.report_dir).resolve()
    report_dir.mkdir(parents=True, exist_ok=True)

    exception_status = read_json(report_dir / "gcp_parallel_runtime_exception_status.json")
    attestation_json_path = report_dir / "gcp_execution_exclusive_window_attestation.json"
    attestation = read_json(attestation_json_path)

    window_state, attestation_summary, validation_errors = normalize_attestation(attestation, args.vm_name)
    exception_state = str(exception_status.get("exception_state") or "unknown")

    next_actions = [
        f"Populate `{attestation_json_path}` with a bounded exclusive-window attestation before starting the first trusted validation session.",
        "Keep the temporary parallel runtime exception frozen and do not run concurrent broker-facing execution across the sanctioned and exception paths.",
        "Run governed post-session assimilation immediately after the trusted validation session ends.",
    ]
    if window_state == "confirmed_future_window":
        next_actions = [
            "Wait until the attested window becomes active before starting the trusted validation session.",
            "Do not widen the exclusive window or move it to another VM without refreshing the attestation packet.",
            "Run governed post-session assimilation immediately after the trusted validation session ends.",
        ]
    elif window_state == "confirmed_active_window":
        next_actions = [
            "The exclusive execution window is active for `vm-execution-paper-01`.",
            "Use the launch pack to start the first trusted validation session manually; do not auto-start it from this packet.",
            "Run governed post-session assimilation immediately after the trusted validation session ends.",
        ]
    elif window_state == "expired_window":
        next_actions = [
            "Refresh the attestation with a new bounded window before starting the trusted validation session.",
            "Do not reuse an expired attestation.",
            "Run governed post-session assimilation immediately after the trusted validation session ends.",
        ]
    elif window_state == "invalid_attestation":
        next_actions = [*validation_errors, "Repair the attestation JSON before treating the exclusive execution window as active."]

    current_time = datetime.now().astimezone().replace(microsecond=0)
    payload = {
        "generated_at": datetime.now().astimezone().isoformat(),
        "project_id": args.project_id,
        "vm_name": args.vm_name,
        "exclusive_window_state": window_state,
        "parallel_runtime_exception_state": exception_state,
        "attestation_json_path": str(attestation_json_path),
        "attestation_present": bool(attestation),
        "attestation_validation_errors": validation_errors,
        "attestation_summary": attestation_summary,
        "required_assertions": [
            "no_other_machine_active",
            "parallel_exception_path_not_running_broker_session",
            "session_starts_only_on_sanctioned_vm",
            "post_session_assimilation_reserved",
        ],
        "guardrails": [
            "Bound the window to one sanctioned writer on `vm-execution-paper-01`.",
            "Do not start a concurrent broker-facing session on the temporary exception path.",
            "Do not treat the attestation as open-ended; it must have start and expiry timestamps.",
            "Do not promote the VM to canonical execution from the first trusted validation session alone.",
        ],
        "attestation_template": {
            "window_id": f"trusted-validation-session-{args.vm_name}",
            "confirmed_by": "user@example.com",
            "confirmed_at": current_time.isoformat(),
            "window_starts_at": current_time.isoformat(),
            "window_expires_at": current_time.isoformat(),
            "target_vm_name": args.vm_name,
            "scope": "paper_account_single_writer",
            "assertions": {
                "no_other_machine_active": True,
                "parallel_exception_path_not_running_broker_session": True,
                "session_starts_only_on_sanctioned_vm": True,
                "post_session_assimilation_reserved": True,
            },
            "notes": "Bounded exclusive window for the first sanctioned GCP trusted validation session.",
        },
        "next_actions": next_actions,
    }

    write_json(report_dir / "gcp_execution_exclusive_window_status.json", payload)
    write_markdown(report_dir / "gcp_execution_exclusive_window_status.md", payload)
    write_handoff(report_dir / "gcp_execution_exclusive_window_handoff.md", payload)
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
