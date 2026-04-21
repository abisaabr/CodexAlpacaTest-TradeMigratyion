from __future__ import annotations

import argparse
import ctypes
import json
import math
import csv
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
DEFAULT_PRIMARY_OUTPUT = ROOT / "output"
DEFAULT_SECONDARY_OUTPUT = Path(r"C:\Users\rabisaab\OneDrive - First American Corporation\qqq_options_30d_cleanroom\output")
DEFAULT_BACKTESTER_READY = DEFAULT_SECONDARY_OUTPUT / "backtester_ready"
DEFAULT_STRATEGY_REPO_JSON = ROOT / "output" / "strategy_repo_build_strategy_repo_20260421" / "strategy_repo.json"


DOWN_CHOPPY_PRIORITY_FAMILIES = [
    "Credit call spread",
    "Debit put spread",
    "Put backspread",
    "Iron condor",
    "Iron butterfly",
    "Put butterfly",
    "Broken-wing put butterfly",
    "Long straddle",
    "Long strangle",
    "Single-leg long put",
]

BALANCED_EXPANSION_PRIORITY_FAMILIES = [
    "Debit call spread",
    "Credit put spread",
    "Call backspread",
    "Call butterfly",
    "Broken-wing call butterfly",
    "Single-leg long call",
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build a machine-aware agent sharding plan for the cleanroom tournament conveyor."
    )
    parser.add_argument("--primary-output-dir", default=str(DEFAULT_PRIMARY_OUTPUT))
    parser.add_argument("--secondary-output-dir", default=str(DEFAULT_SECONDARY_OUTPUT))
    parser.add_argument("--backtester-ready-dir", default=str(DEFAULT_BACKTESTER_READY))
    parser.add_argument("--strategy-repo-json", default=str(DEFAULT_STRATEGY_REPO_JSON))
    parser.add_argument("--target-ticker-count", type=int, default=159)
    parser.add_argument("--output-dir", default=str(DEFAULT_PRIMARY_OUTPUT / f"agent_sharding_plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}"))
    return parser


class MEMORYSTATUSEX(ctypes.Structure):
    _fields_ = [
        ("dwLength", ctypes.c_ulong),
        ("dwMemoryLoad", ctypes.c_ulong),
        ("ullTotalPhys", ctypes.c_ulonglong),
        ("ullAvailPhys", ctypes.c_ulonglong),
        ("ullTotalPageFile", ctypes.c_ulonglong),
        ("ullAvailPageFile", ctypes.c_ulonglong),
        ("ullTotalVirtual", ctypes.c_ulonglong),
        ("ullAvailVirtual", ctypes.c_ulonglong),
        ("sullAvailExtendedVirtual", ctypes.c_ulonglong),
    ]


def get_memory_profile() -> dict[str, float]:
    stat = MEMORYSTATUSEX()
    stat.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
    ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat))
    gb = 1024 ** 3
    return {
        "total_gb": round(stat.ullTotalPhys / gb, 2),
        "free_gb": round(stat.ullAvailPhys / gb, 2),
    }


def chunk_list(values: list[str], chunk_count: int) -> list[list[str]]:
    if chunk_count <= 0:
        return [values]
    size = math.ceil(len(values) / chunk_count)
    return [values[index : index + size] for index in range(0, len(values), size)]


def scan_bundle_tickers(root: Path) -> set[str]:
    return {path.name.replace("_365d_bundle.zip", "").upper() for path in root.glob("*_365d_bundle.zip")}


def scan_backtester_ready_tickers(root: Path) -> list[str]:
    if not root.exists():
        return []
    ignored = {"COLLECTIONS"}
    tickers = [path.name.upper() for path in root.iterdir() if path.is_dir() and path.name.upper() not in ignored]
    return sorted(tickers)


