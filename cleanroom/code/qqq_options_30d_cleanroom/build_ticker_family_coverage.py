from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

import build_agent_sharding_plan as shard_plan
import build_strategy_repo as strategy_repo_builder
import run_multiticker_cleanroom_portfolio as mt


ROOT = Path(__file__).resolve().parent
DEFAULT_OUTPUT_ROOT = ROOT / "output"
DEFAULT_STRATEGY_REPO_JSON = ROOT / "output" / "strategy_repo_build_strategy_repo_20260421" / "strategy_repo.json"
DEFAULT_READY_BASE_DIR = Path(r"C:\Users\rabisaab\OneDrive - First American Corporation\qqq_options_30d_cleanroom\output\backtester_ready")
DEFAULT_SECONDARY_OUTPUT = Path(r"C:\Users\rabisaab\OneDrive - First American Corporation\qqq_options_30d_cleanroom\output")
DEFAULT_REGISTRY_PATH = DEFAULT_SECONDARY_OUTPUT / "backtester_registry.csv"
DEFAULT_MATERIALIZER = ROOT / "materialize_backtester_ready.py"


LANE_TEMPLATES = [
    {
        "lane_id": "01_bear_directional",
        "description": "Single-leg long put plus debit put spread discovery.",
        "families": ["Single-leg long put", "Debit put spread"],
    },
    {
        "lane_id": "02_bear_premium",
        "description": "Credit call spread plus neutral premium structures.",
        "families": ["Credit call spread", "Iron condor", "Iron butterfly"],
    },
    {
        "lane_id": "03_bear_convexity",
        "description": "Put backspread plus long-vol convexity structures.",
        "families": ["Put backspread", "Long straddle", "Long strangle"],
    },
    {
        "lane_id": "04_butterfly_lab",
        "description": "Put butterfly and broken-wing put butterfly lab.",
        "families": ["Put butterfly", "Broken-wing put butterfly"],
    },
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build a ticker-family coverage matrix and next-wave plan for the cleanroom strategy search."
    )
    parser.add_argument("--output-root", default=str(DEFAULT_OUTPUT_ROOT))
    parser.add_argument("--strategy-repo-json", default=str(DEFAULT_STRATEGY_REPO_JSON))
    parser.add_argument("--ready-base-dir", default=str(DEFAULT_READY_BASE_DIR))
    parser.add_argument("--secondary-output-dir", default=str(DEFAULT_SECONDARY_OUTPUT))
    parser.add_argument("--registry-path", default=str(DEFAULT_REGISTRY_PATH))
    parser.add_argument(
        "--report-dir",
        default=str(DEFAULT_OUTPUT_ROOT / f"ticker_family_coverage_{datetime.now().strftime('%Y%m%d_%H%M%S')}"),
    )
    parser.add_argument("--top-ready-per-lane", type=int, default=12)
    parser.add_argument("--top-staged-per-lane", type=int, default=8)
    parser.add_argument("--top-registry-per-lane", type=int, default=8)
    return parser


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


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


def scalar_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def ensure_strategy_repo_json(path: Path, *, output_root: Path, ready_base_dir: Path) -> Path:
    if path.exists():
        return path
    builder_path = ROOT / "build_strategy_repo.py"
    report_dir = output_root / "strategy_repo_autobuild_20260421"
    report_dir.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            sys.executable,
            str(builder_path),
            "--output-root",
            str(output_root),
            "--ready-base-dir",
            str(ready_base_dir),
            "--report-dir",
            str(report_dir),
        ],
        cwd=ROOT,
        check=True,
    )
    candidate = report_dir / "strategy_repo.json"
    if not candidate.exists():
        raise FileNotFoundError(f"strategy repo autobuild did not produce {candidate}")
    return candidate


