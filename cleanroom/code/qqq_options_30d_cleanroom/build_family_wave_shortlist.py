from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
DEFAULT_OUTPUT_ROOT = ROOT / "output"
DEFAULT_RUNNER = ROOT / "run_core_strategy_expansion_overnight.py"


PHASE2_GROUPS = [
    {
        "lane_id": "05_defensive_income",
        "description": "Phase 2 defensive/income follow-up combining directional and premium bear families.",
        "source_lanes": ["01_bear_directional", "02_bear_premium"],
    },
    {
        "lane_id": "06_convexity_butterfly",
        "description": "Phase 2 convexity/butterfly follow-up combining long-vol and butterfly families.",
        "source_lanes": ["03_bear_convexity", "04_butterfly_lab"],
    },
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build a Phase 2 exhaustive shortlist from a completed down/choppy family-wave discovery run."
    )
    parser.add_argument(
        "--wave-plan",
        default="",
        help="Path to family_wave_plan.json. If omitted, the latest one under output/ is used.",
    )
    parser.add_argument(
        "--output-dir",
        default=str(DEFAULT_OUTPUT_ROOT / f"family_wave_shortlist_{datetime.now().strftime('%Y%m%d_%H%M%S')}"),
    )
    parser.add_argument("--runner-path", default=str(DEFAULT_RUNNER))
    parser.add_argument("--python-exe", default="python")
    parser.add_argument("--phase2-strategy-set", default="down_choppy_exhaustive")
    parser.add_argument("--phase2-selection-profile", default="down_choppy_focus")
    parser.add_argument("--top-per-lane", type=int, default=8)
    parser.add_argument("--max-per-phase2-lane", type=int, default=12)
    parser.add_argument("--min-return-pct", type=float, default=0.0)
    parser.add_argument("--max-drawdown-pct", type=float, default=25.0)
    parser.add_argument("--max-avg-friction-pct", type=float, default=95.0)
    parser.add_argument("--max-cheap-share-pct", type=float, default=85.0)
    parser.add_argument("--min-trade-count", type=int, default=20)
    return parser


def find_latest_wave_plan(output_root: Path) -> Path:
    candidates = sorted(output_root.rglob("family_wave_plan.json"), key=lambda path: path.stat().st_mtime, reverse=True)
    if not candidates:
        raise FileNotFoundError(f"no family_wave_plan.json found under {output_root}")
    return candidates[0]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def normalize_family_filter(value: str) -> str:
    return ",".join(
        sorted(
            {
                "".join(character.lower() if character.isalnum() else "_" for character in token).strip("_")
                for token in value.split(",")
                if token.strip()
            }
        )
    )


