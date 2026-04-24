from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[2]
DEFAULT_REPORT_DIR = REPO_ROOT / "docs" / "gcp_foundation"
DEFAULT_RUNTIME_ROOT = REPO_ROOT.parent / "codexalpaca_runtime" / "multi_ticker_portfolio_live"
DEFAULT_QUALITY_SCORECARD_JSON = DEFAULT_RUNTIME_ROOT / "quality_scorecard" / "latest_friday_quality_scorecard.json"
DEFAULT_RESEARCH_DATA_READINESS_JSON = DEFAULT_REPORT_DIR / "gcp_research_data_readiness.json"
DEFAULT_OPTION_AWARE_BACKTEST_STATUS_JSON = DEFAULT_REPORT_DIR / "gcp_option_aware_backtest_status.json"
DEFAULT_TRADE_DATES = "2026-04-21,2026-04-22,2026-04-23"
DEFAULT_GCS_PREFIX = "gs://codexalpaca-control-us/gcp_foundation"
GOVERNED_UNIVERSE = ["QQQ", "SPY", "IWM", "NVDA", "MSFT", "AMZN", "TSLA", "PLTR", "XLE", "GLD", "SLV"]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build compact paper-session learning and data verdict packet.")
    parser.add_argument("--runtime-root", default=str(DEFAULT_RUNTIME_ROOT))
    parser.add_argument("--quality-scorecard-json", default=str(DEFAULT_QUALITY_SCORECARD_JSON))
    parser.add_argument("--research-data-readiness-json", default=str(DEFAULT_RESEARCH_DATA_READINESS_JSON))
    parser.add_argument("--option-aware-backtest-status-json", default=str(DEFAULT_OPTION_AWARE_BACKTEST_STATUS_JSON))
    parser.add_argument("--trade-dates", default=DEFAULT_TRADE_DATES)
    parser.add_argument("--report-dir", default=str(DEFAULT_REPORT_DIR))
    parser.add_argument("--min-net-pnl", type=float, default=200.0)
    parser.add_argument("--target-qualified-winners", type=int, default=20)
    parser.add_argument("--gcs-prefix", default=DEFAULT_GCS_PREFIX)
    return parser


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    return payload if isinstance(payload, dict) else {}


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _float(value: Any, default: float = 0.0) -> float:
    try:
        if value in (None, ""):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _int(value: Any, default: int = 0) -> int:
    try:
        if value in (None, ""):
            return default
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _session_paths(runtime_root: Path, trade_date: str) -> dict[str, Path]:
    run_dir = runtime_root / "runs" / trade_date
    return {
        "run_dir": run_dir,
        "summary": run_dir / "multi_ticker_portfolio_session_summary.json",
        "completed_trades": run_dir / "multi_ticker_portfolio_session_summary_completed_trades.csv",
        "ticker_performance": run_dir / "multi_ticker_portfolio_session_summary_ticker_performance.csv",
        "strategy_performance": run_dir / "multi_ticker_portfolio_session_summary_strategy_performance.csv",
        "evidence": runtime_root / "session_evidence" / f"session_evidence_contract_{trade_date}.json",
        "teaching": runtime_root / "session_teaching" / f"session_teaching_gate_{trade_date}.json",
        "trade_review": runtime_root / "trade_review" / f"trade_review_{trade_date}.json",
        "postmortem": runtime_root / "postmortem" / f"postmortem_{trade_date}.json",
    }


