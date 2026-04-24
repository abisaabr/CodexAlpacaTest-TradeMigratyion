from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[2]
DEFAULT_REPORT_DIR = REPO_ROOT / "docs" / "gcp_foundation"
DEFAULT_RUNNER_REPO_ROOT = REPO_ROOT.parent / "codexalpaca_repo"
DEFAULT_MANIFEST_PATH = "config/strategy_manifests/multi_ticker_portfolio_live.yaml"
DEFAULT_GCS_PREFIX = "gs://codexalpaca-control-us/strategy_registry"
SINGLE_LEG_FAMILIES = {"single-leg long call", "single-leg long put"}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build the strategy registry bootstrap from the current runner manifest.")
    parser.add_argument("--runner-repo-root", default=str(DEFAULT_RUNNER_REPO_ROOT))
    parser.add_argument("--manifest-path", default=DEFAULT_MANIFEST_PATH)
    parser.add_argument("--report-dir", default=str(DEFAULT_REPORT_DIR))
    parser.add_argument("--gcs-prefix", default=DEFAULT_GCS_PREFIX)
    return parser


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return payload if isinstance(payload, dict) else {}


def _strategy_class(family: str, dte_mode: str, leg_count: int) -> str:
    family_lower = family.lower()
    if leg_count == 1 and "same_day" in dte_mode:
        return "Class B: same-day or opening-window single-leg"
    if leg_count == 1:
        return "Class A: liquid single-leg next-expiry directional"
    if "butterfly" in family_lower:
        return "Class D: complex choppy, premium, or convexity-sensitive"
    return "Class C: defined-risk multi-leg debit structure"


def _registry_row(strategy: dict[str, Any]) -> dict[str, Any]:
    legs = strategy.get("legs") if isinstance(strategy.get("legs"), list) else []
    family = str(strategy.get("family") or "unknown")
    dte_mode = str(strategy.get("dte_mode") or "unknown")
    strategy_id = str(strategy.get("name") or "unknown")
    return {
        "strategy_id": strategy_id,
        "display_name": strategy_id,
        "family_id": family.lower().replace(" ", "_").replace("-", "_"),
        "family": family,
        "structure_class": _strategy_class(family, dte_mode, len(legs)),
        "regime": strategy.get("regime"),
        "timing_profile": strategy.get("timing_profile"),
        "signal_name": strategy.get("signal_name"),
        "dte_mode": dte_mode,
        "underlying_symbol": strategy.get("underlying_symbol"),
        "risk_fraction": strategy.get("risk_fraction"),
        "max_contracts": strategy.get("max_contracts"),
        "hard_exit_minute": strategy.get("hard_exit_minute"),
        "profit_target_multiple": strategy.get("profit_target_multiple"),
        "stop_loss_multiple": strategy.get("stop_loss_multiple"),
        "leg_count": len(legs),
        "promotion_tier": "research_observed_executable",
        "promotion_state": "hold",
        "owner_plane": "runner_manifest",
        "runner_entrypoint_status": "manifest_wired",
        "source_research_run_id": None,
        "quarantine_reason": None,
        "kill_reason": None,
    }


