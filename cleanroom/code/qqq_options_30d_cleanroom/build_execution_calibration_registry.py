from __future__ import annotations

import argparse
import csv
import json
import math
from collections import Counter, defaultdict
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
DEFAULT_REPORTS_ROOT = DEFAULT_RUNNER_REPO_ROOT / "reports" / "multi_ticker_portfolio"
DEFAULT_REPORT_DIR = REPO_ROOT / "docs" / "execution_calibration"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build a machine-readable execution calibration registry from paper-runner artifacts."
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


def percentile(values: list[float], pct: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    rank = (len(ordered) - 1) * pct
    low = math.floor(rank)
    high = math.ceil(rank)
    if low == high:
        return ordered[low]
    return ordered[low] + (ordered[high] - ordered[low]) * (rank - low)


def summarize_values(values: list[float]) -> dict[str, Any]:
    if not values:
        return {"count": 0}
    return {
        "count": len(values),
        "mean": round_float(sum(values) / len(values)),
        "median": round_float(percentile(values, 0.5)),
        "p90": round_float(percentile(values, 0.9)),
        "min": round_float(min(values)),
        "max": round_float(max(values)),
    }


def load_json_object(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def load_json_array(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    if not isinstance(payload, list):
        return []
    return [item for item in payload if isinstance(item, dict)]


def load_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        return [dict(row) for row in reader]


def infer_entry_bucket(minute_value: float | None) -> str:
    if minute_value is None:
        return "unknown"
    if minute_value <= 30:
        return "opening_0_30"
    if minute_value <= 90:
        return "opening_follow_through_31_90"
    if minute_value <= 210:
        return "midday_91_210"
    return "power_hour_211_plus"


def new_group() -> dict[str, Any]:
    return {
        "attempt_count": 0,
        "entry_fill_count": 0,
        "exit_fill_count": 0,
        "completed_trade_count": 0,
        "skipped_signal_count": 0,
        "entry_abs_slippage_pct_values": [],
        "entry_abs_slippage_values": [],
        "entry_slippage_values": [],
        "exit_abs_slippage_pct_values": [],
        "exit_abs_slippage_values": [],
        "exit_slippage_values": [],
        "net_pnl_values": [],
        "exit_reasons": Counter(),
    }


def update_group_from_attempt(group: dict[str, Any], row: dict[str, Any]) -> None:
    group["attempt_count"] += 1
    if str(row.get("signal_decision", "")).strip().lower() == "skipped":
        group["skipped_signal_count"] += 1
    if str(row.get("entry_status", "")).strip().lower() == "filled":
        group["entry_fill_count"] += 1
    if str(row.get("exit_status", "")).strip().lower() == "filled":
        group["exit_fill_count"] += 1

    entry_slippage = parse_float(row.get("entry_slippage"))
    if entry_slippage is not None:
        group["entry_slippage_values"].append(entry_slippage)
        group["entry_abs_slippage_values"].append(abs(entry_slippage))
        expected_entry = parse_float(row.get("expected_entry_fill_price"))
        if expected_entry not in (None, 0.0):
            group["entry_abs_slippage_pct_values"].append((abs(entry_slippage) / abs(expected_entry)) * 100.0)


def update_group_from_exit_result(group: dict[str, Any], row: dict[str, Any]) -> None:
    exit_slippage = parse_float(row.get("exit_slippage"))
    if exit_slippage is not None:
        group["exit_slippage_values"].append(exit_slippage)
        group["exit_abs_slippage_values"].append(abs(exit_slippage))
        expected_exit = parse_float(row.get("expected_exit_fill_price"))
        if expected_exit not in (None, 0.0):
            group["exit_abs_slippage_pct_values"].append((abs(exit_slippage) / abs(expected_exit)) * 100.0)


def update_group_from_completed(group: dict[str, Any], row: dict[str, Any]) -> None:
    group["completed_trade_count"] += 1
    pnl = parse_float(row.get("net_pnl"))
    if pnl is not None:
        group["net_pnl_values"].append(pnl)
    exit_reason = str(row.get("exit_reason", "")).strip() or "unknown"
    group["exit_reasons"][exit_reason] += 1


def total_from_summary(summary_payload: dict[str, Any]) -> float:
    count = int(summary_payload.get("count", 0) or 0)
    mean = parse_float(summary_payload.get("mean"))
    if count <= 0 or mean is None:
        return 0.0
    return count * mean


def top_counter_items(counter: Counter[str], top_n: int) -> dict[str, int]:
    return dict(sorted(counter.items(), key=lambda item: (-item[1], item[0]))[:top_n])


def finalize_group_rows(groups: dict[str, dict[str, Any]], key_name: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for key, group in groups.items():
        net_pnl = summarize_values(group["net_pnl_values"])
        rows.append(
            {
                key_name: key,
                "attempt_count": group["attempt_count"],
                "entry_fill_count": group["entry_fill_count"],
                "exit_fill_count": group["exit_fill_count"],
                "completed_trade_count": group["completed_trade_count"],
                "skipped_signal_count": group["skipped_signal_count"],
                "entry_slippage": summarize_values(group["entry_slippage_values"]),
                "entry_abs_slippage": summarize_values(group["entry_abs_slippage_values"]),
                "entry_abs_slippage_pct_of_expected": summarize_values(group["entry_abs_slippage_pct_values"]),
                "exit_slippage": summarize_values(group["exit_slippage_values"]),
                "exit_abs_slippage": summarize_values(group["exit_abs_slippage_values"]),
                "exit_abs_slippage_pct_of_expected": summarize_values(group["exit_abs_slippage_pct_values"]),
                "net_pnl": net_pnl,
                "net_pnl_total_estimate": round_float(total_from_summary(net_pnl)),
                "top_exit_reason": sorted(group["exit_reasons"].items(), key=lambda item: (-item[1], item[0]))[0][0]
                if group["exit_reasons"]
                else "",
                "exit_reason_counts": dict(sorted(group["exit_reasons"].items())),
            }
        )
    return sorted(
        rows,
        key=lambda row: (
            -int(row["completed_trade_count"]),
            -int(row["entry_fill_count"]),
            -int(row["attempt_count"]),
            str(row.get(key_name, "")),
        ),
    )


def flatten_rows_for_csv(category: str, key_name: str, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    flattened: list[dict[str, Any]] = []
    for row in rows:
        entry_pct = row.get("entry_abs_slippage_pct_of_expected", {})
        flattened.append(
            {
                "category": category,
                "name": row.get(key_name, ""),
                "attempt_count": row.get("attempt_count", 0),
                "entry_fill_count": row.get("entry_fill_count", 0),
                "exit_fill_count": row.get("exit_fill_count", 0),
                "completed_trade_count": row.get("completed_trade_count", 0),
                "skipped_signal_count": row.get("skipped_signal_count", 0),
                "entry_abs_slippage_pct_mean": entry_pct.get("mean"),
                "entry_abs_slippage_pct_median": entry_pct.get("median"),
                "exit_abs_slippage_pct_mean": (row.get("exit_abs_slippage_pct_of_expected") or {}).get("mean"),
                "exit_abs_slippage_pct_median": (row.get("exit_abs_slippage_pct_of_expected") or {}).get("median"),
                "net_pnl_total_estimate": row.get("net_pnl_total_estimate"),
                "top_exit_reason": row.get("top_exit_reason", ""),
            }
        )
    return flattened


def build_findings(payload: dict[str, Any]) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    summary = payload["summary"]
    data_quality = payload["data_quality"]
    broker_audit_sessions = int(summary.get("sessions_with_broker_order_audit", 0) or 0)
    broker_activity_audit_sessions = int(summary.get("sessions_with_broker_activity_audit", 0) or 0)
    broker_status_mismatch_count = int(summary.get("broker_status_mismatch_count_total", 0) or 0)
    broker_partial_fill_count = int(summary.get("broker_partially_filled_order_count_total", 0) or 0)
    unmatched_local_order_count = int(summary.get("local_order_without_broker_match_count_total", 0) or 0)
    ending_broker_position_count = int(summary.get("ending_broker_position_count_total", 0) or 0)
    broker_activity_unmatched_count = int(summary.get("broker_activity_unmatched_count_total", 0) or 0)
    local_filled_order_without_activity_match_count = int(
        summary.get("local_filled_order_without_activity_match_count_total", 0) or 0
    )
    broker_activity_partial_fill_count = int(summary.get("broker_activity_partial_fill_count_total", 0) or 0)

    if data_quality["exit_slippage_observations"] == 0:
        findings.append(
            {
                "priority": "high",
                "type": "telemetry_gap",
                "message": "Exit slippage is still not captured reliably in the condensed runner artifacts. Entry-side calibration is actionable today, but exit-side execution modeling should remain conservative until expected exit pricing and exit slippage are logged consistently.",
            }
        )

    if summary["severe_loss_flatten_session_count"] > 0:
        findings.append(
            {
                "priority": "high",
                "type": "guardrail_pressure",
                "message": f"Severe-loss flatten triggered in {summary['severe_loss_flatten_session_count']} session(s). That is a clear signal to pressure-test aggressive opening debit exposure and portfolio loss caps.",
            }
        )

    if broker_audit_sessions == 0:
        findings.append(
            {
                "priority": "medium",
                "type": "broker_audit_gap",
                "message": "Session-level broker order audit artifacts are not present yet in the execution sample. Entry-side calibration is useful today, but combo-exit and reconciliation policy should still stay conservative until upgraded session bundles accumulate.",
            }
        )

    if broker_activity_audit_sessions == 0:
        findings.append(
            {
                "priority": "medium",
                "type": "broker_activity_audit_gap",
                "message": "Session-level broker account-activity audit artifacts are not present yet in the execution sample. That means the control plane still lacks a second source of truth for fills beyond local events and broker order snapshots.",
            }
        )

    if broker_status_mismatch_count > 0 or unmatched_local_order_count > 0 or ending_broker_position_count > 0:
        findings.append(
            {
                "priority": "high",
                "type": "reconciliation_pressure",
                "message": "Broker/runtime reconciliation pressure is visible in the current execution sample. Session summaries show "
                f"`{broker_status_mismatch_count}` broker-status mismatches, `{unmatched_local_order_count}` local order references without broker matches, and `{ending_broker_position_count}` ending broker positions. Combo-heavy challengers should stay on tighter review until these counts stabilize.",
            }
        )

    if broker_activity_unmatched_count > 0 or local_filled_order_without_activity_match_count > 0:
        findings.append(
            {
                "priority": "high",
                "type": "activity_reconciliation_pressure",
                "message": "Broker account activity does not line up cleanly with local filled-order references yet. Session summaries show "
                f"`{broker_activity_unmatched_count}` broker activity row(s) without a local match and `{local_filled_order_without_activity_match_count}` local filled order(s) without an activity match. Until this stabilizes, research should keep entry/exit realism conservative and avoid over-trusting combo-heavy challengers.",
            }
        )

    if broker_partial_fill_count > 0 or broker_activity_partial_fill_count > 0:
        findings.append(
            {
                "priority": "medium",
                "type": "partial_fill_pressure",
                "message": "Execution telemetry captured partial-fill pressure in upgraded session artifacts. "
                f"Broker orders show `{broker_partial_fill_count}` partially filled order(s), and broker activities show `{broker_activity_partial_fill_count}` partial fill activity row(s). That is a useful warning to keep multi-leg cleanup and size-cap assumptions conservative, especially in opening-window profiles.",
            }
        )

    adverse_pct = (summary.get("event_entry_adverse_slippage_pct") or {}).get("mean")
    if adverse_pct is not None and adverse_pct >= 2.0:
        findings.append(
            {
                "priority": "medium",
                "type": "execution_friction",
                "message": f"Event-level adverse entry slippage averaged {adverse_pct:.2f}% of expected fill. Challenger backtests should use stronger entry-fill penalties until this comes down.",
            }
        )

    worst_strategies = sorted(
        [row for row in payload["by_strategy"] if row.get("completed_trade_count", 0) > 0],
        key=lambda row: (float(row.get("net_pnl_total_estimate") or 0.0), str(row.get("strategy_name", ""))),
    )[:3]
    if worst_strategies:
        labels = ", ".join(
            f"{row['strategy_name']} ({float(row.get('net_pnl_total_estimate') or 0.0):.2f})" for row in worst_strategies
        )
        findings.append(
            {
                "priority": "medium",
                "type": "loss_cluster",
                "message": f"Losses are concentrated in a small set of strategies: {labels}. Those are the best immediate candidates for tighter calibration or challenger replacement pressure.",
            }
        )

    return findings


def build_payload(*, runner_repo_root: Path, reports_root: Path, top_n: int) -> dict[str, Any]:
    runs_root = reports_root / "runs"
    state_root = reports_root / "state"
    run_dirs = sorted([path for path in runs_root.iterdir() if path.is_dir()], key=lambda path: path.name) if runs_root.exists() else []

    by_ticker: defaultdict[str, dict[str, Any]] = defaultdict(new_group)
    by_strategy: defaultdict[str, dict[str, Any]] = defaultdict(new_group)
    by_regime: defaultdict[str, dict[str, Any]] = defaultdict(new_group)
    by_timing_profile: defaultdict[str, dict[str, Any]] = defaultdict(new_group)
    by_signal_name: defaultdict[str, dict[str, Any]] = defaultdict(new_group)
    by_entry_bucket: defaultdict[str, dict[str, Any]] = defaultdict(new_group)
    by_exit_reason: defaultdict[str, dict[str, Any]] = defaultdict(new_group)

    summary_counter = Counter()
    signal_decisions = Counter()
    final_statuses = Counter()
    entry_statuses = Counter()
    exit_statuses = Counter()
    startup_statuses = Counter()
    block_reasons = Counter()
    exit_reasons = Counter()
    event_types = Counter()
    guardrail_reasons = Counter()

    entry_slippage_values: list[float] = []
    entry_abs_slippage_values: list[float] = []
    entry_abs_slippage_pct_values: list[float] = []
    event_entry_adverse_slippage_pct_values: list[float] = []
    exit_slippage_values: list[float] = []
    exit_abs_slippage_values: list[float] = []
    exit_abs_slippage_pct_values: list[float] = []

    sessions: list[dict[str, Any]] = []
    missing_summary_dates: list[str] = []
    missing_reconciliation_dates: list[str] = []
    missing_completed_trade_dates: list[str] = []
    missing_state_dates: list[str] = []
    missing_event_dates: list[str] = []
    missing_broker_order_audit_dates: list[str] = []
    missing_broker_activity_audit_dates: list[str] = []
    missing_ending_broker_position_dates: list[str] = []

    severe_loss_flatten_session_count = 0
    attempt_context: dict[str, dict[str, str]] = {}

    for run_dir in run_dirs:
        trade_date = run_dir.name
        summary_path = run_dir / "multi_ticker_portfolio_session_summary.json"
        reconciliation_path = run_dir / "multi_ticker_portfolio_session_summary_trade_reconciliation.csv"
        completed_path = run_dir / "multi_ticker_portfolio_session_summary_completed_trades.csv"
        events_path = run_dir / "trade_reconciliation_events.json"
        broker_order_audit_path = run_dir / "multi_ticker_portfolio_session_summary_broker_order_audit.csv"
        broker_activity_audit_path = run_dir / "multi_ticker_portfolio_session_summary_broker_account_activities.csv"
        ending_broker_positions_path = run_dir / "multi_ticker_portfolio_session_summary_ending_broker_positions.csv"
        state_path = state_root / f"session_{trade_date}.json"

        summary_payload = load_json_object(summary_path)
        reconciliation_rows = load_csv_rows(reconciliation_path)
        completed_rows = load_csv_rows(completed_path)
        event_rows = load_json_array(events_path)
        broker_order_audit_rows = load_csv_rows(broker_order_audit_path)
        broker_activity_audit_rows = load_csv_rows(broker_activity_audit_path)
        ending_broker_position_rows = load_csv_rows(ending_broker_positions_path)
        state_payload = load_json_object(state_path)

        if not summary_payload:
            missing_summary_dates.append(trade_date)
        if not reconciliation_rows:
            missing_reconciliation_dates.append(trade_date)
        if not completed_rows:
            missing_completed_trade_dates.append(trade_date)
        if not state_payload:
            missing_state_dates.append(trade_date)
        if not event_rows:
            missing_event_dates.append(trade_date)
        if "broker_order_audit_available" in summary_payload and not broker_order_audit_path.exists():
            missing_broker_order_audit_dates.append(trade_date)
        if "broker_activity_audit_available" in summary_payload and not broker_activity_audit_path.exists():
            missing_broker_activity_audit_dates.append(trade_date)
        if "ending_broker_position_count" in summary_payload and not ending_broker_positions_path.exists():
            missing_ending_broker_position_dates.append(trade_date)

        if summary_payload:
            startup_statuses[str(summary_payload.get("startup_check_status", "")).strip() or "unknown"] += 1
            block_reason = str(summary_payload.get("block_reason", "")).strip()
            if block_reason:
                block_reasons[block_reason] += 1
            guardrail_reason_payload = summary_payload.get("guardrail_reason_count")
            if isinstance(guardrail_reason_payload, dict):
                guardrail_reasons.update(
                    {str(key): int(value) for key, value in guardrail_reason_payload.items()}
                )
            for key in (
                "completed_trade_count",
                "entry_fill_count",
                "exit_fill_count",
                "signal_attempt_count",
                "skipped_signal_count",
                "eligible_signal_count",
                "guardrail_fire_count",
                "guardrail_auto_fixed_count",
                "guardrail_manual_review_count",
            ):
                summary_counter[key] += parse_int(summary_payload.get(key)) or 0

        alerts = list(state_payload.get("alerts") or [])
        if any("severe_loss_flatten_all triggered" in str(alert.get("message", "")).lower() for alert in alerts if isinstance(alert, dict)):
            severe_loss_flatten_session_count += 1

        for event in event_rows:
            event_type = str(event.get("event_type", "")).strip() or "unknown"
            event_types[event_type] += 1
            if event_type == "entry_result":
                adverse_fraction = parse_float(event.get("entry_adverse_slippage_fraction"))
                if adverse_fraction is not None:
                    event_entry_adverse_slippage_pct_values.append(adverse_fraction * 100.0)
            elif event_type == "exit_result":
                exit_slippage = parse_float(event.get("exit_slippage"))
                if exit_slippage is not None:
                    exit_slippage_values.append(exit_slippage)
                    exit_abs_slippage_values.append(abs(exit_slippage))
                    expected_exit = parse_float(event.get("expected_exit_fill_price"))
                    if expected_exit not in (None, 0.0):
                        exit_abs_slippage_pct_values.append((abs(exit_slippage) / abs(expected_exit)) * 100.0)

                ticker = str(event.get("underlying_symbol", "")).strip().upper() or "unknown"
                strategy = str(event.get("strategy_name", "")).strip() or "unknown"
                regime = str(event.get("regime", "")).strip() or "unknown"
                timing_profile = str(event.get("timing_profile", "")).strip() or "unknown"
                signal_name = str(event.get("signal_name", "")).strip() or "unknown"
                entry_bucket = infer_entry_bucket(parse_float(event.get("entry_minute") or event.get("signal_minute")))

                update_group_from_exit_result(by_ticker[ticker], event)
                update_group_from_exit_result(by_strategy[strategy], event)
                update_group_from_exit_result(by_regime[regime], event)
                update_group_from_exit_result(by_timing_profile[timing_profile], event)
                update_group_from_exit_result(by_signal_name[signal_name], event)
                update_group_from_exit_result(by_entry_bucket[entry_bucket], event)

        for row in reconciliation_rows:
            attempt_id = str(row.get("attempt_id", "")).strip()
            attempt_context[attempt_id] = {
                "signal_name": str(row.get("signal_name", "")).strip() or "unknown",
                "timing_profile": str(row.get("timing_profile", "")).strip() or "unknown",
                "entry_bucket": infer_entry_bucket(parse_float(row.get("signal_minute"))),
            }
            signal_decisions[str(row.get("signal_decision", "")).strip() or "unknown"] += 1
            final_statuses[str(row.get("final_status", "")).strip() or "unknown"] += 1
            entry_statuses[str(row.get("entry_status", "")).strip() or "unknown"] += 1
            exit_statuses[str(row.get("exit_status", "")).strip() or "unknown"] += 1

            entry_slippage = parse_float(row.get("entry_slippage"))
            if entry_slippage is not None:
                entry_slippage_values.append(entry_slippage)
                entry_abs_slippage_values.append(abs(entry_slippage))
                expected_entry = parse_float(row.get("expected_entry_fill_price"))
                if expected_entry not in (None, 0.0):
                    entry_abs_slippage_pct_values.append((abs(entry_slippage) / abs(expected_entry)) * 100.0)

            ticker = str(row.get("underlying_symbol", "")).strip().upper() or "unknown"
            strategy = str(row.get("strategy_name", "")).strip() or "unknown"
            regime = str(row.get("regime", "")).strip() or "unknown"
            timing_profile = str(row.get("timing_profile", "")).strip() or "unknown"
            signal_name = str(row.get("signal_name", "")).strip() or "unknown"
            entry_bucket = infer_entry_bucket(parse_float(row.get("signal_minute")))

            update_group_from_attempt(by_ticker[ticker], row)
            update_group_from_attempt(by_strategy[strategy], row)
            update_group_from_attempt(by_regime[regime], row)
            update_group_from_attempt(by_timing_profile[timing_profile], row)
            update_group_from_attempt(by_signal_name[signal_name], row)
            update_group_from_attempt(by_entry_bucket[entry_bucket], row)

        for row in completed_rows:
            exit_reason = str(row.get("exit_reason", "")).strip() or "unknown"
            exit_reasons[exit_reason] += 1
            attempt_id = str(row.get("entry_attempt_id", "")).strip()
            context = attempt_context.get(
                attempt_id,
                {
                    "signal_name": "unknown",
                    "timing_profile": "unknown",
                    "entry_bucket": infer_entry_bucket(parse_float(row.get("entry_minute"))),
                },
            )

            ticker = str(row.get("underlying_symbol", "")).strip().upper() or "unknown"
            strategy = str(row.get("strategy_name", "")).strip() or "unknown"
            regime = str(row.get("regime", "")).strip() or "unknown"

            update_group_from_completed(by_ticker[ticker], row)
            update_group_from_completed(by_strategy[strategy], row)
            update_group_from_completed(by_regime[regime], row)
            update_group_from_completed(by_timing_profile[context["timing_profile"]], row)
            update_group_from_completed(by_signal_name[context["signal_name"]], row)
            update_group_from_completed(by_entry_bucket[context["entry_bucket"]], row)
            update_group_from_completed(by_exit_reason[exit_reason], row)

        sessions.append(
            {
                "trade_date": trade_date,
                "startup_check_status": str(summary_payload.get("startup_check_status", "")).strip()
                or str(state_payload.get("startup_check_status", "")).strip(),
                "blocked_new_entries": bool(summary_payload.get("blocked_new_entries", state_payload.get("blocked_new_entries", False))),
                "block_reason": str(summary_payload.get("block_reason", "")).strip(),
                "completed_trade_count": len(completed_rows),
                "reconciliation_row_count": len(reconciliation_rows),
                "event_row_count": len(event_rows),
                "broker_order_audit_available": bool(summary_payload.get("broker_order_audit_available", False)),
                "broker_order_count": parse_int(summary_payload.get("broker_order_count"))
                or len(broker_order_audit_rows),
                "broker_activity_audit_available": bool(summary_payload.get("broker_activity_audit_available", False)),
                "broker_activity_count": parse_int(summary_payload.get("broker_activity_count"))
                or len(broker_activity_audit_rows),
                "broker_fill_activity_count": parse_int(summary_payload.get("broker_fill_activity_count"))
                or len(broker_activity_audit_rows),
                "broker_activity_partial_fill_count": parse_int(summary_payload.get("broker_partial_fill_activity_count"))
                or sum(
                    1
                    for row in broker_activity_audit_rows
                    if str(row.get("fill_type", "")).strip().lower() == "partial_fill"
                ),
                "broker_activity_matched_count": parse_int(summary_payload.get("broker_activity_matched_count"))
                or sum(
                    1
                    for row in broker_activity_audit_rows
                    if str(row.get("matched_to_local", "")).strip().lower() == "true"
                ),
                "broker_activity_unmatched_count": parse_int(summary_payload.get("broker_activity_unmatched_count"))
                or sum(
                    1
                    for row in broker_activity_audit_rows
                    if str(row.get("matched_to_local", "")).strip().lower() == "false"
                ),
                "broker_multileg_order_count": parse_int(summary_payload.get("broker_multileg_order_count"))
                or 0,
                "broker_partially_filled_order_count": parse_int(summary_payload.get("broker_partially_filled_order_count"))
                or 0,
                "broker_status_mismatch_count": parse_int(summary_payload.get("broker_status_mismatch_count"))
                or 0,
                "local_order_without_broker_match_count": parse_int(
                    summary_payload.get("local_order_without_broker_match_count")
                )
                or 0,
                "local_filled_order_without_activity_match_count": parse_int(
                    summary_payload.get("local_filled_order_without_activity_match_count")
                )
                or 0,
                "ending_broker_position_count": parse_int(summary_payload.get("ending_broker_position_count"))
                or len(ending_broker_position_rows),
                "guardrail_fire_count": parse_int(summary_payload.get("guardrail_fire_count")) or 0,
                "entry_fill_count": parse_int(summary_payload.get("entry_fill_count")) or 0,
                "exit_fill_count": parse_int(summary_payload.get("exit_fill_count")) or 0,
                "net_pnl": parse_float(summary_payload.get("net_pnl")),
                "severe_loss_flatten_triggered": any(
                    "severe_loss_flatten_all triggered" in str(alert.get("message", "")).lower()
                    for alert in alerts
                    if isinstance(alert, dict)
                ),
            }
        )

    payload = {
        "generated_at": datetime.now().isoformat(),
        "runner_repo_root": str(runner_repo_root),
        "reports_root": str(reports_root),
        "top_n": top_n,
        "summary": {
            "sessions_scanned": len(run_dirs),
            "sessions_with_summary": len(run_dirs) - len(missing_summary_dates),
            "sessions_with_reconciliation": len(run_dirs) - len(missing_reconciliation_dates),
            "sessions_with_completed_trades": sum(1 for row in sessions if row["completed_trade_count"] > 0),
            "sessions_with_event_logs": len(run_dirs) - len(missing_event_dates),
            "sessions_with_broker_order_audit": sum(1 for row in sessions if row["broker_order_audit_available"]),
            "sessions_with_broker_activity_audit": sum(1 for row in sessions if row["broker_activity_audit_available"]),
            "date_span": {"start": run_dirs[0].name if run_dirs else "", "end": run_dirs[-1].name if run_dirs else ""},
            "completed_trade_count": sum(int(row["completed_trade_count"]) for row in sessions),
            "reconciliation_row_count": sum(int(row["reconciliation_row_count"]) for row in sessions),
            "event_row_count": sum(int(row["event_row_count"]) for row in sessions),
            "broker_order_count_total": sum(int(row["broker_order_count"]) for row in sessions),
            "broker_activity_count_total": sum(int(row["broker_activity_count"]) for row in sessions),
            "broker_fill_activity_count_total": sum(int(row["broker_fill_activity_count"]) for row in sessions),
            "broker_activity_partial_fill_count_total": sum(
                int(row["broker_activity_partial_fill_count"]) for row in sessions
            ),
            "broker_activity_matched_count_total": sum(int(row["broker_activity_matched_count"]) for row in sessions),
            "broker_activity_unmatched_count_total": sum(
                int(row["broker_activity_unmatched_count"]) for row in sessions
            ),
            "broker_multileg_order_count_total": sum(int(row["broker_multileg_order_count"]) for row in sessions),
            "broker_partially_filled_order_count_total": sum(
                int(row["broker_partially_filled_order_count"]) for row in sessions
            ),
            "broker_status_mismatch_count_total": sum(int(row["broker_status_mismatch_count"]) for row in sessions),
            "local_order_without_broker_match_count_total": sum(
                int(row["local_order_without_broker_match_count"]) for row in sessions
            ),
            "local_filled_order_without_activity_match_count_total": sum(
                int(row["local_filled_order_without_activity_match_count"]) for row in sessions
            ),
            "ending_broker_position_count_total": sum(int(row["ending_broker_position_count"]) for row in sessions),
            "entry_fill_count": sum(int(row["entry_fill_count"]) for row in sessions),
            "exit_fill_count": sum(int(row["exit_fill_count"]) for row in sessions),
            "signal_attempt_count": summary_counter["signal_attempt_count"],
            "skipped_signal_count": summary_counter["skipped_signal_count"],
            "guardrail_fire_count_total": summary_counter["guardrail_fire_count"],
            "guardrail_auto_fixed_count_total": summary_counter["guardrail_auto_fixed_count"],
            "guardrail_manual_review_count_total": summary_counter["guardrail_manual_review_count"],
            "severe_loss_flatten_session_count": severe_loss_flatten_session_count,
            "severe_loss_flatten_trade_count": int(exit_reasons.get("severe_loss_flatten_all", 0)),
            "entry_slippage": summarize_values(entry_slippage_values),
            "entry_abs_slippage": summarize_values(entry_abs_slippage_values),
            "entry_abs_slippage_pct_of_expected": summarize_values(entry_abs_slippage_pct_values),
            "exit_slippage": summarize_values(exit_slippage_values),
            "exit_abs_slippage": summarize_values(exit_abs_slippage_values),
            "exit_abs_slippage_pct_of_expected": summarize_values(exit_abs_slippage_pct_values),
            "event_entry_adverse_slippage_pct": summarize_values(event_entry_adverse_slippage_pct_values),
            "signal_decisions": dict(sorted(signal_decisions.items())),
            "final_statuses": dict(sorted(final_statuses.items())),
            "entry_statuses": dict(sorted(entry_statuses.items())),
            "exit_statuses": dict(sorted(exit_statuses.items())),
            "startup_check_statuses": dict(sorted(startup_statuses.items())),
            "block_reasons": dict(sorted(block_reasons.items())),
            "exit_reasons": dict(sorted(exit_reasons.items())),
            "event_types": dict(sorted(event_types.items())),
            "guardrail_reasons": dict(sorted(guardrail_reasons.items())),
        },
        "data_quality": {
            "entry_slippage_observations": len(entry_slippage_values),
            "exit_slippage_observations": len(exit_slippage_values),
            "event_entry_adverse_slippage_observations": len(event_entry_adverse_slippage_pct_values),
            "missing_summary_dates": missing_summary_dates,
            "missing_reconciliation_dates": missing_reconciliation_dates,
            "missing_completed_trade_dates": missing_completed_trade_dates,
            "missing_state_dates": missing_state_dates,
            "missing_event_dates": missing_event_dates,
            "missing_broker_order_audit_dates": missing_broker_order_audit_dates,
            "missing_broker_activity_audit_dates": missing_broker_activity_audit_dates,
            "missing_ending_broker_position_dates": missing_ending_broker_position_dates,
        },
        "sessions": sorted(sessions, key=lambda row: row["trade_date"]),
        "by_ticker": finalize_group_rows(by_ticker, "ticker"),
        "by_strategy": finalize_group_rows(by_strategy, "strategy_name"),
        "by_regime": finalize_group_rows(by_regime, "regime"),
        "by_timing_profile": finalize_group_rows(by_timing_profile, "timing_profile"),
        "by_signal_name": finalize_group_rows(by_signal_name, "signal_name"),
        "by_entry_bucket": finalize_group_rows(by_entry_bucket, "entry_bucket"),
        "by_exit_reason": finalize_group_rows(by_exit_reason, "exit_reason"),
    }
    payload["calibration_findings"] = build_findings(payload)
    return payload


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def write_csv(path: Path, payload: dict[str, Any]) -> None:
    rows: list[dict[str, Any]] = []
    rows.extend(flatten_rows_for_csv("ticker", "ticker", payload["by_ticker"]))
    rows.extend(flatten_rows_for_csv("strategy", "strategy_name", payload["by_strategy"]))
    rows.extend(flatten_rows_for_csv("regime", "regime", payload["by_regime"]))
    rows.extend(flatten_rows_for_csv("timing_profile", "timing_profile", payload["by_timing_profile"]))
    rows.extend(flatten_rows_for_csv("signal_name", "signal_name", payload["by_signal_name"]))
    rows.extend(flatten_rows_for_csv("entry_bucket", "entry_bucket", payload["by_entry_bucket"]))
    rows.extend(flatten_rows_for_csv("exit_reason", "exit_reason", payload["by_exit_reason"]))

    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames = sorted({key for row in rows for key in row.keys()})
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    summary = payload["summary"]
    data_quality = payload["data_quality"]
    top_n = int(payload["top_n"])

    def top_loss_rows() -> list[str]:
        rows = sorted(
            [row for row in payload["by_strategy"] if row.get("completed_trade_count", 0) > 0],
            key=lambda row: (float(row.get("net_pnl_total_estimate") or 0.0), str(row.get("strategy_name", ""))),
        )
        lines: list[str] = []
        for row in rows[:top_n]:
            lines.append(
                f"- `{row['strategy_name']}`: completed trades `{row['completed_trade_count']}`, estimated total net PnL `{float(row.get('net_pnl_total_estimate') or 0.0):.2f}`, top exit reason `{row.get('top_exit_reason') or 'n/a'}`"
            )
        return lines

    def top_slippage_rows() -> list[str]:
        rows = sorted(
            [
                row
                for row in payload["by_ticker"]
                if (row.get("entry_abs_slippage_pct_of_expected") or {}).get("count", 0) > 0
            ],
            key=lambda row: (
                -float((row.get("entry_abs_slippage_pct_of_expected") or {}).get("mean") or 0.0),
                -int(row.get("entry_fill_count", 0)),
                str(row.get("ticker", "")),
            ),
        )
        lines: list[str] = []
        for row in rows[:top_n]:
            lines.append(
                f"- `{row['ticker']}`: entry fills `{row['entry_fill_count']}`, mean absolute entry slippage `{(row.get('entry_abs_slippage_pct_of_expected') or {}).get('mean', 'n/a')}`% of expected, completed trades `{row['completed_trade_count']}`"
            )
        return lines

    lines: list[str] = []
    lines.append("# Execution Calibration Registry")
    lines.append("")
    lines.append("This registry is the control-plane source of truth for what the paper runner has actually experienced in fills, exits, loss clusters, and guardrail pressure.")
    lines.append("")
    lines.append("## Sources")
    lines.append("")
    lines.append(f"- Runner repo root: `{payload['runner_repo_root']}`")
    lines.append(f"- Reports root: `{payload['reports_root']}`")
    lines.append(f"- Sessions scanned: `{summary['sessions_scanned']}`")
    lines.append(f"- Date span: `{summary['date_span']['start']}` -> `{summary['date_span']['end']}`")
    lines.append("")
    lines.append("## Headline Calibration Summary")
    lines.append("")
    lines.append(f"- Completed trades: `{summary['completed_trade_count']}`")
    lines.append(f"- Reconciliation attempts: `{summary['reconciliation_row_count']}`")
    lines.append(f"- Event rows: `{summary['event_row_count']}`")
    lines.append(f"- Sessions with broker-order audit: `{summary['sessions_with_broker_order_audit']}`")
    lines.append(f"- Sessions with broker-activity audit: `{summary['sessions_with_broker_activity_audit']}`")
    lines.append(f"- Broker orders audited: `{summary['broker_order_count_total']}`")
    lines.append(f"- Broker activities audited: `{summary['broker_activity_count_total']}`")
    lines.append(f"- Broker activity unmatched rows: `{summary['broker_activity_unmatched_count_total']}`")
    lines.append(f"- Broker status mismatches: `{summary['broker_status_mismatch_count_total']}`")
    lines.append(f"- Local orders without broker match: `{summary['local_order_without_broker_match_count_total']}`")
    lines.append(f"- Local filled orders without activity match: `{summary['local_filled_order_without_activity_match_count_total']}`")
    lines.append(f"- Ending broker positions: `{summary['ending_broker_position_count_total']}`")
    lines.append(f"- Entry fills: `{summary['entry_fill_count']}`")
    lines.append(f"- Exit fills: `{summary['exit_fill_count']}`")
    lines.append(f"- Guardrail fires: `{summary['guardrail_fire_count_total']}`")
    lines.append(f"- Severe-loss flatten sessions: `{summary['severe_loss_flatten_session_count']}`")
    lines.append(f"- Mean absolute entry slippage vs expected: `{(summary['entry_abs_slippage_pct_of_expected'] or {}).get('mean', 'n/a')}`%")
    lines.append(f"- Mean absolute exit slippage vs expected: `{(summary['exit_abs_slippage_pct_of_expected'] or {}).get('mean', 'n/a')}`%")
    lines.append(f"- Mean event-level adverse entry slippage vs expected: `{(summary['event_entry_adverse_slippage_pct'] or {}).get('mean', 'n/a')}`%")
    lines.append("")
    lines.append("## Institutional Findings")
    lines.append("")
    for finding in payload["calibration_findings"]:
        lines.append(f"- `{finding['priority']}` `{finding['type']}`: {finding['message']}")
    if not payload["calibration_findings"]:
        lines.append("- No special calibration findings were generated.")
    lines.append("")
    lines.append(f"## Top {top_n} Entry Slippage Clusters By Ticker")
    lines.append("")
    lines.extend(top_slippage_rows() or ["- No ticker-level entry slippage observations yet."])
    lines.append("")
    lines.append(f"## Top {top_n} Loss Clusters By Strategy")
    lines.append("")
    lines.extend(top_loss_rows() or ["- No strategy-level loss clusters yet."])
    lines.append("")
    lines.append("## Session Health")
    lines.append("")
    for row in payload["sessions"]:
        lines.append(
            f"- `{row['trade_date']}`: startup `{row['startup_check_status'] or 'unknown'}`, completed trades `{row['completed_trade_count']}`, broker-activity rows `{row['broker_activity_count']}`, guardrail fires `{row['guardrail_fire_count']}`, broker mismatches `{row['broker_status_mismatch_count']}`, unmatched local orders `{row['local_order_without_broker_match_count']}`, unmatched broker activities `{row['broker_activity_unmatched_count']}`, ending broker positions `{row['ending_broker_position_count']}`, blocked new entries `{str(bool(row['blocked_new_entries'])).lower()}`, severe-loss flatten `{str(bool(row['severe_loss_flatten_triggered'])).lower()}`"
        )
    if not payload["sessions"]:
        lines.append("- No session artifacts were found.")
    lines.append("")
    lines.append("## Data Quality")
    lines.append("")
    lines.append(f"- Missing summary dates: `{', '.join(data_quality['missing_summary_dates']) or 'none'}`")
    lines.append(f"- Missing reconciliation dates: `{', '.join(data_quality['missing_reconciliation_dates']) or 'none'}`")
    lines.append(f"- Missing completed-trade dates: `{', '.join(data_quality['missing_completed_trade_dates']) or 'none'}`")
    lines.append(f"- Missing state dates: `{', '.join(data_quality['missing_state_dates']) or 'none'}`")
    lines.append(f"- Missing event-log dates: `{', '.join(data_quality['missing_event_dates']) or 'none'}`")
    lines.append(f"- Missing broker-order audit dates: `{', '.join(data_quality['missing_broker_order_audit_dates']) or 'none'}`")
    lines.append(f"- Missing broker-activity audit dates: `{', '.join(data_quality['missing_broker_activity_audit_dates']) or 'none'}`")
    lines.append(f"- Missing ending-broker-position dates: `{', '.join(data_quality['missing_ending_broker_position_dates']) or 'none'}`")
    lines.append("- Current runner telemetry is materially stronger on entry-side calibration than exit-side slippage calibration.")
    lines.append("")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = build_parser().parse_args()
    runner_repo_root = Path(args.runner_repo_root).resolve()
    reports_root = Path(args.reports_root).resolve()
    report_dir = Path(args.report_dir).resolve()
    report_dir.mkdir(parents=True, exist_ok=True)

    payload = build_payload(runner_repo_root=runner_repo_root, reports_root=reports_root, top_n=int(args.top_n))
    write_json(report_dir / "execution_calibration_registry.json", payload)
    write_csv(report_dir / "execution_calibration_registry.csv", payload)
    write_markdown(report_dir / "execution_calibration_registry.md", payload)
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