def scalar_float(mapping: dict[str, Any], key: str) -> float:
    value = mapping.get(key, 0.0)
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def scalar_int(mapping: dict[str, Any], key: str) -> int:
    value = mapping.get(key, 0)
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def load_lane_ticker_rows(lane: dict[str, Any]) -> list[dict[str, Any]]:
    research_dir = Path(lane["research_dir"])
    master_path = research_dir / "master_summary.json"
    master_payload = load_json(master_path) if master_path.exists() else {}
    failed_map = {
        str(item.get("ticker", "")).upper(): item
        for item in master_payload.get("failed_tickers", [])
        if isinstance(item, dict)
    }
    expected_ticker_list = [str(ticker).upper() for ticker in lane.get("tickers", [])]
    expected_ticker_set = set(expected_ticker_list)

    rows: list[dict[str, Any]] = []
    seen_ok: set[str] = set()

    for summary_path in sorted(research_dir.glob("*_summary.json")):
        if summary_path.name in {"master_summary.json", "prep_summary.json", "overnight_run_summary.json"}:
            continue
        payload = load_json(summary_path)
        if not isinstance(payload, dict):
            continue
        ticker = str(payload.get("ticker", summary_path.stem.replace("_summary", ""))).upper()
        if expected_ticker_set and ticker not in expected_ticker_set:
            continue
        frozen = payload.get("frozen_initial", {})
        reoptimized = payload.get("reoptimized", {})
        promoted = payload.get("promoted", {})
        frozen_friction = frozen.get("friction_profile", {})
        reoptimized_friction = reoptimized.get("friction_profile", {})
        seen_ok.add(ticker)
        rows.append(
            {
                "lane_id": lane["lane_id"],
                "lane_description": lane.get("description", ""),
                "lane_research_dir": str(research_dir),
                "strategy_set": lane.get("strategy_set", ""),
                "selection_profile": lane.get("selection_profile", ""),
                "family_include": lane.get("family_include", ""),
                "family_include_normalized": normalize_family_filter(str(lane.get("family_include", ""))),
                "ticker": ticker,
                "status": "ok",
                "error": "",
                "trade_date_start": payload.get("trade_date_start", ""),
                "trade_date_end": payload.get("trade_date_end", ""),
                "day_count": scalar_int(payload, "day_count"),
                "candidate_trade_count": scalar_int(payload, "candidate_trade_count"),
                "frozen_final_equity": scalar_float(frozen, "final_equity"),
                "frozen_total_return_pct": scalar_float(frozen, "total_return_pct"),
                "frozen_trade_count": scalar_int(frozen, "trade_count"),
                "frozen_win_rate_pct": scalar_float(frozen, "win_rate_pct"),
                "frozen_max_drawdown_pct": scalar_float(frozen, "max_drawdown_pct"),
                "frozen_calmar_like": scalar_float(frozen, "calmar_like"),
                "reoptimized_final_equity": scalar_float(reoptimized, "final_equity"),
                "reoptimized_total_return_pct": scalar_float(reoptimized, "total_return_pct"),
                "reoptimized_trade_count": scalar_int(reoptimized, "trade_count"),
                "reoptimized_win_rate_pct": scalar_float(reoptimized, "win_rate_pct"),
                "reoptimized_max_drawdown_pct": scalar_float(reoptimized, "max_drawdown_pct"),
                "reoptimized_calmar_like": scalar_float(reoptimized, "calmar_like"),
                "selected_bull_count": len(promoted.get("selected_bull", [])),
                "selected_bear_count": len(promoted.get("selected_bear", [])),
                "selected_choppy_count": len(promoted.get("selected_choppy", [])),
                "selected_total_count": len(promoted.get("selected_bull", []))
                + len(promoted.get("selected_bear", []))
                + len(promoted.get("selected_choppy", [])),
                "top_frozen_family_bucket": str((frozen.get("family_bucket_contributions", [{}]) or [{}])[0].get("family_bucket", "")),
                "top_frozen_family_bucket_pnl": scalar_float((frozen.get("family_bucket_contributions", [{}]) or [{}])[0], "portfolio_net_pnl"),
                "top_frozen_premium_bucket": str((frozen.get("premium_bucket_contributions", [{}]) or [{}])[0].get("premium_bucket", "")),
                "top_frozen_premium_bucket_pnl": scalar_float((frozen.get("premium_bucket_contributions", [{}]) or [{}])[0], "portfolio_net_pnl"),
                "frozen_median_entry_premium": scalar_float(frozen_friction, "median_entry_premium"),
                "frozen_avg_friction_pct_of_entry_premium": scalar_float(frozen_friction, "avg_friction_pct_of_entry_premium"),
                "frozen_trade_share_sub_0_30_pct": scalar_float(frozen_friction, "trade_share_sub_0_30_pct"),
                "reoptimized_median_entry_premium": scalar_float(reoptimized_friction, "median_entry_premium"),
                "reoptimized_avg_friction_pct_of_entry_premium": scalar_float(reoptimized_friction, "avg_friction_pct_of_entry_premium"),
                "reoptimized_trade_share_sub_0_30_pct": scalar_float(reoptimized_friction, "trade_share_sub_0_30_pct"),
                "lane_shared_return_pct": scalar_float(master_payload.get("shared_account", {}), "total_return_pct"),
                "lane_shared_max_drawdown_pct": scalar_float(master_payload.get("shared_account", {}), "max_drawdown_pct"),
                "lane_shared_trade_count": scalar_int(master_payload.get("shared_account", {}), "trade_count"),
            }
        )

    for ticker in expected_ticker_list:
        if ticker in seen_ok:
            continue
        failed = failed_map.get(ticker, {})
        rows.append(
            {
                "lane_id": lane["lane_id"],
                "lane_description": lane.get("description", ""),
                "lane_research_dir": str(research_dir),
                "strategy_set": lane.get("strategy_set", ""),
                "selection_profile": lane.get("selection_profile", ""),
                "family_include": lane.get("family_include", ""),
                "family_include_normalized": normalize_family_filter(str(lane.get("family_include", ""))),
                "ticker": ticker,
                "status": "error",
                "error": str(failed.get("message", failed.get("error", "missing summary artifact"))),
                "trade_date_start": "",
                "trade_date_end": "",
                "day_count": 0,
                "candidate_trade_count": 0,
                "frozen_final_equity": 0.0,
                "frozen_total_return_pct": 0.0,
                "frozen_trade_count": 0,
                "frozen_win_rate_pct": 0.0,
                "frozen_max_drawdown_pct": 0.0,
                "frozen_calmar_like": 0.0,
                "reoptimized_final_equity": 0.0,
                "reoptimized_total_return_pct": 0.0,
                "reoptimized_trade_count": 0,
                "reoptimized_win_rate_pct": 0.0,
                "reoptimized_max_drawdown_pct": 0.0,
                "reoptimized_calmar_like": 0.0,
                "selected_bull_count": 0,
                "selected_bear_count": 0,
                "selected_choppy_count": 0,
                "selected_total_count": 0,
                "top_frozen_family_bucket": "",
                "top_frozen_family_bucket_pnl": 0.0,
                "top_frozen_premium_bucket": "",
                "top_frozen_premium_bucket_pnl": 0.0,
                "frozen_median_entry_premium": 0.0,
                "frozen_avg_friction_pct_of_entry_premium": 0.0,
                "frozen_trade_share_sub_0_30_pct": 0.0,
                "reoptimized_median_entry_premium": 0.0,
                "reoptimized_avg_friction_pct_of_entry_premium": 0.0,
                "reoptimized_trade_share_sub_0_30_pct": 0.0,
                "lane_shared_return_pct": scalar_float(master_payload.get("shared_account", {}), "total_return_pct"),
                "lane_shared_max_drawdown_pct": scalar_float(master_payload.get("shared_account", {}), "max_drawdown_pct"),
                "lane_shared_trade_count": scalar_int(master_payload.get("shared_account", {}), "trade_count"),
            }
        )

    return rows