def normalize_strategy_repo(path: Path) -> dict[str, Any]:
    payload = load_json(path)
    base_strategies = list(payload.get("base_strategies", []))
    family_coverage = list(payload.get("family_coverage", []))
    family_priority = {
        row["family"]: (
            int(row.get("base_strategy_count", 0)) * 10
            - int(row.get("selected_base_strategy_count", 0)) * 4
            - int(row.get("promoted_base_strategy_count", 0)) * 6
        )
        for row in family_coverage
    }

    family_to_sets: dict[str, set[str]] = defaultdict(set)
    family_to_bases: dict[str, set[str]] = defaultdict(set)
    base_to_family: dict[str, str] = {}
    for row in base_strategies:
        family = str(row.get("family", "Unknown"))
        name = str(row.get("name", ""))
        base_to_family[name] = family
        family_to_bases[family].add(name)
        for strategy_set in row.get("strategy_sets", []):
            family_to_sets[family].add(str(strategy_set))

    return {
        "payload": payload,
        "family_priority": family_priority,
        "family_to_sets": {family: sorted(values) for family, values in family_to_sets.items()},
        "family_to_bases": {family: sorted(values) for family, values in family_to_bases.items()},
        "base_to_family": base_to_family,
    }


def scan_summary_paths(output_root: Path) -> list[Path]:
    paths: list[Path] = []
    for path in sorted(output_root.rglob("*_summary.json")):
        if strategy_repo_builder.is_ticker_summary(path):
            paths.append(path)
    return paths


def infer_tested_families(
    *,
    strategy_set: str,
    family_include_filters: list[str],
    family_exclude_filters: list[str],
    family_to_sets: dict[str, list[str]],
) -> set[str]:
    families = {
        family
        for family, strategy_sets in family_to_sets.items()
        if strategy_set in strategy_sets
    }
    if family_include_filters:
        families = {
            family
            for family in families
            if any(token in {
                mt.normalize_family_token(family),
                mt.normalize_family_token(mt.family_bucket_for_strategy_family(family)),
            } for token in family_include_filters)
        }
    if family_exclude_filters:
        families = {
            family
            for family in families
            if not any(token in {
                mt.normalize_family_token(family),
                mt.normalize_family_token(mt.family_bucket_for_strategy_family(family)),
            } for token in family_exclude_filters)
        }
    return families


