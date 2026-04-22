from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[2]
DEFAULT_PROFILE_REGISTRY_JSON = REPO_ROOT / "docs" / "tournament_profiles" / "tournament_profile_registry.json"
DEFAULT_PROFILE_HANDOFF_JSON = REPO_ROOT / "docs" / "tournament_profiles" / "tournament_profile_handoff.json"
DEFAULT_EXECUTION_HANDOFF_JSON = REPO_ROOT / "docs" / "execution_calibration" / "execution_calibration_handoff.json"
DEFAULT_SESSION_HANDOFF_JSON = REPO_ROOT / "docs" / "session_reconciliation" / "session_reconciliation_handoff.json"
DEFAULT_REPORT_DIR = REPO_ROOT / "docs" / "tournament_unlocks"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build a machine-readable tournament unlock registry that explains what is currently unlocked and what evidence is still needed for higher-tier profiles."
    )
    parser.add_argument("--profile-registry-json", default=str(DEFAULT_PROFILE_REGISTRY_JSON))
    parser.add_argument("--profile-handoff-json", default=str(DEFAULT_PROFILE_HANDOFF_JSON))
    parser.add_argument("--execution-handoff-json", default=str(DEFAULT_EXECUTION_HANDOFF_JSON))
    parser.add_argument("--session-handoff-json", default=str(DEFAULT_SESSION_HANDOFF_JSON))
    parser.add_argument("--report-dir", default=str(DEFAULT_REPORT_DIR))
    parser.add_argument("--top-n", type=int, default=5)
    return parser


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def evidence_strength_rank(value: str) -> int:
    order = {
        "no_recent_trade_sessions": 0,
        "limited_entry_only": 1,
        "entry_only": 2,
        "limited_entry_and_reconciliation": 3,
        "entry_and_reconciliation": 4,
        "limited": 5,
        "broad": 6,
    }
    return order.get(value, 0)


def risk_tier_rank(value: str) -> int:
    return {"conservative": 0, "moderate": 1, "aggressive": 2}.get(value, 1)


def unique_dicts(rows: list[dict[str, Any]], key_name: str) -> list[dict[str, Any]]:
    seen: set[str] = set()
    unique_rows: list[dict[str, Any]] = []
    for row in rows:
        key = str(row.get(key_name) or "")
        if not key or key in seen:
            continue
        seen.add(key)
        unique_rows.append(row)
    return unique_rows


def _objective(
    code: str,
    summary: str,
    *,
    category: str,
    priority: int = 1,
) -> dict[str, Any]:
    return {
        "objective_code": code,
        "summary": summary,
        "category": category,
        "priority": priority,
    }


def _blocker(
    code: str,
    summary: str,
    *,
    category: str,
    current: str,
    required: str,
) -> dict[str, Any]:
    return {
        "blocker_code": code,
        "summary": summary,
        "category": category,
        "current": current,
        "required": required,
    }


