from __future__ import annotations

import importlib.util
import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "cleanroom"
    / "code"
    / "qqq_options_30d_cleanroom"
    / "build_gcp_research_promotion_board_from_packets.py"
)
SPEC = importlib.util.spec_from_file_location("build_gcp_research_promotion_board_from_packets", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def _write_packet(path: Path, payload: dict) -> str:
    path.write_text(json.dumps(payload), encoding="utf-8")
    return str(path)


def test_build_payload_aggregates_blockers_and_best_leads(tmp_path: Path) -> None:
    packet = _write_packet(
        tmp_path / "amd.json",
        {
            "decision": "research_only_blocked",
            "gate_summary": {
                "candidate_count": 2,
                "eligible_for_promotion_review_count": 0,
            },
            "capital_plan": [
                {
                    "candidate_variant_id": "b150__amd__lead",
                    "symbol": "AMD",
                    "min_net_pnl": 1000,
                    "min_test_net_pnl": 250,
                    "min_fill_coverage": 0.7,
                    "min_option_trade_count": 30,
                    "promotion_blockers": ["fill_coverage_below_0.90"],
                }
            ],
            "blocker_counts": {"fill_coverage_below_0.90": 2},
        },
    )

    payload = MODULE.build_payload([packet], generated_at_utc="2026-04-28T00:00:00Z")

    assert payload["packet_count"] == 1
    assert payload["candidate_count"] == 2
    assert payload["eligible_for_promotion_review_count"] == 0
    assert payload["dominant_blocker"] == "fill_coverage_below_0.90"
    assert payload["best_research_only_leads"][0]["candidate_variant_id"] == "b150__amd__lead"
    assert payload["promotion_allowed_from_this_packet"] is False


def test_build_payload_uses_data_repair_target_when_capital_plan_empty(tmp_path: Path) -> None:
    packet = _write_packet(
        tmp_path / "kre.json",
        {
            "decision": "research_only_blocked",
            "gate_summary": {
                "candidate_count": 3,
                "eligible_for_promotion_review_count": 0,
            },
            "capital_plan": [],
            "data_repair_targets": [
                {
                    "candidate_variant_id": "b150__kre__repair",
                    "symbol": "KRE",
                    "min_net_pnl": 500,
                    "min_test_net_pnl": 100,
                    "min_fill_coverage": 0.1,
                    "promotion_blockers": ["option_trades_below_20"],
                }
            ],
            "blocker_counts": {"option_trades_below_20": 3},
        },
    )

    payload = MODULE.build_payload([packet], generated_at_utc="2026-04-28T00:00:00Z")

    assert payload["best_research_only_leads"][0]["candidate_variant_id"] == "b150__kre__repair"
    assert payload["dominant_blocker"] == "option_trades_below_20"


def test_review_candidates_are_reported_but_do_not_authorize_promotion(tmp_path: Path) -> None:
    packet = _write_packet(
        tmp_path / "aapl.json",
        {
            "decision": "candidate_for_walk_forward_review",
            "gate_summary": {
                "candidate_count": 1,
                "eligible_for_promotion_review_count": 1,
            },
            "review_candidates": [
                {
                    "candidate_variant_id": "b150__aapl__candidate",
                    "symbol": "AAPL",
                    "min_net_pnl": 1200,
                    "min_fill_coverage": 0.95,
                }
            ],
            "blocker_counts": {},
        },
    )

    payload = MODULE.build_payload([packet], generated_at_utc="2026-04-28T00:00:00Z")

    assert payload["new_governed_validation_candidates"] == 1
    assert payload["eligible_for_promotion_review_count"] == 1
    assert payload["review_candidates"][0]["candidate_variant_id"] == "b150__aapl__candidate"
    assert payload["promotion_allowed_from_this_packet"] is False
