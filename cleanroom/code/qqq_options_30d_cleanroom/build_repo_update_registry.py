from __future__ import annotations

import argparse
import csv
import json
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[2]
WORKSPACE_ROOT = REPO_ROOT.parent


def first_existing_path(*paths: Path) -> Path:
    for path in paths:
        if path.exists():
            return path
    return paths[0]


DEFAULT_EXECUTION_REPO_ROOT = first_existing_path(
    Path(r"C:\Users\rabisaab\Downloads\codexalpaca_repo"),
    WORKSPACE_ROOT / "codexalpaca_repo",
    Path(r"C:\Users\rabisaab\OneDrive\CodexAlpaca\downloads_remaining_20260417\folders\codexalpaca_repo"),
)
DEFAULT_REPORT_DIR = REPO_ROOT / "docs" / "repo_updates"
RUNNER_REQUIRED_COMMITS = ["50764cf", "4292514", "f6d6168", "8037710", "bdd7663", "1e72e18"]


@dataclass(frozen=True)
class RepoSpec:
    name: str
    role: str
    path: Path
    remote: str
    branch: str
    required_commits: tuple[str, ...] = ()
    ignore_dirty_prefixes: tuple[str, ...] = ()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build a control-plane repo update registry for the execution and control repos."
    )
    parser.add_argument("--control-plane-root", default=str(REPO_ROOT))
    parser.add_argument("--execution-repo-root", default=str(DEFAULT_EXECUTION_REPO_ROOT))
    parser.add_argument("--report-dir", default=str(DEFAULT_REPORT_DIR))
    parser.add_argument("--skip-fetch", action="store_true")
    return parser


def run_git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )


def git_output(repo: Path, *args: str) -> str | None:
    completed = run_git(repo, *args)
    if completed.returncode != 0:
        return None
    return completed.stdout.strip()


def git_bool(repo: Path, *args: str) -> bool:
    return run_git(repo, *args).returncode == 0


def classify_repo_status(
    *,
    repo_exists: bool,
    fetch_ok: bool,
    remote_ref_exists: bool,
    dirty: bool,
    branch_matches_expected: bool,
    ahead_count: int,
    behind_count: int,
    missing_required_commits: list[str],
) -> str:
    if not repo_exists:
        return "missing_repo"
    if not fetch_ok:
        return "fetch_error"
    if not remote_ref_exists:
        return "remote_ref_missing"
    if dirty or not branch_matches_expected or ahead_count > 0:
        return "attention_required"
    if behind_count > 0 or missing_required_commits:
        return "update_required"
    return "up_to_date"


def normalize_status_path(line: str) -> str:
    text = line.strip()
    if len(text) < 4:
        return ""
    path = text[3:].strip()
    if " -> " in path:
        path = path.split(" -> ", 1)[1].strip()
    return path.replace("\\", "/")


