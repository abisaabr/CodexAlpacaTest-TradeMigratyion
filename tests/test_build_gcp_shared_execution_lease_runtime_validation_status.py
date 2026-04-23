from __future__ import annotations

import importlib.util
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "cleanroom"
    / "code"
    / "qqq_options_30d_cleanroom"
    / "build_gcp_shared_execution_lease_runtime_validation_status.py"
)
SPEC = importlib.util.spec_from_file_location(
    "build_gcp_shared_execution_lease_runtime_validation_status",
    MODULE_PATH,
)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_build_payload_marks_failed_runtime_validation() -> None:
    payload = MODULE.build_payload(
        implementation_status={"project_id": "codexalpaca", "implementation_status": "optional_gcs_store_wiring_landed_not_validated"},
        runtime_wiring_status={"runtime_wiring_status": "optional_backend_wired_not_enforced"},
        lease_validation_review={"review_state": "failed", "run_id": "run-1", "validation_result_gcs_prefix": "gs://bucket/prefix"},
    )

    assert payload["runtime_validation_status"] == "dry_run_failed"
    assert payload["next_step"]["name"] == "rerun_corrected_vm_dry_run_gcs_lease_validation"


def test_build_payload_marks_validated_not_enforced() -> None:
    payload = MODULE.build_payload(
        implementation_status={"project_id": "codexalpaca", "implementation_status": "optional_gcs_store_wiring_landed_not_validated"},
        runtime_wiring_status={"runtime_wiring_status": "optional_backend_wired_not_enforced"},
        lease_validation_review={"review_state": "passed", "run_id": "run-2", "validation_result_gcs_prefix": "gs://bucket/prefix"},
    )

    assert payload["runtime_validation_status"] == "validated_not_enforced"
    assert payload["next_step"]["name"] == "trusted_validation_session"
