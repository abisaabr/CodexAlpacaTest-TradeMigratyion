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
        report_dir=tmp_path,
    )

    assert payload["status"] == "blocked"
    assert any(issue["code"] == "shared_execution_lease_enforced_too_early" for issue in payload["issues"])
