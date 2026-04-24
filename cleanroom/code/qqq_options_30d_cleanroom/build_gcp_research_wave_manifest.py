from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime
from itertools import product
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[2]
DEFAULT_REPORT_DIR = REPO_ROOT / "docs" / "gcp_foundation"
DEFAULT_QUEUE_JSON = DEFAULT_REPORT_DIR / "gcp_research_queue_bootstrap.json"
DEFAULT_STRATEGY_REGISTRY_JSON = DEFAULT_REPORT_DIR / "gcp_strategy_registry_bootstrap.json"
DEFAULT_GCS_PREFIX = "gs://codexalpaca-control-us/research_waves/bootstrap"
SINGLE_LEG_FAMILIES = {"single-leg long call", "single-leg long put"}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Expand the governed research queue into a chunked wave manifest.")
    parser.add_argument("--research-queue-json", default=str(DEFAULT_QUEUE_JSON))
    parser.add_argument("--strategy-registry-json", default=str(DEFAULT_STRATEGY_REGISTRY_JSON))
    parser.add_argument("--report-dir", default=str(DEFAULT_REPORT_DIR))
    parser.add_argument("--gcs-prefix", default=DEFAULT_GCS_PREFIX)
    parser.add_argument("--chunk-size", type=int, default=100)
    parser.add_argument("--wave-id", default=None)
    return parser


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def _slug(value: Any) -> str:
    text = str(value).lower().strip()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    return text.strip("_") or "unknown"


