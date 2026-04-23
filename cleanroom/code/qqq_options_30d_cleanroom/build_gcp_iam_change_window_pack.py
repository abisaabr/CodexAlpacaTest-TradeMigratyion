from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[2]
DEFAULT_HARDENING_JSON = REPO_ROOT / "docs" / "gcp_foundation" / "gcp_iam_hardening_status.json"
DEFAULT_DRIFT_JSON = REPO_ROOT / "docs" / "gcp_foundation" / "gcp_drift_classification_status.json"
DEFAULT_REPORT_DIR = REPO_ROOT / "docs" / "gcp_foundation"
PROJECT_ID = "codexalpaca"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build the non-destructive IAM change-window execution pack.")
    parser.add_argument("--hardening-json", default=str(DEFAULT_HARDENING_JSON))
    parser.add_argument("--drift-json", default=str(DEFAULT_DRIFT_JSON))
    parser.add_argument("--report-dir", default=str(DEFAULT_REPORT_DIR))
    return parser


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def build_payload(hardening: dict[str, Any], drift: dict[str, Any]) -> dict[str, Any]:
    generated_at = datetime.now().astimezone().isoformat()
    owner_principals = hardening.get("project_owner_principals", [])
    change_id = f"gcp-iam-change-window-{datetime.now().strftime('%Y%m%d')}"
    target_removals = [
        {
            "principal": "serviceAccount:ramzi-service-account@codexalpaca.iam.gserviceaccount.com",
            "role": "roles/owner",
            "reason": "Step down operator automation principal from project-wide Owner to minimal operator access.",
        },
        {
            "principal": "serviceAccount:sa-bootstrap-admin@codexalpaca.iam.gserviceaccount.com",
            "role": "roles/owner",
            "reason": "Convert bootstrap identity away from standing Owner after foundation setup.",
        },
    ]

    prechecks = [
        "Confirm the temporary parallel-runtime exception is still understood and no migration/decommission work is in flight.",
        "Confirm no bootstrap or provisioning task is currently depending on project-wide Owner through ramzi-service-account or sa-bootstrap-admin.",
        "Confirm operator access is already present through IAP, OS Login, and Compute Viewer for ramzi-service-account.",
        "Capture a fresh project IAM policy snapshot before any mutation.",
        "Use an explicit change window and do not combine this step with broker-facing execution changes.",
    ]

    execution_commands = [
        f"gcloud projects get-iam-policy {PROJECT_ID} --format=json > codexalpaca_iam_policy_before.json",
        f"gcloud projects remove-iam-policy-binding {PROJECT_ID} --member=\"serviceAccount:ramzi-service-account@codexalpaca.iam.gserviceaccount.com\" --role=\"roles/owner\"",
        f"gcloud projects remove-iam-policy-binding {PROJECT_ID} --member=\"serviceAccount:sa-bootstrap-admin@codexalpaca.iam.gserviceaccount.com\" --role=\"roles/owner\"",
        f"gcloud projects get-iam-policy {PROJECT_ID} --format=json > codexalpaca_iam_policy_after.json",
    ]

    rollback_commands = [
        f"gcloud projects add-iam-policy-binding {PROJECT_ID} --member=\"serviceAccount:ramzi-service-account@codexalpaca.iam.gserviceaccount.com\" --role=\"roles/owner\"",
        f"gcloud projects add-iam-policy-binding {PROJECT_ID} --member=\"serviceAccount:sa-bootstrap-admin@codexalpaca.iam.gserviceaccount.com\" --role=\"roles/owner\"",
    ]

    postchecks = [
        "Rebuild gcp_iam_hardening_status and confirm the two service accounts no longer appear in project_owner_principals.",
        "Rebuild gcp_project_state_audit_status and confirm audit posture improves or at minimum does not regress.",
        "Rebuild gcp_parallel_runtime_exception_status and confirm the exception is still documented and bounded.",
        "Publish the post-change packets to GitHub main and gs://codexalpaca-control-us before resuming broader work.",
    ]

    blockers = []
    if "serviceAccount:ramzi-service-account@codexalpaca.iam.gserviceaccount.com" not in owner_principals:
        blockers.append("ramzi-service-account is not currently an Owner; re-check live IAM before executing this pack.")
    if "serviceAccount:sa-bootstrap-admin@codexalpaca.iam.gserviceaccount.com" not in owner_principals:
        blockers.append("sa-bootstrap-admin is not currently an Owner; re-check live IAM before executing this pack.")
    if any(item == "multi-ticker-trader-v1" for item in drift.get("temporary_exception_assets", [])):
        pass

    return {
        "generated_at": generated_at,
        "project_id": PROJECT_ID,
        "change_id": change_id,
        "change_state": "prepared_not_executed",
        "scope": "project_level_owner_removal_for_service_accounts_only",
        "owner_principals_before": owner_principals,
        "target_removals": target_removals,
        "prechecks": prechecks,
        "execution_commands": execution_commands,
        "rollback_commands": rollback_commands,
        "postchecks": postchecks,
        "blockers": blockers,
        "hard_rules": [
            "Do not include the human owner principal in this first cutover unless separately reviewed.",
            "Do not change quarantined multi-ticker-vm privileges during this change window.",
            "Do not combine IAM hardening with first trusted validation-session execution.",
            "Always take before-and-after IAM snapshots.",
        ],
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    lines: list[str] = []
    lines.append("# GCP IAM Change Window Pack")
    lines.append("")
    lines.append("## Snapshot")
    lines.append("")
    lines.append(f"- Generated at: `{payload['generated_at']}`")
    lines.append(f"- Project ID: `{payload['project_id']}`")
    lines.append(f"- Change ID: `{payload['change_id']}`")
    lines.append(f"- Change state: `{payload['change_state']}`")
    lines.append(f"- Scope: `{payload['scope']}`")
    lines.append("")
    lines.append("## Target Removals")
    lines.append("")
    for row in payload["target_removals"]:
        lines.append(f"- `{row['principal']}` -> `{row['role']}`")
        lines.append(f"  - reason: {row['reason']}")
    lines.append("")
    lines.append("## Prechecks")
    lines.append("")
    for item in payload["prechecks"]:
        lines.append(f"- {item}")
    lines.append("")
    lines.append("## Execution Commands")
    lines.append("")
    for cmd in payload["execution_commands"]:
        lines.append(f"- `{cmd}`")
    lines.append("")
    lines.append("## Rollback Commands")
    lines.append("")
    for cmd in payload["rollback_commands"]:
        lines.append(f"- `{cmd}`")
    lines.append("")
    lines.append("## Postchecks")
    lines.append("")
    for item in payload["postchecks"]:
        lines.append(f"- {item}")
    lines.append("")
    lines.append("## Hard Rules")
    lines.append("")
    for item in payload["hard_rules"]:
        lines.append(f"- {item}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_handoff(path: Path, payload: dict[str, Any]) -> None:
    lines: list[str] = []
    lines.append("# GCP IAM Change Window Handoff")
    lines.append("")
    lines.append("## Current Read")
    lines.append("")
    lines.append("- The IAM change pack is ready.")
    lines.append("- It is intentionally non-destructive until an explicit change window is opened.")
    lines.append("- The first cutover removes project-level Owner only from the two service accounts, not from the human owner principal.")
    lines.append("")
    lines.append("## Execute Only When")
    lines.append("")
    lines.append("- no bootstrap activity is in flight")
    lines.append("- the temporary parallel-runtime exception is still frozen")
    lines.append("- the operator is ready to rerun the audit immediately after the change")
    lines.append("")
    lines.append("## First Commands")
    lines.append("")
    for cmd in payload["execution_commands"][:3]:
        lines.append(f"- `{cmd}`")
    lines.append("")
    lines.append("## Rule")
    lines.append("")
    lines.append("- Do not mix this IAM cutover with first trusted validation-session execution. Keep privilege hardening and broker-facing validation as separate controlled events.")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    hardening = load_json(Path(args.hardening_json).resolve())
    drift = load_json(Path(args.drift_json).resolve())
    payload = build_payload(hardening, drift)

    report_dir = Path(args.report_dir).resolve()
    write_json(report_dir / "gcp_iam_change_window_status.json", payload)
    write_markdown(report_dir / "gcp_iam_change_window_status.md", payload)
    write_handoff(report_dir / "gcp_iam_change_window_handoff.md", payload)
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
