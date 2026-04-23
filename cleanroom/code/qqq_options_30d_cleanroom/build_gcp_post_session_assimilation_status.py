from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[2]
WORKSPACE_ROOT = SCRIPT_DIR.parents[4]
DEFAULT_REPORT_DIR = REPO_ROOT / "docs" / "gcp_foundation"


def first_existing_path(*paths: Path) -> Path:
    for path in paths:
        if path.exists():
            return path
    return paths[0]


DEFAULT_RUNNER_REPO_ROOT = first_existing_path(
    WORKSPACE_ROOT / "codexalpaca_repo_gcp_lease_lane_refreshed",
    WORKSPACE_ROOT / "codexalpaca_repo",
    Path(r"C:\Users\rabisaab\Downloads\codexalpaca_repo"),
)
DEFAULT_RUNTIME_ROOT = first_existing_path(
    WORKSPACE_ROOT / "codexalpaca_runtime" / "multi_ticker_portfolio_live",
    Path(r"C:\Users\abisa\Downloads\codexalpaca_runtime\multi_ticker_portfolio_live"),
)
DEFAULT_GCS_PREFIX = "gs://codexalpaca-control-us/gcp_foundation"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build the GCP post-session assimilation status packet for the sanctioned paper runner."
    )
    parser.add_argument("--runner-repo-root", default=str(DEFAULT_RUNNER_REPO_ROOT))
    parser.add_argument("--runtime-root", default=str(DEFAULT_RUNTIME_ROOT))
    parser.add_argument("--report-dir", default=str(DEFAULT_REPORT_DIR))
    parser.add_argument("--gcs-prefix", default=DEFAULT_GCS_PREFIX)
    return parser


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def preferred_evidence_root(runtime_root: Path, repo_reports_root: Path) -> tuple[str, Path]:
    runtime_ready = (runtime_root / "runs").exists() and (runtime_root / "state").exists()
    repo_ready = (repo_reports_root / "runs").exists()
    if runtime_ready:
        return "runtime_live", runtime_root
    if repo_ready:
        return "repo_mirror", repo_reports_root
    return "missing", runtime_root


