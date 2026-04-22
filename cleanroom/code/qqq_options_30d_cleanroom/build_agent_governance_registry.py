from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[2]
DEFAULT_OUTPUT_ROOT = ROOT / "output"
DEFAULT_REPORT_DIR = REPO_ROOT / "docs" / "agent_governance"

FALLBACK_OPERATING_MODEL: dict[str, Any] = {
    "agents": [
        {
            "agent": "Inventory Steward",
            "lane_type": "control_plane",
            "parallelism": 1,
            "writes_live_state": False,
            "scripts": ["build_strategy_repo.py", "build_ticker_family_coverage.py", "build_agent_sharding_plan.py"],
            "inputs": ["backtester_registry.csv", "backtester_ready manifests", "strategy_repo snapshots"],
            "outputs": ["strategy_repo.json", "ticker_family_coverage.md", "agent_sharding_plan.json"],
            "success_gate": "Coverage gaps and ready-universe counts are current before any new wave launches.",
            "handoff_to": ["Strategy Family Steward", "Data Prep Steward", "Bear Directional", "Bear Premium", "Bear Convexity", "Butterfly Lab"],
            "notes": "Owns universe accounting and under-tested family/ticker ranking.",
        },
        {
            "agent": "Strategy Family Steward",
            "lane_type": "control_plane",
            "parallelism": 1,
            "writes_live_state": False,
            "scripts": ["build_strategy_family_registry.py", "build_strategy_family_handoff.py"],
            "inputs": ["strategy repo snapshot", "live manifest", "ticker-family coverage"],
            "outputs": ["strategy_family_registry.json", "strategy_family_handoff.json"],
            "success_gate": "Family priorities are refreshed before major research or review waves.",
            "handoff_to": ["Strategy Architect", "Inventory Steward", "Reporting Steward"],
            "notes": "Single owner of family taxonomy and family-priority labels.",
        },
        {
            "agent": "Data Prep Steward",
            "lane_type": "control_plane",
            "parallelism": 1,
            "writes_live_state": False,
            "scripts": ["materialize_backtester_ready.py"],
            "inputs": ["staged bundle zips", "registry-only symbols", "coverage prep frontier"],
            "outputs": ["expanded backtester_ready universe", "materialization_status.json"],
            "success_gate": "Priority symbols are materialized before discovery consumes them.",
            "handoff_to": ["Inventory Steward", "Bear Directional", "Bear Premium", "Bear Convexity", "Butterfly Lab"],
            "notes": "Keeps data prep separate from research execution.",
        },
        {
            "agent": "Strategy Architect",
            "lane_type": "control_plane",
            "parallelism": 1,
            "writes_live_state": False,
            "scripts": ["backtest_qqq_greeks_portfolio.py", "run_multiticker_cleanroom_portfolio.py"],
            "inputs": ["family registry", "coverage", "postmortem findings"],
            "outputs": ["new family definitions", "parameter-surface changes"],
            "success_gate": "New families are wired into reporting before runners use them.",
            "handoff_to": ["Inventory Steward", "Balanced Expansion"],
            "notes": "Single editor of strategy-family definitions.",
        },
        {
            "agent": "Bear Directional",
            "lane_type": "discovery",
            "parallelism": 1,
            "writes_live_state": False,
            "strategy_set": "down_choppy_only",
            "selection_profile": "down_choppy_focus",
            "family_include_filters": ["single_leg_long_put", "debit_put_spread"],
            "scripts": ["launch_down_choppy_family_wave.ps1", "run_multiticker_cleanroom_portfolio.py"],
            "inputs": ["ready tickers", "coverage-ranked cohort lists"],
            "outputs": ["per-lane research_dir", "per-ticker summaries", "run_manifest.json"],
            "success_gate": "No promotions. Survivors must show friction-aware strength.",
            "handoff_to": ["Reporting Steward"],
            "notes": "Discovery lane for bearish directional structures only.",
        },
        {
            "agent": "Bear Premium",
            "lane_type": "discovery",
            "parallelism": 1,
            "writes_live_state": False,
            "strategy_set": "down_choppy_only",
            "selection_profile": "down_choppy_focus",
            "family_include_filters": ["credit_call_spread", "iron_condor", "iron_butterfly"],
            "scripts": ["launch_down_choppy_family_wave.ps1", "run_multiticker_cleanroom_portfolio.py"],
            "inputs": ["ready tickers", "coverage-ranked cohort lists"],
            "outputs": ["per-lane research_dir", "per-ticker summaries", "run_manifest.json"],
            "success_gate": "No promotions. Survivors must show friction-aware strength.",
            "handoff_to": ["Reporting Steward"],
            "notes": "Discovery lane for premium-defense structures only.",
        },
        {
            "agent": "Bear Convexity",
            "lane_type": "discovery",
            "parallelism": 1,
            "writes_live_state": False,
            "strategy_set": "down_choppy_only",
            "selection_profile": "down_choppy_focus",
            "family_include_filters": ["put_backspread", "long_straddle", "long_strangle"],
            "scripts": ["launch_down_choppy_family_wave.ps1", "run_multiticker_cleanroom_portfolio.py"],
            "inputs": ["ready tickers", "coverage-ranked cohort lists"],
            "outputs": ["per-lane research_dir", "per-ticker summaries", "run_manifest.json"],
            "success_gate": "No promotions. Survivors must show friction-aware strength.",
            "handoff_to": ["Reporting Steward"],
            "notes": "Discovery lane for convexity and long-vol structures only.",
        },
        {
            "agent": "Butterfly Lab",
            "lane_type": "discovery",
            "parallelism": 1,
            "writes_live_state": False,
            "strategy_set": "down_choppy_only",
            "selection_profile": "down_choppy_focus",
            "family_include_filters": ["put_butterfly", "broken_wing_put_butterfly"],
            "scripts": ["launch_down_choppy_family_wave.ps1", "run_multiticker_cleanroom_portfolio.py"],
            "inputs": ["ready tickers", "coverage-ranked cohort lists"],
            "outputs": ["per-lane research_dir", "per-ticker summaries", "run_manifest.json"],
            "success_gate": "No promotions. Survivors must show friction-aware strength.",
            "handoff_to": ["Reporting Steward"],
            "notes": "Discovery lane for butterfly structures only.",
        },
        {
            "agent": "Down/Choppy Exhaustive",
            "lane_type": "deep_dive",
            "parallelism": 1,
            "writes_live_state": False,
            "strategy_set": "down_choppy_exhaustive",
            "selection_profile": "down_choppy_focus",
            "scripts": ["build_family_wave_shortlist.py", "launch_down_choppy_program.ps1"],
            "inputs": ["Phase 1 shortlist", "friction-aware lane summaries"],
            "outputs": ["deep walkforward summaries", "family rankings", "run manifests"],
            "success_gate": "Only shortlisted survivors advance into this phase.",
            "handoff_to": ["Shared-Account Validator", "Reporting Steward"],
            "notes": "Exhaustive validation lane for down/choppy survivors.",
        },
        {
            "agent": "Balanced Expansion",
            "lane_type": "deep_dive",
            "parallelism": 1,
            "writes_live_state": False,
            "strategy_set": "family_expansion",
            "selection_profile": "balanced",
            "scripts": ["run_core_strategy_expansion_overnight.py", "run_multiticker_cleanroom_portfolio.py"],
            "inputs": ["Phase 1 shortlist", "benchmark symbols", "friction-aware lane summaries"],
            "outputs": ["balanced walkforward summaries", "family rankings", "run manifests"],
            "success_gate": "Cross-regime benchmark names and validated survivors only.",
            "handoff_to": ["Shared-Account Validator", "Reporting Steward"],
            "notes": "Deep-dive lane for balanced cross-regime validation.",
        },
        {
            "agent": "Shared-Account Validator",
            "lane_type": "validation",
            "parallelism": 1,
            "writes_live_state": False,
            "strategy_set": "promotion_review",
            "selection_profile": "portfolio_first",
            "scripts": ["validate_program_live_book.py", "run_multiticker_cleanroom_portfolio.py"],
            "inputs": ["deep-dive winners", "current live manifest", "shared-account baselines"],
            "outputs": ["live_book_validation.json", "shared-account comparisons"],
            "success_gate": "Only portfolio-improving challengers may advance.",
            "handoff_to": ["Reporting Steward", "Promotion Steward"],
            "notes": "Single serialized validation lane by design.",
        },
        {
            "agent": "Reporting Steward",
            "lane_type": "control_plane",
            "parallelism": 1,
            "writes_live_state": False,
            "scripts": ["build_family_wave_shortlist.py", "build_live_book_morning_handoff.py", "build_run_registry_report.py"],
            "inputs": ["lane summaries", "validation outputs", "run manifests"],
            "outputs": ["shortlist packets", "replacement plan", "morning handoff", "run registry report"],
            "success_gate": "Reports must separate discovery, validation, and production-ready evidence.",
            "handoff_to": ["Promotion Steward"],
            "notes": "Turns raw results into operator-readable decision packets.",
        },
        {
            "agent": "Promotion Steward",
            "lane_type": "single_writer",
            "parallelism": 1,
            "writes_live_state": True,
            "scripts": ["export_promoted_strategies.py", "wait_and_sync_live_manifest.ps1"],
            "inputs": ["approved promoted_strategies.yaml", "shared-account validation", "current live manifest"],
            "outputs": ["merged live manifest", "GitHub commit/push", "promotion audit trail"],
            "success_gate": "Exactly one writer. Never shrink the live universe accidentally.",
            "handoff_to": [],
            "notes": "The only role allowed to mutate the live book.",
        },
    ]
}


