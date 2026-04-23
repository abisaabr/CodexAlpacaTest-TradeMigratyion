from __future__ import annotations

import argparse
import collections
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[2]
DEFAULT_OUTPUT_ROOT = REPO_ROOT / "output"
DEFAULT_READY_BASE_DIR = Path(
    r"C:\Users\rabisaab\OneDrive - First American Corporation\qqq_options_30d_cleanroom\output\backtester_ready"
)
DEFAULT_RUNNER_PATH = ROOT / "run_core_strategy_expansion_overnight.py"
DEFAULT_COVERAGE_PLANNER_PATH = ROOT / "build_ticker_family_coverage.py"
DEFAULT_OPERATING_MODEL_JSON = DEFAULT_OUTPUT_ROOT / "agent_operating_model_20260421_main" / "agent_operating_model.json"
DEFAULT_COVERAGE_PLAN_JSON = DEFAULT_OUTPUT_ROOT / "ticker_family_coverage_20260421_post_materialize_wave3" / "next_wave_plan.json"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build an execution-ready launch pack for the first discovery wave from the operating model and coverage plan."
    )
    parser.add_argument("--operating-model-json", default=str(DEFAULT_OPERATING_MODEL_JSON))
    parser.add_argument("--coverage-plan-json", default=str(DEFAULT_COVERAGE_PLAN_JSON))
    parser.add_argument("--ready-base-dir", default=str(DEFAULT_READY_BASE_DIR))
    parser.add_argument("--runner-path", default=str(DEFAULT_RUNNER_PATH))
    parser.add_argument("--coverage-planner-path", default=str(DEFAULT_COVERAGE_PLANNER_PATH))
    parser.add_argument("--python-exe", default="python")
    parser.add_argument("--max-tickers-per-lane", type=int, default=8)
    parser.add_argument(
        "--allocation-mode",
        choices=("benchmark", "breadth", "hybrid"),
        default="hybrid",
        help="benchmark keeps each lane's top-ranked symbols, breadth minimizes cross-lane overlap, hybrid keeps a small shared benchmark core then fills breadth-first.",
    )
    parser.add_argument(
        "--shared-benchmark-slots",
        type=int,
        default=2,
        help="When allocation-mode=hybrid, number of shared benchmark symbols to keep in every lane before breadth-first filling.",
    )
    parser.add_argument(
        "--refresh-coverage",
        action="store_true",
        help="Regenerate the coverage-ranked plan before building the launch pack.",
    )
    parser.add_argument("--coverage-top-ready-per-lane", type=int, default=24)
    parser.add_argument("--coverage-top-staged-per-lane", type=int, default=8)
    parser.add_argument("--coverage-top-registry-per-lane", type=int, default=8)
    parser.add_argument(
        "--research-root",
        default=str(DEFAULT_OUTPUT_ROOT / f"phase1_agent_wave_{datetime.now().strftime('%Y%m%d_%H%M%S')}"),
    )
    parser.add_argument(
        "--output-dir",
        default=str(DEFAULT_OUTPUT_ROOT / f"agent_wave_launch_pack_{datetime.now().strftime('%Y%m%d_%H%M%S')}"),
    )
    parser.add_argument(
        "--require-explicit-sources",
        action="store_true",
        help="Require explicit --operating-model-json and --coverage-plan-json instead of falling back to the latest matching artifacts.",
    )
    return parser


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def normalize_family_token(value: str) -> str:
    return "".join(character.lower() if character.isalnum() else "_" for character in value).strip("_")


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def refresh_coverage_plan(
    *,
    planner_path: Path,
    report_dir: Path,
    ready_base_dir: Path,
    top_ready_per_lane: int,
    top_staged_per_lane: int,
    top_registry_per_lane: int,
) -> Path:
    report_dir.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            sys.executable,
            str(planner_path),
            "--ready-base-dir",
            str(ready_base_dir),
            "--report-dir",
            str(report_dir),
            "--top-ready-per-lane",
            str(top_ready_per_lane),
            "--top-staged-per-lane",
            str(top_staged_per_lane),
            "--top-registry-per-lane",
            str(top_registry_per_lane),
        ],
        cwd=ROOT,
        check=True,
    )
    plan_path = report_dir / "next_wave_plan.json"
    if not plan_path.exists():
        raise FileNotFoundError(f"coverage refresh did not produce {plan_path}")
    return plan_path


def resolve_latest_json(path: Path, pattern: str) -> Path:
    if path and path.is_file():
        return path
    candidates = sorted(DEFAULT_OUTPUT_ROOT.rglob(pattern), key=lambda candidate: candidate.stat().st_mtime, reverse=True)
    if not candidates:
        raise FileNotFoundError(f"Could not find {pattern} under {DEFAULT_OUTPUT_ROOT}")
    return candidates[0]


