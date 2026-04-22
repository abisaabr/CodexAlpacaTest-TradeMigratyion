from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[2]
DEFAULT_REPORT_DIR = REPO_ROOT / "docs" / "tournament_profiles"


TOURNAMENT_PROFILES: list[dict[str, Any]] = [
    {
        "profile_id": "down_choppy_coverage_ranked",
        "status": "active",
        "executable_now": True,
        "objective": "Primary institutional nightly challenger cycle for down and choppy markets.",
        "regime_focus": ["down", "choppy"],
        "session_focus": "full_session",
        "execution_window": "all_day",
        "entrypoint": "launch_nightly_operator_cycle.ps1",
        "underlying_program": "launch_down_choppy_program.ps1",
        "discovery_source": "coverage_ranked",
        "bootstrap_ready_universe": True,
        "strategy_sets": ["down_choppy_only", "down_choppy_exhaustive"],
        "selection_profiles": ["down_choppy_focus"],
        "phase1_split_axis": "family_cohort",
        "phase2_split_axis": "ticker_bundle",
        "validation_split_axis": "portfolio_context",
        "promotion_mode": "review_only",
        "execution_risk_tier": "moderate",
        "entry_friction_sensitivity": "medium",
        "exit_model_dependency": "medium",
        "research_bias": "premium_defense_mixed",
        "preferred_machine_now": "current_research_machine",
        "preferred_machine_target": "either_machine",
        "notes": "Default nightly operator profile because it exercises the full discovery-to-morning-handoff chain without auto-promoting the live book.",
        "families": [
            "Single-leg long put",
            "Debit put spread",
            "Credit call spread",
            "Iron condor",
            "Iron butterfly",
            "Put backspread",
            "Long straddle",
            "Long strangle",
            "Put butterfly",
            "Broken-wing put butterfly",
        ],
    },
    {
        "profile_id": "down_choppy_full_ready",
        "status": "active",
        "executable_now": True,
        "objective": "Fallback nightly challenger cycle when breadth over the current ready universe matters more than gap-ranked precision.",
        "regime_focus": ["down", "choppy"],
        "session_focus": "full_session",
        "execution_window": "all_day",
        "entrypoint": "launch_nightly_operator_cycle.ps1",
        "underlying_program": "launch_down_choppy_program.ps1",
        "discovery_source": "full_ready",
        "bootstrap_ready_universe": False,
        "strategy_sets": ["down_choppy_only", "down_choppy_exhaustive"],
        "selection_profiles": ["down_choppy_focus"],
        "phase1_split_axis": "family_cohort",
        "phase2_split_axis": "ticker_bundle",
        "validation_split_axis": "portfolio_context",
        "promotion_mode": "review_only",
        "execution_risk_tier": "moderate",
        "entry_friction_sensitivity": "medium",
        "exit_model_dependency": "medium",
        "research_bias": "premium_defense_mixed",
        "preferred_machine_now": "current_research_machine",
        "preferred_machine_target": "either_machine",
        "notes": "Use when the ready universe is already broad enough and we want a direct run without extra bootstrap materialization.",
        "families": [
            "Single-leg long put",
            "Debit put spread",
            "Credit call spread",
            "Iron condor",
            "Iron butterfly",
            "Put backspread",
            "Long straddle",
            "Long strangle",
            "Put butterfly",
            "Broken-wing put butterfly",
        ],
    },
    {
        "profile_id": "opening_30m_single_vs_multileg",
        "status": "planned",
        "executable_now": False,
        "objective": "Institutional opening-window shootout between directional single-legs and defined-risk multi-leg structures.",
        "regime_focus": ["bull", "bear", "choppy"],
        "session_focus": "opening_30m",
        "execution_window": "first_30_minutes",
        "entrypoint": "planned_profile",
        "underlying_program": "not_yet_wired",
        "discovery_source": "coverage_ranked",
        "bootstrap_ready_universe": True,
        "strategy_sets": ["opening_window_single_vs_multileg"],
        "selection_profiles": ["opening_window_balanced"],
        "phase1_split_axis": "family_cohort",
        "phase2_split_axis": "ticker_bundle",
        "validation_split_axis": "portfolio_context",
        "promotion_mode": "review_only",
        "execution_risk_tier": "aggressive",
        "entry_friction_sensitivity": "high",
        "exit_model_dependency": "high",
        "research_bias": "balanced_directional_vs_multileg",
        "preferred_machine_now": "current_research_machine",
        "preferred_machine_target": "new_machine",
        "notes": "Best next structural tournament for diversifying away from the current single-leg-heavy live book, but it needs opening-window family wiring first.",
        "families": [
            "Single-leg long call",
            "Single-leg long put",
            "Debit call spread",
            "Debit put spread",
            "Credit call spread",
            "Credit put spread",
            "Iron condor",
            "Iron butterfly",
            "Call butterfly",
            "Put butterfly",
            "Call backspread",
            "Put backspread",
        ],
    },
    {
        "profile_id": "opening_30m_premium_defense",
        "status": "planned",
        "executable_now": False,
        "objective": "Focused opening-session premium-defense tournament for bear and choppy regimes.",
        "regime_focus": ["down", "choppy"],
        "session_focus": "opening_30m",
        "execution_window": "first_30_minutes",
        "entrypoint": "planned_profile",
        "underlying_program": "not_yet_wired",
        "discovery_source": "coverage_ranked",
        "bootstrap_ready_universe": True,
        "strategy_sets": ["opening_window_premium_defense"],
        "selection_profiles": ["opening_window_defensive"],
        "phase1_split_axis": "family_cohort",
        "phase2_split_axis": "ticker_bundle",
        "validation_split_axis": "portfolio_context",
        "promotion_mode": "review_only",
        "execution_risk_tier": "conservative",
        "entry_friction_sensitivity": "low",
        "exit_model_dependency": "medium",
        "research_bias": "defined_risk_and_premium_defense",
        "preferred_machine_now": "current_research_machine",
        "preferred_machine_target": "new_machine",
        "notes": "Targets the under-tested premium-defense surface that should help in weak or messy tape once session-specific timing is fully encoded.",
        "families": [
            "Credit call spread",
            "Debit put spread",
            "Iron condor",
            "Iron butterfly",
            "Put butterfly",
        ],
    },
    {
        "profile_id": "opening_30m_convexity_butterfly",
        "status": "planned",
        "executable_now": False,
        "objective": "Focused opening-session convexity and butterfly profile for early expansion or reversal moves.",
        "regime_focus": ["down", "choppy"],
        "session_focus": "opening_30m",
        "execution_window": "first_30_minutes",
        "entrypoint": "planned_profile",
        "underlying_program": "not_yet_wired",
        "discovery_source": "coverage_ranked",
        "bootstrap_ready_universe": True,
        "strategy_sets": ["opening_window_convexity_butterfly"],
        "selection_profiles": ["opening_window_convexity"],
        "phase1_split_axis": "family_cohort",
        "phase2_split_axis": "ticker_bundle",
        "validation_split_axis": "portfolio_context",
        "promotion_mode": "review_only",
        "execution_risk_tier": "aggressive",
        "entry_friction_sensitivity": "high",
        "exit_model_dependency": "high",
        "research_bias": "convexity_and_long_vol",
        "preferred_machine_now": "current_research_machine",
        "preferred_machine_target": "new_machine",
        "notes": "Cleanest planned tournament for testing whether early-session expansion favors long-vol and butterfly structures more than plain long puts.",
        "families": [
            "Put backspread",
            "Long straddle",
            "Long strangle",
            "Put butterfly",
            "Broken-wing put butterfly",
        ],
    },
    {
        "profile_id": "balanced_family_expansion_benchmark",
        "status": "partial",
        "executable_now": False,
        "objective": "Cross-regime balanced family-expansion benchmark for diversified research and replacement pressure on the live book.",
        "regime_focus": ["bull", "bear", "choppy"],
        "session_focus": "full_session",
        "execution_window": "all_day",
        "entrypoint": "manual_orchestrator",
        "underlying_program": "run_core_strategy_expansion_overnight.py",
        "discovery_source": "coverage_ranked",
        "bootstrap_ready_universe": True,
        "strategy_sets": ["family_expansion"],
        "selection_profiles": ["balanced"],
        "phase1_split_axis": "ticker_bundle",
        "phase2_split_axis": "portfolio_context",
        "validation_split_axis": "portfolio_context",
        "promotion_mode": "review_only",
        "execution_risk_tier": "moderate",
        "entry_friction_sensitivity": "medium",
        "exit_model_dependency": "medium",
        "research_bias": "balanced",
        "preferred_machine_now": "current_research_machine",
        "preferred_machine_target": "either_machine",
        "notes": "Already executable as a research program, but not yet wired into the single-command nightly operator cycle.",
        "families": [
            "Single-leg long call",
            "Single-leg long put",
            "Debit call spread",
            "Debit put spread",
            "Credit call spread",
            "Credit put spread",
            "Iron condor",
            "Iron butterfly",
            "Call butterfly",
            "Put butterfly",
            "Broken-wing call butterfly",
            "Broken-wing put butterfly",
            "Call backspread",
            "Put backspread",
            "Long straddle",
            "Long strangle",
        ],
    },
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build a machine-readable tournament profile registry for the institutional control plane."
    )
    parser.add_argument(
        "--report-dir",
        default=str(DEFAULT_REPORT_DIR),
        help="Directory where the tournament profile artifacts will be written.",
    )
    return parser


