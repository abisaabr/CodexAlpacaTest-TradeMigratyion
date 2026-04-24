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
DEFAULT_RUNTIME_ROOT = REPO_ROOT.parent / "codexalpaca_runtime" / "multi_ticker_portfolio_live"
DEFAULT_GCS_PREFIX = "gs://codexalpaca-control-us/research_manifests"
GOVERNED_UNIVERSE = ("QQQ", "SPY", "IWM", "NVDA", "MSFT", "AMZN", "TSLA", "PLTR", "XLE", "GLD", "SLV")
SKIP_DIR_NAMES = {".git", ".venv", "__pycache__", ".pytest_cache", ".ruff_cache"}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build a compact research asset inventory for the GCP research lane.")
    parser.add_argument("--runner-repo-root", default=str(DEFAULT_RUNNER_REPO_ROOT))
    parser.add_argument("--runtime-root", default=str(DEFAULT_RUNTIME_ROOT))
    parser.add_argument("--report-dir", default=str(DEFAULT_REPORT_DIR))
    parser.add_argument("--gcs-prefix", default=DEFAULT_GCS_PREFIX)
    return parser


def _relative(path: Path, root: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve())).replace("\\", "/")
    except ValueError:
        return str(path)


def _iter_files(root: Path, *, max_files: int = 10_000) -> list[Path]:
    if not root.exists():
        return []
    files: list[Path] = []
    for path in root.rglob("*"):
        if any(part in SKIP_DIR_NAMES for part in path.parts):
            continue
        if path.is_file():
            files.append(path)
            if len(files) >= max_files:
                break
    return files


def _matching_files(root: Path, patterns: tuple[str, ...], *, limit: int = 200) -> list[str]:
    matches: list[Path] = []
    for file_path in _iter_files(root):
        normalized = _relative(file_path, root).lower()
        if any(pattern in normalized for pattern in patterns):
            matches.append(file_path)
    matches = sorted(matches)[:limit]
    return [_relative(path, root) for path in matches]


def _runtime_dates(runtime_root: Path) -> list[str]:
    runs_root = runtime_root / "runs"
    if not runs_root.exists():
        return []
    return sorted(path.name for path in runs_root.iterdir() if path.is_dir() and path.name[:4].isdigit())


def _exists(path: Path) -> bool:
    return path.exists()


