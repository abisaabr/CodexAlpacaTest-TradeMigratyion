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
    _write_json(wave_json, {"status": "ready_for_research_only_wave", "wave_id": "wave", "variant_count": 12, "chunk_count": 2})
    _write_json(sample_json, {"bars_source": "local", "trade_count": 3, "net_pnl": 15.0})

    payload = build_payload(
        runner_repo_root=runner,
        wave_manifest_json=wave_json,
        sample_backtest_json=sample_json,
        report_dir=tmp_path,
        gcs_prefix="gs://example/research_executor",
    )

    assert payload["status"] == "ready_for_research_only_execution"
    assert payload["data_inventory"]["has_local_research_bars"] is True
