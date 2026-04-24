from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[2]
DEFAULT_REPORT_DIR = REPO_ROOT / "docs" / "gcp_foundation"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build the non-broker pre-arm preflight packet for the sanctioned VM paper session."
    )
    parser.add_argument("--report-dir", default=str(DEFAULT_REPORT_DIR))
    return parser


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _issue(severity: str, code: str, message: str) -> dict[str, str]:
    return {"severity": severity, "code": code, "message": message}


def build_payload(
    *,
    operator_packet: dict[str, Any],
    runtime_readiness: dict[str, Any],
    runner_provenance: dict[str, Any],
    source_fingerprint: dict[str, Any],
    exclusive_window: dict[str, Any],
    launch_pack: dict[str, Any],
    report_dir: Path,
) -> dict[str, Any]:
    operator_state = str(operator_packet.get("operator_packet_state") or "missing")
    vm_name = str(operator_packet.get("vm_name") or "missing")
    runtime_status = str(runtime_readiness.get("status") or "missing")
    provenance_status = str(runner_provenance.get("status") or "missing")
    source_fingerprint_status = str(source_fingerprint.get("status") or "missing")
    exclusive_window_status = str(exclusive_window.get("exclusive_window_status") or "missing")
    launch_pack_state = str(launch_pack.get("launch_pack_state") or "missing")

    trader_process_absent = runtime_readiness.get("trader_process_absent")
    ownership_enabled = runtime_readiness.get("ownership_enabled")
    ownership_backend = str(runtime_readiness.get("ownership_backend") or "missing")
    ownership_lease_class = str(runtime_readiness.get("ownership_lease_class") or "missing")
    shared_execution_lease_enforced = bool(runtime_readiness.get("shared_execution_lease_enforced"))

    issues: list[dict[str, str]] = []
    if operator_state != "ready_to_arm_window":
        issues.append(
            _issue(
                "error",
                "operator_packet_not_ready_to_arm",
                "The top-level operator packet must be `ready_to_arm_window` before arming.",
            )
        )
    if exclusive_window_status != "awaiting_operator_confirmation":
        issues.append(
            _issue(
                "error",
                "exclusive_window_not_awaiting_operator_confirmation",
                "The exclusive-window packet must be idle and awaiting operator confirmation before pre-arm approval.",
            )
        )
    if launch_pack_state != "awaiting_window_arm":
        issues.append(
            _issue(
                "error",
                "launch_pack_not_awaiting_window_arm",
                "The launch pack must remain in preparation mode until the exclusive window is armed.",
            )
        )
    if runtime_status != "runtime_ready":
        issues.append(
            _issue(
                "error",
                "vm_runtime_not_ready",
                "VM runtime readiness must be clean before arming the exclusive window.",
            )
        )
    if provenance_status != "provenance_matched":
        issues.append(
            _issue(
                "error",
                "vm_runner_provenance_not_matched",
                "VM runner provenance must match the canonical runner checkout before arming.",
            )
        )
    if source_fingerprint_status != "source_fingerprint_matched":
        issues.append(
            _issue(
                "error",
                "vm_source_fingerprint_not_matched",
                "VM source fingerprint must match the canonical runner checkout before arming.",
            )
        )
    if trader_process_absent is not True:
        issues.append(
            _issue(
                "error",
                "trader_process_not_clear",
                "No trader process may already be active on the VM before arming.",
            )
        )
    if ownership_enabled is not True:
        issues.append(
            _issue(
                "error",
                "ownership_not_enabled",
                "Runtime ownership must be enabled before arming.",
            )
        )
    if ownership_backend != "file":
        issues.append(
            _issue(
                "error",
                "ownership_backend_not_file",
                "The first trusted VM session must stay on the local file lease.",
            )
        )
    if ownership_lease_class != "FileOwnershipLease":
        issues.append(
            _issue(
                "error",
                "ownership_lease_class_not_file",
                "The first trusted VM session must resolve to FileOwnershipLease.",
            )
        )
    if shared_execution_lease_enforced:
        issues.append(
            _issue(
                "error",
                "shared_execution_lease_enforced_too_early",
                "GCS shared-lease enforcement is not approved for the first trusted VM session.",
            )
        )

    status = "ready_to_arm_window" if not any(issue["severity"] == "error" for issue in issues) else "blocked"
    next_operator_action = "arm_bounded_exclusive_window" if status == "ready_to_arm_window" else "resolve_prearm_blockers"

    return {
        "generated_at": datetime.now().astimezone().isoformat(),
        "status": status,
        "next_operator_action": next_operator_action,
        "report_dir": str(report_dir),
        "broker_facing": False,
        "live_manifest_effect": "none",
        "risk_policy_effect": "none",
        "vm_name": vm_name,
        "operator_packet_state": operator_state,
        "runtime_readiness_status": runtime_status,
        "runner_provenance_status": provenance_status,
        "source_fingerprint_status": source_fingerprint_status,
        "exclusive_window_status": exclusive_window_status,
        "launch_pack_state": launch_pack_state,
        "trader_process_absent": trader_process_absent,
        "ownership_enabled": ownership_enabled,
        "ownership_backend": ownership_backend,
        "ownership_lease_class": ownership_lease_class,
        "shared_execution_lease_enforced": shared_execution_lease_enforced,
        "arm_window_command_template": operator_packet.get("arm_window_command_template"),
        "review_targets": [
            "docs/gcp_foundation/gcp_execution_prearm_preflight_handoff.md",
            "docs/gcp_foundation/gcp_execution_trusted_validation_operator_handoff.md",
            "docs/gcp_foundation/gcp_vm_runtime_readiness_handoff.md",
            "docs/gcp_foundation/gcp_vm_runner_provenance_handoff.md",
            "docs/gcp_foundation/gcp_vm_runner_source_fingerprint_handoff.md",
            "docs/gcp_foundation/gcp_execution_exclusive_window_handoff.md",
            "docs/gcp_foundation/gcp_execution_trusted_validation_launch_handoff.md",
        ],
        "issues": issues,
        "operator_read": [
            "This packet is non-broker-facing; it does not arm the window or start a session.",
            "Use it immediately before arming the bounded exclusive window.",
            "If status is `blocked`, do not arm; refresh or resolve the named gate first.",
            "If status is `ready_to_arm_window`, the next action is still a human/operator arm command, not an automatic launch.",
        ],
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "# GCP Execution Pre-Arm Preflight",
        "",
        "## Snapshot",
        "",
        f"- Generated at: `{payload['generated_at']}`",
        f"- Status: `{payload['status']}`",
        f"- Next operator action: `{payload['next_operator_action']}`",
        f"- VM name: `{payload['vm_name']}`",
        f"- Operator packet state: `{payload['operator_packet_state']}`",
        f"- Runtime readiness status: `{payload['runtime_readiness_status']}`",
        f"- Runner provenance status: `{payload['runner_provenance_status']}`",
        f"- Source fingerprint status: `{payload['source_fingerprint_status']}`",
        f"- Exclusive window status: `{payload['exclusive_window_status']}`",
        f"- Launch pack state: `{payload['launch_pack_state']}`",
        f"- Trader process absent: `{payload['trader_process_absent']}`",
        f"- Ownership enabled: `{payload['ownership_enabled']}`",
        f"- Ownership backend: `{payload['ownership_backend']}`",
        f"- Ownership lease class: `{payload['ownership_lease_class']}`",
        f"- Shared execution lease enforced: `{payload['shared_execution_lease_enforced']}`",
        "",
        "## Arm Command Template",
        "",
        "```powershell",
        str(payload.get("arm_window_command_template") or ""),
        "```",
        "",
        "## Issues",
        "",
    ]
    if payload["issues"]:
        for issue in payload["issues"]:
            lines.append(f"- `{issue['severity']}` `{issue['code']}`: {issue['message']}")
    else:
        lines.append("- none")
    lines.extend(["", "## Operator Read", ""])
    for item in payload["operator_read"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Review Targets", ""])
    for item in payload["review_targets"]:
        lines.append(f"- `{item}`")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_handoff(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "# GCP Execution Pre-Arm Preflight Handoff",
        "",
        f"- Status: `{payload['status']}`",
        f"- Next operator action: `{payload['next_operator_action']}`",
        f"- VM name: `{payload['vm_name']}`",
        f"- Operator packet state: `{payload['operator_packet_state']}`",
        f"- Runtime readiness status: `{payload['runtime_readiness_status']}`",
        f"- Runner provenance status: `{payload['runner_provenance_status']}`",
        f"- Source fingerprint status: `{payload['source_fingerprint_status']}`",
        f"- Trader process absent: `{payload['trader_process_absent']}`",
        f"- Ownership backend: `{payload['ownership_backend']}`",
        f"- Shared execution lease enforced: `{payload['shared_execution_lease_enforced']}`",
        "",
        "## Operator Rule",
        "",
        "- This is the last non-broker-facing go/no-go check before arming the exclusive execution window.",
        "- If status is `blocked`, do not arm the window.",
        "- If status is `ready_to_arm_window`, the next safe action is to arm a bounded exclusive window, then refresh packets before launch.",
    ]
    if payload["issues"]:
        lines.extend(["", "## Blocking Issues", ""])
        for issue in payload["issues"]:
            lines.append(f"- `{issue['code']}`: {issue['message']}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = build_parser().parse_args()
    report_dir = Path(args.report_dir).resolve()
    payload = build_payload(
        operator_packet=read_json(report_dir / "gcp_execution_trusted_validation_operator_packet.json"),
        runtime_readiness=read_json(report_dir / "gcp_vm_runtime_readiness_status.json"),
        runner_provenance=read_json(report_dir / "gcp_vm_runner_provenance_status.json"),
        source_fingerprint=read_json(report_dir / "gcp_vm_runner_source_fingerprint_status.json"),
        exclusive_window=read_json(report_dir / "gcp_execution_exclusive_window_status.json"),
        launch_pack=read_json(report_dir / "gcp_execution_trusted_validation_launch_pack.json"),
        report_dir=report_dir,
    )
    write_json(report_dir / "gcp_execution_prearm_preflight.json", payload)
    write_markdown(report_dir / "gcp_execution_prearm_preflight.md", payload)
    write_handoff(report_dir / "gcp_execution_prearm_preflight_handoff.md", payload)
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