def build_payload(
    *,
    runner_repo_root: Path,
    runtime_root: Path,
    report_dir: Path,
    gcs_prefix: str,
) -> dict[str, Any]:
    runner_files = _iter_files(runner_repo_root)
    runtime_dates = _runtime_dates(runtime_root)
    scripts_root = runner_repo_root / "scripts"
    config_root = runner_repo_root / "config"
    reports_root = runner_repo_root / "reports"

    downloader_scripts = _matching_files(scripts_root, ("download", "historical", "dataset", "data"))
    backtest_scripts = _matching_files(scripts_root, ("backtest",))
    research_scripts = _matching_files(scripts_root, ("research", "score", "quality", "review", "postmortem"))
    strategy_configs = _matching_files(config_root, ("strategy", "portfolio", "manifest", "backtest", "risk"))
    backtest_reports = _matching_files(reports_root, ("backtest",), limit=100)

    april_23_evidence = {
        "session_summary": _exists(runtime_root / "runs" / "2026-04-23" / "multi_ticker_portfolio_session_summary.json"),
        "completed_trades": _exists(
            runtime_root / "runs" / "2026-04-23" / "multi_ticker_portfolio_session_summary_completed_trades.csv"
        ),
        "evidence_contract": _exists(runtime_root / "session_evidence" / "session_evidence_contract_2026-04-23.json"),
        "teaching_gate": _exists(runtime_root / "session_teaching" / "session_teaching_gate_2026-04-23.json"),
        "trade_review": _exists(runtime_root / "trade_review" / "trade_review_2026-04-23.json"),
        "postmortem": _exists(runtime_root / "postmortem" / "postmortem_2026-04-23.json"),
        "quality_scorecard": _exists(runtime_root / "quality_scorecard" / "friday_quality_scorecard_2026-04-24.json"),
    }
    required_evidence_present = all(april_23_evidence.values())
    status = "ready_for_research_bootstrap" if downloader_scripts and backtest_scripts and required_evidence_present else "review_required"
    blockers: list[str] = []
    if not downloader_scripts:
        blockers.append("no_downloader_or_dataset_script_found")
    if not backtest_scripts:
        blockers.append("no_backtest_script_found")
    missing_evidence = [name for name, present in april_23_evidence.items() if not present]
    blockers.extend(f"missing_april23_{name}" for name in missing_evidence)

    return {
        "generated_at": datetime.now().astimezone().isoformat(),
        "status": status,
        "gcs_prefix": gcs_prefix,
        "runner_repo_root": str(runner_repo_root),
        "runtime_root": str(runtime_root),
        "report_dir": str(report_dir),
        "governed_universe": list(GOVERNED_UNIVERSE),
        "asset_counts": {
            "runner_file_count_sampled": len(runner_files),
            "downloader_script_count": len(downloader_scripts),
            "backtest_script_count": len(backtest_scripts),
            "research_script_count": len(research_scripts),
            "strategy_config_count": len(strategy_configs),
            "backtest_report_count": len(backtest_reports),
            "runtime_session_date_count": len(runtime_dates),
        },
        "assets": {
            "downloader_scripts": downloader_scripts,
            "backtest_scripts": backtest_scripts,
            "research_scripts": research_scripts,
            "strategy_configs": strategy_configs,
            "backtest_reports": backtest_reports,
            "runtime_session_dates": runtime_dates,
        },
        "april_23_evidence": april_23_evidence,
        "blockers": blockers,
        "next_actions": [
            "Publish this inventory to GCS before launching broader research sweeps.",
            "Normalize April 22 and April 23 paper-session evidence into derived research tables.",
            "Run data-quality checks over the governed 11-name universe before trusting any scorecard expansion.",
            "Keep all research outputs advisory until control-plane promotion review.",
        ],
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    assets = payload["assets"]
    counts = payload["asset_counts"]
    lines = [
        "# GCP Research Asset Inventory",
        "",
        "## Snapshot",
        "",
        f"- Generated at: `{payload['generated_at']}`",
        f"- Status: `{payload['status']}`",
        f"- Runner repo root: `{payload['runner_repo_root']}`",
        f"- Runtime root: `{payload['runtime_root']}`",
        f"- GCS prefix: `{payload['gcs_prefix']}`",
        "",
        "## Counts",
        "",
    ]
    for key, value in counts.items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## April 23 Evidence", ""])
    for key, value in payload["april_23_evidence"].items():
        lines.append(f"- {key}: `{value}`")
    if payload["blockers"]:
        lines.extend(["", "## Blockers", ""])
        for blocker in payload["blockers"]:
            lines.append(f"- `{blocker}`")
    lines.extend(["", "## Key Assets", "", "### Downloader Scripts", ""])
    for item in assets["downloader_scripts"][:25]:
        lines.append(f"- `{item}`")
    lines.extend(["", "### Backtest Scripts", ""])
    for item in assets["backtest_scripts"][:25]:
        lines.append(f"- `{item}`")
    lines.extend(["", "### Strategy Configs", ""])
    for item in assets["strategy_configs"][:40]:
        lines.append(f"- `{item}`")
    lines.extend(["", "### Runtime Session Dates", ""])
    for item in assets["runtime_session_dates"]:
        lines.append(f"- `{item}`")
    lines.extend(["", "## Next Actions", ""])
    for item in payload["next_actions"]:
        lines.append(f"- {item}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = build_parser().parse_args()
    report_dir = Path(args.report_dir)
    payload = build_payload(
        runner_repo_root=Path(args.runner_repo_root),
        runtime_root=Path(args.runtime_root),
        report_dir=report_dir,
        gcs_prefix=args.gcs_prefix,
    )
    json_path = report_dir / "gcp_research_asset_inventory.json"
    md_path = report_dir / "gcp_research_asset_inventory.md"
    handoff_path = report_dir / "gcp_research_asset_inventory_handoff.md"
    write_json(json_path, payload)
    write_markdown(md_path, payload)
    write_markdown(handoff_path, payload)
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
