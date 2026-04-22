from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

import build_strategy_repo as repo_builder
from backtest_qqq_greeks_portfolio import build_delta_strategies
import run_multiticker_cleanroom_portfolio as mt


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[2]
WORKSPACE_ROOT = ROOT.parents[3]
DEFAULT_SIBLING_OUTPUT_ROOT = WORKSPACE_ROOT / "qqq_options_30d_cleanroom" / "output"
DEFAULT_ONEDRIVE_OUTPUT_ROOT = (
    Path(r"C:\Users\rabisaab\OneDrive - First American Corporation")
    / "qqq_options_30d_cleanroom"
    / "output"
)


def first_existing_path(*paths: Path) -> Path:
    for path in paths:
        if path.exists():
            return path
    return paths[0]


DEFAULT_OUTPUT_ROOT = first_existing_path(DEFAULT_SIBLING_OUTPUT_ROOT, DEFAULT_ONEDRIVE_OUTPUT_ROOT)
DEFAULT_READY_BASE_DIR = first_existing_path(
    DEFAULT_SIBLING_OUTPUT_ROOT / "backtester_ready",
    DEFAULT_ONEDRIVE_OUTPUT_ROOT / "backtester_ready",
)
DEFAULT_LIVE_MANIFEST_PATH = (
    WORKSPACE_ROOT / "codexalpaca_repo" / "config" / "strategy_manifests" / "multi_ticker_portfolio_live.yaml"
)
DEFAULT_REPORT_DIR = REPO_ROOT / "docs" / "strategy_family_registry"
STRATEGY_SETS = repo_builder.STRATEGY_SETS


STRUCTURE_BUCKETS = {
    "Single-leg long call": "single_leg",
    "Single-leg long put": "single_leg",
    "Debit call spread": "debit_spread",
    "Debit put spread": "debit_spread",
    "Credit call spread": "credit_spread",
    "Credit put spread": "credit_spread",
    "Iron condor": "neutral_premium",
    "Iron butterfly": "neutral_premium",
    "Call butterfly": "butterfly",
    "Put butterfly": "butterfly",
    "Broken-wing call butterfly": "broken_wing_butterfly",
    "Broken-wing put butterfly": "broken_wing_butterfly",
    "Call backspread": "backspread",
    "Put backspread": "backspread",
    "Long straddle": "long_vol",
    "Long strangle": "long_vol",
}


DIRECTIONAL_BIAS = {
    "Single-leg long call": "bull",
    "Single-leg long put": "bear",
    "Debit call spread": "bull",
    "Debit put spread": "bear",
    "Credit call spread": "bear",
    "Credit put spread": "bull",
    "Iron condor": "choppy",
    "Iron butterfly": "choppy",
    "Call butterfly": "bull_or_choppy",
    "Put butterfly": "bear_or_choppy",
    "Broken-wing call butterfly": "bull_or_choppy",
    "Broken-wing put butterfly": "bear_or_choppy",
    "Call backspread": "bull_convexity",
    "Put backspread": "bear_convexity",
    "Long straddle": "choppy_or_expansion",
    "Long strangle": "choppy_or_expansion",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build a formal strategy-family registry for GitHub-backed operator/reference use."
    )
    parser.add_argument(
        "--output-root",
        default=str(DEFAULT_OUTPUT_ROOT),
        help="Root output folder that contains cleanroom research runs.",
    )
    parser.add_argument(
        "--ready-base-dir",
        default=str(DEFAULT_READY_BASE_DIR),
        help="Backtester-ready bundle directory used to estimate ready symbol coverage.",
    )
    parser.add_argument(
        "--live-manifest-path",
        default=str(DEFAULT_LIVE_MANIFEST_PATH),
        help="Optional live manifest path used to overlay current production family coverage.",
    )
    parser.add_argument(
        "--report-dir",
        default=str(DEFAULT_REPORT_DIR),
        help="Optional explicit directory for generated registry artifacts.",
    )
    return parser


def slugify(value: str) -> str:
    return (
        value.lower()
        .replace("/", "_")
        .replace(" ", "_")
        .replace("-", "_")
        .replace("__", "_")
    )


