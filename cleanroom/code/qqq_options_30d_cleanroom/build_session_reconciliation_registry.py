from __future__ import annotations

import argparse
import ast
import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[2]
WORKSPACE_ROOT = ROOT.parents[4]


def first_existing_path(*paths: Path) -> Path:
    for path in paths:
        if path.exists():
            return path
    return paths[0]


DEFAULT_RUNNER_REPO_ROOT = first_existing_path(
    WORKSPACE_ROOT / "codexalpaca_repo",
    Path(r"C:\Users\rabisaab\Downloads\codexalpaca_repo"),
    Path(r"C:\Users\rabisaab\OneDrive\CodexAlpaca\downloads_remaining_20260417\folders\codexalpaca_repo"),
)
DEFAULT_REPORTS_ROOT = DEFAULT_RUNNER_REPO_ROOT / "reports" / "multi_ticker_portfolio" / "runs"
DEFAULT_REPORT_DIR = REPO_ROOT / "docs" / "session_reconciliation"
CONTRACT_MULTIPLIER = 100.0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build a machine-readable session reconciliation registry from paper-runner session bundles."
    )
    parser.add_argument("--runner-repo-root", default=str(DEFAULT_RUNNER_REPO_ROOT))
    parser.add_argument("--reports-root", default=str(DEFAULT_REPORTS_ROOT))
    parser.add_argument("--report-dir", default=str(DEFAULT_REPORT_DIR))
    parser.add_argument("--top-n", type=int, default=10)
    return parser


def parse_float(value: Any) -> float | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def parse_int(value: Any) -> int | None:
    parsed = parse_float(value)
    if parsed is None:
        return None
    return int(parsed)


def round_float(value: float | None, digits: int = 6) -> float | None:
    if value is None:
        return None
    return round(value, digits)


