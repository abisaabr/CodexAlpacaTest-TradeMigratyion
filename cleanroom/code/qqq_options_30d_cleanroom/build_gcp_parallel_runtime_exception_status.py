from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[2]
DEFAULT_DRIFT_JSON = REPO_ROOT / "docs" / "gcp_foundation" / "gcp_drift_classification_status.json"
DEFAULT_IAM_JSON = REPO_ROOT / "docs" / "gcp_foundation" / "gcp_iam_hardening_status.json"
DEFAULT_REPORT_DIR = REPO_ROOT / "docs" / "gcp_foundation"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build a temporary parallel-runtime exception packet.")
    parser.add_argument("--drift-json", default=str(DEFAULT_DRIFT_JSON))
    parser.add_argument("--iam-json", default=str(DEFAULT_IAM_JSON))
    parser.add_argument("--report-dir", default=str(DEFAULT_REPORT_DIR))
    return parser


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def build_payload(drift: dict[str, Any], iam: dict[str, Any]) -> dict[str, Any]:
    generated_at = datetime.now().astimezone().isoformat()
    quarantined = [
        row["resource_name"]
        for row in drift.get("classifications", [])
        if row.get("decision") == "quarantine"
    ]
    owner_principals = iam.get("project_owner_principals", [])

    return {
        "generated_at": generated_at,
        "project_id": drift.get("project_id", "codexalpaca"),
        "exception_id": "parallel-runtime-exception-2026-04-23",
        "exception_state": "active_temporary_exception",
        "sanctioned_path": {
            "primary_asset": "vm-execution-paper-01",
            "description": "The codified execution-validation path under the governed rollout.",
        },
        "temporary_exception_assets": quarantined,
        "reason": "A currently running parallel runner path will remain in place for now while it is documented, frozen, and evaluated for migration or decommission.",
        "compensating_controls": [
            "Do not create any additional runner VM, runtime secret, runtime bucket, or runtime service account for the parallel path.",
            "Do not widen IAM privileges for the parallel path while the exception is active.",
            "Record every material change related to the parallel path in GitHub main and in the GCS control bucket.",
            "Do not promote vm-execution-paper-01 to canonical execution while the exception remains unresolved.",
            "Do not run broker-facing sessions concurrently across the sanctioned path and the temporary exception path.",
            "Use an explicit exclusive execution window for any broker-facing session while the shared execution lease is still missing.",
        ],
        "required_documentation": [
            "The other machine must publish any changes to the parallel path into GitHub main.",
            "The other machine must mirror control-plane status into gs://codexalpaca-control-us.",
            "Any change to the parallel path must include what changed, why it changed, and whether it increases or reduces convergence risk.",
        ],
        "promotion_blockers": [
            "The temporary exception is still active.",
            "Project-level Owner remains on service accounts.",
            "The shared execution lease is still missing.",
            "The first trusted validation paper session on vm-execution-paper-01 has not yet been used to clear promotion by evidence.",
        ],
        "exit_criteria": [
            "A clear keep/migrate/decommission decision exists for multi-ticker-trader-v1.",
            "Any surviving runtime path is represented in the codified control plane.",
            "Project-level Owner is removed from service accounts.",
            "A cloud-backed shared execution lease exists.",
            "The sanctioned execution VM has a clean trusted validation session and assimilation packet.",
        ],
        "current_risk_notes": [
            "Parallel runtime increases architecture ambiguity and operator error risk.",
            f"Current project Owner principals still include: {', '.join(owner_principals)}." if owner_principals else "No project Owner principals detected.",
        ],
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    lines: list[str] = []
    lines.append("# GCP Parallel Runtime Exception")
    lines.append("")
    lines.append("## Snapshot")
    lines.append("")
    lines.append(f"- Generated at: `{payload['generated_at']}`")
    lines.append(f"- Project ID: `{payload['project_id']}`")
    lines.append(f"- Exception ID: `{payload['exception_id']}`")
    lines.append(f"- Exception state: `{payload['exception_state']}`")
    lines.append("")
    lines.append("## Sanctioned Path")
    lines.append("")
    lines.append(f"- Primary asset: `{payload['sanctioned_path']['primary_asset']}`")
    lines.append(f"- {payload['sanctioned_path']['description']}")
    lines.append("")
    lines.append("## Temporary Exception Assets")
    lines.append("")
    for item in payload["temporary_exception_assets"]:
        lines.append(f"- `{item}`")
    lines.append("")
    lines.append("## Reason")
    lines.append("")
    lines.append(f"- {payload['reason']}")
    lines.append("")
    lines.append("## Compensating Controls")
    lines.append("")
    for item in payload["compensating_controls"]:
        lines.append(f"- {item}")
    lines.append("")
    lines.append("## Required Documentation")
    lines.append("")
    for item in payload["required_documentation"]:
        lines.append(f"- {item}")
    lines.append("")
    lines.append("## Promotion Blockers")
    lines.append("")
    for item in payload["promotion_blockers"]:
        lines.append(f"- {item}")
    lines.append("")
    lines.append("## Exit Criteria")
    lines.append("")
    for item in payload["exit_criteria"]:
        lines.append(f"- {item}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_handoff(path: Path, payload: dict[str, Any]) -> None:
    lines: list[str] = []
    lines.append("# GCP Parallel Runtime Exception Handoff")
    lines.append("")
    lines.append("## Current Read")
    lines.append("")
    lines.append("- The codified execution path remains the sanctioned path.")
    lines.append("- The parallel runner path is temporarily allowed to remain, but only under explicit exception controls.")
    lines.append("- This exception does not bless the parallel path as a second sanctioned architecture.")
    lines.append("")
    lines.append("## Operator Rule")
    lines.append("")
    lines.append("- Treat the parallel path as tolerated but frozen.")
    lines.append("- Do not create additional runtime sprawl around it.")
    lines.append("- Document every material change in GitHub and the GCS control bucket.")
    lines.append("- Do not run concurrent broker-facing execution across the sanctioned and exception paths.")
    lines.append("")
    lines.append("## Exit")
    lines.append("")
    lines.append("- The exception ends only when the parallel path is codified into the sanctioned rollout or decommissioned.")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    drift = load_json(Path(args.drift_json).resolve())
    iam = load_json(Path(args.iam_json).resolve())
    payload = build_payload(drift, iam)

    report_dir = Path(args.report_dir).resolve()
    write_json(report_dir / "gcp_parallel_runtime_exception_status.json", payload)
    write_markdown(report_dir / "gcp_parallel_runtime_exception_status.md", payload)
    write_handoff(report_dir / "gcp_parallel_runtime_exception_handoff.md", payload)
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
