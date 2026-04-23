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
    now = datetime.fromisoformat("2026-04-23T16:30:00-04:00")
    template = MODULE.build_attestation_template(
        current_time=now,
        vm_name="vm-execution-paper-01",
        template_window_minutes=45,
    )

    assert template["window_starts_at"] == now.isoformat()
    assert template["window_expires_at"] == (now + timedelta(minutes=45)).isoformat()


def test_normalize_attestation_active_window() -> None:
    now = datetime.fromisoformat("2026-04-23T16:30:00-04:00")
    attestation = {
        "confirmed_by": "operator@example.com",
        "confirmed_at": now.isoformat(),
        "window_starts_at": (now - timedelta(minutes=5)).isoformat(),
        "window_expires_at": (now + timedelta(minutes=20)).isoformat(),
        "scope": "paper_account_single_writer",
        "target_vm_name": "vm-execution-paper-01",
        "assertions": {
            "no_other_machine_active": True,
            "parallel_exception_path_not_running_broker_session": True,
            "session_starts_only_on_sanctioned_vm": True,
            "post_session_assimilation_reserved": True,
        },
    }

    window_state, _, errors = MODULE.normalize_attestation(attestation, "vm-execution-paper-01", now=now)
    assert window_state == "confirmed_active_window"
    assert errors == []


def test_normalize_attestation_blocks_equal_start_and_expiry() -> None:
    now = datetime.fromisoformat("2026-04-23T16:30:00-04:00")
    attestation = {
        "confirmed_by": "operator@example.com",
        "confirmed_at": now.isoformat(),
        "window_starts_at": now.isoformat(),
        "window_expires_at": now.isoformat(),
        "scope": "paper_account_single_writer",
        "target_vm_name": "vm-execution-paper-01",
        "assertions": {
            "no_other_machine_active": True,
            "parallel_exception_path_not_running_broker_session": True,
            "session_starts_only_on_sanctioned_vm": True,
            "post_session_assimilation_reserved": True,
        },
    }

    window_state, _, errors = MODULE.normalize_attestation(attestation, "vm-execution-paper-01", now=now)
    assert window_state == "invalid_attestation"
    assert "`window_expires_at` must be later than `window_starts_at`." in errors


def test_build_payload_marks_active_window_ready_to_launch() -> None:
    now = datetime.fromisoformat("2026-04-23T16:30:00-04:00")
    attestation = {
        "confirmed_by": "operator@example.com",
        "confirmed_at": now.isoformat(),
        "window_starts_at": (now - timedelta(minutes=1)).isoformat(),
        "window_expires_at": (now + timedelta(minutes=30)).isoformat(),
        "scope": "paper_account_single_writer",
        "target_vm_name": "vm-execution-paper-01",
        "assertions": {
            "no_other_machine_active": True,
            "parallel_exception_path_not_running_broker_session": True,
            "session_starts_only_on_sanctioned_vm": True,
            "post_session_assimilation_reserved": True,
        },
    }
    payload = MODULE.build_payload(
        project_id="codexalpaca",
        vm_name="vm-execution-paper-01",
        exception_state="active_temporary_exception",
        attestation_json_path=Path(r"C:\control\gcp_execution_exclusive_window_attestation.json"),
        attestation=attestation,
        now=now,
        template_window_minutes=45,
    )

    assert payload["exclusive_window_state"] == "confirmed_active_window"
    assert payload["exclusive_window_status"] == "ready_for_launch"
    assert payload["template_window_minutes"] == 45


def test_build_payload_defaults_to_repo_relative_attestation_path() -> None:
    now = datetime.fromisoformat("2026-04-23T16:30:00-04:00")
    payload = MODULE.build_payload(
        project_id="codexalpaca",
        vm_name="vm-execution-paper-01",
        exception_state="active_temporary_exception",
        attestation_json_path="docs/gcp_foundation/gcp_execution_exclusive_window_attestation.json",
        attestation={},
        now=now,
        template_window_minutes=45,
    )

    assert payload["exclusive_window_state"] == "awaiting_operator_attestation"
    assert payload["exclusive_window_status"] == "awaiting_operator_confirmation"
    assert payload["attestation_json_path"] == "docs/gcp_foundation/gcp_execution_exclusive_window_attestation.json"
