from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[2]
DEFAULT_REPORT_DIR = REPO_ROOT / "docs" / "gcp_foundation"
DEFAULT_MAX_PREARM_AGE_MINUTES = 20


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build the final launch-authorization packet for the sanctioned VM paper session."
    )
    parser.add_argument("--report-dir", default=str(DEFAULT_REPORT_DIR))
    parser.add_argument("--max-prearm-age-minutes", type=int, default=DEFAULT_MAX_PREARM_AGE_MINUTES)
    return parser


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _issue(severity: str, code: str, message: str) -> dict[str, str]:
    return {"severity": severity, "code": code, "message": message}


def _age_minutes(timestamp: str, now: datetime) -> float | None:
    if not timestamp:
        return None
    try:
        generated_at = datetime.fromisoformat(timestamp)
    except ValueError:
        return None
    if generated_at.tzinfo is None and now.tzinfo is not None:
        generated_at = generated_at.replace(tzinfo=now.tzinfo)
    return (now - generated_at).total_seconds() / 60


def _int_or_default(value: Any, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def build_payload(
    *,
    operator_packet: dict[str, Any],
    launch_pack: dict[str, Any],
    trusted_validation: dict[str, Any],
    exclusive_window: dict[str, Any],
    closeout_status: dict[str, Any],
    runtime_readiness: dict[str, Any],
    runner_provenance: dict[str, Any],
    source_fingerprint: dict[str, Any],
    prearm_preflight: dict[str, Any],
    launch_surface_audit: dict[str, Any] | None = None,
    report_dir: Path,
    max_prearm_age_minutes: int,
    now: datetime | None = None,
) -> dict[str, Any]:
    now = now or datetime.now().astimezone()
    launch_surface_audit = launch_surface_audit or {}
    operator_packet_state = str(operator_packet.get("operator_packet_state") or "missing")
    launch_pack_state = str(launch_pack.get("launch_pack_state") or "missing")
    trusted_validation_readiness = str(trusted_validation.get("trusted_validation_readiness") or "missing")
    exclusive_window_status = str(exclusive_window.get("exclusive_window_status") or "missing")
    closeout_state = str(closeout_status.get("closeout_status") or "missing")
    runtime_status = str(runtime_readiness.get("status") or "missing")
    provenance_status = str(runner_provenance.get("status") or "missing")
    source_fingerprint_status = str(source_fingerprint.get("status") or "missing")
    prearm_status = str(prearm_preflight.get("status") or "missing")
    prearm_age_minutes = _age_minutes(str(prearm_preflight.get("generated_at") or ""), now)
    launch_surface_audit_status = str(launch_surface_audit.get("status") or "missing")
    launch_surface_audit_age_minutes = _age_minutes(
        str(launch_surface_audit.get("generated_at") or launch_surface_audit.get("as_of") or ""), now
    )
    launch_surface_broker_state = launch_surface_audit.get("broker_state") or {}
    if not isinstance(launch_surface_broker_state, dict):
        launch_surface_broker_state = {}
    launch_surface_watch = launch_surface_broker_state.get("post_fencing_no_new_order_watch") or {}
    if not isinstance(launch_surface_watch, dict):
        launch_surface_watch = {}
    launch_surface_broker_flat = (
        launch_surface_broker_state.get("broker_flat") is True
        or str(launch_surface_broker_state.get("read_only_check_after_fencing") or "")
        == "position_count=0, open_order_count=0"
    )
    launch_surface_no_new_order_watch_clean = (
        launch_surface_watch.get("watch_clean") is True
        and _int_or_default(launch_surface_watch.get("duration_seconds"), 0) >= 180
        and _int_or_default(launch_surface_watch.get("position_count_all_samples"), -1) == 0
        and _int_or_default(launch_surface_watch.get("open_order_count_all_samples"), -1) == 0
        and launch_surface_watch.get("newest_order_constant") is True
    )
    vm_name = str(operator_packet.get("vm_name") or launch_pack.get("vm_name") or "missing")
    launch_vm_name = str(launch_pack.get("vm_name") or "missing")
    session_command = str(launch_pack.get("vm_session_command") or "")

    issues: list[dict[str, str]] = []
    if operator_packet_state != "ready_to_launch_session":
        issues.append(
            _issue(
                "error",
                "operator_packet_not_ready_to_launch",
                "The top-level operator packet must be `ready_to_launch_session` before launch.",
            )
        )
    if launch_pack_state != "ready_to_launch":
        issues.append(
            _issue(
                "error",
                "launch_pack_not_ready",
                "The launch pack must be `ready_to_launch` before the broker-facing session command is authorized.",
            )
        )
    if trusted_validation_readiness != "ready_for_manual_launch":
        issues.append(
            _issue(
                "error",
                "trusted_validation_not_ready",
                "Trusted validation readiness must be `ready_for_manual_launch` before launch.",
            )
        )
    if exclusive_window_status != "ready_for_launch":
        issues.append(
            _issue(
                "error",
                "exclusive_window_not_ready",
                "The exclusive-window packet must say `ready_for_launch` before launch.",
            )
        )
    if closeout_state != "ready_to_close_window":
        issues.append(
            _issue(
                "error",
                "closeout_not_reserved",
                "Closeout must be reserved as `ready_to_close_window` before launch.",
            )
        )
    if runtime_status != "runtime_ready":
        issues.append(
            _issue(
                "error",
                "runtime_not_ready",
                "VM runtime readiness must be clean immediately before launch.",
            )
        )
    if provenance_status != "provenance_matched":
        issues.append(
            _issue(
                "error",
                "runner_provenance_not_matched",
                "VM runner provenance must be matched before launch.",
            )
        )
    if source_fingerprint_status != "source_fingerprint_matched":
        issues.append(
            _issue(
                "error",
                "source_fingerprint_not_matched",
                "VM source fingerprint must be matched before launch.",
            )
        )
    if prearm_status != "ready_to_arm_window":
        issues.append(
            _issue(
                "error",
                "prearm_preflight_not_ready",
                "The pre-arm preflight that authorized arming must be present and `ready_to_arm_window`.",
            )
        )
    if prearm_age_minutes is None:
        issues.append(
            _issue(
                "error",
                "prearm_preflight_timestamp_invalid",
                "The pre-arm preflight must have a valid `generated_at` timestamp.",
            )
        )
    elif prearm_age_minutes > max_prearm_age_minutes:
        issues.append(
            _issue(
                "error",
                "prearm_preflight_stale",
                f"The pre-arm preflight is {prearm_age_minutes:.2f} minutes old; maximum allowed is {max_prearm_age_minutes}.",
            )
        )
    elif prearm_age_minutes < -5:
        issues.append(
            _issue(
                "error",
                "prearm_preflight_future_timestamp",
                "The pre-arm preflight timestamp appears to be in the future.",
            )
        )
    if launch_surface_audit_status != "local_broker_capable_surfaces_fenced_broker_flat":
        issues.append(
            _issue(
                "error",
                "launch_surface_audit_not_clean",
                "The launch-surface audit must show broker-capable local surfaces fenced and broker flat before launch.",
            )
        )
    if launch_surface_audit_age_minutes is None:
        issues.append(
            _issue(
                "error",
                "launch_surface_audit_timestamp_invalid",
                "The launch-surface audit must have a valid `generated_at` or `as_of` timestamp.",
            )
        )
    elif launch_surface_audit_age_minutes > max_prearm_age_minutes:
        issues.append(
            _issue(
                "error",
                "launch_surface_audit_stale",
                f"The launch-surface audit is {launch_surface_audit_age_minutes:.2f} minutes old; maximum allowed is {max_prearm_age_minutes}.",
            )
        )
    elif launch_surface_audit_age_minutes < -5:
        issues.append(
            _issue(
                "error",
                "launch_surface_audit_future_timestamp",
                "The launch-surface audit timestamp appears to be in the future.",
            )
        )
    if not launch_surface_broker_flat:
        issues.append(
            _issue(
                "error",
                "launch_surface_broker_not_flat",
                "The launch-surface audit must show zero broker positions and zero open broker orders.",
            )
        )
    if not launch_surface_no_new_order_watch_clean:
        issues.append(
            _issue(
                "error",
                "launch_surface_no_new_order_watch_not_clean",
                "The launch-surface audit must include a clean no-new-order watch with zero positions, zero open orders, and a constant newest order timestamp.",
            )
        )
    if runtime_readiness.get("trader_process_absent") is not True:
        issues.append(
            _issue(
                "error",
                "trader_process_not_clear",
                "No trader process may already be running on the VM before launch.",
            )
        )
    if runtime_readiness.get("ownership_enabled") is not True:
        issues.append(
            _issue(
                "error",
                "runtime_ownership_not_enabled",
                "Runtime ownership must be enabled before launch.",
            )
        )
    if str(runtime_readiness.get("ownership_backend") or "missing") != "file":
        issues.append(
            _issue(
                "error",
                "runtime_ownership_backend_not_file",
                "The first trusted VM session must use the local file ownership lease.",
            )
        )
    if bool(runtime_readiness.get("shared_execution_lease_enforced")):
        issues.append(
            _issue(
                "error",
                "shared_execution_lease_enforced_too_early",
                "GCS shared-lease enforcement is not approved for the first trusted VM session.",
            )
        )
    if vm_name != launch_vm_name:
        issues.append(
            _issue(
                "error",
                "launch_vm_mismatch",
                f"Operator packet VM `{vm_name}` does not match launch pack VM `{launch_vm_name}`.",
            )
        )
    if "--submit-paper-orders" not in session_command:
        issues.append(
            _issue(
                "error",
                "session_command_missing_paper_submit_flag",
                "The authorized session command must explicitly include `--submit-paper-orders`.",
            )
        )

    status = "ready_to_launch_session"
    if any(issue["severity"] == "error" for issue in issues):
        status = "blocked"

    return {
        "generated_at": now.isoformat(),
        "status": status,
        "next_operator_action": "run_vm_session_command" if status == "ready_to_launch_session" else "resolve_launch_blockers",
        "report_dir": str(report_dir),
        "broker_facing": False,
        "authorized_command_broker_facing": status == "ready_to_launch_session",
        "live_manifest_effect": "none",
        "risk_policy_effect": "none",
        "vm_name": vm_name,
        "operator_packet_state": operator_packet_state,
        "launch_pack_state": launch_pack_state,
        "trusted_validation_readiness": trusted_validation_readiness,
        "exclusive_window_status": exclusive_window_status,
        "closeout_status": closeout_state,
        "runtime_readiness_status": runtime_status,
        "runner_provenance_status": provenance_status,
        "source_fingerprint_status": source_fingerprint_status,
        "prearm_preflight_status": prearm_status,
        "prearm_preflight_age_minutes": prearm_age_minutes,
        "launch_surface_audit_status": launch_surface_audit_status,
        "launch_surface_audit_age_minutes": launch_surface_audit_age_minutes,
        "launch_surface_broker_flat": launch_surface_broker_flat,
        "launch_surface_no_new_order_watch_clean": launch_surface_no_new_order_watch_clean,
        "max_prearm_age_minutes": max_prearm_age_minutes,
        "trader_process_absent": runtime_readiness.get("trader_process_absent"),
        "ownership_enabled": runtime_readiness.get("ownership_enabled"),
        "ownership_backend": runtime_readiness.get("ownership_backend"),
        "shared_execution_lease_enforced": bool(runtime_readiness.get("shared_execution_lease_enforced")),
        "operator_ssh_command": launch_pack.get("operator_ssh_command"),
        "vm_session_command": session_command,
        "post_session_assimilation_command": launch_pack.get("post_session_assimilation_command"),
        "closeout_command_template": operator_packet.get("closeout_command_template"),
        "required_evidence": list(launch_pack.get("required_evidence") or []),
        "issues": issues,
        "operator_read": [
            "This packet is non-broker-facing; it does not start the VM session.",
            "If status is `blocked`, do not run the VM session command.",
            "If status is `ready_to_launch_session`, run the VM command manually inside the attested exclusive window, then run post-session assimilation and closeout.",
            "Do not treat a successful launch authorization as strategy-promotion evidence; only the post-session evidence bundle can support review.",
        ],
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "# GCP Execution Launch Authorization",
        "",
        "## Snapshot",
        "",
        f"- Generated at: `{payload['generated_at']}`",
        f"- Status: `{payload['status']}`",
        f"- Next operator action: `{payload['next_operator_action']}`",
        f"- VM name: `{payload['vm_name']}`",
        f"- Operator packet state: `{payload['operator_packet_state']}`",
        f"- Launch pack state: `{payload['launch_pack_state']}`",
        f"- Trusted validation readiness: `{payload['trusted_validation_readiness']}`",
        f"- Exclusive window status: `{payload['exclusive_window_status']}`",
        f"- Runtime readiness status: `{payload['runtime_readiness_status']}`",
        f"- Runner provenance status: `{payload['runner_provenance_status']}`",
        f"- Source fingerprint status: `{payload['source_fingerprint_status']}`",
        f"- Pre-arm preflight status: `{payload['prearm_preflight_status']}`",
        f"- Pre-arm preflight age minutes: `{payload['prearm_preflight_age_minutes']}`",
        f"- Launch-surface audit status: `{payload['launch_surface_audit_status']}`",
        f"- Launch-surface audit age minutes: `{payload['launch_surface_audit_age_minutes']}`",
        f"- Launch-surface broker flat: `{payload['launch_surface_broker_flat']}`",
        f"- Launch-surface no-new-order watch clean: `{payload['launch_surface_no_new_order_watch_clean']}`",
        f"- Trader process absent: `{payload['trader_process_absent']}`",
        f"- Ownership backend: `{payload['ownership_backend']}`",
        f"- Shared execution lease enforced: `{payload['shared_execution_lease_enforced']}`",
        "",
        "## Commands",
        "",
        "### Operator SSH",
        "",
        "```bash",
        str(payload.get("operator_ssh_command") or ""),
        "```",
        "",
        "### VM Session Command",
        "",
        "```bash",
        str(payload.get("vm_session_command") or ""),
        "```",
        "",
        "### Post-Session Assimilation",
        "",
        "```powershell",
        str(payload.get("post_session_assimilation_command") or ""),
        "```",
        "",
        "### Close Window",
        "",
        "```powershell",
        str(payload.get("closeout_command_template") or ""),
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
    lines.extend(["", "## Required Evidence", ""])
    for item in payload["required_evidence"]:
        lines.append(f"- `{item}`")
    lines.extend(["", "## Operator Read", ""])
    for item in payload["operator_read"]:
        lines.append(f"- {item}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_handoff(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "# GCP Execution Launch Authorization Handoff",
        "",
        f"- Status: `{payload['status']}`",
        f"- Next operator action: `{payload['next_operator_action']}`",
        f"- VM name: `{payload['vm_name']}`",
        f"- Operator packet state: `{payload['operator_packet_state']}`",
        f"- Launch pack state: `{payload['launch_pack_state']}`",
        f"- Exclusive window status: `{payload['exclusive_window_status']}`",
        f"- Runtime readiness status: `{payload['runtime_readiness_status']}`",
        f"- Runner provenance status: `{payload['runner_provenance_status']}`",
        f"- Source fingerprint status: `{payload['source_fingerprint_status']}`",
        f"- Launch-surface audit status: `{payload['launch_surface_audit_status']}`",
        f"- Launch-surface broker flat: `{payload['launch_surface_broker_flat']}`",
        f"- Launch-surface no-new-order watch clean: `{payload['launch_surface_no_new_order_watch_clean']}`",
        f"- Trader process absent: `{payload['trader_process_absent']}`",
        f"- Ownership backend: `{payload['ownership_backend']}`",
        "",
        "## Operator Rule",
        "",
        "- This is the final non-broker-facing go/no-go packet before running the VM session command.",
        "- If status is `blocked`, do not run the VM session command.",
        "- If status is `ready_to_launch_session`, run only the listed VM session command inside the active exclusive window.",
        "- After the session ends, run post-session assimilation and close the exclusive window.",
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
        launch_pack=read_json(report_dir / "gcp_execution_trusted_validation_launch_pack.json"),
        trusted_validation=read_json(report_dir / "gcp_execution_trusted_validation_session_status.json"),
        exclusive_window=read_json(report_dir / "gcp_execution_exclusive_window_status.json"),
        closeout_status=read_json(report_dir / "gcp_execution_closeout_status.json"),
        runtime_readiness=read_json(report_dir / "gcp_vm_runtime_readiness_status.json"),
        runner_provenance=read_json(report_dir / "gcp_vm_runner_provenance_status.json"),
        source_fingerprint=read_json(report_dir / "gcp_vm_runner_source_fingerprint_status.json"),
        prearm_preflight=read_json(report_dir / "gcp_execution_prearm_preflight.json"),
        launch_surface_audit=read_json(report_dir / "gcp_execution_launch_surface_audit.json"),
        report_dir=report_dir,
        max_prearm_age_minutes=args.max_prearm_age_minutes,
    )
    write_json(report_dir / "gcp_execution_launch_authorization.json", payload)
    write_markdown(report_dir / "gcp_execution_launch_authorization.md", payload)
    write_handoff(report_dir / "gcp_execution_launch_authorization_handoff.md", payload)
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