def build_profile_unlock_row(
    profile: dict[str, Any],
    evaluation: dict[str, Any],
    execution_handoff: dict[str, Any],
    session_handoff: dict[str, Any],
    resolved_profile: str,
) -> dict[str, Any]:
    execution_posture = dict(execution_handoff.get("posture") or {})
    execution_policy = dict(execution_handoff.get("policy") or {})
    execution_flags = dict(execution_posture.get("flags") or {})
    session_posture = dict(session_handoff.get("posture") or {})
    session_policy = dict(session_handoff.get("policy") or {})

    general_evidence_strength = str(execution_posture.get("evidence_strength") or "no_recent_trade_sessions")
    unlock_evidence_strength = str(execution_posture.get("unlock_evidence_strength") or "no_recent_trade_sessions")
    trusted_unlock_session_count = int(execution_posture.get("trusted_unlock_session_count") or 0)
    current_max_risk_tier = str(execution_policy.get("max_execution_risk_tier") or "moderate")
    required_evidence_strength = str(profile.get("minimum_execution_evidence_strength") or "limited_entry_only")
    minimum_trusted_unlock_session_count = int(profile.get("minimum_trusted_unlock_session_count", 0) or 0)
    current_evidence_strength = (
        unlock_evidence_strength
        if bool(profile.get("requires_broker_order_audit_coverage")) or bool(profile.get("requires_broker_activity_audit_coverage"))
        else general_evidence_strength
    )

    blockers: list[dict[str, Any]] = []
    objectives: list[dict[str, Any]] = []

    if not bool(profile.get("executable_now")):
        blockers.append(
            _blocker(
                "implementation_not_wired",
                "Profile is tracked in governance but does not yet have a governed executable entrypoint.",
                category="implementation",
                current=str(profile.get("status") or "planned"),
                required="executable_now",
            )
        )
        objectives.append(
            _objective(
                "wire_profile_entrypoint",
                "Wire this profile into an executable governed entrypoint and launch path before trying to activate it.",
                category="implementation",
            )
        )

    if evidence_strength_rank(current_evidence_strength) < evidence_strength_rank(required_evidence_strength):
        blockers.append(
            _blocker(
                "execution_evidence_floor",
                f"Current execution evidence `{current_evidence_strength}` is below this profile's floor `{required_evidence_strength}`.",
                category="evidence",
                current=current_evidence_strength,
                required=required_evidence_strength,
            )
        )
        objectives.append(
            _objective(
                f"upgrade_execution_evidence_to_{required_evidence_strength}",
                f"Upgrade execution evidence from `{current_evidence_strength}` to at least `{required_evidence_strength}` through fresh trusted paper sessions and reconciliation artifacts.",
                category="evidence",
            )
        )

    if trusted_unlock_session_count < minimum_trusted_unlock_session_count:
        blockers.append(
            _blocker(
                "unlock_session_count_floor",
                f"Current trusted unlock-grade session count `{trusted_unlock_session_count}` is below this profile's floor `{minimum_trusted_unlock_session_count}`.",
                category="evidence",
                current=str(trusted_unlock_session_count),
                required=str(minimum_trusted_unlock_session_count),
            )
        )
        objectives.append(
            _objective(
                f"land_{minimum_trusted_unlock_session_count}_trusted_unlock_sessions",
                f"Land at least `{minimum_trusted_unlock_session_count}` fresh trusted unlock-grade session(s) before activating this profile.",
                category="evidence",
            )
        )

    if risk_tier_rank(str(profile.get("execution_risk_tier") or "moderate")) > risk_tier_rank(current_max_risk_tier):
        target_risk_tier = str(profile.get("execution_risk_tier") or "moderate")
        blockers.append(
            _blocker(
                "risk_tier_cap",
                f"Current execution policy only permits profiles up to `{current_max_risk_tier}` risk, below this profile's `{target_risk_tier}` tier.",
                category="policy",
                current=current_max_risk_tier,
                required=target_risk_tier,
            )
        )
        objectives.append(
            _objective(
                f"raise_execution_risk_ceiling_to_{target_risk_tier}",
                f"Improve execution posture and trusted evidence enough to raise the activation ceiling from `{current_max_risk_tier}` to `{target_risk_tier}`.",
                category="policy",
            )
        )

    if bool(profile.get("requires_broker_order_audit_coverage")) and not bool(
        execution_policy.get("broker_audited_profile_activation_permitted")
    ):
        blockers.append(
            _blocker(
                "broker_order_audit_coverage",
                "Profile requires broker-order audit coverage in trusted learning sessions before activation.",
                category="audit",
                current=str(bool(execution_flags.get("broker_order_audit_gap"))).lower(),
                required="broker_order_audit_coverage_available",
            )
        )
        objectives.append(
            _objective(
                "land_trusted_broker_order_audit_sessions",
                "Land fresh trusted paper sessions with broker-order audit coverage so broker-audited profiles can activate.",
                category="audit",
            )
        )

    if bool(profile.get("requires_broker_activity_audit_coverage")) and not bool(
        execution_policy.get("broker_audited_profile_activation_permitted")
    ):
        blockers.append(
            _blocker(
                "broker_activity_audit_coverage",
                "Profile requires broker account-activity audit coverage in trusted learning sessions before activation.",
                category="audit",
                current=str(bool(execution_flags.get("broker_activity_audit_gap"))).lower(),
                required="broker_activity_audit_coverage_available",
            )
        )
        objectives.append(
            _objective(
                "land_trusted_broker_activity_audit_sessions",
                "Land fresh trusted paper sessions with broker account-activity audit coverage so broker-audited profiles can activate.",
                category="audit",
            )
        )

    if bool(profile.get("requires_exit_telemetry")) and bool(execution_flags.get("exit_telemetry_gap")):
        blockers.append(
            _blocker(
                "exit_telemetry",
                "Profile requires reliable exit telemetry, but the current execution posture still flags an exit-telemetry gap.",
                category="telemetry",
                current="gap_present",
                required="reliable_exit_telemetry",
            )
        )
        objectives.append(
            _objective(
                "land_reliable_exit_telemetry",
                "Capture reliable exit telemetry from fresh broker-audited paper sessions before activating exit-sensitive profiles.",
                category="telemetry",
            )
        )

    blockers = unique_dicts(blockers, "blocker_code")
    objectives = unique_dicts(objectives, "objective_code")

    if blockers:
        blocker_codes = {str(row["blocker_code"]) for row in blockers}
        if blocker_codes == {"implementation_not_wired"}:
            activation_state = "implementation_blocked"
        elif "implementation_not_wired" in blocker_codes:
            activation_state = "implementation_and_policy_blocked"
        else:
            activation_state = "policy_blocked"
    elif str(profile["profile_id"]) == resolved_profile:
        activation_state = "unlocked_preferred"
    else:
        activation_state = "unlocked_available"

    recommended_profiles = set(execution_policy.get("recommended_profiles") or [])
    if str(profile["profile_id"]) == resolved_profile:
        recommendation_level = "preferred"
    elif str(profile["profile_id"]) in recommended_profiles:
        recommendation_level = "recommended_but_not_yet_unlocked"
    elif activation_state.startswith("unlocked"):
        recommendation_level = "available"
    else:
        recommendation_level = "blocked"

    return {
        "profile_id": profile["profile_id"],
        "status": profile.get("status"),
        "executable_now": bool(profile.get("executable_now")),
        "activation_state": activation_state,
        "recommendation_level": recommendation_level,
        "resolved_now": str(profile["profile_id"]) == resolved_profile,
        "current_score": int(evaluation.get("score", 0) or 0),
        "unmet_requirement_count": len(blockers),
        "blocker_codes": [row["blocker_code"] for row in blockers],
        "blockers": blockers,
        "next_unlock_objectives": objectives,
        "session_focus": profile.get("session_focus"),
        "execution_window": profile.get("execution_window"),
        "execution_risk_tier": profile.get("execution_risk_tier"),
        "minimum_execution_evidence_strength": required_evidence_strength,
        "minimum_trusted_unlock_session_count": minimum_trusted_unlock_session_count,
        "current_trusted_unlock_session_count": trusted_unlock_session_count,
        "preferred_machine_now": profile.get("preferred_machine_now"),
        "preferred_machine_target": profile.get("preferred_machine_target"),
        "trusted_learning_scope": session_policy.get("trusted_learning_scope"),
        "session_reconciliation_posture": session_posture.get("overall_session_reconciliation_posture"),
        "families": list(profile.get("families") or []),
        "evaluation_reasons": list(evaluation.get("reasons") or []),
    }


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    summary = dict(payload.get("summary") or {})
    lines: list[str] = []
    lines.append("# Tournament Unlock Registry")
    lines.append("")
    lines.append("## Snapshot")
    lines.append("")
    lines.append(f"- Generated at: `{payload['generated_at']}`")
    lines.append(f"- Current resolved profile: `{summary.get('current_resolved_profile')}`")
    lines.append(f"- Execution posture: `{summary.get('execution_posture')}`")
    lines.append(f"- Session reconciliation posture: `{summary.get('session_reconciliation_posture')}`")
    lines.append(f"- Trusted learning scope: `{summary.get('trusted_learning_scope')}`")
    lines.append(f"- Unlocked preferred profiles: `{', '.join(summary.get('unlocked_preferred_profiles') or []) or 'none'}`")
    lines.append(f"- Unlocked available profiles: `{', '.join(summary.get('unlocked_available_profiles') or []) or 'none'}`")
    lines.append(f"- Blocked profiles: `{summary.get('blocked_profile_count')}`")
    lines.append("")
    lines.append("## Immediate Unlock Objectives")
    lines.append("")
    for row in list(summary.get("immediate_unlock_objectives") or []):
        lines.append(
            f"- `{row['objective_code']}`: {row['summary']} Affects `{row['affected_profile_count']}` profiles."
        )
    if not list(summary.get("immediate_unlock_objectives") or []):
        lines.append("- none")
    lines.append("")
    lines.append("## Closest Next Unlock Targets")
    lines.append("")
    for row in list(summary.get("next_unlock_targets") or []):
        blockers = ", ".join(list(row.get("blocker_codes") or [])) or "none"
        objectives = ", ".join([item["objective_code"] for item in list(row.get("next_unlock_objectives") or [])]) or "none"
        lines.append(
            f"- `{row['profile_id']}`: state `{row['activation_state']}`, unmet `{row['unmet_requirement_count']}`, blockers `{blockers}`, next objectives `{objectives}`"
        )
    if not list(summary.get("next_unlock_targets") or []):
        lines.append("- none")
    lines.append("")
    lines.append("## Profile Detail")
    lines.append("")
    for row in list(payload.get("profiles") or []):
        lines.append(f"### {row['profile_id']}")
        lines.append("")
        lines.append(f"- State: `{row['activation_state']}`")
        lines.append(f"- Recommendation level: `{row['recommendation_level']}`")
        lines.append(f"- Executable now: `{str(bool(row['executable_now'])).lower()}`")
        lines.append(f"- Unmet requirements: `{row['unmet_requirement_count']}`")
        lines.append(f"- Session focus: `{row['session_focus']}`")
        lines.append(f"- Risk tier: `{row['execution_risk_tier']}`")
        lines.append(f"- Minimum evidence strength: `{row['minimum_execution_evidence_strength']}`")
        lines.append(
            f"- Trusted unlock sessions: current `{row['current_trusted_unlock_session_count']}`, required `{row['minimum_trusted_unlock_session_count']}`"
        )
        lines.append(f"- Preferred machine now: `{row['preferred_machine_now']}`")
        lines.append(f"- Preferred machine target: `{row['preferred_machine_target']}`")
        blocker_text = ", ".join(list(row.get("blocker_codes") or [])) or "none"
        lines.append(f"- Blockers: `{blocker_text}`")
        objective_text = ", ".join([item["objective_code"] for item in list(row.get("next_unlock_objectives") or [])]) or "none"
        lines.append(f"- Next unlock objectives: `{objective_text}`")
        lines.append("")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fieldnames = [
        "profile_id",
        "status",
        "executable_now",
        "activation_state",
        "recommendation_level",
        "current_score",
        "unmet_requirement_count",
        "blocker_codes",
        "next_unlock_objectives",
        "session_focus",
        "execution_window",
        "execution_risk_tier",
        "minimum_execution_evidence_strength",
        "preferred_machine_now",
        "preferred_machine_target",
        "trusted_learning_scope",
        "session_reconciliation_posture",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    **{key: row.get(key) for key in fieldnames},
                    "blocker_codes": ",".join(list(row.get("blocker_codes") or [])),
                    "next_unlock_objectives": ",".join(
                        [item["objective_code"] for item in list(row.get("next_unlock_objectives") or [])]
                    ),
                }
            )


