from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[2]
DEFAULT_REPORT_DIR = REPO_ROOT / "docs" / "gcp_foundation"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build a distilled startup-preflight status packet for the sanctioned VM runner."
    )
    parser.add_argument("--preflight-json", default="")
    parser.add_argument("--stderr-path", default="")
    parser.add_argument("--source-stamp-json", default="")
    parser.add_argument("--report-dir", default=str(DEFAULT_REPORT_DIR))
    parser.add_argument("--gcs-evidence-uri", default="")
    return parser


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _issue(severity: str, code: str, message: str) -> dict[str, str]:
    return {"severity": severity, "code": code, "message": message}


def _int_or_none(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _list_strings(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value]


def build_payload(
    *,
    preflight: dict[str, Any],
    source_stamp: dict[str, Any] | None = None,
    preflight_json_path: str = "",
    stderr_path: str = "",
    gcs_evidence_uri: str = "",
) -> dict[str, Any]:
    source_stamp = source_stamp or {}
    details = preflight.get("details") or {}
    if not isinstance(details, dict):
        details = {}
    underlyings = details.get("underlyings") or {}
    if not isinstance(underlyings, dict):
        underlyings = {}

    raw_status = str(preflight.get("status") or "missing")
    startup_check_status = str(preflight.get("startup_check_status") or "missing")
    would_allow_trading = preflight.get("would_allow_trading")
    broker_cleanup_allowed = preflight.get("broker_cleanup_allowed")
    submit_paper_orders = preflight.get("submit_paper_orders")
    broker_position_count = _int_or_none(details.get("broker_position_count"))
    open_order_count = _int_or_none(details.get("open_order_count"))
    failures = _list_strings(details.get("failures"))
    pending_reasons = _list_strings(details.get("pending_reasons"))

    issues: list[dict[str, str]] = []
    if not preflight:
        issues.append(
            _issue(
                "error",
                "startup_preflight_missing",
                "The latest VM startup-preflight output is missing.",
            )
        )
    if raw_status != "startup_preflight_passed":
        issues.append(
            _issue(
                "error",
                "startup_preflight_not_passed",
                f"The VM startup preflight reported `{raw_status}`.",
            )
        )
    if startup_check_status != "passed":
        issues.append(
            _issue(
                "error",
                "startup_check_not_passed",
                f"The runner startup check reported `{startup_check_status}`.",
            )
        )
    if would_allow_trading is not True:
        issues.append(
            _issue(
                "error",
                "startup_preflight_would_not_allow_trading",
                "The startup preflight says the runner would not allow trading.",
            )
        )
    if broker_cleanup_allowed is not False:
        issues.append(
            _issue(
                "error",
                "startup_preflight_not_read_only",
                "Startup preflight must suppress broker cleanup and remain read-only.",
            )
        )
    if submit_paper_orders is not False:
        issues.append(
            _issue(
                "error",
                "startup_preflight_order_submission_enabled",
                "Startup preflight must run with paper-order submission disabled.",
            )
        )
    if broker_position_count is None:
        issues.append(
            _issue(
                "error",
                "startup_preflight_broker_position_count_missing",
                "Startup preflight must emit broker position count evidence before launch.",
            )
        )
    elif broker_position_count != 0:
        issues.append(
            _issue(
                "error",
                "startup_preflight_broker_not_flat",
                "Startup preflight must observe zero broker positions before launch.",
            )
        )
    if open_order_count is None:
        issues.append(
            _issue(
                "error",
                "startup_preflight_open_order_count_missing",
                "Startup preflight must emit open-order count evidence before launch.",
            )
        )
    elif open_order_count != 0:
        issues.append(
            _issue(
                "error",
                "startup_preflight_open_orders_present",
                "Startup preflight must observe zero open broker orders before launch.",
            )
        )
    for failure in failures:
        issues.append(_issue("error", "startup_preflight_failure", failure))
    for reason in pending_reasons:
        issues.append(_issue("error", "startup_preflight_pending", reason))

    status = "startup_preflight_passed"
    if any(issue["severity"] == "error" for issue in issues):
        status = "startup_preflight_blocked"
    if not preflight:
        status = "startup_preflight_missing"

    return {
        "generated_at": datetime.now().astimezone().isoformat(),
        "status": status,
        "blocks_launch": status != "startup_preflight_passed",
        "raw_status": raw_status,
        "startup_check_status": startup_check_status,
        "would_allow_trading": would_allow_trading,
        "broker_cleanup_allowed": broker_cleanup_allowed,
        "submit_paper_orders": submit_paper_orders,
        "broker_position_count": broker_position_count,
        "open_order_count": open_order_count,
        "underlying_count": len(underlyings),
        "failures": failures,
        "pending_reasons": pending_reasons,
        "runner_commit": source_stamp.get("runner_commit"),
        "runner_branch": source_stamp.get("runner_branch"),
        "source_bundle_sha256": source_stamp.get("source_bundle_sha256"),
        "source_bundle_file_count": source_stamp.get("source_bundle_file_count"),
        "preflight_json_path": preflight_json_path,
        "stderr_path": stderr_path,
        "gcs_evidence_uri": gcs_evidence_uri,
        "broker_facing": False,
        "live_manifest_effect": "none",
        "risk_policy_effect": "none",
        "issues": issues,
        "operator_read": [
            "This packet distills read-only VM startup-preflight evidence; raw broker output should remain in ignored runtime evidence or GCS.",
            "If status is not `startup_preflight_passed`, do not arm the exclusive window or launch a VM session.",
            "The preflight must be rerun immediately before any sanctioned launch because market-data freshness is time-sensitive.",
            "Passing this packet is necessary but not sufficient; exclusive-window, runtime, provenance, launch-surface, and pre-arm gates must also pass.",
        ],
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "# GCP Execution Startup Preflight Status",
        "",
        "## Snapshot",
        "",
        f"- Generated at: `{payload['generated_at']}`",
        f"- Status: `{payload['status']}`",
        f"- Blocks launch: `{payload['blocks_launch']}`",
        f"- Raw status: `{payload['raw_status']}`",
        f"- Startup check status: `{payload['startup_check_status']}`",
        f"- Would allow trading: `{payload['would_allow_trading']}`",
        f"- Broker cleanup allowed: `{payload['broker_cleanup_allowed']}`",
        f"- Submit paper orders: `{payload['submit_paper_orders']}`",
        f"- Broker position count: `{payload['broker_position_count']}`",
        f"- Open order count: `{payload['open_order_count']}`",
        f"- Underlying count: `{payload['underlying_count']}`",
        f"- Runner branch: `{payload['runner_branch']}`",
        f"- Runner commit: `{payload['runner_commit']}`",
        f"- GCS evidence URI: `{payload['gcs_evidence_uri']}`",
        "",
        "## Issues",
        "",
    ]
    if payload["issues"]:
        for issue in payload["issues"]:
            lines.append(f"- `{issue['severity']}` `{issue['code']}`: {issue['message']}")
    else:
        lines.append("- none")

    lines.extend(["", "## Operator Read", ""])
    for item in payload["operator_read"]:
        lines.append(f"- {item}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_handoff(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "# GCP Execution Startup Preflight Handoff",
        "",
        f"- Status: `{payload['status']}`",
        f"- Blocks launch: `{payload['blocks_launch']}`",
        f"- Raw status: `{payload['raw_status']}`",
        f"- Startup check status: `{payload['startup_check_status']}`",
        f"- Would allow trading: `{payload['would_allow_trading']}`",
        f"- Broker cleanup allowed: `{payload['broker_cleanup_allowed']}`",
        f"- Submit paper orders: `{payload['submit_paper_orders']}`",
        f"- Broker position count: `{payload['broker_position_count']}`",
        f"- Open order count: `{payload['open_order_count']}`",
        f"- Underlying count: `{payload['underlying_count']}`",
        f"- Runner branch: `{payload['runner_branch']}`",
        f"- Runner commit: `{payload['runner_commit']}`",
        f"- GCS evidence URI: `{payload['gcs_evidence_uri']}`",
        "",
        "## Operator Rule",
        "",
        "- This is a read-only VM startup check; it must not submit orders or flatten broker positions.",
        "- If status is not `startup_preflight_passed`, do not arm the exclusive window or start a VM session.",
        "- Rerun this preflight immediately before launch because broker/account state and market-data freshness change minute to minute.",
    ]
    if payload["issues"]:
        lines.extend(["", "## Blocking Issues", ""])
        for issue in payload["issues"]:
            lines.append(f"- `{issue['code']}`: {issue['message']}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = build_parser().parse_args()
    report_dir = Path(args.report_dir).resolve()
    preflight_path = Path(args.preflight_json).resolve() if args.preflight_json else Path()
    source_stamp_path = Path(args.source_stamp_json).resolve() if args.source_stamp_json else Path()
    payload = build_payload(
        preflight=read_json(preflight_path) if args.preflight_json else {},
        source_stamp=read_json(source_stamp_path) if args.source_stamp_json else {},
        preflight_json_path=str(preflight_path) if args.preflight_json else "",
        stderr_path=str(Path(args.stderr_path).resolve()) if args.stderr_path else "",
        gcs_evidence_uri=args.gcs_evidence_uri,
    )
    write_json(report_dir / "gcp_execution_startup_preflight_status.json", payload)
    write_markdown(report_dir / "gcp_execution_startup_preflight_status.md", payload)
    write_handoff(report_dir / "gcp_execution_startup_preflight_handoff.md", payload)
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
