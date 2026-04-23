from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[2]
DEFAULT_REPORT_DIR = REPO_ROOT / "docs" / "gcp_foundation"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build the shared execution lease runtime validation status packet."
    )
    parser.add_argument("--report-dir", default=str(DEFAULT_REPORT_DIR))
    return parser


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_json_if_exists(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return read_json(path)


def build_payload(
    *,
    implementation_status: dict[str, Any],
    runtime_wiring_status: dict[str, Any],
    lease_validation_review: dict[str, Any] | None,
) -> dict[str, Any]:
    review_state = None if lease_validation_review is None else str(lease_validation_review.get("review_state"))
    if review_state == "passed":
        runtime_validation_status = "validated_not_enforced"
        next_step = {
            "name": "trusted_validation_session",
            "description": "Use the sanctioned VM in an explicitly exclusive paper window for the first broker-audited trusted validation session.",
        }
    elif review_state == "failed":
        runtime_validation_status = "dry_run_failed"
        next_step = {
            "name": "rerun_corrected_vm_dry_run_gcs_lease_validation",
            "description": "Repair the lease dry-run launch or runtime bundle and rerun the sanctioned VM validation before any broker-facing session.",
        }
    elif review_state == "pending":
        runtime_validation_status = "dry_run_in_progress"
        next_step = {
            "name": "await_vm_dry_run_gcs_lease_validation",
            "description": "Wait for the sanctioned VM lease dry-run artifacts to land and review them before changing execution posture.",
        }
    else:
        runtime_validation_status = "awaiting_dry_run_launch"
        next_step = {
            "name": "vm_dry_run_gcs_lease_validation",
            "description": "Run the sanctioned VM lease dry-run against the real GCS lease object before any broker-facing promotion decision.",
        }

    return {
        "generated_at": datetime.now().astimezone().isoformat(),
        "project_id": implementation_status.get("project_id", "codexalpaca"),
        "runtime_validation_phase": "foundation-phase17-lease-dry-run-validation",
        "runtime_validation_status": runtime_validation_status,
        "lease_live": False,
        "implementation_status": implementation_status.get("implementation_status"),
        "runtime_wiring_status": runtime_wiring_status.get("runtime_wiring_status"),
        "latest_review_state": review_state,
        "latest_run_id": None if lease_validation_review is None else lease_validation_review.get("run_id"),
        "latest_validation_result_gcs_prefix": None
        if lease_validation_review is None
        else lease_validation_review.get("validation_result_gcs_prefix"),
        "guardrails": [
            "Keep the default trader path on the file lease until the sanctioned VM dry-run is green and separately promoted.",
            "Do not widen the temporary parallel-runtime exception onto the cloud lease path.",
            "Do not treat the cloud shared execution lease as live from runtime validation alone.",
        ],
        "next_step": next_step,
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    lines: list[str] = []
    lines.append("# GCP Shared Execution Lease Runtime Validation")
    lines.append("")
    lines.append("## Snapshot")
    lines.append("")
    lines.append(f"- Generated at: `{payload['generated_at']}`")
    lines.append(f"- Project ID: `{payload['project_id']}`")
    lines.append(f"- Runtime validation phase: `{payload['runtime_validation_phase']}`")
    lines.append(f"- Runtime validation status: `{payload['runtime_validation_status']}`")
    lines.append(f"- Lease live: `{payload['lease_live']}`")
    lines.append(f"- Latest review state: `{payload['latest_review_state']}`")
    lines.append("")
    lines.append("## Inputs")
    lines.append("")
    lines.append(f"- Implementation status: `{payload['implementation_status']}`")
    lines.append(f"- Runtime wiring status: `{payload['runtime_wiring_status']}`")
    lines.append(f"- Latest run ID: `{payload['latest_run_id']}`")
    lines.append(f"- Latest result prefix: `{payload['latest_validation_result_gcs_prefix']}`")
    lines.append("")
    lines.append("## Guardrails")
    lines.append("")
    for item in list(payload.get("guardrails") or []):
        lines.append(f"- {item}")
    lines.append("")
    lines.append("## Next Step")
    lines.append("")
    lines.append(f"- Name: `{payload['next_step']['name']}`")
    lines.append(f"- {payload['next_step']['description']}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_handoff(path: Path, payload: dict[str, Any]) -> None:
    lines: list[str] = []
    lines.append("# GCP Shared Execution Lease Runtime Validation Handoff")
    lines.append("")
    lines.append("## Current Read")
    lines.append("")
    lines.append(f"- Runtime validation status: `{payload['runtime_validation_status']}`.")
    lines.append(f"- Latest review state: `{payload['latest_review_state']}`.")
    lines.append("- The cloud shared execution lease is still off by default.")
    lines.append("")
    lines.append("## Operator Rule")
    lines.append("")
    lines.append("- Treat runtime validation as a governance gate, not as automatic permission to switch the trader onto the cloud lease.")
    lines.append("- Keep broker-facing execution on the sanctioned path only after the dry-run and trusted-session gates are both clean.")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = build_parser().parse_args()
    report_dir = Path(args.report_dir).resolve()
    payload = build_payload(
        implementation_status=read_json(report_dir / "gcp_shared_execution_lease_implementation_status.json"),
        runtime_wiring_status=read_json(report_dir / "gcp_shared_execution_lease_runtime_wiring_status.json"),
        lease_validation_review=read_json_if_exists(
            report_dir / "gcp_execution_vm_lease_dry_run_validation_review_status.json"
        ),
    )
    write_json(report_dir / "gcp_shared_execution_lease_runtime_validation_status.json", payload)
    write_markdown(report_dir / "gcp_shared_execution_lease_runtime_validation_status.md", payload)
    write_handoff(report_dir / "gcp_shared_execution_lease_runtime_validation_handoff.md", payload)
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
