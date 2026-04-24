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
    / "build_gcp_paper_winner_session_readiness.py"
)
SPEC = importlib.util.spec_from_file_location("build_gcp_paper_winner_session_readiness", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_build_payload_counts_only_clean_winner_as_qualified(tmp_path: Path) -> None:
    runtime_root = tmp_path / "runtime"
    run_dir = runtime_root / "runs" / "2026-04-24"
    _write_json(
        run_dir / "multi_ticker_portfolio_session_summary.json",
        {
            "net_pnl": 250.0,
            "completed_trade_count": 3,
            "open_reconciled_trade_count": 0,
            "shutdown_reconciled": True,
            "ending_broker_positions": {"position_count": 0},
            "broker_local_economics_comparison": {
                "max_abs_cashflow_diff": 0.01,
                "tolerance_dollars": 0.05,
            },
        },
    )
    _write_json(runtime_root / "session_evidence" / "session_evidence_contract_2026-04-24.json", {"summary": {"status": "ok"}})
    _write_json(
        runtime_root / "session_teaching" / "session_teaching_gate_2026-04-24.json",
        {"summary": {"status": "ok", "automatic_learning_allowed": True}},
    )

    payload = MODULE.build_payload(
        runtime_root=runtime_root,
        report_dir=tmp_path / "report",
        gcs_prefix="gs://bucket/gcp_foundation",
        min_net_pnl=200.0,
        target_qualified_winners=1,
    )

    assert payload["status"] == "ready_for_micro_live_review"
    assert payload["raw_winner_count"] == 1
    assert payload["qualified_winner_count"] == 1
    assert payload["sessions"][0]["disqualifiers"] == []


def test_build_payload_keeps_review_required_winner_out_of_qualified_count(tmp_path: Path) -> None:
    runtime_root = tmp_path / "runtime"
    run_dir = runtime_root / "runs" / "2026-04-22"
    _write_json(
        run_dir / "multi_ticker_portfolio_session_summary.json",
        {
            "net_pnl": 1200.0,
            "completed_trade_count": 10,
            "open_reconciled_trade_count": 0,
            "shutdown_reconciled": True,
            "ending_broker_positions": {"position_count": 0},
            "broker_local_economics_comparison": {
                "max_abs_cashflow_diff": 1.0,
                "tolerance_dollars": 0.05,
            },
        },
    )
    _write_json(
        runtime_root / "session_evidence" / "session_evidence_contract_2026-04-22.json",
        {"summary": {"status": "review_required"}},
    )
    _write_json(
        runtime_root / "session_teaching" / "session_teaching_gate_2026-04-22.json",
        {"summary": {"status": "review_required", "automatic_learning_allowed": False}},
    )

    payload = MODULE.build_payload(
        runtime_root=runtime_root,
        report_dir=tmp_path / "report",
        gcs_prefix="gs://bucket/gcp_foundation",
        min_net_pnl=200.0,
        target_qualified_winners=20,
    )

    assert payload["status"] == "building_sample_with_raw_winners"
    assert payload["raw_winner_count"] == 1
    assert payload["qualified_winner_count"] == 0
    assert payload["review_required_raw_winner_count"] == 1
    assert "evidence_status_review_required" in payload["sessions"][0]["disqualifiers"]
    assert "broker_local_economics_drift" in payload["sessions"][0]["disqualifiers"]

