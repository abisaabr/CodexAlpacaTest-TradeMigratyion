from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[2]
DEFAULT_GCP_REPORT_DIR = REPO_ROOT / "docs" / "gcp_foundation"
DEFAULT_SESSION_HANDOFF_JSON = REPO_ROOT / "docs" / "session_reconciliation" / "session_reconciliation_handoff.json"
DEFAULT_EXECUTION_HANDOFF_JSON = REPO_ROOT / "docs" / "execution_calibration" / "execution_calibration_handoff.json"
DEFAULT_EVIDENCE_HANDOFF_JSON = REPO_ROOT / "docs" / "execution_evidence" / "execution_evidence_contract_handoff.json"
DEFAULT_MORNING_BRIEF_HANDOFF_JSON = REPO_ROOT / "docs" / "morning_brief" / "morning_operator_brief_handoff.json"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build the session-completion evidence gate for the sanctioned GCP paper session."
    )
    parser.add_argument("--report-dir", default=str(DEFAULT_GCP_REPORT_DIR))
    parser.add_argument("--session-handoff-json", default=str(DEFAULT_SESSION_HANDOFF_JSON))
    parser.add_argument("--execution-handoff-json", default=str(DEFAULT_EXECUTION_HANDOFF_JSON))
    parser.add_argument("--evidence-handoff-json", default=str(DEFAULT_EVIDENCE_HANDOFF_JSON))
    parser.add_argument("--morning-brief-handoff-json", default=str(DEFAULT_MORNING_BRIEF_HANDOFF_JSON))
    return parser


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _issue(severity: str, code: str, message: str) -> dict[str, str]:
    return {"severity": severity, "code": code, "message": message}


def _contract_ready(contract_status: str) -> bool:
    return contract_status in {"ready", "satisfied"}


def _parse_timestamp(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value))
    except ValueError:
        return None


def _is_after(lhs: datetime | None, rhs: datetime | None) -> bool:
    if lhs is None or rhs is None:
        return False
    if lhs.tzinfo is None and rhs.tzinfo is not None:
        lhs = lhs.replace(tzinfo=rhs.tzinfo)
    if rhs.tzinfo is None and lhs.tzinfo is not None:
        rhs = rhs.replace(tzinfo=lhs.tzinfo)
    return lhs > rhs


def _required_outputs(paths: dict[str, Path]) -> list[dict[str, Any]]:
    return [
        {
            "name": name,
            "path": str(path),
            "present": path.exists(),
        }
        for name, path in paths.items()
    ]


def _missing_required_outputs(required_outputs: list[dict[str, Any]]) -> list[str]:
    return [str(row["name"]) for row in required_outputs if not bool(row.get("present"))]