def load_live_manifest(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {
            "manifest_path": str(path),
            "strategy_count": 0,
            "underlying_count": 0,
            "by_family": {},
            "tickers": [],
            "family_rows": {},
        }
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    strategies = list(payload.get("strategies", []))
    family_rows: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "strategy_count": 0,
            "ticker_count": 0,
            "tickers": set(),
            "regimes": Counter(),
            "timing_profiles": Counter(),
        }
    )
    tickers: set[str] = set()
    for strategy in strategies:
        if not isinstance(strategy, dict):
            continue
        family = str(strategy.get("family", "")).strip()
        ticker = str(strategy.get("underlying_symbol", "")).upper()
        if not family:
            continue
        tickers.add(ticker)
        row = family_rows[family]
        row["strategy_count"] += 1
        row["tickers"].add(ticker)
        row["regimes"][str(strategy.get("regime", ""))] += 1
        row["timing_profiles"][str(strategy.get("timing_profile", ""))] += 1
    normalized_rows: dict[str, Any] = {}
    for family, row in family_rows.items():
        normalized_rows[family] = {
            "strategy_count": int(row["strategy_count"]),
            "ticker_count": len(row["tickers"]),
            "tickers": sorted(ticker for ticker in row["tickers"] if ticker),
            "regimes": dict(sorted(row["regimes"].items())),
            "timing_profiles": dict(sorted(row["timing_profiles"].items())),
        }
    return {
        "manifest_path": str(path),
        "strategy_count": len(strategies),
        "underlying_count": len(tickers),
        "by_family": dict(
            sorted(
                ((family, row["strategy_count"]) for family, row in normalized_rows.items()),
                key=lambda item: (-item[1], item[0]),
            )
        ),
        "tickers": sorted(tickers),
        "family_rows": normalized_rows,
    }


def priority_for_family(*, live_strategy_count: int, selected_count: int, promoted_count: int, ready_gap: int) -> str:
    if live_strategy_count > 0 and selected_count > 0:
        return "live_benchmark"
    if live_strategy_count == 0 and selected_count == 0 and ready_gap > 0:
        return "priority_discovery"
    if live_strategy_count == 0 and selected_count > 0 and promoted_count == 0:
        return "priority_validation"
    if live_strategy_count == 0 and promoted_count > 0:
        return "promotion_follow_up"
    return "monitor"


def steward_action_for_priority(priority: str) -> str:
    return {
        "live_benchmark": "benchmark_against_current_live_book",
        "priority_discovery": "collect_and_rank_new_family_candidates",
        "priority_validation": "push_family_into_exhaustive_validation",
        "promotion_follow_up": "review_for_live_manifest_addition",
        "monitor": "maintain_registry_and_wait_for_new_evidence",
    }[priority]


def family_note(*, family: str, live_strategy_count: int, selected_count: int, promoted_count: int, ready_gap: int) -> str:
    if live_strategy_count > 0:
        return f"{family} is already live and should be benchmarked for replacement or diversification, not re-added blindly."
    if selected_count == 0:
        return f"{family} is still structurally under-tested across the ready universe and should stay in discovery rotation."
    if promoted_count == 0:
        return f"{family} has produced selections but no approved live sleeves yet, so it belongs in exhaustive validation."
    if ready_gap > 0:
        return f"{family} has some evidence already, but there is still room to widen symbol coverage before promotion."
    return f"{family} is cataloged and should be monitored as more out-of-sample evidence lands."


