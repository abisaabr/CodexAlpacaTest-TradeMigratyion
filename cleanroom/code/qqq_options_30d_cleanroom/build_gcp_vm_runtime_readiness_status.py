from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[2]
DEFAULT_REPORT_DIR = REPO_ROOT / "docs" / "gcp_foundation"
DEFAULT_SOURCE_PROVENANCE_JSON = DEFAULT_REPORT_DIR / "gcp_vm_runner_provenance_status.json"
DEFAULT_VM_NAME = "vm-execution-paper-01"
DEFAULT_VM_RUNNER_PATH = "/opt/codexalpaca/codexalpaca_repo"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build VM runtime readiness status for the sanctioned paper runner.")
    parser.add_argument("--vm-name", default=DEFAULT_VM_NAME)
    parser.add_argument("--vm-runner-path", default=DEFAULT_VM_RUNNER_PATH)
    parser.add_argument("--source-provenance-json", default=str(DEFAULT_SOURCE_PROVENANCE_JSON))
    parser.add_argument("--data-writable", action="store_true")
    parser.add_argument("--reports-writable", action="store_true")
    parser.add_argument("--state-root-writable", action="store_true")
    parser.add_argument("--run-root-writable", action="store_true")
    parser.add_argument("--pytest-cache-writable", action="store_true")
    parser.add_argument("--doctor-status", default="not_run")
    parser.add_argument("--vm-pytest-status", default="not_run")
    parser.add_argument("--vm-pytest-summary", default="")
    parser.add_argument("--report-dir", default=str(DEFAULT_REPORT_DIR))
    return parser


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def build_payload(
    *,
    vm_name: str,
    vm_runner_path: str,
    source_provenance: dict[str, Any] | None,
    data_writable: bool,
    reports_writable: bool,
    state_root_writable: bool,
    run_root_writable: bool,
    pytest_cache_writable: bool,
    doctor_status: str,
    vm_pytest_status: str,
    vm_pytest_summary: str,
    report_dir: Path,
) -> dict[str, Any]:
    source_provenance = source_provenance or {}
    source_provenance_status = str(source_provenance.get("status") or "missing")
    path_checks = [
        {"name": "data", "writable": data_writable},
        {"name": "reports", "writable": reports_writable},
        {"name": "reports/multi_ticker_portfolio/state", "writable": state_root_writable},
        {"name": "reports/multi_ticker_portfolio/runs", "writable": run_root_writable},
        {"name": ".pytest_cache", "writable": pytest_cache_writable},
    ]
    issues: list[dict[str, str]] = []
    for check in path_checks:
        if not check["writable"]:
            issues.append(
                {
                    "severity": "error",
                    "code": f"{check['name'].replace('/', '_').replace('.', '')}_not_writable",
                    "message": f"`{check['name']}` is not writable by the VM operator user.",
                }
            )
    if doctor_status != "passed":
        issues.append(
            {
                "severity": "error",
                "code": "vm_doctor_not_passed",
                "message": "VM doctor did not pass in non-broker validation mode.",
            }
        )
    if vm_pytest_status != "passed":
        issues.append(
            {
                "severity": "warning",
                "code": "vm_pytest_not_green",
                "message": "VM pytest is not green or was not run after runtime readiness changes.",
            }
        )
    if source_provenance_status.startswith("blocked_") or source_provenance_status in {"missing", "provenance_unstamped"}:
        issues.append(
            {
                "severity": "error",
                "code": "source_provenance_not_ready",
                "message": "VM source provenance must be matched before runtime readiness can support trusted launch.",
            }
        )

    status = "runtime_ready"
    if any(issue["severity"] == "error" for issue in issues):
        status = "blocked_vm_runtime_readiness"
    elif any(issue["severity"] == "warning" for issue in issues):
        status = "runtime_ready_with_warnings"

    return {
        "generated_at": datetime.now().astimezone().isoformat(),
        "status": status,
        "vm_name": vm_name,
        "vm_runner_path": vm_runner_path,
        "report_dir": str(report_dir),
        "source_provenance_status": source_provenance_status,
        "data_writable": data_writable,
        "reports_writable": reports_writable,
        "state_root_writable": state_root_writable,
        "run_root_writable": run_root_writable,
        "pytest_cache_writable": pytest_cache_writable,
        "doctor_status": doctor_status,
        "vm_pytest_status": vm_pytest_status,
        "vm_pytest_summary": vm_pytest_summary,
        "broker_facing": False,
        "live_manifest_effect": "none",
        "risk_policy_effect": "none",
        "path_checks": path_checks,
        "issues": issues,
        "operator_read": [
            "This packet validates VM runtime output readiness only; it does not start trading or arm the exclusive window.",
            "The trusted paper session needs writable state and run directories so broker-audited evidence can be left behind.",
            "Source provenance, exclusive-window, and launch-pack gates still control whether a broker-facing session may start.",
        ],
        "next_actions": [
            "If status is `runtime_ready`, keep source and runtime-output responsibilities separate: source stays stamped, runtime directories stay writable.",
            "Refresh this packet after any VM source redeploy, permission repair, or runtime bootstrap change.",
            "Do not use runtime readiness as strategy-promotion evidence; it only supports operational launch readiness.",
        ],
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "# GCP VM Runtime Readiness Status",
        "",
        "## Snapshot",
        "",
        f"- Generated at: `{payload['generated_at']}`",
        f"- Status: `{payload['status']}`",
        f"- VM name: `{payload['vm_name']}`",
        f"- VM runner path: `{payload['vm_runner_path']}`",
        f"- Source provenance status: `{payload['source_provenance_status']}`",
        f"- Doctor status: `{payload['doctor_status']}`",
        f"- VM pytest status: `{payload['vm_pytest_status']}`",
        f"- VM pytest summary: `{payload['vm_pytest_summary']}`",
        "",
        "## Path Checks",
        "",
    ]
    for check in payload["path_checks"]:
        lines.append(f"- `{check['name']}` writable: `{check['writable']}`")
    lines.extend(["", "## Issues", ""])
    if payload["issues"]:
        for issue in payload["issues"]:
            lines.append(f"- `{issue['severity']}` `{issue['code']}`: {issue['message']}")
    else:
        lines.append("- none")
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
        vm_name=args.vm_name,
        vm_runner_path=args.vm_runner_path,
        source_provenance=read_json(Path(args.source_provenance_json)),
        data_writable=args.data_writable,
        reports_writable=args.reports_writable,
        state_root_writable=args.state_root_writable,
        run_root_writable=args.run_root_writable,
        pytest_cache_writable=args.pytest_cache_writable,
        doctor_status=args.doctor_status,
        vm_pytest_status=args.vm_pytest_status,
        vm_pytest_summary=args.vm_pytest_summary,
        report_dir=report_dir,
    )
    write_json(report_dir / "gcp_vm_runtime_readiness_status.json", payload)
    write_markdown(report_dir / "gcp_vm_runtime_readiness_status.md", payload)
    write_markdown(report_dir / "gcp_vm_runtime_readiness_handoff.md", payload)
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
