from __future__ import annotations

import json
from pathlib import Path

from cleanroom.code.qqq_options_30d_cleanroom.build_gcp_research_queue_bootstrap import build_payload


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_research_queue_prioritizes_defined_risk_expansion(tmp_path: Path) -> None:
    registry_json = tmp_path / "registry.json"
    scorecard_json = tmp_path / "scorecard.json"
    _write_json(
        registry_json,
        {
            "single_leg_strategy_share": 0.80,
            "registry": [
                {
                    "strategy_id": "qqq_call",
                    "family": "Single-leg long call",
                    "underlying_symbol": "QQQ",
                },
                {
                    "strategy_id": "msft_put",
                    "family": "Single-leg long put",
                    "underlying_symbol": "MSFT",
                },
                {
                    "strategy_id": "pltr_put",
                    "family": "Single-leg long put",
                    "underlying_symbol": "PLTR",
                },
            ],
        },
    )
    _write_json(
        scorecard_json,
        {
            "target_trade_date": "2026-04-24",
            "status": "ready_with_review_required_evidence",
            "universe": ["QQQ", "MSFT", "PLTR"],
            "recommended_first_session_bias": ["QQQ", "MSFT"],
            "avoid_or_shadow": ["PLTR"],
        },
    )

    payload = build_payload(
        strategy_registry_json=registry_json,
        quality_scorecard_json=scorecard_json,
        report_dir=tmp_path,
        gcs_prefix="gs://example/research_queue",
    )

    assert payload["status"] == "ready_with_research_warnings"
    assert payload["queue"][0]["queue_id"] == "RQ-001-defined-risk-family-expansion"
    assert payload["queue"][0]["symbols"] == ["QQQ", "MSFT"]
    assert payload["queue"][0]["estimated_variant_count"] == 96
    assert payload["queue"][1]["estimated_variant_count"] == 108
    assert payload["queue"][2]["symbols"] == ["PLTR"]
    assert payload["guardrails"] == [
        "research_queue_is_advisory_only",
        "do_not_mutate_live_manifest",
        "do_not_change_risk_policy",
        "do_not_start_broker_facing_session",
        "require_promotion_packet_before_runner_eligibility",
    ]


def test_research_queue_blocks_without_registry(tmp_path: Path) -> None:
    registry_json = tmp_path / "registry.json"
    _write_json(registry_json, {"registry": []})

    payload = build_payload(
        strategy_registry_json=registry_json,
        quality_scorecard_json=None,
        report_dir=tmp_path,
        gcs_prefix="gs://example/research_queue",
    )

    assert payload["status"] == "blocked"
    assert any(issue["code"] == "missing_strategy_registry" for issue in payload["issues"])