def build_payload(
    *,
    runner_repo_root: Path,
    manifest_path: Path,
    report_dir: Path,
    gcs_prefix: str,
) -> dict[str, Any]:
    payload = _load_yaml(manifest_path)
    strategies = payload.get("strategies") if isinstance(payload.get("strategies"), list) else []
    registry = [_registry_row(item) for item in strategies if isinstance(item, dict)]
    family_counts = Counter(str(row["family"]) for row in registry)
    symbol_counts = Counter(str(row["underlying_symbol"]) for row in registry)
    class_counts = Counter(str(row["structure_class"]) for row in registry)
    single_leg_count = sum(count for family, count in family_counts.items() if family.lower() in SINGLE_LEG_FAMILIES)
    strategy_count = len(registry)
    single_leg_share = (single_leg_count / strategy_count) if strategy_count else 0.0

    issues: list[dict[str, str]] = []
    if not registry:
        issues.append({"code": "strategy_registry_empty", "severity": "error", "message": "No strategies found."})
    if single_leg_share > 0.70:
        issues.append(
            {
                "code": "single_leg_concentration",
                "severity": "warning",
                "message": f"Single-leg families represent {single_leg_share:.1%} of manifest strategies.",
            }
        )
    duplicate_ids = [strategy_id for strategy_id, count in Counter(row["strategy_id"] for row in registry).items() if count > 1]
    for strategy_id in duplicate_ids:
        issues.append(
            {
                "code": "duplicate_strategy_id",
                "severity": "error",
                "message": f"Strategy id appears multiple times: {strategy_id}",
            }
        )

    status = "ready_for_research_registry" if registry and not any(item["severity"] == "error" for item in issues) else "blocked"
    if issues and status != "blocked":
        status = "ready_with_concentration_warning"

    return {
        "generated_at": datetime.now().astimezone().isoformat(),
        "status": status,
        "runner_repo_root": str(runner_repo_root),
        "manifest_path": str(manifest_path),
        "report_dir": str(report_dir),
        "gcs_prefix": gcs_prefix,
        "strategy_count": strategy_count,
        "family_counts": dict(sorted(family_counts.items())),
        "symbol_counts": dict(sorted(symbol_counts.items())),
        "strategy_class_counts": dict(sorted(class_counts.items())),
        "single_leg_strategy_count": single_leg_count,
        "single_leg_strategy_share": round(single_leg_share, 4),
        "issues": issues,
        "registry": registry,
        "research_guidance": [
            "Use this registry as the identity layer for brute-force variants and promotion packets.",
            "Prioritize under-covered defined-risk and choppy/premium families before adding more single-leg variants.",
            "Keep generated variants out of the live manifest until they pass research promotion review.",
        ],
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "# GCP Strategy Registry Bootstrap",
        "",
        "## Snapshot",
        "",
        f"- Generated at: `{payload['generated_at']}`",
        f"- Status: `{payload['status']}`",
        f"- Strategy count: `{payload['strategy_count']}`",
        f"- Single-leg strategy share: `{payload['single_leg_strategy_share']:.1%}`",
        f"- Manifest path: `{payload['manifest_path']}`",
        f"- GCS prefix: `{payload['gcs_prefix']}`",
        "",
        "## Family Counts",
        "",
    ]
    for family, count in payload["family_counts"].items():
        lines.append(f"- {family}: `{count}`")
    lines.extend(["", "## Strategy Class Counts", ""])
    for strategy_class, count in payload["strategy_class_counts"].items():
        lines.append(f"- {strategy_class}: `{count}`")
    if payload["issues"]:
        lines.extend(["", "## Issues", ""])
        for issue in payload["issues"]:
            lines.append(f"- `{issue['severity']}` `{issue['code']}`: {issue['message']}")
    lines.extend(["", "## Research Guidance", ""])
    for item in payload["research_guidance"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Registry Preview", ""])
    for row in payload["registry"][:25]:
        lines.append(
            "- `{strategy_id}` {symbol} {family} {timing} {regime}".format(
                strategy_id=row["strategy_id"],
                symbol=row["underlying_symbol"],
                family=row["family"],
                timing=row["timing_profile"],
                regime=row["regime"],
            )
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = build_parser().parse_args()
    runner_repo_root = Path(args.runner_repo_root)
    manifest_path = Path(args.manifest_path)
    if not manifest_path.is_absolute():
        manifest_path = runner_repo_root / manifest_path
    report_dir = Path(args.report_dir)
    payload = build_payload(
        runner_repo_root=runner_repo_root,
        manifest_path=manifest_path,
        report_dir=report_dir,
        gcs_prefix=args.gcs_prefix,
    )
    write_json(report_dir / "gcp_strategy_registry_bootstrap.json", payload)
    write_markdown(report_dir / "gcp_strategy_registry_bootstrap.md", payload)
    write_markdown(report_dir / "gcp_strategy_registry_bootstrap_handoff.md", payload)
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()