ROLE_OVERRIDES: dict[str, dict[str, Any]] = {
    "Inventory Steward": {
        "plane": "control",
        "split_axis": "governance",
        "automation_level": "autonomous",
        "approval_level": "packet_only",
        "preferred_machine_now": "current_research_machine",
        "preferred_machine_target": "either_machine",
        "may_launch_backtests": False,
        "may_edit_strategy_code": False,
        "may_materialize_data": False,
        "may_write_live_manifest": False,
        "may_update_runner_gate": False,
        "may_publish_review_packets": True,
        "prohibited_actions": [
            "write_live_manifest",
            "approve_production_changes",
            "edit_strategy_family_definitions",
        ],
    },
    "Strategy Family Steward": {
        "plane": "control",
        "split_axis": "family_taxonomy",
        "automation_level": "autonomous",
        "approval_level": "packet_only",
        "preferred_machine_now": "current_research_machine",
        "preferred_machine_target": "either_machine",
        "may_launch_backtests": False,
        "may_edit_strategy_code": False,
        "may_materialize_data": False,
        "may_write_live_manifest": False,
        "may_update_runner_gate": False,
        "may_publish_review_packets": True,
        "prohibited_actions": [
            "write_live_manifest",
            "approve_production_changes",
        ],
    },
    "Data Prep Steward": {
        "plane": "research",
        "split_axis": "data_readiness",
        "automation_level": "autonomous",
        "approval_level": "packet_only",
        "preferred_machine_now": "current_research_machine",
        "preferred_machine_target": "either_machine",
        "may_launch_backtests": False,
        "may_edit_strategy_code": False,
        "may_materialize_data": True,
        "may_write_live_manifest": False,
        "may_update_runner_gate": False,
        "may_publish_review_packets": True,
        "prohibited_actions": [
            "write_live_manifest",
            "approve_production_changes",
            "launch_discovery_without_refreshed_coverage",
        ],
    },
    "Strategy Architect": {
        "plane": "research",
        "split_axis": "strategy_surface",
        "automation_level": "human_guided",
        "approval_level": "human_gated",
        "preferred_machine_now": "current_research_machine",
        "preferred_machine_target": "current_research_machine",
        "may_launch_backtests": False,
        "may_edit_strategy_code": True,
        "may_materialize_data": False,
        "may_write_live_manifest": False,
        "may_update_runner_gate": False,
        "may_publish_review_packets": False,
        "prohibited_actions": [
            "write_live_manifest",
            "auto_promote_new_families",
        ],
    },
    "Bear Directional": {
        "plane": "research",
        "split_axis": "family_cohort",
        "automation_level": "autonomous",
        "approval_level": "packet_only",
        "preferred_machine_now": "current_research_machine",
        "preferred_machine_target": "either_machine",
        "may_launch_backtests": True,
        "may_edit_strategy_code": False,
        "may_materialize_data": False,
        "may_write_live_manifest": False,
        "may_update_runner_gate": False,
        "may_publish_review_packets": False,
        "prohibited_actions": [
            "write_live_manifest",
            "expand_scope_beyond_assigned_family_lane",
        ],
    },
    "Bear Premium": {
        "plane": "research",
        "split_axis": "family_cohort",
        "automation_level": "autonomous",
        "approval_level": "packet_only",
        "preferred_machine_now": "current_research_machine",
        "preferred_machine_target": "either_machine",
        "may_launch_backtests": True,
        "may_edit_strategy_code": False,
        "may_materialize_data": False,
        "may_write_live_manifest": False,
        "may_update_runner_gate": False,
        "may_publish_review_packets": False,
        "prohibited_actions": [
            "write_live_manifest",
            "expand_scope_beyond_assigned_family_lane",
        ],
    },
    "Bear Convexity": {
        "plane": "research",
        "split_axis": "family_cohort",
        "automation_level": "autonomous",
        "approval_level": "packet_only",
        "preferred_machine_now": "current_research_machine",
        "preferred_machine_target": "either_machine",
        "may_launch_backtests": True,
        "may_edit_strategy_code": False,
        "may_materialize_data": False,
        "may_write_live_manifest": False,
        "may_update_runner_gate": False,
        "may_publish_review_packets": False,
        "prohibited_actions": [
            "write_live_manifest",
            "expand_scope_beyond_assigned_family_lane",
        ],
    },
    "Butterfly Lab": {
        "plane": "research",
        "split_axis": "family_cohort",
        "automation_level": "autonomous",
        "approval_level": "packet_only",
        "preferred_machine_now": "current_research_machine",
        "preferred_machine_target": "either_machine",
        "may_launch_backtests": True,
        "may_edit_strategy_code": False,
        "may_materialize_data": False,
        "may_write_live_manifest": False,
        "may_update_runner_gate": False,
        "may_publish_review_packets": False,
        "prohibited_actions": [
            "write_live_manifest",
            "expand_scope_beyond_assigned_family_lane",
        ],
    },
    "Down/Choppy Exhaustive": {
        "plane": "research",
        "split_axis": "ticker_bundle",
        "automation_level": "autonomous",
        "approval_level": "packet_only",
        "preferred_machine_now": "current_research_machine",
        "preferred_machine_target": "either_machine",
        "may_launch_backtests": True,
        "may_edit_strategy_code": False,
        "may_materialize_data": False,
        "may_write_live_manifest": False,
        "may_update_runner_gate": False,
        "may_publish_review_packets": False,
        "prohibited_actions": [
            "write_live_manifest",
            "widen_back_to_full_discovery_scope",
        ],
    },
    "Balanced Expansion": {
        "plane": "research",
        "split_axis": "ticker_bundle",
        "automation_level": "autonomous",
        "approval_level": "packet_only",
        "preferred_machine_now": "current_research_machine",
        "preferred_machine_target": "either_machine",
        "may_launch_backtests": True,
        "may_edit_strategy_code": False,
        "may_materialize_data": False,
        "may_write_live_manifest": False,
        "may_update_runner_gate": False,
        "may_publish_review_packets": False,
        "prohibited_actions": [
            "write_live_manifest",
            "skip_shortlist_or_validation_provenance",
        ],
    },
    "Shared-Account Validator": {
        "plane": "research",
        "split_axis": "portfolio_context",
        "automation_level": "autonomous",
        "approval_level": "packet_only",
        "preferred_machine_now": "current_research_machine",
        "preferred_machine_target": "new_machine",
        "may_launch_backtests": True,
        "may_edit_strategy_code": False,
        "may_materialize_data": False,
        "may_write_live_manifest": False,
        "may_update_runner_gate": False,
        "may_publish_review_packets": True,
        "prohibited_actions": [
            "write_live_manifest",
            "approve_production_changes",
            "treat_standalone_strength_as_production_ready",
        ],
    },
    "Reporting Steward": {
        "plane": "control",
        "split_axis": "review_packet",
        "automation_level": "autonomous",
        "approval_level": "packet_only",
        "preferred_machine_now": "current_research_machine",
        "preferred_machine_target": "either_machine",
        "may_launch_backtests": False,
        "may_edit_strategy_code": False,
        "may_materialize_data": False,
        "may_write_live_manifest": False,
        "may_update_runner_gate": True,
        "may_publish_review_packets": True,
        "prohibited_actions": [
            "write_live_manifest",
            "approve_production_changes",
        ],
    },
    "Promotion Steward": {
        "plane": "execution",
        "split_axis": "live_book",
        "automation_level": "human_gated",
        "approval_level": "human_gated",
        "preferred_machine_now": "new_machine",
        "preferred_machine_target": "new_machine",
        "may_launch_backtests": False,
        "may_edit_strategy_code": False,
        "may_materialize_data": False,
        "may_write_live_manifest": True,
        "may_update_runner_gate": True,
        "may_publish_review_packets": False,
        "prohibited_actions": [
            "run_parallel_live_manifest_writers",
            "push_unreviewed_manifest_changes",
        ],
    },
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build a machine-readable agent governance registry from the operating model."
    )
    parser.add_argument(
        "--operating-model-json",
        default="",
        help="Optional explicit path to agent_operating_model.json. If omitted, the newest one under output/ is used.",
    )
    parser.add_argument(
        "--output-root",
        default=str(DEFAULT_OUTPUT_ROOT),
        help="Output root used to discover the latest agent_operating_model.json when not passed explicitly.",
    )
    parser.add_argument(
        "--report-dir",
        default=str(DEFAULT_REPORT_DIR),
        help="Directory where the governance registry artifacts will be written.",
    )
    return parser


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames = sorted({key for row in rows for key in row.keys()})
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    key: json.dumps(value) if isinstance(value, (list, dict)) else value
                    for key, value in row.items()
                }
            )


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def resolve_operating_model_json(path: str, output_root: Path) -> Path | None:
    if path:
        resolved = Path(path).resolve()
        if not resolved.exists():
            raise FileNotFoundError(f"Explicit operating model json does not exist: {resolved}")
        return resolved

    candidates = sorted(
        output_root.rglob("agent_operating_model.json"),
        key=lambda candidate: candidate.stat().st_mtime,
        reverse=True,
    )
    if not candidates:
        return None
    return candidates[0].resolve()


