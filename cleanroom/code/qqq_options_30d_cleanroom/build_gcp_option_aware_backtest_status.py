from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[2]
DEFAULT_REPORT_DIR = REPO_ROOT / "docs" / "gcp_foundation"
DEFAULT_MANIFEST_JSON = (
    REPO_ROOT.parent
    / "codexalpaca_repo_gcp_lease_lane_refreshed"
    / "reports"
    / "research_wave"
    / "option_aware_backtests"
    / "option_aware_research_20260424_gld_put_top25_lag60_diagnostic"
    / "option_aware_research_run_manifest.json"
)
DEFAULT_GCS_PREFIX = "gs://codexalpaca-control-us/research_runs/option_aware_backtests"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build option-aware backtest status packet.")
    parser.add_argument("--manifest-json", default=str(DEFAULT_MANIFEST_JSON))
    parser.add_argument("--report-dir", default=str(DEFAULT_REPORT_DIR))
    parser.add_argument("--gcs-prefix", default=DEFAULT_GCS_PREFIX)
    return parser


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def _fill_stats(candidate_summaries: list[dict[str, Any]]) -> dict[str, Any]:
    coverages = [float(row.get("fill_coverage") or 0.0) for row in candidate_summaries]
    return {
        "max_fill_coverage": round(max(coverages), 4) if coverages else 0.0,
        "mean_fill_coverage": round(sum(coverages) / len(coverages), 4) if coverages else 0.0,
        "candidate_count_with_three_or_more_option_fills": sum(
            1 for row in candidate_summaries if int(row.get("option_trade_count") or 0) >= 3
        ),
    }


def _status(
    *,
    issues: list[dict[str, str]],
    recommendation_counts: dict[str, int],
    fill_stats: dict[str, Any],
) -> str:
    if any(issue["severity"] == "error" for issue in issues):
        return "blocked"
    if recommendation_counts.get("candidate_for_walk_forward_review", 0) > 0:
        return "ready_for_walk_forward_expansion"
    if int(fill_stats["candidate_count_with_three_or_more_option_fills"]) == 0:
        return "blocked_insufficient_option_fills"
    return "hold_option_economics_review"


def _next_step_contract(status: str) -> list[str]:
    if status == "blocked_insufficient_option_fills":
        return [
            "Do not promote or deploy any option-aware candidate from this packet.",
            "Expand option quote/bar coverage for queued contracts before rerunning economics.",
            "Treat sparse positive PnL as diagnostic only until minimum-fill and out-of-sample gates pass.",
        ]
    if status == "ready_for_walk_forward_expansion":
        return [
            "Keep candidates research-only; this is not promotion authority.",
            "Run out-of-sample option-aware walk-forward expansion next.",
            "Send only walk-forward survivors to strategy governance review.",
        ]
    return [
        "Keep candidates research-only while option-aware economics remains under review.",
        "Inspect fill coverage, loser clusters, and train/test splits before any governance action.",
    ]


def build_payload(*, manifest_json: Path, report_dir: Path, gcs_prefix: str) -> dict[str, Any]:
    manifest = _load_json(manifest_json)
    issues: list[dict[str, str]] = []
    if not manifest:
        issues.append(
            {
                "severity": "error",
                "code": "missing_option_aware_backtest_manifest",
                "message": "Option-aware backtest manifest JSON is missing.",
            }
        )
    if manifest.get("promotion_allowed") is not False:
        issues.append(
            {
                "severity": "error",
                "code": "promotion_not_explicitly_blocked",
                "message": "Option-aware backtest packet must explicitly block promotion.",
            }
        )
    if manifest.get("broker_facing") is not False:
        issues.append(
            {
                "severity": "error",
                "code": "broker_facing_not_false",
                "message": "Option-aware backtest packet must be non-broker-facing.",
            }
        )
    candidate_summaries = (
        manifest.get("candidate_summaries")
        if isinstance(manifest.get("candidate_summaries"), list)
        else []
    )
    recommendation_counts = (
        manifest.get("recommendation_counts")
        if isinstance(manifest.get("recommendation_counts"), dict)
        else {}
    )
    recommendation_counts = {
        str(key): int(value) for key, value in recommendation_counts.items()
    }
    fill_stats = _fill_stats([row for row in candidate_summaries if isinstance(row, dict)])
    if recommendation_counts.get("hold_insufficient_option_fills", 0) > 0:
        issues.append(
            {
                "severity": "warning",
                "code": "insufficient_option_fills",
                "message": "At least one candidate lacks enough option-priced trades for promotion-grade economics.",
            }
        )
    status = _status(
        issues=issues,
        recommendation_counts=recommendation_counts,
        fill_stats=fill_stats,
    )
    run_id = manifest.get("run_id") or Path(manifest_json).parent.name
    return {
        "generated_at": datetime.now().astimezone().isoformat(),
        "status": status,
        "manifest_json": str(manifest_json),
        "report_dir": str(report_dir),
        "gcs_prefix": gcs_prefix,
        "run_id": run_id,
        "candidate_count": manifest.get("candidate_count"),
        "option_trade_count": manifest.get("option_trade_count"),
        "recommendation_counts": recommendation_counts,
        **fill_stats,
        "promotion_allowed": manifest.get("promotion_allowed"),
        "broker_facing": manifest.get("broker_facing"),
        "live_manifest_effect": manifest.get("live_manifest_effect"),
        "risk_policy_effect": manifest.get("risk_policy_effect"),
        "gcs_artifacts": {
            "manifest": f"{gcs_prefix}/{run_id}/option_aware_research_run_manifest.json",
            "candidate_summary": f"{gcs_prefix}/{run_id}/option_aware_candidate_summary.json",
            "trade_economics": f"{gcs_prefix}/{run_id}/option_aware_trade_economics.csv",
            "recommendation_packet": f"{gcs_prefix}/{run_id}/option_aware_recommendation_packet.json",
        },
        "issues": issues,
        "next_step_contract": _next_step_contract(status),
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "# GCP Option-Aware Backtest Status",
        "",
        f"- Generated at: `{payload['generated_at']}`",
        f"- Status: `{payload['status']}`",
        f"- Run id: `{payload['run_id']}`",
        f"- Candidate count: `{payload['candidate_count']}`",
        f"- Option trade count: `{payload['option_trade_count']}`",
        f"- Max fill coverage: `{payload['max_fill_coverage']}`",
        f"- Mean fill coverage: `{payload['mean_fill_coverage']}`",
        f"- Promotion allowed: `{payload['promotion_allowed']}`",
        f"- Broker facing: `{payload['broker_facing']}`",
        "",
        "## Recommendation Counts",
        "",
    ]
    for key, value in payload["recommendation_counts"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Issues", ""])
    for issue in payload["issues"]:
        lines.append(f"- `{issue['severity']}` `{issue['code']}`: {issue['message']}")
    lines.extend(["", "## Next Step Contract", ""])
    for item in payload["next_step_contract"]:
        lines.append(f"- {item}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = build_parser().parse_args()
    payload = build_payload(
        manifest_json=Path(args.manifest_json),
        report_dir=Path(args.report_dir),
        gcs_prefix=args.gcs_prefix,
    )
    report_dir = Path(args.report_dir)
    write_json(report_dir / "gcp_option_aware_backtest_status.json", payload)
    write_markdown(report_dir / "gcp_option_aware_backtest_status.md", payload)
    write_markdown(report_dir / "gcp_option_aware_backtest_status_handoff.md", payload)
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
