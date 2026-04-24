from __future__ import annotations

import importlib.util
from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "cleanroom"
    / "code"
    / "qqq_options_30d_cleanroom"
    / "build_gcp_strategy_registry_bootstrap.py"
)
SPEC = importlib.util.spec_from_file_location("build_gcp_strategy_registry_bootstrap", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def _write_manifest(path: Path, strategies: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump({"strategies": strategies}, sort_keys=False), encoding="utf-8")


def test_build_payload_extracts_registry_rows(tmp_path: Path) -> None:
    runner_root = tmp_path / "runner"
    manifest = runner_root / "config" / "strategy_manifests" / "test.yaml"
    _write_manifest(
        manifest,
        [
            {
                "name": "qqq__base__trend_long_call_next_expiry",
                "underlying_symbol": "QQQ",
                "family": "Single-leg long call",
                "regime": "bull",
                "timing_profile": "base",
                "signal_name": "trend_call",
                "dte_mode": "next_expiry",
                "risk_fraction": 0.05,
                "max_contracts": 2,
                "legs": [{"option_type": "call", "side": "long"}],
            },
            {
                "name": "qqq__fast__iron_butterfly_same_day",
                "underlying_symbol": "QQQ",
                "family": "Iron butterfly",
                "regime": "choppy",
                "timing_profile": "fast",
                "signal_name": "range",
                "dte_mode": "same_day",
                "legs": [
                    {"option_type": "put", "side": "long"},
                    {"option_type": "put", "side": "short"},
                    {"option_type": "call", "side": "short"},
                    {"option_type": "call", "side": "long"},
                ],
            },
        ],
    )

    payload = MODULE.build_payload(
        runner_repo_root=runner_root,
        manifest_path=manifest,
        report_dir=tmp_path / "report",
        gcs_prefix="gs://bucket/strategy_registry",
    )

    assert payload["strategy_count"] == 2
    assert payload["status"] == "ready_for_research_registry"
    assert payload["family_counts"]["Single-leg long call"] == 1
    assert payload["family_counts"]["Iron butterfly"] == 1
    assert payload["registry"][0]["promotion_state"] == "hold"


def test_build_payload_flags_single_leg_concentration(tmp_path: Path) -> None:
    runner_root = tmp_path / "runner"
    manifest = runner_root / "config" / "strategy_manifests" / "test.yaml"
    strategies = [
        {
            "name": f"qqq__base__trend_long_call_next_expiry_{index}",
            "underlying_symbol": "QQQ",
            "family": "Single-leg long call",
            "regime": "bull",
            "timing_profile": "base",
            "signal_name": "trend_call",
            "dte_mode": "next_expiry",
            "legs": [{"option_type": "call", "side": "long"}],
        }
        for index in range(4)
    ]
    strategies.append(
        {
            "name": "qqq__fast__iron_butterfly_same_day",
            "underlying_symbol": "QQQ",
            "family": "Iron butterfly",
            "regime": "choppy",
            "timing_profile": "fast",
            "signal_name": "range",
            "dte_mode": "same_day",
            "legs": [{"option_type": "call", "side": "long"}, {"option_type": "call", "side": "short"}],
        }
    )
    _write_manifest(manifest, strategies)

    payload = MODULE.build_payload(
        runner_repo_root=runner_root,
        manifest_path=manifest,
        report_dir=tmp_path / "report",
        gcs_prefix="gs://bucket/strategy_registry",
    )

    assert payload["status"] == "ready_with_concentration_warning"
    assert any(issue["code"] == "single_leg_concentration" for issue in payload["issues"])

