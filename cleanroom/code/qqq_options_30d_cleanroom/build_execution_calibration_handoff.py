from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[2]
DEFAULT_REGISTRY_JSON = REPO_ROOT / "docs" / "execution_calibration" / "execution_calibration_registry.json"
DEFAULT_REPORT_DIR = REPO_ROOT / "docs" / "execution_calibration"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build a concise execution-calibration steward handoff from the formal execution calibration registry."
    )
    parser.add_argument("--registry-json", default=str(DEFAULT_REGISTRY_JSON))
    parser.add_argument("--report-dir", default=str(DEFAULT_REPORT_DIR))
    parser.add_argument("--top-n", type=int, default=5)
    return parser


def determine_posture(payload: dict[str, Any]) -> dict[str, Any]:
    summary = dict(payload.get("summary") or {})
    data_quality = dict(payload.get("data_quality") or {})

    completed_trade_count = int(summary.get("completed_trade_count", 0) or 0)
    severe_loss_sessions = int(summary.get("severe_loss_flatten_session_count", 0) or 0)
    broker_audit_sessions = int(summary.get("sessions_with_broker_order_audit", 0) or 0)
    broker_status_mismatch_count = int(summary.get("broker_status_mismatch_count_total", 0) or 0)
    unmatched_local_order_count = int(summary.get("local_order_without_broker_match_count_total", 0) or 0)
    ending_broker_position_count = int(summary.get("ending_broker_position_count_total", 0) or 0)
    partial_fill_count = int(summary.get("broker_partially_filled_order_count_total", 0) or 0)
    entry_mean_pct = float(((summary.get("entry_abs_slippage_pct_of_expected") or {}).get("mean") or 0.0))
    event_mean_pct = float(((summary.get("event_entry_adverse_slippage_pct") or {}).get("mean") or 0.0))
    exit_obs = int(data_quality.get("exit_slippage_observations", 0) or 0)

    sample_size_limited = completed_trade_count < 25
    high_guardrail_pressure = severe_loss_sessions > 0
    elevated_entry_friction = entry_mean_pct >= 0.75 or event_mean_pct >= 1.25
    exit_telemetry_gap = exit_obs == 0
    reconciliation_pressure = (
        broker_status_mismatch_count > 0
        or unmatched_local_order_count > 0
        or ending_broker_position_count > 0
    )
    partial_fill_pressure = partial_fill_count > 0
    broker_audit_gap = broker_audit_sessions == 0

    if (high_guardrail_pressure and elevated_entry_friction) or (
        reconciliation_pressure and (partial_fill_pressure or exit_telemetry_gap)
    ):
        posture = "caution"
    elif (
        high_guardrail_pressure
        or elevated_entry_friction
        or exit_telemetry_gap
        or reconciliation_pressure
        or partial_fill_pressure
        or broker_audit_gap
    ):
        posture = "watch"
    else:
        posture = "stable"

    if exit_telemetry_gap and broker_audit_gap and sample_size_limited:
        evidence_strength = "limited_entry_only"
    elif exit_telemetry_gap and broker_audit_gap:
        evidence_strength = "entry_only"
    elif exit_telemetry_gap and sample_size_limited:
        evidence_strength = "limited_entry_and_reconciliation"
    elif exit_telemetry_gap:
        evidence_strength = "entry_and_reconciliation"
    elif sample_size_limited:
        evidence_strength = "limited"
    else:
        evidence_strength = "broad"

    return {
        "overall_execution_posture": posture,
        "evidence_strength": evidence_strength,
        "flags": {
            "sample_size_limited": sample_size_limited,
            "high_guardrail_pressure": high_guardrail_pressure,
            "elevated_entry_friction": elevated_entry_friction,
            "exit_telemetry_gap": exit_telemetry_gap,
            "reconciliation_pressure": reconciliation_pressure,
            "partial_fill_pressure": partial_fill_pressure,
            "broker_audit_gap": broker_audit_gap,
        },
    }


