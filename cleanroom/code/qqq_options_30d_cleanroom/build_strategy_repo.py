from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from backtest_qqq_greeks_portfolio import build_delta_strategies
import run_multiticker_cleanroom_portfolio as mt


DEFAULT_OUTPUT_ROOT = Path(__file__).resolve().parent / "output"
DEFAULT_READY_BASE_DIR = Path(
    r"C:\Users\rabisaab\OneDrive - First American Corporation\qqq_options_30d_cleanroom\output\backtester_ready"
)
STRATEGY_SETS = (
    "standard",
    "family_expansion",
    "down_choppy_only",
    "down_choppy_exhaustive",
    "opening_window_premium_defense",
    "opening_window_single_vs_multileg",
    "opening_window_convexity_butterfly",
)
SELECTION_PROFILES = ("balanced", "down_choppy_focus", "opening_window_defensive", "opening_window_balanced", "opening_window_convexity")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build a strategy catalog that shows search coverage, promotions, and expansion gaps."
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
        "--report-dir",
        default="",
        help="Optional explicit directory for generated strategy repo artifacts.",
    )
    return parser


def count_grid(grid: dict[str, list[float] | list[int]]) -> int:
    total = 1
    for values in grid.values():
        total *= len(values)
    return total


def leg_to_dict(leg: Any) -> dict[str, Any]:
    return {
        "option_type": str(leg.option_type),
        "side": str(leg.side),
        "target_delta": float(leg.target_delta),
        "min_abs_delta": float(leg.min_abs_delta),
        "max_abs_delta": float(leg.max_abs_delta),
    }


def ready_tickers(base_dir: Path) -> list[str]:
    if not base_dir.exists():
        return []
    return sorted(
        path.name.lower()
        for path in base_dir.iterdir()
        if path.is_dir() and (path / "manifest.json").exists()
    )


def is_ticker_summary(path: Path) -> bool:
    if path.name in {
        "standalone_summary.json",
        "master_summary.json",
        "tournament_conveyor_summary.json",
        "followon_status.json",
        "familyexp_queue_status.json",
        "summary_queue_status.json",
        "promotion_followon_status.json",
    }:
        return False
    return path.name.endswith("_summary.json")


def safe_base_strategy(strategy_name: str) -> str:
    try:
        return mt.parse_strategy_metadata(strategy_name)[2]
    except Exception:
        return strategy_name


def safe_timing_profile(strategy_name: str) -> str:
    try:
        return mt.parse_strategy_metadata(strategy_name)[1]
    except Exception:
        return ""