def evaluate_row(row: dict[str, Any], args: argparse.Namespace) -> dict[str, Any]:
    reasons: list[str] = []
    if row["status"] != "ok":
        reasons.append("status_error")
    if float(row["frozen_total_return_pct"]) < float(args.min_return_pct):
        reasons.append("return_below_threshold")
    if abs(float(row["frozen_max_drawdown_pct"])) > float(args.max_drawdown_pct):
        reasons.append("drawdown_above_threshold")
    if int(row["frozen_trade_count"]) < int(args.min_trade_count):
        reasons.append("trade_count_below_threshold")
    if float(row["frozen_avg_friction_pct_of_entry_premium"]) > float(args.max_avg_friction_pct):
        reasons.append("friction_above_threshold")
    if float(row["frozen_trade_share_sub_0_30_pct"]) > float(args.max_cheap_share_pct):
        reasons.append("cheap_premium_share_above_threshold")
    if int(row["selected_bear_count"]) + int(row["selected_choppy_count"]) <= 0:
        reasons.append("missing_down_choppy_exposure")

    max_drawdown = abs(float(row["frozen_max_drawdown_pct"]))
    score = (
        float(row["frozen_total_return_pct"])
        + max(0.0, float(row["frozen_calmar_like"])) * 4.0
        - max_drawdown * 0.60
        - float(row["frozen_avg_friction_pct_of_entry_premium"]) * 0.12
        - float(row["frozen_trade_share_sub_0_30_pct"]) * 0.08
        + int(row["selected_bear_count"]) * 2.5
        + int(row["selected_choppy_count"]) * 1.5
        + min(float(row["frozen_median_entry_premium"]), 1.0) * 8.0
        + min(int(row["frozen_trade_count"]), 120) * 0.02
    )
    enriched = dict(row)
    enriched["survivor_score"] = round(score, 4)
    enriched["passes_filters"] = not reasons
    enriched["rejection_reasons"] = reasons
    return enriched


