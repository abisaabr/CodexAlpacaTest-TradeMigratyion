from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[2]
DEFAULT_REGISTRY_JSON = REPO_ROOT / "docs" / "tournament_profiles" / "tournament_profile_registry.json"
DEFAULT_EXECUTION_HANDOFF_JSON = REPO_ROOT / "docs" / "execution_calibration" / "execution_calibration_handoff.json"
DEFAULT_REPORT_DIR = REPO_ROOT / "docs" / "tournament_profiles"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build a machine-readable tournament-profile handoff that resolves the nightly profile from the profile registry and execution-calibration policy."
    )
    parser.add_argument("--registry-json", default=str(DEFAULT_REGISTRY_JSON))
    parser.add_argument("--execution-handoff-json", default=str(DEFAULT_EXECUTION_HANDOFF_JSON))
    parser.add_argument("--report-dir", default=str(DEFAULT_REPORT_DIR))
    parser.add_argument("--requested-profile", default="auto")
    return parser


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def evidence_strength_rank(value: str) -> int:
    order = {
        "no_recent_trade_sessions": 0,
        "limited_entry_only": 1,
        "entry_only": 2,
        "limited_entry_and_reconciliation": 3,
        "entry_and_reconciliation": 4,
        "limited": 5,
        "broad": 6,
    }
    return order.get(value, 0)


def risk_tier_rank(value: str) -> int:
    return {"conservative": 0, "moderate": 1, "aggressive": 2}.get(value, 1)


def _risk_bonus(posture: str, tier: str) -> tuple[int, str]:
    matrix = {
        "caution": {"conservative": 15, "moderate": 5, "aggressive": -15},
        "watch": {"conservative": 10, "moderate": 5, "aggressive": -5},
        "stable": {"conservative": 0, "moderate": 5, "aggressive": 10},
    }
    bonus = matrix.get(posture, matrix["watch"]).get(tier, 0)
    return bonus, f"posture {posture} favors {tier} risk tier ({bonus:+d})"


def _penalty_from_scale(scale: str, base: dict[str, int]) -> int:
    return base.get(scale, 0)