def main() -> None:
    args = build_parser().parse_args()
    report_dir = Path(args.report_dir).resolve()
    report_dir.mkdir(parents=True, exist_ok=True)

    profile_registry_path = Path(args.profile_registry_json).resolve()
    profile_handoff_path = Path(args.profile_handoff_json).resolve()
    execution_handoff_path = Path(args.execution_handoff_json).resolve()
    session_handoff_path = Path(args.session_handoff_json).resolve()

    profile_registry = read_json(profile_registry_path)
    profile_handoff = read_json(profile_handoff_path)
    execution_handoff = read_json(execution_handoff_path)
    session_handoff = read_json(session_handoff_path)

    profile_map = {str(row["profile_id"]): dict(row) for row in list(profile_registry.get("profiles") or [])}
    evaluation_map = {
        str(row["profile_id"]): dict(row) for row in list(profile_handoff.get("profile_evaluations") or []) if isinstance(row, dict)
    }

    resolved_profile = str(profile_handoff.get("resolved_profile") or "")
    rows = [
        build_profile_unlock_row(
            profile_map[profile_id],
            evaluation_map.get(profile_id, {}),
            execution_handoff,
            session_handoff,
            resolved_profile,
        )
        for profile_id in sorted(profile_map)
    ]

    rows.sort(
        key=lambda row: (
            {
                "unlocked_preferred": 0,
                "unlocked_available": 1,
                "implementation_blocked": 2,
                "implementation_and_policy_blocked": 3,
                "policy_blocked": 4,
            }.get(str(row.get("activation_state")), 9),
            int(row.get("unmet_requirement_count", 0)),
            -int(row.get("current_score", 0)),
            str(row.get("profile_id")),
        )
    )

    blocked_rows = [row for row in rows if not str(row.get("activation_state", "")).startswith("unlocked")]
    next_unlock_targets = sorted(
        blocked_rows,
        key=lambda row: (
            int(row.get("unmet_requirement_count", 0)),
            -int(row.get("current_score", 0)),
            str(row.get("profile_id")),
        ),
    )[: int(args.top_n)]

    objective_counter: Counter[str] = Counter()
    objective_meta: dict[str, dict[str, Any]] = {}
    objective_order: dict[str, int] = {}
    order_index = 0
    for row in next_unlock_targets:
        for objective in list(row.get("next_unlock_objectives") or []):
            code = str(objective.get("objective_code") or "")
            if not code:
                continue
            objective_counter[code] += 1
            objective_meta.setdefault(code, dict(objective))
            if code not in objective_order:
                objective_order[code] = order_index
                order_index += 1

    immediate_unlock_objectives = []
    for code in sorted(objective_order, key=lambda item: objective_order[item]):
        meta = dict(objective_meta.get(code) or {})
        meta["affected_profile_count"] = objective_counter[code]
        immediate_unlock_objectives.append(meta)

    payload = {
        "generated_at": datetime.now().isoformat(),
        "profile_registry_json": str(profile_registry_path),
        "profile_handoff_json": str(profile_handoff_path),
        "execution_handoff_json": str(execution_handoff_path),
        "session_handoff_json": str(session_handoff_path),
        "summary": {
            "current_resolved_profile": resolved_profile,
            "execution_posture": ((execution_handoff.get("posture") or {}).get("overall_execution_posture")),
            "execution_evidence_strength": ((execution_handoff.get("posture") or {}).get("evidence_strength")),
            "session_reconciliation_posture": (
                (session_handoff.get("posture") or {}).get("overall_session_reconciliation_posture")
            ),
            "trusted_learning_scope": ((session_handoff.get("policy") or {}).get("trusted_learning_scope")),
            "unlocked_preferred_profiles": [
                row["profile_id"] for row in rows if str(row.get("activation_state")) == "unlocked_preferred"
            ],
            "unlocked_available_profiles": [
                row["profile_id"] for row in rows if str(row.get("activation_state")) == "unlocked_available"
            ],
            "blocked_profile_count": len(blocked_rows),
            "immediate_unlock_objectives": immediate_unlock_objectives,
            "next_unlock_targets": next_unlock_targets,
        },
        "profiles": rows,
    }

    json_path = report_dir / "tournament_unlock_registry.json"
    md_path = report_dir / "tournament_unlock_registry.md"
    csv_path = report_dir / "tournament_unlock_registry.csv"
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    write_markdown(md_path, payload)
    write_csv(csv_path, rows)
    print(
        json.dumps(
            {
                "json_path": str(json_path),
                "markdown_path": str(md_path),
                "csv_path": str(csv_path),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
