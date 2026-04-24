from __future__ import annotations

import json
from pathlib import Path

from cleanroom.code.qqq_options_30d_cleanroom.build_gcp_research_executor_readiness import build_payload


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _touch(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("# test\n", encoding="utf-8")


def test_executor_readiness_blocks_without_full_wave_executor(tmp_path: Path) -> None:
    runner = tmp_path / "runner"
    for relative in [
        "scripts/build_historical_dataset.py",
        "scripts/run_sample_backtest.py",
        "alpaca_lab/backtest/engine.py",
        "alpaca_lab/strategies/options_skeleton.py",
        "alpaca_lab/options/strategies.py",
    ]:
        _touch(runner / relative)
    wave_json = tmp_path / "wave.json"
    sample_json = tmp_path / "sample.json"
    _write_json(wave_json, {"status": "ready_for_research_only_wave", "wave_id": "wave", "variant_count": 12, "chunk_count": 2})
    _write_json(sample_json, {"bars_source": "synthetic", "trade_count": 0, "net_pnl": 0.0})

    payload = build_payload(
        runner_repo_root=runner,
        wave_manifest_json=wave_json,
        sample_backtest_json=sample_json,
        smoke_run_manifest_json=None,
        report_dir=tmp_path,
        gcs_prefix="gs://example/research_executor",
    )

    assert payload["status"] == "blocked_full_wave_executor_missing"
    assert any(issue["code"] == "missing_full_wave_executor" for issue in payload["issues"])
    assert any(issue["code"] == "sample_backtest_no_trades" for issue in payload["issues"])


def test_executor_readiness_ready_when_executor_exists(tmp_path: Path) -> None:
    runner = tmp_path / "runner"
    for relative in [
        "scripts/build_historical_dataset.py",
        "scripts/run_sample_backtest.py",
        "scripts/run_gcp_research_wave.py",
        "alpaca_lab/backtest/engine.py",
        "alpaca_lab/strategies/options_skeleton.py",
        "alpaca_lab/options/strategies.py",
        "data/silver/stocks/bars.parquet",
    ]:
        _touch(runner / relative)
    wave_json = tmp_path / "wave.json"
    sample_json = tmp_path / "sample.json"
    smoke_json = tmp_path / "smoke.json"
    _write_json(wave_json, {"status": "ready_for_research_only_wave", "wave_id": "wave", "variant_count": 12, "chunk_count": 2})
    _write_json(sample_json, {"bars_source": "local", "trade_count": 3, "net_pnl": 15.0})
    _write_json(
        smoke_json,
        {
            "run_id": "smoke",
            "evidence_mode": "metadata_proxy_smoke",
            "input_variant_count": 3,
            "broker_facing": False,
            "live_manifest_effect": "none",
            "risk_policy_effect": "none",
            "required_outputs": [
                "research_run_manifest",
                "normalized_backtest_results",
                "train_test_or_walk_forward_summary",
                "after_cost_expectancy_table",
                "drawdown_and_tail_loss_report",
                "loser_cluster_comparison",
                "candidate_hold_kill_quarantine_recommendation",
            ],
        },
    )

    payload = build_payload(
        runner_repo_root=runner,
        wave_manifest_json=wave_json,
        sample_backtest_json=sample_json,
        smoke_run_manifest_json=smoke_json,
        report_dir=tmp_path,
        gcs_prefix="gs://example/research_executor",
    )

    assert payload["status"] == "ready_for_research_only_execution_smoke_validated"
    assert payload["data_inventory"]["has_local_research_bars"] is True
    assert payload["smoke_run_proof"]["valid"] is True


def test_executor_readiness_marks_real_bar_smoke_validated(tmp_path: Path) -> None:
    runner = tmp_path / "runner"
    for relative in [
        "scripts/build_historical_dataset.py",
        "scripts/run_sample_backtest.py",
        "scripts/run_gcp_research_wave.py",
        "alpaca_lab/backtest/engine.py",
        "alpaca_lab/strategies/options_skeleton.py",
        "alpaca_lab/options/strategies.py",
        "data/silver/stocks/bars.parquet",
    ]:
        _touch(runner / relative)
    wave_json = tmp_path / "wave.json"
    sample_json = tmp_path / "sample.json"
    smoke_json = tmp_path / "smoke.json"
    _write_json(wave_json, {"status": "ready_for_research_only_wave", "wave_id": "wave", "variant_count": 12, "chunk_count": 2})
    _write_json(sample_json, {"bars_source": "local", "trade_count": 3, "net_pnl": 15.0})
    _write_json(
        smoke_json,
        {
            "run_id": "real_bar_smoke",
            "evidence_mode": "real_stock_bar_smoke",
            "input_variant_count": 75,
            "broker_facing": False,
            "live_manifest_effect": "none",
            "risk_policy_effect": "none",
            "result_summary": {"mean_net_expectancy_after_cost_proxy": -1.25},
            "required_outputs": [
                "research_run_manifest",
                "normalized_backtest_results",
                "train_test_or_walk_forward_summary",
                "after_cost_expectancy_table",
                "drawdown_and_tail_loss_report",
                "loser_cluster_comparison",
                "candidate_hold_kill_quarantine_recommendation",
            ],
        },
    )

    payload = build_payload(
        runner_repo_root=runner,
        wave_manifest_json=wave_json,
        sample_backtest_json=sample_json,
        smoke_run_manifest_json=smoke_json,
        report_dir=tmp_path,
        gcs_prefix="gs://example/research_executor",
    )

    assert payload["status"] == "ready_for_research_only_real_bar_smoke_validated"
    assert any(issue["code"] == "real_bar_smoke_negative_mean_expectancy" for issue in payload["issues"])
    assert payload["next_build_contract"][0].startswith("Shard the remaining RQ-002")
