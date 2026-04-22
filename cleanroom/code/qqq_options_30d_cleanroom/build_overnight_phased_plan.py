from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[2]
DEFAULT_REPO_UPDATE_HANDOFF_JSON = REPO_ROOT / "docs" / "repo_updates" / "repo_update_handoff.json"
DEFAULT_TOURNAMENT_UNLOCK_HANDOFF_JSON = REPO_ROOT / "docs" / "tournament_unlocks" / "tournament_unlock_handoff.json"
DEFAULT_TOURNAMENT_UNLOCK_WORKPLAN_HANDOFF_JSON = (
    REPO_ROOT / "docs" / "tournament_unlocks" / "tournament_unlock_workplan_handoff.json"
)
DEFAULT_EXECUTION_EVIDENCE_CONTRACT_HANDOFF_JSON = (
    REPO_ROOT / "docs" / "execution_evidence" / "execution_evidence_contract_handoff.json"
)
DEFAULT_REPORT_DIR = REPO_ROOT / "docs" / "overnight_plan"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build a governed overnight phased plan from the current repo-update, unlock, workplan, and execution-evidence handoffs."
    )
    parser.add_argument("--repo-update-handoff-json", default=str(DEFAULT_REPO_UPDATE_HANDOFF_JSON))
    parser.add_argument("--unlock-handoff-json", default=str(DEFAULT_TOURNAMENT_UNLOCK_HANDOFF_JSON))
    parser.add_argument("--workplan-handoff-json", default=str(DEFAULT_TOURNAMENT_UNLOCK_WORKPLAN_HANDOFF_JSON))
    parser.add_argument("--execution-evidence-handoff-json", default=str(DEFAULT_EXECUTION_EVIDENCE_CONTRACT_HANDOFF_JSON))
    parser.add_argument("--report-dir", default=str(DEFAULT_REPORT_DIR))
    return parser


def read_json(path: Path) -> dict[str, Any]:
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