def scan_run_records(
    *,
    output_root: Path,
    strategy_repo: dict[str, Any],
) -> list[dict[str, Any]]:
    base_to_family = strategy_repo["base_to_family"]
    family_to_sets = strategy_repo["family_to_sets"]
    records: list[dict[str, Any]] = []
    for path in scan_summary_paths(output_root):
        try:
            payload = load_json(path)
        except Exception:
            continue
        if not isinstance(payload, dict):
            continue
        if "ticker" not in payload or "promoted" not in payload:
            continue
        promoted = dict(payload.get("promoted", {}))
        frozen_config = dict(payload.get("frozen_initial_config", {}))
        selected_names = (
            list(frozen_config.get("selected_bull", []))
            + list(frozen_config.get("selected_bear", []))
            + list(frozen_config.get("selected_choppy", []))
        )
        promoted_names = (
            list(promoted.get("selected_bull", []))
            + list(promoted.get("selected_bear", []))
            + list(promoted.get("selected_choppy", []))
        )
        family_include_filters = [str(item) for item in payload.get("family_include_filters", [])]
        family_exclude_filters = [str(item) for item in payload.get("family_exclude_filters", [])]
        selected_families = sorted(
            {
                base_to_family.get(mt.parse_strategy_metadata(name)[2], base_to_family.get(name, "Unknown"))
                if "__" in name
                else base_to_family.get(name, "Unknown")
                for name in selected_names
            }
        )
        promoted_families = sorted(
            {
                base_to_family.get(mt.parse_strategy_metadata(name)[2], base_to_family.get(name, "Unknown"))
                if "__" in name
                else base_to_family.get(name, "Unknown")
                for name in promoted_names
            }
        )
        inferred_tested_families = infer_tested_families(
            strategy_set=str(payload.get("strategy_set", "unknown")),
            family_include_filters=family_include_filters,
            family_exclude_filters=family_exclude_filters,
            family_to_sets=family_to_sets,
        )
        tested_families = sorted(set(inferred_tested_families) | set(selected_families) | set(promoted_families))
        records.append(
            {
                "ticker": str(payload.get("ticker", "")).upper(),
                "path": str(path),
                "mtime_epoch": path.stat().st_mtime,
                "research_dir": path.parent.name,
                "strategy_set": str(payload.get("strategy_set", "unknown")),
                "selection_profile": str(payload.get("selection_profile", "unknown")),
                "timing_profiles": list(payload.get("timing_profiles", [])),
                "family_include_filters": family_include_filters,
                "family_exclude_filters": family_exclude_filters,
                "tested_families": tested_families,
                "selected_families": selected_families,
                "promoted_families": promoted_families,
                "selected_base_strategies": sorted(
                    {
                        mt.parse_strategy_metadata(name)[2] if "__" in name else name
                        for name in selected_names
                    }
                ),
                "promoted_base_strategies": sorted(
                    {
                        mt.parse_strategy_metadata(name)[2] if "__" in name else name
                        for name in promoted_names
                    }
                ),
                "candidate_trade_count": int(payload.get("candidate_trade_count", 0)),
                "day_count": int(payload.get("day_count", 0)),
                "frozen_total_return_pct": scalar_float(payload.get("frozen_initial", {}).get("total_return_pct")),
                "frozen_max_drawdown_pct": scalar_float(payload.get("frozen_initial", {}).get("max_drawdown_pct")),
                "frozen_trade_count": int(payload.get("frozen_initial", {}).get("trade_count", 0)),
                "frozen_calmar_like": scalar_float(payload.get("frozen_initial", {}).get("calmar_like")),
                "frozen_avg_friction_pct": scalar_float(payload.get("frozen_initial", {}).get("friction_profile", {}).get("avg_friction_pct_of_entry_premium")),
                "frozen_trade_share_sub_0_30_pct": scalar_float(payload.get("frozen_initial", {}).get("friction_profile", {}).get("trade_share_sub_0_30_pct")),
            }
        )
    return records


def scan_registry(path: Path) -> tuple[set[str], dict[str, dict[str, Any]]]:
    if not path.exists():
        return set(), {}
    rows: list[dict[str, str]] = []
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        rows.extend(reader)
    registry_symbols = sorted({(row.get("symbol") or "").strip().upper() for row in rows if (row.get("symbol") or "").strip()})
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        symbol = (row.get("symbol") or "").strip().upper()
        if symbol:
            grouped[symbol].append(row)
    summary: dict[str, dict[str, Any]] = {}
    for symbol, entries in grouped.items():
        source_kinds = Counter((entry.get("source_kind") or "").strip() for entry in entries if (entry.get("source_kind") or "").strip())
        artifact_count = len(entries)
        materialized_count = sum(1 for entry in entries if str(entry.get("materialized_exists", "")).lower() == "true")
        bundle_sources = {
            entry.get("source_path") or ""
            for entry in entries
            if (entry.get("source_kind") or "").strip() == "bundle_zip" and (entry.get("source_path") or "").strip()
        }
        summary[symbol] = {
            "registry_artifact_count": artifact_count,
            "registry_materialized_artifact_count": materialized_count,
            "registry_source_kinds": dict(source_kinds),
            "bundle_source_paths": sorted(bundle_sources),
        }
    return set(registry_symbols), summary