def build_payload(
    *,
    report_dir: Path,
    launch_authorization: dict[str, Any],
    assimilation_status: dict[str, Any],
    closeout_status: dict[str, Any],
    exclusive_window: dict[str, Any],
    session_handoff: dict[str, Any],
    execution_handoff: dict[str, Any],
    evidence_handoff: dict[str, Any],
    morning_brief_handoff: dict[str, Any],
    required_output_paths: dict[str, Path],
    now: datetime | None = None,
) -> dict[str, Any]:
    now = now or datetime.now().astimezone()
    launch_status = str(launch_authorization.get("status") or "missing")
    launch_generated_at = _parse_timestamp(launch_authorization.get("generated_at"))
    evidence_generated_at = _parse_timestamp(evidence_handoff.get("generated_at"))
    evidence_refreshed_after_launch = _is_after(evidence_generated_at, launch_generated_at)
    launch_ready = launch_status == "ready_to_launch_session" and bool(
        launch_authorization.get("authorized_command_broker_facing")
    )
    assimilation_state = str(assimilation_status.get("status") or "missing")
    assimilation_ready = assimilation_state == "ready_for_post_session_assimilation"
    closeout_state = str(closeout_status.get("closeout_status") or "missing")
    exclusive_window_status = str(exclusive_window.get("exclusive_window_status") or "missing")
    contract_status = str(evidence_handoff.get("contract_status") or "missing")
    contract_is_ready = _contract_ready(contract_status)
    required_outputs = _required_outputs(required_output_paths)
    missing_required_outputs = _missing_required_outputs(required_outputs)
    immediate_gaps = list(evidence_handoff.get("immediate_gaps") or [])

    session_posture = str(
        (session_handoff.get("posture") or {}).get("overall_session_reconciliation_posture")
        or "missing"
    )
    execution_posture = str(
        (execution_handoff.get("posture") or {}).get("overall_execution_posture")
        or "missing"
    )
    morning_posture = str(morning_brief_handoff.get("morning_decision_posture") or "missing")
    latest_traded_session_date = str(
        evidence_handoff.get("latest_traded_session_date")
        or session_handoff.get("latest_traded_session_date")
        or ""
    )

    issues: list[dict[str, str]] = []
    for name in missing_required_outputs:
        issues.append(
            _issue(
                "error",
                f"missing_{name}",
                f"The required post-session control-plane output `{name}` is missing.",
            )
        )
    if not contract_is_ready:
        for gap in immediate_gaps:
            check_id = str(gap.get("check_id") or "execution_evidence_gap")
            summary = str(gap.get("summary") or "Execution evidence contract remains gapped.")
            issues.append(_issue("error", check_id, summary))

    completion_status = "blocked"
    next_operator_action = "resolve_completion_blockers"
    if missing_required_outputs:
        completion_status = "control_outputs_missing"
        next_operator_action = "rebuild_post_session_control_outputs"
    elif contract_is_ready:
        if closeout_state == "window_already_closed":
            completion_status = "session_complete_for_review"
            next_operator_action = "review_session_evidence"
        else:
            completion_status = "awaiting_closeout"
            next_operator_action = "close_exclusive_window"
            issues.append(
                _issue(
                    "error",
                    "exclusive_window_not_closed",
                    "The session evidence may be complete, but review must wait until the exclusive window is closed.",
                )
            )
    elif launch_ready and not evidence_refreshed_after_launch:
        completion_status = "awaiting_broker_session"
        next_operator_action = "run_vm_session_command"
        issues.append(
            _issue(
                "info",
                "post_launch_evidence_not_refreshed",
                "Launch is authorized, but no newer post-launch evidence handoff has been produced yet.",
            )
        )
    elif launch_ready and not assimilation_ready:
        completion_status = "awaiting_post_session_assimilation"
        next_operator_action = "run_post_session_assimilation"
        issues.append(
            _issue(
                "error",
                "post_session_assimilation_not_ready",
                "Launch is authorized, but governed post-session assimilation has not been refreshed.",
            )
        )
    elif launch_ready and assimilation_ready:
        completion_status = "evidence_gapped"
        next_operator_action = "repair_execution_evidence_bundle"
    elif not launch_ready:
        completion_status = "awaiting_launch_authorization"
        next_operator_action = "do_not_review_unlaunched_session"
        issues.append(
            _issue(
                "info",
                "launch_authorization_not_ready",
                "No broker-facing session is authorized yet; session completion cannot be evaluated.",
            )
        )
    elif assimilation_ready:
        completion_status = "evidence_gapped"
        next_operator_action = "repair_execution_evidence_bundle"

    return {
        "generated_at": now.isoformat(),
        "completion_status": completion_status,
        "next_operator_action": next_operator_action,
        "broker_facing": False,
        "live_manifest_effect": "none",
        "risk_policy_effect": "none",
        "report_dir": str(report_dir),
        "launch_authorization_generated_at": launch_authorization.get("generated_at"),
        "evidence_handoff_generated_at": evidence_handoff.get("generated_at"),
        "evidence_refreshed_after_launch": evidence_refreshed_after_launch,
        "launch_authorization_status": launch_status,
        "launch_authorized": launch_ready,
        "post_session_assimilation_status": assimilation_state,
        "closeout_status": closeout_state,
        "exclusive_window_status": exclusive_window_status,
        "execution_evidence_contract_status": contract_status,
        "session_reconciliation_posture": session_posture,
        "execution_posture": execution_posture,
        "morning_decision_posture": morning_posture,
        "latest_traded_session_date": latest_traded_session_date,
        "required_next_session_artifacts": list(evidence_handoff.get("required_next_session_artifacts") or []),
        "required_control_plane_outputs": required_outputs,
        "missing_required_outputs": missing_required_outputs,
        "immediate_evidence_gaps": immediate_gaps,
        "issues": issues,
        "operator_read": [
            "This packet is non-broker-facing and does not start or close any session.",
            "Exclusive-window closeout is necessary but not sufficient for session completion.",
            "Treat `session_complete_for_review` as evidence-review readiness only, not strategy-promotion approval.",
            "Do not count a raw PnL winner as a qualified winner unless this gate is complete and the evidence contract is clean.",
        ],
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "# GCP Execution Session Completion Gate",
        "",
        "## Snapshot",
        "",
        f"- Generated at: `{payload['generated_at']}`",
        f"- Completion status: `{payload['completion_status']}`",
        f"- Next operator action: `{payload['next_operator_action']}`",
        f"- Launch authorization status: `{payload['launch_authorization_status']}`",
        f"- Evidence refreshed after launch: `{payload['evidence_refreshed_after_launch']}`",
        f"- Launch authorized: `{payload['launch_authorized']}`",
        f"- Post-session assimilation status: `{payload['post_session_assimilation_status']}`",
        f"- Closeout status: `{payload['closeout_status']}`",
        f"- Exclusive window status: `{payload['exclusive_window_status']}`",
        f"- Execution evidence contract status: `{payload['execution_evidence_contract_status']}`",
        f"- Latest traded session date: `{payload['latest_traded_session_date'] or 'none'}`",
        "",
        "## Required Next Session Artifacts",
        "",
    ]
    for artifact in list(payload.get("required_next_session_artifacts") or []):
        lines.append(f"- {artifact}")
    if not list(payload.get("required_next_session_artifacts") or []):
        lines.append("- none listed")
    lines.extend(["", "## Required Control-Plane Outputs", ""])
    for row in list(payload.get("required_control_plane_outputs") or []):
        lines.append(f"- `{row['name']}`: present `{str(bool(row['present'])).lower()}` at `{row['path']}`")
    lines.extend(["", "## Issues", ""])
    if payload.get("issues"):
        for issue in list(payload.get("issues") or []):
            lines.append(f"- `{issue['severity']}` `{issue['code']}`: {issue['message']}")
    else:
        lines.append("- none")
    lines.extend(["", "## Operator Read", ""])
    for item in list(payload.get("operator_read") or []):
        lines.append(f"- {item}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_handoff(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "# GCP Execution Session Completion Gate Handoff",
        "",
        f"- Completion status: `{payload['completion_status']}`",
        f"- Next operator action: `{payload['next_operator_action']}`",
        f"- Launch authorization status: `{payload['launch_authorization_status']}`",
        f"- Evidence refreshed after launch: `{payload['evidence_refreshed_after_launch']}`",
        f"- Post-session assimilation status: `{payload['post_session_assimilation_status']}`",
        f"- Closeout status: `{payload['closeout_status']}`",
        f"- Execution evidence contract status: `{payload['execution_evidence_contract_status']}`",
        f"- Latest traded session date: `{payload['latest_traded_session_date'] or 'none'}`",
        "",
        "## Operator Rule",
        "",
        "- Do not treat closeout alone as a completed trusted session.",
        "- A qualified winner session requires this gate to reach `session_complete_for_review` and the execution evidence contract to be clean.",
        "- If this gate is not complete, keep promotion and unlock review blocked even if raw PnL was positive.",
    ]
    if payload.get("issues"):
        lines.extend(["", "## Open Issues", ""])
        for issue in list(payload.get("issues") or []):
            lines.append(f"- `{issue['code']}`: {issue['message']}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = build_parser().parse_args()
    report_dir = Path(args.report_dir).resolve()
    required_output_paths = {
        "session_reconciliation_handoff": Path(args.session_handoff_json).resolve(),
        "execution_calibration_handoff": Path(args.execution_handoff_json).resolve(),
        "execution_evidence_contract_handoff": Path(args.evidence_handoff_json).resolve(),
        "morning_operator_brief_handoff": Path(args.morning_brief_handoff_json).resolve(),
    }
    payload = build_payload(
        report_dir=report_dir,
        launch_authorization=read_json(report_dir / "gcp_execution_launch_authorization.json"),
        assimilation_status=read_json(report_dir / "gcp_post_session_assimilation_status.json"),
        closeout_status=read_json(report_dir / "gcp_execution_closeout_status.json"),
        exclusive_window=read_json(report_dir / "gcp_execution_exclusive_window_status.json"),
        session_handoff=read_json(required_output_paths["session_reconciliation_handoff"]),
        execution_handoff=read_json(required_output_paths["execution_calibration_handoff"]),
        evidence_handoff=read_json(required_output_paths["execution_evidence_contract_handoff"]),
        morning_brief_handoff=read_json(required_output_paths["morning_operator_brief_handoff"]),
        required_output_paths=required_output_paths,
    )
    write_json(report_dir / "gcp_execution_session_completion_gate.json", payload)
    write_markdown(report_dir / "gcp_execution_session_completion_gate.md", payload)
    write_handoff(report_dir / "gcp_execution_session_completion_gate_handoff.md", payload)
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
