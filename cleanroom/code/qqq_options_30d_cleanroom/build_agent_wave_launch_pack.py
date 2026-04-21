from __future__ import annotations

import argparse
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
DEFAULT_COVERAGE_PLAN_JSON = ROOT / "output" / "ticker_family_coverage_20260421_post_materialize_wave3" / "next_wave_plan.json"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build an execution-ready launch pack for the first discovery wave from the operating model and coverage plan."
    )
    parser.add_argument("--operating-model-json", default=str(DEFAULT_OPERATING_MODEL_JSON))
    parser.add_argument("--coverage-plan-json", default=str(DEFAULT_COVERAGE_PLAN_JSON))
    parser.add_argument("--ready-base-dir", default=str(DEFAULT_READY_BASE_DIR))
    parser.add_argument("--runner-path", default=str(DEFAULT_RUNNER_PATH))
    parser.add_argument("--python-exe", default="python")
    parser.add_argument("--max-tickers-per-lane", type=int, default=8)
    parser.add_argument(
        "--research-root",
        default=str(DEFAULT_OUTPUT_ROOT / f"phase1_agent_wave_{datetime.now().strftime('%Y%m%d_%H%M%S')}"),
    )
    parser.add_argument(
        "--output-dir",
        default=str(DEFAULT_OUTPUT_ROOT / f"agent_wave_launch_pack_{datetime.now().strftime('%Y%m%d_%H%M%S')}"),
    )
    return parser


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def normalize_family_token(value: str) -> str:
    return "".join(character.lower() if character.isalnum() else "_" for character in value).strip("_")


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def resolve_latest_json(path: Path, pattern: str) -> Path:
    if path.exists():
        return path
    candidates = sorted(DEFAULT_OUTPUT_ROOT.rglob(pattern), key=lambda candidate: candidate.stat().st_mtime, reverse=True)
    if not candidates:
        raise FileNotFoundError(f"Could not find {pattern} under {DEFAULT_OUTPUT_ROOT}")
    return candidates[0]


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


def build_pack(
    *,
    operating_model: dict[str, Any],
    coverage_plan: dict[str, Any],
    ready_base_dir: Path,
    runner_path: Path,
    python_exe: str,
    max_tickers_per_lane: int,
    research_root: Path,
) -> dict[str, Any]:
    agent_map = map_discovery_agents(operating_model)
    lanes: list[dict[str, Any]] = []
    logs_root = research_root / "logs"
    for template in coverage_plan.get("lane_templates", []):
        family_filters = sorted(lane_filters_from_template(template))
        agent = agent_map.get("|".join(family_filters))
        if agent is None:
            continue
        ready_rows = list(template.get("ready_discovery", []))[:max_tickers_per_lane]
        tickers = [str(row["ticker"]).lower() for row in ready_rows if str(row.get("ticker", "")).strip()]
        if not tickers:
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

    return {
        "generated_at": datetime.now().isoformat(),
        "phase": "phase1_discovery",
        "python_exe": python_exe,
        "runner_path": str(runner_path),
        "ready_base_dir": str(ready_base_dir),
        "research_root": str(research_root),
        "source_operating_model": operating_model.get("source_plan_path", ""),
        "source_coverage_generated_at": coverage_plan.get("generated_at", ""),
        "governance": {
            "writes_live_state": False,
            "promotion_mode": "none",
            "single_writer_roles": operating_model.get("governance", {}).get("single_writer_roles", []),
            "required_lane_artifacts": operating_model.get("artifacts", {}).get("required_per_lane", []),
        },
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
        "",
        "## Lanes",
        "",
    ]
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
    operating_model_path = resolve_latest_json(Path(args.operating_model_json).resolve(), "agent_operating_model.json")
    coverage_plan_path = resolve_latest_json(Path(args.coverage_plan_json).resolve(), "next_wave_plan.json")
    operating_model = load_json(operating_model_path)
    coverage_plan = load_json(coverage_plan_path)

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
        research_root=research_root,
    )
    write_json(output_dir / "agent_wave_launch_pack.json", payload)
    write_launch_commands(output_dir / "agent_wave_launch_commands.ps1", payload)
    write_readme(output_dir / "README.md", payload)
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
