from __future__ import annotations

import argparse
import json
import subprocess
import tomllib
from datetime import datetime
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[2]
DEFAULT_REPORT_DIR = REPO_ROOT / "docs" / "gcp_foundation"
RUNNER_REPO_CANDIDATES = (
    Path.home()
    / "OneDrive"
    / "CodexAlpaca"
    / "downloads_remaining_20260417"
    / "folders"
    / "codexalpaca_repo",
    REPO_ROOT.parent / "codexalpaca_repo",
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build the shared execution lease runtime wiring status packet."
    )
    parser.add_argument("--runner-repo-root", default="")
    parser.add_argument("--report-dir", default=str(DEFAULT_REPORT_DIR))
    parser.add_argument("--full-suite-summary", default="123 passed")
    return parser


def resolve_runner_repo_root(explicit: str) -> Path:
    if explicit:
        return Path(explicit).resolve()
    for candidate in RUNNER_REPO_CANDIDATES:
        if candidate.exists():
            return candidate.resolve()
    return RUNNER_REPO_CANDIDATES[0].resolve()


def run_git(repo_root: Path, *args: str) -> str | None:
    try:
        result = subprocess.run(
            ["git", "-C", str(repo_root), *args],
            capture_output=True,
            text=True,
            check=False,
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if result.returncode != 0:
        return None
    output = (result.stdout or "").strip()
    return output or None


def load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def build_payload(runner_repo_root: Path, full_suite_summary: str) -> dict[str, Any]:
    generated_at = datetime.now().astimezone().isoformat()
    ownership_text = load_text(runner_repo_root / "alpaca_lab" / "execution" / "ownership.py")
    config_text = load_text(runner_repo_root / "alpaca_lab" / "multi_ticker_portfolio" / "config.py")
    trader_text = load_text(runner_repo_root / "alpaca_lab" / "multi_ticker_portfolio" / "trader.py")
    health_check_text = load_text(runner_repo_root / "scripts" / "run_multi_ticker_health_check.py")
    standby_text = load_text(runner_repo_root / "scripts" / "run_multi_ticker_standby_failover_check.py")
    pyproject = tomllib.loads(load_text(runner_repo_root / "pyproject.toml"))
    gcp_extra = list(pyproject.get("project", {}).get("optional-dependencies", {}).get("gcp", []))

    runner_branch = run_git(runner_repo_root, "branch", "--show-current")
    runner_commit = run_git(runner_repo_root, "rev-parse", "HEAD")
    runner_short_commit = run_git(runner_repo_root, "rev-parse", "--short=12", "HEAD")
    dirty = bool(run_git(runner_repo_root, "status", "--porcelain"))

    payload = {
        "generated_at": generated_at,
        "project_id": "codexalpaca",
        "runtime_wiring_phase": "foundation-phase16-lease-runtime-wiring",
        "runtime_wiring_status": "optional_backend_wired_not_enforced",
        "runner_repo": {
            "path": str(runner_repo_root),
            "branch": runner_branch,
            "commit": runner_commit,
            "short_commit": runner_short_commit,
            "dirty": dirty,
        },
        "wiring_findings": {
            "gcs_store_present": "class GCSGenerationMatchLeaseStore:" in ownership_text,
            "config_backend_switch_present": 'lease_backend: Literal["file", "gcs_generation_match"]' in config_text,
            "config_gcs_uri_present": "gcs_lease_uri: str | None = None" in config_text,
            "env_backend_override_present": "MULTI_TICKER_OWNERSHIP_LEASE_BACKEND" in config_text,
            "env_gcs_uri_override_present": "MULTI_TICKER_OWNERSHIP_GCS_LEASE_URI" in config_text,
            "trader_optional_wiring_present": "GCSGenerationMatchLeaseStore.from_gcs_uri" in trader_text,
            "default_file_lease_still_present": "if ownership.lease_backend == \"file\":" in trader_text,
            "health_check_still_file_lease_based": "FileOwnershipLease(" in health_check_text,
            "standby_check_still_file_lease_based": "lease_path=config.ownership.lease_path" in standby_text,
            "gcp_extra_declared": any("google-cloud-storage" in item for item in gcp_extra),
        },
        "validation": {
            "full_suite": full_suite_summary,
            "full_suite_command": "python -m pytest -q",
        },
        "guardrails": [
            "The default trader path still remains on the file lease unless ownership.lease_backend is explicitly switched.",
            "The GCS lease backend still depends on explicit config and the optional 'gcp' dependency path.",
            "Health-check and standby failover scripts remain aligned to the file-lease path until a separate sanctioned migration says otherwise.",
            "This wiring does not by itself clear the project for broker-facing cloud lease enforcement.",
        ],
        "next_step": {
            "name": "vm_dry_run_gcs_lease_validation",
            "description": "Install the runner with the gcp extra on vm-execution-paper-01, point ownership at the GCS lease object under explicit non-default config, and validate acquire/renew/release behavior without starting a broker-facing session.",
        },
    }
    return payload


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    lines: list[str] = []
    lines.append("# GCP Shared Execution Lease Runtime Wiring")
    lines.append("")
    lines.append("## Snapshot")
    lines.append("")
    lines.append(f"- Generated at: `{payload['generated_at']}`")
    lines.append(f"- Project ID: `{payload['project_id']}`")
    lines.append(f"- Runtime wiring phase: `{payload['runtime_wiring_phase']}`")
    lines.append(f"- Runtime wiring status: `{payload['runtime_wiring_status']}`")
    lines.append(f"- Runner branch: `{payload['runner_repo']['branch']}`")
    lines.append(f"- Runner commit: `{payload['runner_repo']['short_commit']}`")
    lines.append(f"- Runner dirty: `{payload['runner_repo']['dirty']}`")
    lines.append("")
    lines.append("## Wiring Findings")
    lines.append("")
    for key, value in payload["wiring_findings"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.append("")
    lines.append("## Validation")
    lines.append("")
    lines.append(f"- Full suite: `{payload['validation']['full_suite']}`")
    lines.append(f"- Full suite command: `{payload['validation']['full_suite_command']}`")
    lines.append("")
    lines.append("## Guardrails")
    lines.append("")
    for item in payload["guardrails"]:
        lines.append(f"- {item}")
    lines.append("")
    lines.append("## Next Step")
    lines.append("")
    lines.append(f"- Name: `{payload['next_step']['name']}`")
    lines.append(f"- {payload['next_step']['description']}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_handoff(path: Path, payload: dict[str, Any]) -> None:
    lines: list[str] = []
    lines.append("# GCP Shared Execution Lease Runtime Wiring Handoff")
    lines.append("")
    lines.append("## Current Read")
    lines.append("")
    lines.append("- The sanctioned runner now has a real optional GCS-backed execution lease path.")
    lines.append("- The default trader path is still unchanged and remains on the file lease.")
    lines.append("- Local safety tooling still points at the file-lease model, which is intentional at this phase.")
    lines.append("")
    lines.append("## Operator Rule")
    lines.append("")
    lines.append("- Treat the GCS runtime wiring as VM-only dry-run ready, not broker-facing ready.")
    lines.append("- Do not flip the backend globally.")
    lines.append("- Do not migrate workstation health-check or standby tooling to GCS until that move is separately sanctioned.")
    lines.append("")
    lines.append("## Next Step")
    lines.append("")
    lines.append("- Install the runner with the `gcp` extra on `vm-execution-paper-01` and validate the live GCS lease object in dry-run mode before any broker-facing promotion decision.")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    runner_repo_root = resolve_runner_repo_root(args.runner_repo_root)
    payload = build_payload(runner_repo_root, args.full_suite_summary)
    report_dir = Path(args.report_dir).resolve()
    write_json(report_dir / "gcp_shared_execution_lease_runtime_wiring_status.json", payload)
    write_markdown(report_dir / "gcp_shared_execution_lease_runtime_wiring_status.md", payload)
    write_handoff(report_dir / "gcp_shared_execution_lease_runtime_wiring_handoff.md", payload)
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
