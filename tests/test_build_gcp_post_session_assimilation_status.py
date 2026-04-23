from __future__ import annotations

import importlib.util
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "cleanroom"
    / "code"
    / "qqq_options_30d_cleanroom"
    / "build_gcp_post_session_assimilation_status.py"
)
SPEC = importlib.util.spec_from_file_location(
    "build_gcp_post_session_assimilation_status",
    MODULE_PATH,
)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_build_payload_prefers_runtime_live_root(tmp_path: Path) -> None:
    runner_repo_root = tmp_path / "runner"
    runtime_root = tmp_path / "runtime" / "multi_ticker_portfolio_live"
    (runner_repo_root / "reports" / "multi_ticker_portfolio" / "runs").mkdir(parents=True)
    (runtime_root / "runs").mkdir(parents=True)
    (runtime_root / "state").mkdir(parents=True)

    payload = MODULE.build_payload(
        runner_repo_root=runner_repo_root,
        runtime_root=runtime_root,
        gcs_prefix="gs://codexalpaca-control-us/gcp_foundation",
    )

    assert payload["status"] == "ready_for_post_session_assimilation"
    assert payload["evidence_source_preference"] == "runtime_live"
    assert payload["preferred_reports_root"] == str(runtime_root)


def test_build_payload_falls_back_to_repo_mirror(tmp_path: Path) -> None:
    runner_repo_root = tmp_path / "runner"
    runtime_root = tmp_path / "runtime" / "multi_ticker_portfolio_live"
    (runner_repo_root / "reports" / "multi_ticker_portfolio" / "runs").mkdir(parents=True)

    payload = MODULE.build_payload(
        runner_repo_root=runner_repo_root,
        runtime_root=runtime_root,
        gcs_prefix="gs://codexalpaca-control-us/gcp_foundation",
    )

    assert payload["status"] == "ready_for_post_session_assimilation"
    assert payload["evidence_source_preference"] == "repo_mirror"


def test_build_payload_blocks_when_no_evidence_root_exists(tmp_path: Path) -> None:
    runner_repo_root = tmp_path / "runner"
    runtime_root = tmp_path / "runtime" / "multi_ticker_portfolio_live"
    runner_repo_root.mkdir(parents=True)

    payload = MODULE.build_payload(
        runner_repo_root=runner_repo_root,
        runtime_root=runtime_root,
        gcs_prefix="gs://codexalpaca-control-us/gcp_foundation",
    )

    assert payload["status"] == "blocked"
    assert "evidence_root_missing" in payload["missing_dependencies"]
