from __future__ import annotations

import argparse
import json
import re
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[2]
DEFAULT_REPORT_DIR = REPO_ROOT / "docs" / "gcp_foundation"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build a distilled research promotion board from promotion-review packets."
    )
    parser.add_argument("--packet", action="append", required=True, help="Local path or gs:// JSON packet.")
    parser.add_argument("--report-dir", default=str(DEFAULT_REPORT_DIR))
    parser.add_argument("--packet-prefix", default="gcp_research_current_promotion_board")
    parser.add_argument("--generated-at-utc")
    parser.add_argument("--gcloud-cmd", default="gcloud")
    return parser


def _now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _read_text(source: str, gcloud_cmd: str = "gcloud") -> str:
    if source.startswith("gs://"):
        result = subprocess.run(
            [gcloud_cmd, "storage", "cat", source],
            check=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        return result.stdout
    return Path(source).read_text(encoding="utf-8-sig")


def _as_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _as_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _infer_symbol(source: str, packet: dict[str, Any]) -> str | None:
    for key in ("review_candidates", "capital_plan", "data_repair_targets"):
        rows = packet.get(key) or []
        if rows and isinstance(rows[0], dict) and rows[0].get("symbol"):
            return str(rows[0]["symbol"]).upper()
    match = re.search(r"/data_shards/([^/]+)/", source)
    if match:
        return match.group(1).upper()
    match = re.search(r"_([A-Z]{1,6})/portfolio_report", str(packet.get("source_portfolio_report_json") or ""))
    if match:
        return match.group(1).upper()
    return None


def _infer_phase(source: str) -> str | None:
    match = re.search(r"portfolio_event_driven_data/([^/]+)/data_shards/", source)
    if match:
        return match.group(1)
    return None


def _candidate_summary(row: dict[str, Any]) -> dict[str, Any]:
    fields = [
        "candidate_variant_id",
        "symbol",
        "source_strategy_id",
        "directional_option_type",
        "min_net_pnl",
        "min_test_net_pnl",
        "min_fill_coverage",
        "max_fill_coverage",
        "min_option_trade_count",
        "worst_drawdown",
        "promotion_status",
        "promotion_blockers",
    ]
    return {key: row.get(key) for key in fields if key in row}


def summarize_packet(source: str, packet: dict[str, Any]) -> dict[str, Any]:
    gate = packet.get("gate_summary") or {}
    capital_plan = packet.get("capital_plan") or []
    repair_targets = packet.get("data_repair_targets") or []
    review_candidates = packet.get("review_candidates") or []
    best = capital_plan[0] if capital_plan else (repair_targets[0] if repair_targets else None)

    return {
        "source": source,
        "phase_id": _infer_phase(source),
        "symbol": _infer_symbol(source, packet),
        "decision": packet.get("decision"),
        "candidate_count": _as_int(gate.get("candidate_count")),
        "eligible_for_promotion_review_count": _as_int(
            gate.get("eligible_for_promotion_review_count")
        ),
        "blocker_counts": packet.get("blocker_counts") or {},
        "review_candidates": [_candidate_summary(row) for row in review_candidates],
        "best_research_candidate": _candidate_summary(best) if isinstance(best, dict) else None,
    }


def _dominant_blocker(rows: list[dict[str, Any]]) -> str | None:
    counts: Counter[str] = Counter()
    for row in rows:
        for blocker, count in (row.get("blocker_counts") or {}).items():
            counts[str(blocker)] += _as_int(count)
    return counts.most_common(1)[0][0] if counts else None


def build_payload(
    sources: list[str],
    generated_at_utc: str | None = None,
    gcloud_cmd: str = "gcloud",
) -> dict[str, Any]:
    summaries = [
        summarize_packet(source, json.loads(_read_text(source, gcloud_cmd=gcloud_cmd)))
        for source in sources
    ]
    review_candidates = [
        candidate
        for summary in summaries
        for candidate in (summary.get("review_candidates") or [])
    ]
    best_leads = [
        summary["best_research_candidate"]
        for summary in summaries
        if summary.get("best_research_candidate")
    ]
    best_leads.sort(
        key=lambda row: (
            _as_float(row.get("min_net_pnl")) is not None,
            _as_float(row.get("min_net_pnl")) or float("-inf"),
        ),
        reverse=True,
    )

    blocker_counts: Counter[str] = Counter()
    for summary in summaries:
        for blocker, count in (summary.get("blocker_counts") or {}).items():
            blocker_counts[str(blocker)] += _as_int(count)

    return {
        "packet": "gcp_research_promotion_board_from_packets",
        "generated_at_utc": generated_at_utc or _now_utc(),
        "broker_facing": False,
        "trading_effect": "none",
        "live_manifest_effect": "none",
        "risk_policy_effect": "none",
        "promotion_allowed_from_this_packet": False,
        "packet_count": len(summaries),
        "candidate_count": sum(_as_int(row.get("candidate_count")) for row in summaries),
        "eligible_for_promotion_review_count": sum(
            _as_int(row.get("eligible_for_promotion_review_count")) for row in summaries
        ),
        "new_governed_validation_candidates": len(review_candidates),
        "dominant_blocker": _dominant_blocker(summaries),
        "aggregate_blocker_counts": dict(blocker_counts),
        "best_research_only_leads": best_leads[:12],
        "review_candidates": review_candidates,
        "packet_summaries": summaries,
        "hard_rules": [
            "do_not_trade",
            "do_not_arm_window",
            "do_not_start_broker_facing_session",
            "do_not_modify_live_manifests",
            "do_not_change_risk_policy",
            "do_not_relax_0_90_fill_gate",
        ],
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _money(value: Any) -> str:
    numeric = _as_float(value)
    if numeric is None:
        return "n/a"
    return f"${numeric:.4f}".rstrip("0").rstrip(".")


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "# GCP Research Promotion Board From Packets",
        "",
        "## State",
        "",
        f"- Generated at UTC: `{payload['generated_at_utc']}`",
        f"- Packet count: `{payload['packet_count']}`",
        f"- Candidate count: `{payload['candidate_count']}`",
        f"- Eligible for promotion review: `{payload['eligible_for_promotion_review_count']}`",
        f"- New governed-validation candidates: `{payload['new_governed_validation_candidates']}`",
        f"- Dominant blocker: `{payload['dominant_blocker']}`",
        f"- Broker-facing: `{payload['broker_facing']}`",
        f"- Live manifest effect: `{payload['live_manifest_effect']}`",
        f"- Risk policy effect: `{payload['risk_policy_effect']}`",
        "",
        "## Best Research-Only Leads",
        "",
    ]
    for row in payload["best_research_only_leads"]:
        lines.append(
            "- "
            f"`{row.get('symbol')}` `{row.get('candidate_variant_id')}`: "
            f"min net `{_money(row.get('min_net_pnl'))}`, "
            f"min test `{_money(row.get('min_test_net_pnl'))}`, "
            f"fill `{row.get('min_fill_coverage')}`, "
            f"trades `{row.get('min_option_trade_count')}`, "
            f"blockers `{', '.join(row.get('promotion_blockers') or [])}`."
        )

    if payload["review_candidates"]:
        lines.extend(["", "## Review Candidates", ""])
        for row in payload["review_candidates"]:
            lines.append(f"- `{row.get('symbol')}` `{row.get('candidate_variant_id')}`")
    else:
        lines.extend(["", "## Review Candidates", "", "- None."])

    lines.extend(
        [
            "",
            "## Guardrails",
            "",
            "- This board is research-only and cannot promote by itself.",
            "- Do not trade, arm a window, start broker-facing execution, modify live manifests, change risk policy, or relax the `0.90` fill gate.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_handoff(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "# GCP Research Promotion Board From Packets Handoff",
        "",
        f"- Packet count: `{payload['packet_count']}`",
        f"- Candidate count: `{payload['candidate_count']}`",
        f"- Eligible for promotion review: `{payload['eligible_for_promotion_review_count']}`",
        f"- New governed-validation candidates: `{payload['new_governed_validation_candidates']}`",
        f"- Dominant blocker: `{payload['dominant_blocker']}`",
        "",
        "## Operator Rule",
        "",
        "- Use this packet to prioritize review and repair work only.",
        "- No broker-facing execution, live-manifest update, risk-policy change, or promotion is authorized from this packet alone.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = build_parser().parse_args()
    payload = build_payload(
        args.packet,
        generated_at_utc=args.generated_at_utc,
        gcloud_cmd=args.gcloud_cmd,
    )
    report_dir = Path(args.report_dir).resolve()
    write_json(report_dir / f"{args.packet_prefix}.json", payload)
    write_markdown(report_dir / f"{args.packet_prefix}.md", payload)
    write_handoff(report_dir / f"{args.packet_prefix}_handoff.md", payload)
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
