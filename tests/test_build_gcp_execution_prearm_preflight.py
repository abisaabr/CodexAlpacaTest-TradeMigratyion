from __future__ import annotations

import importlib.util
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "cleanroom"
    / "code"
    / "qqq_options_30d_cleanroom"
    / "build_gcp_execution_prearm_preflight.py"
)
SPEC = importlib.util.spec_from_file_location("build_gcp_execution_prearm_preflight", MODULE_PATH)
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
                "newest_order_constant": True,
            },
        },
    }


def _clean_startup_preflight() -> dict:
    return {
        "status": "startup_preflight_passed",
        "blocks_launch": False,
        "freshness_status": "fresh",
        "preflight_age_seconds": 30,
        "max_age_seconds": 600,
    }


def _ready_payload(tmp_path: Path) -> dict:
    return MODULE.build_payload(
        operator_packet={
            "operator_packet_state": "ready_to_arm_window",
            "vm_name": "vm-execution-paper-01",
            "arm_window_command_template": "arm-command",
        },
        runtime_readiness={
            "status": "runtime_ready",
            "trader_process_absent": True,
            "ownership_enabled": True,
            "ownership_backend": "file",
            "ownership_lease_class": "FileOwnershipLease",
            "shared_execution_lease_enforced": False,
        },
        runner_provenance={"status": "provenance_matched"},
        source_fingerprint={"status": "source_fingerprint_matched"},
        exclusive_window={"exclusive_window_status": "awaiting_operator_confirmation"},
        launch_pack={"launch_pack_state": "awaiting_window_arm"},
        launch_surface_audit=_clean_launch_surface_audit(),
        startup_preflight=_clean_startup_preflight(),
        report_dir=tmp_path,
    )


def test_prearm_preflight_ready_when_all_non_broker_gates_align(tmp_path: Path) -> None:
    payload = _ready_payload(tmp_path)

    assert payload["status"] == "ready_to_arm_window"
    assert payload["next_operator_action"] == "arm_bounded_exclusive_window"
    assert payload["vm_name"] == "vm-execution-paper-01"
    assert payload["issues"] == []
    assert payload["broker_facing"] is False
    assert payload["live_manifest_effect"] == "none"
    assert payload["risk_policy_effect"] == "none"


def test_prearm_preflight_blocks_when_operator_packet_is_not_ready(tmp_path: Path) -> None:
    payload = _ready_payload(tmp_path)
    payload = MODULE.build_payload(
        operator_packet={"operator_packet_state": "ready_to_launch_session"},
        runtime_readiness={
            "status": "runtime_ready",
            "trader_process_absent": True,
            "ownership_enabled": True,
            "ownership_backend": "file",
            "ownership_lease_class": "FileOwnershipLease",
            "shared_execution_lease_enforced": False,
        },
        runner_provenance={"status": "provenance_matched"},
        source_fingerprint={"status": "source_fingerprint_matched"},
        exclusive_window={"exclusive_window_status": "awaiting_operator_confirmation"},
        launch_pack={"launch_pack_state": "awaiting_window_arm"},
        launch_surface_audit=_clean_launch_surface_audit(),
        startup_preflight=_clean_startup_preflight(),
        report_dir=tmp_path,
    )

    assert payload["status"] == "blocked"
    assert any(issue["code"] == "operator_packet_not_ready_to_arm" for issue in payload["issues"])


def test_prearm_preflight_blocks_when_trader_process_is_not_clear(tmp_path: Path) -> None:
    payload = MODULE.build_payload(
        operator_packet={"operator_packet_state": "ready_to_arm_window"},
        runtime_readiness={
            "status": "runtime_ready",
            "trader_process_absent": False,
            "ownership_enabled": True,
            "ownership_backend": "file",
            "ownership_lease_class": "FileOwnershipLease",
            "shared_execution_lease_enforced": False,
        },
        runner_provenance={"status": "provenance_matched"},
        source_fingerprint={"status": "source_fingerprint_matched"},
        exclusive_window={"exclusive_window_status": "awaiting_operator_confirmation"},
        launch_pack={"launch_pack_state": "awaiting_window_arm"},
        launch_surface_audit=_clean_launch_surface_audit(),
        startup_preflight=_clean_startup_preflight(),
        report_dir=tmp_path,
    )

    assert payload["status"] == "blocked"
    assert any(issue["code"] == "trader_process_not_clear" for issue in payload["issues"])


