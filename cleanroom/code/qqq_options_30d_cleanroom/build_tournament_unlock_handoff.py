from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[2]
DEFAULT_REGISTRY_JSON = REPO_ROOT / "docs" / "tournament_unlocks" / "tournament_unlock_registry.json"
DEFAULT_REPORT_DIR = REPO_ROOT / "docs" / "tournament_unlocks"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build a concise steward handoff from the tournament unlock registry."
    )
    parser.add_argument("--registry-json", default=str(DEFAULT_REGISTRY_JSON))
    parser.add_argument("--report-dir", default=str(DEFAULT_REPORT_DIR))
    parser.add_argument("--top-n", type=int, default=4)
    return parser


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    lines: list[str] = []
    lines.append("# Tournament Unlock Handoff")
    lines.append("")
    lines.append("## Snapshot")
    lines.append("")
    lines.append(f"- Generated at: `{payload['generated_at']}`")
    lines.append(f"- Current resolved profile: `{payload['current_resolved_profile']}`")
    lines.append(f"- Execution posture: `{payload['execution_posture']}`")
    lines.append(f"- Session reconciliation posture: `{payload['session_reconciliation_posture']}`")
    lines.append(f"- Trusted learning scope: `{payload['trusted_learning_scope']}`")
    lines.append(f"- Unlocked now: `{', '.join(payload['unlocked_now']) or 'none'}`")
    lines.append(f"- Available but not preferred: `{', '.join(payload['available_but_not_preferred']) or 'none'}`")
    lines.append("")
    lines.append("## Closest Next Unlock Targets")
    lines.append("")
    for row in list(payload.get("closest_next_unlock_targets") or []):
        blockers = ", ".join(list(row.get("blocker_codes") or [])) or "none"
        objectives = ", ".join([item["objective_code"] for item in list(row.get("next_unlock_objectives") or [])]) or "none"
        lines.append(
            f"- `{row['profile_id']}`: state `{row['activation_state']}`, blockers `{blockers}`, next objectives `{objectives}`"
        )
    if not list(payload.get("closest_next_unlock_targets") or []):
        lines.append("- none")
    lines.append("")
    lines.append("## Immediate Unlock Objectives")
    lines.append("")
    for row in list(payload.get("immediate_unlock_objectives") or []):
        lines.append(f"- `{row['objective_code']}`: {row['summary']} Affects `{row['affected_profile_count']}` profiles.")
    if not list(payload.get("immediate_unlock_objectives") or []):
        lines.append("- none")
    lines.append("")
    lines.append("## Operator Actions")
    lines.append("")
    for row in list(payload.get("operator_actions") or []):
        lines.append(f"- {row}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = build_parser().parse_args()
    registry_path = Path(args.registry_json).resolve()
    report_dir = Path(args.report_dir).resolve()
    report_dir.mkdir(parents=True, exist_ok=True)

    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    summary = dict(registry.get("summary") or {})
    rows = [dict(row) for row in list(registry.get("profiles") or []) if isinstance(row, dict)]

    unlocked_now = [row["profile_id"] for row in rows if str(row.get("activation_state")) == "unlocked_preferred"]
    available_but_not_preferred = [
        row["profile_id"] for row in rows if str(row.get("activation_state")) == "unlocked_available"
    ]
    blocked_rows = [row for row in rows if not str(row.get("activation_state", "")).startswith("unlocked")]
    closest_next_unlock_targets = sorted(
        blocked_rows,
        key=lambda row: (
            int(row.get("unmet_requirement_count", 0)),
            -int(row.get("current_score", 0)),
            str(row.get("profile_id")),
        ),
    )[: int(args.top_n)]

    operator_actions = [
        f"Run `{summary.get('current_resolved_profile')}` while higher-tier profiles remain blocked by execution evidence or implementation gates.",
    ]
    if available_but_not_preferred:
        operator_actions.append(
            f"Keep `{', '.join(available_but_not_preferred)}` as fallback executable profiles, not the default nightly choice."
        )
    for row in list(summary.get("immediate_unlock_objectives") or [])[: int(args.top_n)]:
        operator_actions.append(row["summary"])

    handoff = {
        "generated_at": registry.get("generated_at"),
        "registry_json": str(registry_path),
        "current_resolved_profile": summary.get("current_resolved_profile"),
        "execution_posture": summary.get("execution_posture"),
        "execution_evidence_strength": summary.get("execution_evidence_strength"),
        "session_reconciliation_posture": summary.get("session_reconciliation_posture"),
        "trusted_learning_scope": summary.get("trusted_learning_scope"),
        "unlocked_now": unlocked_now,
        "available_but_not_preferred": available_but_not_preferred,
        "closest_next_unlock_targets": closest_next_unlock_targets,
        "immediate_unlock_objectives": list(summary.get("immediate_unlock_objectives") or [])[: int(args.top_n)],
        "operator_actions": operator_actions,
    }

    json_path = report_dir / "tournament_unlock_handoff.json"
    md_path = report_dir / "tournament_unlock_handoff.md"
    json_path.write_text(json.dumps(handoff, indent=2), encoding="utf-8")
    write_markdown(md_path, handoff)
    print(json.dumps({"json_path": str(json_path), "markdown_path": str(md_path)}, indent=2))


if __name__ == "__main__":
    main()
