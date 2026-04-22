from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[2]
DEFAULT_CONTRACT_JSON = REPO_ROOT / "docs" / "execution_evidence" / "execution_evidence_contract.json"
DEFAULT_REPORT_DIR = REPO_ROOT / "docs" / "execution_evidence"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build a concise handoff from the execution evidence contract."
    )
    parser.add_argument("--contract-json", default=str(DEFAULT_CONTRACT_JSON))
    parser.add_argument("--report-dir", default=str(DEFAULT_REPORT_DIR))
    return parser


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    lines: list[str] = []
    lines.append("# Execution Evidence Contract Handoff")
    lines.append("")
    lines.append(f"- Current unlocked profile: `{payload['current_unlocked_profile']}`")
    lines.append(f"- Contract status: `{payload['contract_status']}`")
    lines.append(f"- Latest traded session used: `{payload['latest_traded_session_date'] or 'none'}`")
    lines.append("")
    lines.append("## Required Next Session Artifacts")
    lines.append("")
    for row in list(payload.get("required_next_session_artifacts") or []):
        lines.append(f"- {row}")
    lines.append("")
    lines.append("## Immediate Gaps")
    lines.append("")
    for row in list(payload.get("immediate_gaps") or []):
        lines.append(f"- `{row['check_id']}`: {row['summary']}")
    if not list(payload.get("immediate_gaps") or []):
        lines.append("- none")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = build_parser().parse_args()
    contract_path = Path(args.contract_json).resolve()
    report_dir = Path(args.report_dir).resolve()
    report_dir.mkdir(parents=True, exist_ok=True)

    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    required_artifacts = [
        "broker-order audit",
        "broker account-activity audit",
        "ending broker-position snapshot",
        "shutdown reconciliation",
        "completed trade table with broker/local economics comparison",
    ]
    payload = {
        "generated_at": contract.get("generated_at"),
        "contract_json": str(contract_path),
        "current_unlocked_profile": contract.get("current_unlocked_profile"),
        "contract_status": contract.get("contract_status"),
        "latest_traded_session_date": contract.get("latest_traded_session_date"),
        "required_next_session_artifacts": required_artifacts,
        "immediate_gaps": list(contract.get("failed_checks") or []),
    }

    json_path = report_dir / "execution_evidence_contract_handoff.json"
    md_path = report_dir / "execution_evidence_contract_handoff.md"
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    write_markdown(md_path, payload)
    print(json.dumps({"json_path": str(json_path), "markdown_path": str(md_path)}, indent=2))


if __name__ == "__main__":
    main()