def build_family_rows(
    *,
    strategies_by_family: dict[str, list[Any]],
    strategy_sets_by_base_name: dict[str, set[str]],
    summary_records: list[dict[str, Any]],
    ready_tickers: list[str],
    live_manifest: dict[str, Any],
) -> list[dict[str, Any]]:
    selected_bases_by_family: defaultdict[str, set[str]] = defaultdict(set)
    promoted_bases_by_family: defaultdict[str, set[str]] = defaultdict(set)
    selected_tickers_by_family: defaultdict[str, set[str]] = defaultdict(set)
    promoted_tickers_by_family: defaultdict[str, set[str]] = defaultdict(set)

    strategy_name_to_family = {
        strategy.name: strategy.family
        for strategies in strategies_by_family.values()
        for strategy in strategies
    }

    for record in summary_records:
        ticker = str(record["ticker"]).upper()
        for base_name in record["selected_base_strategies"]:
            family = strategy_name_to_family.get(base_name)
            if not family:
                continue
            selected_bases_by_family[family].add(base_name)
            selected_tickers_by_family[family].add(ticker)
        for base_name in record["promoted_base_strategies"]:
            family = strategy_name_to_family.get(base_name)
            if not family:
                continue
            promoted_bases_by_family[family].add(base_name)
            promoted_tickers_by_family[family].add(ticker)

    rows: list[dict[str, Any]] = []
    ready_ticker_upper = [ticker.upper() for ticker in ready_tickers]
    for family, strategies in sorted(strategies_by_family.items()):
        base_names = sorted({strategy.name for strategy in strategies})
        leg_counts = sorted({len(strategy.legs) for strategy in strategies})
        live_row = dict(live_manifest.get("family_rows", {}).get(family, {}))
        selected_count = len(selected_bases_by_family.get(family, set()))
        promoted_count = len(promoted_bases_by_family.get(family, set()))
        selected_tickers = sorted(selected_tickers_by_family.get(family, set()))
        promoted_tickers = sorted(promoted_tickers_by_family.get(family, set()))
        live_strategy_count = int(live_row.get("strategy_count", 0))
        ready_gap = max(0, len(ready_ticker_upper) - len(selected_tickers))
        priority = priority_for_family(
            live_strategy_count=live_strategy_count,
            selected_count=selected_count,
            promoted_count=promoted_count,
            ready_gap=ready_gap,
        )
        rows.append(
            {
                "family": family,
                "slug": slugify(family),
                "structure_bucket": STRUCTURE_BUCKETS.get(family, "other"),
                "directional_bias": DIRECTIONAL_BIAS.get(family, "mixed"),
                "base_strategy_count": len(base_names),
                "base_strategies": base_names,
                "leg_count_range": [min(leg_counts), max(leg_counts)] if leg_counts else [0, 0],
                "strategy_sets": sorted(
                    {
                        strategy_set
                        for base_name in base_names
                        for strategy_set in strategy_sets_by_base_name.get(base_name, set())
                    }
                ),
                "signal_names": sorted({strategy.signal_name for strategy in strategies}),
                "dte_modes": sorted({strategy.dte_mode for strategy in strategies}),
                "selected_base_strategy_count": selected_count,
                "promoted_base_strategy_count": promoted_count,
                "selected_ticker_count": len(selected_tickers),
                "promoted_ticker_count": len(promoted_tickers),
                "selected_tickers": selected_tickers,
                "promoted_tickers": promoted_tickers,
                "ready_ticker_gap_count": ready_gap,
                "ready_ticker_gap_ratio": round(ready_gap / max(len(ready_ticker_upper), 1), 4),
                "live_manifest_strategy_count": live_strategy_count,
                "live_manifest_ticker_count": int(live_row.get("ticker_count", 0)),
                "live_manifest_tickers": list(live_row.get("tickers", [])),
                "live_manifest_regimes": dict(live_row.get("regimes", {})),
                "live_manifest_timing_profiles": dict(live_row.get("timing_profiles", {})),
                "priority": priority,
                "steward_action": steward_action_for_priority(priority),
                "note": family_note(
                    family=family,
                    live_strategy_count=live_strategy_count,
                    selected_count=selected_count,
                    promoted_count=promoted_count,
                    ready_gap=ready_gap,
                ),
            }
        )
    return rows