def _queue_by_id(queue_payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    queue = queue_payload.get("queue") if isinstance(queue_payload.get("queue"), list) else []
    return {str(item.get("queue_id")): item for item in queue if isinstance(item, dict) and item.get("queue_id")}


def _single_leg_rows(registry_payload: dict[str, Any], symbols: set[str]) -> list[dict[str, Any]]:
    registry = registry_payload.get("registry") if isinstance(registry_payload.get("registry"), list) else []
    rows = []
    for row in registry:
        if not isinstance(row, dict):
            continue
        family = str(row.get("family") or "").lower()
        symbol = str(row.get("underlying_symbol") or "")
        if family in SINGLE_LEG_FAMILIES and symbol in symbols:
            rows.append(row)
    return rows


def _parameter_rows(grid: dict[str, list[Any]]) -> list[dict[str, Any]]:
    keys = list(grid)
    values = [grid[key] for key in keys]
    return [dict(zip(keys, combo, strict=True)) for combo in product(*values)]


def _variant(
    *,
    variant_id: str,
    queue_id: str,
    priority: int,
    symbol: str,
    variant_type: str,
    parameters: dict[str, Any],
    source_strategy_id: str | None = None,
) -> dict[str, Any]:
    return {
        "variant_id": variant_id,
        "queue_id": queue_id,
        "priority": priority,
        "symbol": symbol,
        "variant_type": variant_type,
        "parameters": parameters,
        "source_strategy_id": source_strategy_id,
        "state": "research_only",
        "live_manifest_effect": "none",
        "risk_policy_effect": "none",
        "execution_effect": "none",
    }


def _expand_defined_risk(item: dict[str, Any]) -> list[dict[str, Any]]:
    design = item.get("sweep_design") if isinstance(item.get("sweep_design"), dict) else {}
    symbols = [str(symbol) for symbol in item.get("symbols", [])]
    templates = [str(value) for value in design.get("family_templates", [])]
    timings = [str(value) for value in design.get("timing_profiles", [])]
    dte_modes = [str(value) for value in design.get("dte_modes", [])]
    rows: list[dict[str, Any]] = []
    for symbol, template, timing, dte_mode in product(symbols, templates, timings, dte_modes):
        variant_id = f"rq001__{_slug(symbol)}__{_slug(template)}__{_slug(timing)}__{_slug(dte_mode)}"
        rows.append(
            _variant(
                variant_id=variant_id,
                queue_id=str(item["queue_id"]),
                priority=int(item["priority"]),
                symbol=symbol,
                variant_type="defined_risk_family_expansion",
                parameters={"family_template": template, "timing_profile": timing, "dte_mode": dte_mode},
            )
        )
    return rows


def _expand_single_leg_repair(item: dict[str, Any], registry_payload: dict[str, Any]) -> list[dict[str, Any]]:
    design = item.get("sweep_design") if isinstance(item.get("sweep_design"), dict) else {}
    grid = design.get("parameter_grid") if isinstance(design.get("parameter_grid"), dict) else {}
    symbols = {str(symbol) for symbol in item.get("symbols", [])}
    source_rows = _single_leg_rows(registry_payload, symbols)
    parameter_rows = _parameter_rows(grid)
    rows: list[dict[str, Any]] = []
    for source, parameters in product(source_rows, parameter_rows):
        source_id = str(source.get("strategy_id"))
        symbol = str(source.get("underlying_symbol"))
        parameter_slug = "__".join(f"{_slug(key)}_{_slug(value)}" for key, value in parameters.items())
        variant_id = f"rq002__{_slug(source_id)}__{parameter_slug}"
        rows.append(
            _variant(
                variant_id=variant_id,
                queue_id=str(item["queue_id"]),
                priority=int(item["priority"]),
                symbol=symbol,
                variant_type="single_leg_repair",
                parameters=parameters,
                source_strategy_id=source_id,
            )
        )
    return rows


def _expand_loser_diagnostics(item: dict[str, Any], registry_payload: dict[str, Any]) -> list[dict[str, Any]]:
    design = item.get("sweep_design") if isinstance(item.get("sweep_design"), dict) else {}
    grid = design.get("parameter_grid") if isinstance(design.get("parameter_grid"), dict) else {}
    symbols = {str(symbol) for symbol in item.get("symbols", [])}
    source_rows = _single_leg_rows(registry_payload, symbols)
    parameter_rows = _parameter_rows(grid)
    rows: list[dict[str, Any]] = []
    for source, parameters in product(source_rows, parameter_rows):
        source_id = str(source.get("strategy_id"))
        symbol = str(source.get("underlying_symbol"))
        parameter_slug = "__".join(f"{_slug(key)}_{_slug(value)}" for key, value in parameters.items())
        variant_id = f"rq003__{_slug(source_id)}__{parameter_slug}"
        rows.append(
            _variant(
                variant_id=variant_id,
                queue_id=str(item["queue_id"]),
                priority=int(item["priority"]),
                symbol=symbol,
                variant_type="loser_cluster_shadow_diagnostic",
                parameters=parameters,
                source_strategy_id=source_id,
            )
        )
    return rows


def _expand_regime_features(item: dict[str, Any]) -> list[dict[str, Any]]:
    design = item.get("sweep_design") if isinstance(item.get("sweep_design"), dict) else {}
    symbols = [str(symbol) for symbol in item.get("symbols", [])]
    feature_groups = [str(value) for value in design.get("feature_groups", [])]
    rows: list[dict[str, Any]] = []
    for symbol, feature_group in product(symbols, feature_groups):
        variant_id = f"rq004__{_slug(symbol)}__{_slug(feature_group)}"
        rows.append(
            _variant(
                variant_id=variant_id,
                queue_id=str(item["queue_id"]),
                priority=int(item["priority"]),
                symbol=symbol,
                variant_type="regime_liquidity_feature_grid",
                parameters={"feature_group": feature_group},
            )
        )
    return rows


def _chunk_variants(variants: list[dict[str, Any]], chunk_size: int) -> list[dict[str, Any]]:
    chunks = []
    for index in range(0, len(variants), chunk_size):
        chunk_variants = variants[index : index + chunk_size]
        chunk_id = f"chunk_{len(chunks) + 1:04d}"
        chunks.append(
            {
                "chunk_id": chunk_id,
                "start_index": index,
                "end_index": index + len(chunk_variants) - 1,
                "variant_count": len(chunk_variants),
                "priority_counts": dict(sorted(_counts(row["priority"] for row in chunk_variants).items())),
                "queue_counts": dict(sorted(_counts(row["queue_id"] for row in chunk_variants).items())),
                "symbols": sorted({str(row["symbol"]) for row in chunk_variants}),
            }
        )
    return chunks


def _counts(values: Any) -> dict[Any, int]:
    counts: dict[Any, int] = {}
    for value in values:
        counts[value] = counts.get(value, 0) + 1
    return counts


def build_payload(
    *,
    research_queue_json: Path,
    strategy_registry_json: Path,
    report_dir: Path,
    gcs_prefix: str,
    chunk_size: int,
    wave_id: str | None = None,
) -> dict[str, Any]:
    queue_payload = _load_json(research_queue_json)
    registry_payload = _load_json(strategy_registry_json)
    queue = _queue_by_id(queue_payload)
    generated_at = datetime.now().astimezone()
    resolved_wave_id = wave_id or f"research_wave_{generated_at.strftime('%Y%m%d_%H%M%S')}"
    variants: list[dict[str, Any]] = []
    if "RQ-001-defined-risk-family-expansion" in queue:
        variants.extend(_expand_defined_risk(queue["RQ-001-defined-risk-family-expansion"]))
    if "RQ-002-single-leg-repair-and-loss-filter" in queue:
        variants.extend(_expand_single_leg_repair(queue["RQ-002-single-leg-repair-and-loss-filter"], registry_payload))
    if "RQ-003-loser-cluster-shadow-diagnostics" in queue:
        variants.extend(_expand_loser_diagnostics(queue["RQ-003-loser-cluster-shadow-diagnostics"], registry_payload))
    if "RQ-004-regime-and-liquidity-feature-grid" in queue:
        variants.extend(_expand_regime_features(queue["RQ-004-regime-and-liquidity-feature-grid"]))
    variants = sorted(variants, key=lambda row: (row["priority"], row["queue_id"], row["symbol"], row["variant_id"]))
    duplicate_ids = sorted(_id for _id, count in _counts(row["variant_id"] for row in variants).items() if count > 1)
    chunks = _chunk_variants(variants, chunk_size)
    queue_estimated_count = int(queue_payload.get("total_estimated_variant_count") or 0)
    issues: list[dict[str, str]] = []
    if not queue:
        issues.append({"severity": "error", "code": "missing_research_queue", "message": "Research queue is empty."})
    if not registry_payload.get("registry"):
        issues.append({"severity": "error", "code": "missing_strategy_registry", "message": "Strategy registry is empty."})
    if duplicate_ids:
        issues.append(
            {
                "severity": "error",
                "code": "duplicate_variant_id",
                "message": f"Duplicate variant ids detected: {', '.join(duplicate_ids[:5])}",
            }
        )
    if queue_estimated_count and queue_estimated_count != len(variants):
        issues.append(
            {
                "severity": "error",
                "code": "queue_count_mismatch",
                "message": f"Queue estimated {queue_estimated_count} variants but wave expanded {len(variants)}.",
            }
        )
    status = "blocked" if any(item["severity"] == "error" for item in issues) else "ready_for_research_only_wave"
    return {
        "generated_at": generated_at.isoformat(),
        "status": status,
        "wave_id": resolved_wave_id,
        "research_queue_json": str(research_queue_json),
        "strategy_registry_json": str(strategy_registry_json),
        "report_dir": str(report_dir),
        "gcs_prefix": gcs_prefix,
        "chunk_size": chunk_size,
        "variant_count": len(variants),
        "chunk_count": len(chunks),
        "priority_counts": dict(sorted(_counts(row["priority"] for row in variants).items())),
        "queue_counts": dict(sorted(_counts(row["queue_id"] for row in variants).items())),
        "symbol_counts": dict(sorted(_counts(row["symbol"] for row in variants).items())),
        "chunks": chunks,
        "variants": variants,
        "issues": issues,
        "execution_contract": {
            "plane": "research",
            "broker_facing": False,
            "live_manifest_effect": "none",
            "risk_policy_effect": "none",
            "required_result_artifacts": [
                "research_run_manifest",
                "normalized_backtest_results",
                "train_test_or_walk_forward_summary",
                "after_cost_expectancy_table",
                "drawdown_and_tail_loss_report",
                "loser_cluster_comparison",
                "candidate_hold_kill_quarantine_recommendation",
            ],
        },
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def write_jsonl(path: Path, variants: list[dict[str, Any]]) -> dict[str, Any]:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [json.dumps(row, sort_keys=True) for row in variants]
    text = "\n".join(lines) + "\n"
    path.write_text(text, encoding="utf-8")
    return {
        "local_path": str(path),
        "line_count": len(variants),
        "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "gcs_path": "gs://codexalpaca-control-us/research_waves/bootstrap/gcp_research_wave_variants.jsonl",
    }


def compact_payload(payload: dict[str, Any], variant_artifact: dict[str, Any]) -> dict[str, Any]:
    compact = {key: value for key, value in payload.items() if key != "variants"}
    compact["variant_artifact"] = variant_artifact
    return compact


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "# GCP Research Wave Manifest",
        "",
        "## Snapshot",
        "",
        f"- Generated at: `{payload['generated_at']}`",
        f"- Status: `{payload['status']}`",
        f"- Wave id: `{payload['wave_id']}`",
        f"- Variant count: `{payload['variant_count']}`",
        f"- Chunk count: `{payload['chunk_count']}`",
        f"- Chunk size: `{payload['chunk_size']}`",
        f"- GCS prefix: `{payload['gcs_prefix']}`",
        "",
        "## Variant Artifact",
        "",
        f"- Local path: `{payload.get('variant_artifact', {}).get('local_path')}`",
        f"- GCS path: `{payload.get('variant_artifact', {}).get('gcs_path')}`",
        f"- Line count: `{payload.get('variant_artifact', {}).get('line_count')}`",
        f"- SHA256: `{payload.get('variant_artifact', {}).get('sha256')}`",
        "",
        "## Queue Counts",
        "",
    ]
    for queue_id, count in payload["queue_counts"].items():
        lines.append(f"- `{queue_id}`: `{count}`")
    lines.extend(["", "## Top Symbol Counts", ""])
    for symbol, count in sorted(payload["symbol_counts"].items(), key=lambda item: (-item[1], item[0]))[:12]:
        lines.append(f"- `{symbol}`: `{count}`")
    lines.extend(["", "## Execution Contract", ""])
    contract = payload["execution_contract"]
    lines.extend(
        [
            f"- Plane: `{contract['plane']}`",
            f"- Broker facing: `{contract['broker_facing']}`",
            f"- Live manifest effect: `{contract['live_manifest_effect']}`",
            f"- Risk policy effect: `{contract['risk_policy_effect']}`",
            "",
            "## Required Result Artifacts",
            "",
        ]
    )
    for artifact in contract["required_result_artifacts"]:
        lines.append(f"- `{artifact}`")
    if payload["issues"]:
        lines.extend(["", "## Issues", ""])
        for issue in payload["issues"]:
            lines.append(f"- `{issue['severity']}` `{issue['code']}`: {issue['message']}")
    lines.extend(["", "## Chunk Preview", ""])
    for chunk in payload["chunks"][:10]:
        lines.append(
            "- `{chunk_id}` variants `{variant_count}` priorities `{priority_counts}` queues `{queue_counts}`".format(
                chunk_id=chunk["chunk_id"],
                variant_count=chunk["variant_count"],
                priority_counts=chunk["priority_counts"],
                queue_counts=chunk["queue_counts"],
            )
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = build_parser().parse_args()
    report_dir = Path(args.report_dir)
    payload = build_payload(
        research_queue_json=Path(args.research_queue_json),
        strategy_registry_json=Path(args.strategy_registry_json),
        report_dir=report_dir,
        gcs_prefix=args.gcs_prefix,
        chunk_size=args.chunk_size,
        wave_id=args.wave_id,
    )
    variant_artifact = write_jsonl(report_dir / "gcp_research_wave_variants.jsonl", payload["variants"])
    compact = compact_payload(payload, variant_artifact)
    write_json(report_dir / "gcp_research_wave_manifest.json", compact)
    write_markdown(report_dir / "gcp_research_wave_manifest.md", compact)
    write_markdown(report_dir / "gcp_research_wave_manifest_handoff.md", compact)
    print(json.dumps(compact, indent=2))


if __name__ == "__main__":
    main()
