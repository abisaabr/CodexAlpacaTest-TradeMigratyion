from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[2]
DEFAULT_WORKPLAN_JSON = REPO_ROOT / "docs" / "tournament_unlocks" / "tournament_unlock_workplan.json"
DEFAULT_SESSION_REGISTRY_JSON = REPO_ROOT / "docs" / "session_reconciliation" / "session_reconciliation_registry.json"
DEFAULT_SESSION_HANDOFF_JSON = REPO_ROOT / "docs" / "session_reconciliation" / "session_reconciliation_handoff.json"
DEFAULT_EXECUTION_HANDOFF_JSON = REPO_ROOT / "docs" / "execution_calibration" / "execution_calibration_handoff.json"
DEFAULT_REPORT_DIR = REPO_ROOT / "docs" / "execution_evidence"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build a machine-readable execution evidence contract for the next trusted paper-runner session."
    )
    parser.add_argument("--workplan-json", default=str(DEFAULT_WORKPLAN_JSON))
    parser.add_argument("--session-registry-json", default=str(DEFAULT_SESSION_REGISTRY_JSON))
    parser.add_argument("--session-handoff-json", default=str(DEFAULT_SESSION_HANDOFF_JSON))
    parser.add_argument("--execution-handoff-json", default=str(DEFAULT_EXECUTION_HANDOFF_JSON))
    parser.add_argument("--report-dir", default=str(DEFAULT_REPORT_DIR))
    return parser


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def latest_traded_session(registry: dict[str, Any]) -> dict[str, Any] | None:
    sessions = [
        dict(row)
        for row in list(registry.get("sessions") or [])
        if isinstance(row, dict) and str(row.get("session_kind")) == "traded"
    ]
    if not sessions:
        return None
    sessions.sort(key=lambda row: str(row.get("trade_date", "")), reverse=True)
    return sessions[0]


def bool_ok(value: Any) -> bool:
    return bool(value)


