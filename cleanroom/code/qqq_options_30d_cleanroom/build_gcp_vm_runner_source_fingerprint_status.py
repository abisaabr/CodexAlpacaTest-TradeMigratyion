from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[2]
DEFAULT_REPORT_DIR = REPO_ROOT / "docs" / "gcp_foundation"
DEFAULT_RUNNER_REPO_ROOT = REPO_ROOT.parent / "codexalpaca_repo_gcp_lease_lane_refreshed"
DEFAULT_VM_MANIFEST_JSON = DEFAULT_REPORT_DIR / "gcp_vm_runner_source_manifest_observed.json"
DEFAULT_VM_NAME = "vm-execution-paper-01"
DEFAULT_VM_RUNNER_PATH = "/opt/codexalpaca/codexalpaca_repo"

INCLUDE_ROOTS = {"alpaca_lab", "scripts", "config"}
INCLUDE_FILES = {".env.example", "AGENTS.md", "Dockerfile", "README.md", "docker-compose.yml", "pyproject.toml"}
EXCLUDE_DIRS = {".git", ".venv", "data", "reports", "__pycache__", ".pytest_cache", ".ruff_cache", ".mypy_cache"}
EXCLUDE_SUFFIXES = {".pyc", ".pyo"}
SOURCE_NORMALIZATION = "lf_text"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Compare VM runner source fingerprints against the canonical runner checkout.")
    parser.add_argument("--runner-repo-root", default=str(DEFAULT_RUNNER_REPO_ROOT))
    parser.add_argument("--vm-manifest-json", default=str(DEFAULT_VM_MANIFEST_JSON))
    parser.add_argument("--vm-name", default=DEFAULT_VM_NAME)
    parser.add_argument("--vm-runner-path", default=DEFAULT_VM_RUNNER_PATH)
    parser.add_argument("--report-dir", default=str(DEFAULT_REPORT_DIR))
    return parser


def _git_output(repo_root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo_root), *args],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def should_include_relative(rel: str) -> bool:
    parts = Path(rel).parts
    if not parts:
        return False
    if any(part in EXCLUDE_DIRS for part in parts):
        return False
    top = parts[0]
    if top not in INCLUDE_ROOTS and rel not in INCLUDE_FILES:
        return False
    return Path(rel).suffix not in EXCLUDE_SUFFIXES


def normalize_source_bytes(data: bytes) -> bytes:
    return data.replace(b"\r\n", b"\n").replace(b"\r", b"\n")


def build_local_manifest(runner_repo_root: Path) -> list[dict[str, Any]]:
    files = _git_output(runner_repo_root, "ls-files").splitlines()
    entries: list[dict[str, Any]] = []
    for rel in files:
        if not should_include_relative(rel):
            continue
        data = normalize_source_bytes((runner_repo_root / rel).read_bytes())
        entries.append(
            {
                "path": rel,
                "sha256": hashlib.sha256(data).hexdigest(),
                "bytes": len(data),
            }
        )
    return sorted(entries, key=lambda item: item["path"])


def compare_entries(
    local_entries: list[dict[str, Any]],
    vm_entries: list[dict[str, Any]],
) -> dict[str, Any]:
    local_by_path = {str(entry["path"]): entry for entry in local_entries}
    vm_by_path = {str(entry["path"]): entry for entry in vm_entries}
    local_paths = set(local_by_path)
    vm_paths = set(vm_by_path)
    changed_paths: list[str] = []
    for path in sorted(local_paths & vm_paths):
        local_entry = local_by_path[path]
        vm_entry = vm_by_path[path]
        if local_entry.get("sha256") != vm_entry.get("sha256") or local_entry.get("bytes") != vm_entry.get("bytes"):
            changed_paths.append(path)

    only_local = sorted(local_paths - vm_paths)
    only_vm = sorted(vm_paths - local_paths)
    return {
        "local_file_count": len(local_entries),
        "vm_file_count": len(vm_entries),
        "matching_file_count": len(local_paths & vm_paths) - len(changed_paths),
        "changed_count": len(changed_paths),
        "only_local_count": len(only_local),
        "only_vm_count": len(only_vm),
        "changed_paths": changed_paths,
        "only_local_paths": only_local,
        "only_vm_paths": only_vm,
    }


