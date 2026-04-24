from __future__ import annotations

import subprocess
from pathlib import Path

from cleanroom.code.qqq_options_30d_cleanroom.build_gcp_vm_runner_provenance_status import build_payload


def _git(repo: Path, *args: str) -> str:
    result = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, check=True)
    return result.stdout.strip()


def _init_repo(path: Path) -> tuple[str, str]:
    path.mkdir(parents=True)
    subprocess.run(["git", "-C", str(path), "init"], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(path), "config", "user.email", "test@example.com"], check=True)
    subprocess.run(["git", "-C", str(path), "config", "user.name", "Test User"], check=True)
    (path / "README.md").write_text("test\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(path), "add", "README.md"], check=True)
    subprocess.run(["git", "-C", str(path), "commit", "-m", "init"], check=True, capture_output=True)
    return _git(path, "rev-parse", "--abbrev-ref", "HEAD"), _git(path, "rev-parse", "HEAD")


def test_provenance_matched_when_vm_commit_matches_local(tmp_path: Path) -> None:
    repo = tmp_path / "runner"
    branch, commit = _init_repo(repo)

    payload = build_payload(
        runner_repo_root=repo,
        vm_name="vm-execution-paper-01",
        vm_runner_path="/opt/codexalpaca/codexalpaca_repo",
        vm_path_present=True,
        vm_git_present=True,
        vm_runner_branch=branch,
        vm_runner_commit=commit,
        source_fingerprint=None,
        report_dir=tmp_path,
        gcs_prefix="gs://example/gcp_foundation",
    )

    assert payload["status"] == "provenance_matched"
    assert payload["vm_commit_matches_local"] is True
    assert payload["issues"] == []


def test_provenance_unstamped_when_vm_has_no_commit(tmp_path: Path) -> None:
    repo = tmp_path / "runner"
    _init_repo(repo)

    payload = build_payload(
        runner_repo_root=repo,
        vm_name="vm-execution-paper-01",
        vm_runner_path="/opt/codexalpaca/codexalpaca_repo",
        vm_path_present=True,
        vm_git_present=False,
        vm_runner_branch="",
        vm_runner_commit="",
        source_fingerprint=None,
        report_dir=tmp_path,
        gcs_prefix="gs://example/gcp_foundation",
    )

    assert payload["status"] == "provenance_unstamped"
    assert any(issue["code"] == "vm_runner_commit_unstamped" for issue in payload["issues"])


def test_provenance_blocks_when_vm_path_missing(tmp_path: Path) -> None:
    repo = tmp_path / "runner"
    _init_repo(repo)

    payload = build_payload(
        runner_repo_root=repo,
        vm_name="vm-execution-paper-01",
        vm_runner_path="/opt/codexalpaca/codexalpaca_repo",
        vm_path_present=False,
        vm_git_present=False,
        vm_runner_branch="",
        vm_runner_commit="",
        source_fingerprint=None,
        report_dir=tmp_path,
        gcs_prefix="gs://example/gcp_foundation",
    )

    assert payload["status"] == "blocked_vm_runner_missing"
    assert any(issue["severity"] == "error" for issue in payload["issues"])


def test_provenance_blocks_when_source_fingerprint_mismatches(tmp_path: Path) -> None:
    repo = tmp_path / "runner"
    _init_repo(repo)

    payload = build_payload(
        runner_repo_root=repo,
        vm_name="vm-execution-paper-01",
        vm_runner_path="/opt/codexalpaca/codexalpaca_repo",
        vm_path_present=True,
        vm_git_present=False,
        vm_runner_branch="",
        vm_runner_commit="",
        source_fingerprint={
            "status": "source_fingerprint_mismatch",
            "safe_to_write_source_stamp": False,
            "comparison": {"changed_count": 1},
        },
        report_dir=tmp_path,
        gcs_prefix="gs://example/gcp_foundation",
    )

    assert payload["status"] == "blocked_vm_runner_source_mismatch"
    assert payload["source_fingerprint_status"] == "source_fingerprint_mismatch"
    assert any(issue["code"] == "vm_runner_source_fingerprint_mismatch" for issue in payload["issues"])
