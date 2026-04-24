from __future__ import annotations

import subprocess
from pathlib import Path

from cleanroom.code.qqq_options_30d_cleanroom.build_gcp_vm_runner_source_fingerprint_status import (
    build_local_manifest,
    build_payload,
)


def _git(repo: Path, *args: str) -> str:
    result = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, check=True)
    return result.stdout.strip()


def _init_repo(path: Path) -> None:
    path.mkdir(parents=True)
    subprocess.run(["git", "-C", str(path), "init"], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(path), "config", "user.email", "test@example.com"], check=True)
    subprocess.run(["git", "-C", str(path), "config", "user.name", "Test User"], check=True)
    (path / "alpaca_lab").mkdir()
    (path / "scripts").mkdir()
    (path / "config").mkdir()
    (path / "alpaca_lab" / "__init__.py").write_text("version = 'test'\n", encoding="utf-8")
    (path / "scripts" / "run.py").write_text("print('run')\n", encoding="utf-8")
    (path / "config" / "paper.yaml").write_text("risk: bounded\n", encoding="utf-8")
    (path / "README.md").write_text("readme\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(path), "add", "."], check=True)
    subprocess.run(["git", "-C", str(path), "commit", "-m", "init"], check=True, capture_output=True)


def test_source_fingerprint_matched_when_vm_manifest_matches_local(tmp_path: Path) -> None:
    repo = tmp_path / "runner"
    _init_repo(repo)
    entries = build_local_manifest(repo)

    payload = build_payload(
        runner_repo_root=repo,
        vm_manifest={"root": "/opt/codexalpaca/codexalpaca_repo", "entries": entries},
        vm_name="vm-execution-paper-01",
        vm_runner_path="/opt/codexalpaca/codexalpaca_repo",
        report_dir=tmp_path,
    )

    assert payload["status"] == "source_fingerprint_matched"
    assert payload["safe_to_write_source_stamp"] is True
    assert payload["issues"] == []
    assert payload["local_runner_commit"] == _git(repo, "rev-parse", "HEAD")


def test_source_fingerprint_mismatch_blocks_source_stamp(tmp_path: Path) -> None:
    repo = tmp_path / "runner"
    _init_repo(repo)
    entries = build_local_manifest(repo)
    entries = [dict(entry) for entry in entries]
    entries[0]["sha256"] = "0" * 64

    payload = build_payload(
        runner_repo_root=repo,
        vm_manifest={"root": "/opt/codexalpaca/codexalpaca_repo", "entries": entries},
        vm_name="vm-execution-paper-01",
        vm_runner_path="/opt/codexalpaca/codexalpaca_repo",
        report_dir=tmp_path,
    )

    assert payload["status"] == "source_fingerprint_mismatch"
    assert payload["safe_to_write_source_stamp"] is False
    assert payload["comparison"]["changed_count"] == 1
    assert any(issue["code"] == "vm_runner_source_fingerprint_mismatch" for issue in payload["issues"])
