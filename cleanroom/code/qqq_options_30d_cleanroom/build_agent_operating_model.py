from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
DEFAULT_OUTPUT_ROOT = ROOT / "output"
DEFAULT_PLAN_JSON = ROOT / "output" / "agent_sharding_plan_20260421_159" / "agent_sharding_plan.json"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build an institutional-style agent operating model from the current sharding plan."
    )
    parser.add_argument("--agent-plan-json", default=str(DEFAULT_PLAN_JSON))
    parser.add_argument(
        "--output-dir",
        default=str(DEFAULT_OUTPUT_ROOT / f"agent_operating_model_{datetime.now().strftime('%Y%m%d_%H%M%S')}"),
    )
    return parser


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def resolve_agent_plan_json(path: Path, output_root: Path) -> Path:
    if path.exists():
        return path
    candidates = sorted(
        output_root.rglob("agent_sharding_plan.json"),
        key=lambda candidate: candidate.stat().st_mtime,
        reverse=True,
    )
    if not candidates:
        raise FileNotFoundError(f"Could not find agent_sharding_plan.json under {output_root}")
    return candidates[0]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def family_arg(agent: dict[str, Any]) -> str:
    return ",".join(agent.get("family_include_filters", []))


def build_agent_rows(plan: dict[str, Any]) -> list[dict[str, Any]]:
    output_dir = str(plan["data_universe"]["primary_output_dir"])
    discovery_agents = plan["agent_layout"]["discovery_agents"]
    deep_dive_agents = plan["agent_layout"]["deep_dive_agents"]
    validation_agents = plan["agent_layout"]["validation_agents"]

    rows: list[dict[str, Any]] = [
        {
            "agent": "Inventory Steward",
            "lane_type": "control_plane",
            "parallelism": 1,
            "writes_live_state": False,
            "scripts": [
                "build_strategy_repo.py",
                "build_ticker_family_coverage.py",
                "build_agent_sharding_plan.py",
                "build_agent_operating_model.py",
            ],
            "inputs": [
                "backtester_registry.csv",
                "backtester_ready manifests",
                "strategy_repo.json snapshots",
            ],
            "outputs": [
                "strategy_repo.json",
                "ticker_family_coverage.md",
                "agent_sharding_plan.json",
                "agent_operating_model.json",
            ],
            "success_gate": "Coverage gaps, ready-universe counts, and family priorities are refreshed before any new wave launches.",
            "handoff_to": ["Strategy Family Steward", "Data Prep Steward", *[row["agent"] for row in discovery_agents]],
            "notes": "Owns universe accounting and decides which families/symbols are still under-tested.",
        },
        {
            "agent": "Strategy Family Steward",
            "lane_type": "control_plane",
            "parallelism": 1,
            "writes_live_state": False,
            "scripts": [
                "build_strategy_repo.py",
                "build_strategy_family_registry.py",
                "build_ticker_family_coverage.py",
            ],
            "inputs": [
                "strategy_repo.json snapshots",
                "current live manifest",
                "ticker_family_coverage.md",
            ],
            "outputs": [
                "strategy_family_registry.json",
                "strategy_family_registry.md",
                "strategy_family_registry.csv",
                "family priority list",
            ],
            "success_gate": "The formal family registry is refreshed before major family-expansion waves or live-book review.",
            "handoff_to": ["Strategy Architect", "Inventory Steward", "Reporting Steward"],
            "notes": "Single owner of the GitHub-backed family taxonomy, live-overlay snapshot, and per-family research priority labels.",
        },
        {
            "agent": "Data Prep Steward",
            "lane_type": "control_plane",
            "parallelism": 1,
            "writes_live_state": False,
            "scripts": [
                "materialize_backtester_ready.py",
                "launch_down_choppy_program.ps1",
            ],
            "inputs": [
                "staged bundle zips",
                "registry-only symbols",
                "next_wave_prep_commands.ps1",
            ],
            "outputs": [
                "expanded backtester_ready universe",
                "materialization_status.json",
            ],
            "success_gate": "Priority staged/registry symbols are materialized before discovery lanes consume them.",
            "handoff_to": ["Inventory Steward", *[row["agent"] for row in discovery_agents]],
            "notes": "Single owner of prep/bootstrap so discovery runners do not mix data prep with research.",
        },
        {
            "agent": "Strategy Architect",
            "lane_type": "control_plane",
            "parallelism": 1,
            "writes_live_state": False,
            "scripts": [
                "backtest_qqq_greeks_portfolio.py",
                "run_multiticker_cleanroom_portfolio.py",
                "build_strategy_repo.py",
            ],
            "inputs": [
                "strategy_repo.json",
                "strategy_family_registry.json",
                "ticker_family_coverage.md",
                "loss/postmortem findings",
            ],
            "outputs": [
                "new or expanded strategy families",
                "parameter-surface changes",
            ],
            "success_gate": "Any new family must be wired into the catalog, family filters, and reporting before runners use it.",
            "handoff_to": ["Inventory Steward", "Balanced Expansion"],
            "notes": "Single editor of strategy-family definitions to avoid conflicting local forks.",
        },
    ]

    for agent in discovery_agents:
        rows.append(
            {
                "agent": agent["agent"],
                "lane_type": "discovery",
                "parallelism": int(agent.get("parallel_workers", 1)),
                "writes_live_state": False,
                "strategy_set": agent["strategy_set"],
                "selection_profile": "down_choppy_focus",
                "family_include_filters": list(agent.get("family_include_filters", [])),
                "scripts": [
                    "launch_down_choppy_family_wave.ps1",
                    "run_multiticker_cleanroom_portfolio.py",
                ],
                "inputs": [
                    "backtester_ready tickers",
                    "coverage-ranked cohort lists",
                    "family include filters",
                ],
                "outputs": [
                    "per-lane research_dir",
                    "per-ticker summaries",
                    "run_manifest.json",
                    "run_registry.jsonl entries",
                ],
                "success_gate": "No promotions. Survivors must show friction-aware strength and acceptable cheap-premium exposure.",
                "handoff_to": ["Reporting Steward"],
                "notes": f"Owns only the family lane `{family_arg(agent)}` and should not overlap with sibling discovery lanes.",
            }
        )

    for agent in deep_dive_agents:
        rows.append(
            {
                "agent": agent["agent"],
                "lane_type": "deep_dive",
                "parallelism": int(agent.get("parallel_workers", 1)),
                "writes_live_state": False,
                "strategy_set": agent["strategy_set"],
                "selection_profile": "down_choppy_focus" if agent["strategy_set"] == "down_choppy_exhaustive" else "balanced",
                "scripts": [
                    "build_family_wave_shortlist.py",
                    (
                        "launch_down_choppy_program.ps1"
                        if agent["strategy_set"] == "down_choppy_exhaustive"
                        else (
                            "launch_balanced_family_expansion_program.ps1"
                            if agent["strategy_set"] == "family_expansion"
                            else "run_core_strategy_expansion_overnight.py"
                        )
                    ),
                    "run_multiticker_cleanroom_portfolio.py",
                ],
                "inputs": [
                    "Phase 1 shortlist",
                    "friction-aware lane summaries",
                ],
                "outputs": [
                    "deeper walkforward summaries",
                    "family rankings",
                    "premium-bucket rankings",
                    "run manifests",
                ],
                "success_gate": agent.get("use_for", "Deep-dive survivors only."),
                "handoff_to": ["Shared-Account Validator", "Reporting Steward"],
                "notes": "Heavy lanes should stay small and resume-safe; no GitHub promotion from this phase.",
            }
        )

    for agent in validation_agents:
        rows.append(
            {
                "agent": agent["agent"],
                "lane_type": "validation",
                "parallelism": int(agent.get("parallel_workers", 1)),
                "writes_live_state": False,
                "strategy_set": agent["strategy_set"],
                "selection_profile": "portfolio_first",
                "scripts": [
                    "run_multiticker_cleanroom_portfolio.py",
                    "export_promoted_strategies.py",
                ],
                "inputs": [
                    "deep-dive winners",
                    "current live manifest",
                    "shared-account baselines",
                ],
                "outputs": [
                    "promotion candidate set",
                    "promoted_strategies.yaml",
                    "shared-account comparisons",
                ],
                "success_gate": "Only strategies that improve portfolio context or clearly replace weaker live sleeves may pass.",
                "handoff_to": ["Reporting Steward", "Promotion Steward"],
                "notes": "Single validation lane by design so final comparisons stay consistent.",
            }
        )

    rows.append(
        {
            "agent": "Reporting Steward",
            "lane_type": "control_plane",
            "parallelism": 1,
            "writes_live_state": False,
            "scripts": [
                "build_family_wave_shortlist.py",
                "summarize_tournament_conveyor.py",
                "build_agent_operating_model.py",
            ],
            "inputs": [
                "lane summaries",
                "family rankings",
                "friction profiles",
                "run manifests",
            ],
            "outputs": [
                "family_wave_shortlist.md",
                "phase2_plan.json",
                "tournament_conveyor_summary.json",
                "promotion review packet",
            ],
            "success_gate": "Reports must separate discovery, exhaustive, validation, and promotion-ready winners.",
            "handoff_to": ["Shared-Account Validator", "Promotion Steward"],
            "notes": "This lane turns raw results into decision artifacts and keeps auditability readable.",
        }
    )
    rows.append(
        {
            "agent": "Promotion Steward",
            "lane_type": "single_writer",
            "parallelism": 1,
            "writes_live_state": True,
            "scripts": [
                "export_promoted_strategies.py",
                "wait_and_sync_live_manifest.ps1",
                "sync_live_strategy_manifest.py",
            ],
            "inputs": [
                "approved promoted_strategies.yaml",
                "shared-account validation results",
                "current GitHub live manifest",
            ],
            "outputs": [
                "merged live manifest",
                "GitHub commit/push",
                "promotion audit trail",
            ],
            "success_gate": "Exactly one writer. Never shrink the live universe accidentally. Only push when the manifest truly improves.",
            "handoff_to": [],
            "notes": "No other agent may write the live manifest, merge promotions, or push live-book changes.",
        }
    )
    return rows


