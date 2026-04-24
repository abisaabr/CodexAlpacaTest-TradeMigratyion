from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[2]
DEFAULT_REPORT_DIR = REPO_ROOT / "docs" / "gcp_foundation"
DEFAULT_QUEUE_JSON = (
    REPO_ROOT.parent
    / "codexalpaca_repo_gcp_lease_lane_refreshed"
    / "reports"
    / "research_wave"
    / "option_aware_queue"
    / "option_aware_research_queue.json"
)
DEFAULT_SUMMARY_JSON = (
    REPO_ROOT.parent
    / "codexalpaca_repo_gcp_lease_lane_refreshed"
    / "reports"
    / "research_wave"
    / "summaries"
    / "gcp_research_run_summary.json"
)
DEFAULT_GCS_PREFIX = "gs://codexalpaca-control-us/research_runs"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build the GCP option-aware research queue status packet."
    )
    parser.add_argument("--queue-json", default=str(DEFAULT_QUEUE_JSON))
    parser.add_argument("--summary-json", default=str(DEFAULT_SUMMARY_JSON))
    parser.add_argument("--report-dir", default=str(DEFAULT_REPORT_DIR))
    parser.add_argument("--gcs-prefix", default=DEFAULT_GCS_PREFIX)
    return parser


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def build_payload(
    *,
    queue_json: Path,
    summary_json: Path,
    report_dir: Path,
    gcs_prefix: str,
) -> dict[str, Any]:
    queue = _load_json(queue_json)
    summary = _load_json(summary_json)
    issues = []
    if not queue:
        issues.append(
            {
                "severity": "error",
                "code": "missing_option_aware_queue",
                "message": "Option-aware research queue JSON is missing.",
            }
        )
    if not summary:
        issues.append(
            {
                "severity": "error",
                "code": "missing_research_run_summary",
                "message": "Research run summary JSON is missing.",
            }
        )
    if queue.get("promotion_allowed") is not False:
        issues.append(
            {
                "severity": "error",
                "code": "promotion_not_explicitly_blocked",
                "message": "Option-aware queue must explicitly block promotion.",
            }
        )
    blocker_counts = (
        queue.get("blocker_counts") if isinstance(queue.get("blocker_counts"), dict) else {}
    )
    for blocker, count in sorted(blocker_counts.items()):
        if int(count) > 0:
            issues.append(
                {
                    "severity": "warning",
                    "code": str(blocker),
                    "message": f"{count} queued follow-up items are blocked by {blocker}.",
                }
            )

    status = "blocked"
    if not any(issue["severity"] == "error" for issue in issues):
        status = (
            "blocked_missing_option_market_data"
            if blocker_counts
            else "ready_for_option_aware_backtest"
        )

    return {
        "generated_at": datetime.now().astimezone().isoformat(),
        "status": status,
        "queue_json": str(queue_json),
        "summary_json": str(summary_json),
        "report_dir": str(report_dir),
        "gcs_prefix": gcs_prefix,
        "smoke_unique_variant_count": summary.get("variant_result_count"),
        "smoke_candidate_count": summary.get("recommendation_counts", {}).get(
            "candidate_for_deeper_option_backtest"
        )
        if isinstance(summary.get("recommendation_counts"), dict)
        else None,
        "queue_item_count": queue.get("queue_item_count"),
        "source_candidate_count": queue.get("source_candidate_count"),
        "promotion_allowed": queue.get("promotion_allowed"),
        "broker_facing": queue.get("broker_facing"),
        "live_manifest_effect": queue.get("live_manifest_effect"),
        "risk_policy_effect": queue.get("risk_policy_effect"),
        "blocker_counts": blocker_counts,
        "top_follow_up_ids": [
            item.get("candidate_variant_id")
            for item in queue.get("queue_items", [])[:10]
            if isinstance(item, dict)
        ],
        "gcs_artifacts": {
            "research_summary": f"{gcs_prefix}/summaries/gcp_research_run_summary.json",
            "option_aware_queue": f"{gcs_prefix}/option_aware_queue/option_aware_research_queue.json",
        },
        "issues": issues,
        "next_step_contract": [
            "Keep all smoke candidates out of promotion until option-market-data blockers clear.",
            "Download bounded historical option bars for representative selected contracts first.",
            "Add option trades or quote/spread data before fill-cost calibration is trusted.",
            "Run option-aware entry/exit economics and walk-forward summary before strategy governance review.",
        ],
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "# GCP Option-Aware Research Queue Status",
        "",
        f"- Generated at: `{payload['generated_at']}`",
        f"- Status: `{payload['status']}`",
        f"- Smoke unique variants: `{payload['smoke_unique_variant_count']}`",
        f"- Smoke candidates: `{payload['smoke_candidate_count']}`",
        f"- Queue items: `{payload['queue_item_count']}`",
        f"- Promotion allowed: `{payload['promotion_allowed']}`",
        f"- Broker facing: `{payload['broker_facing']}`",
        "",
        "## Blocker Counts",
        "",
    ]
    for blocker, count in payload["blocker_counts"].items():
        lines.append(f"- `{blocker}`: `{count}`")
    lines.extend(["", "## Top Follow-Up IDs", ""])
    for item in payload["top_follow_up_ids"]:
        lines.append(f"- `{item}`")
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
        queue_json=Path(args.queue_json),
        summary_json=Path(args.summary_json),
        report_dir=Path(args.report_dir),
        gcs_prefix=args.gcs_prefix,
    )
    report_dir = Path(args.report_dir)
    write_json(report_dir / "gcp_option_aware_research_queue_status.json", payload)
    write_markdown(report_dir / "gcp_option_aware_research_queue_status.md", payload)
    write_markdown(report_dir / "gcp_option_aware_research_queue_status_handoff.md", payload)
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
