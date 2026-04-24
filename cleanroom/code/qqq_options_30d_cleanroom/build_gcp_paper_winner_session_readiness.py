from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[2]
DEFAULT_REPORT_DIR = REPO_ROOT / "docs" / "gcp_foundation"
DEFAULT_RUNTIME_ROOT = REPO_ROOT.parent / "codexalpaca_runtime" / "multi_ticker_portfolio_live"
DEFAULT_GCS_PREFIX = "gs://codexalpaca-control-us/gcp_foundation"
DEFAULT_MIN_NET_PNL = 200.0
DEFAULT_TARGET_QUALIFIED_WINNERS = 20


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build the paper winner-session readiness packet for live-trading confidence tracking."
    )
    parser.add_argument("--runtime-root", default=str(DEFAULT_RUNTIME_ROOT))
    parser.add_argument("--report-dir", default=str(DEFAULT_REPORT_DIR))
    parser.add_argument("--gcs-prefix", default=DEFAULT_GCS_PREFIX)
    parser.add_argument("--min-net-pnl", type=float, default=DEFAULT_MIN_NET_PNL)
    parser.add_argument("--target-qualified-winners", type=int, default=DEFAULT_TARGET_QUALIFIED_WINNERS)
    return parser


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _bool(value: Any) -> bool:
    return bool(value)


def _evidence_summary(runtime_root: Path, trade_date: str) -> dict[str, Any]:
    payload = read_json(runtime_root / "session_evidence" / f"session_evidence_contract_{trade_date}.json")
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    return summary if isinstance(summary, dict) else {}


def _teaching_summary(runtime_root: Path, trade_date: str) -> dict[str, Any]:
    payload = read_json(runtime_root / "session_teaching" / f"session_teaching_gate_{trade_date}.json")
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    return summary if isinstance(summary, dict) else {}


def _session_summary_path(run_dir: Path) -> Path:
    return run_dir / "multi_ticker_portfolio_session_summary.json"


def _classify_session(
    *,
    runtime_root: Path,
    trade_date: str,
    session_summary: dict[str, Any],
    min_net_pnl: float,
) -> dict[str, Any]:
    evidence = _evidence_summary(runtime_root, trade_date)
    teaching = _teaching_summary(runtime_root, trade_date)
    economics = session_summary.get("broker_local_economics_comparison")
    if not isinstance(economics, dict):
        economics = {}
    ending_positions = session_summary.get("ending_broker_positions")
    if not isinstance(ending_positions, dict):
        ending_positions = {}

    net_pnl = _float(session_summary.get("net_pnl"))
    block_reason = str(session_summary.get("block_reason") or "")
    raw_winner = net_pnl >= min_net_pnl
    evidence_status = str(evidence.get("status") or "missing")
    teaching_status = str(teaching.get("status") or "missing")
    automatic_learning_allowed = bool(teaching.get("automatic_learning_allowed"))
    open_trade_count = _int(session_summary.get("open_reconciled_trade_count"))
    ending_position_count = _int(ending_positions.get("position_count"))
    shutdown_reconciled = _bool(session_summary.get("shutdown_reconciled"))
    economics_diff = _float(economics.get("max_abs_cashflow_diff"))
    economics_tolerance = _float(economics.get("tolerance_dollars"), 0.05)
    severe_loss = "severe_loss" in block_reason

    disqualifiers: list[str] = []
    if not raw_winner:
        disqualifiers.append("net_pnl_below_winner_threshold")
    if not shutdown_reconciled:
        disqualifiers.append("shutdown_not_reconciled")
    if open_trade_count != 0:
        disqualifiers.append("open_trades_remaining")
    if ending_position_count != 0:
        disqualifiers.append("broker_positions_not_flat")
    if evidence_status != "ok":
        disqualifiers.append(f"evidence_status_{evidence_status}")
    if teaching_status != "ok" or not automatic_learning_allowed:
        disqualifiers.append("teaching_gate_not_ok")
    if economics_diff > economics_tolerance:
        disqualifiers.append("broker_local_economics_drift")
    if severe_loss:
        disqualifiers.append("severe_loss_incident")

    qualified_winner = raw_winner and not disqualifiers
    return {
        "trade_date": trade_date,
        "net_pnl": net_pnl,
        "raw_winner": raw_winner,
        "qualified_winner": qualified_winner,
        "completed_trade_count": _int(session_summary.get("completed_trade_count")),
        "open_trade_count": open_trade_count,
        "shutdown_reconciled": shutdown_reconciled,
        "ending_broker_position_count": ending_position_count,
        "evidence_status": evidence_status,
        "teaching_gate_status": teaching_status,
        "automatic_learning_allowed": automatic_learning_allowed,
        "economics_max_abs_cashflow_diff": economics_diff,
        "economics_tolerance": economics_tolerance,
        "block_reason": block_reason,
        "disqualifiers": disqualifiers,
    }


