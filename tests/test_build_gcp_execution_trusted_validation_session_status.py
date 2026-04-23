from __future__ import annotations

import importlib.util
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "cleanroom"
    / "code"
    / "qqq_options_30d_cleanroom"
    / "build_gcp_execution_trusted_validation_session_status.py"
)
SPEC = importlib.util.spec_from_file_location(
    "build_gcp_execution_trusted_validation_session_status",
    MODULE_PATH,
)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_build_payload_blocks_when_lease_runtime_validation_not_green() -> None:
    payload = MODULE.build_payload(
        project_id="codexalpaca",
        vm_name="vm-execution-paper-01",
        access={"access_readiness": "ready_for_operator_validation"},
        validation_review={"review_state": "passed", "run_id": "headless-run"},
        runtime_security={"secret_results": [{"required": True, "seeded": True}]},
        runner_branch="codex/qqq-paper-portfolio",
        runner_commit="abc123",
        exclusive_window={"exclusive_window_status": "awaiting_operator_confirmation"},
        lease_runtime_validation={"runtime_validation_status": "dry_run_failed", "latest_run_id": "lease-run"},
    )

    assert payload["trusted_validation_readiness"] == "blocked"
    gate_statuses = {gate["name"]: gate["status"] for gate in payload["gate_checks"]}
    assert gate_statuses["shared_lease_dry_run_green"] == "blocked"


def test_build_payload_ready_for_manual_launch_when_window_and_lease_are_green() -> None:
    payload = MODULE.build_payload(
        project_id="codexalpaca",
        vm_name="vm-execution-paper-01",
        access={"access_readiness": "ready_for_operator_validation"},
        validation_review={"review_state": "passed", "run_id": "headless-run"},
        runtime_security={"secret_results": [{"required": True, "seeded": True}]},
        runner_branch="codex/qqq-paper-portfolio",
        runner_commit="abc123",
        exclusive_window={"exclusive_window_status": "ready_for_launch"},
        lease_runtime_validation={"runtime_validation_status": "validated_not_enforced", "latest_run_id": "lease-run"},
    )

    assert payload["trusted_validation_readiness"] == "ready_for_manual_launch"
    gate_statuses = {gate["name"]: gate["status"] for gate in payload["gate_checks"]}
    assert gate_statuses["shared_lease_dry_run_green"] == "passed"
    assert gate_statuses["exclusive_execution_window_confirmed"] == "passed"
