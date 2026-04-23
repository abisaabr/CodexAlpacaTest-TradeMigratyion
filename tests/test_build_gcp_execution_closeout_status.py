from __future__ import annotations

import importlib.util
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "cleanroom"
    / "code"
    / "qqq_options_30d_cleanroom"
    / "build_gcp_execution_closeout_status.py"
)
SPEC = importlib.util.spec_from_file_location(
    "build_gcp_execution_closeout_status",
    MODULE_PATH,
)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_build_payload_ready_to_close_window_when_attestation_present_and_assimilation_ready(tmp_path: Path) -> None:
    report_dir = tmp_path / "gcp_foundation"
    report_dir.mkdir(parents=True)
    attestation_path = report_dir / "gcp_execution_exclusive_window_attestation.json"
    attestation_path.write_text("{}", encoding="utf-8")

    payload = MODULE.build_payload(
        report_dir=report_dir,
        vm_name="vm-execution-paper-01",
        gcs_prefix="gs://codexalpaca-control-us/gcp_foundation",
        exclusive_window_status={
            "attestation_json_path": str(attestation_path),
            "exclusive_window_state": "confirmed_active_window",
            "exclusive_window_status": "ready_for_launch",
        },
        trusted_validation_status={"trusted_validation_readiness": "ready_for_manual_launch"},
        launch_pack={"launch_pack_state": "ready_to_launch"},
        assimilation_status={"status": "ready_for_post_session_assimilation"},
    )

    assert payload["closeout_status"] == "ready_to_close_window"
    assert payload["attestation_present"] is True


def test_build_payload_window_already_closed_when_attestation_missing(tmp_path: Path) -> None:
    report_dir = tmp_path / "gcp_foundation"
    report_dir.mkdir(parents=True)
    attestation_path = report_dir / "gcp_execution_exclusive_window_attestation.json"

    payload = MODULE.build_payload(
        report_dir=report_dir,
        vm_name="vm-execution-paper-01",
        gcs_prefix="gs://codexalpaca-control-us/gcp_foundation",
        exclusive_window_status={
            "attestation_json_path": str(attestation_path),
            "exclusive_window_state": "awaiting_operator_attestation",
            "exclusive_window_status": "awaiting_operator_confirmation",
        },
        trusted_validation_status={"trusted_validation_readiness": "awaiting_exclusive_execution_window"},
        launch_pack={"launch_pack_state": "awaiting_window_arm"},
        assimilation_status={"status": "ready_for_post_session_assimilation"},
    )

    assert payload["closeout_status"] == "window_already_closed"
    assert payload["attestation_present"] is False


def test_build_payload_blocks_when_assimilation_not_ready(tmp_path: Path) -> None:
    report_dir = tmp_path / "gcp_foundation"
    report_dir.mkdir(parents=True)
    attestation_path = report_dir / "gcp_execution_exclusive_window_attestation.json"
    attestation_path.write_text("{}", encoding="utf-8")

    payload = MODULE.build_payload(
        report_dir=report_dir,
        vm_name="vm-execution-paper-01",
        gcs_prefix="gs://codexalpaca-control-us/gcp_foundation",
        exclusive_window_status={
            "attestation_json_path": str(attestation_path),
            "exclusive_window_state": "confirmed_active_window",
            "exclusive_window_status": "ready_for_launch",
        },
        trusted_validation_status={"trusted_validation_readiness": "ready_for_manual_launch"},
        launch_pack={"launch_pack_state": "ready_to_launch"},
        assimilation_status={"status": "blocked"},
    )

    assert payload["closeout_status"] == "blocked"
