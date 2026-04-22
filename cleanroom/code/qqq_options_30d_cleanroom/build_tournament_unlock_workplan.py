from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[2]
DEFAULT_UNLOCK_REGISTRY_JSON = REPO_ROOT / "docs" / "tournament_unlocks" / "tournament_unlock_registry.json"
DEFAULT_UNLOCK_HANDOFF_JSON = REPO_ROOT / "docs" / "tournament_unlocks" / "tournament_unlock_handoff.json"
DEFAULT_REPORT_DIR = REPO_ROOT / "docs" / "tournament_unlocks"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build a two-machine unlock workplan so the research plane and execution plane know the highest-value next steps for unlocking the next tournament tier."
    )
    parser.add_argument("--unlock-registry-json", default=str(DEFAULT_UNLOCK_REGISTRY_JSON))
    parser.add_argument("--unlock-handoff-json", default=str(DEFAULT_UNLOCK_HANDOFF_JSON))
    parser.add_argument("--report-dir", default=str(DEFAULT_REPORT_DIR))
    parser.add_argument("--top-n", type=int, default=3)
    return parser


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _priority(row: dict[str, Any]) -> tuple[int, int, int, str]:
    recommendation_rank = {
        "recommended_but_not_yet_unlocked": 0,
        "blocked": 1,
        "available": 2,
        "preferred": 3,
    }.get(str(row.get("recommendation_level") or "blocked"), 9)
    return (
        recommendation_rank,
        int(row.get("unmet_requirement_count", 0)),
        -int(row.get("current_score", 0)),
        str(row.get("profile_id") or ""),
    )


def build_research_plane_mission(rows: list[dict[str, Any]]) -> dict[str, Any]:
    implementation_candidates = [
        row for row in rows if "implementation_not_wired" in set(row.get("blocker_codes") or [])
    ]
    implementation_candidates.sort(key=_priority)
    if not implementation_candidates:
        return {
            "owner": "current_research_machine",
            "mission_code": "maintain_current_governed_profiles",
            "title": "No research-plane unlock wiring is immediately required.",
            "primary_target_profile": "",
            "summary": "The current unlock surface is blocked more by execution evidence than by missing governed entrypoints.",
            "actions": [],
            "success_criteria": [],
        }

    target = implementation_candidates[0]
    return {
        "owner": "current_research_machine",
        "mission_code": "wire_next_unlock_profile",
        "title": f"Wire governed execution for `{target['profile_id']}`.",
        "primary_target_profile": target["profile_id"],
        "summary": f"Clear the implementation blocker on `{target['profile_id']}` so the remaining unlock path is governed only by execution evidence and session trust.",
        "actions": [
            f"Add a governed executable entrypoint for `{target['profile_id']}` instead of leaving it tracked-only in policy.",
            "Make sure the new path participates in the same nightly-operator control plane, lineage, validation, and morning-handoff chain.",
            "Refresh the tournament profile registry, tournament profile handoff, tournament unlock registry, and tournament unlock handoff after wiring is complete.",
        ],
        "success_criteria": [
            f"`{target['profile_id']}` no longer carries `implementation_not_wired` in the unlock registry.",
            f"`{target['profile_id']}` is executable in code, even if execution evidence still blocks activation.",
            "The governed operator artifacts regenerate cleanly after the new profile wiring.",
        ],
    }


def build_execution_plane_mission(rows: list[dict[str, Any]], handoff: dict[str, Any]) -> dict[str, Any]:
    blocked_rows = [row for row in rows if not str(row.get("activation_state", "")).startswith("unlocked")]
    primary_targets = sorted(blocked_rows, key=_priority)[:2]
    target_profiles = [row["profile_id"] for row in primary_targets]

    audit_gap = any(
        blocker in {"broker_order_audit_coverage", "broker_activity_audit_coverage"}
        for row in primary_targets
        for blocker in list(row.get("blocker_codes") or [])
    )
    evidence_gap = any("execution_evidence_floor" in set(row.get("blocker_codes") or []) for row in primary_targets)
    exit_gap = any("exit_telemetry" in set(row.get("blocker_codes") or []) for row in primary_targets)

    actions = [
        "Run the current unlocked profile without changing live strategy selection, risk policy, or the live manifest.",
        "Ensure the session bundle captures broker-order audit, broker account-activity audit, and ending broker-position snapshot artifacts.",
        "Immediately rerun session reconciliation, execution calibration, tournament unlock registry, and tournament unlock handoff after the next trusted session lands.",
    ]
    if audit_gap:
        actions.append("Treat trusted broker-order and broker-activity audit coverage as the primary missing evidence package.")
    if evidence_gap:
        actions.append("Aim to improve execution evidence beyond `limited_entry_only` by landing a trusted, fully reconciled paper session.")
    if exit_gap:
        actions.append("Prefer a session that produces clean exit telemetry, because aggressive opening-window profiles still need that evidence tier.")

    success_criteria = [
        "At least one fresh trusted paper session lands with broker-order audit coverage.",
        "At least one fresh trusted paper session lands with broker account-activity audit coverage.",
        "The refreshed session reconciliation handoff remains `trusted_and_cautious_sessions` or better without flipping the new session to `review_required`.",
        "The refreshed execution calibration handoff improves the evidence floor or removes audit-gap blockers for the nearest unlock target.",
    ]
    if exit_gap:
        success_criteria.append("A fresh session contributes usable exit telemetry for future aggressive-profile consideration.")

    return {
        "owner": "new_machine_execution_plane",
        "mission_code": "produce_next_unlock_evidence_package",
        "title": "Produce the next trusted broker-audited execution evidence package.",
        "primary_target_profiles": target_profiles,
        "summary": "The execution plane should focus on landing fresh trusted paper-runner evidence that removes the current audit and evidence-floor blockers from the nearest unlock targets.",
        "actions": actions,
        "success_criteria": success_criteria,
        "current_unlocked_profile": handoff.get("current_resolved_profile"),
        "available_but_not_preferred": list(handoff.get("available_but_not_preferred") or []),
    }


