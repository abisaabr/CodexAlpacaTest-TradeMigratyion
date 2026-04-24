[CmdletBinding()]
param(
    [string]$ControlPlaneRoot = "",
    [string]$RunnerRepoRoot = "",
    [string]$ProjectId = "codexalpaca",
    [string]$VmName = "vm-execution-paper-01",
    [string]$Zone = "us-east1-b",
    [string]$VmRunnerPath = "/opt/codexalpaca/codexalpaca_repo",
    [switch]$SkipVmPytest,
    [switch]$MirrorToGcs,
    [string]$GcsPrefix = "gs://codexalpaca-control-us/gcp_foundation"
)

$ErrorActionPreference = "Stop"

function Resolve-PythonCommand {
    param([string]$RunnerRepoRoot)

    if ($RunnerRepoRoot) {
        $venvPython = Join-Path $RunnerRepoRoot ".venv\Scripts\python.exe"
        if (Test-Path $venvPython) {
            return @($venvPython)
        }
    }
    if (Get-Command py -ErrorAction SilentlyContinue) {
        return @("py", "-3")
    }
    if (Get-Command python -ErrorAction SilentlyContinue) {
        return @("python")
    }
    throw "No Python interpreter found. Provide -RunnerRepoRoot with a venv or expose py/python on PATH."
}

function Invoke-PythonScript {
    param(
        [string[]]$PythonCommand,
        [string]$ScriptPath,
        [string[]]$Arguments
    )
    $command = @($PythonCommand + @($ScriptPath) + $Arguments)
    & $command[0] $command[1..($command.Length - 1)]
    if ($LASTEXITCODE -ne 0) {
        throw "Python script failed with exit code $LASTEXITCODE`: $ScriptPath"
    }
}

function Add-FlagIfTrue {
    param(
        [string[]]$Arguments,
        [string]$Flag,
        [bool]$Value
    )
    if ($Value) {
        return @($Arguments + @($Flag))
    }
    return $Arguments
}

if (-not $ControlPlaneRoot) {
    $ControlPlaneRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..\..")).Path
}
if (-not $RunnerRepoRoot) {
    $RunnerRepoRoot = (Resolve-Path (Join-Path $ControlPlaneRoot "..\codexalpaca_repo_gcp_lease_lane_refreshed")).Path
}
if (-not (Get-Command gcloud -ErrorAction SilentlyContinue)) {
    throw "gcloud CLI not found on PATH. Cannot refresh VM pre-arm evidence."
}

$reportDir = Join-Path $ControlPlaneRoot "docs\gcp_foundation"
$observedPath = Join-Path $reportDir "gcp_vm_prearm_observed.json"
$manifestPath = Join-Path $reportDir "gcp_vm_runner_source_manifest_observed.json"
$pythonCommand = Resolve-PythonCommand -RunnerRepoRoot $RunnerRepoRoot
$remoteScript = "/tmp/codexalpaca_vm_prearm_preflight.py"
$localScript = Join-Path ([System.IO.Path]::GetTempPath()) ("codexalpaca_vm_prearm_preflight_" + $PID + ".py")

$remoteScriptContent = @'
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


INCLUDE_ROOTS = {"alpaca_lab", "scripts", "config"}
INCLUDE_FILES = {".env.example", "AGENTS.md", "Dockerfile", "README.md", "docker-compose.yml", "pyproject.toml"}
EXCLUDE_DIRS = {".git", ".venv", "data", "reports", "__pycache__", ".pytest_cache", ".ruff_cache", ".mypy_cache"}
EXCLUDE_SUFFIXES = {".pyc", ".pyo"}


def run_command(args: list[str], *, cwd: Path, timeout: int = 180) -> dict:
    try:
        result = subprocess.run(args, cwd=str(cwd), capture_output=True, text=True, timeout=timeout)
    except Exception as exc:
        return {"status": "failed", "returncode": None, "stdout": "", "stderr": str(exc), "summary": str(exc)}
    lines = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    return {
        "status": "passed" if result.returncode == 0 else "failed",
        "returncode": result.returncode,
        "stdout": result.stdout[-4000:],
        "stderr": result.stderr[-4000:],
        "summary": lines[-1] if lines else ("passed" if result.returncode == 0 else "failed"),
    }


