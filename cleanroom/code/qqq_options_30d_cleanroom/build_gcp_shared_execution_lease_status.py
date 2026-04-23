from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[2]
DEFAULT_REPORT_DIR = REPO_ROOT / "docs" / "gcp_foundation"
DEFAULT_EXCEPTION_JSON = REPO_ROOT / "docs" / "gcp_foundation" / "gcp_parallel_runtime_exception_status.json"
DEFAULT_PROJECT_AUDIT_JSON = REPO_ROOT / "docs" / "gcp_foundation" / "gcp_project_state_audit_status.json"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build a shared execution lease design packet.")
    parser.add_argument("--exception-json", default=str(DEFAULT_EXCEPTION_JSON))
    parser.add_argument("--project-audit-json", default=str(DEFAULT_PROJECT_AUDIT_JSON))
    parser.add_argument("--report-dir", default=str(DEFAULT_REPORT_DIR))
    return parser


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def build_payload(exception: dict[str, Any], audit: dict[str, Any]) -> dict[str, Any]:
    generated_at = datetime.now().astimezone().isoformat()
    buckets = set(audit.get("buckets", []))
    enabled_services = set(audit.get("enabled_services", []))
    firestore_enabled = "firestore.googleapis.com" in enabled_services

    recommended_bucket = "codexalpaca-control-us" if "codexalpaca-control-us" in buckets else None
    lease_object = f"gs://{recommended_bucket}/leases/paper-execution/lease.json" if recommended_bucket else None

    option_gcs = {
        "name": "gcs_generation_match_lease",
        "status": "recommended_now",
        "pros": [
            "Uses infrastructure already present in the codified control plane.",
            "Does not require enabling a new stateful database service.",
            "Supports compare-and-set semantics through Cloud Storage generation preconditions.",
            "Fits well with the existing control bucket and packet model.",
        ],
        "cons": [
            "Requires careful lease content design and expiry handling.",
            "Is less expressive than a transactional document store for multi-step orchestration later.",
        ],
        "implementation_shape": {
            "bucket": recommended_bucket,
            "object": lease_object,
            "acquire": "Create only if absent using ifGenerationMatch=0.",
            "renew": "Rewrite only if the stored generation matches the caller's last-seen generation.",
            "release": "Delete only if the stored generation matches the caller's last-seen generation.",
            "expiry_field": "expires_at",
            "owner_fields": ["owner_id", "machine_label", "runner_path", "git_commit", "acquired_at", "expires_at"],
        },
    }

    option_firestore = {
        "name": "firestore_transaction_lease",
        "status": "future_upgrade_only" if not firestore_enabled else "optional_future_upgrade",
        "pros": [
            "Offers richer transactional semantics for orchestration-heavy coordination.",
            "Would be a cleaner long-term fit if Workflows, Scheduler, and multi-step cloud orchestration become primary.",
        ],
        "cons": [
            "Cloud Firestore API is not enabled in this project today.",
            "Adds a new operational surface area before the basic lease problem is solved.",
            "Would slow down convergence on the immediate execution-safety control.",
        ],
    }

    recommended_decision = "gcs_generation_match_lease"

    immediate_design_rules = [
        "Only one broker-facing paper execution holder may own the lease at a time.",
        "Lease acquisition must be atomic and must fail closed on contention.",
        "Lease records must include expiry and ownership metadata.",
        "Expired leases may be stolen only through an explicit compare-and-set flow, never by blind overwrite.",
        "Every acquire, renew, release, and steal event should write an audit artifact into the control bucket.",
    ]

    promotion_blockers = list(exception.get("promotion_blockers", []))
    if "The shared execution lease is still missing." not in promotion_blockers:
        promotion_blockers.append("The shared execution lease is still missing.")

    phased_rollout = [
        "Phase A: design and publish the GCS lease contract.",
        "Phase B: implement lease helpers in both workstation and VM runners without enabling them by default.",
        "Phase C: validate acquire, renew, release, stale-expiry, and conflict handling in dry-run mode.",
        "Phase D: turn lease enforcement on for broker-facing paper execution.",
        "Phase E: reassess whether Firestore is needed after orchestration matures.",
    ]

    return {
        "generated_at": generated_at,
        "project_id": audit.get("project_id", "codexalpaca"),
        "lease_readiness": "design_ready_not_implemented",
        "recommended_lease": recommended_decision,
        "firestore_enabled": firestore_enabled,
        "gcs_control_bucket_present": bool(recommended_bucket),
        "lease_options": [option_gcs, option_firestore],
        "immediate_design_rules": immediate_design_rules,
        "promotion_blockers": promotion_blockers,
        "phased_rollout": phased_rollout,
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    lines: list[str] = []
    lines.append("# GCP Shared Execution Lease")
    lines.append("")
    lines.append("## Snapshot")
    lines.append("")
    lines.append(f"- Generated at: `{payload['generated_at']}`")
    lines.append(f"- Project ID: `{payload['project_id']}`")
    lines.append(f"- Lease readiness: `{payload['lease_readiness']}`")
    lines.append(f"- Recommended lease: `{payload['recommended_lease']}`")
    lines.append(f"- Firestore enabled: `{payload['firestore_enabled']}`")
    lines.append(f"- Control bucket present: `{payload['gcs_control_bucket_present']}`")
    lines.append("")
    lines.append("## Recommendation")
    lines.append("")
    lines.append("- Use a Cloud Storage generation-match lease in `codexalpaca-control-us` first.")
    lines.append("- Do not wait for Firestore to solve the immediate execution-safety problem.")
    lines.append("")
    lines.append("## Lease Options")
    lines.append("")
    for option in payload["lease_options"]:
        lines.append(f"- `{option['name']}`")
        lines.append(f"  - status: `{option['status']}`")
        for pro in option.get("pros", []):
            lines.append(f"  - pro: {pro}")
        for con in option.get("cons", []):
            lines.append(f"  - con: {con}")
        if "implementation_shape" in option:
            shape = option["implementation_shape"]
            lines.append(f"  - bucket: `{shape['bucket']}`")
            lines.append(f"  - object: `{shape['object']}`")
            lines.append(f"  - acquire: {shape['acquire']}")
            lines.append(f"  - renew: {shape['renew']}")
            lines.append(f"  - release: {shape['release']}")
            lines.append(f"  - expiry field: `{shape['expiry_field']}`")
    lines.append("")
    lines.append("## Immediate Design Rules")
    lines.append("")
    for rule in payload["immediate_design_rules"]:
        lines.append(f"- {rule}")
    lines.append("")
    lines.append("## Phased Rollout")
    lines.append("")
    for step in payload["phased_rollout"]:
        lines.append(f"- {step}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_handoff(path: Path, payload: dict[str, Any]) -> None:
    lines: list[str] = []
    lines.append("# GCP Shared Execution Lease Handoff")
    lines.append("")
    lines.append("## Current Read")
    lines.append("")
    lines.append("- The lease design is ready, but not yet implemented.")
    lines.append("- The recommended first implementation is a GCS generation-match lease in the control bucket.")
    lines.append("- Firestore is not enabled, so it should not be the immediate dependency for execution safety.")
    lines.append("")
    lines.append("## Operator Rule")
    lines.append("")
    lines.append("- Keep using explicit exclusive execution windows until the lease is implemented and enforced.")
    lines.append("- Do not run concurrent broker-facing sessions across machines until lease enforcement exists.")
    lines.append("")
    lines.append("## Next Build Step")
    lines.append("")
    lines.append("- Implement lease helpers in the sanctioned runner paths and validate them in dry-run mode before turning on enforcement.")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    exception = load_json(Path(args.exception_json).resolve())
    audit = load_json(Path(args.project_audit_json).resolve())
    payload = build_payload(exception, audit)

    report_dir = Path(args.report_dir).resolve()
    write_json(report_dir / "gcp_shared_execution_lease_status.json", payload)
    write_markdown(report_dir / "gcp_shared_execution_lease_status.md", payload)
    write_handoff(report_dir / "gcp_shared_execution_lease_handoff.md", payload)
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