def build_coverage_rows(
    *,
    families: list[str],
    tickers: list[str],
    ready_tickers: set[str],
    staged_bundle_tickers: set[str],
    registry_tickers: set[str],
    registry_summary: dict[str, dict[str, Any]],
    run_records: list[dict[str, Any]],
    strategy_repo: dict[str, Any],
) -> list[dict[str, Any]]:
    run_records_by_ticker: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in run_records:
        run_records_by_ticker[record["ticker"]].append(record)

    rows: list[dict[str, Any]] = []
    for ticker in tickers:
        ticker_runs = run_records_by_ticker.get(ticker, [])
        for family in families:
            tested_runs = [record for record in ticker_runs if family in record["tested_families"]]
            selected_runs = [record for record in ticker_runs if family in record["selected_families"]]
            promoted_runs = [record for record in ticker_runs if family in record["promoted_families"]]
            best_selected = max(selected_runs, key=lambda record: record["frozen_total_return_pct"], default=None)
            best_promoted = max(promoted_runs, key=lambda record: record["frozen_total_return_pct"], default=None)
            family_priority = int(strategy_repo["family_priority"].get(family, 0))
            tested_penalty = len(tested_runs) * 10
            selected_penalty = len(selected_runs) * 18
            promoted_penalty = len(promoted_runs) * 30
            readiness_bonus = 30 if ticker in ready_tickers else 15 if ticker in staged_bundle_tickers else 5 if ticker in registry_tickers else 0
            novelty_bonus = 25 if not tested_runs else 10 if not selected_runs else 0
            gap_score = family_priority + readiness_bonus + novelty_bonus - tested_penalty - selected_penalty - promoted_penalty
            rows.append(
                {
                    "ticker": ticker,
                    "family": family,
                    "family_bucket": mt.family_bucket_for_strategy_family(family),
                    "is_registry_symbol": ticker in registry_tickers,
                    "is_staged_bundle": ticker in staged_bundle_tickers,
                    "is_ready": ticker in ready_tickers,
                    "registry_artifact_count": int(registry_summary.get(ticker, {}).get("registry_artifact_count", 0)),
                    "tested_run_count": len(tested_runs),
                    "selected_run_count": len(selected_runs),
                    "promoted_run_count": len(promoted_runs),
                    "tested_strategy_sets": sorted({record["strategy_set"] for record in tested_runs}),
                    "tested_selection_profiles": sorted({record["selection_profile"] for record in tested_runs}),
                    "last_tested_research_dir": tested_runs[-1]["research_dir"] if tested_runs else "",
                    "last_tested_path": tested_runs[-1]["path"] if tested_runs else "",
                    "last_tested_at_epoch": tested_runs[-1]["mtime_epoch"] if tested_runs else 0.0,
                    "best_selected_return_pct": best_selected["frozen_total_return_pct"] if best_selected else 0.0,
                    "best_selected_max_drawdown_pct": best_selected["frozen_max_drawdown_pct"] if best_selected else 0.0,
                    "best_selected_avg_friction_pct": best_selected["frozen_avg_friction_pct"] if best_selected else 0.0,
                    "best_selected_trade_share_sub_0_30_pct": best_selected["frozen_trade_share_sub_0_30_pct"] if best_selected else 0.0,
                    "best_promoted_return_pct": best_promoted["frozen_total_return_pct"] if best_promoted else 0.0,
                    "best_promoted_max_drawdown_pct": best_promoted["frozen_max_drawdown_pct"] if best_promoted else 0.0,
                    "family_priority_score": family_priority,
                    "gap_score": gap_score,
                }
            )
    return rows


