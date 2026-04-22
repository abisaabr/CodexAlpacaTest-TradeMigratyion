from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[2]
DEFAULT_REGISTRY_JSON = REPO_ROOT / "docs" / "strategy_family_registry" / "strategy_family_registry.json"
DEFAULT_REPORT_DIR = REPO_ROOT / "docs" / "strategy_family_registry"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build a concise strategy-family steward handoff from the formal family registry."
    )
    parser.add_argument(
        "--registry-json",
        default=str(DEFAULT_REGISTRY_JSON),
        help="Path to strategy_family_registry.json.",
    )
    parser.add_argument(
        "--report-dir",
        default=str(DEFAULT_REPORT_DIR),
        help="Directory where the handoff artifacts will be written.",
    )
    parser.add_argument(
        "--top-n",
        type=int,
        default=5,
        help="How many families per section to include.",
    )
    return parser


def top_rows(rows: list[dict[str, Any]], *, priority: str, top_n: int) -> list[dict[str, Any]]:
    matches = [row for row in rows if str(row.get("priority", "")) == priority]
    matches.sort(
        key=lambda row: (
            -int(row.get("ready_ticker_gap_count", 0)),
            -int(row.get("base_strategy_count", 0)),
            str(row.get("family", "")),
        )
    )
    return matches[:top_n]


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    lines: list[str] = []
    lines.append("# Strategy Family Handoff")
    lines.append("")
    lines.append("## Snapshot")
    lines.append("")
    lines.append(f"- Generated at: `{payload['generated_at']}`")
    lines.append(f"- Ready tickers: `{payload['ready_ticker_count']}`")
    lines.append(f"- Live strategies: `{payload['live_strategy_count']}` across `{payload['live_underlying_count']}` underlyings")
    lines.append("")
    lines.append("## Immediate Focus")
    lines.append("")
    lines.append("- Keep the live manifest stable unless a validated add/replace packet says otherwise.")
    lines.append("- Use `priority_discovery` families for new broad waves.")
    lines.append("- Use `priority_validation` families for exhaustive follow-up.")
    lines.append("- Use `promotion_follow_up` families for manual live-book review, not automatic promotion.")
    lines.append("")

    for section_name, section_rows in (
        ("Priority Discovery", payload["priority_discovery"]),
        ("Priority Validation", payload["priority_validation"]),
        ("Promotion Follow-Up", payload["promotion_follow_up"]),
        ("Live Benchmarks", payload["live_benchmarks"]),
    ):
        lines.append(f"## {section_name}")
        lines.append("")
        if not section_rows:
            lines.append("- none")
            lines.append("")
            continue
        for row in section_rows:
            lines.append(
                f"- `{row['family']}`: lane `{row['steward_action']}`, ready gap `{row['ready_ticker_gap_count']}`, live strategies `{row['live_manifest_strategy_count']}`"
            )
        lines.append("")

    lines.append("## Suggested Next Tournaments")
    lines.append("")
    for tournament in payload["suggested_tournaments"]:
        lines.append(f"- `{tournament['name']}`: {tournament['why']}")
        lines.append(f"  Families: {', '.join(f'`{family}`' for family in tournament['families'])}")
    lines.append("")

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = build_parser().parse_args()
    registry_path = Path(args.registry_json).resolve()
    report_dir = Path(args.report_dir).resolve()
    report_dir.mkdir(parents=True, exist_ok=True)

    payload = json.loads(registry_path.read_text(encoding="utf-8"))
    rows = list(payload.get("families", []))
    top_n = max(1, int(args.top_n))

    priority_discovery = top_rows(rows, priority="priority_discovery", top_n=top_n)
    priority_validation = top_rows(rows, priority="priority_validation", top_n=top_n)
    promotion_follow_up = top_rows(rows, priority="promotion_follow_up", top_n=top_n)
    live_benchmarks = top_rows(rows, priority="live_benchmark", top_n=top_n)

    suggested_tournaments = [
        {
            "name": "Opening 30-Minute Premium Defense",
            "families": [row["family"] for row in priority_discovery if row["family"] in {"Credit call spread", "Iron condor", "Debit put spread"}],
            "why": "Targets our biggest non-live premium-defense gaps in the opening session where execution control matters most.",
        },
        {
            "name": "Opening 30-Minute Butterfly Lab",
            "families": [row["family"] for row in priority_discovery if "butterfly" in row["family"].lower()],
            "why": "Builds evidence in the most under-tested multi-leg structures without mixing them into directional lanes.",
        },
        {
            "name": "Convexity And Long-Vol Follow-Up",
            "families": [row["family"] for row in (priority_validation + promotion_follow_up) if row["family"] in {"Put backspread", "Long straddle", "Long strangle"}],
            "why": "Pushes the best bear/choppy convexity families toward live-book review using exhaustive validation.",
        },
    ]
    suggested_tournaments = [item for item in suggested_tournaments if item["families"]]

    handoff = {
        "generated_at": payload.get("generated_at"),
        "registry_json": str(registry_path),
        "ready_ticker_count": int(payload.get("ready_ticker_count", 0)),
        "live_strategy_count": int(payload.get("live_manifest", {}).get("strategy_count", 0)),
        "live_underlying_count": int(payload.get("live_manifest", {}).get("underlying_count", 0)),
        "priority_discovery": priority_discovery,
        "priority_validation": priority_validation,
        "promotion_follow_up": promotion_follow_up,
        "live_benchmarks": live_benchmarks,
        "suggested_tournaments": suggested_tournaments,
    }

    json_path = report_dir / "strategy_family_handoff.json"
    md_path = report_dir / "strategy_family_handoff.md"
    json_path.write_text(json.dumps(handoff, indent=2), encoding="utf-8")
    write_markdown(md_path, handoff)
    print(json.dumps({"json_path": str(json_path), "markdown_path": str(md_path)}, indent=2))


if __name__ == "__main__":
    main()