def scan_ticker_summaries(output_root: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for path in sorted(output_root.rglob("*_summary.json")):
        if not is_ticker_summary(path):
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(payload, dict):
            continue
        if "ticker" not in payload or "promoted" not in payload:
            continue
        ticker = str(payload.get("ticker", "")).upper()
        strategy_set = str(payload.get("strategy_set", "unknown"))
        selection_profile = str(payload.get("selection_profile", "unknown"))
        frozen_config = dict(payload.get("frozen_initial_config", {}))
        selected_names = (
            list(frozen_config.get("selected_bull", []))
            + list(frozen_config.get("selected_bear", []))
            + list(frozen_config.get("selected_choppy", []))
        )
        promoted = dict(payload.get("promoted", {}))
        promoted_names = (
            list(promoted.get("selected_bull", []))
            + list(promoted.get("selected_bear", []))
            + list(promoted.get("selected_choppy", []))
        )
        records.append(
            {
                "path": str(path),
                "research_dir": str(path.parent.name),
                "ticker": ticker,
                "strategy_set": strategy_set,
                "selection_profile": selection_profile,
                "selected_names": selected_names,
                "selected_base_strategies": sorted({safe_base_strategy(name) for name in selected_names}),
                "selected_timing_profiles": sorted({safe_timing_profile(name) for name in selected_names if safe_timing_profile(name)}),
                "promoted_names": promoted_names,
                "promoted_base_strategies": sorted({safe_base_strategy(name) for name in promoted_names}),
                "promoted_timing_profiles": sorted({safe_timing_profile(name) for name in promoted_names if safe_timing_profile(name)}),
                "candidate_trade_count": int(payload.get("candidate_trade_count", 0)),
                "day_count": int(payload.get("day_count", 0)),
            }
        )
    return records


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    lines: list[str] = []
    lines.append("# Strategy Repo")
    lines.append("")
    lines.append("## Snapshot")
    lines.append("")
    lines.append(f"- Ready tickers: {payload['ready_ticker_count']}")
    lines.append(f"- Cataloged base strategies: {payload['base_strategy_count']}")
    lines.append(f"- Research ticker summaries found: {payload['research_summary_count']}")
    lines.append(f"- Unique tickers researched: {payload['researched_ticker_count']}")
    lines.append(f"- Base strategies ever selected: {payload['coverage']['selected_base_strategy_count']}")
    lines.append(f"- Base strategies ever promoted: {payload['coverage']['promoted_base_strategy_count']}")
    lines.append("")
    lines.append("## Strategy Sets")
    lines.append("")
    for strategy_set, item in payload["strategy_sets"].items():
        lines.append(f"### {strategy_set}")
        lines.append("")
        lines.append(
            f"- Base strategies: {item['base_strategy_count']}; timing profiles: {', '.join(item['timing_profiles'])}; variants/ticker: {item['variant_count_per_ticker']}"
        )
        selection_chunks = []
        for selection_profile, selection_item in item["selection_profiles"].items():
            combos = int(selection_item["variant_config_combinations_per_ticker"])
            selection_chunks.append(f"{selection_profile} `{combos:,}`")
        lines.append(f"- Variant-config combos/ticker: {'; '.join(selection_chunks)}")
        lines.append("")
    lines.append("## Family Coverage")
    lines.append("")
    for row in payload["family_coverage"]:
        lines.append(
            f"- `{row['family']}`: {row['base_strategy_count']} base strategies, {row['selected_base_strategy_count']} ever selected, {row['promoted_base_strategy_count']} ever promoted"
        )
    lines.append("")
    lines.append("## Expansion Gaps")
    lines.append("")
    never_selected = list(payload["coverage"]["never_selected_base_strategies"])
    never_promoted = list(payload["coverage"]["never_promoted_base_strategies"])
    lines.append(
        f"- Never selected yet ({len(never_selected)}): {', '.join(f'`{name}`' for name in never_selected[:25]) if never_selected else 'none'}"
    )
    lines.append(
        f"- Never promoted yet ({len(never_promoted)}): {', '.join(f'`{name}`' for name in never_promoted[:25]) if never_promoted else 'none'}"
    )
    lines.append("")
    lines.append("## Research Runs By Strategy Set")
    lines.append("")
    for strategy_set, count in payload["research_runs_by_strategy_set"].items():
        lines.append(f"- `{strategy_set}`: {count}")
    lines.append("")
    lines.append("## Most Promoted Base Strategies")
    lines.append("")
    for row in payload["most_promoted_base_strategies"][:20]:
        lines.append(
            f"- `{row['base_strategy']}`: promoted {row['promotion_count']} times across {row['ticker_count']} tickers"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = build_parser().parse_args()
    output_root = Path(args.output_root).resolve()
    ready_base_dir = Path(args.ready_base_dir).resolve()
    report_dir = (
        Path(args.report_dir).resolve()
        if args.report_dir
        else output_root / f"strategy_repo_{Path(__file__).resolve().stem}_20260421"
    )
    report_dir.mkdir(parents=True, exist_ok=True)

    strategy_catalog: dict[str, dict[str, Any]] = {}
    strategy_sets_payload: dict[str, Any] = {}
    all_base_strategies: set[str] = set()
    family_to_base_names: dict[str, set[str]] = defaultdict(set)

    for strategy_set in STRATEGY_SETS:
        strategies = build_delta_strategies(strategy_set=strategy_set)
        profiles = mt.build_timing_profiles(strategy_set)
        selection_payload: dict[str, Any] = {}
        for selection_profile in SELECTION_PROFILES:
            grid = mt.build_selection_grids(selection_profile, strategy_set)
            selection_payload[selection_profile] = {
                "selection_grid": grid,
                "selection_grid_count": count_grid(grid),
                "variant_config_combinations_per_ticker": len(strategies) * len(profiles) * count_grid(grid),
            }
        strategy_sets_payload[strategy_set] = {
            "base_strategy_count": len(strategies),
            "timing_profiles": [profile.name for profile in profiles],
            "timing_profile_count": len(profiles),
            "variant_count_per_ticker": len(strategies) * len(profiles),
            "families": dict(sorted(Counter(strategy.family for strategy in strategies).items())),
            "signals": dict(sorted(Counter(strategy.signal_name for strategy in strategies).items())),
            "dte_modes": dict(sorted(Counter(strategy.dte_mode for strategy in strategies).items())),
            "selection_profiles": selection_payload,
        }
        for strategy in strategies:
            all_base_strategies.add(strategy.name)
            family_to_base_names[strategy.family].add(strategy.name)
            record = strategy_catalog.setdefault(
                strategy.name,
                {
                    "name": strategy.name,
                    "family": strategy.family,
                    "description": strategy.description,
                    "signal_name": strategy.signal_name,
                    "dte_mode": strategy.dte_mode,
                    "leg_count": len(strategy.legs),
                    "legs": [leg_to_dict(leg) for leg in strategy.legs],
                    "strategy_sets": [],
                },
            )
            if strategy_set not in record["strategy_sets"]:
                record["strategy_sets"].append(strategy_set)

    summary_records = scan_ticker_summaries(output_root)
    ready = ready_tickers(ready_base_dir)

    selected_counter: Counter[str] = Counter()
    promoted_counter: Counter[str] = Counter()
    selected_ticker_counter: defaultdict[str, set[str]] = defaultdict(set)
    promoted_ticker_counter: defaultdict[str, set[str]] = defaultdict(set)
    research_runs_by_strategy_set: Counter[str] = Counter()
    researched_tickers: set[str] = set()

    for record in summary_records:
        research_runs_by_strategy_set[record["strategy_set"]] += 1
        researched_tickers.add(record["ticker"])
        for name in record["selected_base_strategies"]:
            selected_counter[name] += 1
            selected_ticker_counter[name].add(record["ticker"])
        for name in record["promoted_base_strategies"]:
            promoted_counter[name] += 1
            promoted_ticker_counter[name].add(record["ticker"])

    family_rows: list[dict[str, Any]] = []
    for family, base_names in sorted(family_to_base_names.items()):
        selected_names = sorted(name for name in base_names if selected_counter[name] > 0)
        promoted_names = sorted(name for name in base_names if promoted_counter[name] > 0)
        family_rows.append(
            {
                "family": family,
                "base_strategy_count": len(base_names),
                "selected_base_strategy_count": len(selected_names),
                "promoted_base_strategy_count": len(promoted_names),
                "never_selected_base_strategies": sorted(name for name in base_names if selected_counter[name] == 0),
                "never_promoted_base_strategies": sorted(name for name in base_names if promoted_counter[name] == 0),
            }
        )

    most_promoted = [
        {
            "base_strategy": name,
            "promotion_count": count,
            "ticker_count": len(promoted_ticker_counter[name]),
        }
        for name, count in promoted_counter.most_common()
    ]

    payload = {
        "ready_ticker_count": len(ready),
        "ready_tickers": ready,
        "base_strategy_count": len(all_base_strategies),
        "base_strategies": [
            {
                **record,
                "strategy_sets": sorted(record["strategy_sets"]),
                "selected_count": int(selected_counter.get(name, 0)),
                "promotion_count": int(promoted_counter.get(name, 0)),
                "selected_ticker_count": len(selected_ticker_counter.get(name, set())),
                "promoted_ticker_count": len(promoted_ticker_counter.get(name, set())),
            }
            for name, record in sorted(strategy_catalog.items())
        ],
        "strategy_sets": strategy_sets_payload,
        "research_summary_count": len(summary_records),
        "researched_ticker_count": len(researched_tickers),
        "research_runs_by_strategy_set": dict(sorted(research_runs_by_strategy_set.items())),
        "coverage": {
            "selected_base_strategy_count": sum(1 for name in all_base_strategies if selected_counter[name] > 0),
            "promoted_base_strategy_count": sum(1 for name in all_base_strategies if promoted_counter[name] > 0),
            "never_selected_base_strategies": sorted(name for name in all_base_strategies if selected_counter[name] == 0),
            "never_promoted_base_strategies": sorted(name for name in all_base_strategies if promoted_counter[name] == 0),
        },
        "family_coverage": family_rows,
        "most_promoted_base_strategies": most_promoted,
    }

    json_path = report_dir / "strategy_repo.json"
    md_path = report_dir / "strategy_repo.md"
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    write_markdown(md_path, payload)
    print(json.dumps({"json_path": str(json_path), "markdown_path": str(md_path)}, indent=2))


if __name__ == "__main__":
    main()