def build_checks(
    latest_session: dict[str, Any] | None,
    workplan: dict[str, Any],
    session_handoff: dict[str, Any],
    execution_handoff: dict[str, Any],
) -> list[dict[str, Any]]:
    execution_mission = dict(workplan.get("execution_plane_mission") or {})
    target_profiles = list(execution_mission.get("primary_target_profiles") or [])
    exit_sensitive_targets = any("convexity" in target or "single_vs_multileg" in target for target in target_profiles)

    session = latest_session or {}
    checks: list[dict[str, Any]] = []

    def add_check(check_id: str, summary: str, required: str, passed: bool, current: Any) -> None:
        checks.append(
            {
                "check_id": check_id,
                "summary": summary,
                "required": required,
                "current": current,
                "passed": passed,
            }
        )

    add_check(
        "traded_session_exists",
        "A traded paper-runner session must exist for the session to teach research anything.",
        "session_kind = traded",
        latest_session is not None,
        session.get("session_kind", "none"),
    )
    add_check(
        "shutdown_reconciled",
        "The session must complete shutdown reconciliation cleanly.",
        "shutdown_reconciled = true",
        bool_ok(session.get("shutdown_reconciled")),
        session.get("shutdown_reconciled"),
    )
    add_check(
        "trust_tier_not_review_required",
        "The session must not be review-required.",
        "trust_tier in {trusted, caution}",
        str(session.get("trust_tier", "")) in {"trusted", "caution"},
        session.get("trust_tier"),
    )
    add_check(
        "broker_order_audit",
        "Broker-order audit coverage must be present in the session bundle.",
        "broker_order_audit_available = true",
        bool_ok(session.get("broker_order_audit_available")),
        session.get("broker_order_audit_available"),
    )
    add_check(
        "broker_activity_audit",
        "Broker account-activity audit coverage must be present in the session bundle.",
        "broker_activity_audit_available = true",
        bool_ok(session.get("broker_activity_audit_available")),
        session.get("broker_activity_audit_available"),
    )
    add_check(
        "ending_positions_flat",
        "Residual broker positions must be zero at the end of the session.",
        "ending_broker_position_count = 0",
        int(session.get("ending_broker_position_count", 0) or 0) == 0,
        int(session.get("ending_broker_position_count", 0) or 0),
    )
    add_check(
        "broker_local_cashflow_comparable",
        "Broker/local economics comparison must be available when broker activity audit exists.",
        "broker_local_cashflow_comparable = true",
        bool_ok(session.get("broker_local_cashflow_comparable")),
        session.get("broker_local_cashflow_comparable"),
    )
    add_check(
        "completed_trade_count_positive",
        "The session must contain at least one completed trade to improve execution evidence beyond idle status.",
        "completed_trade_count > 0",
        int(session.get("completed_trade_count", 0) or 0) > 0,
        int(session.get("completed_trade_count", 0) or 0),
    )
    add_check(
        "review_scope_preserved",
        "Trusted learning scope must remain at least `trusted_and_cautious_sessions` after the session refresh.",
        "trusted_learning_scope in {trusted_and_cautious_sessions, all_recent_sessions}",
        str((session_handoff.get("policy") or {}).get("trusted_learning_scope", "")) in {
            "trusted_and_cautious_sessions",
            "all_recent_sessions",
        },
        (session_handoff.get("policy") or {}).get("trusted_learning_scope"),
    )
    add_check(
        "evidence_strength_progress",
        "Execution evidence should improve beyond `limited_entry_only` for the nearest unlock target.",
        "execution_evidence_strength != limited_entry_only",
        str((execution_handoff.get("posture") or {}).get("evidence_strength", "")) != "limited_entry_only",
        (execution_handoff.get("posture") or {}).get("evidence_strength"),
    )

    if exit_sensitive_targets:
        add_check(
            "exit_telemetry_present",
            "Exit-sensitive unlock targets require explicit exit telemetry in the evidence set.",
            "exit_telemetry_gap = false",
            not bool((execution_handoff.get("posture") or {}).get("flags", {}).get("exit_telemetry_gap")),
            bool((execution_handoff.get("posture") or {}).get("flags", {}).get("exit_telemetry_gap")),
        )

    return checks


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    lines: list[str] = []
    lines.append("# Execution Evidence Contract")
    lines.append("")
    lines.append("## Snapshot")
    lines.append("")
    lines.append(f"- Generated at: `{payload['generated_at']}`")
    lines.append(f"- Current unlocked profile: `{payload['current_unlocked_profile']}`")
    lines.append(f"- Execution mission title: {payload['execution_mission_title']}")
    lines.append(f"- Contract status: `{payload['contract_status']}`")
    lines.append(f"- Latest traded session used: `{payload['latest_traded_session_date'] or 'none'}`")
    lines.append("")
    lines.append("## Required Checks")
    lines.append("")
    for row in list(payload.get("checks") or []):
        lines.append(
            f"- `{row['check_id']}`: passed `{str(bool(row['passed'])).lower()}`, required `{row['required']}`, current `{row['current']}`"
        )
    lines.append("")
    lines.append("## Immediate Gaps")
    lines.append("")
    for row in list(payload.get("failed_checks") or []):
        lines.append(f"- `{row['check_id']}`: {row['summary']}")
    if not list(payload.get("failed_checks") or []):
        lines.append("- none")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = build_parser().parse_args()
    report_dir = Path(args.report_dir).resolve()
    report_dir.mkdir(parents=True, exist_ok=True)

    workplan = read_json(Path(args.workplan_json).resolve())
    session_registry = read_json(Path(args.session_registry_json).resolve())
    session_handoff = read_json(Path(args.session_handoff_json).resolve())
    execution_handoff = read_json(Path(args.execution_handoff_json).resolve())

    latest_session = latest_traded_session(session_registry)
    checks = build_checks(latest_session, workplan, session_handoff, execution_handoff)
    failed_checks = [dict(row) for row in checks if not bool(row.get("passed"))]

    payload = {
        "generated_at": datetime.now().isoformat(),
        "workplan_json": str(Path(args.workplan_json).resolve()),
        "session_registry_json": str(Path(args.session_registry_json).resolve()),
        "session_handoff_json": str(Path(args.session_handoff_json).resolve()),
        "execution_handoff_json": str(Path(args.execution_handoff_json).resolve()),
        "current_unlocked_profile": workplan.get("current_unlocked_profile"),
        "execution_mission_title": ((workplan.get("execution_plane_mission") or {}).get("title")),
        "latest_traded_session_date": (latest_session or {}).get("trade_date"),
        "contract_status": "ready" if not failed_checks else "gapped",
        "checks": checks,
        "failed_checks": failed_checks,
    }

    json_path = report_dir / "execution_evidence_contract.json"
    md_path = report_dir / "execution_evidence_contract.md"
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    write_markdown(md_path, payload)
    print(json.dumps({"json_path": str(json_path), "markdown_path": str(md_path)}, indent=2))


if __name__ == "__main__":
    main()
