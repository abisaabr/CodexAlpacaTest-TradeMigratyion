from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[2]
DEFAULT_REPORT_DIR = REPO_ROOT / "docs" / "gcp_foundation"
DEFAULT_RUNNER_REPO_ROOT = REPO_ROOT.parent / "codexalpaca_repo_gcp_lease_lane_refreshed"
DEFAULT_BUILD_NAME = "research_preferred_1min_20260421_20260423_stock_contracts"
DEFAULT_GCS_PREFIX = "gs://codexalpaca-data-us"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build the GCP research data readiness packet.")
    parser.add_argument("--runner-repo-root", default=str(DEFAULT_RUNNER_REPO_ROOT))
    parser.add_argument("--build-name", default=DEFAULT_BUILD_NAME)
    parser.add_argument("--sample-backtest-json", default=None)
    parser.add_argument("--report-dir", default=str(DEFAULT_REPORT_DIR))
    parser.add_argument("--gcs-prefix", default=DEFAULT_GCS_PREFIX)
    return parser


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def _parquet_row_count(path: Path) -> int:
    import pandas as pd

    if not path.exists():
        return 0
    return int(len(pd.read_parquet(path)))


def _stock_summary(runner_repo_root: Path, build_name: str) -> list[dict[str, Any]]:
    root = runner_repo_root / "data" / "silver" / "historical" / build_name / "stock_bars"
    rows = []
    for path in sorted(root.rglob("part.parquet")):
        import pandas as pd

        frame = pd.read_parquet(path)
        symbol = str(frame["symbol"].iloc[0]) if len(frame) else path.parent.parent.name.split("=", 1)[-1]
        rows.append(
            {
                "symbol": symbol,
                "row_count": int(len(frame)),
                "start_timestamp": str(frame["timestamp"].min()) if len(frame) else None,
                "end_timestamp": str(frame["timestamp"].max()) if len(frame) else None,
                "path": str(path),
            }
        )
    return rows


def _partition_summary(runner_repo_root: Path, build_name: str, dataset: str) -> dict[str, int]:
    root = runner_repo_root / "data" / "silver" / "historical" / build_name / dataset
    counts: dict[str, int] = {}
    for path in sorted(root.rglob("part.parquet")):
        underlying = "unknown"
        for part in path.parts:
            if part.startswith("underlying="):
                underlying = part.split("=", 1)[1]
                break
        counts[underlying] = counts.get(underlying, 0) + _parquet_row_count(path)
    return dict(sorted(counts.items()))