def build_payload(
    *,
    runner_repo_root: Path,
    vm_manifest: dict[str, Any],
    vm_name: str,
    vm_runner_path: str,
    report_dir: Path,
) -> dict[str, Any]:
    local_branch = _git_output(runner_repo_root, "rev-parse", "--abbrev-ref", "HEAD")
    local_commit = _git_output(runner_repo_root, "rev-parse", "HEAD")
    local_entries = build_local_manifest(runner_repo_root)
    comparison = compare_entries(local_entries, list(vm_manifest.get("entries") or []))

    mismatch_count = (
        int(comparison["changed_count"])
        + int(comparison["only_local_count"])
        + int(comparison["only_vm_count"])
    )
    status = "source_fingerprint_matched" if mismatch_count == 0 else "source_fingerprint_mismatch"
    issue_severity = "none" if status == "source_fingerprint_matched" else "error"

    issues: list[dict[str, str]] = []
    if status != "source_fingerprint_matched":
        issues.append(
            {
                "severity": issue_severity,
                "code": "vm_runner_source_fingerprint_mismatch",
                "message": "The VM runner source fingerprint does not match the canonical local runner checkout.",
            }
        )
    if status == "source_fingerprint_matched":
        next_actions = [
            "Keep the VM source stamp in place and refresh this packet after any future runner deployment.",
            "Use this packet as source-attestation support only; the exclusive-window and broker-evidence gates still control launch and promotion.",
            "Do not modify strategy selection or risk policy from this provenance packet.",
        ]
    else:
        next_actions = [
            "Do not write a source stamp while the fingerprint mismatch remains.",
            "Reconcile the VM runner deployment to the canonical runner checkout or intentionally select a different published runner commit.",
            "Recapture the VM manifest and rebuild this packet before arming a trusted execution window.",
        ]

    return {
        "generated_at": datetime.now().astimezone().isoformat(),
        "status": status,
        "vm_name": vm_name,
        "vm_runner_path": vm_runner_path,
        "vm_manifest_root": vm_manifest.get("root"),
        "runner_repo_root": str(runner_repo_root),
        "local_runner_branch": local_branch,
        "local_runner_commit": local_commit,
        "report_dir": str(report_dir),
        "include_roots": sorted(INCLUDE_ROOTS),
        "include_files": sorted(INCLUDE_FILES),
        "excluded_dirs": sorted(EXCLUDE_DIRS),
        "excluded_suffixes": sorted(EXCLUDE_SUFFIXES),
        "source_normalization": SOURCE_NORMALIZATION,
        "vm_manifest_normalization": vm_manifest.get("source_normalization") or "unknown",
        "safe_to_write_source_stamp": status == "source_fingerprint_matched",
        "broker_facing": False,
        "live_manifest_effect": "none",
        "risk_policy_effect": "none",
        "comparison": comparison,
        "issues": issues,
        "operator_read": [
            "This is a source-fingerprint comparison only; it does not start trading or change the VM.",
            "A source stamp is defensible only when the VM fingerprint matches the intended runner checkout.",
            "A mismatch means the VM may still run, but the session should not be treated as source-attested trusted evidence.",
        ],
        "next_actions": next_actions,
    }


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    comparison = dict(payload.get("comparison") or {})
    lines = [
        "# GCP VM Runner Source Fingerprint Status",
        "",
        "## Snapshot",
        "",
        f"- Generated at: `{payload['generated_at']}`",
        f"- Status: `{payload['status']}`",
        f"- VM name: `{payload['vm_name']}`",
        f"- VM runner path: `{payload['vm_runner_path']}`",
        f"- Local runner branch: `{payload['local_runner_branch']}`",
        f"- Local runner commit: `{payload['local_runner_commit']}`",
        f"- Safe to write source stamp: `{payload['safe_to_write_source_stamp']}`",
        "",
        "## Comparison",
        "",
        f"- Local file count: `{comparison.get('local_file_count')}`",
        f"- VM file count: `{comparison.get('vm_file_count')}`",
        f"- Matching file count: `{comparison.get('matching_file_count')}`",
        f"- Changed file count: `{comparison.get('changed_count')}`",
        f"- Local-only file count: `{comparison.get('only_local_count')}`",
        f"- VM-only file count: `{comparison.get('only_vm_count')}`",
        "",
        "## Mismatch Samples",
        "",
    ]
    for label, key in (
        ("Changed", "changed_paths"),
        ("Local-only", "only_local_paths"),
        ("VM-only", "only_vm_paths"),
    ):
        rows = list(comparison.get(key) or [])[:25]
        lines.append(f"### {label}")
        lines.append("")
        if rows:
            for row in rows:
                lines.append(f"- `{row}`")
        else:
            lines.append("- none")
        lines.append("")

    lines.extend(["## Issues", ""])
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
        runner_repo_root=Path(args.runner_repo_root),
        vm_manifest=read_json(Path(args.vm_manifest_json)),
        vm_name=args.vm_name,
        vm_runner_path=args.vm_runner_path,
        report_dir=report_dir,
    )
    write_json(report_dir / "gcp_vm_runner_source_fingerprint_status.json", payload)
    write_markdown(report_dir / "gcp_vm_runner_source_fingerprint_status.md", payload)
    write_markdown(report_dir / "gcp_vm_runner_source_fingerprint_handoff.md", payload)
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
