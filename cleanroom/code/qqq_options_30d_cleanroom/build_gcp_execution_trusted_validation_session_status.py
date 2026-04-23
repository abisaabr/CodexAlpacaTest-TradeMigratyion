from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[2]
DEFAULT_REPORT_DIR = REPO_ROOT / "docs" / "gcp_foundation"
DEFAULT_PROJECT_ID = "codexalpaca"
DEFAULT_VM_NAME = "vm-execution-paper-01"
DEFAULT_RUNNER_REPO_ROOT = Path(r"C:\Users\rabisaab\Downloads\codexalpaca_repo")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build the trusted validation-session readiness packet for the GCP execution VM.")
    parser.add_argument("--project-id", default=DEFAULT_PROJECT_ID)
    parser.add_argument("--vm-name", default=DEFAULT_VM_NAME)
    parser.add_argument("--report-dir", default=str(DEFAULT_REPORT_DIR))
    parser.add_argument("--runner-repo-root", default=str(DEFAULT_RUNNER_REPO_ROOT))
    return parser


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_json_if_exists(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return read_json(path)


def git_output(repo_root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo_root), *args],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def normalize_exclusive_window_status(exclusive_window: dict[str, Any] | None) -> str:
    status = str((exclusive_window or {}).get("exclusive_window_status") or "").strip()
    if status:
        return status
    state = str((exclusive_window or {}).get("exclusive_window_state") or "").strip()
    state_to_status = {
        "awaiting_operator_attestation": "awaiting_operator_confirmation",
        "invalid_attestation": "blocked",
        "confirmed_future_window": "awaiting_window_start",
        "confirmed_active_window": "ready_for_launch",
        "expired_window": "blocked",
    }
    return state_to_status.get(state, "missing")


