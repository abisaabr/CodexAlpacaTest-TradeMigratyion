from __future__ import annotations

import json
from pathlib import Path

from cleanroom.code.qqq_options_30d_cleanroom.build_gcp_paper_session_learning_packet import build_payload


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_learning_packet_blocks_until_qualified_winner_and_clean_evidence(tmp_path: Path) -> None:
    runtime = tmp_path / "runtime"
    run_dir = runtime / "runs" / "2026-04-23"
    _write_json(
        run_dir / "multi_ticker_portfolio_session_summary.json",
        {
            "trade_date": "2026-04-23",
            "net_pnl": -300.0,
            "completed_trade_count": 2,
            "open_reconciled_trade_count": 0,
            "shutdown_reconciled": True,
            "blocked_new_entries": True,
            "ending_broker_positions": {"position_count": 0},
        },
    )
    _write_text(
        run_dir / "multi_ticker_portfolio_session_summary_completed_trades.csv",
        "strategy_name,underlying_symbol,regime,quantity,entry_minute,exit_minute,exit_reason,net_pnl\n"
        "nvda__base__trend_long_put_next_expiry,NVDA,bear,1,30,60,stop_loss,-350\n"
        "qqq__fast__iron_butterfly_same_day,QQQ,neutral,1,40,80,target_profit,50\n",
    )
    _write_json(
        runtime / "session_evidence" / "session_evidence_contract_2026-04-23.json",
        {
            "summary": {
                "status": "review_required",
                "shutdown_reconciled": True,
                "ending_broker_position_count": 0,
                "economics_max_abs_cashflow_diff": 1.2,
            }
        },
    )
    _write_json(
        runtime / "session_teaching" / "session_teaching_gate_2026-04-23.json",
        {"summary": {"status": "review_required", "incident_level": "SEV1", "incident_code": "severe_loss_halt_new_entries"}},
    )
    _write_json(runtime / "trade_review" / "trade_review_2026-04-23.json", {"summary": {"winner_count": 1, "loser_count": 1}})
    quality = tmp_path / "quality.json"
    _write_json(
        quality,
        {
            "ranked_symbols": [
                {"symbol": "QQQ", "score": 77, "stance": "preferred_if_preopen_liquidity_clean", "reasons": ["positive"]},
                {"symbol": "NVDA", "score": 1, "stance": "avoid_for_first_gcp_session", "reasons": ["stop_loss_cluster"]},
            ]
        },
    )
    data = tmp_path / "data.json"
    _write_json(
        data,
        {
            "stock_rows": [{"symbol": "QQQ", "row_count": 100}],
            "selected_contract_rows_by_underlying": {"QQQ": 20},
            "option_contract_inventory_rows_by_underlying": {"QQQ": 50},
        },
    )
    option_status = tmp_path / "option.json"
    _write_json(option_status, {"status": "hold_option_economics_review", "promotion_allowed": False})

    payload = build_payload(
        runtime_root=runtime,
        quality_scorecard_json=quality,
        research_data_readiness_json=data,
        option_aware_backtest_status_json=option_status,
        trade_dates=["2026-04-23"],
        report_dir=tmp_path,
        min_net_pnl=200.0,
        target_qualified_winners=20,
        gcs_prefix="gs://example/gcp_foundation",
    )

    assert payload["status"] == "blocked_no_governed_validation_candidate"
    assert payload["qualified_winner_count"] == 0
    assert "severe_loss_incident_present" in payload["promotion_readiness"]["blockers"]
    assert payload["loser_learning"]["top_losing_symbols"][0]["name"] == "NVDA"
    qqq = next(row for row in payload["governed_universe_data_verdicts"] if row["symbol"] == "QQQ")
    nvda = next(row for row in payload["governed_universe_data_verdicts"] if row["symbol"] == "NVDA")
    assert qqq["verdict"] == "research_ready_with_quality_score"
    assert nvda["verdict"] == "avoid_for_first_session"


def test_learning_packet_counts_clean_qualified_winner(tmp_path: Path) -> None:
    runtime = tmp_path / "runtime"
    run_dir = runtime / "runs" / "2026-04-22"
    _write_json(
        run_dir / "multi_ticker_portfolio_session_summary.json",
        {
            "trade_date": "2026-04-22",
            "net_pnl": 250.0,
            "completed_trade_count": 1,
            "open_reconciled_trade_count": 0,
            "shutdown_reconciled": True,
            "ending_broker_positions": {"position_count": 0},
        },
    )
    _write_text(
        run_dir / "multi_ticker_portfolio_session_summary_completed_trades.csv",
        "strategy_name,underlying_symbol,regime,quantity,entry_minute,exit_minute,exit_reason,net_pnl\n"
        "qqq__fast__iron_butterfly_same_day,QQQ,neutral,1,40,80,target_profit,250\n",
    )
    _write_json(runtime / "session_evidence" / "session_evidence_contract_2026-04-22.json", {"summary": {"status": "ok", "shutdown_reconciled": True, "ending_broker_position_count": 0}})
    _write_json(runtime / "session_teaching" / "session_teaching_gate_2026-04-22.json", {"summary": {"status": "ok"}})

    payload = build_payload(
        runtime_root=runtime,
        quality_scorecard_json=tmp_path / "missing_quality.json",
        research_data_readiness_json=tmp_path / "missing_data.json",
        option_aware_backtest_status_json=tmp_path / "missing_option.json",
        trade_dates=["2026-04-22"],
        report_dir=tmp_path,
        min_net_pnl=200.0,
        target_qualified_winners=1,
        gcs_prefix="gs://example/gcp_foundation",
    )

    assert payload["raw_winner_count"] == 1
    assert payload["qualified_winner_count"] == 1
    assert payload["promotion_readiness"]["promotion_allowed"] is True