def build_phases(
    repo_update: dict[str, Any],
    unlock: dict[str, Any],
    workplan: dict[str, Any],
    evidence: dict[str, Any],
) -> list[dict[str, Any]]:
    current_profile = str(unlock.get("current_resolved_profile") or workplan.get("current_unlocked_profile") or "")
    research_mission = dict(workplan.get("research_plane_mission") or {})
    execution_mission = dict(workplan.get("execution_plane_mission") or {})
    available_fallbacks = list(unlock.get("available_but_not_preferred") or [])
    immediate_gaps = [dict(row) for row in list(evidence.get("immediate_gaps") or []) if isinstance(row, dict)]

    phases: list[dict[str, Any]] = []
    phases.append(
        {
            "phase_code": "phase_0_governance_preflight",
            "owner": "shared_control_plane",
            "title": "Confirm governed repo state before overnight work begins.",
            "objective": "Start only from current, branch-aligned repos and the currently unlocked tournament profile.",
            "success_criteria": [
                "repo_update_handoff overall status is `ready`",
                "safe_to_run_nightly_cycle = true",
                f"current unlocked profile remains `{current_profile}`",
            ],
            "actions": unique_strings(
                list(repo_update.get("overall_actions") or [])
                + [
                    f"Keep `{current_profile}` as the safe overnight default unless the refreshed unlock handoff changes it.",
                    "Do not activate any policy-blocked or implementation-blocked profile during preflight.",
                ]
            ),
            "gates": [
                "If repo update control is not ready, pause overnight execution until GitHub drift is cleared.",
            ],
        }
    )
    phases.append(
        {
            "phase_code": "phase_1_current_research_launch",
            "owner": "current_research_machine",
            "title": "Run the currently unlocked governed research profile.",
            "objective": "Use the safe unlocked profile to keep research moving while higher-risk profiles remain blocked by execution evidence.",
            "recommended_profile": current_profile,
            "fallback_profiles": available_fallbacks,
            "success_criteria": [
                f"`{current_profile}` launches through the governed nightly operator path",
                "discovery stays parallel and production decisions remain serialized",
                "the live manifest remains unchanged",
            ],
            "actions": [
                f"Launch `{current_profile}` through `launch_nightly_operator_cycle.ps1`.",
                "Keep promotion review-only and leave the live manifest untouched.",
                "Treat higher-tier blocked profiles as out of bounds for tonight even if they are strategically interesting.",
            ],
            "gates": [
                "If the unlock handoff changes the current resolved profile, stop and re-evaluate the overnight plan before launching research.",
            ],
        }
    )
    phases.append(
        {
            "phase_code": "phase_2_research_unlock_progress",
            "owner": research_mission.get("owner") or "current_research_machine",
            "title": str(research_mission.get("title") or "Advance the next research-plane unlock target."),
            "objective": str(
                research_mission.get("summary")
                or "Clear the next implementation blocker so the remaining unlock path is governed by evidence rather than missing tooling."
            ),
            "primary_target_profile": research_mission.get("primary_target_profile"),
            "success_criteria": list(research_mission.get("success_criteria") or []),
            "actions": list(research_mission.get("actions") or []),
            "gates": [
                "Do this through the governed control-plane path, not as an ad hoc side script.",
            ],
        }
    )
    phases.append(
        {
            "phase_code": "phase_3_execution_evidence_capture",
            "owner": execution_mission.get("owner") or "new_machine_execution_plane",
            "title": str(execution_mission.get("title") or "Produce the next trusted execution evidence package."),
            "objective": str(
                execution_mission.get("summary")
                or "Land trusted broker-audited paper-runner evidence that can safely influence research policy."
            ),
            "primary_target_profiles": list(execution_mission.get("primary_target_profiles") or []),
            "required_next_session_artifacts": list(evidence.get("required_next_session_artifacts") or []),
            "success_criteria": list(execution_mission.get("success_criteria") or []),
            "actions": unique_strings(
                list(execution_mission.get("actions") or [])
                + [
                    "Keep live strategy selection, risk policy, and the live manifest unchanged while producing evidence.",
                ]
            ),
            "gates": [
                "Only trusted or caution sessions with complete broker-audit evidence should be allowed to teach research policy.",
            ],
        }
    )
    phases.append(
        {
            "phase_code": "phase_4_post_session_assimilation",
            "owner": "new_machine_execution_plane",
            "title": "Refresh reconciliation, calibration, unlock, and evidence artifacts from the latest trusted session.",
            "objective": "Turn the next paper-runner session into governed control-plane learning instead of raw local exhaust.",
            "success_criteria": [
                "session reconciliation is rebuilt from the latest session bundle",
                "execution calibration is rebuilt from trusted session evidence only",
                "tournament unlock, workplan, and execution evidence artifacts are refreshed",
            ],
            "actions": [
                "Run `launch_post_session_assimilation.ps1` as the governed entrypoint for post-session control-plane refresh.",
                "Rebuild session reconciliation registry and handoff.",
                "Rebuild execution calibration registry and handoff.",
                "Rebuild tournament unlock registry, unlock handoff, unlock workplan, and execution evidence contract.",
                "Build the morning operator brief and handoff so tomorrow starts from one compact decision packet.",
                "Commit only distilled governance artifacts if they changed materially.",
            ],
            "gates": [
                "Do not commit raw session exhaust, raw order logs, or raw intraday trade activity.",
            ],
        }
    )
    phases.append(
        {
            "phase_code": "phase_5_morning_decision_packet",
            "owner": "human_reviewer_and_promotion_steward",
            "title": "Review the refreshed overnight state before any profile escalation or manifest mutation.",
            "objective": "Decide what changed overnight, what remains blocked, and whether the next tournament tier is any closer to being safely unlocked.",
            "success_criteria": [
                "morning operator can see the current unlocked profile, the next blocked targets, and the missing evidence package",
                "blocked profiles remain blocked unless the refreshed evidence genuinely clears their gates",
                "the live manifest stays review-gated",
            ],
            "actions": [
                "Inspect the refreshed overnight phased plan handoff.",
                "Inspect tournament unlock and execution evidence handoffs before choosing tomorrow's research profile.",
                "Keep blocked profiles blocked until their audit and evidence gates are actually cleared.",
            ],
            "gates": [
                "No auto-promotion into the live manifest.",
            ],
        }
    )

    if immediate_gaps:
        phases[3]["current_evidence_gaps"] = [
            {
                "check_id": row.get("check_id"),
                "summary": row.get("summary"),
            }
            for row in immediate_gaps
        ]

    return phases


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    lines: list[str] = []
    lines.append("# Overnight Phased Plan")
    lines.append("")
    lines.append("## Snapshot")
    lines.append("")
    lines.append(f"- Generated at: `{payload['generated_at']}`")
    lines.append(f"- Repo update status: `{payload['repo_update_status']}`")
    lines.append(f"- Current unlocked profile: `{payload['current_unlocked_profile']}`")
    lines.append(f"- Execution posture: `{payload['execution_posture']}`")
    lines.append(f"- Session trust posture: `{payload['session_reconciliation_posture']}`")
    lines.append(f"- Execution evidence contract: `{payload['execution_evidence_contract_status']}`")
    lines.append("")
    lines.append("## Hard Rules")
    lines.append("")
    for item in list(payload.get("hard_rules") or []):
        lines.append(f"- {item}")
    lines.append("")
    lines.append("## By-Morning Success")
    lines.append("")
    for item in list(payload.get("by_morning_success") or []):
        lines.append(f"- {item}")
    lines.append("")
    lines.append("## Phases")
    lines.append("")
    for phase in list(payload.get("phases") or []):
        lines.append(f"### {phase['title']}")
        lines.append("")
        lines.append(f"- Code: `{phase['phase_code']}`")
        lines.append(f"- Owner: `{phase['owner']}`")
        lines.append(f"- Objective: {phase['objective']}")
        if phase.get("recommended_profile"):
            lines.append(f"- Recommended profile: `{phase['recommended_profile']}`")
        if phase.get("primary_target_profile"):
            lines.append(f"- Primary target profile: `{phase['primary_target_profile']}`")
        if list(phase.get("primary_target_profiles") or []):
            lines.append(f"- Primary target profiles: `{', '.join(list(phase.get('primary_target_profiles') or []))}`")
        if list(phase.get("required_next_session_artifacts") or []):
            lines.append("- Required next session artifacts:")
            for item in list(phase.get("required_next_session_artifacts") or []):
                lines.append(f"  - {item}")
        if list(phase.get("actions") or []):
            lines.append("- Actions:")
            for item in list(phase.get("actions") or []):
                lines.append(f"  - {item}")
        if list(phase.get("success_criteria") or []):
            lines.append("- Success criteria:")
            for item in list(phase.get("success_criteria") or []):
                lines.append(f"  - {item}")
        if list(phase.get("gates") or []):
            lines.append("- Gates:")
            for item in list(phase.get("gates") or []):
                lines.append(f"  - {item}")
        if list(phase.get("current_evidence_gaps") or []):
            lines.append("- Current evidence gaps:")
            for row in list(phase.get("current_evidence_gaps") or []):
                lines.append(f"  - `{row['check_id']}`: {row['summary']}")
        lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    args = build_parser().parse_args()
    report_dir = Path(args.report_dir).resolve()
    report_dir.mkdir(parents=True, exist_ok=True)

    repo_update = read_json(Path(args.repo_update_handoff_json).resolve())
    unlock = read_json(Path(args.unlock_handoff_json).resolve())
    workplan = read_json(Path(args.workplan_handoff_json).resolve())
    evidence = read_json(Path(args.execution_evidence_handoff_json).resolve())

    current_profile = str(unlock.get("current_resolved_profile") or workplan.get("current_unlocked_profile") or "")
    phases = build_phases(repo_update, unlock, workplan, evidence)

    payload = {
        "generated_at": datetime.now().isoformat(),
        "repo_update_handoff_json": str(Path(args.repo_update_handoff_json).resolve()),
        "unlock_handoff_json": str(Path(args.unlock_handoff_json).resolve()),
        "workplan_handoff_json": str(Path(args.workplan_handoff_json).resolve()),
        "execution_evidence_handoff_json": str(Path(args.execution_evidence_handoff_json).resolve()),
        "repo_update_status": repo_update.get("overall_status"),
        "safe_to_run_nightly_cycle": bool(repo_update.get("safe_to_run_nightly_cycle")),
        "safe_to_run_execution_plane_without_update_review": bool(
            repo_update.get("safe_to_run_execution_plane_without_update_review")
        ),
        "current_unlocked_profile": current_profile,
        "execution_posture": unlock.get("execution_posture"),
        "session_reconciliation_posture": unlock.get("session_reconciliation_posture"),
        "trusted_learning_scope": unlock.get("trusted_learning_scope"),
        "execution_evidence_contract_status": evidence.get("contract_status"),
        "blocked_profiles_must_remain_blocked": [
            row.get("profile_id")
            for row in list(unlock.get("closest_next_unlock_targets") or [])
            if isinstance(row, dict)
        ],
        "hard_rules": [
            "Do not modify the live manifest during the overnight plan itself.",
            "Do not activate policy-blocked or implementation-blocked profiles just because they are strategically interesting.",
            "Do not let review-required or incomplete broker-audit sessions loosen research policy.",
            "Keep production decisions serialized and review-gated.",
        ],
        "by_morning_success": unique_strings(
            [
                f"`{current_profile}` completes or remains healthy as the governed overnight research run.",
                "A fresh paper-runner session lands with trusted broker-order and broker account-activity audit coverage.",
                "Session reconciliation, execution calibration, unlock, workplan, and execution evidence artifacts are refreshed from the latest evidence.",
                "The control plane can state clearly whether the next blocked profile is still blocked or has moved closer to being unlocked.",
            ]
        ),
        "phases": phases,
    }

    json_path = report_dir / "overnight_phased_plan.json"
    md_path = report_dir / "overnight_phased_plan.md"
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    write_markdown(md_path, payload)
    print(json.dumps({"json_path": str(json_path), "markdown_path": str(md_path)}, indent=2))


if __name__ == "__main__":
    main()