def build_phase2_plan(
    *,
    lanes: list[dict[str, Any]],
    shortlisted_rows: list[dict[str, Any]],
    wave_root: Path,
    args: argparse.Namespace,
) -> list[dict[str, Any]]:
    lane_map = {lane["lane_id"]: lane for lane in lanes}
    rows_by_lane: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in shortlisted_rows:
        rows_by_lane[str(row["lane_id"])].append(row)

    phase2_plan: list[dict[str, Any]] = []
    for group in PHASE2_GROUPS:
        family_filters: set[str] = set()
        ticker_best: dict[str, dict[str, Any]] = {}
        ticker_sources: dict[str, set[str]] = defaultdict(set)
        for source_lane in group["source_lanes"]:
            lane = lane_map.get(source_lane)
            if lane is None:
                continue
            for token in str(lane.get("family_include", "")).split(","):
                token = token.strip()
                if token:
                    family_filters.add(token)
            for row in rows_by_lane.get(source_lane, []):
                ticker = str(row["ticker"]).lower()
                existing = ticker_best.get(ticker)
                if existing is None or float(row["survivor_score"]) > float(existing["survivor_score"]):
                    ticker_best[ticker] = row
                ticker_sources[ticker].add(source_lane)

        ranked_rows = sorted(ticker_best.values(), key=lambda row: (-float(row["survivor_score"]), row["ticker"]))
        selected_rows = ranked_rows[: max(0, int(args.max_per_phase2_lane))]
        tickers = [str(row["ticker"]).lower() for row in selected_rows]
        research_dir = wave_root / group["lane_id"]
        command = ""
        if tickers:
            arg_list = [
                str(Path(args.runner_path).resolve()),
                "--tickers",
                ",".join(tickers),
                "--ready-base-dir",
                str(Path(lanes[0]["research_dir"]).parent.parent.resolve() / "backtester_ready") if False else "",
            ]
        # Build the command manually from lane metadata to preserve the ready-base-dir exactly.
        ready_base_dir = ""
        if lanes:
            first_lane = lanes[0]
            lane_command = str(first_lane.get("command", ""))
            marker = "--ready-base-dir"
            if marker in lane_command:
                after = lane_command.split(marker, 1)[1].strip()
                if after.startswith('"'):
                    ready_base_dir = after.split('"', 2)[1]
                else:
                    ready_base_dir = after.split(" ", 1)[0]
        command_parts = [
            args.python_exe,
            str(Path(args.runner_path).resolve()),
            "--tickers",
            ",".join(tickers),
        ]
        if ready_base_dir:
            command_parts.extend(["--ready-base-dir", ready_base_dir])
        command_parts.extend(
            [
                "--research-dir",
                str(research_dir),
                "--strategy-set",
                args.phase2_strategy_set,
                "--selection-profile",
                args.phase2_selection_profile,
                "--family-include",
                ",".join(sorted(family_filters)),
            ]
        )
        command = " ".join(f'"{part}"' if " " in part else part for part in command_parts) if tickers else ""
        phase2_plan.append(
            {
                "lane_id": group["lane_id"],
                "description": group["description"],
                "source_lanes": list(group["source_lanes"]),
                "strategy_set": args.phase2_strategy_set,
                "selection_profile": args.phase2_selection_profile,
                "family_include": ",".join(sorted(family_filters)),
                "tickers": tickers,
                "research_dir": str(research_dir),
                "source_row_count": len(ranked_rows),
                "selected_row_count": len(selected_rows),
                "rows": [
                    {
                        "ticker": row["ticker"],
                        "survivor_score": row["survivor_score"],
                        "source_lanes": sorted(ticker_sources[str(row["ticker"]).lower()]),
                        "frozen_total_return_pct": row["frozen_total_return_pct"],
                        "frozen_max_drawdown_pct": row["frozen_max_drawdown_pct"],
                        "frozen_avg_friction_pct_of_entry_premium": row["frozen_avg_friction_pct_of_entry_premium"],
                        "frozen_trade_share_sub_0_30_pct": row["frozen_trade_share_sub_0_30_pct"],
                    }
                    for row in selected_rows
                ],
                "command": command,
            }
        )
    return phase2_plan


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
            normalized = {
                key: json.dumps(value) if isinstance(value, (list, dict)) else value
                for key, value in row.items()
            }
            writer.writerow(normalized)


