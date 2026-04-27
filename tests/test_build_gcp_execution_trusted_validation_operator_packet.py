from __future__ import annotations

import importlib.util
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "cleanroom"
    / "code"
    / "qqq_options_30d_cleanroom"
    / "build_gcp_execution_trusted_validation_operator_packet.py"
)
SPEC = importlib.util.spec_from_file_location(
    "build_gcp_execution_trusted_validation_operator_packet",
    MODULE_PATH,
)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def _clean_launch_surface_audit() -> dict:
    return {
        "status": "local_broker_capable_surfaces_fenced_broker_flat",
        "broker_state": {
            "read_only_check_after_fencing": "position_count=0, open_order_count=0",
            "post_fencing_no_new_order_watch": {
                "duration_seconds": 180,
                "position_count_all_samples": 0,
                "open_order_count_all_samples": 0,
            },
        },
    }


def _clean_startup_preflight() -> dict:
    return {
        "status": "startup_preflight_passed",
        "blocks_launch": False,
        "startup_check_status": "passed",
        "broker_position_count": 0,
        "open_order_count": 0,
        "failures": [],
    }


def test_build_payload_ready_to_arm_window_when_all_prelaunch_gates_align() -> None:
    payload = MODULE.build_payload(
        project_id="codexalpaca",
        vm_name="vm-execution-paper-01",
        zone="us-east1-b",
        gcs_prefix="gs://codexalpaca-control-us/gcp_foundation",
        exclusive_window={
            "exclusive_window_status": "awaiting_operator_confirmation",
        },
        trusted_validation={
            "trusted_validation_readiness": "awaiting_exclusive_execution_window",
            "runner_branch": "codex/qqq-paper-portfolio",
            "runner_commit": "abc123",
            "required_evidence": ["broker-order audit"],
        },
        launch_pack={
            "launch_pack_state": "awaiting_window_arm",
            "operator_ssh_command": "ssh-command",
            "vm_session_command": "vm-command",
            "post_session_assimilation_command": "assimilation-command",
            "review_targets": ["docs/morning_brief/morning_operator_brief.md"],
        },
        closeout_status={
            "closeout_status": "window_already_closed",
        },
        runner_provenance={
            "status": "provenance_unstamped",
            "source_fingerprint_status": "source_fingerprint_mismatch",
            "issues": [{"code": "vm_runner_commit_unstamped"}],
        },
        runtime_readiness={
            "status": "runtime_ready",
        },
        launch_surface_audit=_clean_launch_surface_audit(),
        startup_preflight=_clean_startup_preflight(),
    )

    assert payload["operator_packet_state"] == "ready_to_arm_window"
    assert "<control-plane-root>" in payload["arm_window_command_template"]
    assert payload["closeout_command_template"].endswith('-MirrorToGcs')
    assert payload["runner_provenance_status"] == "provenance_unstamped"
    assert "vm_runner_commit_unstamped" in payload["runner_provenance_issue_codes"]
    assert "docs/gcp_foundation/gcp_vm_runner_provenance_handoff.md" in payload["review_targets"]
    assert "docs/gcp_foundation/gcp_vm_runner_source_fingerprint_handoff.md" in payload["review_targets"]
    assert "docs/gcp_foundation/gcp_vm_runtime_readiness_handoff.md" in payload["review_targets"]
    assert "docs/gcp_foundation/gcp_execution_launch_authorization_handoff.md" in payload["review_targets"]
    assert "docs/gcp_foundation/gcp_execution_session_completion_gate_handoff.md" in payload["review_targets"]
    assert "docs/gcp_foundation/gcp_execution_launch_surface_audit_handoff.md" in payload["review_targets"]
    assert "docs/gcp_foundation/gcp_execution_startup_preflight_handoff.md" in payload["review_targets"]
    assert payload["launch_surface_audit_blocks_launch"] is False
    assert payload["startup_preflight_blocks_launch"] is False


def test_build_payload_ready_to_launch_session_after_window_is_armed() -> None:
    payload = MODULE.build_payload(
        project_id="codexalpaca",
        vm_name="vm-execution-paper-01",
        zone="us-east1-b",
        gcs_prefix="gs://codexalpaca-control-us/gcp_foundation",
        exclusive_window={
            "exclusive_window_status": "ready_for_launch",
        },
        trusted_validation={
            "trusted_validation_readiness": "ready_for_manual_launch",
            "runner_branch": "codex/qqq-paper-portfolio",
            "runner_commit": "abc123",
        },
        launch_pack={
            "launch_pack_state": "ready_to_launch",
        },
        closeout_status={
            "closeout_status": "ready_to_close_window",
        },
        launch_surface_audit=_clean_launch_surface_audit(),
        startup_preflight=_clean_startup_preflight(),
    )

    assert payload["operator_packet_state"] == "ready_to_launch_session"


def test_build_payload_blocks_launch_when_runtime_readiness_blocks() -> None:
    payload = MODULE.build_payload(
        project_id="codexalpaca",
        vm_name="vm-execution-paper-01",
        zone="us-east1-b",
        gcs_prefix="gs://codexalpaca-control-us/gcp_foundation",
        exclusive_window={
            "exclusive_window_status": "ready_for_launch",
        },
        trusted_validation={
            "trusted_validation_readiness": "ready_for_manual_launch",
            "runner_branch": "codex/qqq-paper-portfolio",
            "runner_commit": "abc123",
        },
        launch_pack={
            "launch_pack_state": "ready_to_launch",
        },
        closeout_status={
            "closeout_status": "ready_to_close_window",
        },
        runner_provenance={
            "status": "provenance_matched",
        },
        runtime_readiness={
            "status": "blocked_vm_runtime_readiness",
        },
        launch_surface_audit=_clean_launch_surface_audit(),
        startup_preflight=_clean_startup_preflight(),
    )

    assert payload["operator_packet_state"] == "blocked"
    assert payload["runtime_readiness_blocks_launch"] is True