def build_family_summary(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[row["family"]].append(row)
    summary: list[dict[str, Any]] = []
    for family, family_rows in sorted(grouped.items()):
        summary.append(
            {
                "family": family,
                "family_bucket": family_rows[0]["family_bucket"],
                "ready_untested_ticker_count": sum(1 for row in family_rows if row["is_ready"] and row["tested_run_count"] == 0),
                "staged_untested_ticker_count": sum(1 for row in family_rows if row["is_staged_bundle"] and row["tested_run_count"] == 0),
                "registry_untested_ticker_count": sum(1 for row in family_rows if row["is_registry_symbol"] and row["tested_run_count"] == 0),
                "selected_ticker_count": sum(1 for row in family_rows if row["selected_run_count"] > 0),
                "promoted_ticker_count": sum(1 for row in family_rows if row["promoted_run_count"] > 0),
                "avg_gap_score_ready": round(
                    sum(row["gap_score"] for row in family_rows if row["is_ready"]) / max(1, sum(1 for row in family_rows if row["is_ready"])),
                    2,
                ),
            }
        )
    summary.sort(key=lambda row: (-row["ready_untested_ticker_count"], -row["avg_gap_score_ready"], row["family"]))
    return summary


def build_ticker_summary(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[row["ticker"]].append(row)
    summary: list[dict[str, Any]] = []
    for ticker, ticker_rows in sorted(grouped.items()):
        summary.append(
            {
                "ticker": ticker,
                "is_ready": ticker_rows[0]["is_ready"],
                "is_staged_bundle": ticker_rows[0]["is_staged_bundle"],
                "is_registry_symbol": ticker_rows[0]["is_registry_symbol"],
                "untested_family_count": sum(1 for row in ticker_rows if row["tested_run_count"] == 0),
                "selected_family_count": sum(1 for row in ticker_rows if row["selected_run_count"] > 0),
                "promoted_family_count": sum(1 for row in ticker_rows if row["promoted_run_count"] > 0),
                "avg_gap_score": round(sum(row["gap_score"] for row in ticker_rows) / max(1, len(ticker_rows)), 2),
                "max_gap_score": max(row["gap_score"] for row in ticker_rows),
            }
        )
    summary.sort(key=lambda row: (-row["avg_gap_score"], row["ticker"]))
    return summary


def build_next_wave_plan(
    *,
    rows: list[dict[str, Any]],
    ready_tickers: set[str],
    staged_bundle_tickers: set[str],
    registry_tickers: set[str],
    args: argparse.Namespace,
) -> dict[str, Any]:
    next_wave_rows = []
    for template in LANE_TEMPLATES:
        lane_rows = [row for row in rows if row["family"] in template["families"]]

        def top_tickers(pool_rows: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
            best_by_ticker: dict[str, dict[str, Any]] = {}
            for row in pool_rows:
                ticker = row["ticker"]
                existing = best_by_ticker.get(ticker)
                if existing is None or row["gap_score"] > existing["gap_score"]:
                    best_by_ticker[ticker] = row
            ranked = sorted(
                best_by_ticker.values(),
                key=lambda row: (-row["gap_score"], row["tested_run_count"], row["ticker"]),
            )
            return ranked[:limit]

        ready_rows = top_tickers([row for row in lane_rows if row["ticker"] in ready_tickers], args.top_ready_per_lane)
        staged_rows = top_tickers(
            [row for row in lane_rows if row["ticker"] in staged_bundle_tickers and row["ticker"] not in ready_tickers],
            args.top_staged_per_lane,
        )
        registry_rows = top_tickers(
            [row for row in lane_rows if row["ticker"] in registry_tickers and row["ticker"] not in staged_bundle_tickers and row["ticker"] not in ready_tickers],
            args.top_registry_per_lane,
        )
        next_wave_rows.append(
            {
                "lane_id": template["lane_id"],
                "description": template["description"],
                "families": list(template["families"]),
                "ready_discovery": ready_rows,
                "staged_materialization": staged_rows,
                "registry_download": registry_rows,
            }
        )
    return {
        "generated_at": datetime.now().isoformat(),
        "lane_templates": next_wave_rows,
    }


def write_markdown(
    *,
    path: Path,
    coverage_rows: list[dict[str, Any]],
    family_summary: list[dict[str, Any]],
    ticker_summary: list[dict[str, Any]],
    next_wave_plan: dict[str, Any],
) -> None:
    lines = [
        "# Ticker-Family Coverage",
        "",
        f"- Coverage rows: {len(coverage_rows)}",
        f"- Families: {len({row['family'] for row in coverage_rows})}",
        f"- Tickers: {len({row['ticker'] for row in coverage_rows})}",
        "",
        "## Highest-Gap Families",
        "",
    ]
    for row in family_summary[:12]:
        lines.append(
            f"- `{row['family']}`: ready untested `{row['ready_untested_ticker_count']}`, staged untested `{row['staged_untested_ticker_count']}`, promoted tickers `{row['promoted_ticker_count']}`"
        )
    lines.append("")
    lines.append("## Highest-Gap Tickers")
    lines.append("")
    for row in ticker_summary[:20]:
        lines.append(
            f"- `{row['ticker']}`: avg gap `{row['avg_gap_score']}`, untested families `{row['untested_family_count']}`, promoted families `{row['promoted_family_count']}`"
        )
    lines.append("")
    lines.append("## Next Wave")
    lines.append("")
    for lane in next_wave_plan["lane_templates"]:
        lines.append(f"### {lane['lane_id']}")
        lines.append("")
        lines.append(f"- families: {', '.join(f'`{family}`' for family in lane['families'])}")
        ready_discovery = ", ".join(f"`{row['ticker']}`" for row in lane["ready_discovery"]) if lane["ready_discovery"] else "none"
        staged_materialization = (
            ", ".join(f"`{row['ticker']}`" for row in lane["staged_materialization"])
            if lane["staged_materialization"]
            else "none"
        )
        registry_download = (
            ", ".join(f"`{row['ticker']}`" for row in lane["registry_download"])
            if lane["registry_download"]
            else "none"
        )
        lines.append(
            f"- ready discovery: {ready_discovery}"
        )
        lines.append(
            f"- staged materialization: {staged_materialization}"
        )
        lines.append(
            f"- registry download: {registry_download}"
        )
        prep_tickers = sorted(
            {
                row["ticker"]
                for bucket in ("staged_materialization", "registry_download")
                for row in lane[bucket]
            }
        )
        lines.append(
            f"- prep/materialize next: {', '.join(f'`{ticker}`' for ticker in prep_tickers) if prep_tickers else 'none'}"
        )
        lines.append("")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def family_include_arg(families: list[str]) -> str:
    return ",".join(sorted({mt.normalize_family_token(family) for family in families}))


def build_next_wave_commands(
    *,
    next_wave_plan: dict[str, Any],
    ready_base_dir: Path,
    report_dir: Path,
) -> list[str]:
    commands: list[str] = []
    for lane in next_wave_plan["lane_templates"]:
        tickers = [row["ticker"].lower() for row in lane["ready_discovery"]]
        if not tickers:
            continue
        research_dir = report_dir / "ready_discovery" / lane["lane_id"]
        family_include = family_include_arg(list(lane["families"]))
        parts = [
            "python",
            str((ROOT / "run_core_strategy_expansion_overnight.py").resolve()),
            "--tickers",
            ",".join(tickers),
            "--ready-base-dir",
            str(ready_base_dir.resolve()),
            "--research-dir",
            str(research_dir.resolve()),
            "--strategy-set",
            "down_choppy_only",
            "--selection-profile",
            "down_choppy_focus",
            "--family-include",
            family_include,
        ]
        commands.append(" ".join(f'"{part}"' if " " in part else part for part in parts))
    return commands


def build_materialization_commands(
    *,
    next_wave_plan: dict[str, Any],
    report_dir: Path,
) -> list[str]:
    commands: list[str] = []
    materializer_path = DEFAULT_MATERIALIZER.resolve()
    for lane in next_wave_plan["lane_templates"]:
        tickers = sorted(
            {
                row["ticker"].lower()
                for bucket in ("staged_materialization", "registry_download")
                for row in lane[bucket]
            }
        )
        if not tickers:
            continue
        prep_dir = report_dir / "data_prep" / lane["lane_id"]
        parts = [
            "python",
            str(materializer_path),
            "--tickers",
            ",".join(tickers),
            "--report-dir",
            str(prep_dir.resolve()),
            "--only-missing",
            "--update-registry",
        ]
        commands.append(" ".join(f'"{part}"' if " " in part else part for part in parts))
    return commands


def main() -> None:
    args = build_parser().parse_args()
    output_root = Path(args.output_root).resolve()
    strategy_repo_json = Path(args.strategy_repo_json).resolve()
    ready_base_dir = Path(args.ready_base_dir).resolve()
    secondary_output_dir = Path(args.secondary_output_dir).resolve()
    registry_path = Path(args.registry_path).resolve()
    report_dir = Path(args.report_dir).resolve()
    report_dir.mkdir(parents=True, exist_ok=True)

    strategy_repo_json = ensure_strategy_repo_json(
        strategy_repo_json,
        output_root=output_root,
        ready_base_dir=ready_base_dir,
    )
    strategy_repo = normalize_strategy_repo(strategy_repo_json)
    run_records = scan_run_records(output_root=output_root, strategy_repo=strategy_repo)
    ready_tickers = set(ticker.upper() for ticker in strategy_repo_builder.ready_tickers(ready_base_dir))
    staged_bundle_tickers = set(shard_plan.scan_bundle_tickers(output_root) | shard_plan.scan_bundle_tickers(secondary_output_dir))
    registry_tickers, registry_summary = scan_registry(registry_path)

    all_tickers = sorted(ready_tickers | staged_bundle_tickers | registry_tickers | {record["ticker"] for record in run_records})
    families = sorted(strategy_repo["family_to_sets"].keys())

    coverage_rows = build_coverage_rows(
        families=families,
        tickers=all_tickers,
        ready_tickers=ready_tickers,
        staged_bundle_tickers=staged_bundle_tickers,
        registry_tickers=registry_tickers,
        registry_summary=registry_summary,
        run_records=sorted(run_records, key=lambda record: record["mtime_epoch"]),
        strategy_repo=strategy_repo,
    )
    family_summary = build_family_summary(coverage_rows)
    ticker_summary = build_ticker_summary(coverage_rows)
    next_wave_plan = build_next_wave_plan(
        rows=coverage_rows,
        ready_tickers=ready_tickers,
        staged_bundle_tickers=staged_bundle_tickers,
        registry_tickers=registry_tickers,
        args=args,
    )
    next_wave_commands = build_next_wave_commands(
        next_wave_plan=next_wave_plan,
        ready_base_dir=ready_base_dir,
        report_dir=report_dir,
    )
    next_wave_prep_commands = build_materialization_commands(
        next_wave_plan=next_wave_plan,
        report_dir=report_dir,
    )

    payload = {
        "generated_at": datetime.now().isoformat(),
        "ready_ticker_count": len(ready_tickers),
        "staged_bundle_ticker_count": len(staged_bundle_tickers),
        "registry_ticker_count": len(registry_tickers),
        "research_run_count": len(run_records),
        "coverage_rows": coverage_rows,
        "family_summary": family_summary,
        "ticker_summary": ticker_summary,
        "next_wave_plan": next_wave_plan,
        "next_wave_commands": next_wave_commands,
        "next_wave_prep_commands": next_wave_prep_commands,
    }

    write_json(report_dir / "ticker_family_coverage.json", payload)
    write_csv(report_dir / "ticker_family_coverage.csv", coverage_rows)
    write_csv(report_dir / "family_summary.csv", family_summary)
    write_csv(report_dir / "ticker_summary.csv", ticker_summary)
    write_json(report_dir / "next_wave_plan.json", next_wave_plan)
    (report_dir / "next_wave_commands.ps1").write_text("\n".join(next_wave_commands), encoding="utf-8")
    (report_dir / "next_wave_prep_commands.ps1").write_text("\n".join(next_wave_prep_commands), encoding="utf-8")
    write_markdown(
        path=report_dir / "ticker_family_coverage.md",
        coverage_rows=coverage_rows,
        family_summary=family_summary,
        ticker_summary=ticker_summary,
        next_wave_plan=next_wave_plan,
    )

    print(
        json.dumps(
            {
                "report_dir": str(report_dir),
                "coverage_row_count": len(coverage_rows),
                "family_count": len(families),
                "ticker_count": len(all_tickers),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
