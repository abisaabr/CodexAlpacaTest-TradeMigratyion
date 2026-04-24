from __future__ import annotations

import importlib.util
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "cleanroom"
    / "code"
    / "qqq_options_30d_cleanroom"
    / "build_gcp_research_expansion_plan.py"
)
SPEC = importlib.util.spec_from_file_location("build_gcp_research_expansion_plan", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_expansion_plan_has_150_unique_tickers() -> None:
    tickers = MODULE._dedupe(MODULE.TICKER_UNIVERSE_150)

    assert len(tickers) == 150
    assert len(set(tickers)) == 150
    assert {"QQQ", "SPY", "IWM", "NVDA", "TSLA", "GLD", "SLV"}.issubset(set(tickers))


def test_expansion_plan_ready_when_wave_has_enough_variants(tmp_path: Path) -> None:
    wave_json = tmp_path / "wave.json"
    wave_json.write_text(
        '{"status":"ready_for_research_only_wave","variant_count":2070,"wave_id":"wave"}',
        encoding="utf-8",
    )

    payload = MODULE.build_payload(
        wave_manifest_json=wave_json,
        report_dir=tmp_path,
        data_gcs_prefix="gs://data",
        control_gcs_prefix="gs://control",
    )

    assert payload["status"] == "ready_for_parallel_data_and_strategy_expansion"
    assert payload["observed_strategy_variants"] >= 1000
    assert payload["ticker_count"] == 150
    assert payload["target_initial_cash"] == 25000
    assert payload["broker_facing"] is False
    assert payload["live_manifest_effect"] == "none"
    assert payload["risk_policy_effect"] == "none"


def test_expansion_plan_blocks_when_strategy_wave_is_too_small(tmp_path: Path) -> None:
    wave_json = tmp_path / "wave.json"
    wave_json.write_text(
        '{"status":"ready_for_research_only_wave","variant_count":999,"wave_id":"wave"}',
        encoding="utf-8",
    )

    payload = MODULE.build_payload(
        wave_manifest_json=wave_json,
        report_dir=tmp_path,
        data_gcs_prefix="gs://data",
        control_gcs_prefix="gs://control",
    )

    assert payload["status"] == "blocked_research_expansion_plan"
    assert any(issue["code"] == "strategy_variant_count_below_target" for issue in payload["issues"])
