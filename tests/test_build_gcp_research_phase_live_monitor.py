from __future__ import annotations

import importlib.util
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "cleanroom"
    / "code"
    / "qqq_options_30d_cleanroom"
    / "build_gcp_research_phase_live_monitor.py"
)
SPEC = importlib.util.spec_from_file_location("build_gcp_research_phase_live_monitor", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_live_monitor_detects_active_downloader() -> None:
    payload = MODULE.build_payload(
        {
            "project_id": "codexalpaca",
            "location": "us-central1",
            "zone": "us-central1-f",
            "job_id": "phase19",
            "wave_id": "top100",
            "phase_id": "phase19_id",
            "batch_vm": "vm",
            "batch_state": "RUNNING",
            "batch_run_duration": "123.45s",
            "gcs_final_artifacts_visible": False,
            "remote_observation": {
                "container_name": "container",
                "container_status": "Up 1 hour",
                "container_found": True,
                "selected_contract_files": 266,
                "raw_download_files": 16898,
                "raw_download_bytes": 261911981,
                "silver_download_files": 17164,
                "silver_download_bytes": 141954301,
                "download_report_files": 0,
                "replay_files": 0,
                "portfolio_report_files": 0,
                "promotion_review_files": 0,
                "log_tail_redacted": (
                    "[04/27/26 15:38:52] INFO 'symbols': "
                    "'AMZN260515C00237500,AMZN260515C00240000', "
                    "'start': '2026-03-27T13:30:00+00:00'"
                ),
            },
        }
    )

    assert payload["status"] == "running_active_downloader"
    assert payload["active_stage"] == "download_option_market_data_for_selected_contracts"
    assert payload["run_duration_seconds_observed"] == 123
    assert payload["latest_observed_symbol_family"] == "AMZN option contracts"
    assert payload["latest_observed_download_date"] == "2026-03-27"
    assert payload["promotion_review_state"] == "not_started"
    assert payload["hard_rules"]["trading_started"] is False


def test_live_monitor_detects_replay_started() -> None:
    payload = MODULE.build_payload(
        {
            "batch_state": "RUNNING",
            "batch_run_duration": "99s",
            "gcs_final_artifacts_visible": False,
            "remote_observation": {
                "container_found": True,
                "selected_contract_files": 10,
                "raw_download_files": 10,
                "silver_download_files": 10,
                "replay_files": 3,
                "portfolio_report_files": 0,
                "promotion_review_files": 0,
            },
        }
    )

    assert payload["status"] == "running_option_aware_replay"
    assert payload["active_stage"] == "option_aware_replay"
    assert payload["promotion_review_state"] == "replay_started"


def test_live_monitor_detects_failed_job() -> None:
    payload = MODULE.build_payload(
        {
            "batch_state": "FAILED",
            "batch_run_duration": "200s",
            "gcs_final_artifacts_visible": False,
            "remote_observation": {
                "container_found": False,
            },
        }
    )

    assert payload["status"] == "failed_needs_diagnosis"
    assert payload["active_stage"] == "bootstrap_or_waiting"