def policy_recommendations(payload: dict[str, Any], posture: dict[str, Any]) -> dict[str, Any]:
    summary = dict(payload.get("summary") or {})
    flags = dict(posture.get("flags") or {})

    entry_mean_pct = float(((summary.get("entry_abs_slippage_pct_of_expected") or {}).get("mean") or 0.0))
    event_mean_pct = float(((summary.get("event_entry_adverse_slippage_pct") or {}).get("mean") or 0.0))

    if flags["elevated_entry_friction"]:
        entry_penalty_mode = "raised"
    else:
        entry_penalty_mode = "standard"

    if flags["high_guardrail_pressure"] or flags["reconciliation_pressure"]:
        opening_window_debit_posture = "caution"
        preferred_research_bias = "defined_risk_and_premium_defense"
    else:
        opening_window_debit_posture = "normal"
        preferred_research_bias = "balanced"

    if flags["exit_telemetry_gap"] or flags["reconciliation_pressure"]:
        exit_model_posture = "conservative_fallback"
    else:
        exit_model_posture = "observed_exit_calibration"

    recommended_profiles: list[str] = ["down_choppy_coverage_ranked"]
    if flags["high_guardrail_pressure"] or flags["elevated_entry_friction"] or flags["reconciliation_pressure"]:
        recommended_profiles.append("opening_30m_premium_defense")
    else:
        recommended_profiles.append("opening_30m_single_vs_multileg")

    deprioritized_profiles: list[str] = []
    if flags["high_guardrail_pressure"] or flags["sample_size_limited"]:
        deprioritized_profiles.append("opening_30m_convexity_butterfly")
    if (flags["high_guardrail_pressure"] and flags["elevated_entry_friction"]) or flags["reconciliation_pressure"]:
        deprioritized_profiles.append("opening_30m_single_vs_multileg")

    operator_actions = [
        f"Use `{entry_penalty_mode}` entry-fill penalties while observed entry friction remains around {entry_mean_pct:.2f}% mean absolute slippage and {event_mean_pct:.2f}% mean adverse event slippage.",
        "Keep exit-side execution modeling conservative until explicit exit slippage telemetry becomes reliable.",
    ]
    if flags["high_guardrail_pressure"]:
        operator_actions.append("Favor premium-defense and defined-risk opening-window challengers before adding more aggressive debit-heavy opening profiles.")
    if flags["sample_size_limited"]:
        operator_actions.append("Treat current execution evidence as directional rather than fully authoritative because the completed-trade sample is still small.")
    if flags["reconciliation_pressure"]:
        operator_actions.append("Inspect broker-order audit mismatches, unmatched local orders, and residual broker positions before trusting combo-heavy challengers or loosening exit assumptions.")
    if flags["partial_fill_pressure"]:
        operator_actions.append("Favor simpler exits, smaller size caps, and stronger cleanup assumptions while partial-fill pressure remains visible in broker audit artifacts.")
    if flags["broker_audit_gap"]:
        operator_actions.append("Treat broker-order audit coverage itself as a telemetry gap until upgraded session bundles start landing from the execution machine.")

    return {
        "entry_penalty_mode": entry_penalty_mode,
        "exit_model_posture": exit_model_posture,
        "opening_window_debit_posture": opening_window_debit_posture,
        "preferred_research_bias": preferred_research_bias,
        "recommended_profiles": recommended_profiles,
        "deprioritized_profiles": deprioritized_profiles,
        "operator_actions": operator_actions,
    }


def top_rows(rows: list[dict[str, Any]], key_name: str, top_n: int) -> list[dict[str, Any]]:
    return [dict(row) for row in rows[:top_n] if row.get(key_name)]


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    posture = payload["posture"]
    policies = payload["policy"]
    lines: list[str] = []
    lines.append("# Execution Calibration Handoff")
    lines.append("")
    lines.append("## Snapshot")
    lines.append("")
    lines.append(f"- Generated at: `{payload['generated_at']}`")
    lines.append(f"- Posture: `{posture['overall_execution_posture']}`")
    lines.append(f"- Evidence strength: `{posture['evidence_strength']}`")
    lines.append("")
    lines.append("## Flags")
    lines.append("")
    for key, value in posture["flags"].items():
        lines.append(f"- `{key}`: `{str(bool(value)).lower()}`")
    lines.append("")
    lines.append("## Policy Guidance")
    lines.append("")
    lines.append(f"- Entry penalty mode: `{policies['entry_penalty_mode']}`")
    lines.append(f"- Exit model posture: `{policies['exit_model_posture']}`")
    lines.append(f"- Opening-window debit posture: `{policies['opening_window_debit_posture']}`")
    lines.append(f"- Preferred research bias: `{policies['preferred_research_bias']}`")
    lines.append(f"- Recommended profiles: `{', '.join(policies['recommended_profiles'])}`")
    lines.append(f"- Deprioritized profiles: `{', '.join(policies['deprioritized_profiles']) or 'none'}`")
    lines.append("")
    lines.append("## Operator Actions")
    lines.append("")
    for action in policies["operator_actions"]:
        lines.append(f"- {action}")
    lines.append("")
    lines.append("## Top Entry Slippage Clusters")
    lines.append("")
    for row in payload["top_entry_slippage_clusters"]:
        lines.append(
            f"- `{row['ticker']}`: mean absolute entry slippage `{(row.get('entry_abs_slippage_pct_of_expected') or {}).get('mean', 'n/a')}`% of expected across `{row.get('entry_fill_count', 0)}` filled entries"
        )
    if not payload["top_entry_slippage_clusters"]:
        lines.append("- none")
    lines.append("")
    lines.append("## Top Loss Clusters")
    lines.append("")
    for row in payload["top_loss_clusters"]:
        lines.append(
            f"- `{row['strategy_name']}`: estimated total net PnL `{float(row.get('net_pnl_total_estimate') or 0.0):.2f}`, exit reason `{row.get('top_exit_reason') or 'n/a'}`"
        )
    if not payload["top_loss_clusters"]:
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
        "top_entry_slippage_clusters": top_rows(list(registry.get("by_ticker") or []), "ticker", int(args.top_n)),
        "top_loss_clusters": top_rows(
            sorted(
                [row for row in list(registry.get("by_strategy") or []) if row.get("completed_trade_count", 0) > 0],
                key=lambda row: (float(row.get("net_pnl_total_estimate") or 0.0), str(row.get("strategy_name", ""))),
            ),
            "strategy_name",
            int(args.top_n),
        ),
    }

    json_path = report_dir / "execution_calibration_handoff.json"
    md_path = report_dir / "execution_calibration_handoff.md"
    json_path.write_text(json.dumps(handoff, indent=2), encoding="utf-8")
    write_markdown(md_path, handoff)
    print(json.dumps({"json_path": str(json_path), "markdown_path": str(md_path)}, indent=2))


if __name__ == "__main__":
    main()
