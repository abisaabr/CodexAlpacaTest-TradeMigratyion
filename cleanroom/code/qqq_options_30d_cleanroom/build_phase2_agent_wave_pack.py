from __future__ import annotations

import argparse
import collections
import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
DEFAULT_OUTPUT_ROOT = ROOT / "output"
DEFAULT_READY_BASE_DIR = Path(
    r"C:\Users\rabisaab\OneDrive - First American Corporation\qqq_options_30d_cleanroom\output\backtester_ready"
)
DEFAULT_RUNNER_PATH = ROOT / "run_core_strategy_expansion_overnight.py"
DEFAULT_OPERATING_MODEL_JSON = ROOT / "output" / "agent_operating_model_20260421_main" / "agent_operating_model.json"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build an execution-ready launch pack for Phase 2 exhaustive follow-up lanes."
    )
    parser.add_argument("--phase2-plan-json", default="")
    parser.add_argument("--shortlist-json", default="")
    parser.add_argument("--operating-model-json", default=str(DEFAULT_OPERATING_MODEL_JSON))
    parser.add_argument("--ready-base-dir", default=str(DEFAULT_READY_BASE_DIR))
    parser.add_argument("--runner-path", default=str(DEFAULT_RUNNER_PATH))
    parser.add_argument("--python-exe", default="python")
    parser.add_argument(
        "--research-root",
        default=str(DEFAULT_OUTPUT_ROOT / f"phase2_agent_wave_{datetime.now().strftime('%Y%m%d_%H%M%S')}"),
    )
    parser.add_argument(
        "--output-dir",
        default=str(DEFAULT_OUTPUT_ROOT / f"phase2_agent_wave_pack_{datetime.now().strftime('%Y%m%d_%H%M%S')}"),
    )
    return parser


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def resolve_latest_json(path: Path, pattern: str) -> Path:
    if path and path.exists():
        return path
    candidates = sorted(DEFAULT_OUTPUT_ROOT.rglob(pattern), key=lambda candidate: candidate.stat().st_mtime, reverse=True)
    if not candidates:
        raise FileNotFoundError(f"Could not find {pattern} under {DEFAULT_OUTPUT_ROOT}")
    return candidates[0]


def normalize_family_filter(value: str) -> list[str]:
    return sorted(
        {
            "".join(character.lower() if character.isalnum() else "_" for character in token).strip("_")
            for token in value.split(",")
            if token.strip()
        }
    )


def build_command_text(python_exe: str, command_args: list[str]) -> str:
    parts = [python_exe]
    for arg in command_args:
        if any(character.isspace() for character in arg):
            parts.append(f'"{arg}"')
        else:
            parts.append(arg)
    return " ".join(parts)


def load_phase2_plan(path: Path) -> list[dict[str, Any]]:
    payload = load_json(path)
    if isinstance(payload, list):
        return [dict(item) for item in payload]
    if isinstance(payload, dict) and payload.get("lane_id") and payload.get("strategy_set"):
        return [dict(payload)]
    if isinstance(payload, dict) and isinstance(payload.get("phase2_plan"), list):
        return [dict(item) for item in payload["phase2_plan"]]
    raise ValueError(f"{path} does not contain a valid phase2 plan payload")


def resolve_shortlist_payload(phase2_plan_path: Path, explicit_shortlist_path: str) -> tuple[Path | None, dict[str, Any] | None]:
    candidate_paths: list[Path] = []
    if explicit_shortlist_path:
        candidate_paths.append(Path(explicit_shortlist_path).resolve())
    sibling = phase2_plan_path.parent / "family_wave_shortlist.json"
    if sibling.exists():
        candidate_paths.append(sibling)
    for candidate in candidate_paths:
        if candidate.exists():
            payload = load_json(candidate)
            if isinstance(payload, dict) and isinstance(payload.get("phase2_plan"), list):
                return candidate, payload
    return None, None