def scan_registry_tickers(root: Path) -> list[str]:
    path = root / "backtester_registry.csv"
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        return sorted(
            {
                (row.get("symbol") or "").strip().upper()
                for row in reader
                if (row.get("symbol") or "").strip()
            }
        )


def load_strategy_repo(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def family_gap_ranking(strategy_repo: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for row in strategy_repo.get("family_coverage", []):
        rows.append(
            {
                "family": row["family"],
                "base_strategy_count": int(row["base_strategy_count"]),
                "selected_base_strategy_count": int(row["selected_base_strategy_count"]),
                "promoted_base_strategy_count": int(row["promoted_base_strategy_count"]),
                "never_selected_base_strategies": list(row.get("never_selected_base_strategies", [])),
                "never_promoted_base_strategies": list(row.get("never_promoted_base_strategies", [])),
                "priority_score": (
                    int(row["base_strategy_count"]) * 10
                    - int(row["selected_base_strategy_count"]) * 4
                    - int(row["promoted_base_strategy_count"]) * 6
                ),
            }
        )
    rows.sort(key=lambda row: (-row["priority_score"], row["promoted_base_strategy_count"], row["selected_base_strategy_count"], row["family"]))
    return rows


def recommend_concurrency(logical_cpus: int, free_gb: float) -> dict[str, int]:
    if logical_cpus >= 16 and free_gb >= 32:
        return {
            "lean_parallel_backtests": 4,
            "heavy_parallel_backtests": 2,
            "validation_parallel_backtests": 1,
            "recommended_total_agents": 8,
        }
    if logical_cpus >= 12 and free_gb >= 24:
        return {
            "lean_parallel_backtests": 3,
            "heavy_parallel_backtests": 2,
            "validation_parallel_backtests": 1,
            "recommended_total_agents": 7,
        }
    return {
        "lean_parallel_backtests": 2,
        "heavy_parallel_backtests": 1,
        "validation_parallel_backtests": 1,
        "recommended_total_agents": 5,
    }


def build_cohort_plan(
    *,
    tickers: list[str],
    cohort_count: int,
    label_prefix: str,
) -> list[dict[str, Any]]:
    cohorts = []
    for index, cohort in enumerate(chunk_list(tickers, cohort_count), start=1):
        cohorts.append(
            {
                "cohort_id": f"{label_prefix}{index:02d}",
                "ticker_count": len(cohort),
                "tickers": cohort,
            }
        )
    return cohorts


def build_plan(
    *,
    primary_output_dir: Path,
    secondary_output_dir: Path,
    backtester_ready_dir: Path,
    strategy_repo_json: Path,
    target_ticker_count: int,
) -> dict[str, Any]:
    logical_cpus = int(__import__("os").cpu_count() or 1)
    memory = get_memory_profile()
    concurrency = recommend_concurrency(logical_cpus, memory["free_gb"])

    primary_bundles = scan_bundle_tickers(primary_output_dir)
    secondary_bundles = scan_bundle_tickers(secondary_output_dir)
    staged_union = sorted(primary_bundles | secondary_bundles)
    backtester_ready = scan_backtester_ready_tickers(backtester_ready_dir)
    registry_tickers = scan_registry_tickers(secondary_output_dir)

    strategy_repo = load_strategy_repo(strategy_repo_json)
    family_gaps = family_gap_ranking(strategy_repo)
    top_gaps = family_gaps[:10]

    current_ready_cohorts = build_cohort_plan(
        tickers=backtester_ready,
        cohort_count=max(1, concurrency["lean_parallel_backtests"]),
        label_prefix="R",
    )
    full_target_placeholder = [f"TICKER_{index:03d}" for index in range(1, target_ticker_count + 1)]
    full_target_cohorts = build_cohort_plan(
        tickers=full_target_placeholder,
        cohort_count=max(1, concurrency["lean_parallel_backtests"] * 3),
        label_prefix="U",
    )

    immediate_plan = {
        "control_plane_agents": [
            {
                "agent": "Inventory Steward",
                "ownership": "Refresh strategy repo, maintain cohort lists, and track family coverage gaps.",
            },
            {
                "agent": "Promotion Steward",
                "ownership": "Serialize shared-account validation and GitHub live-manifest promotion.",
            },
        ],
        "discovery_agents": [
            {
                "agent": "Bear Directional",
                "strategy_set": "down_choppy_only",
                "family_focus": ["Single-leg long put", "Debit put spread"],
                "parallel_workers": 1,
            },
            {
                "agent": "Bear Premium",
                "strategy_set": "down_choppy_only",
                "family_focus": ["Credit call spread", "Iron condor", "Iron butterfly"],
                "parallel_workers": 1,
            },
            {
                "agent": "Bear Convexity",
                "strategy_set": "down_choppy_only",
                "family_focus": ["Put backspread", "Long straddle", "Long strangle"],
                "parallel_workers": 1,
            },
            {
                "agent": "Butterfly Lab",
                "strategy_set": "down_choppy_only",
                "family_focus": ["Put butterfly", "Broken-wing put butterfly"],
                "parallel_workers": 1,
            },
        ][: concurrency["lean_parallel_backtests"]],
        "deep_dive_agents": [
            {
                "agent": "Down/Choppy Exhaustive",
                "strategy_set": "down_choppy_exhaustive",
                "parallel_workers": 1,
                "use_for": "Top decile discovery survivors only.",
            },
            {
                "agent": "Balanced Expansion",
                "strategy_set": "family_expansion",
                "parallel_workers": 1,
                "use_for": "Balanced benchmark names and cross-regime validation.",
            },
        ][: concurrency["heavy_parallel_backtests"]],
        "validation_agents": [
            {
                "agent": "Shared-Account Validator",
                "strategy_set": "promotion_review",
                "parallel_workers": concurrency["validation_parallel_backtests"],
                "use_for": "Portfolio-level retest before GitHub promotion.",
            }
        ],
    }

    phases = [
        {
            "phase": "Phase 0 - Inventory Refresh",
            "goal": "Refresh strategy repo against the broader ticker lake before launching new waves.",
            "max_parallel_backtests": 0,
            "notes": [
                "Rebuild strategy coverage after the latest 59+ bundle universe is staged.",
                "Separate currently backtester-ready tickers from full staged-but-not-ready tickers.",
            ],
        },
        {
            "phase": "Phase 1 - Down/Choppy Discovery",
            "goal": "Run fast, low-promotion-risk discovery across the currently backtester-ready universe.",
            "max_parallel_backtests": concurrency["lean_parallel_backtests"],
            "strategy_set": "down_choppy_only",
            "selection_profile": "down_choppy_focus",
            "promotion_mode": "none",
            "cohorts": current_ready_cohorts,
        },
        {
            "phase": "Phase 2 - Exhaustive Follow-Up",
            "goal": "Retest only shortlisted tickers/families with the wider down/choppy surface.",
            "max_parallel_backtests": concurrency["heavy_parallel_backtests"],
            "strategy_set": "down_choppy_exhaustive",
            "selection_profile": "down_choppy_focus",
            "promotion_mode": "none",
            "notes": [
                "Only pass survivors from Phase 1 with good friction profile and low cheap-premium dependence.",
                "Keep shard size smaller than discovery to protect RAM.",
            ],
        },
        {
            "phase": "Phase 3 - Balanced Cross-Regime Benchmark",
            "goal": "Run family_expansion on core symbols and any candidates that look robust beyond down/choppy.",
            "max_parallel_backtests": concurrency["heavy_parallel_backtests"],
            "strategy_set": "family_expansion",
            "selection_profile": "balanced",
            "promotion_mode": "none",
        },
        {
            "phase": "Phase 4 - Shared-Account Validation",
            "goal": "Retest winners in portfolio context and reject standalone-only false positives.",
            "max_parallel_backtests": concurrency["validation_parallel_backtests"],
            "strategy_set": "shared_account_validation",
            "selection_profile": "portfolio_first",
            "promotion_mode": "merge_only",
        },
        {
            "phase": "Phase 5 - Promotion",
            "goal": "Serialize GitHub manifest updates so the paper runner never races on live state.",
            "max_parallel_backtests": 0,
            "notes": [
                "Exactly one promotion steward.",
                "No concurrent manifest writers.",
            ],
        },
    ]

    return {
        "generated_at": datetime.now().isoformat(),
        "machine_profile": {
            "logical_cpus": logical_cpus,
            "memory": memory,
            "concurrency": concurrency,
        },
        "data_universe": {
            "primary_output_dir": str(primary_output_dir),
            "secondary_output_dir": str(secondary_output_dir),
            "backtester_ready_dir": str(backtester_ready_dir),
            "primary_bundle_count": len(primary_bundles),
            "secondary_bundle_count": len(secondary_bundles),
            "staged_union_bundle_count": len(staged_union),
            "backtester_ready_count": len(backtester_ready),
            "backtester_ready_tickers": backtester_ready,
            "registry_symbol_count": len(registry_tickers),
            "registry_symbol_sample": registry_tickers[:25],
            "full_target_ticker_count": int(target_ticker_count),
        },
        "strategy_inventory": {
            "cataloged_base_strategy_count": int(strategy_repo.get("base_strategy_count", 0)),
            "ready_ticker_count_in_repo_snapshot": int(strategy_repo.get("ready_ticker_count", 0)),
            "researched_ticker_count_in_repo_snapshot": int(strategy_repo.get("researched_ticker_count", 0)),
            "research_summary_count_in_repo_snapshot": int(strategy_repo.get("research_summary_count", 0)),
            "top_family_gaps": top_gaps,
            "down_choppy_priority_families": DOWN_CHOPPY_PRIORITY_FAMILIES,
            "balanced_expansion_priority_families": BALANCED_EXPANSION_PRIORITY_FAMILIES,
        },
        "phases": phases,
        "agent_layout": immediate_plan,
        "full_target_sharding": {
            "cohort_count": len(full_target_cohorts),
            "cohorts": full_target_cohorts,
            "waves": math.ceil(len(full_target_cohorts) / max(1, concurrency["lean_parallel_backtests"])),
            "notes": [
                "Today we can shard cleanly by ticker cohort and strategy set.",
                "If we later add family include/exclude flags, we should shard by family lane as well.",
                "For the full 159-ticker universe, queue all cohorts but keep only the recommended concurrency active at once.",
            ],
        },
    }


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    machine = payload["machine_profile"]
    universe = payload["data_universe"]
    inventory = payload["strategy_inventory"]
    lines: list[str] = []
    lines.append("# Agent Sharding Plan")
    lines.append("")
    lines.append("## Machine Profile")
    lines.append("")
    lines.append(f"- Logical CPUs: {machine['logical_cpus']}")
    lines.append(f"- Total RAM: {machine['memory']['total_gb']:.2f} GB")
    lines.append(f"- Free RAM at plan time: {machine['memory']['free_gb']:.2f} GB")
    lines.append(f"- Lean parallel backtests: {machine['concurrency']['lean_parallel_backtests']}")
    lines.append(f"- Heavy parallel backtests: {machine['concurrency']['heavy_parallel_backtests']}")
    lines.append(f"- Validation lane concurrency: {machine['concurrency']['validation_parallel_backtests']}")
    lines.append(f"- Recommended total Codex agents: {machine['concurrency']['recommended_total_agents']}")
    lines.append("")
    lines.append("## Data Universe")
    lines.append("")
    lines.append(f"- Staged bundle universe: {universe['staged_union_bundle_count']} tickers")
    lines.append(f"- Backtester-ready universe: {universe['backtester_ready_count']} tickers")
    lines.append(f"- Registry-symbol universe: {universe['registry_symbol_count']} tickers")
    lines.append(f"- Full target universe: {universe['full_target_ticker_count']} tickers")
    lines.append("")
    lines.append("## Strategy Inventory")
    lines.append("")
    lines.append(f"- Cataloged base strategies: {inventory['cataloged_base_strategy_count']}")
    lines.append(f"- Ready ticker count in repo snapshot: {inventory['ready_ticker_count_in_repo_snapshot']}")
    lines.append(f"- Researched ticker count in repo snapshot: {inventory['researched_ticker_count_in_repo_snapshot']}")
    lines.append("")
    lines.append("### Highest-Value Family Gaps")
    lines.append("")
    for row in inventory["top_family_gaps"][:10]:
        lines.append(
            f"- `{row['family']}`: {row['base_strategy_count']} base strategies, "
            f"{row['selected_base_strategy_count']} ever selected, {row['promoted_base_strategy_count']} ever promoted"
        )
    lines.append("")
    lines.append("## Immediate Agent Layout")
    lines.append("")
    for row in payload["agent_layout"]["control_plane_agents"]:
        lines.append(f"- `{row['agent']}`: {row['ownership']}")
    for row in payload["agent_layout"]["discovery_agents"]:
        lines.append(
            f"- `{row['agent']}`: `{row['strategy_set']}` on {', '.join(row['family_focus'])}"
        )
    for row in payload["agent_layout"]["deep_dive_agents"]:
        lines.append(f"- `{row['agent']}`: `{row['strategy_set']}` ({row['use_for']})")
    for row in payload["agent_layout"]["validation_agents"]:
        lines.append(f"- `{row['agent']}`: {row['use_for']}")
    lines.append("")
    lines.append("## Phased Plan")
    lines.append("")
    for phase in payload["phases"]:
        lines.append(f"### {phase['phase']}")
        lines.append("")
        lines.append(f"- Goal: {phase['goal']}")
        lines.append(f"- Max parallel backtests: {phase['max_parallel_backtests']}")
        if "strategy_set" in phase:
            lines.append(f"- Strategy set: `{phase['strategy_set']}`")
        if "selection_profile" in phase:
            lines.append(f"- Selection profile: `{phase['selection_profile']}`")
        if "promotion_mode" in phase:
            lines.append(f"- Promotion mode: `{phase['promotion_mode']}`")
        for note in phase.get("notes", []):
            lines.append(f"- {note}")
        if "cohorts" in phase:
            lines.append("- Cohorts:")
            for cohort in phase["cohorts"]:
                lines.append(
                    f"  - `{cohort['cohort_id']}`: {cohort['ticker_count']} tickers"
                )
        lines.append("")
    lines.append("## Full 159-Ticker Queue Shape")
    lines.append("")
    lines.append(
        f"- Build {payload['full_target_sharding']['cohort_count']} queued cohorts and run {machine['concurrency']['lean_parallel_backtests']} at a time."
    )
    lines.append(f"- Total waves: {payload['full_target_sharding']['waves']}")
    for note in payload["full_target_sharding"]["notes"]:
        lines.append(f"- {note}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = build_parser().parse_args()
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    payload = build_plan(
        primary_output_dir=Path(args.primary_output_dir).resolve(),
        secondary_output_dir=Path(args.secondary_output_dir).resolve(),
        backtester_ready_dir=Path(args.backtester_ready_dir).resolve(),
        strategy_repo_json=Path(args.strategy_repo_json).resolve(),
        target_ticker_count=args.target_ticker_count,
    )
    json_path = output_dir / "agent_sharding_plan.json"
    md_path = output_dir / "agent_sharding_plan.md"
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    write_markdown(md_path, payload)
    print(json.dumps({"json_path": str(json_path), "md_path": str(md_path)}, indent=2))


if __name__ == "__main__":
    main()
