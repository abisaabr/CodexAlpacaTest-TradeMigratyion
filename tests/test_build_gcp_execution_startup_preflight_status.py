from __future__ import annotations

import importlib.util
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "cleanroom"
    / "code"
    / "qqq_options_30d_cleanroom"
    / "build_gcp_execution_startup_preflight_status.py"
)
SPEC = importlib.util.spec_from_file_location(
    "build_gcp_execution_startup_preflight_status",
    MODULE_PATH,
)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_startup_preflight_status_passes_only_when_read_only_and_clean() -> None:
    payload = MODULE.build_payload(
        preflight={
            "status": "startup_preflight_passed",
            "startup_check_status": "passed",
            "would_allow_trading": True,
            "broker_cleanup_allowed": False,
            "submit_paper_orders": False,
            "details": {
                "broker_position_count": 0,
                "open_order_count": 0,
                "underlyings": {"QQQ": {}, "SPY": {}},
                "failures": [],
                "pending_reasons": [],
            },
        },
        source_stamp={
            "runner_branch": "codex/qqq-paper-portfolio",
            "runner_commit": "abc123",
            "source_bundle_sha256": "sha",
            "source_bundle_file_count": 164,
        },
    )

    assert payload["status"] == "startup_preflight_passed"
    assert payload["blocks_launch"] is False
    assert payload["broker_facing"] is False
    assert payload["broker_cleanup_allowed"] is False
    assert payload["submit_paper_orders"] is False
    assert payload["underlying_count"] == 2
    assert payload["runner_commit"] == "abc123"
    assert payload["issues"] == []


def test_startup_preflight_status_blocks_when_broker_cleanup_would_be_allowed() -> None:
    payload = MODULE.build_payload(
        preflight={
            "status": "startup_preflight_passed",
            "startup_check_status": "passed",
            "would_allow_trading": True,
            "broker_cleanup_allowed": True,
            "submit_paper_orders": False,
            "details": {
                "broker_position_count": 0,
                "open_order_count": 0,
                "failures": [],
                "pending_reasons": [],
            },
        },
    )

    assert payload["status"] == "startup_preflight_blocked"
    assert payload["blocks_launch"] is True
    assert any(issue["code"] == "startup_preflight_not_read_only" for issue in payload["issues"])


def test_startup_preflight_status_blocks_on_stale_data_failure() -> None:
    payload = MODULE.build_payload(
        preflight={
            "status": "startup_preflight_failed",
            "startup_check_status": "failed",
            "would_allow_trading": False,
            "broker_cleanup_allowed": False,
            "submit_paper_orders": False,
            "details": {
                "broker_position_count": 0,
                "open_order_count": 0,
                "failures": ["IWM stock data stale at 189s"],
                "pending_reasons": [],
            },
        },
    )

    assert payload["status"] == "startup_preflight_blocked"
    assert payload["blocks_launch"] is True
    assert "IWM stock data stale at 189s" in payload["failures"]
    assert any(issue["code"] == "startup_preflight_failure" for issue in payload["issues"])


def test_startup_preflight_status_blocks_when_missing() -> None:
    payload = MODULE.build_payload(preflight={})

    assert payload["status"] == "startup_preflight_missing"
    assert payload["blocks_launch"] is True
    assert any(issue["code"] == "startup_preflight_missing" for issue in payload["issues"])
