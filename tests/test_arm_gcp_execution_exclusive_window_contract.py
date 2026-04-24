from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = (
    REPO_ROOT
    / "cleanroom"
    / "code"
    / "qqq_options_30d_cleanroom"
    / "arm_gcp_execution_exclusive_window.ps1"
)


def test_arm_script_requires_fresh_ready_prearm_preflight_before_attestation() -> None:
    script = SCRIPT_PATH.read_text(encoding="utf-8")
    prearm_check = script.index("Assert-PrearmPreflightReady")
    attestation_write = script.index("$attestation | ConvertTo-Json")

    assert prearm_check < attestation_write
    assert "gcp_execution_prearm_preflight.json" in script
    assert "MaxPrearmAgeMinutes" in script
    assert "ready_to_arm_window" in script
    assert "arm_bounded_exclusive_window" in script
    assert "provenance_matched" in script
    assert "source_fingerprint_matched" in script
    assert "runtime_ready" in script
    assert "launch_surface_audit_status" in script
    assert "local_broker_capable_surfaces_fenced_broker_flat" in script
    assert "launch_surface_broker_flat" in script
    assert "launch_surface_no_new_order_watch_clean" in script
    assert "launch_surface_newest_order_constant" in script
    assert "launch_surface_watch_duration_seconds" in script
    assert "FileOwnershipLease" in script
    assert "shared_execution_lease_enforced" in script


def test_arm_script_refreshes_top_level_packets_after_arming() -> None:
    script = SCRIPT_PATH.read_text(encoding="utf-8")

    assert "build_gcp_execution_closeout_status.py" in script
    assert "build_gcp_execution_trusted_validation_operator_packet.py" in script
    assert "build_gcp_execution_launch_authorization.py" in script
    assert "gcp_execution_trusted_validation_operator_handoff.md" in script
    assert "gcp_execution_launch_authorization_handoff.md" in script
    assert "gcp_execution_closeout_handoff.md" in script
    assert "gcp_execution_prearm_preflight_handoff.md" in script
    assert "gcp_execution_launch_surface_audit_handoff.md" in script
    assert "gcp_execution_launch_surface_broker_watch_observed.json" in script
