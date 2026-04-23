from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[2]
DEFAULT_AUDIT_JSON = REPO_ROOT / "docs" / "gcp_foundation" / "gcp_project_state_audit_status.json"
DEFAULT_REPORT_DIR = REPO_ROOT / "docs" / "gcp_foundation"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build a GCP drift-classification packet from the live project audit.")
    parser.add_argument("--audit-json", default=str(DEFAULT_AUDIT_JSON))
    parser.add_argument("--report-dir", default=str(DEFAULT_REPORT_DIR))
    return parser


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def classification_payload(audit: dict[str, Any]) -> dict[str, Any]:
    generated_at = datetime.now().astimezone().isoformat()
    project_id = str(audit.get("project_id") or "codexalpaca")
    buckets = set(audit.get("buckets", []))
    services = set(audit.get("enabled_services", []))

    classifications = [
        {
            "resource_type": "compute_instance",
            "resource_name": "vm-execution-paper-01",
            "classification": "sanctioned_validation_asset",
            "decision": "keep",
            "rationale": "This is the codified validation execution VM on the governed rollout path and it already has a green headless validation gate.",
        },
        {
            "resource_type": "compute_instance",
            "resource_name": "multi-ticker-trader-v1",
            "classification": "parallel_runtime_drift",
            "decision": "quarantine",
            "rationale": "It is a second running broker-facing runtime path on default network with its own startup bootstrap, static IP, runtime secret, and container repo outside the codified execution rollout.",
        },
        {
            "resource_type": "service_account",
            "resource_name": "multi-ticker-vm@codexalpaca.iam.gserviceaccount.com",
            "classification": "parallel_runtime_identity",
            "decision": "quarantine",
            "rationale": "This service account exists only to support the unmanaged multi-ticker VM path and should not be treated as a sanctioned runtime identity until formally adopted.",
        },
        {
            "resource_type": "secret",
            "resource_name": "multi-ticker-vm-env",
            "classification": "parallel_runtime_secret",
            "decision": "quarantine",
            "rationale": "This secret feeds the unmanaged VM runtime path and should not be reused or expanded until the owning architecture decision is made.",
        },
        {
            "resource_type": "bucket",
            "resource_name": "codexalpaca-runtime-us-central1",
            "classification": "parallel_runtime_storage",
            "decision": "quarantine",
            "rationale": "This runtime bucket is outside the codified role-separated foundation. It is currently empty, which makes it a good candidate for explicit keep-or-delete review.",
        },
        {
            "resource_type": "artifact_repository",
            "resource_name": "codexalpaca-containers",
            "classification": "parallel_runtime_artifacts",
            "decision": "quarantine",
            "rationale": "This repository contains the unmanaged multi-ticker runtime image stream and is not yet governed by the codified execution pipeline.",
        },
        {
            "resource_type": "network",
            "resource_name": "default",
            "classification": "network_drift",
            "decision": "retire_runtime_use",
            "rationale": "Default VPC remains broad and currently hosts the unmanaged runtime VM. Institutional promotion requires runtime migration onto vpc-codex-core or explicit decommission.",
        },
        {
            "resource_type": "iam_posture",
            "resource_name": "project_owner_assignments",
            "classification": "bootstrap_privilege_drift",
            "decision": "narrow",
            "rationale": "Project-level Owner remains on service accounts, which is acceptable for bootstrap but not for steady-state runtime or operator posture.",
        },
        {
            "resource_type": "bucket",
            "resource_name": "codexalpaca-transfer-922745393036",
            "classification": "bootstrap_transfer_storage",
            "decision": "keep_temporary",
            "rationale": "This bucket is useful as a bootstrap transfer archive, but it is not part of the long-term governed runtime storage model and should later be lifecycle-managed or retired.",
        },
        {
            "resource_type": "bucket",
            "resource_name": "codexalpaca_cloudbuild",
            "classification": "build_utility_storage",
            "decision": "formalize_or_retire",
            "rationale": "This is a Cloud Build source bucket pattern rather than part of the runtime foundation. Keep it only if Cloud Build becomes part of the sanctioned deployment plane.",
        },
    ]

    promotion_blockers = [
        "A second unmanaged runtime path exists in GCP and has not yet been classified.",
        "Project-level Owner is still granted to service accounts.",
        "Default network is still active and still hosting runtime compute.",
        "There is no cloud-backed shared execution lease yet.",
    ]

    immediate_operator_rules = [
        "Do not create any new runner VM, service account, secret, bucket, or artifact repository until the drift classification is accepted.",
        "Do not start broker-facing execution from multi-ticker-trader-v1.",
        "Do not promote vm-execution-paper-01 to canonical execution until Phase 0 and Phase 1 are complete and a trusted validation session is clean.",
        "Treat the codified execution path as the only sanctioned path under active development.",
    ]

    required_decisions = [
        "Keep, migrate, or decommission multi-ticker-trader-v1.",
        "Keep or decommission the multi-ticker-vm identity and multi-ticker-vm-env secret.",
        "Keep or decommission codexalpaca-runtime-us-central1.",
        "Formalize or retire codexalpaca-containers and codexalpaca_cloudbuild.",
        "Define when default VPC can be considered empty enough to quarantine.",
    ]

    return {
        "generated_at": generated_at,
        "project_id": project_id,
        "phase0_freeze_state": "active",
        "phase0_readiness": "classification_required",
        "audit_posture": audit.get("audit_posture"),
        "service_summary": {
            "enabled_service_count": len(services),
            "workflows_enabled": "workflows.googleapis.com" in services,
            "scheduler_enabled": "cloudscheduler.googleapis.com" in services,
            "batch_enabled": "batch.googleapis.com" in services,
        },
        "observed_storage": {
            "foundation_buckets": sorted(name for name in buckets if name in {
                "codexalpaca-data-us",
                "codexalpaca-artifacts-us",
                "codexalpaca-control-us",
                "codexalpaca-backups-us",
            }),
            "nonfoundation_buckets": sorted(name for name in buckets if name not in {
                "codexalpaca-data-us",
                "codexalpaca-artifacts-us",
                "codexalpaca-control-us",
                "codexalpaca-backups-us",
            }),
        },
        "classifications": classifications,
        "promotion_blockers": promotion_blockers,
        "immediate_operator_rules": immediate_operator_rules,
        "required_decisions": required_decisions,
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    lines: list[str] = []
    lines.append("# GCP Drift Classification")
    lines.append("")
    lines.append("## Snapshot")
    lines.append("")
    lines.append(f"- Generated at: `{payload['generated_at']}`")
    lines.append(f"- Project ID: `{payload['project_id']}`")
    lines.append(f"- Freeze state: `{payload['phase0_freeze_state']}`")
    lines.append(f"- Phase 0 readiness: `{payload['phase0_readiness']}`")
    lines.append("")
    lines.append("## Immediate Operator Rules")
    lines.append("")
    for rule in payload["immediate_operator_rules"]:
        lines.append(f"- {rule}")
    lines.append("")
    lines.append("## Resource Decisions")
    lines.append("")
    for row in payload["classifications"]:
        lines.append(f"- `{row['resource_type']}` `{row['resource_name']}`")
        lines.append(f"  - classification: `{row['classification']}`")
        lines.append(f"  - decision: `{row['decision']}`")
        lines.append(f"  - rationale: {row['rationale']}")
    lines.append("")
    lines.append("## Promotion Blockers")
    lines.append("")
    for blocker in payload["promotion_blockers"]:
        lines.append(f"- {blocker}")
    lines.append("")
    lines.append("## Required Decisions")
    lines.append("")
    for decision in payload["required_decisions"]:
        lines.append(f"- {decision}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_handoff(path: Path, payload: dict[str, Any]) -> None:
    lines: list[str] = []
    lines.append("# GCP Drift Classification Handoff")
    lines.append("")
    lines.append("## Current Read")
    lines.append("")
    lines.append("- Phase 0 freeze is active.")
    lines.append("- The sanctioned execution asset is `vm-execution-paper-01`.")
    lines.append("- The highest-risk drift asset is `multi-ticker-trader-v1`.")
    lines.append("- The project should not create more runtime resources until drift classification is resolved.")
    lines.append("")
    lines.append("## Keep")
    lines.append("")
    lines.append("- `vm-execution-paper-01`")
    lines.append("- `vpc-codex-core` execution path")
    lines.append("- role-separated foundation buckets")
    lines.append("")
    lines.append("## Quarantine")
    lines.append("")
    lines.append("- `multi-ticker-trader-v1`")
    lines.append("- `multi-ticker-vm@codexalpaca.iam.gserviceaccount.com`")
    lines.append("- `multi-ticker-vm-env`")
    lines.append("- `codexalpaca-runtime-us-central1`")
    lines.append("- `codexalpaca-containers`")
    lines.append("- `default` VPC runtime use")
    lines.append("")
    lines.append("## Next Decisions")
    lines.append("")
    for decision in payload["required_decisions"]:
        lines.append(f"- {decision}")
    lines.append("")
    lines.append("## Rule")
    lines.append("")
    lines.append("- Do not promote cloud execution or create new runner infrastructure until the quarantined footprint is either codified or decommissioned.")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    audit_json = Path(args.audit_json).resolve()
    report_dir = Path(args.report_dir).resolve()

    audit = load_json(audit_json)
    payload = classification_payload(audit)

    write_json(report_dir / "gcp_drift_classification_status.json", payload)
    write_markdown(report_dir / "gcp_drift_classification_status.md", payload)
    write_handoff(report_dir / "gcp_drift_classification_handoff.md", payload)
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
