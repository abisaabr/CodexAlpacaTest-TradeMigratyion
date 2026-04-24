from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = (
    REPO_ROOT
    / "cleanroom"
    / "code"
    / "qqq_options_30d_cleanroom"
    / "launch_gcp_execution_prearm_preflight.ps1"
)


def test_prearm_launcher_rebuilds_and_mirrors_launch_authorization() -> None:
    script = SCRIPT_PATH.read_text(encoding="utf-8-sig")

    prearm_build = script.index("build_gcp_execution_prearm_preflight.py")
    launch_authorization_build = script.index("build_gcp_execution_launch_authorization.py")

    assert launch_authorization_build > prearm_build
    assert '"gcp_execution_launch_authorization.json"' in script
    assert '"gcp_execution_launch_authorization.md"' in script
    assert '"gcp_execution_launch_authorization_handoff.md"' in script