def build_payload(
    *,
    runtime_root: Path,
    report_dir: Path,
    gcs_prefix: str,
    min_net_pnl: float,
    target_qualified_winners: int,
) -> dict[str, Any]:
    runs_root = runtime_root / "runs"
    sessions: list[dict[str, Any]] = []
    if runs_root.exists():
        for run_dir in sorted(path for path in runs_root.iterdir() if path.is_dir()):
            trade_date = run_dir.name
            summary = read_json(_session_summary_path(run_dir))
            if not summary:
                sessions.append(
                    {
                        "trade_date": trade_date,
                        "net_pnl": 0.0,
                        "raw_winner": False,
                        "qualified_winner": False,
                        "disqualifiers": ["missing_session_summary"],
                    }
                )
                continue
            sessions.append(
                _classify_session(
                    runtime_root=runtime_root,
                    trade_date=trade_date,
                    session_summary=summary,
                    min_net_pnl=min_net_pnl,
                )
            )

    raw_winners = [session for session in sessions if session.get("raw_winner")]
    qualified_winners = [session for session in sessions if session.get("qualified_winner")]
    review_required_sessions = [
        session for session in sessions if session.get("disqualifiers") and session.get("raw_winner")
    ]
    remaining = max(target_qualified_winners - len(qualified_winners), 0)
    status = "live_not_ready"
    if len(qualified_winners) >= target_qualified_winners:
        status = "ready_for_micro_live_review"
    elif raw_winners:
        status = "building_sample_with_raw_winners"

    return {
        "generated_at": datetime.now().astimezone().isoformat(),
        "status": status,
        "runtime_root": str(runtime_root),
        "report_dir": str(report_dir),
        "gcs_prefix": gcs_prefix,
        "min_net_pnl": min_net_pnl,
        "target_qualified_winners": target_qualified_winners,
        "raw_winner_count": len(raw_winners),
        "qualified_winner_count": len(qualified_winners),
        "qualified_winners_remaining": remaining,
        "review_required_raw_winner_count": len(review_required_sessions),
        "session_count": len(sessions),
        "sessions": sessions,
        "operator_read": [
            "A raw winner only proves the session ended above the PnL threshold.",
            "A qualified winner must also be flat, reconciled, evidence-clean, teaching-gate clean, and free of severe-loss incidents.",
            "Do not use raw winners alone for live-trading confidence.",
        ],
        "next_actions": [
            "Keep the research arm aggressive while the paper runner accumulates qualified winners.",
            "Use loser-learning and quality scorecards to improve the chance that future sessions clear the qualified-winner gate.",
            "Treat review-required winners as useful diagnostics, not as live-readiness evidence.",
        ],
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "# GCP Paper Winner Session Readiness",
        "",
        "## Snapshot",
        "",
        f"- Generated at: `{payload['generated_at']}`",
        f"- Status: `{payload['status']}`",
        f"- Minimum net PnL for raw winner: `${payload['min_net_pnl']:.2f}`",
        f"- Target qualified winners: `{payload['target_qualified_winners']}`",
        f"- Raw winner count: `{payload['raw_winner_count']}`",
        f"- Qualified winner count: `{payload['qualified_winner_count']}`",
        f"- Qualified winners remaining: `{payload['qualified_winners_remaining']}`",
        f"- Review-required raw winners: `{payload['review_required_raw_winner_count']}`",
        "",
        "## Session Ledger",
        "",
        "| Date | Net PnL | Raw Winner | Qualified Winner | Evidence | Teaching | Disqualifiers |",
        "|---|---:|---|---|---|---|---|",
    ]
    for session in payload["sessions"]:
        disqualifiers = ", ".join(session.get("disqualifiers") or [])
        lines.append(
            "| {date} | {pnl:.2f} | {raw} | {qualified} | {evidence} | {teaching} | {disqualifiers} |".format(
                date=session.get("trade_date"),
                pnl=_float(session.get("net_pnl")),
                raw=session.get("raw_winner"),
                qualified=session.get("qualified_winner"),
                evidence=session.get("evidence_status", "missing"),
                teaching=session.get("teaching_gate_status", "missing"),
                disqualifiers=disqualifiers,
            )
        )
    lines.extend(["", "## Operator Read", ""])
    for item in payload["operator_read"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Next Actions", ""])
    for item in payload["next_actions"]:
        lines.append(f"- {item}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = build_parser().parse_args()
    report_dir = Path(args.report_dir)
    payload = build_payload(
        runtime_root=Path(args.runtime_root),
        report_dir=report_dir,
        gcs_prefix=args.gcs_prefix,
        min_net_pnl=args.min_net_pnl,
        target_qualified_winners=args.target_qualified_winners,
    )
    json_path = report_dir / "gcp_paper_winner_session_readiness.json"
    md_path = report_dir / "gcp_paper_winner_session_readiness.md"
    handoff_path = report_dir / "gcp_paper_winner_session_readiness_handoff.md"
    write_json(json_path, payload)
    write_markdown(md_path, payload)
    write_markdown(handoff_path, payload)
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()