def test_prearm_preflight_blocks_when_gcs_shared_lease_is_enforced_too_early(tmp_path: Path) -> None:
    payload = MODULE.build_payload(
        operator_packet={"operator_packet_state": "ready_to_arm_window"},
        runtime_readiness={
            "status": "runtime_ready",
            "trader_process_absent": True,
            "ownership_enabled": True,
            "ownership_backend": "gcs_generation_match",
            "ownership_lease_class": "GcsGenerationMatchOwnershipLease",
            "shared_execution_lease_enforced": True,
        },
        runner_provenance={"status": "provenance_matched"},
        source_fingerprint={"status": "source_fingerprint_matched"},
        exclusive_window={"exclusive_window_status": "awaiting_operator_confirmation"},
        launch_pack={"launch_pack_state": "awaiting_window_arm"},
        launch_surface_audit=_clean_launch_surface_audit(),
        startup_preflight=_clean_startup_preflight(),
        report_dir=tmp_path,
    )

    assert payload["status"] == "blocked"
    assert any(issue["code"] == "shared_execution_lease_enforced_too_early" for issue in payload["issues"])


def test_prearm_preflight_blocks_when_launch_surface_watch_is_not_clean(tmp_path: Path) -> None:
    audit = _clean_launch_surface_audit()
    audit["broker_state"]["post_fencing_no_new_order_watch"]["duration_seconds"] = 60
    payload = MODULE.build_payload(
        operator_packet={"operator_packet_state": "ready_to_arm_window"},
        runtime_readiness={
            "status": "runtime_ready",
            "trader_process_absent": True,
            "ownership_enabled": True,
            "ownership_backend": "file",
            "ownership_lease_class": "FileOwnershipLease",
            "shared_execution_lease_enforced": False,
        },
        runner_provenance={"status": "provenance_matched"},
        source_fingerprint={"status": "source_fingerprint_matched"},
        exclusive_window={"exclusive_window_status": "awaiting_operator_confirmation"},
        launch_pack={"launch_pack_state": "awaiting_window_arm"},
        launch_surface_audit=audit,
        startup_preflight=_clean_startup_preflight(),
        report_dir=tmp_path,
    )

    assert payload["status"] == "blocked"
    assert any(
        issue["code"] == "launch_surface_no_new_order_watch_not_clean"
        for issue in payload["issues"]
    )


def test_prearm_preflight_blocks_when_newest_order_timestamp_changes(tmp_path: Path) -> None:
    audit = _clean_launch_surface_audit()
    audit["broker_state"]["post_fencing_no_new_order_watch"]["newest_order_constant"] = False
    payload = MODULE.build_payload(
        operator_packet={"operator_packet_state": "ready_to_arm_window"},
        runtime_readiness={
            "status": "runtime_ready",
            "trader_process_absent": True,
            "ownership_enabled": True,
            "ownership_backend": "file",
            "ownership_lease_class": "FileOwnershipLease",
            "shared_execution_lease_enforced": False,
        },
        runner_provenance={"status": "provenance_matched"},
        source_fingerprint={"status": "source_fingerprint_matched"},
        exclusive_window={"exclusive_window_status": "awaiting_operator_confirmation"},
        launch_pack={"launch_pack_state": "awaiting_window_arm"},
        launch_surface_audit=audit,
        startup_preflight=_clean_startup_preflight(),
        report_dir=tmp_path,
    )

    assert payload["status"] == "blocked"
    assert payload["launch_surface_newest_order_constant"] is False
    assert any(
        issue["code"] == "launch_surface_no_new_order_watch_not_clean"
        for issue in payload["issues"]
    )


def test_prearm_preflight_blocks_when_startup_preflight_is_not_clean(tmp_path: Path) -> None:
    payload = MODULE.build_payload(
        operator_packet={"operator_packet_state": "blocked"},
        runtime_readiness={
            "status": "runtime_ready",
            "trader_process_absent": True,
            "ownership_enabled": True,
            "ownership_backend": "file",
            "ownership_lease_class": "FileOwnershipLease",
            "shared_execution_lease_enforced": False,
        },
        runner_provenance={"status": "provenance_matched"},
        source_fingerprint={"status": "source_fingerprint_matched"},
        exclusive_window={"exclusive_window_status": "awaiting_operator_confirmation"},
        launch_pack={"launch_pack_state": "awaiting_window_arm"},
        launch_surface_audit=_clean_launch_surface_audit(),
        startup_preflight={
            "status": "startup_preflight_blocked",
            "blocks_launch": True,
            "freshness_status": "fresh",
            "preflight_age_seconds": 60,
            "max_age_seconds": 600,
        },
        report_dir=tmp_path,
    )

    assert payload["status"] == "blocked"
    assert payload["startup_preflight_blocks_launch"] is True
    assert any(issue["code"] == "startup_preflight_not_clean" for issue in payload["issues"])