def load_or_build_operating_model(path: str, output_root: Path) -> tuple[dict[str, Any], str]:
    source_path = resolve_operating_model_json(path, output_root)
    if source_path is not None:
        return load_json(source_path), str(source_path)

    return FALLBACK_OPERATING_MODEL, "embedded_fallback_operating_model"


def normalize_row(row: dict[str, Any]) -> dict[str, Any]:
    agent = str(row.get("agent", ""))
    override = ROLE_OVERRIDES.get(agent, {})
    writes_live_state = bool(row.get("writes_live_state", False))
    lane_type = str(row.get("lane_type", ""))
    split_axis = str(override.get("split_axis", "governance" if lane_type == "control_plane" else "ticker_bundle"))
    automation_level = str(
        override.get(
            "automation_level",
            "human_gated" if writes_live_state else "autonomous",
        )
    )
    approval_level = str(
        override.get(
            "approval_level",
            "human_gated" if writes_live_state else "packet_only",
        )
    )
    plane = str(
        override.get(
            "plane",
            "execution" if writes_live_state else ("control" if lane_type == "control_plane" else "research"),
        )
    )
    may_publish_review_packets = bool(override.get("may_publish_review_packets", lane_type == "control_plane"))
    may_update_runner_gate = bool(override.get("may_update_runner_gate", agent in {"Reporting Steward", "Promotion Steward"}))
    may_launch_backtests = bool(override.get("may_launch_backtests", lane_type in {"discovery", "deep_dive", "validation"}))
    may_edit_strategy_code = bool(override.get("may_edit_strategy_code", False))
    may_materialize_data = bool(override.get("may_materialize_data", False))
    may_write_live_manifest = bool(override.get("may_write_live_manifest", writes_live_state))

    return {
        "agent": agent,
        "plane": plane,
        "lane_type": lane_type,
        "split_axis": split_axis,
        "parallelism": int(row.get("parallelism", 1)),
        "strategy_set": str(row.get("strategy_set", "")),
        "selection_profile": str(row.get("selection_profile", "")),
        "family_include_filters": list(row.get("family_include_filters", [])),
        "automation_level": automation_level,
        "approval_level": approval_level,
        "preferred_machine_now": str(override.get("preferred_machine_now", "current_research_machine")),
        "preferred_machine_target": str(override.get("preferred_machine_target", "either_machine")),
        "writes_live_state": writes_live_state,
        "may_launch_backtests": may_launch_backtests,
        "may_edit_strategy_code": may_edit_strategy_code,
        "may_materialize_data": may_materialize_data,
        "may_write_live_manifest": may_write_live_manifest,
        "may_update_runner_gate": may_update_runner_gate,
        "may_publish_review_packets": may_publish_review_packets,
        "scripts": list(row.get("scripts", [])),
        "inputs": list(row.get("inputs", [])),
        "outputs": list(row.get("outputs", [])),
        "success_gate": str(row.get("success_gate", "")),
        "handoff_to": list(row.get("handoff_to", [])),
        "notes": str(row.get("notes", "")),
        "prohibited_actions": list(override.get("prohibited_actions", [])),
    }


