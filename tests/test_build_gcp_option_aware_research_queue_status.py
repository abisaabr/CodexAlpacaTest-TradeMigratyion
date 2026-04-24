from __future__ import annotations

import json
from pathlib import Path

from cleanroom.code.qqq_options_30d_cleanroom.build_gcp_option_aware_research_queue_status import (
    build_payload,
)


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_option_aware_status_blocks_when_option_market_data_missing(tmp_path: Path) -> None:
    queue_json = tmp_path / "queue.json"
    summary_json = tmp_path / "summary.json"
    _write_json(
        queue_json,
        {
            "status": "blocked_missing_option_market_data",
            "queue_item_count": 25,
            "source_candidate_count": 25,
            "promotion_allowed": False,
            "broker_facing": False,
            "live_manifest_effect": "none",
            "risk_policy_effect": "none",
            "blocker_counts": {
                "missing_historical_option_bars": 25,
                "missing_historical_option_trades": 25,
            },
            "queue_items": [{"candidate_variant_id": "candidate"}],
        },
    )
    _write_json(
        summary_json,
        {
            "variant_result_count": 160,
            "recommendation_counts": {"candidate_for_deeper_option_backtest": 48},
        },
    )

    payload = build_payload(
        queue_json=queue_json,
        summary_json=summary_json,
        report_dir=tmp_path,
        gcs_prefix="gs://example/research_runs",
    )

    assert payload["status"] == "blocked_missing_option_market_data"
    assert payload["promotion_allowed"] is False
    assert payload["smoke_candidate_count"] == 48
    assert payload["top_follow_up_ids"] == ["candidate"]
    assert any(issue["code"] == "missing_historical_option_bars" for issue in payload["issues"])
    assert any("Download bounded historical option bars" in item for item in payload["next_step_contract"])


def test_option_aware_status_errors_without_explicit_promotion_block(tmp_path: Path) -> None:
    queue_json = tmp_path / "queue.json"
    summary_json = tmp_path / "summary.json"
    _write_json(queue_json, {"promotion_allowed": True})
    _write_json(summary_json, {})

    payload = build_payload(
        queue_json=queue_json,
        summary_json=summary_json,
        report_dir=tmp_path,
        gcs_prefix="gs://example/research_runs",
    )

    assert payload["status"] == "blocked"
    assert any(issue["code"] == "promotion_not_explicitly_blocked" for issue in payload["issues"])
    assert any("Repair missing or invalid" in item for item in payload["next_step_contract"])


def test_option_aware_status_advances_contract_when_market_data_ready(tmp_path: Path) -> None:
    queue_json = tmp_path / "queue.json"
    summary_json = tmp_path / "summary.json"
    _write_json(
        queue_json,
        {
            "status": "ready_for_option_aware_backtest",
            "queue_item_count": 25,
            "source_candidate_count": 25,
            "promotion_allowed": False,
            "broker_facing": False,
            "live_manifest_effect": "none",
            "risk_policy_effect": "none",
            "blocker_counts": {},
            "queue_items": [{"candidate_variant_id": "candidate"}],
        },
    )
    _write_json(
        summary_json,
        {
            "variant_result_count": 260,
            "recommendation_counts": {"candidate_for_deeper_option_backtest": 54},
        },
    )

    payload = build_payload(
        queue_json=queue_json,
        summary_json=summary_json,
        report_dir=tmp_path,
        gcs_prefix="gs://example/research_runs",
    )

    assert payload["status"] == "ready_for_option_aware_backtest"
    assert not payload["issues"]
    assert any("Run option-aware entry/exit economics" in item for item in payload["next_step_contract"])
    assert not any("Download bounded historical option bars" in item for item in payload["next_step_contract"])
