from __future__ import annotations

import argparse
import json
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[2]
DEFAULT_BRIEF_JSON = REPO_ROOT / "docs" / "morning_brief" / "morning_operator_brief.json"
DEFAULT_REPORT_DIR = REPO_ROOT / "docs" / "morning_brief"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build a concise handoff from the morning operator brief."
    )
    parser.add_argument("--brief-json", default=str(DEFAULT_BRIEF_JSON))
    parser.add_argument("--report-dir", default=str(DEFAULT_REPORT_DIR))
    return parser


def write_markdown(path: Path, payload: dict) -> None:
    lines: list[str] = []
    lines.append("# Morning Operator Brief Handoff")
    lines.append("")
    lines.append("## Snapshot")
    lines.append("")
    lines.append(f"- Morning decision posture: `{payload['morning_decision_posture']}`")
    lines.append(f"- Current unlocked profile: `{payload['current_unlocked_profile']}`")
    lines.append(f"- Repo update status: `{payload['repo_update_status']}`")
    lines.append(f"- Session reconciliation posture: `{payload['session_reconciliation_posture']}`")
    lines.append(f"- Execution posture: `{payload['execution_posture']}`")
    lines.append(f"- Execution evidence contract: `{payload['execution_evidence_contract_status']}`")
    lines.append(f"- General evidence strength: `{payload['execution_evidence_strength']}`")
    lines.append(f"- Unlock evidence strength: `{payload['unlock_execution_evidence_strength']}`")
    lines.append("")
    lines.append("## Immediate Actions")
    lines.append("")
    for row in list(payload.get("operator_actions") or []):
        lines.append(f"- {row}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = build_parser().parse_args()
    brief_path = Path(args.brief_json).resolve()
    report_dir = Path(args.report_dir).resolve()
    report_dir.mkdir(parents=True, exist_ok=True)

    brief = json.loads(brief_path.read_text(encoding="utf-8"))
    payload = {
        "generated_at": brief.get("generated_at"),
        "brief_json": str(brief_path),
        "morning_decision_posture": brief.get("morning_decision_posture"),
        "current_unlocked_profile": brief.get("current_unlocked_profile"),
        "repo_update_status": brief.get("repo_update_status"),
        "session_reconciliation_posture": brief.get("session_reconciliation_posture"),
        "execution_posture": brief.get("execution_posture"),
        "execution_evidence_contract_status": brief.get("execution_evidence_contract_status"),
        "execution_evidence_strength": brief.get("execution_evidence_strength"),
        "unlock_execution_evidence_strength": brief.get("unlock_execution_evidence_strength"),
        "blocked_profiles_must_remain_blocked": list(brief.get("blocked_profiles_must_remain_blocked") or []),
        "required_next_session_artifacts": list(brief.get("required_next_session_artifacts") or []),
        "operator_actions": list(brief.get("operator_actions") or [])[:8],
        "nearest_unlock_targets": list(brief.get("nearest_unlock_targets") or [])[:3],
    }

    json_path = report_dir / "morning_operator_brief_handoff.json"
    md_path = report_dir / "morning_operator_brief_handoff.md"
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    write_markdown(md_path, payload)
    print(json.dumps({"json_path": str(json_path), "markdown_path": str(md_path)}, indent=2))


if __name__ == "__main__":
    main()