def build_completion_gates(rows: list[dict[str, Any]], top_n: int) -> list[dict[str, Any]]:
    blocked_rows = [row for row in rows if not str(row.get("activation_state", "")).startswith("unlocked")]
    blocked_rows.sort(key=_priority)
    gates: list[dict[str, Any]] = []
    for row in blocked_rows[:top_n]:
        gates.append(
            {
                "profile_id": row["profile_id"],
                "activation_state": row["activation_state"],
                "required_clearances": list(row.get("blocker_codes") or []),
                "next_unlock_objectives": [item["objective_code"] for item in list(row.get("next_unlock_objectives") or [])],
            }
        )
    return gates


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    research = dict(payload.get("research_plane_mission") or {})
    execution = dict(payload.get("execution_plane_mission") or {})
    lines: list[str] = []
    lines.append("# Tournament Unlock Workplan")
    lines.append("")
    lines.append("## Snapshot")
    lines.append("")
    lines.append(f"- Generated at: `{payload['generated_at']}`")
    lines.append(f"- Current unlocked profile: `{payload['current_unlocked_profile']}`")
    lines.append(f"- Available but not preferred: `{', '.join(payload.get('available_but_not_preferred') or []) or 'none'}`")
    lines.append("")
    lines.append("## Research Plane Mission")
    lines.append("")
    lines.append(f"- Owner: `{research.get('owner')}`")
    lines.append(f"- Title: {research.get('title')}")
    lines.append(f"- Primary target profile: `{research.get('primary_target_profile') or 'none'}`")
    for item in list(research.get("actions") or []):
        lines.append(f"- Action: {item}")
    for item in list(research.get("success_criteria") or []):
        lines.append(f"- Success: {item}")
    lines.append("")
    lines.append("## Execution Plane Mission")
    lines.append("")
    lines.append(f"- Owner: `{execution.get('owner')}`")
    lines.append(f"- Title: {execution.get('title')}")
    lines.append(f"- Primary target profiles: `{', '.join(execution.get('primary_target_profiles') or []) or 'none'}`")
    for item in list(execution.get("actions") or []):
        lines.append(f"- Action: {item}")
    for item in list(execution.get("success_criteria") or []):
        lines.append(f"- Success: {item}")
    lines.append("")
    lines.append("## Completion Gates")
    lines.append("")
    for row in list(payload.get("completion_gates") or []):
        lines.append(
            f"- `{row['profile_id']}`: clear `{', '.join(row.get('required_clearances') or [])}` via `{', '.join(row.get('next_unlock_objectives') or [])}`"
        )
    if not list(payload.get("completion_gates") or []):
        lines.append("- none")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = build_parser().parse_args()
    report_dir = Path(args.report_dir).resolve()
    report_dir.mkdir(parents=True, exist_ok=True)

    unlock_registry = read_json(Path(args.unlock_registry_json).resolve())
    unlock_handoff = read_json(Path(args.unlock_handoff_json).resolve())
    rows = [dict(row) for row in list(unlock_registry.get("profiles") or []) if isinstance(row, dict)]

    payload = {
        "generated_at": datetime.now().isoformat(),
        "unlock_registry_json": str(Path(args.unlock_registry_json).resolve()),
        "unlock_handoff_json": str(Path(args.unlock_handoff_json).resolve()),
        "current_unlocked_profile": unlock_handoff.get("current_resolved_profile"),
        "available_but_not_preferred": list(unlock_handoff.get("available_but_not_preferred") or []),
        "research_plane_mission": build_research_plane_mission(rows),
        "execution_plane_mission": build_execution_plane_mission(rows, unlock_handoff),
        "completion_gates": build_completion_gates(rows, int(args.top_n)),
    }

    json_path = report_dir / "tournament_unlock_workplan.json"
    md_path = report_dir / "tournament_unlock_workplan.md"
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    write_markdown(md_path, payload)
    print(json.dumps({"json_path": str(json_path), "markdown_path": str(md_path)}, indent=2))


if __name__ == "__main__":
    main()