def test_build_payload_blocks_launch_when_runner_provenance_blocks() -> None:
    payload = MODULE.build_payload(
        project_id="codexalpaca",
        vm_name="vm-execution-paper-01",
        zone="us-east1-b",
        gcs_prefix="gs://codexalpaca-control-us/gcp_foundation",
        exclusive_window={
            "exclusive_window_status": "ready_for_launch",
        },
        trusted_validation={
            "trusted_validation_readiness": "ready_for_manual_launch",
            "runner_branch": "codex/qqq-paper-portfolio",
            "runner_commit": "abc123",
        },
        launch_pack={
            "launch_pack_state": "ready_to_launch",
        },
        closeout_status={
            "closeout_status": "ready_to_close_window",
        },
        runner_provenance={
            "status": "blocked_vm_runner_source_mismatch",
            "issues": [{"code": "vm_runner_source_fingerprint_mismatch"}],
        },
        launch_surface_audit=_clean_launch_surface_audit(),
        startup_preflight=_clean_startup_preflight(),
    )

    assert payload["operator_packet_state"] == "blocked"
    assert payload["runner_provenance_blocks_launch"] is True
    assert "vm_runner_source_fingerprint_mismatch" in payload["runner_provenance_issue_codes"]


def test_build_payload_blocks_when_launch_surface_audit_is_missing() -> None:
    payload = MODULE.build_payload(
        project_id="codexalpaca",
        vm_name="vm-execution-paper-01",
        zone="us-east1-b",
        gcs_prefix="gs://codexalpaca-control-us/gcp_foundation",
        exclusive_window={
            "exclusive_window_status": "awaiting_operator_confirmation",
        },
        trusted_validation={
            "trusted_validation_readiness": "awaiting_exclusive_execution_window",
            "runner_branch": "codex/qqq-paper-portfolio",
            "runner_commit": "abc123",
        },
        launch_pack={
            "launch_pack_state": "awaiting_window_arm",
        },
        closeout_status={
            "closeout_status": "window_already_closed",
        },
        runner_provenance={
            "status": "provenance_matched",
        },
        runtime_readiness={
            "status": "runtime_ready",
        },
        startup_preflight=_clean_startup_preflight(),
    )

    assert payload["operator_packet_state"] == "blocked"
    assert payload["launch_surface_audit_status"] == "missing"
    assert payload["launch_surface_audit_blocks_launch"] is True


def test_build_payload_blocks_when_startup_preflight_is_missing() -> None:
    payload = MODULE.build_payload(
        project_id="codexalpaca",
        vm_name="vm-execution-paper-01",
        zone="us-east1-b",
        gcs_prefix="gs://codexalpaca-control-us/gcp_foundation",
        exclusive_window={
            "exclusive_window_status": "awaiting_operator_confirmation",
        },
        trusted_validation={
            "trusted_validation_readiness": "awaiting_exclusive_execution_window",
            "runner_branch": "codex/qqq-paper-portfolio",
            "runner_commit": "abc123",
        },
        launch_pack={
            "launch_pack_state": "awaiting_window_arm",
        },
        closeout_status={
            "closeout_status": "window_already_closed",
        },
        runner_provenance={
            "status": "provenance_matched",
        },
        runtime_readiness={
            "status": "runtime_ready",
        },
        launch_surface_audit=_clean_launch_surface_audit(),
    )

    assert payload["operator_packet_state"] == "blocked"
    assert payload["startup_preflight_status"] == "missing"
    assert payload["startup_preflight_blocks_launch"] is True


def test_build_payload_blocks_when_startup_preflight_failed() -> None:
    payload = MODULE.build_payload(
        project_id="codexalpaca",
        vm_name="vm-execution-paper-01",
        zone="us-east1-b",
        gcs_prefix="gs://codexalpaca-control-us/gcp_foundation",
        exclusive_window={
            "exclusive_window_status": "awaiting_operator_confirmation",
        },
        trusted_validation={
            "trusted_validation_readiness": "awaiting_exclusive_execution_window",
            "runner_branch": "codex/qqq-paper-portfolio",
            "runner_commit": "abc123",
        },
        launch_pack={
            "launch_pack_state": "awaiting_window_arm",
        },
        closeout_status={
            "closeout_status": "window_already_closed",
        },
        runner_provenance={
            "status": "provenance_matched",
        },
        runtime_readiness={
            "status": "runtime_ready",
        },
        launch_surface_audit=_clean_launch_surface_audit(),
        startup_preflight={
            "status": "startup_preflight_blocked",
            "blocks_launch": True,
            "startup_check_status": "failed",
            "broker_position_count": 0,
            "open_order_count": 0,
            "failures": ["IWM stock data stale at 189s"],
        },
    )

    assert payload["operator_packet_state"] == "blocked"
    assert payload["startup_preflight_blocks_launch"] is True
    assert payload["startup_preflight_failures"] == ["IWM stock data stale at 189s"]
