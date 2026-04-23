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
    )

    assert payload["operator_packet_state"] == "ready_to_arm_window"
    assert "<control-plane-root>" in payload["arm_window_command_template"]
    assert payload["closeout_command_template"].endswith('-MirrorToGcs')


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
    )

    assert payload["operator_packet_state"] == "ready_to_launch_session"