def build_payload(operating_model: dict[str, Any], *, source_path: str) -> dict[str, Any]:
    rows = [normalize_row(row) for row in operating_model.get("agents", [])]
    split_summary: dict[str, list[str]] = {}
    for row in rows:
        split_summary.setdefault(row["split_axis"], []).append(row["agent"])
    for key in list(split_summary):
        split_summary[key] = sorted(split_summary[key])

    return {
        "generated_at": datetime.now().isoformat(),
        "source_operating_model_json": source_path,
        "institutional_rules": [
            "Discovery should be assigned by family cohort to avoid overlap and improve frontier coverage.",
            "Exhaustive follow-up should be assigned by ticker bundle so symbol-specific fit is validated on survivors instead of on the full universe.",
            "Shared-account validation must remain serialized and portfolio-context aware.",
            "Only the Promotion Steward may write the live manifest or finalize production-book mutations.",
            "Control-plane stewards may publish packets and gates, but not production strategy changes.",
        ],
        "split_recommendation": {
            "discovery": "family_cohort",
            "exhaustive_validation": "ticker_bundle",
            "shared_account_validation": "portfolio_context",
            "production_decision": "live_book_single_writer",
        },
        "agents": rows,
        "split_summary": split_summary,
    }


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    lines: list[str] = []
    lines.append("# Agent Governance Registry")
    lines.append("")
    lines.append("This registry turns the operating model into machine-readable governance.")
    lines.append("")
    lines.append("## Institutional Rules")
    lines.append("")
    for item in payload["institutional_rules"]:
        lines.append(f"- {item}")
    lines.append("")
    lines.append("## Split Recommendation")
    lines.append("")
    for key, value in payload["split_recommendation"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.append("")
    lines.append("## Agent Contracts")
    lines.append("")
    for row in payload["agents"]:
        lines.append(f"### {row['agent']}")
        lines.append("")
        lines.append(f"- Plane: `{row['plane']}`")
        lines.append(f"- Lane type: `{row['lane_type']}`")
        lines.append(f"- Split axis: `{row['split_axis']}`")
        lines.append(f"- Automation level: `{row['automation_level']}`")
        lines.append(f"- Approval level: `{row['approval_level']}`")
        lines.append(f"- Preferred machine now: `{row['preferred_machine_now']}`")
        lines.append(f"- Preferred machine target: `{row['preferred_machine_target']}`")
        lines.append(f"- Writes live state: `{str(row['writes_live_state']).lower()}`")
        lines.append(f"- May launch backtests: `{str(row['may_launch_backtests']).lower()}`")
        lines.append(f"- May edit strategy code: `{str(row['may_edit_strategy_code']).lower()}`")
        lines.append(f"- May materialize data: `{str(row['may_materialize_data']).lower()}`")
        lines.append(f"- May write live manifest: `{str(row['may_write_live_manifest']).lower()}`")
        lines.append(f"- May update runner gate: `{str(row['may_update_runner_gate']).lower()}`")
        lines.append(f"- May publish review packets: `{str(row['may_publish_review_packets']).lower()}`")
        if row["strategy_set"]:
            lines.append(f"- Strategy set: `{row['strategy_set']}`")
        if row["selection_profile"]:
            lines.append(f"- Selection profile: `{row['selection_profile']}`")
        if row["family_include_filters"]:
            lines.append(f"- Family filters: `{','.join(row['family_include_filters'])}`")
        lines.append(f"- Success gate: {row['success_gate']}")
        if row["handoff_to"]:
            lines.append(f"- Hands off to: {', '.join(row['handoff_to'])}")
        if row["prohibited_actions"]:
            lines.append(f"- Prohibited actions: {', '.join(f'`{item}`' for item in row['prohibited_actions'])}")
        lines.append(f"- Notes: {row['notes']}")
        lines.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = build_parser().parse_args()
    output_root = Path(args.output_root).resolve()
    report_dir = Path(args.report_dir).resolve()
    report_dir.mkdir(parents=True, exist_ok=True)

    operating_model, source_path = load_or_build_operating_model(args.operating_model_json, output_root)
    payload = build_payload(operating_model, source_path=source_path)

    write_json(report_dir / "agent_governance_registry.json", payload)
    write_csv(report_dir / "agent_governance_registry.csv", payload["agents"])
    write_markdown(report_dir / "agent_governance_registry.md", payload)
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