def build_repo_result(spec: RepoSpec, *, skip_fetch: bool) -> dict[str, Any]:
    repo_exists = spec.path.exists()
    result: dict[str, Any] = {
        "name": spec.name,
        "role": spec.role,
        "repo_path": str(spec.path),
        "remote": spec.remote,
        "expected_branch": spec.branch,
        "repo_exists": repo_exists,
    }
    if not repo_exists:
        result.update(
            {
                "status": "missing_repo",
                "recommendation": "Clone or restore this repo before relying on the machine for governed updates or execution.",
            }
        )
        return result

    fetch_ok = True
    fetch_error = ""
    if not skip_fetch:
        fetch = run_git(spec.path, "fetch", spec.remote, spec.branch, "--quiet")
        fetch_ok = fetch.returncode == 0
        fetch_error = fetch.stderr.strip() if fetch.returncode != 0 else ""

    current_branch = git_output(spec.path, "rev-parse", "--abbrev-ref", "HEAD") or ""
    head_sha = git_output(spec.path, "rev-parse", "HEAD") or ""
    remote_ref = f"{spec.remote}/{spec.branch}"
    remote_head_sha = git_output(spec.path, "rev-parse", remote_ref) or ""
    remote_ref_exists = bool(remote_head_sha)
    status_porcelain = git_output(spec.path, "status", "--porcelain") or ""
    dirty_lines = []
    for line in status_porcelain.splitlines():
        if not line.strip():
            continue
        normalized_path = normalize_status_path(line)
        if normalized_path and any(
            normalized_path.startswith(prefix.rstrip("/\\") + "/") or normalized_path == prefix.rstrip("/\\")
            for prefix in spec.ignore_dirty_prefixes
        ):
            continue
        dirty_lines.append(line)
    dirty = bool(dirty_lines)

    ahead_count = 0
    behind_count = 0
    if remote_ref_exists and head_sha:
        rev_list = git_output(spec.path, "rev-list", "--left-right", "--count", f"HEAD...{remote_ref}") or ""
        parts = rev_list.split()
        if len(parts) >= 2:
            ahead_count = int(parts[0])
            behind_count = int(parts[1])

    present_required_commits: list[str] = []
    missing_required_commits: list[str] = []
    for commit in spec.required_commits:
        if git_bool(spec.path, "merge-base", "--is-ancestor", commit, "HEAD"):
            present_required_commits.append(commit)
        else:
            missing_required_commits.append(commit)

    branch_matches_expected = current_branch == spec.branch
    status = classify_repo_status(
        repo_exists=repo_exists,
        fetch_ok=fetch_ok,
        remote_ref_exists=remote_ref_exists,
        dirty=dirty,
        branch_matches_expected=branch_matches_expected,
        ahead_count=ahead_count,
        behind_count=behind_count,
        missing_required_commits=missing_required_commits,
    )

    recommendation_parts: list[str] = []
    if status == "up_to_date":
        recommendation_parts.append("No GitHub update action is required right now.")
    else:
        if not fetch_ok:
            recommendation_parts.append("Fix remote connectivity or authentication before trusting update status.")
        if not branch_matches_expected:
            recommendation_parts.append(f"Switch to `{spec.branch}` or inspect why this machine is pinned elsewhere.")
        if dirty:
            recommendation_parts.append("Review or stash local modifications before integrating GitHub updates.")
        if behind_count > 0:
            recommendation_parts.append(f"Integrate `{behind_count}` remote commit(s) from `{remote_ref}` deliberately.")
        if missing_required_commits:
            recommendation_parts.append(
                "Verify the required institutional commits are present: "
                + ", ".join(f"`{commit}`" for commit in missing_required_commits)
                + "."
            )
        if ahead_count > 0:
            recommendation_parts.append("Inspect local-only commits before treating the machine as a controlled replica.")
        if not recommendation_parts:
            recommendation_parts.append("Inspect this repo manually before continuing.")

    result.update(
        {
            "status": status,
            "fetch_ok": fetch_ok,
            "fetch_error": fetch_error,
            "current_branch": current_branch,
            "branch_matches_expected": branch_matches_expected,
            "head_sha": head_sha,
            "remote_ref": remote_ref,
            "remote_head_sha": remote_head_sha,
            "remote_ref_exists": remote_ref_exists,
            "ahead_count": ahead_count,
            "behind_count": behind_count,
            "dirty": dirty,
            "dirty_file_count": len(dirty_lines),
            "dirty_files_preview": dirty_lines[:10],
            "required_commits": list(spec.required_commits),
            "present_required_commits": present_required_commits,
            "missing_required_commits": missing_required_commits,
            "safe_to_run_without_update_review": status == "up_to_date",
            "recommendation": " ".join(recommendation_parts).strip(),
        }
    )
    return result


