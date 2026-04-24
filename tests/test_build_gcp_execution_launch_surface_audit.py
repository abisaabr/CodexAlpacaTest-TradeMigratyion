from __future__ import annotations

import importlib.util
from datetime import datetime, timezone
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "cleanroom"
    / "code"
    / "qqq_options_30d_cleanroom"
    / "build_gcp_execution_launch_surface_audit.py"
)
SPEC = importlib.util.spec_from_file_location("build_gcp_execution_launch_surface_audit", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def _disabled_task_rows() -> list[dict]:
    return [
        {"TaskName": "Multi-Ticker Portfolio Paper Trader", "TaskPath": "\\", "State": 1},
        {"TaskName": "Stage27_DailyReport", "TaskPath": "\\", "State": "Disabled"},
        {
            "TaskName": "GovernedFeatureUsageProcessing",
            "TaskPath": "\\Microsoft\\Windows\\Flighting\\FeatureConfig\\",
            "State": 3,
        },
    ]


def _ready_payload(tmp_path: Path) -> dict:
    return MODULE.build_payload(
        report_dir=tmp_path,
        project_id="codexalpaca",
        vm_name="vm-execution-paper-01",
        zone="us-east1-b",
        expected_runner_commit="f008006",
        broker_position_count=0,
        broker_open_order_count=0,
        watch_duration_seconds=180,
        watch_start_utc="2026-04-24T15:49:19Z",
        watch_end_utc="2026-04-24T15:52:20Z",
        watch_samples=7,
        watch_sample_interval_seconds=30,
        watch_position_count_all_samples=0,
        watch_open_order_count_all_samples=0,
        watch_newest_order_created_at="2026-04-24T15:32:04Z",
        watch_newest_order_constant=True,
        scheduled_task_rows=_disabled_task_rows(),
        local_process_count=0,
        local_process_note="inspection commands only",
        vm_process_clear=True,
        vm_process_note="pgrep matched inspection command only",
        vm_runner_commit="f008006",
        vm_runner_branch="codex/qqq-paper-portfolio",
        vm_source_stamp={},
        now=datetime(2026, 4, 24, 12, 0, tzinfo=timezone.utc),
    )


def test_launch_surface_audit_ready_when_all_surfaces_are_clean(tmp_path: Path) -> None:
    payload = _ready_payload(tmp_path)

    assert payload["status"] == "local_broker_capable_surfaces_fenced_broker_flat"
    assert payload["broker_state"]["broker_flat"] is True
    assert payload["broker_state"]["post_fencing_no_new_order_watch"]["watch_clean"] is True
    assert payload["sanctioned_vm_audit"]["runner_commit_matches_expected"] is True
    assert payload["local_windows_task_scheduler"]["blocking_ready_tasks"] == []
    assert payload["issues"] == []
    assert payload["broker_facing"] is False
    assert payload["live_manifest_effect"] == "none"
    assert payload["risk_policy_effect"] == "none"


def test_launch_surface_audit_blocks_when_broker_not_flat(tmp_path: Path) -> None:
    blocked = MODULE.build_payload(
        report_dir=tmp_path,
        project_id="codexalpaca",
        vm_name="vm-execution-paper-01",
        zone="us-east1-b",
        expected_runner_commit="f008006",
        broker_position_count=1,
        broker_open_order_count=0,
        watch_duration_seconds=180,
        watch_start_utc="",
        watch_end_utc="",
        watch_samples=7,
        watch_sample_interval_seconds=30,
        watch_position_count_all_samples=0,
        watch_open_order_count_all_samples=0,
        watch_newest_order_created_at="",
        watch_newest_order_constant=True,
        scheduled_task_rows=_disabled_task_rows(),
        local_process_count=0,
        local_process_note="",
        vm_process_clear=True,
        vm_process_note="",
        vm_runner_commit="f008006",
        vm_runner_branch="codex/qqq-paper-portfolio",
    )

    assert blocked["status"] == "blocked_launch_surface_audit"
    assert any(issue["code"] == "broker_not_flat" for issue in blocked["issues"])


def test_launch_surface_audit_blocks_ready_project_task(tmp_path: Path) -> None:
    payload = _ready_payload(tmp_path)
    payload = MODULE.build_payload(
        report_dir=tmp_path,
        project_id="codexalpaca",
        vm_name="vm-execution-paper-01",
        zone="us-east1-b",
        expected_runner_commit="f008006",
        broker_position_count=0,
        broker_open_order_count=0,
        watch_duration_seconds=180,
        watch_start_utc="",
        watch_end_utc="",
        watch_samples=7,
        watch_sample_interval_seconds=30,
        watch_position_count_all_samples=0,
        watch_open_order_count_all_samples=0,
        watch_newest_order_created_at="",
        watch_newest_order_constant=True,
        scheduled_task_rows=[
            {"TaskName": "Stage27_PaperLive", "TaskPath": "\\", "State": 3},
        ],
        local_process_count=0,
        local_process_note="",
        vm_process_clear=True,
        vm_process_note="",
        vm_runner_commit="f008006",
        vm_runner_branch="codex/qqq-paper-portfolio",
    )

    assert payload["status"] == "blocked_launch_surface_audit"
    assert any(
        issue["code"] == "local_scheduled_launch_surface_ready"
        for issue in payload["issues"]
    )


def test_launch_surface_audit_blocks_stale_vm_commit(tmp_path: Path) -> None:
    payload = _ready_payload(tmp_path)
    payload = MODULE.build_payload(
        report_dir=tmp_path,
        project_id="codexalpaca",
        vm_name="vm-execution-paper-01",
        zone="us-east1-b",
        expected_runner_commit="f008006",
        broker_position_count=0,
        broker_open_order_count=0,
        watch_duration_seconds=180,
        watch_start_utc="",
        watch_end_utc="",
        watch_samples=7,
        watch_sample_interval_seconds=30,
        watch_position_count_all_samples=0,
        watch_open_order_count_all_samples=0,
        watch_newest_order_created_at="",
        watch_newest_order_constant=True,
        scheduled_task_rows=_disabled_task_rows(),
        local_process_count=0,
        local_process_note="",
        vm_process_clear=True,
        vm_process_note="",
        vm_runner_commit="8acef9e",
        vm_runner_branch="codex/qqq-paper-portfolio",
    )

    assert payload["status"] == "blocked_launch_surface_audit"
    assert any(issue["code"] == "vm_runner_commit_mismatch" for issue in payload["issues"])


def test_launch_surface_audit_blocks_when_newest_order_timestamp_changes(tmp_path: Path) -> None:
    payload = MODULE.build_payload(
        report_dir=tmp_path,
        project_id="codexalpaca",
        vm_name="vm-execution-paper-01",
        zone="us-east1-b",
        expected_runner_commit="f008006",
        broker_position_count=0,
        broker_open_order_count=0,
        watch_duration_seconds=180,
        watch_start_utc="",
        watch_end_utc="",
        watch_samples=7,
        watch_sample_interval_seconds=30,
        watch_position_count_all_samples=0,
        watch_open_order_count_all_samples=0,
        watch_newest_order_created_at="2026-04-24T15:33:00Z",
        watch_newest_order_constant=False,
        scheduled_task_rows=_disabled_task_rows(),
        local_process_count=0,
        local_process_note="",
        vm_process_clear=True,
        vm_process_note="",
        vm_runner_commit="f008006",
        vm_runner_branch="codex/qqq-paper-portfolio",
    )

    assert payload["status"] == "blocked_launch_surface_audit"
    assert any(issue["code"] == "no_new_order_watch_not_clean" for issue in payload["issues"])