def build_payload(
    *,
    runner_repo_root: Path,
    build_name: str,
    sample_backtest_json: Path | None,
    report_dir: Path,
    gcs_prefix: str,
) -> dict[str, Any]:
    build_manifest = _load_json(runner_repo_root / "data" / "raw" / "manifests" / f"{build_name}.json")
    combined_manifest = _load_json(runner_repo_root / "data" / "silver" / "stocks" / f"{build_name}.manifest.json")
    sample = _load_json(sample_backtest_json) if sample_backtest_json else {}
    stock_rows = _stock_summary(runner_repo_root, build_name)
    contract_counts = _partition_summary(runner_repo_root, build_name, "option_contract_inventory")
    selected_counts = _partition_summary(runner_repo_root, build_name, "selected_option_contracts")
    failed_chunks = 0
    for dataset in build_manifest.get("datasets", {}).values():
        chunks = dataset.get("chunks", {}) if isinstance(dataset, dict) else {}
        for chunk in chunks.values():
            if isinstance(chunk, dict) and chunk.get("status") == "failed":
                failed_chunks += 1
    sample_expectancy = float(sample.get("expectancy") or 0.0) if sample else None
    issues: list[dict[str, str]] = []
    if not build_manifest:
        issues.append({"severity": "error", "code": "missing_build_manifest", "message": "Historical build manifest is missing."})
    if not stock_rows:
        issues.append({"severity": "error", "code": "missing_stock_bars", "message": "No stock bars found for the research build."})
    if failed_chunks:
        issues.append({"severity": "error", "code": "failed_data_chunks", "message": f"{failed_chunks} data chunks failed."})
    if not combined_manifest:
        issues.append({"severity": "warning", "code": "missing_combined_stock_panel", "message": "Combined stock panel manifest is missing."})
    if sample and sample_expectancy is not None and sample_expectancy < 0:
        issues.append(
            {
                "severity": "warning",
                "code": "negative_sample_backtest_expectancy",
                "message": "The real-bar sample stock baseline has negative expectancy and should be treated as a loser-learning baseline.",
            }
        )
    status = "blocked" if any(issue["severity"] == "error" for issue in issues) else "ready_for_real_bar_research_with_warnings"
    if status != "blocked" and not issues:
        status = "ready_for_real_bar_research"
    return {
        "generated_at": datetime.now().astimezone().isoformat(),
        "status": status,
        "runner_repo_root": str(runner_repo_root),
        "build_name": build_name,
        "report_dir": str(report_dir),
        "gcs_prefix": gcs_prefix,
        "stock_symbol_count": len(stock_rows),
        "stock_row_count": sum(row["row_count"] for row in stock_rows),
        "stock_rows": stock_rows,
        "option_contract_inventory_rows_by_underlying": contract_counts,
        "selected_contract_rows_by_underlying": selected_counts,
        "combined_stock_panel": combined_manifest,
        "sample_backtest_summary": sample,
        "gcs_artifacts": {
            "raw_manifest": f"{gcs_prefix}/raw/manifests/{build_name}.json",
            "raw_historical_prefix": f"{gcs_prefix}/raw/historical/{build_name}/",
            "curated_historical_prefix": f"{gcs_prefix}/curated/historical/{build_name}/",
            "combined_stock_panel": f"{gcs_prefix}/curated/stocks/{build_name}.parquet",
            "combined_stock_panel_manifest": f"{gcs_prefix}/curated/stocks/{build_name}.manifest.json",
            "reports_prefix": f"{gcs_prefix}/reports/historical/{build_name}/",
            "sample_backtest_prefix": f"{gcs_prefix}/reports/sample_backtest/{build_name}/",
        },
        "issues": issues,
        "next_research_step": [
            "Use this dataset for real-bar single-leg repair smoke backtests first.",
            "Treat the negative stock baseline as loser-learning evidence, not as a deployment candidate.",
            "Add historical option bars/trades only after the stock-bar and selected-contract workflow remains stable.",
        ],
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "# GCP Research Data Readiness",
        "",
        "## Snapshot",
        "",
        f"- Generated at: `{payload['generated_at']}`",
        f"- Status: `{payload['status']}`",
        f"- Build name: `{payload['build_name']}`",
        f"- Stock symbols: `{payload['stock_symbol_count']}`",
        f"- Stock rows: `{payload['stock_row_count']}`",
        f"- GCS prefix: `{payload['gcs_prefix']}`",
        "",
        "## Stock Rows",
        "",
    ]
    for row in payload["stock_rows"]:
        lines.append(f"- `{row['symbol']}` rows `{row['row_count']}` `{row['start_timestamp']}` to `{row['end_timestamp']}`")
    lines.extend(["", "## Option Contract Inventory Rows", ""])
    for underlying, count in payload["option_contract_inventory_rows_by_underlying"].items():
        lines.append(f"- `{underlying}`: `{count}`")
    lines.extend(["", "## Selected Contract Rows", ""])
    for underlying, count in payload["selected_contract_rows_by_underlying"].items():
        lines.append(f"- `{underlying}`: `{count}`")
    lines.extend(
        [
            "",
            "## Sample Backtest Baseline",
            "",
            f"- Trade count: `{payload['sample_backtest_summary'].get('trade_count')}`",
            f"- Net PnL: `{payload['sample_backtest_summary'].get('net_pnl')}`",
            f"- Expectancy: `{payload['sample_backtest_summary'].get('expectancy')}`",
            f"- Win rate: `{payload['sample_backtest_summary'].get('win_rate')}`",
            "",
            "## GCS Artifacts",
            "",
        ]
    )
    for name, uri in payload["gcs_artifacts"].items():
        lines.append(f"- `{name}`: `{uri}`")
    if payload["issues"]:
        lines.extend(["", "## Issues", ""])
        for issue in payload["issues"]:
            lines.append(f"- `{issue['severity']}` `{issue['code']}`: {issue['message']}")
    lines.extend(["", "## Next Research Step", ""])
    for item in payload["next_research_step"]:
        lines.append(f"- {item}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = build_parser().parse_args()
    payload = build_payload(
        runner_repo_root=Path(args.runner_repo_root),
        build_name=args.build_name,
        sample_backtest_json=Path(args.sample_backtest_json) if args.sample_backtest_json else None,
        report_dir=Path(args.report_dir),
        gcs_prefix=args.gcs_prefix,
    )
    report_dir = Path(args.report_dir)
    write_json(report_dir / "gcp_research_data_readiness.json", payload)
    write_markdown(report_dir / "gcp_research_data_readiness.md", payload)
    write_markdown(report_dir / "gcp_research_data_readiness_handoff.md", payload)
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