def resolve_source_json(
    *,
    raw_value: str,
    pattern: str,
    require_explicit: bool,
) -> Path:
    if raw_value:
        candidate = Path(raw_value).resolve()
        if candidate.is_file():
            return candidate
        if require_explicit:
            raise FileNotFoundError(f"explicit source path does not exist: {candidate}")
        return resolve_latest_json(Path(), pattern)
    if require_explicit:
        raise FileNotFoundError(f"explicit source path required for {pattern}")
    return resolve_latest_json(Path(), pattern)


def map_discovery_agents(operating_model: dict[str, Any]) -> dict[str, dict[str, Any]]:
    mapping: dict[str, dict[str, Any]] = {}
    for agent in operating_model.get("agents", []):
        if agent.get("lane_type") != "discovery":
            continue
        family_filters = tuple(sorted(agent.get("family_include_filters", [])))
        mapping["|".join(family_filters)] = agent
    return mapping


def lane_filters_from_template(template: dict[str, Any]) -> list[str]:
    return [normalize_family_token(str(family)) for family in template.get("families", []) if str(family).strip()]


def build_command_text(python_exe: str, command_args: list[str]) -> str:
    parts = [python_exe]
    for arg in command_args:
        if any(character.isspace() for character in arg):
            parts.append(f'"{arg}"')
        else:
            parts.append(arg)
    return " ".join(parts)


def score_shared_benchmark_tickers(
    templates: list[dict[str, Any]],
    *,
    max_rank_window: int,
) -> list[str]:
    frequency: collections.Counter[str] = collections.Counter()
    rank_totals: dict[str, int] = {}
    for template in templates:
        for rank, row in enumerate(list(template.get("ready_discovery", []))[:max_rank_window], start=1):
            ticker = str(row.get("ticker", "")).upper()
            if not ticker:
                continue
            frequency[ticker] += 1
            rank_totals[ticker] = rank_totals.get(ticker, 0) + rank
    scored = sorted(
        frequency,
        key=lambda ticker: (-frequency[ticker], rank_totals.get(ticker, 999999), ticker),
    )
    return scored


def allocate_lane_tickers(
    templates: list[dict[str, Any]],
    *,
    max_tickers_per_lane: int,
    allocation_mode: str,
    shared_benchmark_slots: int,
) -> tuple[dict[str, list[str]], dict[str, Any]]:
    lane_candidates: dict[str, list[str]] = {}
    for template in templates:
        lane_candidates[str(template["lane_id"])] = [
            str(row.get("ticker", "")).upper()
            for row in template.get("ready_discovery", [])
            if str(row.get("ticker", "")).strip()
        ]

    if allocation_mode == "benchmark":
        assigned = {
            lane_id: candidates[:max_tickers_per_lane]
            for lane_id, candidates in lane_candidates.items()
        }
        return assigned, {
            "allocation_mode": allocation_mode,
            "shared_benchmark_tickers": [],
        }

    shared_benchmark: list[str] = []
    if allocation_mode == "hybrid" and shared_benchmark_slots > 0:
        ranked = score_shared_benchmark_tickers(templates, max_rank_window=max_tickers_per_lane)
        shared_benchmark = ranked[:shared_benchmark_slots]

    assigned: dict[str, list[str]] = {lane_id: [] for lane_id in lane_candidates}
    globally_assigned: set[str] = set()

    if shared_benchmark:
        for lane_id, candidates in lane_candidates.items():
            for ticker in shared_benchmark:
                if ticker in candidates and len(assigned[lane_id]) < max_tickers_per_lane:
                    assigned[lane_id].append(ticker)

    while True:
        progress = False
        for lane_id, candidates in lane_candidates.items():
            if len(assigned[lane_id]) >= max_tickers_per_lane:
                continue
            for ticker in candidates:
                if ticker in assigned[lane_id]:
                    continue
                if ticker in globally_assigned:
                    continue
                assigned[lane_id].append(ticker)
                globally_assigned.add(ticker)
                progress = True
                break
        if not progress:
            break

    for lane_id, candidates in lane_candidates.items():
        if len(assigned[lane_id]) >= max_tickers_per_lane:
            continue
        for ticker in candidates:
            if ticker in assigned[lane_id]:
                continue
            assigned[lane_id].append(ticker)
            if len(assigned[lane_id]) >= max_tickers_per_lane:
                break

    return assigned, {
        "allocation_mode": allocation_mode,
        "shared_benchmark_tickers": shared_benchmark,
    }


