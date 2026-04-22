from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[2]
DEFAULT_REGISTRY_JSON = REPO_ROOT / "docs" / "session_reconciliation" / "session_reconciliation_registry.json"
DEFAULT_REPORT_DIR = REPO_ROOT / "docs" / "session_reconciliation"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build a concise session-reconciliation steward handoff from the formal session reconciliation registry."
    )
    parser.add_argument("--registry-json", default=str(DEFAULT_REGISTRY_JSON))
    parser.add_argument("--report-dir", default=str(DEFAULT_REPORT_DIR))
    parser.add_argument("--top-n", type=int, default=5)
    return parser


def determine_posture(payload: dict[str, Any]) -> dict[str, Any]:
    summary = dict(payload.get("summary") or {})
    sessions = [row for row in list(payload.get("sessions") or []) if isinstance(row, dict)]
    recent_trade_sessions = sorted(
        [row for row in sessions if str(row.get("session_kind")) == "traded"],
        key=lambda row: str(row.get("trade_date", "")),
        reverse=True,
    )[:5]

    review_required_recent = any(str(row.get("trust_tier")) == "review_required" for row in recent_trade_sessions)
    caution_recent = any(str(row.get("trust_tier")) == "caution" for row in recent_trade_sessions)
    broker_order_gap = bool((payload.get("data_quality") or {}).get("missing_broker_order_audit_dates"))
    broker_activity_gap = bool((payload.get("data_quality") or {}).get("missing_broker_activity_audit_dates"))
    residual_positions = int(summary.get("ending_broker_position_count_total", 0) or 0) > 0
    economics_delta = float(summary.get("realized_reconciliation_delta_abs_total", 0.0) or 0.0) > 0.05
    mismatch_pressure = (
        int(summary.get("broker_status_mismatch_count_total", 0) or 0) > 0
        or int(summary.get("local_order_without_broker_match_count_total", 0) or 0) > 0
        or int(summary.get("broker_activity_unmatched_count_total", 0) or 0) > 0
        or int(summary.get("local_filled_order_without_activity_match_count_total", 0) or 0) > 0
    )
    partial_fill_pressure = int(summary.get("partial_fill_count_total", 0) or 0) > 0
    cleanup_pressure = (
        int(summary.get("known_trade_cleanup_count_total", 0) or 0) > 0
        or int(summary.get("unexpected_position_cleanup_count_total", 0) or 0) > 0
        or int(summary.get("forced_exit_failure_count_total", 0) or 0) > 0
    )

    if review_required_recent or residual_positions or economics_delta:
        posture = "review_required"
    elif caution_recent or broker_order_gap or broker_activity_gap or mismatch_pressure or partial_fill_pressure or cleanup_pressure:
        posture = "caution"
    else:
        posture = "stable"

    audited_recent_sessions = [
        row
        for row in recent_trade_sessions
        if bool(row.get("broker_order_audit_available")) and bool(row.get("broker_activity_audit_available"))
    ]
    if not recent_trade_sessions:
        evidence_strength = "no_recent_trade_sessions"
    elif len(audited_recent_sessions) == len(recent_trade_sessions):
        evidence_strength = "full"
    elif audited_recent_sessions:
        evidence_strength = "partial"
    else:
        evidence_strength = "limited"

    return {
        "overall_session_reconciliation_posture": posture,
        "evidence_strength": evidence_strength,
        "flags": {
            "review_required_recent": review_required_recent,
            "caution_recent": caution_recent,
            "broker_order_audit_gap": broker_order_gap,
            "broker_activity_audit_gap": broker_activity_gap,
            "residual_positions": residual_positions,
            "economics_delta": economics_delta,
            "mismatch_pressure": mismatch_pressure,
            "partial_fill_pressure": partial_fill_pressure,
            "cleanup_pressure": cleanup_pressure,
        },
    }