def score_profile(profile: dict[str, Any], execution_handoff: dict[str, Any]) -> tuple[int, list[str]]:
    posture = str(((execution_handoff.get("posture") or {}).get("overall_execution_posture")) or "watch")
    flags = dict((execution_handoff.get("posture") or {}).get("flags") or {})
    policy = dict(execution_handoff.get("policy") or {})
    general_evidence_strength = str((execution_handoff.get("posture") or {}).get("evidence_strength") or "no_recent_trade_sessions")
    unlock_evidence_strength = str((execution_handoff.get("posture") or {}).get("unlock_evidence_strength") or "no_recent_trade_sessions")
    trusted_unlock_session_count = int((execution_handoff.get("posture") or {}).get("trusted_unlock_session_count") or 0)
    latest_trusted_unlock_session_age_days_raw = (execution_handoff.get("posture") or {}).get(
        "latest_trusted_unlock_session_age_days"
    )
    latest_trusted_unlock_session_age_days = (
        int(latest_trusted_unlock_session_age_days_raw)
        if latest_trusted_unlock_session_age_days_raw not in (None, "")
        else None
    )
    current_max_risk_tier = str(policy.get("max_execution_risk_tier") or "moderate")

    score = 0
    reasons: list[str] = []
    profile_id = str(profile["profile_id"])
    minimum_execution_evidence_strength = str(profile.get("minimum_execution_evidence_strength") or "limited_entry_only")
    minimum_trusted_unlock_session_count = int(profile.get("minimum_trusted_unlock_session_count", 0) or 0)
    maximum_latest_unlock_session_age_days = int(profile.get("maximum_latest_unlock_session_age_days", 0) or 0)
    requires_broker_order_audit_coverage = bool(profile.get("requires_broker_order_audit_coverage", False))
    requires_broker_activity_audit_coverage = bool(profile.get("requires_broker_activity_audit_coverage", False))
    requires_exit_telemetry = bool(profile.get("requires_exit_telemetry", False))
    current_evidence_strength = (
        unlock_evidence_strength
        if (requires_broker_order_audit_coverage or requires_broker_activity_audit_coverage)
        else general_evidence_strength
    )

    if profile_id in set(policy.get("recommended_profiles") or []):
        score += 100
        reasons.append("execution handoff explicitly recommends this profile (+100)")
    if profile_id in set(policy.get("deprioritized_profiles") or []):
        score -= 100
        reasons.append("execution handoff explicitly deprioritizes this profile (-100)")

    risk_bonus, risk_reason = _risk_bonus(posture, str(profile.get("execution_risk_tier") or "moderate"))
    score += risk_bonus
    reasons.append(risk_reason)

    if evidence_strength_rank(current_evidence_strength) < evidence_strength_rank(minimum_execution_evidence_strength):
        score -= 250
        reasons.append(
            f"current execution evidence `{current_evidence_strength}` is below the profile floor `{minimum_execution_evidence_strength}` (-250)"
        )

    if risk_tier_rank(str(profile.get("execution_risk_tier") or "moderate")) > risk_tier_rank(current_max_risk_tier):
        score -= 250
        reasons.append(
            f"current execution policy caps profile risk at `{current_max_risk_tier}`, below this profile's `{profile.get('execution_risk_tier')}` tier (-250)"
        )

    if trusted_unlock_session_count < minimum_trusted_unlock_session_count:
        score -= 250
        reasons.append(
            f"trusted unlock-grade session count `{trusted_unlock_session_count}` is below this profile's floor `{minimum_trusted_unlock_session_count}` (-250)"
        )

    if maximum_latest_unlock_session_age_days > 0 and (
        latest_trusted_unlock_session_age_days is None
        or latest_trusted_unlock_session_age_days > maximum_latest_unlock_session_age_days
    ):
        current_age = (
            str(latest_trusted_unlock_session_age_days)
            if latest_trusted_unlock_session_age_days is not None
            else "none"
        )
        score -= 250
        reasons.append(
            f"latest trusted unlock-grade session age `{current_age}` day(s) is older than this profile's freshness ceiling `{maximum_latest_unlock_session_age_days}` (-250)"
        )

    if requires_broker_order_audit_coverage and not bool(policy.get("broker_audited_profile_activation_permitted")):
        score -= 250
        reasons.append("profile requires broker-order audit coverage, which is not yet permitted by current execution policy (-250)")

    if requires_broker_activity_audit_coverage and not bool(policy.get("broker_audited_profile_activation_permitted")):
        score -= 250
        reasons.append("profile requires broker-activity audit coverage, which is not yet permitted by current execution policy (-250)")

    if requires_exit_telemetry and bool((execution_handoff.get("posture") or {}).get("flags", {}).get("exit_telemetry_gap")):
        score -= 250
        reasons.append("profile requires reliable exit telemetry, but the current execution posture still flags an exit-telemetry gap (-250)")

    if bool(flags.get("elevated_entry_friction")):
        penalty = _penalty_from_scale(
            str(profile.get("entry_friction_sensitivity") or "medium"),
            {"low": 0, "medium": 10, "high": 20},
        )
        score -= penalty
        reasons.append(f"elevated entry friction penalizes {profile.get('entry_friction_sensitivity')} sensitivity (-{penalty})")

    if bool(flags.get("exit_telemetry_gap")):
        penalty = _penalty_from_scale(
            str(profile.get("exit_model_dependency") or "medium"),
            {"low": 0, "medium": 8, "high": 15},
        )
        score -= penalty
        reasons.append(f"exit telemetry gap penalizes {profile.get('exit_model_dependency')} exit-model dependency (-{penalty})")

    preferred_bias = str(policy.get("preferred_research_bias") or "")
    profile_bias = str(profile.get("research_bias") or "")
    if preferred_bias and preferred_bias == profile_bias:
        score += 15
        reasons.append("profile research bias matches preferred execution-informed research bias (+15)")
    elif preferred_bias == "defined_risk_and_premium_defense" and profile_bias == "premium_defense_mixed":
        score += 10
        reasons.append("profile keeps a premium-defense tilt under cautious execution posture (+10)")
    elif preferred_bias == "balanced" and profile_bias == "balanced":
        score += 10
        reasons.append("profile keeps a balanced research bias under stable execution posture (+10)")

    if bool(flags.get("sample_size_limited")) and str(profile.get("execution_risk_tier")) == "aggressive":
        score -= 10
        reasons.append("sample size is still limited, so aggressive profiles are discounted (-10)")

    if bool(flags.get("high_guardrail_pressure")) and str(profile.get("execution_risk_tier")) == "aggressive":
        score -= 10
        reasons.append("recent guardrail pressure further discounts aggressive profiles (-10)")

    return score, reasons


