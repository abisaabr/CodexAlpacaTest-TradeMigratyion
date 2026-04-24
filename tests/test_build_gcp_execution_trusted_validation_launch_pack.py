from __future__ import annotations

import importlib.util
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "cleanroom"
    / "code"
    / "qqq_options_30d_cleanroom"
    / "build_gcp_execution_trusted_validation_launch_pack.py"
)
SPEC = importlib.util.spec_from_file_location(
    "build_gcp_execution_trusted_validation_launch_pack",
    MODULE_PATH,
)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_build_payload_awaiting_window_arm_when_not_yet_confirmed() -> None:
    payload = MODULE.build_payload(
        project_id="codexalpaca",
        vm_name="vm-execution-paper-01",
        zone="us-east1-b",
        trusted_status={
            "trusted_validation_readiness": "awaiting_exclusive_execution_window",
            "runner_branch": "codex/qqq-paper-portfolio",
            "runner_commit": "abc123",
            "trusted_validation_session_command": "run-session",
            "required_evidence": ["broker-order audit"],
        },
        exclusive_window={
            "exclusive_window_state": "awaiting_operator_attestation",
            "exclusive_window_status": "awaiting_operator_confirmation",
        },
    )

    assert payload["launch_pack_state"] == "awaiting_window_arm"
    assert payload["runner_repo_root_hint"] == "<runner-repo-root>"
    assert payload["control_plane_root_hint"] == "<control-plane-root>"
    assert payload["operator_steps"][0].startswith("Do not start the session yet;")
    assert "<control-plane-root>" in payload["post_session_assimilation_command"]
    assert payload["review_targets"] == [
        "docs/morning_brief/morning_operator_brief.md",
        "docs/execution_calibration/execution_calibration_handoff.md",
        "docs/tournament_unlocks/tournament_unlock_handoff.md",
        "docs/execution_evidence/execution_evidence_contract_handoff.md",
        "docs/gcp_foundation/gcp_execution_launch_authorization_handoff.md",
    ]


def test_build_payload_ready_to_launch_when_window_and_session_are_green() -> None:
    payload = MODULE.build_payload(
        project_id="codexalpaca",
        vm_name="vm-execution-paper-01",
        zone="us-east1-b",
        trusted_status={
            "trusted_validation_readiness": "ready_for_manual_launch",
            "runner_branch": "codex/qqq-paper-portfolio",
            "runner_commit": "abc123",
            "trusted_validation_session_command": "run-session",
            "required_evidence": ["broker-order audit"],
            "latest_lease_runtime_validation_status": "validated_not_enforced",
            "latest_lease_validation_run_id": "lease-run",
        },
        exclusive_window={
            "exclusive_window_state": "confirmed_active_window",
            "exclusive_window_status": "ready_for_launch",
        },
    )

    assert payload["launch_pack_state"] == "ready_to_launch"
    assert payload["latest_lease_runtime_validation_status"] == "validated_not_enforced"
    assert not payload["operator_steps"][0].startswith("Do not start the session yet;")
    assert payload["operator_steps"][0] == (
        "Confirm the exclusive-window packet says `ready_for_launch` and this launch pack says `ready_to_launch`."
    )
    assert "ready_to_launch_session" in payload["operator_steps"][1]
