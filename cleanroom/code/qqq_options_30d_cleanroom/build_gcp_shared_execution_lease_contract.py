from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[2]
DEFAULT_LEASE_JSON = REPO_ROOT / "docs" / "gcp_foundation" / "gcp_shared_execution_lease_status.json"
DEFAULT_REPORT_DIR = REPO_ROOT / "docs" / "gcp_foundation"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build the shared execution lease contract and validation packet.")
    parser.add_argument("--lease-json", default=str(DEFAULT_LEASE_JSON))
    parser.add_argument("--report-dir", default=str(DEFAULT_REPORT_DIR))
    return parser


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def build_payload(lease_status: dict[str, Any]) -> dict[str, Any]:
    generated_at = datetime.now().astimezone().isoformat()
    gcs_option = next(
        option
        for option in lease_status.get("lease_options", [])
        if option.get("name") == "gcs_generation_match_lease"
    )
    implementation_shape = gcs_option["implementation_shape"]

    lease_schema = {
        "version": 1,
        "lease_kind": "paper_execution",
        "owner_id": "string",
        "owner_label": "string",
        "machine_label": "string",
        "runner_path": "string",
        "git_commit": "string",
        "acquired_at": "RFC3339 timestamp",
        "heartbeat_at": "RFC3339 timestamp",
        "expires_at": "RFC3339 timestamp",
        "generation": "storage generation returned by GCS, tracked by the caller but not trusted inside the object body",
        "roles": {
            "<role_name>": {
                "heartbeat_at": "RFC3339 timestamp",
                "expires_at": "RFC3339 timestamp",
                "pid": "string or null",
                "metadata": "object with role-specific context",
            }
        },
        "audit_context": {
            "plane": "execution|research|operator",
            "environment": "paper|validation|dry_run",
            "source": "workstation|vm|workflow",
        },
    }

    compatibility_mapping = [
        {
            "current_file_lease_field": "owner_id",
            "cloud_lease_field": "owner_id",
            "decision": "preserve",
            "rationale": "Existing runner logic already uses owner_id as the core holder identity.",
        },
        {
            "current_file_lease_field": "owner_label",
            "cloud_lease_field": "owner_label",
            "decision": "preserve",
            "rationale": "Useful for operator visibility and debugging across machines.",
        },
        {
            "current_file_lease_field": "heartbeat_at",
            "cloud_lease_field": "heartbeat_at",
            "decision": "preserve",
            "rationale": "Needed for liveness inspection and stale-lease analysis.",
        },
        {
            "current_file_lease_field": "expires_at",
            "cloud_lease_field": "expires_at",
            "decision": "preserve",
            "rationale": "TTL-based fail-closed behavior already exists conceptually and should remain first-class.",
        },
        {
            "current_file_lease_field": "roles",
            "cloud_lease_field": "roles",
            "decision": "preserve",
            "rationale": "Allows one holder to describe role-scoped subclaims without inventing a second coordination model.",
        },
        {
            "current_file_lease_field": "(new)",
            "cloud_lease_field": "machine_label",
            "decision": "add",
            "rationale": "Explicit machine_label improves cross-machine debugging and aligns with current runtime env conventions.",
        },
        {
            "current_file_lease_field": "(new)",
            "cloud_lease_field": "runner_path",
            "decision": "add",
            "rationale": "Needed to distinguish workstation, VM, and future workflow execution paths.",
        },
        {
            "current_file_lease_field": "(new)",
            "cloud_lease_field": "git_commit",
            "decision": "add",
            "rationale": "Supports forensic traceability between lease holder and code revision.",
        },
        {
            "current_file_lease_field": "(new)",
            "cloud_lease_field": "audit_context",
            "decision": "add",
            "rationale": "Supports future cloud-native audit packets and differentiated control handling.",
        },
    ]

    operation_contract = {
        "acquire": {
            "mechanism": "GCS object create with ifGenerationMatch=0",
            "success_condition": "object did not previously exist and caller becomes the sole current holder",
            "failure_condition": "precondition failure if object already exists",
        },
        "renew": {
            "mechanism": "GCS object rewrite with ifGenerationMatch=<last_seen_generation>",
            "success_condition": "caller still owns the current generation and extends heartbeat/expires_at",
            "failure_condition": "precondition failure if another holder replaced or stole the lease",
        },
        "release": {
            "mechanism": "GCS object delete with ifGenerationMatch=<last_seen_generation>",
            "success_condition": "lease removed only by the current holder",
            "failure_condition": "precondition failure if generation has changed",
        },
        "steal_after_expiry": {
            "mechanism": "read current object, verify expiry, then rewrite with ifGenerationMatch=<expired_generation>",
            "success_condition": "expired lease is replaced atomically by the new holder",
            "failure_condition": "precondition failure if another actor renewed or stole first",
        },
    }

    validation_matrix = [
        "Acquire succeeds when no lease object exists.",
        "Concurrent acquire attempts result in exactly one success and one precondition failure.",
        "Renew succeeds for the current holder and bumps heartbeat/expires_at.",
        "Renew fails when the caller uses a stale generation.",
        "Release succeeds only for the current holder generation.",
        "Release fails for a stale generation.",
        "Steal after expiry succeeds only when the observed generation still matches the expired lease.",
        "Steal after expiry fails if the original holder renewed before the replace.",
        "Audit artifact is written for acquire, renew, release, and steal events.",
        "Dry-run mode exercises the state machine without enabling broker-facing execution.",
    ]

    rollout_steps = [
        "Publish the lease contract and validation matrix.",
        "Implement helper functions in the sanctioned runner code paths without enforcing them yet.",
        "Add dry-run tests for contention, stale renewal, release mismatch, and expired steal.",
        "Enable audit artifact emission for every lease transition.",
        "Turn on enforcement only after dry-run validation is green on both workstation and VM paths.",
    ]

    return {
        "generated_at": generated_at,
        "project_id": lease_status.get("project_id", "codexalpaca"),
        "contract_readiness": "ready_for_helper_implementation",
        "recommended_lease": lease_status.get("recommended_lease"),
        "lease_object": implementation_shape["object"],
        "lease_schema": lease_schema,
        "compatibility_mapping": compatibility_mapping,
        "operation_contract": operation_contract,
        "validation_matrix": validation_matrix,
        "rollout_steps": rollout_steps,
        "code_alignment": {
            "current_ownership_module": "alpaca_lab/execution/ownership.py",
            "current_failover_module": "alpaca_lab/execution/failover.py",
            "current_example_config": "config/multi_ticker_paper_portfolio.yaml",
        },
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    lines: list[str] = []
    lines.append("# GCP Shared Execution Lease Contract")
    lines.append("")
    lines.append("## Snapshot")
    lines.append("")
    lines.append(f"- Generated at: `{payload['generated_at']}`")
    lines.append(f"- Project ID: `{payload['project_id']}`")
    lines.append(f"- Contract readiness: `{payload['contract_readiness']}`")
    lines.append(f"- Recommended lease: `{payload['recommended_lease']}`")
    lines.append(f"- Lease object: `{payload['lease_object']}`")
    lines.append("")
    lines.append("## Code Alignment")
    lines.append("")
    lines.append(f"- current ownership module: `{payload['code_alignment']['current_ownership_module']}`")
    lines.append(f"- current failover module: `{payload['code_alignment']['current_failover_module']}`")
    lines.append(f"- current example config: `{payload['code_alignment']['current_example_config']}`")
    lines.append("")
    lines.append("## Compatibility Mapping")
    lines.append("")
    for row in payload["compatibility_mapping"]:
        lines.append(f"- `{row['current_file_lease_field']}` -> `{row['cloud_lease_field']}`")
        lines.append(f"  - decision: `{row['decision']}`")
        lines.append(f"  - rationale: {row['rationale']}")
    lines.append("")
    lines.append("## Operation Contract")
    lines.append("")
    for name, item in payload["operation_contract"].items():
        lines.append(f"- `{name}`")
        lines.append(f"  - mechanism: {item['mechanism']}")
        lines.append(f"  - success: {item['success_condition']}")
        lines.append(f"  - failure: {item['failure_condition']}")
    lines.append("")
    lines.append("## Validation Matrix")
    lines.append("")
    for item in payload["validation_matrix"]:
        lines.append(f"- {item}")
    lines.append("")
    lines.append("## Rollout Steps")
    lines.append("")
    for item in payload["rollout_steps"]:
        lines.append(f"- {item}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_handoff(path: Path, payload: dict[str, Any]) -> None:
    lines: list[str] = []
    lines.append("# GCP Shared Execution Lease Contract Handoff")
    lines.append("")
    lines.append("## Current Read")
    lines.append("")
    lines.append("- The lease design is now implementation-ready.")
    lines.append("- The cloud lease should preserve the current ownership semantics instead of inventing a second coordination model.")
    lines.append("- The next step is helper implementation in the sanctioned runner paths with enforcement still off by default.")
    lines.append("")
    lines.append("## Key Rule")
    lines.append("")
    lines.append("- Preserve `owner_id`, `owner_label`, `heartbeat_at`, `expires_at`, and `roles` semantics from the current file lease.")
    lines.append("- Add `machine_label`, `runner_path`, and `git_commit` for cloud traceability.")
    lines.append("")
    lines.append("## Next Build Step")
    lines.append("")
    lines.append("- Implement `acquire`, `renew`, `release`, and `steal_after_expiry` helpers against GCS generation preconditions in dry-run mode first.")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    lease_status = load_json(Path(args.lease_json).resolve())
    payload = build_payload(lease_status)

    report_dir = Path(args.report_dir).resolve()
    write_json(report_dir / "gcp_shared_execution_lease_contract_status.json", payload)
    write_markdown(report_dir / "gcp_shared_execution_lease_contract_status.md", payload)
    write_handoff(report_dir / "gcp_shared_execution_lease_contract_handoff.md", payload)
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
