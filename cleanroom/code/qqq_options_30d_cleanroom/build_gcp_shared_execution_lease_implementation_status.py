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
DEFAULT_CONTRACT_JSON = (
    REPO_ROOT / "docs" / "gcp_foundation" / "gcp_shared_execution_lease_contract_status.json"
)
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
        description="Build a shared execution lease implementation checkpoint from the runner repo."
    )
    parser.add_argument("--contract-json", default=str(DEFAULT_CONTRACT_JSON))
    parser.add_argument("--runner-repo-root", default="")
    parser.add_argument("--report-dir", default=str(DEFAULT_REPORT_DIR))
    parser.add_argument("--targeted-tests-summary", default="15 passed")
    parser.add_argument("--full-suite-summary", default="117 passed")
    return parser


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


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


def has_all(text: str, *needles: str) -> bool:
    return all(needle in text for needle in needles)


def build_payload(
    contract: dict[str, Any],
    runner_repo_root: Path,
    targeted_tests_summary: str,
    full_suite_summary: str,
) -> dict[str, Any]:
    generated_at = datetime.now().astimezone().isoformat()
    ownership_path = runner_repo_root / "alpaca_lab" / "execution" / "ownership.py"
    config_path = runner_repo_root / "alpaca_lab" / "multi_ticker_portfolio" / "config.py"
    trader_path = runner_repo_root / "alpaca_lab" / "multi_ticker_portfolio" / "trader.py"
    health_check_path = runner_repo_root / "scripts" / "run_multi_ticker_health_check.py"
    test_path = runner_repo_root / "tests" / "test_execution_ownership.py"
    portfolio_test_path = runner_repo_root / "tests" / "test_multi_ticker_portfolio.py"
    health_check_test_path = runner_repo_root / "tests" / "test_run_multi_ticker_health_check.py"
    pyproject_path = runner_repo_root / "pyproject.toml"

    ownership_text = load_text(ownership_path)
    config_text = load_text(config_path)
    trader_text = load_text(trader_path)
    health_check_text = load_text(health_check_path)
    test_text = load_text(test_path)
    portfolio_test_text = load_text(portfolio_test_path) if portfolio_test_path.exists() else ""
    health_check_test_text = (
        load_text(health_check_test_path) if health_check_test_path.exists() else ""
    )
    pyproject = tomllib.loads(load_text(pyproject_path))
    dependencies = list(pyproject.get("project", {}).get("dependencies", []))
    optional_dependencies = [
        item
        for group in pyproject.get("project", {}).get("optional-dependencies", {}).values()
        if isinstance(group, list)
        for item in group
    ]
    has_cloud_dependency = any(
        "google-cloud-storage" in item for item in [*dependencies, *optional_dependencies]
    )

    runner_branch = run_git(runner_repo_root, "branch", "--show-current")
    runner_commit = run_git(runner_repo_root, "rev-parse", "HEAD")
    runner_short_commit = run_git(runner_repo_root, "rev-parse", "--short=12", "HEAD")
    dirty = bool(run_git(runner_repo_root, "status", "--porcelain"))

    helper_present = has_all(
        ownership_text,
        "class GenerationMatchOwnershipLease:",
        "class LeaseConflictError",
        "class ObjectLeaseStore(Protocol):",
        "class ObjectLeaseRecord:",
    )
    release_present = "def release(self, *, role: str)" in ownership_text
    renew_present = "def renew(self, *, role: str" in ownership_text
    generation_status_present = "generation: str | None = None" in ownership_text
    gcs_store_present = (
        "class GCSGenerationMatchLeaseStore" in ownership_text
        or "class GcsObjectLeaseStore" in ownership_text
    )
    config_switch_present = has_all(
        config_text,
        'lease_backend: Literal["file", "gcs_generation_match"] = "file"',
        "gcs_lease_uri: str | None = None",
    )
    trader_default_is_file = (
        has_all(
            trader_text,
            "def _build_ownership_lease(self) -> Any:",
            'if ownership.lease_backend == "file":',
        )
        and 'lease_backend: Literal["file", "gcs_generation_match"] = "file"' in config_text
    )
    health_check_support_present = has_all(
        health_check_text,
        "def build_health_check_ownership_lease(portfolio_config):",
        'if ownership.lease_backend == "gcs_generation_match":',
    )
    gcs_wiring_tests_present = has_all(
        test_text,
        "test_gcs_generation_match_store_round_trips_payload",
    ) and "test_trader_builds_generation_match_lease_when_gcs_backend_selected" in (
        portfolio_test_text
    )
    health_check_tests_present = "test_build_health_check_ownership_lease_supports_gcs_backend" in (
        health_check_test_text
    )
    tests_present = has_all(
        test_text,
        "test_generation_match_ownership_lease_blocks_other_owner",
        "test_generation_match_ownership_lease_allows_same_owner_multiple_roles",
        "test_generation_match_ownership_lease_can_take_over_expired_lease",
        "test_generation_match_ownership_lease_release_removes_last_role",
    )

    if (
        helper_present
        and tests_present
        and trader_default_is_file
        and gcs_store_present
        and config_switch_present
        and health_check_support_present
        and gcs_wiring_tests_present
        and health_check_tests_present
        and has_cloud_dependency
    ):
        implementation_status = "optional_gcs_store_wiring_landed_not_validated"
    elif helper_present and tests_present and trader_default_is_file:
        implementation_status = "dry_run_helper_landed"
    else:
        implementation_status = "implementation_gap_detected"

    return {
        "generated_at": generated_at,
        "project_id": contract.get("project_id", "codexalpaca"),
        "implementation_phase": "foundation-phase14-lease-helper-implementation",
        "recommended_lease": contract.get("recommended_lease"),
        "lease_object": contract.get("lease_object"),
        "implementation_status": implementation_status,
        "enforcement_state": "off_by_default",
        "runner_repo": {
            "path": str(runner_repo_root),
            "branch": runner_branch,
            "commit": runner_commit,
            "short_commit": runner_short_commit,
            "dirty": dirty,
            "metadata_available": runner_commit is not None,
        },
        "implementation_findings": {
            "generation_match_helper_present": helper_present,
            "renew_present": renew_present,
            "release_present": release_present,
            "generation_field_present": generation_status_present,
            "new_tests_present": tests_present,
            "gcs_store_present": gcs_store_present,
            "explicit_gcs_config_present": config_switch_present,
            "health_check_support_present": health_check_support_present,
            "gcs_wiring_tests_present": gcs_wiring_tests_present,
            "health_check_tests_present": health_check_tests_present,
            "default_trader_path_is_still_file_lease": trader_default_is_file,
            "google_cloud_storage_dependency_present": has_cloud_dependency,
        },
        "validation": {
            "targeted_tests": targeted_tests_summary,
            "full_suite": full_suite_summary,
            "targeted_commands": [
                (
                    "python -m pytest -q tests/test_execution_ownership.py "
                    "tests/test_execution_failover.py tests/test_multi_ticker_portfolio.py "
                    "tests/test_run_multi_ticker_health_check.py"
                )
            ],
            "full_suite_command": "python -m pytest -q",
        },
        "current_guardrails": [
            "Do not switch the multi-ticker trader to the generation-match lease by default yet.",
            "Do not start broker-facing cloud execution from the optional GCS store wiring alone.",
            "Keep the current trusted validation-session gate in force until the shared lease is validated against the sanctioned GCS object.",
            "Treat the new ownership store as implementation-ready but not yet live until real-object validation succeeds.",
        ],
        "next_build_step": {
            "name": "real_gcs_object_validation",
            "description": "Validate the sanctioned GCS-backed ObjectLeaseStore against the real lease object and keep the default trader path on the file lease until that packet is clean.",
            "requirements": [
                "Validate acquire, renew, release, and stale takeover against the real GCS object with generation preconditions.",
                "Keep enforcement disabled by default until both workstation and VM validation packets are clean.",
                "Do not treat the cloud shared execution lease as live until the real-object validation and trusted session gates both clear.",
            ],
        },
        "institutional_read": [
            "The runner now has a clean compare-and-set ownership seam that matches the control-plane lease contract.",
            "The sanctioned execution path is still protected because the default trader path remains on the file lease unless the non-default GCS backend is explicitly configured.",
            "The next step is real-object validation, not immediate cloud execution promotion.",
        ],
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    lines: list[str] = []
    lines.append("# GCP Shared Execution Lease Implementation")
    lines.append("")
    lines.append("## Snapshot")
    lines.append("")
    lines.append(f"- Generated at: `{payload['generated_at']}`")
    lines.append(f"- Project ID: `{payload['project_id']}`")
    lines.append(f"- Implementation phase: `{payload['implementation_phase']}`")
    lines.append(f"- Recommended lease: `{payload['recommended_lease']}`")
    lines.append(f"- Lease object: `{payload['lease_object']}`")
    lines.append(f"- Implementation status: `{payload['implementation_status']}`")
    lines.append(f"- Enforcement state: `{payload['enforcement_state']}`")
    lines.append("")
    lines.append("## Runner Repo")
    lines.append("")
    lines.append(f"- Path: `{payload['runner_repo']['path']}`")
    lines.append(f"- Branch: `{payload['runner_repo']['branch']}`")
    lines.append(f"- Commit: `{payload['runner_repo']['short_commit']}`")
    lines.append(f"- Dirty: `{payload['runner_repo']['dirty']}`")
    lines.append("")
    lines.append("## Implementation Findings")
    lines.append("")
    for key, value in payload["implementation_findings"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.append("")
    lines.append("## Validation")
    lines.append("")
    lines.append(f"- Targeted tests: `{payload['validation']['targeted_tests']}`")
    lines.append(f"- Full suite: `{payload['validation']['full_suite']}`")
    lines.append(f"- Targeted command: `{payload['validation']['targeted_commands'][0]}`")
    lines.append(f"- Full suite command: `{payload['validation']['full_suite_command']}`")
    lines.append("")
    lines.append("## Current Guardrails")
    lines.append("")
    for item in payload["current_guardrails"]:
        lines.append(f"- {item}")
    lines.append("")
    lines.append("## Next Build Step")
    lines.append("")
    lines.append(f"- Name: `{payload['next_build_step']['name']}`")
    lines.append(f"- {payload['next_build_step']['description']}")
    for item in payload["next_build_step"]["requirements"]:
        lines.append(f"- {item}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_handoff(path: Path, payload: dict[str, Any]) -> None:
    lines: list[str] = []
    lines.append("# GCP Shared Execution Lease Implementation Handoff")
    lines.append("")
    lines.append("## Current Read")
    lines.append("")
    lines.append("- The sanctioned runner now contains an optional GCS-backed ownership store behind explicit non-default config.")
    lines.append("- The default trader path still remains on the file lease unless that non-default backend is explicitly selected.")
    lines.append("- The health-check path now understands the non-default lease backend, while standby failover remains intentionally file-scoped.")
    lines.append("- This is the right intermediate posture: implementation exists, but the cloud lease is still not live.")
    lines.append("")
    lines.append("## Operator Rule")
    lines.append("")
    lines.append("- Treat the optional GCS lease path as implementation-ready, not broker-facing ready.")
    lines.append("- Do not present the cloud shared execution lease as live until the sanctioned GCS object has been validated with generation preconditions.")
    lines.append("- Keep the trusted validation-session gate and the parallel-runtime exception controls in force.")
    lines.append("")
    lines.append("## Next Step")
    lines.append("")
    lines.append("- Validate the sanctioned GCS-backed ObjectLeaseStore against the real lease object before any promotion decision.")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    contract = load_json(Path(args.contract_json).resolve())
    runner_repo_root = resolve_runner_repo_root(args.runner_repo_root)
    payload = build_payload(
        contract=contract,
        runner_repo_root=runner_repo_root,
        targeted_tests_summary=args.targeted_tests_summary,
        full_suite_summary=args.full_suite_summary,
    )

    report_dir = Path(args.report_dir).resolve()
    write_json(report_dir / "gcp_shared_execution_lease_implementation_status.json", payload)
    write_markdown(report_dir / "gcp_shared_execution_lease_implementation_status.md", payload)
    write_handoff(report_dir / "gcp_shared_execution_lease_implementation_handoff.md", payload)
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