def attach_strategy_set_metadata(
    strategies_by_family: dict[str, list[Any]],
    strategy_sets_by_base_name: dict[str, set[str]],
) -> None:
    for strategy_set in STRATEGY_SETS:
        for strategy in build_delta_strategies(strategy_set=strategy_set):
            strategies_by_family.setdefault(strategy.family, []).append(strategy)
            strategy_sets_by_base_name.setdefault(strategy.name, set()).add(strategy_set)


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    lines: list[str] = []
    lines.append("# Strategy Family Registry")
    lines.append("")
    lines.append("## Snapshot")
    lines.append("")
    lines.append(f"- Generated at: `{payload['generated_at']}`")
    lines.append(f"- Ready tickers: {payload['ready_ticker_count']}")
    lines.append(f"- Cataloged families: {payload['family_count']}")
    lines.append(f"- Cataloged base strategies: {payload['base_strategy_count']}")
    lines.append(f"- Research ticker summaries found: {payload['research_summary_count']}")
    lines.append(f"- Unique researched tickers: {payload['researched_ticker_count']}")
    lines.append("")
    lines.append("## Live Manifest Overlay")
    lines.append("")
    live = payload["live_manifest"]
    lines.append(f"- Manifest path: `{live['manifest_path'] or 'not provided'}`")
    lines.append(f"- Live strategies: {live['strategy_count']}")
    lines.append(f"- Live underlyings: {live['underlying_count']}")
    if live["by_family"]:
        lines.append("- Live families:")
        for family, count in live["by_family"].items():
            lines.append(f"  - `{family}`: {count}")
    else:
        lines.append("- Live families: none loaded")
    lines.append("")
    lines.append("## Priority Families")
    lines.append("")
    for row in payload["priority_families"]:
        lines.append(
            f"- `{row['family']}`: `{row['priority']}`; live strategies `{row['live_manifest_strategy_count']}`; selected bases `{row['selected_base_strategy_count']}`; ready gap `{row['ready_ticker_gap_count']}`"
        )
    lines.append("")
    lines.append("## Registry")
    lines.append("")
    for row in payload["families"]:
        lines.append(f"### {row['family']}")
        lines.append("")
        lines.append(
            f"- Bucket: `{row['structure_bucket']}`; bias: `{row['directional_bias']}`; leg range: `{row['leg_count_range'][0]}-{row['leg_count_range'][1]}`"
        )
        lines.append(
            f"- Priority: `{row['priority']}`; steward action: `{row['steward_action']}`"
        )
        lines.append(
            f"- Base strategies: {row['base_strategy_count']}; selected `{row['selected_base_strategy_count']}`; promoted `{row['promoted_base_strategy_count']}`"
        )
        lines.append(
            f"- Selected tickers: {row['selected_ticker_count']}; promoted tickers: {row['promoted_ticker_count']}; ready gap: {row['ready_ticker_gap_count']}"
        )
        lines.append(
            f"- Live overlay: strategies `{row['live_manifest_strategy_count']}` across `{row['live_manifest_ticker_count']}` tickers"
        )
        lines.append(
            f"- Strategy sets: {', '.join(f'`{name}`' for name in row['strategy_sets']) if row['strategy_sets'] else 'none'}"
        )
        lines.append(
            f"- Signals: {', '.join(f'`{name}`' for name in row['signal_names']) if row['signal_names'] else 'none'}"
        )
        lines.append(
            f"- DTE modes: {', '.join(f'`{name}`' for name in row['dte_modes']) if row['dte_modes'] else 'none'}"
        )
        lines.append(f"- Note: {row['note']}")
        lines.append("")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fieldnames = [
        "family",
        "structure_bucket",
        "directional_bias",
        "priority",
        "steward_action",
        "base_strategy_count",
        "selected_base_strategy_count",
        "promoted_base_strategy_count",
        "selected_ticker_count",
        "promoted_ticker_count",
        "ready_ticker_gap_count",
        "live_manifest_strategy_count",
        "live_manifest_ticker_count",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def main() -> None:
    args = build_parser().parse_args()
    output_root = Path(args.output_root).resolve()
    ready_base_dir = Path(args.ready_base_dir).resolve()
    live_manifest_path = Path(args.live_manifest_path).resolve() if args.live_manifest_path else Path()
    report_dir = Path(args.report_dir).resolve()
    report_dir.mkdir(parents=True, exist_ok=True)

    strategies_by_family: dict[str, list[Any]] = {}
    strategy_sets_by_base_name: dict[str, set[str]] = {}
    attach_strategy_set_metadata(strategies_by_family, strategy_sets_by_base_name)
    ready = repo_builder.ready_tickers(ready_base_dir)
    summary_records = repo_builder.scan_ticker_summaries(output_root)
    live_manifest = load_live_manifest(live_manifest_path) if args.live_manifest_path else {
        "manifest_path": "",
        "strategy_count": 0,
        "underlying_count": 0,
        "by_family": {},
        "tickers": [],
        "family_rows": {},
    }

    family_rows = build_family_rows(
        strategies_by_family=strategies_by_family,
        strategy_sets_by_base_name=strategy_sets_by_base_name,
        summary_records=summary_records,
        ready_tickers=ready,
        live_manifest=live_manifest,
    )
    priority_families = sorted(
        family_rows,
        key=lambda row: (
            {
                "priority_discovery": 0,
                "priority_validation": 1,
                "promotion_follow_up": 2,
                "live_benchmark": 3,
                "monitor": 4,
            }.get(row["priority"], 9),
            -row["ready_ticker_gap_count"],
            row["family"],
        ),
    )

    researched_tickers = sorted({str(record["ticker"]).upper() for record in summary_records})
    payload = {
        "generated_at": datetime.now().astimezone().isoformat(),
        "output_root": str(output_root),
        "ready_base_dir": str(ready_base_dir),
        "live_manifest": {
            key: value
            for key, value in live_manifest.items()
            if key != "family_rows"
        },
        "ready_ticker_count": len(ready),
        "ready_tickers": ready,
        "research_summary_count": len(summary_records),
        "researched_ticker_count": len(researched_tickers),
        "researched_tickers": researched_tickers,
        "family_count": len(family_rows),
        "base_strategy_count": sum(len(row["base_strategies"]) for row in family_rows),
        "priority_families": priority_families[:12],
        "families": family_rows,
    }

    json_path = report_dir / "strategy_family_registry.json"
    md_path = report_dir / "strategy_family_registry.md"
    csv_path = report_dir / "strategy_family_registry.csv"
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    write_markdown(md_path, payload)
    write_csv(csv_path, family_rows)
    print(
        json.dumps(
            {
                "json_path": str(json_path),
                "markdown_path": str(md_path),
                "csv_path": str(csv_path),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