def build_overlap_summary(lanes: list[dict[str, Any]]) -> dict[str, Any]:
    counter: collections.Counter[str] = collections.Counter()
    lane_map: dict[str, list[str]] = {}
    for lane in lanes:
        tickers = [str(ticker).upper() for ticker in lane["tickers"]]
        lane_map[str(lane["lane_id"])] = tickers
        counter.update(tickers)
    overlapping = {
        ticker: count
        for ticker, count in sorted(counter.items(), key=lambda item: (-item[1], item[0]))
        if count > 1
    }
    return {
        "unique_ticker_count": len(counter),
        "total_lane_slots": sum(counter.values()),
        "overlap_ticker_count": len(overlapping),
        "overlap_share_pct": round((len(overlapping) / len(counter)) * 100.0, 2) if counter else 0.0,
        "overlapping_tickers": overlapping,
        "lane_tickers": lane_map,
    }


def build_pack(
    *,
    operating_model: dict[str, Any],
    coverage_plan: dict[str, Any],
    ready_base_dir: Path,
    runner_path: Path,
    python_exe: str,
    max_tickers_per_lane: int,
    allocation_mode: str,
    shared_benchmark_slots: int,
    research_root: Path,
) -> dict[str, Any]:
    agent_map = map_discovery_agents(operating_model)
    lanes: list[dict[str, Any]] = []
    logs_root = research_root / "logs"
    templates = list(coverage_plan.get("lane_templates", []))
    if not templates:
        raise ValueError("coverage plan has no lane_templates; cannot build a discovery pack")
    lane_assignments, allocation_summary = allocate_lane_tickers(
        templates,
        max_tickers_per_lane=max_tickers_per_lane,
        allocation_mode=allocation_mode,
        shared_benchmark_slots=shared_benchmark_slots,
    )
    unmapped_lanes: list[str] = []
    empty_lanes: list[str] = []
    for template in templates:
        family_filters = sorted(lane_filters_from_template(template))
        agent = agent_map.get("|".join(family_filters))
        if agent is None:
            unmapped_lanes.append(str(template.get("lane_id", "")))
            continue
        tickers = [ticker.lower() for ticker in lane_assignments.get(str(template["lane_id"]), [])]
        if not tickers:
            empty_lanes.append(str(template.get("lane_id", "")))
            continue
        lane_id = str(template["lane_id"])
        lane_research_dir = research_root / lane_id
        lane_logs_dir = logs_root / lane_id
        command_args = [
            str(runner_path),
            "--tickers",
            ",".join(tickers),
            "--ready-base-dir",
            str(ready_base_dir),
            "--research-dir",
            str(lane_research_dir),
            "--strategy-set",
            str(agent["strategy_set"]),
            "--selection-profile",
            str(agent["selection_profile"]),
            "--family-include",
            ",".join(family_filters),
        ]
        lanes.append(
            {
                "lane_id": lane_id,
                "agent": agent["agent"],
                "description": str(template.get("description", "")),
                "strategy_set": str(agent["strategy_set"]),
                "selection_profile": str(agent["selection_profile"]),
                "family_include_filters": family_filters,
                "tickers": [ticker.upper() for ticker in tickers],
                "research_dir": str(lane_research_dir),
                "logs_dir": str(lane_logs_dir),
                "stdout_path": str(lane_logs_dir / "phase1_stdout.log"),
                "stderr_path": str(lane_logs_dir / "phase1_stderr.log"),
                "command_args": command_args,
                "command_text": build_command_text(python_exe, command_args),
                "expected_outputs": [
                    "run_manifest.json",
                    "*_summary.json",
                    "family_rankings.csv",
                    "premium_bucket_rankings.csv",
                ],
                "success_gate": str(agent["success_gate"]),
            }
        )

    if unmapped_lanes or empty_lanes:
        problems: list[str] = []
        if unmapped_lanes:
            problems.append(f"unmapped lanes: {', '.join(unmapped_lanes)}")
        if empty_lanes:
            problems.append(f"empty lanes: {', '.join(empty_lanes)}")
        raise ValueError("cannot build a complete discovery pack; " + "; ".join(problems))

    return {
        "generated_at": datetime.now().isoformat(),
        "phase": "phase1_discovery",
        "python_exe": python_exe,
        "runner_path": str(runner_path),
        "ready_base_dir": str(ready_base_dir),
        "research_root": str(research_root),
        "source_operating_model": operating_model.get("source_plan_path", ""),
        "source_coverage_plan_path": str(coverage_plan.get("_source_plan_path", "")),
        "source_coverage_generated_at": coverage_plan.get("generated_at", ""),
        "governance": {
            "writes_live_state": False,
            "promotion_mode": "none",
            "single_writer_roles": operating_model.get("governance", {}).get("single_writer_roles", []),
            "required_lane_artifacts": operating_model.get("artifacts", {}).get("required_per_lane", []),
        },
        "build_summary": {
            "expected_lane_count": len(templates),
            "built_lane_count": len(lanes),
            "allocation_mode": allocation_summary.get("allocation_mode", ""),
        },
        "allocation": allocation_summary,
        "overlap_summary": build_overlap_summary(lanes),
        "lanes": lanes,
    }