def _session_record(runtime_root: Path, trade_date: str, min_net_pnl: float) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    paths = _session_paths(runtime_root, trade_date)
    summary = _load_json(paths["summary"])
    evidence = _load_json(paths["evidence"])
    teaching = _load_json(paths["teaching"])
    trade_review = _load_json(paths["trade_review"])
    completed_rows = _read_csv(paths["completed_trades"])

    evidence_summary = evidence.get("summary") if isinstance(evidence.get("summary"), dict) else {}
    teaching_summary = teaching.get("summary") if isinstance(teaching.get("summary"), dict) else {}
    review_summary = trade_review.get("summary") if isinstance(trade_review.get("summary"), dict) else {}

    net_pnl = _float(summary.get("net_pnl"))
    completed_trade_count = _int(summary.get("completed_trade_count"), len(completed_rows))
    open_trade_count = _int(summary.get("open_reconciled_trade_count") or summary.get("open_trade_count"))
    ending_position_count = _int(
        (summary.get("ending_broker_positions") or {}).get("position_count")
        if isinstance(summary.get("ending_broker_positions"), dict)
        else evidence_summary.get("ending_broker_position_count")
    )
    shutdown_reconciled = bool(summary.get("shutdown_reconciled") or evidence_summary.get("shutdown_reconciled"))
    evidence_status = str(evidence_summary.get("status") or ("missing" if not evidence else evidence.get("status", "unknown")))
    teaching_status = str(teaching_summary.get("status") or ("missing" if not teaching else teaching.get("status", "unknown")))
    incident_level = str(teaching_summary.get("incident_level") or "")
    incident_code = str(teaching_summary.get("incident_code") or "")
    severe_loss_incident = incident_level == "SEV1" or "severe_loss" in incident_code or "severe_loss" in str(summary.get("block_reason", ""))
    flat = open_trade_count == 0 and ending_position_count == 0 and shutdown_reconciled
    raw_winner = net_pnl >= min_net_pnl
    qualified_winner = raw_winner and flat and evidence_status == "ok" and teaching_status == "ok" and not severe_loss_incident

    disqualifiers: list[str] = []
    if not raw_winner:
        disqualifiers.append("net_pnl_below_winner_threshold")
    if not flat:
        disqualifiers.append("not_flat_or_not_shutdown_reconciled")
    if evidence_status != "ok":
        disqualifiers.append(f"evidence_status_{evidence_status}")
    if teaching_status != "ok":
        disqualifiers.append(f"teaching_status_{teaching_status}")
    if severe_loss_incident:
        disqualifiers.append("severe_loss_incident")

    normalized_trades: list[dict[str, Any]] = []
    for row in completed_rows:
        pnl = _float(row.get("net_pnl"))
        strategy_name = str(row.get("strategy_name") or "")
        normalized_trades.append(
            {
                "trade_date": trade_date,
                "underlying_symbol": str(row.get("underlying_symbol") or ""),
                "strategy_name": strategy_name,
                "regime": str(row.get("regime") or ""),
                "exit_reason": str(row.get("exit_reason") or ""),
                "net_pnl": pnl,
                "quantity": _int(row.get("quantity")),
                "entry_minute": _int(row.get("entry_minute")),
                "exit_minute": _int(row.get("exit_minute")),
                "single_leg_directional": "trend_long_" in strategy_name or "orb_long_" in strategy_name,
                "winner": pnl > 0,
            }
        )

    record = {
        "trade_date": trade_date,
        "session_present": bool(summary),
        "net_pnl": net_pnl,
        "completed_trade_count": completed_trade_count,
        "open_trade_count": open_trade_count,
        "ending_broker_position_count": ending_position_count,
        "shutdown_reconciled": shutdown_reconciled,
        "flat": flat,
        "blocked_new_entries": bool(summary.get("blocked_new_entries")),
        "block_reason": summary.get("block_reason"),
        "raw_winner": raw_winner,
        "qualified_winner": qualified_winner,
        "evidence_status": evidence_status,
        "teaching_status": teaching_status,
        "incident_level": incident_level,
        "incident_code": incident_code,
        "severe_loss_incident": severe_loss_incident,
        "economics_max_abs_cashflow_diff": _float(evidence_summary.get("economics_max_abs_cashflow_diff")),
        "economics_within_tolerance_trade_count": _int(evidence_summary.get("economics_within_tolerance_trade_count")),
        "trade_review_status": "present" if trade_review else "missing",
        "trade_review_loser_count": _int(review_summary.get("loser_count")),
        "trade_review_winner_count": _int(review_summary.get("winner_count")),
        "disqualifiers": disqualifiers,
        "artifact_presence": {name: path.exists() for name, path in paths.items() if name != "run_dir"},
    }
    return record, normalized_trades