def git_output(root: Path, *args: str) -> str:
    result = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True)
    if result.returncode != 0:
        return ""
    return result.stdout.strip()


def read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return {}


def parse_env(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


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


def build_manifest(root: Path) -> dict:
    entries: list[dict] = []
    if not root.exists():
        return {"root": str(root), "source_normalization": "lf_text", "entries": entries}
    for current_root, dirnames, filenames in os.walk(root):
        dirnames[:] = [name for name in dirnames if name not in EXCLUDE_DIRS]
        for filename in filenames:
            path = Path(current_root) / filename
            rel = path.relative_to(root).as_posix()
            if not should_include_relative(rel):
                continue
            data = normalize_source_bytes(path.read_bytes())
            entries.append({"path": rel, "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)})
    return {"root": str(root), "source_normalization": "lf_text", "entries": sorted(entries, key=lambda item: item["path"])}


def writable(root: Path, relative: str) -> bool:
    path = root / relative
    if not path.exists() or not path.is_dir():
        return False
    try:
        fd, temp_path = tempfile.mkstemp(prefix=".codex_prearm_", dir=str(path))
        os.close(fd)
        os.unlink(temp_path)
        return True
    except Exception:
        return False


def trader_processes() -> list[dict]:
    proc = Path("/proc")
    if not proc.exists():
        return []
    current_pid = os.getpid()
    hits: list[dict] = []
    for child in proc.iterdir():
        if not child.name.isdigit() or int(child.name) == current_pid:
            continue
        try:
            raw = (child / "cmdline").read_bytes()
        except OSError:
            continue
        args = [item.decode("utf-8", "replace") for item in raw.split(b"\0") if item]
        if any(arg.endswith("run_multi_ticker_portfolio_paper_trader.py") for arg in args):
            hits.append({"pid": int(child.name), "args": args})
    return hits


def load_ownership(root: Path) -> dict:
    try:
        sys.path.insert(0, str(root))
        from alpaca_lab.multi_ticker_portfolio import load_portfolio_config

        config = load_portfolio_config(root / "config" / "multi_ticker_paper_portfolio.yaml")
        ownership = config.ownership
        enabled = bool(ownership.enabled)
        backend = str(ownership.lease_backend)
        lease_class = "NoopOwnershipLease"
        if enabled and backend == "gcs_generation_match":
            lease_class = "GcsGenerationMatchOwnershipLease"
        elif enabled:
            lease_class = "FileOwnershipLease"
        return {
            "enabled": enabled,
            "lease_backend": backend,
            "lease_path": str(ownership.lease_path),
            "gcs_lease_uri": str(ownership.gcs_lease_uri) if ownership.gcs_lease_uri else None,
            "machine_label": str(ownership.machine_label),
            "lease_class": lease_class,
            "source": "portfolio_config",
        }
    except Exception as exc:
        env_values = parse_env(root / ".env")
        enabled = env_values.get("MULTI_TICKER_OWNERSHIP_ENABLED", "").lower() in {"1", "true", "yes", "on"}
        backend = env_values.get("MULTI_TICKER_OWNERSHIP_LEASE_BACKEND") or "file"
        lease_class = "NoopOwnershipLease"
        if enabled and backend == "gcs_generation_match":
            lease_class = "GcsGenerationMatchOwnershipLease"
        elif enabled:
            lease_class = "FileOwnershipLease"
        return {
            "enabled": enabled,
            "lease_backend": backend,
            "lease_path": env_values.get("MULTI_TICKER_OWNERSHIP_LEASE_PATH") or "reports/multi_ticker_portfolio/state/ownership_lease.json",
            "gcs_lease_uri": env_values.get("MULTI_TICKER_OWNERSHIP_GCS_LEASE_URI") or None,
            "machine_label": env_values.get("MULTI_TICKER_MACHINE_LABEL") or "",
            "lease_class": lease_class,
            "source": "env_fallback",
            "load_error": str(exc),
        }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runner-path", required=True)
    parser.add_argument("--skip-pytest", action="store_true")
    args = parser.parse_args()

    root = Path(args.runner_path)
    runner_python = root / ".venv" / "bin" / "python"
    if not runner_python.exists():
        runner_python = Path(sys.executable)

    stamp = read_json(root / ".codexalpaca_source_stamp.json")
    git_present = (root / ".git").exists() and bool(git_output(root, "rev-parse", "HEAD"))
    git_commit = git_output(root, "rev-parse", "HEAD") if git_present else ""
    git_branch = git_output(root, "rev-parse", "--abbrev-ref", "HEAD") if git_present else ""
    observed_commit = git_commit or str(stamp.get("commit") or stamp.get("runner_commit") or "")
    observed_branch = git_branch or str(stamp.get("branch") or stamp.get("runner_branch") or "")
    doctor = run_command([str(runner_python), "scripts/doctor.py", "--skip-connectivity"], cwd=root, timeout=180)
    if args.skip_pytest:
        pytest = {"status": "not_run", "returncode": None, "stdout": "", "stderr": "", "summary": "skipped by pre-arm preflight"}
    else:
        pytest = run_command([str(runner_python), "-m", "pytest", "-q"], cwd=root, timeout=600)
    processes = trader_processes()
    payload = {
        "vm_path_present": root.exists(),
        "vm_git_present": git_present,
        "vm_runner_branch": observed_branch,
        "vm_runner_commit": observed_commit,
        "source_stamp": stamp,
        "vm_source_manifest": build_manifest(root),
        "path_checks": {
            "data": writable(root, "data"),
            "reports": writable(root, "reports"),
            "state_root": writable(root, "reports/multi_ticker_portfolio/state"),
            "run_root": writable(root, "reports/multi_ticker_portfolio/runs"),
            "pytest_cache": writable(root, ".pytest_cache"),
        },
        "doctor": doctor,
        "pytest": pytest,
        "trader_process_absent": len(processes) == 0,
        "trader_processes": processes,
        "ownership": load_ownership(root),
    }
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
'@

New-Item -ItemType Directory -Path $reportDir -Force | Out-Null
Set-Content -Path $localScript -Value $remoteScriptContent -Encoding utf8

try {
    & gcloud compute scp `
        --project $ProjectId `
        --zone $Zone `
        --tunnel-through-iap `
        $localScript `
        "${VmName}:$remoteScript" | Out-Host
    if ($LASTEXITCODE -ne 0) {
        throw "gcloud compute scp failed with exit code $LASTEXITCODE."
    }

    $remoteCommand = "cd '$VmRunnerPath' && ./.venv/bin/python '$remoteScript' --runner-path '$VmRunnerPath'"
    if ($SkipVmPytest) {
        $remoteCommand = "$remoteCommand --skip-pytest"
    }
    $observedRaw = & gcloud compute ssh `
        $VmName `
        --project $ProjectId `
        --zone $Zone `
        --tunnel-through-iap `
        --command $remoteCommand
    if ($LASTEXITCODE -ne 0) {
        throw "gcloud compute ssh preflight failed with exit code $LASTEXITCODE."
    }
    $observedJson = ($observedRaw | Out-String).Trim()
    $observed = $observedJson | ConvertFrom-Json
    Set-Content -Path $observedPath -Value $observedJson -Encoding utf8
    $observed.vm_source_manifest | ConvertTo-Json -Depth 100 | Set-Content -Path $manifestPath -Encoding utf8

    Invoke-PythonScript -PythonCommand $pythonCommand -ScriptPath (Join-Path $PSScriptRoot "build_gcp_vm_runner_source_fingerprint_status.py") -Arguments @(
        "--runner-repo-root", $RunnerRepoRoot,
        "--vm-manifest-json", $manifestPath,
        "--vm-name", $VmName,
        "--vm-runner-path", $VmRunnerPath,
        "--report-dir", $reportDir
    )

    $provenanceArgs = @(
        "--runner-repo-root", $RunnerRepoRoot,
        "--vm-name", $VmName,
        "--vm-runner-path", $VmRunnerPath,
        "--source-fingerprint-json", (Join-Path $reportDir "gcp_vm_runner_source_fingerprint_status.json"),
        "--report-dir", $reportDir,
        "--gcs-prefix", $GcsPrefix
    )
    if ($observed.vm_runner_branch) {
        $provenanceArgs += @("--vm-runner-branch", [string]$observed.vm_runner_branch)
    }
    if ($observed.vm_runner_commit) {
        $provenanceArgs += @("--vm-runner-commit", [string]$observed.vm_runner_commit)
    }
    $provenanceArgs = Add-FlagIfTrue -Arguments $provenanceArgs -Flag "--vm-path-present" -Value ([bool]$observed.vm_path_present)
    $provenanceArgs = Add-FlagIfTrue -Arguments $provenanceArgs -Flag "--vm-git-present" -Value ([bool]$observed.vm_git_present)
    Invoke-PythonScript -PythonCommand $pythonCommand -ScriptPath (Join-Path $PSScriptRoot "build_gcp_vm_runner_provenance_status.py") -Arguments $provenanceArgs

    $runtimeArgs = @(
        "--vm-name", $VmName,
        "--vm-runner-path", $VmRunnerPath,
        "--source-provenance-json", (Join-Path $reportDir "gcp_vm_runner_provenance_status.json"),
        "--doctor-status", [string]$observed.doctor.status,
        "--vm-pytest-status", [string]$observed.pytest.status,
        "--vm-pytest-summary", [string]$observed.pytest.summary,
        "--ownership-backend", [string]$observed.ownership.lease_backend,
        "--ownership-lease-class", [string]$observed.ownership.lease_class,
        "--ownership-machine-label", [string]$observed.ownership.machine_label,
        "--report-dir", $reportDir
    )
    $runtimeArgs = Add-FlagIfTrue -Arguments $runtimeArgs -Flag "--data-writable" -Value ([bool]$observed.path_checks.data)
    $runtimeArgs = Add-FlagIfTrue -Arguments $runtimeArgs -Flag "--reports-writable" -Value ([bool]$observed.path_checks.reports)
    $runtimeArgs = Add-FlagIfTrue -Arguments $runtimeArgs -Flag "--state-root-writable" -Value ([bool]$observed.path_checks.state_root)
    $runtimeArgs = Add-FlagIfTrue -Arguments $runtimeArgs -Flag "--run-root-writable" -Value ([bool]$observed.path_checks.run_root)
    $runtimeArgs = Add-FlagIfTrue -Arguments $runtimeArgs -Flag "--pytest-cache-writable" -Value ([bool]$observed.path_checks.pytest_cache)
    $runtimeArgs = Add-FlagIfTrue -Arguments $runtimeArgs -Flag "--trader-process-absent" -Value ([bool]$observed.trader_process_absent)
    $runtimeArgs = Add-FlagIfTrue -Arguments $runtimeArgs -Flag "--ownership-enabled" -Value ([bool]$observed.ownership.enabled)
    if ($observed.ownership.gcs_lease_uri) {
        $runtimeArgs += @("--gcs-lease-uri", [string]$observed.ownership.gcs_lease_uri)
    }
    Invoke-PythonScript -PythonCommand $pythonCommand -ScriptPath (Join-Path $PSScriptRoot "build_gcp_vm_runtime_readiness_status.py") -Arguments $runtimeArgs

    Invoke-PythonScript -PythonCommand $pythonCommand -ScriptPath (Join-Path $PSScriptRoot "build_gcp_execution_exclusive_window_status.py") -Arguments @("--report-dir", $reportDir, "--project-id", $ProjectId, "--vm-name", $VmName)
    Invoke-PythonScript -PythonCommand $pythonCommand -ScriptPath (Join-Path $PSScriptRoot "build_gcp_execution_trusted_validation_session_status.py") -Arguments @("--report-dir", $reportDir, "--project-id", $ProjectId, "--vm-name", $VmName, "--runner-repo-root", $RunnerRepoRoot)
    Invoke-PythonScript -PythonCommand $pythonCommand -ScriptPath (Join-Path $PSScriptRoot "build_gcp_execution_trusted_validation_launch_pack.py") -Arguments @("--report-dir", $reportDir, "--project-id", $ProjectId, "--vm-name", $VmName, "--zone", $Zone)
    Invoke-PythonScript -PythonCommand $pythonCommand -ScriptPath (Join-Path $PSScriptRoot "build_gcp_execution_closeout_status.py") -Arguments @("--report-dir", $reportDir, "--vm-name", $VmName, "--gcs-prefix", $GcsPrefix)
    Invoke-PythonScript -PythonCommand $pythonCommand -ScriptPath (Join-Path $PSScriptRoot "build_gcp_execution_trusted_validation_operator_packet.py") -Arguments @("--report-dir", $reportDir, "--project-id", $ProjectId, "--vm-name", $VmName, "--zone", $Zone, "--gcs-prefix", $GcsPrefix)
    Invoke-PythonScript -PythonCommand $pythonCommand -ScriptPath (Join-Path $PSScriptRoot "build_gcp_execution_prearm_preflight.py") -Arguments @("--report-dir", $reportDir)

    if ($MirrorToGcs) {
        $mirrorFiles = @(
            "gcp_vm_prearm_observed.json",
            "gcp_vm_runner_source_manifest_observed.json",
            "gcp_vm_runner_source_fingerprint_status.json",
            "gcp_vm_runner_source_fingerprint_status.md",
            "gcp_vm_runner_source_fingerprint_handoff.md",
            "gcp_vm_runner_provenance_status.json",
            "gcp_vm_runner_provenance_status.md",
            "gcp_vm_runner_provenance_handoff.md",
            "gcp_vm_runtime_readiness_status.json",
            "gcp_vm_runtime_readiness_status.md",
            "gcp_vm_runtime_readiness_handoff.md",
            "gcp_execution_trusted_validation_operator_packet.json",
            "gcp_execution_trusted_validation_operator_packet.md",
            "gcp_execution_trusted_validation_operator_handoff.md",
            "gcp_execution_prearm_preflight.json",
            "gcp_execution_prearm_preflight.md",
            "gcp_execution_prearm_preflight_handoff.md"
        ) | ForEach-Object { Join-Path $reportDir $_ }
        & gcloud storage cp @mirrorFiles $GcsPrefix
        if ($LASTEXITCODE -ne 0) {
            throw "gcloud storage cp failed with exit code $LASTEXITCODE."
        }
    }

    $prearm = Get-Content -Path (Join-Path $reportDir "gcp_execution_prearm_preflight.json") -Raw | ConvertFrom-Json
    $summary = @{
        generated_at = [datetimeoffset]::Now.ToString("o")
        control_plane_root = $ControlPlaneRoot
        runner_repo_root = $RunnerRepoRoot
        vm_name = $VmName
        vm_runner_path = $VmRunnerPath
        prearm_status = $prearm.status
        next_operator_action = $prearm.next_operator_action
        observed_json = $observedPath
        source_manifest_json = $manifestPath
        prearm_handoff = Join-Path $reportDir "gcp_execution_prearm_preflight_handoff.md"
        broker_facing = $false
        mirrored_to_gcs = [bool]$MirrorToGcs
        gcs_prefix = $GcsPrefix
    }
    $summary | ConvertTo-Json -Depth 5
}
finally {
    Remove-Item -LiteralPath $localScript -Force -ErrorAction SilentlyContinue
    & gcloud compute ssh `
        $VmName `
        --project $ProjectId `
        --zone $Zone `
        --tunnel-through-iap `
        --command "rm -f '$remoteScript'" *> $null
}
