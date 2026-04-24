from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = REPO_ROOT / "cleanroom" / "code" / "qqq_options_30d_cleanroom"


def test_post_session_assimilation_script_fails_on_builder_errors_and_refreshes_completion_gate() -> None:
    script = (SCRIPT_DIR / "launch_post_session_assimilation.ps1").read_text(encoding="utf-8")

    assert "$LASTEXITCODE -ne 0" in script
    assert "build_gcp_execution_closeout_status.py" in script
    assert "build_gcp_execution_session_completion_gate.py" in script
    assert "gcp_execution_session_completion_gate_handoff.md" in script
    assert "gcp_execution_launch_authorization_handoff.md" in script
    assert "gcp_execution_trusted_validation_operator_handoff.md" in script


def test_close_window_script_refreshes_final_operator_and_completion_state() -> None:
    script = (SCRIPT_DIR / "close_gcp_execution_exclusive_window.ps1").read_text(encoding="utf-8")

    assert "$LASTEXITCODE -ne 0" in script
    assert "build_gcp_execution_session_completion_gate.py" in script
    assert "build_gcp_execution_trusted_validation_operator_packet.py" in script
    assert "build_gcp_execution_launch_authorization.py" in script
    assert "gcp_execution_session_completion_gate_handoff.md" in script
    assert "gcp_execution_launch_authorization_handoff.md" in script
    assert "gcp_execution_trusted_validation_operator_handoff.md" in script