def build_operating_model(plan: dict[str, Any], *, plan_path: Path) -> dict[str, Any]:
    machine = plan["machine_profile"]
    concurrency = machine["concurrency"]
    return {
        "generated_at": datetime.now().isoformat(),
        "source_plan_path": str(plan_path),
        "machine_profile": machine,
        "governance": {
            "principles": [
                "Parallelize discovery and prep, serialize validation and promotion.",
                "Never allow concurrent live-manifest writers.",
                "Every large lane must emit run_manifest.json and append to run_registry.jsonl.",
                "Refresh the formal strategy-family registry before major family-expansion waves or live-book review.",
                "Promotion requires friction-aware results plus portfolio-context validation.",
                "Checkpoint reuse is allowed only when the run signature still matches.",
            ],
            "single_writer_roles": ["Promotion Steward"],
            "serialized_roles": ["Shared-Account Validator", "Promotion Steward"],
            "max_discovery_lanes": int(concurrency["lean_parallel_backtests"]),
            "max_heavy_lanes": int(concurrency["heavy_parallel_backtests"]),
            "max_validation_lanes": int(concurrency["validation_parallel_backtests"]),
        },
        "artifacts": {
            "required_per_lane": [
                "run_manifest.json",
                "run_registry.jsonl entry",
                "*_summary.json",
                "family_rankings.csv",
                "premium_bucket_rankings.csv",
            ],
            "promotion_inputs": [
                "promoted_strategies.yaml",
                "shared-account comparison",
                "current live manifest snapshot",
            ],
        },
        "agents": build_agent_rows(plan),
        "phase_flow": [
            {
                "phase": "Phase 0 - Inventory Refresh",
                "owner": "Inventory Steward",
                "feeds": ["Strategy Family Steward", "Data Prep Steward", "Strategy Architect", "Discovery lanes"],
            },
            {
                "phase": "Phase 0.25 - Family Registry",
                "owner": "Strategy Family Steward",
                "feeds": ["Strategy Architect", "Discovery lanes", "Reporting Steward"],
            },
            {
                "phase": "Phase 0.5 - Data Prep",
                "owner": "Data Prep Steward",
                "feeds": ["Inventory Steward", "Discovery lanes"],
            },
            {
                "phase": "Phase 1 - Discovery",
                "owner": "Discovery lanes",
                "feeds": ["Reporting Steward"],
            },
            {
                "phase": "Phase 2 - Exhaustive Follow-Up",
                "owner": "Down/Choppy Exhaustive", 
                "feeds": ["Reporting Steward", "Shared-Account Validator"],
            },
            {
                "phase": "Phase 3 - Balanced Expansion",
                "owner": "Balanced Expansion",
                "feeds": ["Reporting Steward", "Shared-Account Validator"],
            },
            {
                "phase": "Phase 4 - Shared-Account Validation",
                "owner": "Shared-Account Validator",
                "feeds": ["Promotion Steward"],
            },
            {
                "phase": "Phase 5 - Promotion",
                "owner": "Promotion Steward",
                "feeds": [],
            },
        ],
    }


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    machine = payload["machine_profile"]
    governance = payload["governance"]
    lines: list[str] = []
    lines.append("# Agent Operating Model")
    lines.append("")
    lines.append("## Machine Budget")
    lines.append("")
    lines.append(f"- Logical CPUs: {machine['logical_cpus']}")
    lines.append(f"- Total RAM: {machine['memory']['total_gb']:.2f} GB")
    lines.append(f"- Free RAM at plan time: {machine['memory']['free_gb']:.2f} GB")
    lines.append(f"- Discovery lanes: {governance['max_discovery_lanes']}")
    lines.append(f"- Heavy lanes: {governance['max_heavy_lanes']}")
    lines.append(f"- Validation lanes: {governance['max_validation_lanes']}")
    lines.append("")
    lines.append("## Governance")
    lines.append("")
    for item in governance["principles"]:
        lines.append(f"- {item}")
    lines.append("")
    lines.append("## Agent Roles")
    lines.append("")
    for agent in payload["agents"]:
        lines.append(f"### {agent['agent']}")
        lines.append("")
        lines.append(f"- Lane type: `{agent['lane_type']}`")
        lines.append(f"- Parallelism: `{agent['parallelism']}`")
        lines.append(f"- Writes live state: `{str(agent['writes_live_state']).lower()}`")
        if agent.get("strategy_set"):
            lines.append(f"- Strategy set: `{agent['strategy_set']}`")
        if agent.get("selection_profile"):
            lines.append(f"- Selection profile: `{agent['selection_profile']}`")
        if agent.get("family_include_filters"):
            lines.append(f"- Family include filters: `{','.join(agent['family_include_filters'])}`")
        lines.append(f"- Scripts: `{', '.join(agent['scripts'])}`")
        lines.append(f"- Inputs: {', '.join(agent['inputs'])}")
        lines.append(f"- Outputs: {', '.join(agent['outputs'])}")
        lines.append(f"- Success gate: {agent['success_gate']}")
        if agent["handoff_to"]:
            lines.append(f"- Hands off to: {', '.join(agent['handoff_to'])}")
        lines.append(f"- Notes: {agent['notes']}")
        lines.append("")
    lines.append("## Phase Flow")
    lines.append("")
    for phase in payload["phase_flow"]:
        lines.append(f"- `{phase['phase']}`: {phase['owner']}")
        if phase["feeds"]:
            lines.append(f"  - feeds: {', '.join(phase['feeds'])}")
    lines.append("")
    lines.append("## Required Artifacts")
    lines.append("")
    lines.append("- Per lane:")
    for item in payload["artifacts"]["required_per_lane"]:
        lines.append(f"  - `{item}`")
    lines.append("- Promotion inputs:")
    for item in payload["artifacts"]["promotion_inputs"]:
        lines.append(f"  - `{item}`")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = build_parser().parse_args()
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    plan_path = resolve_agent_plan_json(Path(args.agent_plan_json).resolve(), DEFAULT_OUTPUT_ROOT)
    plan = load_json(plan_path)
    payload = build_operating_model(plan, plan_path=plan_path)
    write_json(output_dir / "agent_operating_model.json", payload)
    write_markdown(output_dir / "agent_operating_model.md", payload)
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
