from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[2]
DEFAULT_REPORT_DIR = REPO_ROOT / "docs" / "gcp_foundation"
DEFAULT_RUNNER_REPO_ROOT = REPO_ROOT.parent / "codexalpaca_repo_gcp_lease_lane_refreshed"
DEFAULT_VM_NAME = "vm-execution-paper-01"
DEFAULT_VM_RUNNER_PATH = "/opt/codexalpaca/codexalpaca_repo"
DEFAULT_GCS_PREFIX = "gs://codexalpaca-control-us/gcp_foundation"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build VM runner source-provenance status packet.")
    parser.add_argument("--runner-repo-root", default=str(DEFAULT_RUNNER_REPO_ROOT))
    parser.add_argument("--vm-name", default=DEFAULT_VM_NAME)
    parser.add_argument("--vm-runner-path", default=DEFAULT_VM_RUNNER_PATH)
    parser.add_argument("--vm-path-present", action="store_true")
    parser.add_argument("--vm-git-present", action="store_true")
    parser.add_argument("--vm-runner-branch", default="")
    parser.add_argument("--vm-runner-commit", default="")
    parser.add_argument("--report-dir", default=str(DEFAULT_REPORT_DIR))
    parser.add_argument("--gcs-prefix", default=DEFAULT_GCS_PREFIX)
    return parser


def _git_output(repo_root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo_root), *args],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def build_payload(
    *,
    runner_repo_root: Path,
    vm_name: str,
    vm_runner_path: str,
    vm_path_present: bool,
    vm_git_present: bool,
    vm_runner_branch: str,
    vm_runner_commit: str,
    report_dir: Path,
    gcs_prefix: str,
) -> dict[str, Any]:
    local_branch = _git_output(runner_repo_root, "rev-parse", "--abbrev-ref", "HEAD")
    local_commit = _git_output(runner_repo_root, "rev-parse", "HEAD")
    local_dirty = bool(_git_output(runner_repo_root, "status", "--short"))

    vm_commit_matches_local = bool(vm_runner_commit and vm_runner_commit == local_commit)
    issues: list[dict[str, str]] = []
    if local_dirty:
        issues.append(
            {
                "severity": "warning",
                "code": "local_runner_dirty",
                "message": "The local runner checkout has uncommitted changes and should not be used as a provenance source.",
            }
        )
    if not vm_path_present:
        issues.append(
            {
                "severity": "error",
                "code": "vm_runner_path_missing",
                "message": f"The VM runner path `{vm_runner_path}` was not observed.",
            }
        )
    elif not vm_git_present and not vm_runner_commit:
        issues.append(
            {
                "severity": "warning",
                "code": "vm_runner_commit_unstamped",
                "message": "The VM runner path exists but does not expose Git metadata or an observed source commit stamp.",
            }
        )
    elif vm_runner_commit and not vm_commit_matches_local:
        issues.append(
            {
                "severity": "warning",
                "code": "vm_runner_commit_differs_from_local",
                "message": "The VM runner commit differs from the local canonical runner checkout.",
            }
        )

    if any(issue["severity"] == "error" for issue in issues):
        status = "blocked_vm_runner_missing"
    elif vm_commit_matches_local:
        status = "provenance_matched"
    elif vm_runner_commit:
        status = "provenance_observed_commit_mismatch"
    else:
        status = "provenance_unstamped"

    return {
        "generated_at": datetime.now().astimezone().isoformat(),
        "status": status,
        "runner_repo_root": str(runner_repo_root),
        "report_dir": str(report_dir),
        "gcs_prefix": gcs_prefix,
        "vm_name": vm_name,
        "vm_runner_path": vm_runner_path,
        "local_runner_branch": local_branch,
        "local_runner_commit": local_commit,
        "local_runner_dirty": local_dirty,
        "vm_path_present": vm_path_present,
        "vm_git_present": vm_git_present,
        "vm_runner_branch": vm_runner_branch or None,
        "vm_runner_commit": vm_runner_commit or None,
        "vm_commit_matches_local": vm_commit_matches_local,
        "broker_facing": False,
        "live_manifest_effect": "none",
        "risk_policy_effect": "none",
        "issues": issues,
        "operator_read": [
            "This packet is a source-provenance check only; it does not start trading or change the VM.",
            "A trusted session is strongest when the VM runner exposes the exact Git commit or a deployment stamp.",
            "If provenance is unstamped, treat the session as operationally bounded but not fully source-attested until post-session review confirms code identity.",
        ],
        "next_actions": [
            "Add a lightweight deployment source stamp to the VM runner path before the next trusted session, or deploy the runner as a Git checkout.",
            "Refresh this packet after source provenance is stamped.",
            "Do not use unstamped VM source provenance to justify strategy promotion.",
        ],
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "# GCP VM Runner Provenance Status",
        "",
        "## Snapshot",
        "",
        f"- Generated at: `{payload['generated_at']}`",
        f"- Status: `{payload['status']}`",
        f"- VM name: `{payload['vm_name']}`",
        f"- VM runner path: `{payload['vm_runner_path']}`",
        f"- Local runner branch: `{payload['local_runner_branch']}`",
        f"- Local runner commit: `{payload['local_runner_commit']}`",
        f"- VM path present: `{payload['vm_path_present']}`",
        f"- VM Git present: `{payload['vm_git_present']}`",
        f"- VM runner commit: `{payload['vm_runner_commit']}`",
        f"- VM commit matches local: `{payload['vm_commit_matches_local']}`",
        "",
        "## Issues",
        "",
    ]
    for issue in payload["issues"]:
        lines.append(f"- `{issue['severity']}` `{issue['code']}`: {issue['message']}")
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
        runner_repo_root=Path(args.runner_repo_root),
        vm_name=args.vm_name,
        vm_runner_path=args.vm_runner_path,
        vm_path_present=args.vm_path_present,
        vm_git_present=args.vm_git_present,
        vm_runner_branch=args.vm_runner_branch,
        vm_runner_commit=args.vm_runner_commit,
        report_dir=report_dir,
        gcs_prefix=args.gcs_prefix,
    )
    write_json(report_dir / "gcp_vm_runner_provenance_status.json", payload)
    write_markdown(report_dir / "gcp_vm_runner_provenance_status.md", payload)
    write_markdown(report_dir / "gcp_vm_runner_provenance_handoff.md", payload)
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