def policy_recommendations(payload: dict[str, Any], posture: dict[str, Any]) -> dict[str, Any]:
    flags = dict(posture.get("flags") or {})
    review_required = posture.get("overall_session_reconciliation_posture") == "review_required"

    if review_required:
        trusted_learning_scope = "trusted_sessions_only"
        promotion_readiness = "hold"
    elif posture.get("overall_session_reconciliation_posture") == "caution":
        trusted_learning_scope = "trusted_and_cautious_sessions"
        promotion_readiness = "review_only"
    else:
        trusted_learning_scope = "all_recent_sessions"
        promotion_readiness = "normal_review"

    operator_actions = [
        f"Use `{trusted_learning_scope}` when deciding which paper-runner sessions should influence research calibration and tournament policy.",
    ]
    if review_required:
        operator_actions.append("Do not loosen research policy or clear promotion-style conclusions from sessions marked review-required until reconciliation is manually checked.")
    if flags.get("broker_order_audit_gap"):
        operator_actions.append("Treat broker-order audit coverage as incomplete and avoid over-trusting clean local order logs alone.")
    if flags.get("broker_activity_audit_gap"):
        operator_actions.append("Treat broker account-activity coverage as incomplete and avoid over-trusting local fill telemetry alone.")
    if flags.get("mismatch_pressure"):
        operator_actions.append("Inspect order-state and activity mismatches before using combo-heavy sessions to relax fill or cleanup assumptions.")
    if flags.get("partial_fill_pressure"):
        operator_actions.append("Keep partial-fill and cleanup assumptions conservative while partial-fill pressure remains visible.")
    if flags.get("cleanup_pressure"):
        operator_actions.append("Prefer simpler exits and smaller size caps until cleanup pressure normalizes.")

    return {
        "trusted_learning_scope": trusted_learning_scope,
        "promotion_readiness": promotion_readiness,
        "operator_actions": operator_actions,
    }


def top_review_sessions(payload: dict[str, Any], top_n: int) -> list[dict[str, Any]]:
    sessions = [row for row in list(payload.get("sessions") or []) if isinstance(row, dict)]
    filtered = [row for row in sessions if str(row.get("trust_tier")) in {"review_required", "caution"}]
    filtered.sort(
        key=lambda row: (
            {"review_required": 0, "caution": 1}.get(str(row.get("trust_tier")), 9),
            int(row.get("quality_score", 0)),
            str(row.get("trade_date", "")),
        )
    )
    return [dict(row) for row in filtered[:top_n]]


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    posture = payload["posture"]
    policy = payload["policy"]
    lines: list[str] = []
    lines.append("# Session Reconciliation Handoff")
    lines.append("")
    lines.append("## Snapshot")
    lines.append("")
    lines.append(f"- Generated at: `{payload['generated_at']}`")
    lines.append(f"- Posture: `{posture['overall_session_reconciliation_posture']}`")
    lines.append(f"- Evidence strength: `{posture['evidence_strength']}`")
    lines.append("")
    lines.append("## Flags")
    lines.append("")
    for key, value in posture["flags"].items():
        lines.append(f"- `{key}`: `{str(bool(value)).lower()}`")
    lines.append("")
    lines.append("## Policy Guidance")
    lines.append("")
    lines.append(f"- Trusted learning scope: `{policy['trusted_learning_scope']}`")
    lines.append(f"- Promotion readiness: `{policy['promotion_readiness']}`")
    lines.append("")
    lines.append("## Operator Actions")
    lines.append("")
    for action in policy["operator_actions"]:
        lines.append(f"- {action}")
    lines.append("")
    lines.append("## Sessions Needing Attention")
    lines.append("")
    for row in payload["sessions_needing_attention"]:
        reasons = row.get("review_required_reasons") or row.get("caution_reasons") or []
        lines.append(
            f"- `{row['trade_date']}`: tier `{row['trust_tier']}`, quality `{row['quality_score']}`, reasons `{', '.join(reasons)}`"
        )
    if not payload["sessions_needing_attention"]:
        lines.append("- none")
    lines.append("")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = build_parser().parse_args()
    registry_path = Path(args.registry_json).resolve()
    report_dir = Path(args.report_dir).resolve()
    report_dir.mkdir(parents=True, exist_ok=True)

    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    posture = determine_posture(registry)
    policy = policy_recommendations(registry, posture)
    handoff = {
        "generated_at": registry.get("generated_at"),
        "registry_json": str(registry_path),
        "posture": posture,
        "policy": policy,
        "sessions_needing_attention": top_review_sessions(registry, int(args.top_n)),
    }

    json_path = report_dir / "session_reconciliation_handoff.json"
    md_path = report_dir / "session_reconciliation_handoff.md"
    json_path.write_text(json.dumps(handoff, indent=2), encoding="utf-8")
    write_markdown(md_path, handoff)
    print(json.dumps({"json_path": str(json_path), "markdown_path": str(md_path)}, indent=2))


if __name__ == "__main__":
    main()