def _quality_verdicts(quality_scorecard: dict[str, Any], research_data: dict[str, Any]) -> list[dict[str, Any]]:
    ranked = {
        str(item.get("symbol")): item
        for item in quality_scorecard.get("ranked_symbols", [])
        if isinstance(item, dict) and item.get("symbol")
    }
    stock_rows = {
        str(item.get("symbol")): _int(item.get("row_count"))
        for item in research_data.get("stock_rows", [])
        if isinstance(item, dict) and item.get("symbol")
    }
    selected_contract_rows = {
        str(key): _int(value)
        for key, value in (research_data.get("selected_contract_rows_by_underlying") or {}).items()
    }
    option_inventory_rows = {
        str(key): _int(value)
        for key, value in (research_data.get("option_contract_inventory_rows_by_underlying") or {}).items()
    }

    verdicts = []
    for symbol in GOVERNED_UNIVERSE:
        scorecard = ranked.get(symbol, {})
        stance = str(scorecard.get("stance") or "missing_quality_score")
        rows = stock_rows.get(symbol, 0)
        selected_rows = selected_contract_rows.get(symbol, 0)
        inventory_rows = option_inventory_rows.get(symbol, 0)
        if stance.startswith("avoid"):
            verdict = "avoid_for_first_session"
        elif stance.startswith("shadow"):
            verdict = "shadow_only"
        elif rows > 0 and selected_rows > 0:
            verdict = "research_ready_with_quality_score"
        elif scorecard:
            verdict = "quality_score_only_research_data_gap"
        else:
            verdict = "missing_quality_and_research_data"
        verdicts.append(
            {
                "symbol": symbol,
                "score": scorecard.get("score"),
                "stance": stance,
                "verdict": verdict,
                "research_stock_rows": rows,
                "selected_contract_rows": selected_rows,
                "option_inventory_rows": inventory_rows,
                "reasons": scorecard.get("reasons", []),
            }
        )
    return verdicts


def _loser_learning(normalized_trades: list[dict[str, Any]]) -> dict[str, Any]:
    losers = [trade for trade in normalized_trades if _float(trade.get("net_pnl")) < 0]
    winners = [trade for trade in normalized_trades if _float(trade.get("net_pnl")) > 0]

    by_symbol: dict[str, dict[str, Any]] = defaultdict(lambda: {"trade_count": 0, "net_pnl": 0.0, "loss_count": 0, "stop_loss_count": 0, "single_leg_directional_loss_count": 0})
    by_strategy: dict[str, dict[str, Any]] = defaultdict(lambda: {"trade_count": 0, "net_pnl": 0.0, "loss_count": 0, "stop_loss_count": 0})
    by_exit_reason: dict[str, dict[str, Any]] = defaultdict(lambda: {"trade_count": 0, "net_pnl": 0.0})
    for trade in losers:
        symbol = str(trade.get("underlying_symbol") or "UNKNOWN")
        strategy = str(trade.get("strategy_name") or "UNKNOWN")
        exit_reason = str(trade.get("exit_reason") or "UNKNOWN")
        pnl = _float(trade.get("net_pnl"))
        by_symbol[symbol]["trade_count"] += 1
        by_symbol[symbol]["loss_count"] += 1
        by_symbol[symbol]["net_pnl"] += pnl
        by_symbol[symbol]["stop_loss_count"] += 1 if exit_reason == "stop_loss" else 0
        by_symbol[symbol]["single_leg_directional_loss_count"] += 1 if trade.get("single_leg_directional") else 0
        by_strategy[strategy]["trade_count"] += 1
        by_strategy[strategy]["loss_count"] += 1
        by_strategy[strategy]["net_pnl"] += pnl
        by_strategy[strategy]["stop_loss_count"] += 1 if exit_reason == "stop_loss" else 0
        by_exit_reason[exit_reason]["trade_count"] += 1
        by_exit_reason[exit_reason]["net_pnl"] += pnl

    def compact(mapping: dict[str, dict[str, Any]], limit: int = 10) -> list[dict[str, Any]]:
        rows = []
        for name, values in mapping.items():
            row = {"name": name, **values}
            row["net_pnl"] = round(float(row["net_pnl"]), 4)
            row["avg_pnl"] = round(row["net_pnl"] / max(1, int(row["trade_count"])), 4)
            rows.append(row)
        return sorted(rows, key=lambda item: item["net_pnl"])[:limit]

    return {
        "trade_count": len(normalized_trades),
        "winner_count": len(winners),
        "loser_count": len(losers),
        "total_loser_net_pnl": round(sum(_float(trade["net_pnl"]) for trade in losers), 4),
        "top_losing_symbols": compact(by_symbol),
        "top_losing_strategies": compact(by_strategy),
        "exit_reason_loss_clusters": compact(by_exit_reason),
        "learning_actions": [
            "Suppress or shadow symbols with repeated stop-loss and single-leg directional loser similarity until new evidence clears.",
            "Require option-aware fill coverage before promoting sparse positive backtest candidates.",
            "Prefer defined-risk or reduced-risk structures for symbols that repeatedly lose through single-leg directional exits.",
        ],
    }


