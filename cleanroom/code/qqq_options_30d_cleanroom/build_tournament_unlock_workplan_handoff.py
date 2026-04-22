from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[2]
DEFAULT_WORKPLAN_JSON = REPO_ROOT / "docs" / "tournament_unlocks" / "tournament_unlock_workplan.json"
DEFAULT_REPORT_DIR = REPO_ROOT / "docs" / "tournament_unlocks"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build a concise handoff from the tournament unlock workplan."
    )
    parser.add_argument("--workplan-json", default=str(DEFAULT_WORKPLAN_JSON))
    parser.add_argument("--report-dir", default=str(DEFAULT_REPORT_DIR))
    return parser


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    lines: list[str] = []
    lines.append("# Tournament Unlock Workplan Handoff")
    lines.append("")
    lines.append("## Snapshot")
    lines.append("")
    lines.append(f"- Current unlocked profile: `{payload['current_unlocked_profile']}`")
    lines.append(f"- Research plane mission: {payload['research_plane_title']}")
    lines.append(f"- Execution plane mission: {payload['execution_plane_title']}")
    lines.append("")
    lines.append("## Immediate Operator Actions")
    lines.append("")
    for action in list(payload.get("operator_actions") or []):
        lines.append(f"- {action}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = build_parser().parse_args()
    workplan_path = Path(args.workplan_json).resolve()
    report_dir = Path(args.report_dir).resolve()
    report_dir.mkdir(parents=True, exist_ok=True)

    workplan = json.loads(workplan_path.read_text(encoding="utf-8"))
    research = dict(workplan.get("research_plane_mission") or {})
    execution = dict(workplan.get("execution_plane_mission") or {})

    payload = {
        "generated_at": workplan.get("generated_at"),
        "workplan_json": str(workplan_path),
        "current_unlocked_profile": workplan.get("current_unlocked_profile"),
        "research_plane_title": research.get("title"),
        "execution_plane_title": execution.get("title"),
        "operator_actions": [
            f"Keep running `{workplan.get('current_unlocked_profile')}` as the unlocked governed profile.",
            research.get("summary"),
            execution.get("summary"),
        ],
        "research_plane_mission": research,
        "execution_plane_mission": execution,
        "completion_gates": list(workplan.get("completion_gates") or []),
    }

    json_path = report_dir / "tournament_unlock_workplan_handoff.json"
    md_path = report_dir / "tournament_unlock_workplan_handoff.md"
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    write_markdown(md_path, payload)
    print(json.dumps({"json_path": str(json_path), "markdown_path": str(md_path)}, indent=2))


if __name__ == "__main__":
    main()