def write_markdown(
    *,
    path: Path,
    wave_plan_path: Path,
    lanes: list[dict[str, Any]],
    evaluated_rows: list[dict[str, Any]],
    shortlisted_rows: list[dict[str, Any]],
    phase2_plan: list[dict[str, Any]],
    args: argparse.Namespace,
) -> None:
    lines = [
        "# Family Wave Shortlist",
        "",
        f"- Wave plan: `{wave_plan_path}`",
        f"- Top survivors per lane: `{args.top_per_lane}`",
        f"- Phase 2 max tickers per lane: `{args.max_per_phase2_lane}`",
        f"- Filters: return >= `{args.min_return_pct:.2f}%`, drawdown <= `{args.max_drawdown_pct:.2f}%`, friction <= `{args.max_avg_friction_pct:.2f}%`, cheap-premium share <= `{args.max_cheap_share_pct:.2f}%`, trade count >= `{args.min_trade_count}`",
        "",
        "## Lane Summary",
        "",
    ]

    for lane in lanes:
        lane_rows = [row for row in evaluated_rows if row["lane_id"] == lane["lane_id"]]
        passes = [row for row in lane_rows if row["passes_filters"]]
        lines.append(f"- `{lane['lane_id']}`: {len(passes)} survivors out of {len(lane_rows)} tickers")
    lines.append("")
    lines.append("## Top Survivors By Lane")
    lines.append("")
    for lane in lanes:
        lane_rows = [row for row in shortlisted_rows if row["lane_id"] == lane["lane_id"]]
        lines.append(f"### {lane['lane_id']}")
        lines.append("")
        if not lane_rows:
            lines.append("- none")
            lines.append("")
            continue
        for row in lane_rows:
            lines.append(
                f"- `{row['ticker']}` score `{row['survivor_score']:.2f}` | return `{row['frozen_total_return_pct']:.2f}%` | max DD `{row['frozen_max_drawdown_pct']:.2f}%` | friction `{row['frozen_avg_friction_pct_of_entry_premium']:.2f}%` | sub-0.30 share `{row['frozen_trade_share_sub_0_30_pct']:.2f}%`"
            )
        lines.append("")

    lines.append("## Rejections")
    lines.append("")
    rejected_rows = [row for row in evaluated_rows if not row["passes_filters"]]
    if rejected_rows:
        for row in sorted(rejected_rows, key=lambda item: (item["lane_id"], item["ticker"])):
            lines.append(f"- `{row['lane_id']}` / `{row['ticker']}`: {', '.join(row['rejection_reasons'])}")
    else:
        lines.append("- none")
    lines.append("")

    lines.append("## Phase 2 Exhaustive Lanes")
    lines.append("")
    for lane in phase2_plan:
        lines.append(f"### {lane['lane_id']}")
        lines.append("")
        lines.append(f"- description: {lane['description']}")
        lines.append(f"- family include: `{lane['family_include']}`")
        lines.append(f"- ticker count: `{len(lane['tickers'])}`")
        if lane["rows"]:
            for row in lane["rows"]:
                lines.append(
                    f"- `{row['ticker'].upper()}` from `{','.join(row['source_lanes'])}` | score `{row['survivor_score']:.2f}` | return `{row['frozen_total_return_pct']:.2f}%` | max DD `{row['frozen_max_drawdown_pct']:.2f}%`"
                )
        else:
            lines.append("- none")
        if lane["command"]:
            lines.append(f"- command: `{lane['command']}`")
        lines.append("")

    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    args = build_parser().parse_args()
    wave_plan_path = Path(args.wave_plan) if args.wave_plan else find_latest_wave_plan(DEFAULT_OUTPUT_ROOT)
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    lanes = load_json(wave_plan_path)
    evaluated_rows: list[dict[str, Any]] = []
    for lane in lanes:
        for row in load_lane_ticker_rows(lane):
            evaluated_rows.append(evaluate_row(row, args))

    shortlisted_rows: list[dict[str, Any]] = []
    for lane in lanes:
        lane_rows = [row for row in evaluated_rows if row["lane_id"] == lane["lane_id"] and row["passes_filters"]]
        lane_rows.sort(
            key=lambda row: (
                -float(row["survivor_score"]),
                -float(row["frozen_total_return_pct"]),
                abs(float(row["frozen_max_drawdown_pct"])),
                row["ticker"],
            )
        )
        shortlisted_rows.extend(lane_rows[: max(0, int(args.top_per_lane))])

    phase2_plan = build_phase2_plan(
        lanes=lanes,
        shortlisted_rows=shortlisted_rows,
        wave_root=output_dir,
        args=args,
    )

    payload = {
        "wave_plan_path": str(wave_plan_path.resolve()),
        "generated_at": datetime.now().isoformat(),
        "filters": {
            "top_per_lane": int(args.top_per_lane),
            "max_per_phase2_lane": int(args.max_per_phase2_lane),
            "min_return_pct": float(args.min_return_pct),
            "max_drawdown_pct": float(args.max_drawdown_pct),
            "max_avg_friction_pct": float(args.max_avg_friction_pct),
            "max_cheap_share_pct": float(args.max_cheap_share_pct),
            "min_trade_count": int(args.min_trade_count),
        },
        "lanes": lanes,
        "evaluated_rows": evaluated_rows,
        "shortlisted_rows": shortlisted_rows,
        "phase2_plan": phase2_plan,
    }

    shortlist_json = output_dir / "family_wave_shortlist.json"
    shortlist_csv = output_dir / "family_wave_shortlist.csv"
    shortlist_md = output_dir / "family_wave_shortlist.md"
    commands_path = output_dir / "phase2_commands.ps1"
    phase2_plan_path = output_dir / "phase2_plan.json"

    shortlist_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    write_csv(shortlist_csv, evaluated_rows)
    phase2_plan_path.write_text(json.dumps(phase2_plan, indent=2), encoding="utf-8")
    commands_path.write_text(
        "\n".join(lane["command"] for lane in phase2_plan if lane["command"]),
        encoding="utf-8",
    )
    write_markdown(
        path=shortlist_md,
        wave_plan_path=wave_plan_path,
        lanes=lanes,
        evaluated_rows=evaluated_rows,
        shortlisted_rows=shortlisted_rows,
        phase2_plan=phase2_plan,
        args=args,
    )

    print(json.dumps({"output_dir": str(output_dir), "wave_plan": str(wave_plan_path), "shortlisted_count": len(shortlisted_rows)}, indent=2))


if __name__ == "__main__":
    main()