def build_payload(registry: dict[str, Any], execution_handoff: dict[str, Any], requested_profile: str) -> dict[str, Any]:
    profiles = list(registry.get("profiles") or [])
    profile_map = {str(profile["profile_id"]): dict(profile) for profile in profiles}
    executable_profiles = [profile for profile in profiles if bool(profile.get("executable_now"))]
    evaluations: list[dict[str, Any]] = []

    for profile in profiles:
        score, reasons = score_profile(profile, execution_handoff)
        minimum_trusted_unlock_session_count = int(profile.get("minimum_trusted_unlock_session_count", 0) or 0)
        maximum_latest_unlock_session_age_days = int(profile.get("maximum_latest_unlock_session_age_days", 0) or 0)
        evaluations.append(
            {
                "profile_id": profile["profile_id"],
                "status": profile["status"],
                "executable_now": bool(profile.get("executable_now")),
                "score": score,
                "reasons": reasons,
                "execution_risk_tier": profile.get("execution_risk_tier"),
                "entry_friction_sensitivity": profile.get("entry_friction_sensitivity"),
                "exit_model_dependency": profile.get("exit_model_dependency"),
                "research_bias": profile.get("research_bias"),
                "minimum_execution_evidence_strength": profile.get("minimum_execution_evidence_strength"),
                "minimum_trusted_unlock_session_count": minimum_trusted_unlock_session_count,
                "maximum_latest_unlock_session_age_days": maximum_latest_unlock_session_age_days,
                "requires_broker_order_audit_coverage": bool(profile.get("requires_broker_order_audit_coverage", False)),
                "requires_broker_activity_audit_coverage": bool(profile.get("requires_broker_activity_audit_coverage", False)),
                "requires_exit_telemetry": bool(profile.get("requires_exit_telemetry", False)),
                "discovery_source": profile.get("discovery_source"),
                "bootstrap_ready_universe": profile.get("bootstrap_ready_universe"),
                "activation_blocked": score < 0 and any("(-250)" in reason for reason in reasons),
            }
        )

    evaluations.sort(key=lambda row: (-int(row["score"]), str(row["profile_id"])))
    executable_evaluations = [row for row in evaluations if row["executable_now"]]
    recommended_executable_profiles = (
        [row["profile_id"] for row in executable_evaluations if row["score"] == executable_evaluations[0]["score"]]
        if executable_evaluations
        else []
    )
    recommended_executable_profile = (
        recommended_executable_profiles[0]
        if recommended_executable_profiles
        else str(registry.get("default_profile") or "")
    )

    execution_policy = dict(execution_handoff.get("policy") or {})
    deprioritized_profiles = set(execution_policy.get("deprioritized_profiles") or [])
    recommended_profiles = set(execution_policy.get("recommended_profiles") or [])

    if requested_profile == "auto":
        resolved_profile = recommended_executable_profile
        resolution_mode = "auto_recommended"
        resolution_warning = ""
    else:
        resolved_profile = requested_profile
        resolution_mode = "explicit_requested"
        resolution_warning = ""
        if requested_profile not in profile_map:
            resolution_warning = "Requested profile is not present in the tournament profile registry."
        elif not bool(profile_map[requested_profile].get("executable_now")):
            resolution_warning = "Requested profile is tracked but not executable now."
        elif any(
            row["profile_id"] == requested_profile and bool(row.get("activation_blocked"))
            for row in evaluations
        ):
            resolution_mode = "explicit_requested_with_warning"
            resolution_warning = "Requested profile is executable in code, but current execution-evidence policy blocks activating it tonight."
        elif requested_profile in deprioritized_profiles:
            resolution_mode = "explicit_requested_with_warning"
            resolution_warning = "Requested profile is currently deprioritized by the execution-calibration policy."
        elif requested_profile not in recommended_profiles and requested_profile != recommended_executable_profile:
            resolution_mode = "explicit_requested_with_warning"
            resolution_warning = "Requested profile is executable, but execution-calibration policy would currently prefer a different profile."

    return {
        "generated_at": datetime.now().isoformat(),
        "registry_generated_at": registry.get("generated_at"),
        "execution_handoff_generated_at": execution_handoff.get("generated_at"),
        "requested_profile": requested_profile,
        "resolved_profile": resolved_profile,
        "resolution_mode": resolution_mode,
        "resolution_warning": resolution_warning,
        "default_profile": registry.get("default_profile"),
        "execution_posture": (execution_handoff.get("posture") or {}).get("overall_execution_posture"),
        "execution_evidence_strength": (execution_handoff.get("posture") or {}).get("evidence_strength"),
        "unlock_execution_evidence_strength": (execution_handoff.get("posture") or {}).get("unlock_evidence_strength"),
        "preferred_research_bias": execution_policy.get("preferred_research_bias"),
        "recommended_profiles_from_execution": list(execution_policy.get("recommended_profiles") or []),
        "deprioritized_profiles_from_execution": list(execution_policy.get("deprioritized_profiles") or []),
        "recommended_executable_profile": recommended_executable_profile,
        "recommended_executable_profiles": recommended_executable_profiles,
        "deprioritized_executable_profiles": [
            row["profile_id"] for row in executable_evaluations if row["profile_id"] in deprioritized_profiles
        ],
        "profile_evaluations": evaluations,
    }


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    lines: list[str] = []
    lines.append("# Tournament Profile Handoff")
    lines.append("")
    lines.append("## Resolution")
    lines.append("")
    lines.append(f"- Generated at: `{payload['generated_at']}`")
    lines.append(f"- Requested profile: `{payload['requested_profile']}`")
    lines.append(f"- Resolved profile: `{payload['resolved_profile']}`")
    lines.append(f"- Resolution mode: `{payload['resolution_mode']}`")
    lines.append(f"- Resolution warning: `{payload['resolution_warning'] or 'none'}`")
    lines.append(f"- Execution posture: `{payload['execution_posture']}`")
    lines.append(f"- Evidence strength: `{payload['execution_evidence_strength']}`")
    lines.append(f"- Unlock evidence strength: `{payload['unlock_execution_evidence_strength']}`")
    lines.append(f"- Preferred research bias: `{payload['preferred_research_bias']}`")
    lines.append(f"- Recommended executable profile: `{payload['recommended_executable_profile']}`")
    lines.append(f"- Recommended executable profiles: `{', '.join(payload['recommended_executable_profiles']) or 'none'}`")
    lines.append(f"- Deprioritized executable profiles: `{', '.join(payload['deprioritized_executable_profiles']) or 'none'}`")
    lines.append("")
    lines.append("## Execution Policy Inputs")
    lines.append("")
    lines.append(f"- Recommended profiles from execution: `{', '.join(payload['recommended_profiles_from_execution']) or 'none'}`")
    lines.append(f"- Deprioritized profiles from execution: `{', '.join(payload['deprioritized_profiles_from_execution']) or 'none'}`")
    lines.append("")
    lines.append("## Profile Scores")
    lines.append("")
    for row in payload["profile_evaluations"]:
        lines.append(f"### {row['profile_id']}")
        lines.append("")
        lines.append(f"- Score: `{row['score']}`")
        lines.append(f"- Executable now: `{str(bool(row['executable_now'])).lower()}`")
        lines.append(f"- Execution risk tier: `{row['execution_risk_tier']}`")
        lines.append(f"- Entry friction sensitivity: `{row['entry_friction_sensitivity']}`")
        lines.append(f"- Exit model dependency: `{row['exit_model_dependency']}`")
        lines.append(f"- Research bias: `{row['research_bias']}`")
        lines.append(f"- Minimum execution evidence strength: `{row['minimum_execution_evidence_strength']}`")
        lines.append(f"- Minimum trusted unlock sessions: `{row['minimum_trusted_unlock_session_count']}`")
        lines.append(f"- Maximum latest unlock-session age (days): `{row['maximum_latest_unlock_session_age_days']}`")
        lines.append(f"- Requires broker-order audit coverage: `{str(bool(row['requires_broker_order_audit_coverage'])).lower()}`")
        lines.append(f"- Requires broker-activity audit coverage: `{str(bool(row['requires_broker_activity_audit_coverage'])).lower()}`")
        lines.append(f"- Requires exit telemetry: `{str(bool(row['requires_exit_telemetry'])).lower()}`")
        lines.append(f"- Activation blocked by policy: `{str(bool(row['activation_blocked'])).lower()}`")
        lines.append(f"- Discovery source: `{row['discovery_source']}`")
        lines.append(f"- Bootstrap ready universe: `{str(bool(row['bootstrap_ready_universe'])).lower()}`")
        lines.append("- Reasons:")
        for reason in row["reasons"]:
            lines.append(f"  - {reason}")
        lines.append("")

    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    args = build_parser().parse_args()
    registry_path = Path(args.registry_json).resolve()
    execution_handoff_path = Path(args.execution_handoff_json).resolve()
    report_dir = Path(args.report_dir).resolve()
    report_dir.mkdir(parents=True, exist_ok=True)

    payload = build_payload(
        registry=read_json(registry_path),
        execution_handoff=read_json(execution_handoff_path),
        requested_profile=str(args.requested_profile),
    )
    payload["registry_json"] = str(registry_path)
    payload["execution_handoff_json"] = str(execution_handoff_path)

    json_path = report_dir / "tournament_profile_handoff.json"
    md_path = report_dir / "tournament_profile_handoff.md"
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    write_markdown(md_path, payload)
    print(json.dumps({"json_path": str(json_path), "markdown_path": str(md_path)}, indent=2))


if __name__ == "__main__":
    main()