def build_payload(
    *,
    project_id: str,
    vm_name: str,
    access: dict[str, Any],
    validation_review: dict[str, Any],
    runtime_security: dict[str, Any],
    runner_branch: str,
    runner_commit: str,
    exclusive_window: dict[str, Any] | None,
    lease_runtime_validation: dict[str, Any] | None,
) -> dict[str, Any]:
    secret_results = list(runtime_security.get("secret_results") or [])
    required_secret_results = [row for row in secret_results if bool(row.get("required"))]
    required_secrets_seeded = all(bool(row.get("seeded")) for row in required_secret_results)
    exclusive_window_status = normalize_exclusive_window_status(exclusive_window)
    exclusive_window_gate_status = "operator_required"
    if exclusive_window_status == "ready_for_launch":
        exclusive_window_gate_status = "passed"
    elif exclusive_window_status == "blocked":
        exclusive_window_gate_status = "blocked"
    lease_validation_green = (
        lease_runtime_validation is not None
        and str(lease_runtime_validation.get("runtime_validation_status")) == "validated_not_enforced"
    )

    gate_checks = [
        {
            "name": "operator_access_ready",
            "status": "passed"
            if str(access.get("access_readiness")) == "ready_for_operator_validation"
            else "blocked",
        },
        {
            "name": "headless_validation_green",
            "status": "passed"
            if str(validation_review.get("review_state")) == "passed"
            else "blocked",
        },
        {
            "name": "shared_lease_dry_run_green",
            "status": "passed" if lease_validation_green else "blocked",
        },
        {
            "name": "runtime_secret_containers_seeded",
            "status": "passed" if required_secrets_seeded else "blocked",
        },
        {
            "name": "runner_branch_published",
            "status": "passed" if bool(runner_branch) and bool(runner_commit) else "blocked",
        },
        {
            "name": "exclusive_execution_window_confirmed",
            "status": exclusive_window_gate_status,
        },
    ]

    remaining_gates = [
        "The shared execution lease is now proven in dry-run mode on the sanctioned VM, but enforcement is still intentionally off until a separate promotion decision says otherwise.",
        "The session must be followed immediately by governed post-session assimilation before any promotion decision.",
    ]
    if not lease_validation_green:
        remaining_gates.insert(
            0,
            "The shared execution lease dry-run on vm-execution-paper-01 must be clean before any trusted validation session starts.",
        )
    if exclusive_window_gate_status == "passed":
        remaining_gates.insert(
            0,
            "The exclusive execution window is active; keep the trusted validation session bounded to `vm-execution-paper-01` and end it inside the attested window.",
        )
    else:
        remaining_gates.insert(
            0,
            "An operator still needs to confirm an active exclusive execution window so no other machine is using the shared paper account when the VM session starts.",
        )

    readiness = "awaiting_exclusive_execution_window"
    if any(gate["status"] == "blocked" for gate in gate_checks):
        readiness = "blocked"
    elif all(gate["status"] == "passed" for gate in gate_checks):
        readiness = "ready_for_manual_launch"

    return {
        "generated_at": datetime.now().astimezone().isoformat(),
        "project_id": project_id,
        "vm_name": vm_name,
        "runner_branch": runner_branch,
        "runner_commit": runner_commit,
        "trusted_validation_readiness": readiness,
        "exclusive_window_status": exclusive_window_status,
        "gate_checks": gate_checks,
        "latest_validation_run_id": validation_review.get("run_id"),
        "latest_validation_review_state": validation_review.get("review_state"),
        "latest_lease_runtime_validation_status": None
        if lease_runtime_validation is None
        else lease_runtime_validation.get("runtime_validation_status"),
        "latest_lease_validation_run_id": None
        if lease_runtime_validation is None
        else lease_runtime_validation.get("latest_run_id"),
        "trusted_validation_session_command": (
            "cd /opt/codexalpaca/codexalpaca_repo && "
            "./.venv/bin/python scripts/run_multi_ticker_portfolio_paper_trader.py "
            "--portfolio-config config/multi_ticker_paper_portfolio.yaml --submit-paper-orders"
        ),
        "required_evidence": [
            "broker-order audit",
            "broker account-activity audit",
            "ending broker-position snapshot",
            "shutdown reconciliation",
            "completed trade table with broker/local cashflow comparison",
        ],
        "remaining_gates": remaining_gates,
        "next_actions": [
            "Refresh the governed exclusive execution-window packet before the first broker-facing VM session.",
            "Keep the shared execution lease in dry-run posture; do not switch default enforcement on as part of the first trusted validation session.",
            "Use the trusted validation launch pack only inside an explicitly exclusive paper-account window.",
            "Run governed post-session assimilation immediately after the session finishes.",
            "Do not promote the VM to canonical execution until the trusted session evidence is reviewed cleanly.",
        ],
    }


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    lines: list[str] = []
    lines.append("# GCP Execution Trusted Validation Session Status")
    lines.append("")
    lines.append("## Snapshot")
    lines.append("")
    lines.append(f"- Generated at: `{payload['generated_at']}`")
    lines.append(f"- Project ID: `{payload['project_id']}`")
    lines.append(f"- VM name: `{payload['vm_name']}`")
    lines.append(f"- Readiness: `{payload['trusted_validation_readiness']}`")
    lines.append(f"- Runner branch: `{payload['runner_branch']}`")
    lines.append(f"- Runner commit: `{payload['runner_commit']}`")
    lines.append(f"- Exclusive window status: `{payload['exclusive_window_status']}`")
    lines.append(f"- Lease runtime validation: `{payload.get('latest_lease_runtime_validation_status')}`")
    lines.append("")
    lines.append("## Gates")
    lines.append("")
    for gate in list(payload.get("gate_checks") or []):
        lines.append(f"- `{gate['name']}`: `{gate['status']}`")
    lines.append("")
    lines.append("## Proposed VM Command")
    lines.append("")
    lines.append("```bash")
    lines.append(str(payload["trusted_validation_session_command"]))
    lines.append("```")
    lines.append("")
    lines.append("## Required Evidence")
    lines.append("")
    for row in list(payload.get("required_evidence") or []):
        lines.append(f"- `{row}`")
    lines.append("")
    lines.append("## Remaining Gates")
    lines.append("")
    for row in list(payload.get("remaining_gates") or []):
        lines.append(f"- {row}")
    lines.append("")
    lines.append("## Next Actions")
    lines.append("")
    for row in list(payload.get("next_actions") or []):
        lines.append(f"- {row}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = build_parser().parse_args()
    report_dir = Path(args.report_dir).resolve()
    runner_repo_root = Path(args.runner_repo_root).resolve()

    access = read_json(report_dir / "gcp_execution_access_readiness_status.json")
    validation_review = read_json(report_dir / "gcp_execution_vm_headless_validation_review_status.json")
    exclusive_window = read_json_if_exists(report_dir / "gcp_execution_exclusive_window_status.json")
    runtime_security = read_json(report_dir / "gcp_runtime_security_status.json")
    lease_runtime_validation = read_json_if_exists(
        report_dir / "gcp_shared_execution_lease_runtime_validation_status.json"
    )

    runner_branch = git_output(runner_repo_root, "rev-parse", "--abbrev-ref", "HEAD")
    runner_commit = git_output(runner_repo_root, "rev-parse", "HEAD")
    payload = build_payload(
        project_id=args.project_id,
        vm_name=args.vm_name,
        access=access,
        validation_review=validation_review,
        runtime_security=runtime_security,
        runner_branch=runner_branch,
        runner_commit=runner_commit,
        exclusive_window=exclusive_window,
        lease_runtime_validation=lease_runtime_validation,
    )
    write_json(report_dir / "gcp_execution_trusted_validation_session_status.json", payload)
    write_markdown(report_dir / "gcp_execution_trusted_validation_session_status.md", payload)
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
