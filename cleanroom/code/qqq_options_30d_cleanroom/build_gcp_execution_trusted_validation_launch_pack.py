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
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build the manual launch pack for the first sanctioned GCP trusted validation session."
    )
    parser.add_argument("--project-id", default=DEFAULT_PROJECT_ID)
    parser.add_argument("--vm-name", default=DEFAULT_VM_NAME)
    parser.add_argument("--zone", default=DEFAULT_ZONE)
    parser.add_argument("--report-dir", default=str(DEFAULT_REPORT_DIR))
    return parser


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def build_payload(
    *,
    project_id: str,
    vm_name: str,
    zone: str,
    trusted_status: dict[str, Any],
    exclusive_window: dict[str, Any],
) -> dict[str, Any]:
    readiness = str(trusted_status.get("trusted_validation_readiness") or "blocked")
    exclusive_window_state = str(exclusive_window.get("exclusive_window_state") or "missing")
    exclusive_window_status = str(exclusive_window.get("exclusive_window_status") or "missing")

    launch_pack_state = "blocked"
    if readiness == "ready_for_manual_launch" and exclusive_window_status == "ready_for_launch":
        launch_pack_state = "ready_to_launch"
    elif readiness == "awaiting_exclusive_execution_window":
        launch_pack_state = "awaiting_window_arm"

    operator_ssh_command = (
        f"gcloud compute ssh {vm_name} --project {project_id} --zone {zone} --tunnel-through-iap"
    )
    vm_session_command = str(
        trusted_status.get("trusted_validation_session_command")
        or "cd /opt/codexalpaca/codexalpaca_repo && ./.venv/bin/python scripts/run_multi_ticker_portfolio_paper_trader.py --portfolio-config config/multi_ticker_paper_portfolio.yaml --submit-paper-orders"
    )
    post_session_assimilation_command = (
        'powershell -NoProfile -ExecutionPolicy Bypass -File '
        '"<control-plane-root>\\cleanroom\\code\\qqq_options_30d_cleanroom\\launch_post_session_assimilation.ps1" '
        '-ControlPlaneRoot "<control-plane-root>" -RunnerRepoRoot "<runner-repo-root>"'
    )

    operator_steps = [
        "Confirm the exclusive-window packet says `ready_for_launch` and the trusted-validation readiness packet says `ready_for_manual_launch`.",
        "SSH to `vm-execution-paper-01` through IAP.",
        "Run the trusted validation session command on the VM without changing strategy selection or risk policy.",
        "When the session ends, run governed post-session assimilation from the control-plane machine.",
        "Review the refreshed morning brief, execution calibration handoff, tournament unlock handoff, and execution evidence contract before any promotion decision.",
    ]
    if launch_pack_state != "ready_to_launch":
        operator_steps.insert(
            0,
            "Do not start the session yet; this pack is in preparation mode until the exclusive execution window is actively confirmed.",
        )

    return {
        "generated_at": datetime.now().astimezone().isoformat(),
        "project_id": project_id,
        "vm_name": vm_name,
        "runner_branch": trusted_status.get("runner_branch"),
        "runner_commit": trusted_status.get("runner_commit"),
        "runner_repo_root_hint": "<runner-repo-root>",
        "control_plane_root_hint": "<control-plane-root>",
        "trusted_validation_readiness": readiness,
        "exclusive_window_state": exclusive_window_state,
        "exclusive_window_status": exclusive_window_status,
        "latest_lease_runtime_validation_status": trusted_status.get("latest_lease_runtime_validation_status"),
        "latest_lease_validation_run_id": trusted_status.get("latest_lease_validation_run_id"),
        "launch_pack_state": launch_pack_state,
        "operator_ssh_command": operator_ssh_command,
        "vm_session_command": vm_session_command,
        "post_session_assimilation_command": post_session_assimilation_command,
        "operator_steps": operator_steps,
        "required_evidence": list(trusted_status.get("required_evidence") or []),
        "review_targets": [
            "docs/morning_brief/morning_operator_brief.md",
            "docs/execution_calibration/execution_calibration_handoff.md",
            "docs/tournament_unlocks/tournament_unlock_handoff.md",
            "docs/execution_evidence/execution_evidence_contract_handoff.md",
        ],
        "guardrails": [
            "Do not auto-start trading from this packet.",
            "Keep the shared execution lease in dry-run posture for the first trusted validation session.",
            "Do not widen the temporary parallel-runtime exception.",
            "Do not promote the VM to canonical execution from this launch alone.",
        ],
    }


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    lines: list[str] = []
    lines.append("# GCP Execution Trusted Validation Launch Pack")
    lines.append("")
    lines.append("## Snapshot")
    lines.append("")
    lines.append(f"- Generated at: `{payload['generated_at']}`")
    lines.append(f"- Project ID: `{payload['project_id']}`")
    lines.append(f"- VM name: `{payload['vm_name']}`")
    lines.append(f"- Launch pack state: `{payload['launch_pack_state']}`")
    lines.append(f"- Runner branch: `{payload['runner_branch']}`")
    lines.append(f"- Runner commit: `{payload['runner_commit']}`")
    lines.append(f"- Exclusive window state: `{payload['exclusive_window_state']}`")
    lines.append(f"- Exclusive window status: `{payload['exclusive_window_status']}`")
    lines.append(f"- Lease runtime validation: `{payload.get('latest_lease_runtime_validation_status')}`")
    lines.append("")
    lines.append("## Commands")
    lines.append("")
    lines.append("### Operator SSH")
    lines.append("")
    lines.append("```bash")
    lines.append(payload["operator_ssh_command"])
    lines.append("```")
    lines.append("")
    lines.append("### VM Session Command")
    lines.append("")
    lines.append("```bash")
    lines.append(payload["vm_session_command"])
    lines.append("```")
    lines.append("")
    lines.append("### Post-Session Assimilation")
    lines.append("")
    lines.append("```powershell")
    lines.append(payload["post_session_assimilation_command"])
    lines.append("```")
    lines.append("")
    lines.append("## Operator Steps")
    lines.append("")
    for row in list(payload.get("operator_steps") or []):
        lines.append(f"- {row}")
    lines.append("")
    lines.append("## Required Evidence")
    lines.append("")
    for row in list(payload.get("required_evidence") or []):
        lines.append(f"- `{row}`")
    lines.append("")
    lines.append("## Review Targets")
    lines.append("")
    for row in list(payload.get("review_targets") or []):
        lines.append(f"- `{row}`")
    lines.append("")
    lines.append("## Guardrails")
    lines.append("")
    for row in list(payload.get("guardrails") or []):
        lines.append(f"- {row}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_handoff(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "# GCP Execution Trusted Validation Launch Handoff",
        "",
        f"- Launch pack state: `{payload['launch_pack_state']}`",
        f"- VM name: `{payload['vm_name']}`",
        f"- Runner commit: `{payload['runner_commit']}`",
        f"- Exclusive window state: `{payload['exclusive_window_state']}`",
        f"- Exclusive window status: `{payload['exclusive_window_status']}`",
        "",
        "## Operator Rule",
        "",
        "- This pack prepares the first sanctioned trusted validation session but does not auto-start it.",
        "- Do not use this pack unless the exclusive-window packet says `ready_for_launch` and this packet says `ready_to_launch`.",
        "- Run post-session assimilation immediately after the broker-facing session ends.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = build_parser().parse_args()
    report_dir = Path(args.report_dir).resolve()
    report_dir.mkdir(parents=True, exist_ok=True)

    trusted_status = read_json(report_dir / "gcp_execution_trusted_validation_session_status.json")
    exclusive_window = read_json(report_dir / "gcp_execution_exclusive_window_status.json")
    payload = build_payload(
        project_id=args.project_id,
        vm_name=args.vm_name,
        zone=args.zone,
        trusted_status=trusted_status,
        exclusive_window=exclusive_window,
    )

    write_json(report_dir / "gcp_execution_trusted_validation_launch_pack.json", payload)
    write_markdown(report_dir / "gcp_execution_trusted_validation_launch_pack.md", payload)
    write_handoff(report_dir / "gcp_execution_trusted_validation_launch_handoff.md", payload)
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