def build_payload(
    *,
    runner_repo_root: Path,
    runtime_root: Path,
    gcs_prefix: str,
) -> dict[str, Any]:
    repo_reports_root = runner_repo_root / "reports" / "multi_ticker_portfolio"
    evidence_source_preference, preferred_root = preferred_evidence_root(runtime_root, repo_reports_root)
    session_reports_root = preferred_root / "runs"
    state_root = preferred_root / "state"

    required_artifacts = [
        REPO_ROOT / "docs" / "session_reconciliation" / "session_reconciliation_handoff.json",
        REPO_ROOT / "docs" / "execution_calibration" / "execution_calibration_handoff.json",
        REPO_ROOT / "docs" / "tournament_profiles" / "tournament_profile_handoff.json",
        REPO_ROOT / "docs" / "tournament_unlocks" / "tournament_unlock_handoff.json",
        REPO_ROOT / "docs" / "tournament_unlocks" / "tournament_unlock_workplan_handoff.json",
        REPO_ROOT / "docs" / "execution_evidence" / "execution_evidence_contract_handoff.json",
        REPO_ROOT / "docs" / "overnight_plan" / "overnight_phased_plan_handoff.json",
        REPO_ROOT / "docs" / "morning_brief" / "morning_operator_brief_handoff.json",
    ]
    missing_dependencies: list[str] = []
    if not runner_repo_root.exists():
        missing_dependencies.append(f"runner_repo_root_missing:{runner_repo_root}")
    if evidence_source_preference == "missing":
        missing_dependencies.append("evidence_root_missing")

    status = "ready_for_post_session_assimilation"
    if missing_dependencies:
        status = "blocked"

    operator_actions = [
        f"Use `{evidence_source_preference}` as the canonical evidence lane for the first sanctioned VM validation session.",
        f"Rebuild governed handoffs from `{preferred_root}` immediately after the VM session ends.",
        "Refresh the morning brief and execution evidence contract before any promotion decision.",
    ]
    if evidence_source_preference == "runtime_live":
        operator_actions.insert(
            0,
            "Prefer the runtime-local `multi_ticker_portfolio_live` evidence bundle over the repo mirror for governed post-session assimilation.",
        )
    if evidence_source_preference == "repo_mirror":
        operator_actions.insert(
            0,
            "Runtime-local evidence is unavailable, so governed post-session assimilation will fall back to the repo mirror path.",
        )
    if status == "blocked":
        operator_actions = [
            "Do not run governed post-session assimilation until the runner repo and at least one evidence root are available."
        ] + operator_actions

    return {
        "generated_at": datetime.now().astimezone().isoformat(),
        "status": status,
        "runner_repo_root": str(runner_repo_root),
        "runtime_root": str(runtime_root),
        "repo_reports_root": str(repo_reports_root),
        "preferred_reports_root": str(preferred_root),
        "session_reports_root": str(session_reports_root),
        "state_root": str(state_root),
        "evidence_source_preference": evidence_source_preference,
        "runtime_root_available": runtime_root.exists(),
        "repo_reports_root_available": repo_reports_root.exists(),
        "gcs_prefix": gcs_prefix,
        "required_control_plane_outputs": [str(path) for path in required_artifacts],
        "missing_dependencies": missing_dependencies,
        "operator_actions": operator_actions,
    }


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "# GCP Post-Session Assimilation Status",
        "",
        "## Snapshot",
        "",
        f"- Generated at: `{payload['generated_at']}`",
        f"- Status: `{payload['status']}`",
        f"- Evidence source preference: `{payload['evidence_source_preference']}`",
        f"- Runner repo root: `{payload['runner_repo_root']}`",
        f"- Runtime root: `{payload['runtime_root']}`",
        f"- Preferred reports root: `{payload['preferred_reports_root']}`",
        f"- Session reports root: `{payload['session_reports_root']}`",
        f"- State root: `{payload['state_root']}`",
        f"- GCS prefix: `{payload['gcs_prefix']}`",
        "",
        "## Operator Actions",
        "",
    ]
    for action in list(payload.get("operator_actions") or []):
        lines.append(f"- {action}")
    lines.extend(["", "## Required Control-Plane Outputs", ""])
    for item in list(payload.get("required_control_plane_outputs") or []):
        lines.append(f"- `{item}`")
    if payload.get("missing_dependencies"):
        lines.extend(["", "## Missing Dependencies", ""])
        for item in list(payload.get("missing_dependencies") or []):
            lines.append(f"- `{item}`")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_handoff(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "# GCP Post-Session Assimilation Handoff",
        "",
        f"- Status: `{payload['status']}`",
        f"- Evidence source preference: `{payload['evidence_source_preference']}`",
        f"- Preferred reports root: `{payload['preferred_reports_root']}`",
        "",
        "## Operator Rule",
        "",
        "- Run governed post-session assimilation immediately after the first trusted VM session ends.",
        "- Prefer the runtime-local evidence bundle when it is available.",
        "- Refresh and review the morning brief plus execution evidence contract before any promotion decision.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = build_parser().parse_args()
    report_dir = Path(args.report_dir).resolve()
    report_dir.mkdir(parents=True, exist_ok=True)
    payload = build_payload(
        runner_repo_root=Path(args.runner_repo_root).resolve(),
        runtime_root=Path(args.runtime_root).resolve(),
        gcs_prefix=str(args.gcs_prefix),
    )
    write_json(report_dir / "gcp_post_session_assimilation_status.json", payload)
    write_markdown(report_dir / "gcp_post_session_assimilation_status.md", payload)
    write_handoff(report_dir / "gcp_post_session_assimilation_handoff.md", payload)
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
