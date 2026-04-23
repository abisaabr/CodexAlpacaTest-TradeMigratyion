from __future__ import annotations

import importlib.util
from datetime import datetime, timedelta
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "cleanroom"
    / "code"
    / "qqq_options_30d_cleanroom"
    / "build_gcp_execution_exclusive_window_status.py"
)
SPEC = importlib.util.spec_from_file_location(
    "build_gcp_execution_exclusive_window_status",
    MODULE_PATH,
)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_build_attestation_template_uses_bounded_future_window() -> None:
    current_time = datetime.fromisoformat("2026-04-23T16:30:00-04:00")
    template = MODULE.build_attestation_template(
        current_time=current_time,
        vm_name="vm-execution-paper-01",
        template_window_minutes=45,
    )

    assert template["window_starts_at"] == current_time.isoformat()
    assert template["window_expires_at"] == (current_time + timedelta(minutes=45)).isoformat()


def test_build_payload_defaults_to_operator_confirmation_without_attestation() -> None:
    current_time = datetime.fromisoformat("2026-04-23T16:30:00-04:00")
    payload = MODULE.build_payload(
        project_id="codexalpaca",
        vm_name="vm-execution-paper-01",
        exception_status={"exception_state": "temporary_exception"},
        attestation={},
        attestation_relpath="docs/gcp_foundation/gcp_execution_exclusive_window_attestation.json",
        current_time=current_time,
        template_window_minutes=45,
    )

    assert payload["exclusive_window_state"] == "awaiting_operator_attestation"
    assert payload["exclusive_window_status"] == "awaiting_operator_confirmation"
    assert payload["attestation_json_path"] == "docs/gcp_foundation/gcp_execution_exclusive_window_attestation.json"
    assert payload["attestation_present"] is False
    assert payload["template_window_minutes"] == 45


def test_normalize_attestation_rejects_equal_start_and_expiry() -> None:
    current_time = datetime.fromisoformat("2026-04-23T16:30:00-04:00")
    attestation = {
        "confirmed_by": "operator@example.com",
        "confirmed_at": current_time.isoformat(),
        "window_starts_at": current_time.isoformat(),
        "window_expires_at": current_time.isoformat(),
        "scope": "paper_account_single_writer",
        "target_vm_name": "vm-execution-paper-01",
        "assertions": {
            "no_other_machine_active": True,
            "parallel_exception_path_not_running_broker_session": True,
            "session_starts_only_on_sanctioned_vm": True,
            "post_session_assimilation_reserved": True,
        },
    }

    window_state, _, errors = MODULE.normalize_attestation(
        attestation,
        "vm-execution-paper-01",
        current_time=current_time,
    )

    assert window_state == "invalid_attestation"
    assert "`window_expires_at` must be later than `window_starts_at`." in errors


def test_build_payload_marks_active_window_ready_for_launch() -> None:
    current_time = datetime.fromisoformat("2026-04-23T16:30:00-04:00")
    payload = MODULE.build_payload(
        project_id="codexalpaca",
        vm_name="vm-execution-paper-01",
        exception_status={"exception_state": "temporary_exception"},
        attestation={
            "window_id": "trusted-validation-session-vm-execution-paper-01",
            "confirmed_by": "user@example.com",
            "confirmed_at": (current_time - timedelta(minutes=2)).isoformat(),
            "window_starts_at": (current_time - timedelta(minutes=1)).isoformat(),
            "window_expires_at": (current_time + timedelta(minutes=20)).isoformat(),
            "target_vm_name": "vm-execution-paper-01",
            "scope": "paper_account_single_writer",
            "assertions": {
                "no_other_machine_active": True,
                "parallel_exception_path_not_running_broker_session": True,
                "session_starts_only_on_sanctioned_vm": True,
                "post_session_assimilation_reserved": True,
            },
        },
        attestation_relpath="docs/gcp_foundation/gcp_execution_exclusive_window_attestation.json",
        current_time=current_time,
        template_window_minutes=45,
    )

    assert payload["exclusive_window_state"] == "confirmed_active_window"
    assert payload["exclusive_window_status"] == "ready_for_launch"
    assert payload["attestation_validation_errors"] == []
    assert payload["next_actions"][0] == "The exclusive execution window is active for `vm-execution-paper-01`."
