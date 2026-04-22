from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[2]
DEFAULT_REPO_UPDATE_HANDOFF_JSON = REPO_ROOT / "docs" / "repo_updates" / "repo_update_handoff.json"
DEFAULT_SESSION_RECONCILIATION_HANDOFF_JSON = (
    REPO_ROOT / "docs" / "session_reconciliation" / "session_reconciliation_handoff.json"
)
DEFAULT_EXECUTION_CALIBRATION_HANDOFF_JSON = (
    REPO_ROOT / "docs" / "execution_calibration" / "execution_calibration_handoff.json"
)
DEFAULT_TOURNAMENT_PROFILE_HANDOFF_JSON = (
    REPO_ROOT / "docs" / "tournament_profiles" / "tournament_profile_handoff.json"
)
DEFAULT_TOURNAMENT_UNLOCK_HANDOFF_JSON = (
    REPO_ROOT / "docs" / "tournament_unlocks" / "tournament_unlock_handoff.json"
)
DEFAULT_TOURNAMENT_UNLOCK_WORKPLAN_HANDOFF_JSON = (
    REPO_ROOT / "docs" / "tournament_unlocks" / "tournament_unlock_workplan_handoff.json"
)
DEFAULT_EXECUTION_EVIDENCE_HANDOFF_JSON = (
    REPO_ROOT / "docs" / "execution_evidence" / "execution_evidence_contract_handoff.json"
)
DEFAULT_OVERNIGHT_PLAN_HANDOFF_JSON = (
    REPO_ROOT / "docs" / "overnight_plan" / "overnight_phased_plan_handoff.json"
)
DEFAULT_REPORT_DIR = REPO_ROOT / "docs" / "morning_brief"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build a compact morning operator brief from the governed post-session control-plane handoffs."
    )
    parser.add_argument("--repo-update-handoff-json", default=str(DEFAULT_REPO_UPDATE_HANDOFF_JSON))
    parser.add_argument("--session-handoff-json", default=str(DEFAULT_SESSION_RECONCILIATION_HANDOFF_JSON))
    parser.add_argument("--execution-handoff-json", default=str(DEFAULT_EXECUTION_CALIBRATION_HANDOFF_JSON))
    parser.add_argument("--profile-handoff-json", default=str(DEFAULT_TOURNAMENT_PROFILE_HANDOFF_JSON))
    parser.add_argument("--unlock-handoff-json", default=str(DEFAULT_TOURNAMENT_UNLOCK_HANDOFF_JSON))
    parser.add_argument("--workplan-handoff-json", default=str(DEFAULT_TOURNAMENT_UNLOCK_WORKPLAN_HANDOFF_JSON))
    parser.add_argument("--evidence-handoff-json", default=str(DEFAULT_EXECUTION_EVIDENCE_HANDOFF_JSON))
    parser.add_argument("--overnight-plan-handoff-json", default=str(DEFAULT_OVERNIGHT_PLAN_HANDOFF_JSON))
    parser.add_argument("--report-dir", default=str(DEFAULT_REPORT_DIR))
    return parser


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def unique_strings(values: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        text = str(value or "").strip()
        if not text or text in seen:
            continue
        seen.add(text)
        ordered.append(text)
    return ordered


def derive_decision_posture(
    repo_update: dict[str, Any],
    session_handoff: dict[str, Any],
    execution_handoff: dict[str, Any],
    evidence_handoff: dict[str, Any],
) -> tuple[str, list[str]]:
    actions: list[str] = []
    repo_status = str(repo_update.get("overall_status") or "")
    session_posture = str(((session_handoff.get("posture") or {}).get("overall_session_reconciliation_posture")) or "")
    execution_posture = str(((execution_handoff.get("posture") or {}).get("overall_execution_posture")) or "")
    contract_status = str(evidence_handoff.get("contract_status") or "")

    if repo_status and repo_status != "ready":
        actions.append("Pause morning escalation until repo update control is back to `ready`.")
        return "hold_for_repo_update", actions
    if session_posture == "review_required":
        actions.append("Do not let the latest session teach research policy until reconciliation review is complete.")
        return "hold_for_reconciliation_review", actions
    if contract_status == "satisfied":
        if execution_posture == "caution":
            actions.append("Reassess the nearest blocked profile, but keep activation disciplined because execution posture is still `caution`.")
            return "reassess_blocked_profiles_with_caution", actions
        actions.append("Reassess the nearest blocked profile because the current execution evidence contract is satisfied.")
        return "reassess_blocked_profiles", actions
    if contract_status == "gapped":
        actions.append("Keep blocked profiles blocked until the missing execution evidence package lands.")
        return "keep_blocked_profiles_blocked", actions
    actions.append("Continue from the current unlocked profile and inspect fresh evidence before changing policy.")
    return "continue_with_caution", actions


def build_operator_actions(
    repo_update: dict[str, Any],
    session_handoff: dict[str, Any],
    execution_handoff: dict[str, Any],
    unlock_handoff: dict[str, Any],
    workplan_handoff: dict[str, Any],
    evidence_handoff: dict[str, Any],
    overnight_plan_handoff: dict[str, Any],
) -> list[str]:
    current_profile = str(
        overnight_plan_handoff.get("current_unlocked_profile")
        or unlock_handoff.get("current_resolved_profile")
        or ""
    )
    blocked_profiles = list(overnight_plan_handoff.get("blocked_profiles_must_remain_blocked") or [])
    nearest_targets = [
        str(row.get("profile_id") or "")
        for row in list(unlock_handoff.get("closest_next_unlock_targets") or [])
        if isinstance(row, dict)
    ][:3]

    actions = []
    if current_profile:
        actions.append(f"Keep `{current_profile}` as the current governed profile unless the refreshed unlock packet says otherwise.")
    actions.extend(list(repo_update.get("overall_actions") or []))
    actions.extend(list(((session_handoff.get("policy") or {}).get("operator_actions")) or []))
    actions.extend(list(((execution_handoff.get("policy") or {}).get("operator_actions")) or []))
    actions.extend(list(workplan_handoff.get("operator_actions") or []))
    actions.extend(list(overnight_plan_handoff.get("operator_actions") or []))
    if blocked_profiles:
        actions.append(f"Keep blocked profiles blocked for now: `{', '.join(blocked_profiles)}`.")
    if nearest_targets:
        actions.append(f"The nearest unlock targets to reassess after trusted evidence lands are `{', '.join(nearest_targets)}`.")
    actions.extend(
        f"Close the immediate evidence gap `{row.get('check_id')}`: {row.get('summary')}"
        for row in list(evidence_handoff.get("immediate_gaps") or [])
        if isinstance(row, dict)
    )
    return unique_strings(actions)


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    lines: list[str] = []
    lines.append("# Morning Operator Brief")
    lines.append("")
    lines.append("## Snapshot")
    lines.append("")
    lines.append(f"- Generated at: `{payload['generated_at']}`")
    lines.append(f"- Morning decision posture: `{payload['morning_decision_posture']}`")
    lines.append(f"- Current unlocked profile: `{payload['current_unlocked_profile']}`")
    lines.append(f"- Repo update status: `{payload['repo_update_status']}`")
    lines.append(f"- Session reconciliation posture: `{payload['session_reconciliation_posture']}`")
    lines.append(f"- Execution posture: `{payload['execution_posture']}`")
    lines.append(f"- Execution evidence contract: `{payload['execution_evidence_contract_status']}`")
    lines.append("")
    lines.append("## Current Missions")
    lines.append("")
    lines.append(f"- Research machine: {payload['research_machine_mission']}")
    lines.append(f"- New machine: {payload['new_machine_mission']}")
    lines.append("")
    lines.append("## Immediate Actions")
    lines.append("")
    for action in list(payload.get("operator_actions") or []):
        lines.append(f"- {action}")
    lines.append("")
    lines.append("## Required Next-Session Artifacts")
    lines.append("")
    for artifact in list(payload.get("required_next_session_artifacts") or []):
        lines.append(f"- {artifact}")
    lines.append("")
    lines.append("## Blocked Profiles")
    lines.append("")
    for profile in list(payload.get("blocked_profiles_must_remain_blocked") or []):
        lines.append(f"- `{profile}`")
    lines.append("")
    lines.append("## Nearest Unlock Targets")
    lines.append("")
    for row in list(payload.get("nearest_unlock_targets") or []):
        lines.append(f"- `{row['profile_id']}`: {row['activation_state']} via {', '.join(list(row.get('blocker_codes') or []))}")
    lines.append("")
    lines.append("## By-Morning Success")
    lines.append("")
    for item in list(payload.get("by_morning_success") or []):
        lines.append(f"- {item}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = build_parser().parse_args()
    report_dir = Path(args.report_dir).resolve()
    report_dir.mkdir(parents=True, exist_ok=True)

    repo_update = read_json(Path(args.repo_update_handoff_json).resolve())
    session_handoff = read_json(Path(args.session_handoff_json).resolve())
    execution_handoff = read_json(Path(args.execution_handoff_json).resolve())
    profile_handoff = read_json(Path(args.profile_handoff_json).resolve())
    unlock_handoff = read_json(Path(args.unlock_handoff_json).resolve())
    workplan_handoff = read_json(Path(args.workplan_handoff_json).resolve())
    evidence_handoff = read_json(Path(args.evidence_handoff_json).resolve())
    overnight_plan_handoff = read_json(Path(args.overnight_plan_handoff_json).resolve())

    morning_decision_posture, posture_actions = derive_decision_posture(
        repo_update=repo_update,
        session_handoff=session_handoff,
        execution_handoff=execution_handoff,
        evidence_handoff=evidence_handoff,
    )

    payload = {
        "generated_at": datetime.now().isoformat(),
        "repo_update_handoff_json": str(Path(args.repo_update_handoff_json).resolve()),
        "session_handoff_json": str(Path(args.session_handoff_json).resolve()),
        "execution_handoff_json": str(Path(args.execution_handoff_json).resolve()),
        "profile_handoff_json": str(Path(args.profile_handoff_json).resolve()),
        "unlock_handoff_json": str(Path(args.unlock_handoff_json).resolve()),
        "workplan_handoff_json": str(Path(args.workplan_handoff_json).resolve()),
        "evidence_handoff_json": str(Path(args.evidence_handoff_json).resolve()),
        "overnight_plan_handoff_json": str(Path(args.overnight_plan_handoff_json).resolve()),
        "morning_decision_posture": morning_decision_posture,
        "repo_update_status": repo_update.get("overall_status"),
        "current_unlocked_profile": (
            overnight_plan_handoff.get("current_unlocked_profile")
            or unlock_handoff.get("current_resolved_profile")
            or profile_handoff.get("resolved_profile")
        ),
        "session_reconciliation_posture": (session_handoff.get("posture") or {}).get("overall_session_reconciliation_posture"),
        "execution_posture": (execution_handoff.get("posture") or {}).get("overall_execution_posture"),
        "execution_evidence_contract_status": evidence_handoff.get("contract_status"),
        "research_machine_mission": overnight_plan_handoff.get("research_machine_mission"),
        "new_machine_mission": overnight_plan_handoff.get("new_machine_mission"),
        "blocked_profiles_must_remain_blocked": list(overnight_plan_handoff.get("blocked_profiles_must_remain_blocked") or []),
        "required_next_session_artifacts": list(evidence_handoff.get("required_next_session_artifacts") or []),
        "nearest_unlock_targets": [
            {
                "profile_id": row.get("profile_id"),
                "activation_state": row.get("activation_state"),
                "blocker_codes": list(row.get("blocker_codes") or []),
            }
            for row in list(unlock_handoff.get("closest_next_unlock_targets") or [])
            if isinstance(row, dict)
        ][:3],
        "by_morning_success": list(overnight_plan_handoff.get("by_morning_success") or []),
        "operator_actions": unique_strings(
            posture_actions
            + build_operator_actions(
                repo_update=repo_update,
                session_handoff=session_handoff,
                execution_handoff=execution_handoff,
                unlock_handoff=unlock_handoff,
                workplan_handoff=workplan_handoff,
                evidence_handoff=evidence_handoff,
                overnight_plan_handoff=overnight_plan_handoff,
            )
        ),
    }

    json_path = report_dir / "morning_operator_brief.json"
    md_path = report_dir / "morning_operator_brief.md"
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    write_markdown(md_path, payload)
    print(json.dumps({"json_path": str(json_path), "markdown_path": str(md_path)}, indent=2))


if __name__ == "__main__":
    main()
