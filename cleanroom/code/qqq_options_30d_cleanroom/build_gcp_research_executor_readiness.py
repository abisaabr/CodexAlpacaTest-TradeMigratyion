from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[2]
DEFAULT_REPORT_DIR = REPO_ROOT / "docs" / "gcp_foundation"
DEFAULT_RUNNER_REPO_ROOT = REPO_ROOT.parent / "codexalpaca_repo"
DEFAULT_WAVE_MANIFEST_JSON = DEFAULT_REPORT_DIR / "gcp_research_wave_manifest.json"
DEFAULT_SAMPLE_BACKTEST_JSON = DEFAULT_RUNNER_REPO_ROOT / "reports" / "sample_backtest" / "sample_backtest.json"
DEFAULT_GCS_PREFIX = "gs://codexalpaca-control-us/research_executor"

REQUIRED_RUNNER_ASSETS = {
    "historical_dataset_builder": "scripts/build_historical_dataset.py",
    "sample_backtest_runner": "scripts/run_sample_backtest.py",
    "generic_backtest_engine": "alpaca_lab/backtest/engine.py",
    "option_long_call_skeleton": "alpaca_lab/strategies/options_skeleton.py",
    "option_candidate_selector": "alpaca_lab/options/strategies.py",
}

FULL_WAVE_EXECUTOR_CANDIDATES = [
    "scripts/run_gcp_research_wave.py",
    "scripts/run_options_research_wave.py",
    "scripts/run_research_wave_backtest.py",
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build the GCP research executor readiness packet.")
    parser.add_argument("--runner-repo-root", default=str(DEFAULT_RUNNER_REPO_ROOT))
    parser.add_argument("--wave-manifest-json", default=str(DEFAULT_WAVE_MANIFEST_JSON))
    parser.add_argument("--sample-backtest-json", default=str(DEFAULT_SAMPLE_BACKTEST_JSON))
    parser.add_argument("--smoke-run-manifest-json", default=None)
    parser.add_argument("--report-dir", default=str(DEFAULT_REPORT_DIR))
    parser.add_argument("--gcs-prefix", default=DEFAULT_GCS_PREFIX)
    return parser


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def _asset_status(root: Path, assets: dict[str, str]) -> dict[str, dict[str, Any]]:
    status: dict[str, dict[str, Any]] = {}
    for name, relative_path in assets.items():
        path = root / relative_path
        status[name] = {
            "relative_path": relative_path,
            "exists": path.exists(),
            "absolute_path": str(path),
        }
    return status


def _data_inventory(root: Path) -> dict[str, Any]:
    data_root = root / "data"
    parquet_files = list(data_root.rglob("*.parquet")) if data_root.exists() else []
    csv_files = list(data_root.rglob("*.csv")) if data_root.exists() else []
    return {
        "data_root": str(data_root),
        "data_root_exists": data_root.exists(),
        "parquet_file_count": len(parquet_files),
        "csv_file_count": len(csv_files),
        "has_local_research_bars": bool(parquet_files or csv_files),
    }


def build_payload(
    *,
    runner_repo_root: Path,
    wave_manifest_json: Path,
    sample_backtest_json: Path,
    smoke_run_manifest_json: Path | None = None,
    report_dir: Path,
    gcs_prefix: str,
) -> dict[str, Any]:
    wave = _load_json(wave_manifest_json)
    sample = _load_json(sample_backtest_json)
    smoke = _load_json(smoke_run_manifest_json) if smoke_run_manifest_json else {}
    assets = _asset_status(runner_repo_root, REQUIRED_RUNNER_ASSETS)
    executor_candidates = _asset_status(
        runner_repo_root, {Path(path).stem: path for path in FULL_WAVE_EXECUTOR_CANDIDATES}
    )
    missing_assets = [name for name, item in assets.items() if not item["exists"]]
    present_executor_candidates = [
        name for name, item in executor_candidates.items() if item["exists"]
    ]
    data_inventory = _data_inventory(runner_repo_root)
    sample_trade_count = int(sample.get("trade_count") or 0) if sample else None

    issues: list[dict[str, str]] = []
    if missing_assets:
        issues.append(
            {
                "severity": "error",
                "code": "missing_runner_research_assets",
                "message": f"Missing runner assets: {', '.join(missing_assets)}.",
            }
        )
    if not present_executor_candidates:
        issues.append(
            {
                "severity": "error",
                "code": "missing_full_wave_executor",
                "message": "No runner script exists yet to consume the GCP research wave variants JSONL.",
            }
        )
    if not data_inventory["has_local_research_bars"]:
        issues.append(
            {
                "severity": "warning",
                "code": "missing_local_research_bars",
                "message": "No local parquet/csv research bars were found under the runner data root.",
            }
        )
    if sample and sample_trade_count == 0:
        issues.append(
            {
                "severity": "warning",
                "code": "sample_backtest_no_trades",
                "message": "The current synthetic sample backtest completed but produced zero trades.",
            }
        )
    if not wave:
        issues.append(
            {
                "severity": "error",
                "code": "missing_wave_manifest",
                "message": "Research wave manifest is missing.",
            }
        )

    required_smoke_outputs = [
        "research_run_manifest",
        "normalized_backtest_results",
        "train_test_or_walk_forward_summary",
        "after_cost_expectancy_table",
        "drawdown_and_tail_loss_report",
        "loser_cluster_comparison",
        "candidate_hold_kill_quarantine_recommendation",
    ]
    smoke_valid = bool(
        smoke
        and smoke.get("broker_facing") is False
        and smoke.get("live_manifest_effect") == "none"
        and smoke.get("risk_policy_effect") == "none"
        and all(item in smoke.get("required_outputs", []) for item in required_smoke_outputs)
    )

    status = "blocked_full_wave_executor_missing"
    if any(issue["severity"] == "error" and issue["code"] != "missing_full_wave_executor" for issue in issues):
        status = "blocked_missing_foundation"
    elif present_executor_candidates:
        status = "ready_for_research_only_execution_smoke_validated" if smoke_valid else "ready_for_research_only_execution"

    if present_executor_candidates:
        next_build_contract = [
            "Populate or mount curated research bars for the governed universe before treating results as real backtests.",
            "Run the research-only executor on bounded chunks and mirror raw result exhaust to GCS.",
            "Extend the executor from metadata proxy smoke to real single-leg repair backtests first.",
            "Add multi-leg payoff simulation before treating defined-risk variants as promotable.",
            "Keep compact promotion/rejection summaries in GitHub and require governance review before runner eligibility.",
        ]
    else:
        next_build_contract = [
            "Add a research-only runner script that reads gcp_research_wave_variants.jsonl.",
            "Executor must write research_run_manifest, normalized_backtest_results, train/test or walk-forward summary, after-cost expectancy, drawdown/tail-loss, loser-cluster comparison, and hold/kill/quarantine recommendation.",
            "Executor must not import broker trading paths, place orders, change live manifests, or change risk policy.",
            "Start with smoke chunks and single-leg repair diagnostics before treating multi-leg defined-risk variants as promotable.",
            "Keep raw result exhaust in GCS and compact promotion/rejection summaries in GitHub.",
        ]

    return {
        "generated_at": datetime.now().astimezone().isoformat(),
        "status": status,
        "runner_repo_root": str(runner_repo_root),
        "wave_manifest_json": str(wave_manifest_json),
        "sample_backtest_json": str(sample_backtest_json),
        "smoke_run_manifest_json": str(smoke_run_manifest_json) if smoke_run_manifest_json else None,
        "report_dir": str(report_dir),
        "gcs_prefix": gcs_prefix,
        "wave_status": wave.get("status"),
        "wave_id": wave.get("wave_id"),
        "wave_variant_count": wave.get("variant_count"),
        "wave_chunk_count": wave.get("chunk_count"),
        "runner_assets": assets,
        "full_wave_executor_candidates": executor_candidates,
        "data_inventory": data_inventory,
        "sample_backtest_summary": sample,
        "smoke_run_proof": {
            "present": bool(smoke),
            "valid": smoke_valid,
            "run_id": smoke.get("run_id"),
            "evidence_mode": smoke.get("evidence_mode"),
            "input_variant_count": smoke.get("input_variant_count"),
            "broker_facing": smoke.get("broker_facing"),
            "live_manifest_effect": smoke.get("live_manifest_effect"),
            "risk_policy_effect": smoke.get("risk_policy_effect"),
            "result_summary": smoke.get("result_summary"),
        },
        "issues": issues,
        "next_build_contract": next_build_contract,
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "# GCP Research Executor Readiness",
        "",
        "## Snapshot",
        "",
        f"- Generated at: `{payload['generated_at']}`",
        f"- Status: `{payload['status']}`",
        f"- Wave id: `{payload['wave_id']}`",
        f"- Wave variants: `{payload['wave_variant_count']}`",
        f"- Wave chunks: `{payload['wave_chunk_count']}`",
            f"- GCS prefix: `{payload['gcs_prefix']}`",
            "",
            "## Smoke Run Proof",
            "",
            f"- Present: `{payload['smoke_run_proof']['present']}`",
            f"- Valid: `{payload['smoke_run_proof']['valid']}`",
            f"- Run id: `{payload['smoke_run_proof']['run_id']}`",
            f"- Evidence mode: `{payload['smoke_run_proof']['evidence_mode']}`",
            f"- Input variants: `{payload['smoke_run_proof']['input_variant_count']}`",
            f"- Broker facing: `{payload['smoke_run_proof']['broker_facing']}`",
            "",
            "## Runner Asset Status",
            "",
    ]
    for name, item in payload["runner_assets"].items():
        lines.append(f"- `{name}`: `{item['exists']}` `{item['relative_path']}`")
    lines.extend(["", "## Full Wave Executor Candidates", ""])
    for name, item in payload["full_wave_executor_candidates"].items():
        lines.append(f"- `{name}`: `{item['exists']}` `{item['relative_path']}`")
    lines.extend(
        [
            "",
            "## Data Inventory",
            "",
            f"- Data root exists: `{payload['data_inventory']['data_root_exists']}`",
            f"- Parquet files: `{payload['data_inventory']['parquet_file_count']}`",
            f"- CSV files: `{payload['data_inventory']['csv_file_count']}`",
            f"- Has local research bars: `{payload['data_inventory']['has_local_research_bars']}`",
            "",
            "## Sample Backtest",
            "",
            f"- Trade count: `{payload['sample_backtest_summary'].get('trade_count')}`",
            f"- Net PnL: `{payload['sample_backtest_summary'].get('net_pnl')}`",
            f"- Bars source: `{payload['sample_backtest_summary'].get('bars_source')}`",
            "",
            "## Issues",
            "",
        ]
    )
    for issue in payload["issues"]:
        lines.append(f"- `{issue['severity']}` `{issue['code']}`: {issue['message']}")
    lines.extend(["", "## Next Build Contract", ""])
    for item in payload["next_build_contract"]:
        lines.append(f"- {item}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = build_parser().parse_args()
    payload = build_payload(
        runner_repo_root=Path(args.runner_repo_root),
        wave_manifest_json=Path(args.wave_manifest_json),
        sample_backtest_json=Path(args.sample_backtest_json),
        smoke_run_manifest_json=Path(args.smoke_run_manifest_json) if args.smoke_run_manifest_json else None,
        report_dir=Path(args.report_dir),
        gcs_prefix=args.gcs_prefix,
    )
    report_dir = Path(args.report_dir)
    write_json(report_dir / "gcp_research_executor_readiness.json", payload)
    write_markdown(report_dir / "gcp_research_executor_readiness.md", payload)
    write_markdown(report_dir / "gcp_research_executor_readiness_handoff.md", payload)
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
