from __future__ import annotations

import json
from pathlib import Path

from cleanroom.code.qqq_options_30d_cleanroom.build_gcp_research_wave_manifest import build_payload, compact_payload


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_wave_manifest_expands_queue_into_stable_variants(tmp_path: Path) -> None:
    queue_json = tmp_path / "queue.json"
    registry_json = tmp_path / "registry.json"
    _write_json(
        queue_json,
        {
            "total_estimated_variant_count": 16,
            "queue": [
                {
                    "queue_id": "RQ-001-defined-risk-family-expansion",
                    "priority": 1,
                    "symbols": ["QQQ"],
                    "estimated_variant_count": 4,
                    "sweep_design": {
                        "family_templates": ["debit_call_vertical"],
                        "timing_profiles": ["fast", "slow"],
                        "dte_modes": ["same_day", "next_expiry"],
                    },
                },
                {
                    "queue_id": "RQ-002-single-leg-repair-and-loss-filter",
                    "priority": 2,
                    "symbols": ["QQQ"],
                    "estimated_variant_count": 4,
                    "sweep_design": {
                        "parameter_grid": {
                            "profit_target_multiple": [0.35, 0.45],
                            "stop_loss_multiple": [0.18],
                            "hard_exit_minute": [210, 300],
                            "liquidity_gate": ["tight"],
                        }
                    },
                },
                {
                    "queue_id": "RQ-003-loser-cluster-shadow-diagnostics",
                    "priority": 3,
                    "symbols": ["PLTR"],
                    "estimated_variant_count": 4,
                    "sweep_design": {
                        "parameter_grid": {
                            "entry_delay_minutes": [5, 15],
                            "stop_tightening": ["strict"],
                            "avoid_after_loser_similarity": [True, False],
                        }
                    },
                },
                {
                    "queue_id": "RQ-004-regime-and-liquidity-feature-grid",
                    "priority": 4,
                    "symbols": ["QQQ", "PLTR"],
                    "estimated_variant_count": 4,
                    "sweep_design": {"feature_groups": ["spread", "trend"]},
                },
            ],
        },
    )
    _write_json(
        registry_json,
        {
            "registry": [
                {"strategy_id": "qqq_call", "family": "Single-leg long call", "underlying_symbol": "QQQ"},
                {"strategy_id": "pltr_put", "family": "Single-leg long put", "underlying_symbol": "PLTR"},
            ]
        },
    )

    payload = build_payload(
        research_queue_json=queue_json,
        strategy_registry_json=registry_json,
        report_dir=tmp_path,
        gcs_prefix="gs://example/research_waves",
        chunk_size=5,
        wave_id="test_wave",
    )

    assert payload["status"] == "ready_for_research_only_wave"
    assert payload["wave_id"] == "test_wave"
    assert payload["variant_count"] == 16
    assert payload["chunk_count"] == 4
    assert payload["queue_counts"] == {
        "RQ-001-defined-risk-family-expansion": 4,
        "RQ-002-single-leg-repair-and-loss-filter": 4,
        "RQ-003-loser-cluster-shadow-diagnostics": 4,
        "RQ-004-regime-and-liquidity-feature-grid": 4,
    }
    assert payload["variants"][0]["variant_id"] == "rq001__qqq__debit_call_vertical__fast__next_expiry"
    assert payload["variants"][0]["state"] == "research_only"
    assert payload["execution_contract"]["broker_facing"] is False
    compact = compact_payload(payload, {"local_path": "variants.jsonl", "line_count": 16, "sha256": "abc"})
    assert "variants" not in compact
    assert compact["variant_artifact"]["line_count"] == 16


def test_wave_manifest_blocks_on_count_mismatch(tmp_path: Path) -> None:
    queue_json = tmp_path / "queue.json"
    registry_json = tmp_path / "registry.json"
    _write_json(
        queue_json,
        {
            "total_estimated_variant_count": 99,
            "queue": [
                {
                    "queue_id": "RQ-004-regime-and-liquidity-feature-grid",
                    "priority": 4,
                    "symbols": ["QQQ"],
                    "estimated_variant_count": 1,
                    "sweep_design": {"feature_groups": ["spread"]},
                }
            ],
        },
    )
    _write_json(
        registry_json,
        {"registry": [{"strategy_id": "qqq_call", "family": "Single-leg long call", "underlying_symbol": "QQQ"}]},
    )

    payload = build_payload(
        research_queue_json=queue_json,
        strategy_registry_json=registry_json,
        report_dir=tmp_path,
        gcs_prefix="gs://example/research_waves",
        chunk_size=10,
        wave_id="bad_wave",
    )

    assert payload["status"] == "blocked"
    assert any(issue["code"] == "queue_count_mismatch" for issue in payload["issues"])