def build_payload(
    *,
    control_plane_root: Path,
    execution_repo_root: Path,
    skip_fetch: bool,
) -> dict[str, Any]:
    specs = [
        RepoSpec(
            name="control_plane",
            role="governance_and_prompts",
            path=control_plane_root,
            remote="origin",
            branch="main",
            ignore_dirty_prefixes=("docs/repo_updates",),
        ),
        RepoSpec(
            name="execution_repo",
            role="paper_runner_runtime",
            path=execution_repo_root,
            remote="origin",
            branch="codex/qqq-paper-portfolio",
            required_commits=tuple(RUNNER_REQUIRED_COMMITS),
        ),
    ]

    repos = [build_repo_result(spec, skip_fetch=skip_fetch) for spec in specs]
    update_required = [row["name"] for row in repos if row["status"] == "update_required"]
    attention_required = [row["name"] for row in repos if row["status"] in {"attention_required", "fetch_error", "remote_ref_missing", "missing_repo"}]
    fully_current = [row["name"] for row in repos if row["status"] == "up_to_date"]

    overall_status = "ready"
    if attention_required:
        overall_status = "attention_required"
    elif update_required:
        overall_status = "update_required"

    overall_actions: list[str] = []
    if update_required:
        overall_actions.append(
            "Integrate remote updates for: " + ", ".join(f"`{name}`" for name in update_required) + "."
        )
    if attention_required:
        overall_actions.append(
            "Resolve local branch, fetch, or dirty-worktree issues for: "
            + ", ".join(f"`{name}`" for name in attention_required)
            + "."
        )
    if not overall_actions:
        overall_actions.append("Both governed repos are current enough to proceed without update action.")

    payload = {
        "generated_at": datetime.now().isoformat(),
        "overall_status": overall_status,
        "safe_to_run_nightly_cycle": overall_status == "ready",
        "safe_to_run_execution_plane_without_update_review": overall_status == "ready",
        "repos": repos,
        "summary": {
            "repo_count": len(repos),
            "up_to_date_repo_count": len(fully_current),
            "update_required_repo_count": len(update_required),
            "attention_required_repo_count": len(attention_required),
            "fully_current_repos": fully_current,
            "update_required_repos": update_required,
            "attention_required_repos": attention_required,
        },
        "overall_actions": overall_actions,
    }
    return payload


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def write_csv(path: Path, payload: dict[str, Any]) -> None:
    rows = []
    for row in payload["repos"]:
        rows.append(
            {
                "name": row["name"],
                "role": row["role"],
                "status": row["status"],
                "repo_path": row["repo_path"],
                "current_branch": row.get("current_branch", ""),
                "expected_branch": row.get("expected_branch", ""),
                "branch_matches_expected": row.get("branch_matches_expected"),
                "ahead_count": row.get("ahead_count", 0),
                "behind_count": row.get("behind_count", 0),
                "dirty": row.get("dirty", False),
                "dirty_file_count": row.get("dirty_file_count", 0),
                "missing_required_commits": ",".join(row.get("missing_required_commits", [])),
                "safe_to_run_without_update_review": row.get("safe_to_run_without_update_review", False),
                "recommendation": row.get("recommendation", ""),
            }
        )
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames = sorted({key for row in rows for key in row.keys()})
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def write_registry_markdown(path: Path, payload: dict[str, Any]) -> None:
    lines: list[str] = []
    lines.append("# Repo Update Registry")
    lines.append("")
    lines.append("This registry is the governed answer to whether the machine is current enough, clean enough, and on the right branch to trust GitHub-backed control-plane and execution-plane work.")
    lines.append("")
    lines.append("## Snapshot")
    lines.append("")
    lines.append(f"- Generated at: `{payload['generated_at']}`")
    lines.append(f"- Overall status: `{payload['overall_status']}`")
    lines.append(f"- Safe to run nightly cycle: `{str(bool(payload['safe_to_run_nightly_cycle'])).lower()}`")
    lines.append(f"- Safe to run execution plane without update review: `{str(bool(payload['safe_to_run_execution_plane_without_update_review'])).lower()}`")
    lines.append("")
    lines.append("## Repo Status")
    lines.append("")
    for row in payload["repos"]:
        lines.append(f"### `{row['name']}`")
        lines.append("")
        lines.append(f"- Role: `{row['role']}`")
        lines.append(f"- Repo path: `{row['repo_path']}`")
        lines.append(f"- Status: `{row['status']}`")
        lines.append(f"- Current branch: `{row.get('current_branch', '')}`")
        lines.append(f"- Expected branch: `{row.get('expected_branch', '')}`")
        lines.append(f"- Branch matches expected: `{str(bool(row.get('branch_matches_expected', False))).lower()}`")
        lines.append(f"- Ahead / behind: `{row.get('ahead_count', 0)}` / `{row.get('behind_count', 0)}`")
        lines.append(f"- Dirty worktree: `{str(bool(row.get('dirty', False))).lower()}`")
        lines.append(f"- Missing required commits: `{', '.join(row.get('missing_required_commits', [])) or 'none'}`")
        lines.append(f"- Safe to run without update review: `{str(bool(row.get('safe_to_run_without_update_review', False))).lower()}`")
        lines.append(f"- Recommendation: {row.get('recommendation', '')}")
        lines.append("")
    lines.append("## Overall Actions")
    lines.append("")
    for action in payload["overall_actions"]:
        lines.append(f"- {action}")
    lines.append("")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_handoff_markdown(path: Path, payload: dict[str, Any]) -> None:
    lines: list[str] = []
    lines.append("# Repo Update Handoff")
    lines.append("")
    lines.append("## Snapshot")
    lines.append("")
    lines.append(f"- Overall status: `{payload['overall_status']}`")
    lines.append(f"- Safe to run nightly cycle: `{str(bool(payload['safe_to_run_nightly_cycle'])).lower()}`")
    lines.append(f"- Safe to run execution plane without update review: `{str(bool(payload['safe_to_run_execution_plane_without_update_review'])).lower()}`")
    lines.append("")
    lines.append("## Required Actions")
    lines.append("")
    for action in payload["overall_actions"]:
        lines.append(f"- {action}")
    lines.append("")
    lines.append("## Repo Decisions")
    lines.append("")
    for row in payload["repos"]:
        lines.append(f"- `{row['name']}`: `{row['status']}`. {row.get('recommendation', '')}")
    lines.append("")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = build_parser().parse_args()
    control_plane_root = Path(args.control_plane_root).resolve()
    execution_repo_root = Path(args.execution_repo_root).resolve()
    report_dir = Path(args.report_dir).resolve()
    report_dir.mkdir(parents=True, exist_ok=True)

    payload = build_payload(
        control_plane_root=control_plane_root,
        execution_repo_root=execution_repo_root,
        skip_fetch=bool(args.skip_fetch),
    )

    write_json(report_dir / "repo_update_registry.json", payload)
    write_csv(report_dir / "repo_update_registry.csv", payload)
    write_registry_markdown(report_dir / "repo_update_registry.md", payload)
    write_json(report_dir / "repo_update_handoff.json", payload)
    write_handoff_markdown(report_dir / "repo_update_handoff.md", payload)
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
