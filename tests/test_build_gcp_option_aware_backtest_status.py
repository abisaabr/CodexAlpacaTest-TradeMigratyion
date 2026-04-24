from __future__ import annotations

import json
from pathlib import Path

from cleanroom.code.qqq_options_30d_cleanroom.build_gcp_option_aware_backtest_status import (
    build_payload,
)


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_option_aware_backtest_status_blocks_sparse_fills(tmp_path: Path) -> None:
    manifest_json = tmp_path / "option_aware_research_run_manifest.json"
    _write_json(
        manifest_json,
        {
            "run_id": "run-1",
            "candidate_count": 2,
            "option_trade_count": 2,
            "recommendation_counts": {"hold_insufficient_option_fills": 2},
            "candidate_summaries": [
                {"fill_coverage": 0.2, "option_trade_count": 1},
                {"fill_coverage": 0.0, "option_trade_count": 0},
            ],
            "promotion_allowed": False,
            "broker_facing": False,
            "live_manifest_effect": "none",
            "risk_policy_effect": "none",
        },
    )

    payload = build_payload(
        manifest_json=manifest_json,
        report_dir=tmp_path,
        gcs_prefix="gs://example/option_aware_backtests",
    )

    assert payload["status"] == "blocked_insufficient_option_fills"
    assert payload["max_fill_coverage"] == 0.2
    assert payload["candidate_count_with_three_or_more_option_fills"] == 0
    assert any(issue["code"] == "insufficient_option_fills" for issue in payload["issues"])
    assert any("Do not promote" in item for item in payload["next_step_contract"])


def test_option_aware_backtest_status_requires_promotion_block(tmp_path: Path) -> None:
    manifest_json = tmp_path / "option_aware_research_run_manifest.json"
    _write_json(manifest_json, {"promotion_allowed": True, "broker_facing": False})

    payload = build_payload(
        manifest_json=manifest_json,
        report_dir=tmp_path,
        gcs_prefix="gs://example/option_aware_backtests",
    )

    assert payload["status"] == "blocked"
    assert any(issue["code"] == "promotion_not_explicitly_blocked" for issue in payload["issues"])
