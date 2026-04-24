from __future__ import annotations

import importlib.util
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "cleanroom"
    / "code"
    / "qqq_options_30d_cleanroom"
    / "build_gcp_research_asset_inventory.py"
)
SPEC = importlib.util.spec_from_file_location("build_gcp_research_asset_inventory", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_build_payload_ready_when_core_assets_exist(tmp_path: Path) -> None:
    runner_root = tmp_path / "runner"
    runtime_root = tmp_path / "runtime"
    report_dir = tmp_path / "reports"
    (runner_root / "scripts").mkdir(parents=True)
    (runner_root / "config" / "strategy_manifests").mkdir(parents=True)
    (runner_root / "reports" / "sample_backtest").mkdir(parents=True)
    (runtime_root / "runs" / "2026-04-23").mkdir(parents=True)
    (runtime_root / "session_evidence").mkdir(parents=True)
    (runtime_root / "session_teaching").mkdir(parents=True)
    (runtime_root / "trade_review").mkdir(parents=True)
    (runtime_root / "postmortem").mkdir(parents=True)
    (runtime_root / "quality_scorecard").mkdir(parents=True)

    (runner_root / "scripts" / "build_historical_dataset.py").write_text("", encoding="utf-8")
    (runner_root / "scripts" / "run_sample_backtest.py").write_text("", encoding="utf-8")
    (runner_root / "config" / "strategy_manifests" / "research.yaml").write_text("", encoding="utf-8")
    (runner_root / "reports" / "sample_backtest" / "sample_backtest_summary.json").write_text("{}", encoding="utf-8")
    (runtime_root / "runs" / "2026-04-23" / "multi_ticker_portfolio_session_summary.json").write_text(
        "{}", encoding="utf-8"
    )
    (runtime_root / "runs" / "2026-04-23" / "multi_ticker_portfolio_session_summary_completed_trades.csv").write_text(
        "", encoding="utf-8"
    )
    (runtime_root / "session_evidence" / "session_evidence_contract_2026-04-23.json").write_text("{}", encoding="utf-8")
    (runtime_root / "session_teaching" / "session_teaching_gate_2026-04-23.json").write_text("{}", encoding="utf-8")
    (runtime_root / "trade_review" / "trade_review_2026-04-23.json").write_text("{}", encoding="utf-8")
    (runtime_root / "postmortem" / "postmortem_2026-04-23.json").write_text("{}", encoding="utf-8")
    (runtime_root / "quality_scorecard" / "friday_quality_scorecard_2026-04-24.json").write_text("{}", encoding="utf-8")

    payload = MODULE.build_payload(
        runner_repo_root=runner_root,
        runtime_root=runtime_root,
        report_dir=report_dir,
        gcs_prefix="gs://bucket/research_manifests",
    )

    assert payload["status"] == "ready_for_research_bootstrap"
    assert payload["blockers"] == []
    assert payload["asset_counts"]["downloader_script_count"] == 1
    assert payload["asset_counts"]["backtest_script_count"] == 1
    assert "2026-04-23" in payload["assets"]["runtime_session_dates"]


def test_build_payload_review_required_when_assets_are_missing(tmp_path: Path) -> None:
    payload = MODULE.build_payload(
        runner_repo_root=tmp_path / "missing_runner",
        runtime_root=tmp_path / "missing_runtime",
        report_dir=tmp_path / "reports",
        gcs_prefix="gs://bucket/research_manifests",
    )

    assert payload["status"] == "review_required"
    assert "no_downloader_or_dataset_script_found" in payload["blockers"]
    assert "no_backtest_script_found" in payload["blockers"]
    assert "missing_april23_session_summary" in payload["blockers"]

