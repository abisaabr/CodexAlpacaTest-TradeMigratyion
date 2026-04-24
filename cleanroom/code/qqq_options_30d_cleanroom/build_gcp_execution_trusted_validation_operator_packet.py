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
DEFAULT_GCS_PREFIX = "gs://codexalpaca-control-us/gcp_foundation"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build the top-level operator packet for the first sanctioned GCP trusted validation session."
    )
    parser.add_argument("--project-id", default=DEFAULT_PROJECT_ID)
    parser.add_argument("--vm-name", default=DEFAULT_VM_NAME)
    parser.add_argument("--zone", default=DEFAULT_ZONE)
    parser.add_argument("--report-dir", default=str(DEFAULT_REPORT_DIR))
    parser.add_argument("--gcs-prefix", default=DEFAULT_GCS_PREFIX)
    return parser


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def build_payload(
    *,
    project_id: str,
    vm_name: str,
    zone: str,
    gcs_prefix: str,
    exclusive_window: dict[str, Any],
    trusted_validation: dict[str, Any],
    launch_pack: dict[str, Any],
    closeout_status: dict[str, Any],
    runner_provenance: dict[str, Any] | None = None,
    runtime_readiness: dict[str, Any] | None = None,
    session_completion_gate: dict[str, Any] | None = None,
) -> dict[str, Any]:
    runner_provenance = runner_provenance or {}
    runtime_readiness = runtime_readiness or {}
    session_completion_gate = session_completion_gate or {}
    exclusive_window_status = str(exclusive_window.get("exclusive_window_status") or "missing")
    trusted_validation_readiness = str(
        trusted_validation.get("trusted_validation_readiness") or "missing"
    )
    launch_pack_state = str(launch_pack.get("launch_pack_state") or "missing")
    closeout_state = str(closeout_status.get("closeout_status") or "missing")
    runner_provenance_status = str(runner_provenance.get("status") or "missing")
    runner_provenance_blocks_launch = runner_provenance_status.startswith("blocked_")
    runtime_readiness_status = str(runtime_readiness.get("status") or "missing")
    runtime_readiness_blocks_launch = runtime_readiness_status.startswith("blocked_")
    runtime_ownership_enabled = runtime_readiness.get("ownership_enabled")
    runtime_ownership_backend = str(runtime_readiness.get("ownership_backend") or "missing")
    runtime_ownership_lease_class = str(runtime_readiness.get("ownership_lease_class") or "missing")
    runtime_shared_execution_lease_enforced = bool(
        runtime_readiness.get("shared_execution_lease_enforced")
    )
    runtime_trader_process_absent = runtime_readiness.get("trader_process_absent")
    session_completion_status = str(
        session_completion_gate.get("completion_status") or "missing"
    )

    operator_packet_state = "blocked"
    if runner_provenance_blocks_launch or runtime_readiness_blocks_launch:
        operator_packet_state = "blocked"
    elif (
        trusted_validation_readiness == "awaiting_exclusive_execution_window"
        and launch_pack_state == "awaiting_window_arm"
        and exclusive_window_status == "awaiting_operator_confirmation"
        and closeout_state in {"window_already_closed", "ready_to_close_window"}
    ):
        operator_packet_state = "ready_to_arm_window"
    elif (
        trusted_validation_readiness == "ready_for_manual_launch"
        and launch_pack_state == "ready_to_launch"
        and exclusive_window_status == "ready_for_launch"
    ):
        operator_packet_state = "ready_to_launch_session"
    elif closeout_state == "ready_to_close_window":
        operator_packet_state = "ready_to_close_window"

    arm_window_command_template = (
        'powershell -NoProfile -ExecutionPolicy Bypass -File '
        '"<control-plane-root>\\cleanroom\\code\\qqq_options_30d_cleanroom\\arm_gcp_execution_exclusive_window.ps1" '
        '-ControlPlaneRoot "<control-plane-root>" '
        f'-VmName "{vm_name}" '
        '-ConfirmedBy "<confirmed-by>" '
        '-WindowStartsAt "<window-starts-at>" '
        '-WindowExpiresAt "<window-expires-at>" '
        '-ParallelPathState "paused" '
        '-MirrorToGcs'
    )
    operator_ssh_command = str(
        launch_pack.get("operator_ssh_command")
        or f"gcloud compute ssh {vm_name} --project {project_id} --zone {zone} --tunnel-through-iap"
    )
    vm_session_command = str(launch_pack.get("vm_session_command") or "")
    post_session_assimilation_command = str(launch_pack.get("post_session_assimilation_command") or "")
    closeout_command_template = (
        'powershell -NoProfile -ExecutionPolicy Bypass -File '
        '"<control-plane-root>\\cleanroom\\code\\qqq_options_30d_cleanroom\\close_gcp_execution_exclusive_window.ps1" '
        '-ControlPlaneRoot "<control-plane-root>" '
        f'-VmName "{vm_name}" '
        '-MirrorToGcs'
    )

    lifecycle_steps = [
        "Run the non-broker pre-arm preflight and require `ready_to_arm_window` before arming the exclusive window.",
        "Pick a bounded exclusive window and confirm the temporary parallel runtime path is paused for that window.",
        "Arm the exclusive window from the control-plane root and confirm the refreshed packets move to `ready_for_launch` / `ready_to_launch`.",
        "Build the non-broker launch authorization packet and require `ready_to_launch_session` before running the VM session command.",
        "SSH into the sanctioned VM through IAP.",
        "Run the trusted validation session command on the VM without changing strategy selection or risk policy.",
        "Run governed post-session assimilation immediately after the session ends.",
        "Close the exclusive window and mirror the refreshed packet set to GCS.",
        "Refresh the session-completion evidence gate before treating the session as complete for review.",
        "Review the morning brief, execution calibration, tournament unlock, and execution evidence packets before any promotion decision.",
    ]

    gating_summary = [
        f"Exclusive window status: `{exclusive_window_status}`",
        f"Trusted validation readiness: `{trusted_validation_readiness}`",
        f"Launch pack state: `{launch_pack_state}`",
        f"Closeout status: `{closeout_state}`",
        f"Runner provenance status: `{runner_provenance_status}`",
        f"Runtime readiness status: `{runtime_readiness_status}`",
        f"Runtime trader process absent: `{runtime_trader_process_absent}`",
        f"Runtime ownership enabled: `{runtime_ownership_enabled}`",
        f"Runtime ownership backend: `{runtime_ownership_backend}`",
        f"Runtime ownership lease class: `{runtime_ownership_lease_class}`",
        f"Runtime shared execution lease enforced: `{runtime_shared_execution_lease_enforced}`",
        f"Session completion gate: `{session_completion_status}`",
    ]
    review_targets = list(launch_pack.get("review_targets") or [])
    if runner_provenance_status != "missing":
        provenance_handoff = "docs/gcp_foundation/gcp_vm_runner_provenance_handoff.md"
        if provenance_handoff not in review_targets:
            review_targets.append(provenance_handoff)
    if str(runner_provenance.get("source_fingerprint_status") or "not_checked") != "not_checked":
        source_fingerprint_handoff = "docs/gcp_foundation/gcp_vm_runner_source_fingerprint_handoff.md"
        if source_fingerprint_handoff not in review_targets:
            review_targets.append(source_fingerprint_handoff)
    if runtime_readiness_status != "missing":
        runtime_readiness_handoff = "docs/gcp_foundation/gcp_vm_runtime_readiness_handoff.md"
        if runtime_readiness_handoff not in review_targets:
            review_targets.append(runtime_readiness_handoff)
    prearm_handoff = "docs/gcp_foundation/gcp_execution_prearm_preflight_handoff.md"
    if prearm_handoff not in review_targets:
        review_targets.append(prearm_handoff)
    launch_authorization_handoff = "docs/gcp_foundation/gcp_execution_launch_authorization_handoff.md"
    if launch_authorization_handoff not in review_targets:
        review_targets.append(launch_authorization_handoff)
    session_completion_handoff = "docs/gcp_foundation/gcp_execution_session_completion_gate_handoff.md"
    if session_completion_handoff not in review_targets:
        review_targets.append(session_completion_handoff)

    runner_provenance_issue_codes = [
        str(issue.get("code"))
        for issue in list(runner_provenance.get("issues") or [])
        if issue.get("code")
    ]

    return {
        "generated_at": datetime.now().astimezone().isoformat(),
        "project_id": project_id,
        "vm_name": vm_name,
        "zone": zone,
        "gcs_prefix": gcs_prefix,
        "operator_packet_state": operator_packet_state,
        "exclusive_window_status": exclusive_window_status,
        "trusted_validation_readiness": trusted_validation_readiness,
        "launch_pack_state": launch_pack_state,
        "closeout_status": closeout_state,
        "runner_provenance_status": runner_provenance_status,
        "runner_provenance_blocks_launch": runner_provenance_blocks_launch,
        "runner_provenance_issue_codes": runner_provenance_issue_codes,
        "runtime_readiness_status": runtime_readiness_status,
        "runtime_readiness_blocks_launch": runtime_readiness_blocks_launch,
        "runtime_trader_process_absent": runtime_trader_process_absent,
        "runtime_ownership_enabled": runtime_ownership_enabled,
        "runtime_ownership_backend": runtime_ownership_backend,
        "runtime_ownership_lease_class": runtime_ownership_lease_class,
        "runtime_shared_execution_lease_enforced": runtime_shared_execution_lease_enforced,
        "session_completion_status": session_completion_status,
        "runner_branch": trusted_validation.get("runner_branch"),
        "runner_commit": trusted_validation.get("runner_commit"),
        "arm_window_command_template": arm_window_command_template,
        "operator_ssh_command": operator_ssh_command,
        "vm_session_command": vm_session_command,
        "post_session_assimilation_command": post_session_assimilation_command,
        "closeout_command_template": closeout_command_template,
        "required_evidence": list(trusted_validation.get("required_evidence") or []),
        "review_targets": review_targets,
        "lifecycle_steps": lifecycle_steps,
        "gating_summary": gating_summary,
        "guardrails": [
            "Do not arm the exclusive window until you are ready to actually reserve the paper-account slot.",
            "Do not start a broker-facing session unless the refreshed exclusive-window packet says `ready_for_launch` and the launch pack says `ready_to_launch`.",
            "Do not arm or launch a trusted session while runner provenance status starts with `blocked_`.",
            "Do not arm or launch a trusted session while VM runtime readiness starts with `blocked_`.",
            "Do not arm the exclusive window if the non-broker pre-arm preflight is missing or blocked.",
            "Do not run the VM session command if launch authorization is missing or blocked.",
            "Do not enable shared-lease enforcement by default during the first trusted validation session.",
            "Do not use unstamped VM runner provenance as strategy-promotion evidence.",
            "Do not skip post-session assimilation or closeout after the session ends.",
            "Do not count a raw PnL winner as a qualified winner unless the session-completion evidence gate is complete.",
        ],
    }


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "# GCP Execution Trusted Validation Operator Packet",
        "",
        "## Snapshot",
        "",
        f"- Generated at: `{payload['generated_at']}`",
        f"- Operator packet state: `{payload['operator_packet_state']}`",
        f"- Project ID: `{payload['project_id']}`",
        f"- VM name: `{payload['vm_name']}`",
        f"- Runner branch: `{payload['runner_branch']}`",
        f"- Runner commit: `{payload['runner_commit']}`",
        "",
        "## Current Gates",
        "",
    ]
    for row in list(payload.get("gating_summary") or []):
        lines.append(f"- {row}")

    lines.extend(
        [
            "",
            "## Commands",
            "",
            "### Arm Window",
            "",
            "```powershell",
            str(payload["arm_window_command_template"]),
            "```",
            "",
            "### Operator SSH",
            "",
            "```bash",
            str(payload["operator_ssh_command"]),
            "```",
            "",
            "### VM Session",
            "",
            "```bash",
            str(payload["vm_session_command"]),
            "```",
            "",
            "### Post-Session Assimilation",
            "",
            "```powershell",
            str(payload["post_session_assimilation_command"]),
            "```",
            "",
            "### Close Window",
            "",
            "```powershell",
            str(payload["closeout_command_template"]),
            "```",
            "",
            "## Lifecycle Steps",
            "",
        ]
    )
    for row in list(payload.get("lifecycle_steps") or []):
        lines.append(f"- {row}")

    lines.extend(["", "## Required Evidence", ""])
    for row in list(payload.get("required_evidence") or []):
        lines.append(f"- `{row}`")

    lines.extend(["", "## Review Targets", ""])
    for row in list(payload.get("review_targets") or []):
        lines.append(f"- `{row}`")

    lines.extend(["", "## Guardrails", ""])
    for row in list(payload.get("guardrails") or []):
        lines.append(f"- {row}")

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_handoff(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "# GCP Execution Trusted Validation Operator Handoff",
        "",
        f"- Operator packet state: `{payload['operator_packet_state']}`",
        f"- Exclusive window status: `{payload['exclusive_window_status']}`",
        f"- Launch pack state: `{payload['launch_pack_state']}`",
        f"- Closeout status: `{payload['closeout_status']}`",
        f"- Runner provenance status: `{payload.get('runner_provenance_status')}`",
        f"- Runner provenance blocks launch: `{payload.get('runner_provenance_blocks_launch')}`",
        f"- Runtime readiness status: `{payload.get('runtime_readiness_status')}`",
        f"- Runtime readiness blocks launch: `{payload.get('runtime_readiness_blocks_launch')}`",
        f"- Runtime trader process absent: `{payload.get('runtime_trader_process_absent')}`",
        f"- Runtime ownership enabled: `{payload.get('runtime_ownership_enabled')}`",
        f"- Runtime ownership backend: `{payload.get('runtime_ownership_backend')}`",
        f"- Runtime ownership lease class: `{payload.get('runtime_ownership_lease_class')}`",
        f"- Runtime shared execution lease enforced: `{payload.get('runtime_shared_execution_lease_enforced')}`",
        f"- Session completion gate: `{payload.get('session_completion_status')}`",
        "",
        "## Operator Rule",
        "",
        "- Use this packet as the single top-level checklist for the first sanctioned VM trusted validation session.",
        "- If the packet state is `blocked`, resolve the blocking gate and refresh packets before arming the window.",
        "- If the packet says `ready_to_arm_window`, arm the window first and re-read the refreshed packets before launching anything.",
        "- Do not start the VM session unless the refreshed launch packet says `ready_to_launch`.",
        "- Always follow with post-session assimilation and exclusive-window closeout.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = build_parser().parse_args()
    report_dir = Path(args.report_dir).resolve()
    report_dir.mkdir(parents=True, exist_ok=True)

    payload = build_payload(
        project_id=args.project_id,
        vm_name=args.vm_name,
        zone=args.zone,
        gcs_prefix=args.gcs_prefix,
        exclusive_window=read_json(report_dir / "gcp_execution_exclusive_window_status.json"),
        trusted_validation=read_json(report_dir / "gcp_execution_trusted_validation_session_status.json"),
        launch_pack=read_json(report_dir / "gcp_execution_trusted_validation_launch_pack.json"),
        closeout_status=read_json(report_dir / "gcp_execution_closeout_status.json"),
        runner_provenance=read_json(report_dir / "gcp_vm_runner_provenance_status.json"),
        runtime_readiness=read_json(report_dir / "gcp_vm_runtime_readiness_status.json"),
        session_completion_gate=read_json(report_dir / "gcp_execution_session_completion_gate.json"),
    )
    write_json(report_dir / "gcp_execution_trusted_validation_operator_packet.json", payload)
    write_markdown(report_dir / "gcp_execution_trusted_validation_operator_packet.md", payload)
    write_handoff(report_dir / "gcp_execution_trusted_validation_operator_handoff.md", payload)
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