def select_phase2_agent(operating_model: dict[str, Any], lane: dict[str, Any]) -> dict[str, Any]:
    strategy_set = str(lane.get("strategy_set", ""))
    selection_profile = str(lane.get("selection_profile", ""))
    deep_dive_agents = [
        agent
        for agent in operating_model.get("agents", [])
        if agent.get("lane_type") == "deep_dive"
    ]
    exact_matches = [
        agent
        for agent in deep_dive_agents
        if str(agent.get("strategy_set", "")) == strategy_set
        and str(agent.get("selection_profile", "")) == selection_profile
    ]
    if exact_matches:
        return exact_matches[0]
    if deep_dive_agents:
        return deep_dive_agents[0]
    raise ValueError("No deep_dive agent found in the operating model")


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
    phase2_plan: list[dict[str, Any]],
    phase2_plan_path: Path,
    operating_model: dict[str, Any],
    ready_base_dir: Path,
    runner_path: Path,
    python_exe: str,
    research_root: Path,
    shortlist_payload: dict[str, Any] | None,
    shortlist_path: Path | None,
) -> dict[str, Any]:
    lanes: list[dict[str, Any]] = []
    logs_root = research_root / "logs"
    for lane in phase2_plan:
        tickers = [str(ticker).lower() for ticker in lane.get("tickers", []) if str(ticker).strip()]
        if not tickers:
            continue
        agent = select_phase2_agent(operating_model, lane)
        lane_id = str(lane["lane_id"])
        lane_research_dir = research_root / lane_id
        lane_logs_dir = logs_root / lane_id
        family_filters = normalize_family_filter(str(lane.get("family_include", "")))
        command_args = [
            str(runner_path),
            "--tickers",
            ",".join(tickers),
            "--ready-base-dir",
            str(ready_base_dir),
            "--research-dir",
            str(lane_research_dir),
            "--strategy-set",
            str(lane["strategy_set"]),
            "--selection-profile",
            str(lane["selection_profile"]),
        ]
        if family_filters:
            command_args.extend(["--family-include", ",".join(family_filters)])
        lanes.append(
            {
                "lane_id": lane_id,
                "agent": str(agent["agent"]),
                "description": str(lane.get("description", "")),
                "strategy_set": str(lane["strategy_set"]),
                "selection_profile": str(lane["selection_profile"]),
                "family_include_filters": family_filters,
                "source_lanes": [str(value) for value in lane.get("source_lanes", [])],
                "tickers": [ticker.upper() for ticker in tickers],
                "research_dir": str(lane_research_dir),
                "logs_dir": str(lane_logs_dir),
                "stdout_path": str(lane_logs_dir / "phase2_stdout.log"),
                "stderr_path": str(lane_logs_dir / "phase2_stderr.log"),
                "command_args": command_args,
                "command_text": build_command_text(python_exe, command_args),
                "expected_outputs": [
                    "run_manifest.json",
                    "*_summary.json",
                    "master_summary.json",
                    "family_rankings.csv",
                    "premium_bucket_rankings.csv",
                ],
                "success_gate": str(agent["success_gate"]),
                "source_row_count": int(lane.get("source_row_count", 0)),
                "selected_row_count": int(lane.get("selected_row_count", 0)),
                "rows": list(lane.get("rows", [])),
            }
        )

    return {
        "generated_at": datetime.now().isoformat(),
        "phase": "phase2_exhaustive",
        "python_exe": python_exe,
        "runner_path": str(runner_path),
        "ready_base_dir": str(ready_base_dir),
        "research_root": str(research_root),
        "source_operating_model": operating_model.get("source_plan_path", ""),
        "source_shortlist_path": str(shortlist_path) if shortlist_path else "",
        "source_shortlist_generated_at": shortlist_payload.get("generated_at", "") if shortlist_payload else "",
        "source_wave_plan_path": shortlist_payload.get("wave_plan_path", "") if shortlist_payload else "",
        "source_phase2_plan_path": str(phase2_plan_path),
        "source_phase2_filters": shortlist_payload.get("filters", {}) if shortlist_payload else {},
        "governance": {
            "writes_live_state": False,
            "promotion_mode": "none",
            "single_writer_roles": operating_model.get("governance", {}).get("single_writer_roles", []),
            "required_lane_artifacts": operating_model.get("artifacts", {}).get("required_per_lane", []),
        },
        "overlap_summary": build_overlap_summary(lanes),
        "lanes": lanes,
    }


def write_launch_commands(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "$ErrorActionPreference = 'Stop'",
        f"$packPath = '{path.parent / 'phase2_agent_wave_pack.json'}'",
        "",
    ]
    for lane in payload["lanes"]:
        lines.append(f"# {lane['agent']} :: {lane['lane_id']}")
        lines.append(lane["command_text"])
        lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def write_readme(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "# Phase 2 Agent Wave Launch Pack",
        "",
        f"- Phase: `{payload['phase']}`",
        f"- Ready base dir: `{payload['ready_base_dir']}`",
        f"- Research root: `{payload['research_root']}`",
        f"- Promotion mode: `{payload['governance']['promotion_mode']}`",
        f"- Shortlist path: `{payload.get('source_shortlist_path', '')}`",
        f"- Wave plan path: `{payload.get('source_wave_plan_path', '')}`",
        "",
        "## Overlap Summary",
        "",
        f"- Unique ticker count: `{payload['overlap_summary']['unique_ticker_count']}`",
        f"- Total lane slots: `{payload['overlap_summary']['total_lane_slots']}`",
        f"- Overlap ticker count: `{payload['overlap_summary']['overlap_ticker_count']}`",
        f"- Overlap share: `{payload['overlap_summary']['overlap_share_pct']}`%",
        "",
        "## Lanes",
        "",
    ]
    for lane in payload["lanes"]:
        lines.append(f"- `{lane['lane_id']}` / `{lane['agent']}`")
        lines.append(f"  - source lanes: {', '.join(lane['source_lanes'])}")
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
            "Use `launch_agent_wave.ps1` with this pack when you are ready to run the exhaustive follow-up lanes.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = build_parser().parse_args()
    phase2_plan_path = resolve_latest_json(Path(args.phase2_plan_json).resolve() if args.phase2_plan_json else Path(), "phase2_plan.json")
    operating_model_path = resolve_latest_json(Path(args.operating_model_json).resolve(), "agent_operating_model.json")
    phase2_plan = load_phase2_plan(phase2_plan_path)
    operating_model = load_json(operating_model_path)
    shortlist_path, shortlist_payload = resolve_shortlist_payload(phase2_plan_path, args.shortlist_json)

    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    research_root = Path(args.research_root).resolve()

    payload = build_pack(
        phase2_plan=phase2_plan,
        phase2_plan_path=phase2_plan_path,
        operating_model=operating_model,
        ready_base_dir=Path(args.ready_base_dir).resolve(),
        runner_path=Path(args.runner_path).resolve(),
        python_exe=args.python_exe,
        research_root=research_root,
        shortlist_payload=shortlist_payload,
        shortlist_path=shortlist_path,
    )
    write_json(output_dir / "phase2_agent_wave_pack.json", payload)
    write_launch_commands(output_dir / "phase2_agent_wave_commands.ps1", payload)
    write_readme(output_dir / "README.md", payload)
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
