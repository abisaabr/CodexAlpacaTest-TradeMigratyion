from __future__ import annotations

import importlib.util
from datetime import datetime, timedelta, timezone
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "cleanroom"
    / "code"
    / "qqq_options_30d_cleanroom"
    / "build_gcp_execution_launch_authorization.py"
)
SPEC = importlib.util.spec_from_file_location("build_gcp_execution_launch_authorization", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


NOW = datetime(2026, 4, 24, 14, 0, tzinfo=timezone.utc)


def _clean_launch_surface_audit(minutes_old: int = 3) -> dict:
    return {
        "status": "local_broker_capable_surfaces_fenced_broker_flat",
        "generated_at": (NOW - timedelta(minutes=minutes_old)).isoformat(),
        "broker_state": {
            "read_only_check_after_fencing": "position_count=0, open_order_count=0",
            "broker_flat": True,
            "post_fencing_no_new_order_watch": {
                "watch_clean": True,
                "duration_seconds": 180,
                "position_count_all_samples": 0,
                "open_order_count_all_samples": 0,
                "newest_order_constant": True,
            },
        },
    }


def _ready_payload(tmp_path: Path) -> dict:
    return MODULE.build_payload(
        operator_packet={
            "operator_packet_state": "ready_to_launch_session",
            "vm_name": "vm-execution-paper-01",
            "closeout_command_template": "close-window",
        },
        launch_pack={
            "launch_pack_state": "ready_to_launch",
            "vm_name": "vm-execution-paper-01",
            "operator_ssh_command": "ssh-command",
            "vm_session_command": "run-session --submit-paper-orders",
            "post_session_assimilation_command": "assimilate",
            "required_evidence": ["broker-order audit"],
        },
        trusted_validation={"trusted_validation_readiness": "ready_for_manual_launch"},
        exclusive_window={"exclusive_window_status": "ready_for_launch"},
        closeout_status={"closeout_status": "ready_to_close_window"},
        runtime_readiness={
            "status": "runtime_ready",
            "trader_process_absent": True,
            "ownership_enabled": True,
            "ownership_backend": "file",
            "shared_execution_lease_enforced": False,
        },
        runner_provenance={"status": "provenance_matched"},
        source_fingerprint={"status": "source_fingerprint_matched"},
        prearm_preflight={
            "status": "ready_to_arm_window",
            "generated_at": (NOW - timedelta(minutes=3)).isoformat(),
        },
        launch_surface_audit=_clean_launch_surface_audit(),
        report_dir=tmp_path,
        max_prearm_age_minutes=20,
        now=NOW,
    )


def test_launch_authorization_ready_when_all_launch_gates_align(tmp_path: Path) -> None:
    payload = _ready_payload(tmp_path)

    assert payload["status"] == "ready_to_launch_session"
    assert payload["next_operator_action"] == "run_vm_session_command"
    assert payload["authorized_command_broker_facing"] is True
    assert payload["broker_facing"] is False
    assert payload["issues"] == []


def test_launch_authorization_blocks_before_window_is_armed(tmp_path: Path) -> None:
    payload = MODULE.build_payload(
        operator_packet={"operator_packet_state": "ready_to_arm_window", "vm_name": "vm-execution-paper-01"},
        launch_pack={
            "launch_pack_state": "awaiting_window_arm",
            "vm_name": "vm-execution-paper-01",
            "vm_session_command": "run-session --submit-paper-orders",
        },
        trusted_validation={"trusted_validation_readiness": "awaiting_exclusive_execution_window"},
        exclusive_window={"exclusive_window_status": "awaiting_operator_confirmation"},
        closeout_status={"closeout_status": "window_already_closed"},
        runtime_readiness={
            "status": "runtime_ready",
            "trader_process_absent": True,
            "ownership_enabled": True,
            "ownership_backend": "file",
            "shared_execution_lease_enforced": False,
        },
        runner_provenance={"status": "provenance_matched"},
        source_fingerprint={"status": "source_fingerprint_matched"},
        prearm_preflight={
            "status": "ready_to_arm_window",
            "generated_at": (NOW - timedelta(minutes=3)).isoformat(),
        },
        launch_surface_audit=_clean_launch_surface_audit(),
        report_dir=tmp_path,
        max_prearm_age_minutes=20,
        now=NOW,
    )

    assert payload["status"] == "blocked"
    assert any(issue["code"] == "exclusive_window_not_ready" for issue in payload["issues"])
    assert any(issue["code"] == "launch_pack_not_ready" for issue in payload["issues"])


def test_launch_authorization_blocks_when_prearm_preflight_is_stale(tmp_path: Path) -> None:
    payload = _ready_payload(tmp_path)
    payload = MODULE.build_payload(
        operator_packet={
            "operator_packet_state": "ready_to_launch_session",
            "vm_name": "vm-execution-paper-01",
        },
        launch_pack={
            "launch_pack_state": "ready_to_launch",
            "vm_name": "vm-execution-paper-01",
            "vm_session_command": "run-session --submit-paper-orders",
        },
        trusted_validation={"trusted_validation_readiness": "ready_for_manual_launch"},
        exclusive_window={"exclusive_window_status": "ready_for_launch"},
        closeout_status={"closeout_status": "ready_to_close_window"},
        runtime_readiness={
            "status": "runtime_ready",
            "trader_process_absent": True,
            "ownership_enabled": True,
            "ownership_backend": "file",
            "shared_execution_lease_enforced": False,
        },
        runner_provenance={"status": "provenance_matched"},
        source_fingerprint={"status": "source_fingerprint_matched"},
        prearm_preflight={
            "status": "ready_to_arm_window",
            "generated_at": (NOW - timedelta(minutes=25)).isoformat(),
        },
        launch_surface_audit=_clean_launch_surface_audit(),
        report_dir=tmp_path,
        max_prearm_age_minutes=20,
        now=NOW,
    )

    assert payload["status"] == "blocked"
    assert any(issue["code"] == "prearm_preflight_stale" for issue in payload["issues"])


def test_launch_authorization_blocks_when_session_command_is_not_explicit_submit(tmp_path: Path) -> None:
    payload = MODULE.build_payload(
        operator_packet={
            "operator_packet_state": "ready_to_launch_session",
            "vm_name": "vm-execution-paper-01",
        },
        launch_pack={
            "launch_pack_state": "ready_to_launch",
            "vm_name": "vm-execution-paper-01",
            "vm_session_command": "run-session",
        },
        trusted_validation={"trusted_validation_readiness": "ready_for_manual_launch"},
        exclusive_window={"exclusive_window_status": "ready_for_launch"},
        closeout_status={"closeout_status": "ready_to_close_window"},
        runtime_readiness={
            "status": "runtime_ready",
            "trader_process_absent": True,
            "ownership_enabled": True,
            "ownership_backend": "file",
            "shared_execution_lease_enforced": False,
        },
        runner_provenance={"status": "provenance_matched"},
        source_fingerprint={"status": "source_fingerprint_matched"},
        prearm_preflight={
            "status": "ready_to_arm_window",
            "generated_at": (NOW - timedelta(minutes=3)).isoformat(),
        },
        launch_surface_audit=_clean_launch_surface_audit(),
        report_dir=tmp_path,
        max_prearm_age_minutes=20,
        now=NOW,
    )

    assert payload["status"] == "blocked"
    assert any(issue["code"] == "session_command_missing_paper_submit_flag" for issue in payload["issues"])


def test_launch_authorization_blocks_when_launch_surface_audit_is_stale(tmp_path: Path) -> None:
    payload = MODULE.build_payload(
        operator_packet={
            "operator_packet_state": "ready_to_launch_session",
            "vm_name": "vm-execution-paper-01",
        },
        launch_pack={
            "launch_pack_state": "ready_to_launch",
            "vm_name": "vm-execution-paper-01",
            "vm_session_command": "run-session --submit-paper-orders",
        },
        trusted_validation={"trusted_validation_readiness": "ready_for_manual_launch"},
        exclusive_window={"exclusive_window_status": "ready_for_launch"},
        closeout_status={"closeout_status": "ready_to_close_window"},
        runtime_readiness={
            "status": "runtime_ready",
            "trader_process_absent": True,
            "ownership_enabled": True,
            "ownership_backend": "file",
            "shared_execution_lease_enforced": False,
        },
        runner_provenance={"status": "provenance_matched"},
        source_fingerprint={"status": "source_fingerprint_matched"},
        prearm_preflight={
            "status": "ready_to_arm_window",
            "generated_at": (NOW - timedelta(minutes=3)).isoformat(),
        },
        launch_surface_audit=_clean_launch_surface_audit(minutes_old=25),
        report_dir=tmp_path,
        max_prearm_age_minutes=20,
        now=NOW,
    )

    assert payload["status"] == "blocked"
    assert any(issue["code"] == "launch_surface_audit_stale" for issue in payload["issues"])


def test_launch_authorization_blocks_when_launch_surface_watch_is_not_clean(tmp_path: Path) -> None:
    launch_surface_audit = _clean_launch_surface_audit()
    launch_surface_audit["broker_state"]["post_fencing_no_new_order_watch"][
        "newest_order_constant"
    ] = False
    payload = MODULE.build_payload(
        operator_packet={
            "operator_packet_state": "ready_to_launch_session",
            "vm_name": "vm-execution-paper-01",
        },
        launch_pack={
            "launch_pack_state": "ready_to_launch",
            "vm_name": "vm-execution-paper-01",
            "vm_session_command": "run-session --submit-paper-orders",
        },
        trusted_validation={"trusted_validation_readiness": "ready_for_manual_launch"},
        exclusive_window={"exclusive_window_status": "ready_for_launch"},
        closeout_status={"closeout_status": "ready_to_close_window"},
        runtime_readiness={
            "status": "runtime_ready",
            "trader_process_absent": True,
            "ownership_enabled": True,
            "ownership_backend": "file",
            "shared_execution_lease_enforced": False,
        },
        runner_provenance={"status": "provenance_matched"},
        source_fingerprint={"status": "source_fingerprint_matched"},
        prearm_preflight={
            "status": "ready_to_arm_window",
            "generated_at": (NOW - timedelta(minutes=3)).isoformat(),
        },
        launch_surface_audit=launch_surface_audit,
        report_dir=tmp_path,
        max_prearm_age_minutes=20,
        now=NOW,
    )

    assert payload["status"] == "blocked"
    assert any(
        issue["code"] == "launch_surface_no_new_order_watch_not_clean"
        for issue in payload["issues"]
    )