def write_launch_commands(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "$ErrorActionPreference = 'Stop'",
        f"$packPath = '{path.parent / 'agent_wave_launch_pack.json'}'",
        "",
    ]
    for lane in payload["lanes"]:
        lines.append(f"# {lane['agent']} :: {lane['lane_id']}")
        lines.append(lane["command_text"])
        lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def write_readme(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "# Agent Wave Launch Pack",
        "",
        f"- Phase: `{payload['phase']}`",
        f"- Ready base dir: `{payload['ready_base_dir']}`",
        f"- Research root: `{payload['research_root']}`",
        f"- Promotion mode: `{payload['governance']['promotion_mode']}`",
        f"- Allocation mode: `{payload['allocation']['allocation_mode']}`",
        "",
        "## Lanes",
        "",
    ]
    shared = payload["allocation"].get("shared_benchmark_tickers", [])
    if shared:
        lines.extend(
            [
                "## Shared Benchmark Core",
                "",
                f"- {', '.join(shared)}",
                "",
            ]
        )
    overlap = payload["overlap_summary"]
    lines.extend(
        [
            "## Overlap Summary",
            "",
            f"- Unique ticker count: `{overlap['unique_ticker_count']}`",
            f"- Total lane slots: `{overlap['total_lane_slots']}`",
            f"- Overlap ticker count: `{overlap['overlap_ticker_count']}`",
            f"- Overlap share: `{overlap['overlap_share_pct']}`%",
            "",
            "## Lanes",
            "",
        ]
    )
    for lane in payload["lanes"]:
        lines.append(f"- `{lane['lane_id']}` / `{lane['agent']}`")
        lines.append(f"  - tickers: {', '.join(lane['tickers'])}")
        lines.append(f"  - family include: `{','.join(lane['family_include_filters'])}`")
        lines.append(f"  - research dir: `{lane['research_dir']}`")
        lines.append(f"  - logs dir: `{lane['logs_dir']}`")
        lines.append(f"  - success gate: {lane['success_gate']}")
    lines.extend(
        [
            "",
            "## Execute",
            "",
            "Use `launch_agent_wave.ps1` with this pack when you are ready to unpause backtesting.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = build_parser().parse_args()
    operating_model_path = resolve_source_json(
        raw_value=str(args.operating_model_json),
        pattern="agent_operating_model.json",
        require_explicit=bool(args.require_explicit_sources),
    )
    coverage_plan_path = resolve_source_json(
        raw_value=str(args.coverage_plan_json),
        pattern="next_wave_plan.json",
        require_explicit=bool(args.require_explicit_sources),
    )
    if args.refresh_coverage:
        coverage_plan_path = refresh_coverage_plan(
            planner_path=Path(args.coverage_planner_path).resolve(),
            report_dir=Path(args.output_dir).resolve() / "coverage_refresh",
            ready_base_dir=Path(args.ready_base_dir).resolve(),
            top_ready_per_lane=int(args.coverage_top_ready_per_lane),
            top_staged_per_lane=int(args.coverage_top_staged_per_lane),
            top_registry_per_lane=int(args.coverage_top_registry_per_lane),
        )
    operating_model = load_json(operating_model_path)
    coverage_plan = load_json(coverage_plan_path)
    coverage_plan["_source_plan_path"] = str(coverage_plan_path)

    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    research_root = Path(args.research_root).resolve()

    payload = build_pack(
        operating_model=operating_model,
        coverage_plan=coverage_plan,
        ready_base_dir=Path(args.ready_base_dir).resolve(),
        runner_path=Path(args.runner_path).resolve(),
        python_exe=args.python_exe,
        max_tickers_per_lane=int(args.max_tickers_per_lane),
        allocation_mode=args.allocation_mode,
        shared_benchmark_slots=int(args.shared_benchmark_slots),
        research_root=research_root,
    )
    write_json(output_dir / "agent_wave_launch_pack.json", payload)
    write_launch_commands(output_dir / "agent_wave_launch_commands.ps1", payload)
    write_readme(output_dir / "README.md", payload)
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