def write_json(path: Path, payload: Any) -> None:
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


def build_payload() -> dict[str, Any]:
    return {
        "generated_at": datetime.now().isoformat(),
        "default_profile": "down_choppy_coverage_ranked",
        "active_profiles": sorted([row["profile_id"] for row in TOURNAMENT_PROFILES if row["status"] == "active"]),
        "executable_profiles": sorted([row["profile_id"] for row in TOURNAMENT_PROFILES if row["executable_now"]]),
        "planned_profiles": sorted([row["profile_id"] for row in TOURNAMENT_PROFILES if row["status"] in {"planned", "partial"}]),
        "profiles": TOURNAMENT_PROFILES,
    }


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    lines: list[str] = []
    lines.append("# Tournament Profile Registry")
    lines.append("")
    lines.append("This registry is the control-plane source of truth for which institutional tournaments exist, which are executable today, and which are still planned.")
    lines.append("")
    lines.append("## Defaults")
    lines.append("")
    lines.append(f"- Default profile: `{payload['default_profile']}`")
    lines.append(f"- Active profiles: `{', '.join(payload['active_profiles'])}`")
    lines.append(f"- Executable profiles: `{', '.join(payload['executable_profiles'])}`")
    lines.append("")
    lines.append("## Profiles")
    lines.append("")
    for row in payload["profiles"]:
        lines.append(f"### {row['profile_id']}")
        lines.append("")
        lines.append(f"- Status: `{row['status']}`")
        lines.append(f"- Executable now: `{str(row['executable_now']).lower()}`")
        lines.append(f"- Objective: {row['objective']}")
        lines.append(f"- Regime focus: `{', '.join(row['regime_focus'])}`")
        lines.append(f"- Session focus: `{row['session_focus']}`")
        lines.append(f"- Execution window: `{row['execution_window']}`")
        lines.append(f"- Entrypoint: `{row['entrypoint']}`")
        lines.append(f"- Underlying program: `{row['underlying_program']}`")
        lines.append(f"- Discovery source: `{row['discovery_source']}`")
        lines.append(f"- Bootstrap ready universe: `{str(row['bootstrap_ready_universe']).lower()}`")
        lines.append(f"- Strategy sets: `{', '.join(row['strategy_sets'])}`")
        lines.append(f"- Selection profiles: `{', '.join(row['selection_profiles'])}`")
        lines.append(f"- Phase 1 split axis: `{row['phase1_split_axis']}`")
        lines.append(f"- Phase 2 split axis: `{row['phase2_split_axis']}`")
        lines.append(f"- Validation split axis: `{row['validation_split_axis']}`")
        lines.append(f"- Promotion mode: `{row['promotion_mode']}`")
        lines.append(f"- Execution risk tier: `{row['execution_risk_tier']}`")
        lines.append(f"- Entry friction sensitivity: `{row['entry_friction_sensitivity']}`")
        lines.append(f"- Exit model dependency: `{row['exit_model_dependency']}`")
        lines.append(f"- Research bias: `{row['research_bias']}`")
        lines.append(f"- Preferred machine now: `{row['preferred_machine_now']}`")
        lines.append(f"- Preferred machine target: `{row['preferred_machine_target']}`")
        lines.append(f"- Families: {', '.join(f'`{family}`' for family in row['families'])}")
        lines.append(f"- Notes: {row['notes']}")
        lines.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = build_parser().parse_args()
    report_dir = Path(args.report_dir).resolve()
    report_dir.mkdir(parents=True, exist_ok=True)
    payload = build_payload()
    write_json(report_dir / "tournament_profile_registry.json", payload)
    write_csv(report_dir / "tournament_profile_registry.csv", payload["profiles"])
    write_markdown(report_dir / "tournament_profile_registry.md", payload)
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
