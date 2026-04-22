from __future__ import annotations

import argparse
import json
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[2]
DEFAULT_PLAN_JSON = REPO_ROOT / "docs" / "overnight_plan" / "overnight_phased_plan.json"
DEFAULT_REPORT_DIR = REPO_ROOT / "docs" / "overnight_plan"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build a concise handoff from the governed overnight phased plan."
    )
    parser.add_argument("--plan-json", default=str(DEFAULT_PLAN_JSON))
    parser.add_argument("--report-dir", default=str(DEFAULT_REPORT_DIR))
    return parser


def write_markdown(path: Path, payload: dict) -> None:
    lines: list[str] = []
    lines.append("# Overnight Phased Plan Handoff")
    lines.append("")
    lines.append("## Snapshot")
    lines.append("")
    lines.append(f"- Current unlocked profile: `{payload['current_unlocked_profile']}`")
    lines.append(f"- Repo update status: `{payload['repo_update_status']}`")
    lines.append(f"- Execution posture: `{payload['execution_posture']}`")
    lines.append(f"- Execution evidence contract: `{payload['execution_evidence_contract_status']}`")
    lines.append("")
    lines.append("## Tonight's Machine Missions")
    lines.append("")
    lines.append(f"- Research machine: {payload['research_machine_mission']}")
    lines.append(f"- New machine: {payload['new_machine_mission']}")
    lines.append("")
    lines.append("## Immediate Operator Actions")
    lines.append("")
    for row in list(payload.get("operator_actions") or []):
        lines.append(f"- {row}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = build_parser().parse_args()
    plan_path = Path(args.plan_json).resolve()
    report_dir = Path(args.report_dir).resolve()
    report_dir.mkdir(parents=True, exist_ok=True)

    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    phases = [dict(row) for row in list(plan.get("phases") or []) if isinstance(row, dict)]
    research_phase = next((row for row in phases if row.get("phase_code") == "phase_2_research_unlock_progress"), {})
    execution_phase = next((row for row in phases if row.get("phase_code") == "phase_3_execution_evidence_capture"), {})

    payload = {
        "generated_at": plan.get("generated_at"),
        "plan_json": str(plan_path),
        "current_unlocked_profile": plan.get("current_unlocked_profile"),
        "repo_update_status": plan.get("repo_update_status"),
        "execution_posture": plan.get("execution_posture"),
        "execution_evidence_contract_status": plan.get("execution_evidence_contract_status"),
        "research_machine_mission": research_phase.get("title"),
        "new_machine_mission": execution_phase.get("title"),
        "blocked_profiles_must_remain_blocked": list(plan.get("blocked_profiles_must_remain_blocked") or []),
        "required_next_session_artifacts": list(execution_phase.get("required_next_session_artifacts") or []),
        "operator_actions": [
            f"Keep running `{plan.get('current_unlocked_profile')}` as the governed overnight default.",
            str(research_phase.get("objective") or ""),
            str(execution_phase.get("objective") or ""),
            "Rebuild reconciliation, calibration, unlock, workplan, and execution evidence artifacts after the next trusted session lands.",
            "Do not activate blocked profiles or mutate the live manifest during the overnight cycle.",
        ],
        "by_morning_success": list(plan.get("by_morning_success") or []),
    }

    json_path = report_dir / "overnight_phased_plan_handoff.json"
    md_path = report_dir / "overnight_phased_plan_handoff.md"
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    write_markdown(md_path, payload)
    print(json.dumps({"json_path": str(json_path), "markdown_path": str(md_path)}, indent=2))


if __name__ == "__main__":
    main()
