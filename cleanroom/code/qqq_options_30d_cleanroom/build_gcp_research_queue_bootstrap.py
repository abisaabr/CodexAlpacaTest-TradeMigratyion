from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[2]
DEFAULT_REPORT_DIR = REPO_ROOT / "docs" / "gcp_foundation"
DEFAULT_STRATEGY_REGISTRY_JSON = DEFAULT_REPORT_DIR / "gcp_strategy_registry_bootstrap.json"
DEFAULT_GCS_PREFIX = "gs://codexalpaca-control-us/research_queue/bootstrap"
SINGLE_LEG_FAMILIES = {"single-leg long call", "single-leg long put"}

DEFINED_RISK_TEMPLATES = [
    "debit_call_vertical",
    "debit_put_vertical",
    "broken_wing_call_butterfly",
    "broken_wing_put_butterfly",
    "iron_butterfly",
    "premium_defense_spread",
]
DEFINED_RISK_TIMING_PROFILES = ["fast", "base", "slow", "patient"]
DEFINED_RISK_DTE_MODES = ["same_day", "next_expiry"]
SINGLE_LEG_REPAIR_GRID = {
    "profit_target_multiple": [0.35, 0.45, 0.55],
    "stop_loss_multiple": [0.18, 0.24, 0.30],
    "hard_exit_minute": [210, 300, 360],
    "liquidity_gate": ["baseline", "tight"],
}
LOSER_DIAGNOSTIC_GRID = {
    "entry_delay_minutes": [5, 15, 30],
    "stop_tightening": ["none", "moderate", "strict"],
    "avoid_after_loser_similarity": [True, False],
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build a governed research queue from the strategy registry.")
    parser.add_argument("--strategy-registry-json", default=str(DEFAULT_STRATEGY_REGISTRY_JSON))
    parser.add_argument("--quality-scorecard-json", default=None)
    parser.add_argument("--report-dir", default=str(DEFAULT_REPORT_DIR))
    parser.add_argument("--gcs-prefix", default=DEFAULT_GCS_PREFIX)
    return parser


def _load_json(path: Path | None) -> dict[str, Any]:
    if path is None or not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def _grid_size(grid: dict[str, list[Any]]) -> int:
    size = 1
    for values in grid.values():
        size *= len(values)
    return size


def _registry_symbols(registry: list[dict[str, Any]]) -> list[str]:
    symbols = {str(row.get("underlying_symbol")) for row in registry if row.get("underlying_symbol")}
    return sorted(symbols)


def _scorecard_context(scorecard: dict[str, Any], registry: list[dict[str, Any]]) -> dict[str, Any]:
    fallback_symbols = _registry_symbols(registry)
    preferred = [str(item) for item in scorecard.get("recommended_first_session_bias", []) if item]
    avoid = [str(item) for item in scorecard.get("avoid_or_shadow", []) if item]
    ranked = scorecard.get("ranked_symbols") if isinstance(scorecard.get("ranked_symbols"), list) else []
    stances = {
        str(item.get("symbol")): str(item.get("stance"))
        for item in ranked
        if isinstance(item, dict) and item.get("symbol") and item.get("stance")
    }
    if not preferred:
        counts = Counter(str(row.get("underlying_symbol")) for row in registry if row.get("underlying_symbol"))
        preferred = [symbol for symbol, _count in counts.most_common(5)]
    universe = [str(item) for item in scorecard.get("universe", []) if item] or fallback_symbols
    return {
        "target_trade_date": scorecard.get("target_trade_date"),
        "scorecard_status": scorecard.get("status") or "missing_scorecard",
        "preferred_symbols": preferred,
        "avoid_or_shadow_symbols": avoid,
        "universe": universe,
        "stances": stances,
    }


def _single_leg_rows(registry: list[dict[str, Any]], symbols: set[str] | None = None) -> list[dict[str, Any]]:
    rows = []
    for row in registry:
        symbol = str(row.get("underlying_symbol"))
        family = str(row.get("family") or "").lower()
        if family in SINGLE_LEG_FAMILIES and (symbols is None or symbol in symbols):
            rows.append(row)
    return rows


def _queue_item(
    *,
    queue_id: str,
    priority: int,
    mission: str,
    symbols: list[str],
    estimated_variant_count: int,
    sweep_design: dict[str, Any],
    promotion_gate: list[str],
) -> dict[str, Any]:
    return {
        "queue_id": queue_id,
        "priority": priority,
        "mission": mission,
        "symbols": symbols,
        "estimated_variant_count": estimated_variant_count,
        "sweep_design": sweep_design,
        "required_outputs": [
            "research_run_manifest",
            "normalized_backtest_results",
            "train_test_or_walk_forward_summary",
            "after_cost_expectancy_table",
            "drawdown_and_tail_loss_report",
            "loser_cluster_comparison",
            "candidate_hold_kill_quarantine_recommendation",
        ],
        "promotion_gate": promotion_gate,
        "live_manifest_effect": "none",
        "risk_policy_effect": "none",
        "execution_effect": "none_research_only",
    }


def build_payload(
    *,
    strategy_registry_json: Path,
    quality_scorecard_json: Path | None,
    report_dir: Path,
    gcs_prefix: str,
) -> dict[str, Any]:
    registry_payload = _load_json(strategy_registry_json)
    scorecard_payload = _load_json(quality_scorecard_json)
    registry = registry_payload.get("registry") if isinstance(registry_payload.get("registry"), list) else []
    scorecard = _scorecard_context(scorecard_payload, registry)
    preferred_symbols = scorecard["preferred_symbols"]
    avoid_symbols = scorecard["avoid_or_shadow_symbols"]
    preferred_symbol_set = set(preferred_symbols)
    avoid_symbol_set = set(avoid_symbols)
    single_leg_preferred_rows = _single_leg_rows(registry, preferred_symbol_set)
    single_leg_avoid_rows = _single_leg_rows(registry, avoid_symbol_set)
    all_symbols = scorecard["universe"] or _registry_symbols(registry)
    queue: list[dict[str, Any]] = []

    defined_risk_variants = (
        len(preferred_symbols)
        * len(DEFINED_RISK_TEMPLATES)
        * len(DEFINED_RISK_TIMING_PROFILES)
        * len(DEFINED_RISK_DTE_MODES)
    )
    queue.append(
        _queue_item(
            queue_id="RQ-001-defined-risk-family-expansion",
            priority=1,
            mission="Expand under-covered defined-risk and choppy/premium structures before adding more directional single-leg variants.",
            symbols=preferred_symbols,
            estimated_variant_count=defined_risk_variants,
            sweep_design={
                "family_templates": DEFINED_RISK_TEMPLATES,
                "timing_profiles": DEFINED_RISK_TIMING_PROFILES,
                "dte_modes": DEFINED_RISK_DTE_MODES,
                "admission_note": "Research-only candidates. They require promotion review before runner eligibility.",
            },
            promotion_gate=[
                "positive after-cost expectancy in out-of-sample or walk-forward segment",
                "max drawdown and tail-loss behavior better than comparable single-leg baseline",
                "no single symbol contributes more than 40% of total edge",
                "slippage stress remains profitable at conservative fill assumptions",
            ],
        )
    )

    single_leg_repair_variants = len(single_leg_preferred_rows) * _grid_size(SINGLE_LEG_REPAIR_GRID)
    queue.append(
        _queue_item(
            queue_id="RQ-002-single-leg-repair-and-loss-filter",
            priority=2,
            mission="Repair existing single-leg families with stricter exits, liquidity gates, and loser-similarity filters.",
            symbols=preferred_symbols,
            estimated_variant_count=single_leg_repair_variants,
            sweep_design={
                "source_strategy_count": len(single_leg_preferred_rows),
                "parameter_grid": SINGLE_LEG_REPAIR_GRID,
                "baseline_family_filter": sorted(SINGLE_LEG_FAMILIES),
                "admission_note": "A repair candidate must beat its original manifest strategy after costs and loser penalties.",
            },
            promotion_gate=[
                "beats current same-symbol same-family baseline after fees and slippage",
                "reduces stop-loss cluster frequency",
                "passes loser-similarity filter against April 23 loss clusters",
                "does not rely on widening risk or increasing contracts",
            ],
        )
    )

    loser_diagnostic_variants = len(single_leg_avoid_rows) * _grid_size(LOSER_DIAGNOSTIC_GRID)
    queue.append(
        _queue_item(
            queue_id="RQ-003-loser-cluster-shadow-diagnostics",
            priority=3,
            mission="Use avoid/shadow symbols to learn what failed without granting them execution eligibility.",
            symbols=avoid_symbols,
            estimated_variant_count=loser_diagnostic_variants,
            sweep_design={
                "source_strategy_count": len(single_leg_avoid_rows),
                "parameter_grid": LOSER_DIAGNOSTIC_GRID,
                "admission_note": "Diagnostics can produce quarantine or hold decisions, not immediate promotion.",
            },
            promotion_gate=[
                "identifies repeatable loser features",
                "produces explicit quarantine or repair recommendations",
                "does not promote an avoid/shadow symbol without separate control-plane review",
            ],
        )
    )

    regime_variants = len(all_symbols) * 6
    queue.append(
        _queue_item(
            queue_id="RQ-004-regime-and-liquidity-feature-grid",
            priority=4,
            mission="Build symbol/regime/liquidity features that explain when each strategy family should be suppressed.",
            symbols=all_symbols,
            estimated_variant_count=regime_variants,
            sweep_design={
                "feature_groups": [
                    "opening_gap_and_range",
                    "realized_volatility",
                    "trend_persistence",
                    "spread_and_quote_quality",
                    "relative_volume",
                    "paper_fill_slippage",
                ],
                "admission_note": "Feature outputs can improve scorecards and promotion review, not live rules without review.",
            },
            promotion_gate=[
                "feature has stable explanatory value across multiple dates",
                "feature improves loser avoidance without removing most winners",
                "feature can be computed before trade admission",
            ],
        )
    )

    issues: list[dict[str, str]] = []
    if not registry:
        issues.append({"severity": "error", "code": "missing_strategy_registry", "message": "Strategy registry is empty."})
    if not scorecard_payload:
        issues.append({"severity": "warning", "code": "missing_quality_scorecard", "message": "No quality scorecard supplied."})
    single_leg_share = float(registry_payload.get("single_leg_strategy_share") or 0.0)
    if single_leg_share > 0.70:
        issues.append(
            {
                "severity": "warning",
                "code": "single_leg_concentration",
                "message": f"Current manifest is {single_leg_share:.1%} single-leg directional strategies.",
            }
        )

    status = "blocked" if any(item["severity"] == "error" for item in issues) else "ready_for_bounded_research_sweep"
    if status != "blocked" and any(item["severity"] == "warning" for item in issues):
        status = "ready_with_research_warnings"

    return {
        "generated_at": datetime.now().astimezone().isoformat(),
        "status": status,
        "strategy_registry_json": str(strategy_registry_json),
        "quality_scorecard_json": str(quality_scorecard_json) if quality_scorecard_json else None,
        "report_dir": str(report_dir),
        "gcs_prefix": gcs_prefix,
        "strategy_count": len(registry),
        "target_trade_date": scorecard["target_trade_date"],
        "scorecard_status": scorecard["scorecard_status"],
        "preferred_symbols": preferred_symbols,
        "avoid_or_shadow_symbols": avoid_symbols,
        "single_leg_strategy_share": round(single_leg_share, 4),
        "total_estimated_variant_count": sum(item["estimated_variant_count"] for item in queue),
        "queue": queue,
        "issues": issues,
        "guardrails": [
            "research_queue_is_advisory_only",
            "do_not_mutate_live_manifest",
            "do_not_change_risk_policy",
            "do_not_start_broker_facing_session",
            "require_promotion_packet_before_runner_eligibility",
        ],
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "# GCP Research Queue Bootstrap",
        "",
        "## Snapshot",
        "",
        f"- Generated at: `{payload['generated_at']}`",
        f"- Status: `{payload['status']}`",
        f"- Strategy count: `{payload['strategy_count']}`",
        f"- Target trade date: `{payload['target_trade_date']}`",
        f"- Scorecard status: `{payload['scorecard_status']}`",
        f"- Single-leg strategy share: `{payload['single_leg_strategy_share']:.1%}`",
        f"- Estimated research variants: `{payload['total_estimated_variant_count']}`",
        f"- GCS prefix: `{payload['gcs_prefix']}`",
        "",
        "## Preferred Research Symbols",
        "",
    ]
    for symbol in payload["preferred_symbols"]:
        lines.append(f"- `{symbol}`")
    lines.extend(["", "## Avoid Or Shadow Symbols", ""])
    for symbol in payload["avoid_or_shadow_symbols"]:
        lines.append(f"- `{symbol}`")
    lines.extend(["", "## Queue", ""])
    for item in payload["queue"]:
        lines.extend(
            [
                f"### {item['queue_id']}",
                "",
                f"- Priority: `{item['priority']}`",
                f"- Estimated variants: `{item['estimated_variant_count']}`",
                f"- Mission: {item['mission']}",
                f"- Symbols: `{', '.join(item['symbols'])}`",
                f"- Live manifest effect: `{item['live_manifest_effect']}`",
                "",
            ]
        )
    if payload["issues"]:
        lines.extend(["## Issues", ""])
        for issue in payload["issues"]:
            lines.append(f"- `{issue['severity']}` `{issue['code']}`: {issue['message']}")
        lines.append("")
    lines.extend(["## Guardrails", ""])
    for guardrail in payload["guardrails"]:
        lines.append(f"- `{guardrail}`")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = build_parser().parse_args()
    report_dir = Path(args.report_dir)
    scorecard_json = Path(args.quality_scorecard_json) if args.quality_scorecard_json else None
    payload = build_payload(
        strategy_registry_json=Path(args.strategy_registry_json),
        quality_scorecard_json=scorecard_json,
        report_dir=report_dir,
        gcs_prefix=args.gcs_prefix,
    )
    write_json(report_dir / "gcp_research_queue_bootstrap.json", payload)
    write_markdown(report_dir / "gcp_research_queue_bootstrap.md", payload)
    write_markdown(report_dir / "gcp_research_queue_bootstrap_handoff.md", payload)
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