def build_payload(
    *,
    runtime_root: Path,
    quality_scorecard_json: Path,
    research_data_readiness_json: Path,
    option_aware_backtest_status_json: Path,
    trade_dates: list[str],
    report_dir: Path,
    min_net_pnl: float,
    target_qualified_winners: int,
    gcs_prefix: str,
) -> dict[str, Any]:
    session_records = []
    normalized_trades: list[dict[str, Any]] = []
    for trade_date in trade_dates:
        record, trades = _session_record(runtime_root, trade_date, min_net_pnl)
        session_records.append(record)
        normalized_trades.extend(trades)

    quality_scorecard = _load_json(quality_scorecard_json)
    research_data = _load_json(research_data_readiness_json)
    option_status = _load_json(option_aware_backtest_status_json)
    raw_winner_count = sum(1 for record in session_records if record["raw_winner"])
    qualified_winner_count = sum(1 for record in session_records if record["qualified_winner"])
    severe_loss_count = sum(1 for record in session_records if record["severe_loss_incident"])
    review_required_count = sum(
        1
        for record in session_records
        if record["evidence_status"] != "ok" or record["teaching_status"] != "ok"
    )

    promotion_blockers = []
    if qualified_winner_count < target_qualified_winners:
        promotion_blockers.append(f"qualified_winner_count_{qualified_winner_count}_below_target_{target_qualified_winners}")
    if review_required_count:
        promotion_blockers.append("session_evidence_or_teaching_review_required")
    if severe_loss_count:
        promotion_blockers.append("severe_loss_incident_present")
    if option_status and not option_status.get("promotion_allowed", False):
        promotion_blockers.append(f"option_aware_status_{option_status.get('status')}")

    status = "blocked_no_governed_validation_candidate" if promotion_blockers else "ready_for_governed_validation_candidate_review"
    return {
        "generated_at": datetime.now().astimezone().isoformat(),
        "status": status,
        "runtime_root": str(runtime_root),
        "report_dir": str(report_dir),
        "gcs_prefix": gcs_prefix,
        "trade_dates": trade_dates,
        "min_net_pnl": min_net_pnl,
        "target_qualified_winners": target_qualified_winners,
        "raw_winner_count": raw_winner_count,
        "qualified_winner_count": qualified_winner_count,
        "qualified_winners_remaining": max(0, target_qualified_winners - qualified_winner_count),
        "session_ledger": session_records,
        "governed_universe_data_verdicts": _quality_verdicts(quality_scorecard, research_data),
        "loser_learning": _loser_learning(normalized_trades),
        "promotion_readiness": {
            "candidate_state": status,
            "promotion_allowed": not promotion_blockers,
            "blockers": promotion_blockers,
            "option_aware_status": option_status.get("status"),
            "option_aware_recommendation_counts": option_status.get("recommendation_counts", {}),
            "smallest_next_evidence_package": [
                "Run the April 24 bounded VM paper session and require flat, reconciled, evidence-clean closeout.",
                "Resolve evidence/teaching review on prior raw winner before counting it as qualified.",
                "Improve option-aware fill coverage or add quote/spread evidence before considering SLV research candidates.",
                "Keep Friday execution limited by the current quality scorecard; use loser clusters only as suppressors, not promotions.",
            ],
        },
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "# GCP Paper Session Learning Packet",
        "",
        "## Snapshot",
        "",
        f"- Generated at: `{payload['generated_at']}`",
        f"- Status: `{payload['status']}`",
        f"- Raw winners: `{payload['raw_winner_count']}`",
        f"- Qualified winners: `{payload['qualified_winner_count']}`",
        f"- Qualified winners remaining: `{payload['qualified_winners_remaining']}`",
        "",
        "## Session Ledger",
        "",
        "| Date | Net PnL | Trades | Flat | Evidence | Teaching | Raw Winner | Qualified | Disqualifiers |",
        "|---|---:|---:|---|---|---|---|---|---|",
    ]
    for record in payload["session_ledger"]:
        lines.append(
            "| {trade_date} | {net_pnl:.2f} | {completed_trade_count} | {flat} | {evidence_status} | {teaching_status} | {raw_winner} | {qualified_winner} | {disq} |".format(
                disq=", ".join(record["disqualifiers"]) or "none",
                **record,
            )
        )
    lines.extend(
        [
            "",
            "## Governed Universe Verdicts",
            "",
            "| Symbol | Score | Stance | Research Rows | Selected Contracts | Verdict |",
            "|---|---:|---|---:|---:|---|",
        ]
    )
    for row in payload["governed_universe_data_verdicts"]:
        lines.append(
            f"| {row['symbol']} | {row.get('score')} | {row['stance']} | {row['research_stock_rows']} | {row['selected_contract_rows']} | {row['verdict']} |"
        )
    loser = payload["loser_learning"]
    lines.extend(
        [
            "",
            "## Loser Learning",
            "",
            f"- Normalized trades: `{loser['trade_count']}`",
            f"- Winners: `{loser['winner_count']}`",
            f"- Losers: `{loser['loser_count']}`",
            f"- Total loser PnL: `{loser['total_loser_net_pnl']}`",
            "",
            "### Top Losing Symbols",
            "",
        ]
    )
    for row in loser["top_losing_symbols"][:8]:
        lines.append(f"- `{row['name']}` trades `{row['trade_count']}` net `{row['net_pnl']}` stops `{row.get('stop_loss_count', 0)}`")
    lines.extend(["", "### Learning Actions", ""])
    for item in loser["learning_actions"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Promotion Readiness", ""])
    readiness = payload["promotion_readiness"]
    lines.append(f"- Candidate state: `{readiness['candidate_state']}`")
    lines.append(f"- Promotion allowed: `{readiness['promotion_allowed']}`")
    lines.append(f"- Option-aware status: `{readiness.get('option_aware_status')}`")
    lines.extend(["", "### Blockers", ""])
    for blocker in readiness["blockers"]:
        lines.append(f"- `{blocker}`")
    lines.extend(["", "### Smallest Next Evidence Package", ""])
    for item in readiness["smallest_next_evidence_package"]:
        lines.append(f"- {item}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = build_parser().parse_args()
    report_dir = Path(args.report_dir)
    trade_dates = [item.strip() for item in args.trade_dates.split(",") if item.strip()]
    payload = build_payload(
        runtime_root=Path(args.runtime_root),
        quality_scorecard_json=Path(args.quality_scorecard_json),
        research_data_readiness_json=Path(args.research_data_readiness_json),
        option_aware_backtest_status_json=Path(args.option_aware_backtest_status_json),
        trade_dates=trade_dates,
        report_dir=report_dir,
        min_net_pnl=args.min_net_pnl,
        target_qualified_winners=args.target_qualified_winners,
        gcs_prefix=args.gcs_prefix,
    )
    write_json(report_dir / "gcp_paper_session_learning_packet.json", payload)
    write_markdown(report_dir / "gcp_paper_session_learning_packet.md", payload)
    write_markdown(report_dir / "gcp_paper_session_learning_handoff.md", payload)
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