def load_json_object(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def load_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        return [dict(row) for row in reader]


def sum_float_field(rows: list[dict[str, str]], field: str) -> float:
    total = 0.0
    for row in rows:
        parsed = parse_float(row.get(field))
        if parsed is not None:
            total += parsed
    return total


def parse_legs(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    text = str(value or "").strip()
    if not text:
        return []
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        try:
            parsed = ast.literal_eval(text)
        except (SyntaxError, ValueError):
            return []
    return parsed if isinstance(parsed, list) else []


def build_local_cashflow_summary(completed_rows: list[dict[str, str]]) -> dict[str, Any]:
    entry_gross_total = 0.0
    exit_gross_total = 0.0
    gross_cashflow_total = 0.0
    net_cashflow_total = 0.0
    fee_total = 0.0
    compatible_trade_count = 0
    incompatible_trade_count = 0

    for row in completed_rows:
        quantity = parse_int(row.get("quantity"))
        entry_fill_price = parse_float(row.get("entry_fill_price"))
        exit_fill_price = parse_float(row.get("exit_fill_price"))
        if quantity is None or entry_fill_price is None or exit_fill_price is None:
            incompatible_trade_count += 1
            continue

        leg_count = len(parse_legs(row.get("legs")))
        entry_gross = -entry_fill_price * CONTRACT_MULTIPLIER * quantity
        exit_cashflow_sign = -1.0 if leg_count > 1 else 1.0
        exit_gross = exit_cashflow_sign * exit_fill_price * CONTRACT_MULTIPLIER * quantity
        total_fees = (parse_float(row.get("entry_total_fees")) or 0.0) + (parse_float(row.get("exit_total_fees")) or 0.0)

        entry_gross_total += entry_gross
        exit_gross_total += exit_gross
        gross_cashflow_total += entry_gross + exit_gross
        net_cashflow_total += entry_gross + exit_gross - total_fees
        fee_total += total_fees
        compatible_trade_count += 1

    return {
        "local_entry_gross_cashflow_total": round_float(entry_gross_total),
        "local_exit_gross_cashflow_total": round_float(exit_gross_total),
        "local_gross_cashflow_total": round_float(gross_cashflow_total),
        "local_net_cashflow_total": round_float(net_cashflow_total),
        "local_total_fees": round_float(fee_total),
        "local_cashflow_compatible_trade_count": compatible_trade_count,
        "local_cashflow_incompatible_trade_count": incompatible_trade_count,
    }


def build_broker_activity_cashflow_summary(broker_activity_rows: list[dict[str, str]]) -> dict[str, Any]:
    cashflow_total = 0.0
    comparable_activity_count = 0
    incompatible_activity_count = 0

    for row in broker_activity_rows:
        quantity = parse_float(row.get("qty"))
        price = parse_float(row.get("price"))
        side = str(row.get("side") or "").strip().lower()
        if quantity is None or price is None or side not in {"buy", "sell"}:
            incompatible_activity_count += 1
            continue

        signed_cashflow = price * quantity * CONTRACT_MULTIPLIER
        if side == "buy":
            signed_cashflow *= -1.0
        cashflow_total += signed_cashflow
        comparable_activity_count += 1

    return {
        "broker_activity_cashflow_total": round_float(cashflow_total),
        "broker_cashflow_comparable_activity_count": comparable_activity_count,
        "broker_cashflow_incompatible_activity_count": incompatible_activity_count,
    }


def broker_cashflow_tolerance(
    *,
    local_gross_cashflow_total: float,
    broker_activity_cashflow_total: float,
    comparable_activity_count: int,
) -> float:
    gross_reference = max(abs(local_gross_cashflow_total), abs(broker_activity_cashflow_total))
    tolerance = max(1.0, 0.25 * max(comparable_activity_count, 1), 0.0005 * gross_reference)
    return round_float(tolerance) or 1.0


def determine_session_kind(summary_payload: dict[str, Any]) -> str:
    completed_trade_count = int(summary_payload.get("completed_trade_count", 0) or 0)
    entry_submission_count = int(summary_payload.get("entry_submission_count", 0) or 0)
    exit_submission_count = int(summary_payload.get("exit_submission_count", 0) or 0)
    signal_attempt_count = int(summary_payload.get("signal_attempt_count", 0) or 0)
    eligible_signal_count = int(summary_payload.get("eligible_signal_count", 0) or 0)

    if completed_trade_count > 0 or entry_submission_count > 0 or exit_submission_count > 0:
        return "traded"
    if signal_attempt_count > 0 or eligible_signal_count > 0:
        return "active_no_trade"
    return "idle"


def session_reasons(summary_payload: dict[str, Any], session: dict[str, Any]) -> tuple[list[str], list[str]]:
    review_required: list[str] = []
    caution: list[str] = []

    traded = session["session_kind"] == "traded"
    if traded and not session["shutdown_reconciled"]:
        review_required.append("shutdown_not_reconciled")
    if traded and session["ending_broker_position_count"] > 0:
        review_required.append("residual_broker_positions")
    if traded and session["forced_exit_failure_count"] > 0:
        review_required.append("forced_exit_failures")
    if traded and session["completed_trade_count_delta"] != 0:
        review_required.append("completed_trade_count_delta")
    if traded and session["realized_reconciliation_delta_abs"] > 0.05:
        review_required.append("realized_pnl_delta")
    if traded and session["broker_local_cashflow_comparable"] and session["broker_local_cashflow_delta_abs"] > session["broker_local_cashflow_tolerance"]:
        review_required.append("broker_local_cashflow_delta")

    if traded and not session["broker_order_audit_available"]:
        caution.append("broker_order_audit_gap")
    if traded and not session["broker_activity_audit_available"]:
        caution.append("broker_activity_audit_gap")
    if traded and session["broker_activity_audit_available"] and not session["broker_local_cashflow_comparable"]:
        caution.append("broker_local_cashflow_not_comparable")
    if traded and session["broker_status_mismatch_count"] > 0:
        caution.append("broker_status_mismatch")
    if traded and session["local_order_without_broker_match_count"] > 0:
        caution.append("local_order_without_broker_match")
    if traded and session["unexpected_broker_order_count"] > 0:
        caution.append("unexpected_broker_order")
    if traded and session["broker_activity_unmatched_count"] > 0:
        caution.append("broker_activity_unmatched")
    if traded and session["local_filled_order_without_activity_match_count"] > 0:
        caution.append("local_fill_without_activity_match")
    if traded and session["partial_fill_count"] > 0:
        caution.append("partial_fill_pressure")
    if traded and session["known_trade_cleanup_count"] > 0:
        caution.append("known_trade_cleanup")
    if traded and session["unexpected_position_cleanup_count"] > 0:
        caution.append("unexpected_position_cleanup")
    if session["guardrail_manual_review_count"] > 0:
        caution.append("guardrail_manual_review")
    if session["severe_loss_flatten_triggered"]:
        caution.append("severe_loss_flatten_triggered")
    if summary_payload.get("startup_check_status") not in (None, "", "passed", "pending"):
        caution.append("startup_check_not_passed")

    return review_required, caution


def trust_tier(review_required: list[str], caution: list[str], session_kind: str) -> str:
    if review_required:
        return "review_required"
    if caution:
        return "caution"
    if session_kind == "traded":
        return "trusted"
    return "idle"


def quality_score(review_required: list[str], caution: list[str], session: dict[str, Any]) -> int:
    score = 100
    penalties = {
        "shutdown_not_reconciled": 40,
        "residual_broker_positions": 30,
        "forced_exit_failures": 25,
        "realized_pnl_delta": 20,
        "completed_trade_count_delta": 15,
        "broker_local_cashflow_delta": 15,
        "broker_order_audit_gap": 10,
        "broker_activity_audit_gap": 10,
        "broker_local_cashflow_not_comparable": 10,
        "broker_status_mismatch": 10,
        "local_order_without_broker_match": 10,
        "unexpected_broker_order": 10,
        "broker_activity_unmatched": 10,
        "local_fill_without_activity_match": 10,
        "partial_fill_pressure": 5,
        "known_trade_cleanup": 5,
        "unexpected_position_cleanup": 5,
        "guardrail_manual_review": 5,
        "severe_loss_flatten_triggered": 5,
        "startup_check_not_passed": 5,
    }
    for reason in review_required + caution:
        score -= penalties.get(reason, 0)

    if session["completed_trade_count"] == 0 and session["session_kind"] == "idle":
        score = min(score, 95)

    return max(0, min(100, score))


def build_session_row(run_dir: Path) -> dict[str, Any]:
    summary_path = run_dir / "multi_ticker_portfolio_session_summary.json"
    completed_path = run_dir / "multi_ticker_portfolio_session_summary_completed_trades.csv"
    reconciliation_path = run_dir / "multi_ticker_portfolio_session_summary_trade_reconciliation.csv"
    event_path = run_dir / "multi_ticker_portfolio_session_summary_trade_reconciliation_events.csv"
    broker_order_audit_path = run_dir / "multi_ticker_portfolio_session_summary_broker_order_audit.csv"
    broker_activity_path = run_dir / "multi_ticker_portfolio_session_summary_broker_account_activities.csv"
    ending_positions_path = run_dir / "multi_ticker_portfolio_session_summary_ending_broker_positions.csv"

    summary_payload = load_json_object(summary_path)
    completed_rows = load_csv_rows(completed_path)
    reconciliation_rows = load_csv_rows(reconciliation_path)
    event_rows = load_csv_rows(event_path)
    broker_order_audit_rows = load_csv_rows(broker_order_audit_path)
    broker_activity_rows = load_csv_rows(broker_activity_path)
    ending_position_rows = load_csv_rows(ending_positions_path)
    local_cashflow_summary = build_local_cashflow_summary(completed_rows)
    broker_cashflow_summary = build_broker_activity_cashflow_summary(broker_activity_rows)

    cleanup_summary = dict(summary_payload.get("end_of_day_cleanup") or {})
    session_kind = determine_session_kind(summary_payload)
    completed_trade_count = int(summary_payload.get("completed_trade_count", 0) or 0)
    completed_trade_count_table = len(completed_rows)
    completed_trade_count_delta = completed_trade_count_table - completed_trade_count

    realized_reconciled_net_pnl = parse_float(summary_payload.get("realized_reconciled_net_pnl")) or 0.0
    completed_trade_net_pnl_total = sum_float_field(completed_rows, "net_pnl")
    realized_reconciliation_delta = completed_trade_net_pnl_total - realized_reconciled_net_pnl

    broker_partially_filled_order_count = int(summary_payload.get("broker_partially_filled_order_count", 0) or 0)
    broker_activity_partial_fill_count = int(summary_payload.get("broker_partial_fill_activity_count", 0) or 0)
    local_gross_cashflow_total = float(local_cashflow_summary["local_gross_cashflow_total"] or 0.0)
    broker_activity_cashflow_total = float(broker_cashflow_summary["broker_activity_cashflow_total"] or 0.0)
    broker_local_cashflow_comparable = bool(
        broker_activity_rows
        and local_cashflow_summary["local_cashflow_compatible_trade_count"] > 0
        and broker_cashflow_summary["broker_cashflow_comparable_activity_count"] > 0
    )
    broker_local_cashflow_delta = (
        broker_activity_cashflow_total - local_gross_cashflow_total
        if broker_local_cashflow_comparable
        else None
    )
    broker_local_cashflow_delta_abs = abs(broker_local_cashflow_delta) if broker_local_cashflow_delta is not None else None
    broker_local_cashflow_tolerance = (
        broker_cashflow_tolerance(
            local_gross_cashflow_total=local_gross_cashflow_total,
            broker_activity_cashflow_total=broker_activity_cashflow_total,
            comparable_activity_count=int(broker_cashflow_summary["broker_cashflow_comparable_activity_count"]),
        )
        if broker_local_cashflow_comparable
        else None
    )

    session = {
        "trade_date": str(summary_payload.get("trade_date") or run_dir.name),
        "session_kind": session_kind,
        "submit_paper_orders": bool(summary_payload.get("submit_paper_orders", False)),
        "startup_check_status": str(summary_payload.get("startup_check_status", "")).strip(),
        "blocked_new_entries": bool(summary_payload.get("blocked_new_entries", False)),
        "block_reason": str(summary_payload.get("block_reason", "")).strip(),
        "completed_trade_count": completed_trade_count,
        "completed_trade_count_table": completed_trade_count_table,
        "completed_trade_count_delta": completed_trade_count_delta,
        "reconciliation_row_count": len(reconciliation_rows),
        "event_row_count": len(event_rows),
        "realized_reconciled_net_pnl": round_float(realized_reconciled_net_pnl),
        "completed_trade_net_pnl_total": round_float(completed_trade_net_pnl_total),
        "realized_reconciliation_delta": round_float(realized_reconciliation_delta),
        "realized_reconciliation_delta_abs": round_float(abs(realized_reconciliation_delta)) or 0.0,
        **local_cashflow_summary,
        "shutdown_reconciled": bool(summary_payload.get("shutdown_reconciled", False)),
        "guardrail_fire_count": int(summary_payload.get("guardrail_fire_count", 0) or 0),
        "guardrail_manual_review_count": int(summary_payload.get("guardrail_manual_review_count", 0) or 0),
        "broker_order_audit_available": bool(summary_payload.get("broker_order_audit_available", False)),
        "broker_order_count": int(summary_payload.get("broker_order_count", 0) or len(broker_order_audit_rows)),
        "broker_status_mismatch_count": int(summary_payload.get("broker_status_mismatch_count", 0) or 0),
        "local_order_without_broker_match_count": int(
            summary_payload.get("local_order_without_broker_match_count", 0) or 0
        ),
        "unexpected_broker_order_count": int(summary_payload.get("broker_order_unmatched_count", 0) or 0),
        "broker_activity_audit_available": bool(summary_payload.get("broker_activity_audit_available", False)),
        "broker_activity_count": int(summary_payload.get("broker_activity_count", 0) or len(broker_activity_rows)),
        "broker_activity_unmatched_count": int(summary_payload.get("broker_activity_unmatched_count", 0) or 0),
        "local_filled_order_without_activity_match_count": int(
            summary_payload.get("local_filled_order_without_activity_match_count", 0) or 0
        ),
        **broker_cashflow_summary,
        "broker_local_cashflow_comparable": broker_local_cashflow_comparable,
        "broker_local_cashflow_delta": round_float(broker_local_cashflow_delta),
        "broker_local_cashflow_delta_abs": round_float(broker_local_cashflow_delta_abs),
        "broker_local_cashflow_tolerance": round_float(broker_local_cashflow_tolerance),
        "broker_partially_filled_order_count": broker_partially_filled_order_count,
        "broker_activity_partial_fill_count": broker_activity_partial_fill_count,
        "partial_fill_count": broker_partially_filled_order_count + broker_activity_partial_fill_count,
        "ending_broker_position_count": int(
            summary_payload.get("ending_broker_position_count", 0) or len(ending_position_rows)
        ),
        "forced_exit_failure_count": int(cleanup_summary.get("forced_exit_failure_count", 0) or 0),
        "known_trade_cleanup_count": int(cleanup_summary.get("known_trade_cleanup_count", 0) or 0),
        "unexpected_position_cleanup_count": int(cleanup_summary.get("unexpected_position_cleanup_count", 0) or 0),
        "severe_loss_flatten_triggered": "severe_loss_flatten_all triggered"
        in str(summary_payload.get("block_reason", "")).lower(),
        "run_dir": str(run_dir),
    }

    review_required, caution = session_reasons(summary_payload, session)
    session["review_required_reasons"] = review_required
    session["caution_reasons"] = caution
    session["trust_tier"] = trust_tier(review_required, caution, session_kind)
    session["quality_score"] = quality_score(review_required, caution, session)
    return session


def flatten_sessions_for_csv(sessions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for session in sessions:
        rows.append(
            {
                "trade_date": session["trade_date"],
                "session_kind": session["session_kind"],
                "trust_tier": session["trust_tier"],
                "quality_score": session["quality_score"],
                "completed_trade_count": session["completed_trade_count"],
                "completed_trade_count_table": session["completed_trade_count_table"],
                "completed_trade_count_delta": session["completed_trade_count_delta"],
                "realized_reconciled_net_pnl": session["realized_reconciled_net_pnl"],
                "completed_trade_net_pnl_total": session["completed_trade_net_pnl_total"],
                "realized_reconciliation_delta": session["realized_reconciliation_delta"],
                "shutdown_reconciled": session["shutdown_reconciled"],
                "local_gross_cashflow_total": session["local_gross_cashflow_total"],
                "local_net_cashflow_total": session["local_net_cashflow_total"],
                "local_total_fees": session["local_total_fees"],
                "guardrail_fire_count": session["guardrail_fire_count"],
                "guardrail_manual_review_count": session["guardrail_manual_review_count"],
                "broker_order_audit_available": session["broker_order_audit_available"],
                "broker_status_mismatch_count": session["broker_status_mismatch_count"],
                "local_order_without_broker_match_count": session["local_order_without_broker_match_count"],
                "unexpected_broker_order_count": session["unexpected_broker_order_count"],
                "broker_activity_audit_available": session["broker_activity_audit_available"],
                "broker_activity_unmatched_count": session["broker_activity_unmatched_count"],
                "local_filled_order_without_activity_match_count": session[
                    "local_filled_order_without_activity_match_count"
                ],
                "broker_activity_cashflow_total": session["broker_activity_cashflow_total"],
                "broker_local_cashflow_comparable": session["broker_local_cashflow_comparable"],
                "broker_local_cashflow_delta": session["broker_local_cashflow_delta"],
                "broker_local_cashflow_tolerance": session["broker_local_cashflow_tolerance"],
                "partial_fill_count": session["partial_fill_count"],
                "ending_broker_position_count": session["ending_broker_position_count"],
                "forced_exit_failure_count": session["forced_exit_failure_count"],
                "known_trade_cleanup_count": session["known_trade_cleanup_count"],
                "unexpected_position_cleanup_count": session["unexpected_position_cleanup_count"],
                "review_required_reasons": "|".join(session["review_required_reasons"]),
                "caution_reasons": "|".join(session["caution_reasons"]),
                "run_dir": session["run_dir"],
            }
        )
    return rows


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fieldnames: list[str] = []
    for row in rows:
        for key in row.keys():
            if key not in fieldnames:
                fieldnames.append(key)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    summary = payload["summary"]
    data_quality = payload["data_quality"]
    lines: list[str] = []
    lines.append("# Session Reconciliation Registry")
    lines.append("")
    lines.append("## Snapshot")
    lines.append("")
    lines.append(f"- Generated at: `{payload['generated_at']}`")
    lines.append(f"- Sessions scanned: `{summary['sessions_scanned']}`")
    lines.append(f"- Trade sessions: `{summary['trade_session_count']}`")
    lines.append(f"- Trusted trade sessions: `{summary['trusted_trade_session_count']}`")
    lines.append(f"- Caution sessions: `{summary['caution_session_count']}`")
    lines.append(f"- Review-required sessions: `{summary['review_required_session_count']}`")
    lines.append(f"- Sessions with broker-order audit: `{summary['broker_order_audit_session_count']}`")
    lines.append(f"- Sessions with broker-activity audit: `{summary['broker_activity_audit_session_count']}`")
    lines.append(f"- Sessions with broker/local cashflow comparison: `{summary['broker_cashflow_comparable_session_count']}`")
    lines.append(f"- Residual broker positions: `{summary['ending_broker_position_count_total']}`")
    lines.append(
        f"- Mean absolute realized reconciliation delta: `{summary['realized_reconciliation_delta_abs_mean']}`"
    )
    lines.append(
        f"- Mean absolute broker/local cashflow delta: `{summary['broker_local_cashflow_delta_abs_mean']}`"
    )
    lines.append("")
    lines.append("## Institutional Findings")
    lines.append("")
    for finding in payload["findings"]:
        lines.append(f"- `{finding['type']}`: {finding['message']}")
    if not payload["findings"]:
        lines.append("- none")
    lines.append("")
    lines.append("## Review-Required Sessions")
    lines.append("")
    review_rows = [row for row in payload["sessions"] if row["trust_tier"] == "review_required"][: payload["top_n"]]
    for row in review_rows:
        lines.append(
            f"- `{row['trade_date']}`: quality `{row['quality_score']}`, completed trades `{row['completed_trade_count']}`, reasons `{', '.join(row['review_required_reasons'])}`"
        )
    if not review_rows:
        lines.append("- none")
    lines.append("")
    lines.append("## Caution Sessions")
    lines.append("")
    caution_rows = [row for row in payload["sessions"] if row["trust_tier"] == "caution"][: payload["top_n"]]
    for row in caution_rows:
        lines.append(
            f"- `{row['trade_date']}`: quality `{row['quality_score']}`, completed trades `{row['completed_trade_count']}`, reasons `{', '.join(row['caution_reasons'])}`"
        )
    if not caution_rows:
        lines.append("- none")
    lines.append("")
    lines.append("## Data Quality")
    lines.append("")
    lines.append(
        f"- Missing broker-order audit on traded sessions: `{', '.join(data_quality['missing_broker_order_audit_dates']) or 'none'}`"
    )
    lines.append(
        f"- Missing broker-activity audit on traded sessions: `{', '.join(data_quality['missing_broker_activity_audit_dates']) or 'none'}`"
    )
    lines.append(
        f"- Missing broker/local cashflow comparison on broker-audited traded sessions: `{', '.join(data_quality['missing_broker_cashflow_comparison_dates']) or 'none'}`"
    )
    lines.append("")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_findings(summary: dict[str, Any], data_quality: dict[str, Any]) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    if summary["review_required_session_count"] > 0:
        findings.append(
            {
                "type": "review_required_sessions",
                "message": f"`{summary['review_required_session_count']}` session(s) have reconciliation issues severe enough that they should not automatically steer research policy.",
            }
        )
    if summary["ending_broker_position_count_total"] > 0:
        findings.append(
            {
                "type": "residual_broker_positions",
                "message": f"`{summary['ending_broker_position_count_total']}` residual broker position row(s) were observed in session end-state artifacts.",
            }
        )
    if summary["broker_status_mismatch_count_total"] > 0 or summary["local_order_without_broker_match_count_total"] > 0:
        findings.append(
            {
                "type": "broker_order_mismatch_pressure",
                "message": f"`{summary['broker_status_mismatch_count_total']}` broker status mismatch(es) and `{summary['local_order_without_broker_match_count_total']}` unmatched local order(s) were observed.",
            }
        )
    if (
        summary["broker_activity_unmatched_count_total"] > 0
        or summary["local_filled_order_without_activity_match_count_total"] > 0
    ):
        findings.append(
            {
                "type": "broker_activity_mismatch_pressure",
                "message": f"`{summary['broker_activity_unmatched_count_total']}` unmatched broker activity row(s) and `{summary['local_filled_order_without_activity_match_count_total']}` local fill(s) without activity match were observed.",
            }
        )
    if summary["broker_local_cashflow_delta_review_required_count"] > 0:
        findings.append(
            {
                "type": "broker_local_economics_drift",
                "message": f"`{summary['broker_local_cashflow_delta_review_required_count']}` session(s) showed broker/local cashflow drift above tolerance and should not automatically steer research policy.",
            }
        )
    if data_quality["missing_broker_order_audit_dates"]:
        findings.append(
            {
                "type": "broker_order_audit_gap",
                "message": f"Broker-order audit is missing for traded session(s): `{', '.join(data_quality['missing_broker_order_audit_dates'])}`.",
            }
        )
    if data_quality["missing_broker_activity_audit_dates"]:
        findings.append(
            {
                "type": "broker_activity_audit_gap",
                "message": f"Broker-activity audit is missing for traded session(s): `{', '.join(data_quality['missing_broker_activity_audit_dates'])}`.",
            }
        )
    if data_quality["missing_broker_cashflow_comparison_dates"]:
        findings.append(
            {
                "type": "broker_local_cashflow_comparison_gap",
                "message": f"Broker/local cashflow comparison was not available for broker-audited traded session(s): `{', '.join(data_quality['missing_broker_cashflow_comparison_dates'])}`.",
            }
        )
    return findings


def main() -> None:
    args = build_parser().parse_args()
    runner_repo_root = Path(args.runner_repo_root).resolve()
    reports_root = Path(args.reports_root).resolve()
    report_dir = Path(args.report_dir).resolve()
    report_dir.mkdir(parents=True, exist_ok=True)

    run_dirs = sorted(
        [path for path in reports_root.iterdir() if path.is_dir() and (path / "multi_ticker_portfolio_session_summary.json").exists()],
        key=lambda path: path.name,
    )
    sessions = [build_session_row(run_dir) for run_dir in run_dirs]
    sessions_sorted = sorted(
        sessions,
        key=lambda row: (
            {"review_required": 0, "caution": 1, "trusted": 2, "idle": 3}.get(row["trust_tier"], 9),
            row["quality_score"],
            row["trade_date"],
        ),
    )

    traded_sessions = [row for row in sessions if row["session_kind"] == "traded"]
    trusted_trade_sessions = [row for row in traded_sessions if row["trust_tier"] == "trusted"]
    caution_sessions = [row for row in sessions if row["trust_tier"] == "caution"]
    review_required_sessions = [row for row in sessions if row["trust_tier"] == "review_required"]

    missing_broker_order_audit_dates = [
        row["trade_date"]
        for row in traded_sessions
        if not row["broker_order_audit_available"]
    ]
    missing_broker_activity_audit_dates = [
        row["trade_date"]
        for row in traded_sessions
        if not row["broker_activity_audit_available"]
    ]
    missing_broker_cashflow_comparison_dates = [
        row["trade_date"]
        for row in traded_sessions
        if row["broker_activity_audit_available"] and not row["broker_local_cashflow_comparable"]
    ]

    realized_reconciliation_deltas = [row["realized_reconciliation_delta_abs"] for row in traded_sessions]
    realized_reconciliation_delta_abs_mean = (
        round_float(sum(realized_reconciliation_deltas) / len(realized_reconciliation_deltas))
        if realized_reconciliation_deltas
        else 0.0
    )
    broker_local_cashflow_deltas = [
        float(row["broker_local_cashflow_delta_abs"])
        for row in traded_sessions
        if row["broker_local_cashflow_delta_abs"] is not None
    ]
    broker_local_cashflow_delta_abs_mean = (
        round_float(sum(broker_local_cashflow_deltas) / len(broker_local_cashflow_deltas))
        if broker_local_cashflow_deltas
        else 0.0
    )

    payload = {
        "generated_at": datetime.now().isoformat(),
        "runner_repo_root": str(runner_repo_root),
        "reports_root": str(reports_root),
        "top_n": int(args.top_n),
        "summary": {
            "sessions_scanned": len(run_dirs),
            "trade_session_count": len(traded_sessions),
            "trusted_trade_session_count": len(trusted_trade_sessions),
            "caution_session_count": len(caution_sessions),
            "review_required_session_count": len(review_required_sessions),
            "shutdown_reconciled_session_count": sum(1 for row in sessions if row["shutdown_reconciled"]),
            "broker_order_audit_session_count": sum(1 for row in sessions if row["broker_order_audit_available"]),
            "broker_activity_audit_session_count": sum(1 for row in sessions if row["broker_activity_audit_available"]),
            "broker_cashflow_comparable_session_count": sum(
                1 for row in sessions if row["broker_local_cashflow_comparable"]
            ),
            "completed_trade_count_total": sum(int(row["completed_trade_count"]) for row in sessions),
            "broker_status_mismatch_count_total": sum(int(row["broker_status_mismatch_count"]) for row in sessions),
            "local_order_without_broker_match_count_total": sum(
                int(row["local_order_without_broker_match_count"]) for row in sessions
            ),
            "unexpected_broker_order_count_total": sum(int(row["unexpected_broker_order_count"]) for row in sessions),
            "broker_activity_unmatched_count_total": sum(
                int(row["broker_activity_unmatched_count"]) for row in sessions
            ),
            "local_filled_order_without_activity_match_count_total": sum(
                int(row["local_filled_order_without_activity_match_count"]) for row in sessions
            ),
            "partial_fill_count_total": sum(int(row["partial_fill_count"]) for row in sessions),
            "ending_broker_position_count_total": sum(int(row["ending_broker_position_count"]) for row in sessions),
            "forced_exit_failure_count_total": sum(int(row["forced_exit_failure_count"]) for row in sessions),
            "known_trade_cleanup_count_total": sum(int(row["known_trade_cleanup_count"]) for row in sessions),
            "unexpected_position_cleanup_count_total": sum(
                int(row["unexpected_position_cleanup_count"]) for row in sessions
            ),
            "guardrail_manual_review_count_total": sum(int(row["guardrail_manual_review_count"]) for row in sessions),
            "completed_trade_count_delta_total": sum(abs(int(row["completed_trade_count_delta"])) for row in sessions),
            "realized_reconciliation_delta_abs_total": round_float(
                sum(float(row["realized_reconciliation_delta_abs"]) for row in sessions)
            ),
            "realized_reconciliation_delta_abs_mean": realized_reconciliation_delta_abs_mean,
            "broker_local_cashflow_delta_abs_total": round_float(sum(broker_local_cashflow_deltas)),
            "broker_local_cashflow_delta_abs_mean": broker_local_cashflow_delta_abs_mean,
            "broker_local_cashflow_delta_review_required_count": sum(
                1 for row in sessions if "broker_local_cashflow_delta" in row["review_required_reasons"]
            ),
        },
        "data_quality": {
            "missing_broker_order_audit_dates": missing_broker_order_audit_dates,
            "missing_broker_activity_audit_dates": missing_broker_activity_audit_dates,
            "missing_broker_cashflow_comparison_dates": missing_broker_cashflow_comparison_dates,
        },
        "sessions": sessions_sorted,
    }
    payload["findings"] = build_findings(payload["summary"], payload["data_quality"])

    json_path = report_dir / "session_reconciliation_registry.json"
    md_path = report_dir / "session_reconciliation_registry.md"
    csv_path = report_dir / "session_reconciliation_registry.csv"
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    write_markdown(md_path, payload)
    write_csv(csv_path, flatten_sessions_for_csv(sessions_sorted))
    print(json.dumps({"json_path": str(json_path), "markdown_path": str(md_path), "csv_path": str(csv_path)}, indent=2))


if __name__ == "__main__":
    main()
