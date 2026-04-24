[CmdletBinding()]
param(
    [string]$ControlPlaneRoot = "",
    [string]$RunnerRepoRoot = "",
    [string]$ProjectId = "codexalpaca",
    [string]$VmName = "vm-execution-paper-01",
    [string]$Zone = "us-east1-b",
    [string]$VmRunnerPath = "/opt/codexalpaca/codexalpaca_repo",
    [string]$ExpectedRunnerCommit = "",
    [int]$BrokerWatchDurationSeconds = 180,
    [int]$BrokerWatchSampleIntervalSeconds = 30,
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

function Test-PythonImports {
    param(
        [string[]]$PythonCommand,
        [string[]]$Modules
    )
    $importLine = "import " + ($Modules -join ", ")
    $command = @($PythonCommand + @("-c", $importLine))
    & $command[0] $command[1..($command.Length - 1)] *> $null
    return ($LASTEXITCODE -eq 0)
}

function Resolve-BrokerPythonCommand {
    param(
        [string]$ControlPlaneRoot,
        [string]$RunnerRepoRoot
    )
    $workspaceRoot = Split-Path $ControlPlaneRoot -Parent
    $candidateCommands = @()
    if ($RunnerRepoRoot) {
        $candidateCommands += ,@(Join-Path $RunnerRepoRoot ".venv\Scripts\python.exe")
    }
    $candidateCommands += ,@(Join-Path $workspaceRoot "codexalpaca_repo\.venv\Scripts\python.exe")
    $candidateCommands += ,@(Join-Path $workspaceRoot "codexalpaca_repo_gcp_lease_lane_refreshed\.venv\Scripts\python.exe")
    if (Get-Command py -ErrorAction SilentlyContinue) {
        $candidateCommands += ,@("py", "-3")
    }
    if (Get-Command python -ErrorAction SilentlyContinue) {
        $candidateCommands += ,@("python")
    }
    foreach ($candidate in $candidateCommands) {
        if ($candidate.Count -eq 1 -and $candidate[0] -match "\\python\.exe$" -and -not (Test-Path $candidate[0])) {
            continue
        }
        if (Test-PythonImports -PythonCommand $candidate -Modules @("dotenv", "requests")) {
            return $candidate
        }
    }
    throw "No broker-capable Python interpreter found. Need modules: dotenv, requests."
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

function Invoke-PythonCommand {
    param(
        [string[]]$PythonCommand,
        [string[]]$Arguments
    )
    $command = @($PythonCommand + $Arguments)
    & $command[0] $command[1..($command.Length - 1)]
    if ($LASTEXITCODE -ne 0) {
        throw "Python command failed with exit code $LASTEXITCODE`: $($Arguments -join ' ')"
    }
}

function Get-GitOutput {
    param(
        [string]$RepoRoot,
        [string[]]$Arguments
    )
    $result = & git -C $RepoRoot @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "git command failed in $RepoRoot`: git $($Arguments -join ' ')"
    }
    return ([string]($result | Out-String)).Trim()
}

function Write-ScheduledTaskObservation {
    param([string]$OutPath)
    $rows = @(
        Get-ScheduledTask |
            Where-Object {
                $_.TaskName -match 'Alpaca|Codex|Ticker|Portfolio|Stage27|Governed|QQQ|Trader|Trade' -or
                $_.TaskPath -match 'Alpaca|Codex|Ticker|Portfolio|Stage27|Governed|QQQ|Trader|Trade'
            } |
            Select-Object TaskName, TaskPath, State |
            Sort-Object TaskName
    )
    ConvertTo-Json -InputObject @($rows) -Depth 5 | Set-Content -Path $OutPath -Encoding utf8
}

function Write-LocalProcessObservation {
    param([string]$OutPath)
    $patterns = @(
        "run_multi_ticker_portfolio_paper_trader\.py",
        "stage27_supervisor\.ps1.*paper_live",
        "run_stage27_paper_live\.ps1",
        "src\\stage27_runner\.py.*paper_live",
        "run_governed_downchoppy_exec5\.ps1"
    )
    $selfPid = [int]$PID
    $selfParentPid = -1
    try {
        $selfProc = Get-CimInstance Win32_Process -Filter ("ProcessId={0}" -f $selfPid) -ErrorAction SilentlyContinue
        if ($null -ne $selfProc) {
            $selfParentPid = [int]$selfProc.ParentProcessId
        }
    } catch {
    }
    $rows = @()
    foreach ($proc in @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue)) {
        $cmdline = [string]$proc.CommandLine
        if ([string]::IsNullOrWhiteSpace($cmdline)) { continue }
        $hit = $false
        foreach ($pattern in $patterns) {
            if ($cmdline -match $pattern) {
                $hit = $true
                break
            }
        }
        if (-not $hit) { continue }
        $pidValue = [int]$proc.ProcessId
        $parentPidValue = [int]$proc.ParentProcessId
        if ($pidValue -eq $selfPid -or $pidValue -eq $selfParentPid -or $parentPidValue -eq $selfPid) { continue }
        $rows += [pscustomobject]@{
            process_id = $pidValue
            parent_process_id = $parentPidValue
            name = [string]$proc.Name
            command_line = $cmdline
        }
    }
    ConvertTo-Json -InputObject @($rows) -Depth 5 | Set-Content -Path $OutPath -Encoding utf8
    return @($rows).Count
}

function Invoke-BrokerReadOnlyWatch {
    param(
        [string[]]$PythonCommand,
        [string]$RunnerRepoRoot,
        [int]$DurationSeconds,
        [int]$SampleIntervalSeconds,
        [string]$OutPath
    )
    $localBrokerScript = Join-Path ([System.IO.Path]::GetTempPath()) ("codexalpaca_broker_readonly_watch_" + $PID + ".py")
    $brokerScriptContent = @'
from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runner-repo-root", required=True)
    parser.add_argument("--duration-seconds", type=int, required=True)
    parser.add_argument("--sample-interval-seconds", type=int, required=True)
    parser.add_argument("--out-json", required=True)
    args = parser.parse_args()

    runner_root = Path(args.runner_repo_root)
    sys.path.insert(0, str(runner_root))

    from alpaca_lab.config import load_settings
    from alpaca_lab.brokers.alpaca import AlpacaBrokerAdapter

    broker = AlpacaBrokerAdapter(load_settings())
    interval = max(int(args.sample_interval_seconds), 1)
    duration = max(int(args.duration_seconds), 0)
    sample_count = max(int(duration / interval), 1) + 1
    start = datetime.now(timezone.utc)
    samples = []
    newest_values = []
    for index in range(sample_count):
        positions = broker.get_positions()
        open_orders = broker.get_orders(status="open")
        recent_orders = broker.get_orders(status="all", limit=10)
        newest = None
        for order in recent_orders:
            created_at = order.get("created_at")
            if created_at and (newest is None or created_at > newest):
                newest = created_at
        newest_values.append(newest)
        samples.append(
            {
                "sample": index,
                "position_count": len(positions),
                "open_order_count": len(open_orders),
                "newest_order_created_at": newest,
            }
        )
        print(
            f"sample={index} position_count={len(positions)} "
            f"open_order_count={len(open_orders)} newest_order_created_at={newest}",
            flush=True,
        )
        if index < sample_count - 1:
            time.sleep(interval)
    end = datetime.now(timezone.utc)
    newest_order_constant = len(set(newest_values)) <= 1
    payload = {
        "watch_start_utc": start.isoformat(),
        "watch_end_utc": end.isoformat(),
        "duration_seconds": int((end - start).total_seconds()),
        "samples": len(samples),
        "sample_interval_seconds": interval,
        "position_count_all_samples": max(row["position_count"] for row in samples),
        "open_order_count_all_samples": max(row["open_order_count"] for row in samples),
        "newest_order_created_at_all_samples": newest_values[-1] if newest_values else None,
        "newest_order_constant": newest_order_constant,
        "sample_rows": samples,
    }
    Path(args.out_json).write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
'@
    try {
        Set-Content -Path $localBrokerScript -Value $brokerScriptContent -Encoding utf8
        Invoke-PythonCommand -PythonCommand $PythonCommand -Arguments @(
            $localBrokerScript,
            "--runner-repo-root", $RunnerRepoRoot,
            "--duration-seconds", ([string]$DurationSeconds),
            "--sample-interval-seconds", ([string]$SampleIntervalSeconds),
            "--out-json", $OutPath
        )
    }
    finally {
        Remove-Item -LiteralPath $localBrokerScript -Force -ErrorAction SilentlyContinue
    }
}

if (-not $ControlPlaneRoot) {
    $ControlPlaneRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..\..")).Path
}
if (-not $RunnerRepoRoot) {
    $RunnerRepoRoot = (Resolve-Path (Join-Path $ControlPlaneRoot "..\codexalpaca_repo_gcp_lease_lane_refreshed")).Path
}
if (-not $ExpectedRunnerCommit) {
    $ExpectedRunnerCommit = Get-GitOutput -RepoRoot $RunnerRepoRoot -Arguments @("rev-parse", "HEAD")
}
if (-not (Get-Command gcloud -ErrorAction SilentlyContinue)) {
    throw "gcloud CLI not found on PATH. Cannot refresh VM pre-arm evidence."
}

$reportDir = Join-Path $ControlPlaneRoot "docs\gcp_foundation"
$observedPath = Join-Path $reportDir "gcp_vm_prearm_observed.json"
$manifestPath = Join-Path $reportDir "gcp_vm_runner_source_manifest_observed.json"
$scheduledTaskObservationPath = Join-Path $reportDir "gcp_execution_launch_surface_scheduled_tasks_observed.json"
$localProcessObservationPath = Join-Path $reportDir "gcp_execution_launch_surface_local_processes_observed.json"
$brokerWatchObservationPath = Join-Path $reportDir "gcp_execution_launch_surface_broker_watch_observed.json"
$pythonCommand = Resolve-PythonCommand -RunnerRepoRoot $RunnerRepoRoot
$brokerPythonCommand = Resolve-BrokerPythonCommand -ControlPlaneRoot $ControlPlaneRoot -RunnerRepoRoot $RunnerRepoRoot
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

    Write-ScheduledTaskObservation -OutPath $scheduledTaskObservationPath
    $localProcessCount = Write-LocalProcessObservation -OutPath $localProcessObservationPath
    Invoke-BrokerReadOnlyWatch -PythonCommand $brokerPythonCommand -RunnerRepoRoot $RunnerRepoRoot -DurationSeconds $BrokerWatchDurationSeconds -SampleIntervalSeconds $BrokerWatchSampleIntervalSeconds -OutPath $brokerWatchObservationPath
    $brokerWatch = Get-Content -Path $brokerWatchObservationPath -Raw | ConvertFrom-Json
    $launchSurfaceArgs = @(
        "--report-dir", $reportDir,
        "--project-id", $ProjectId,
        "--vm-name", $VmName,
        "--zone", $Zone,
        "--expected-runner-commit", $ExpectedRunnerCommit,
        "--broker-position-count", ([string][int]$brokerWatch.position_count_all_samples),
        "--broker-open-order-count", ([string][int]$brokerWatch.open_order_count_all_samples),
        "--watch-duration-seconds", ([string][int]$brokerWatch.duration_seconds),
        "--watch-start-utc", ([string]$brokerWatch.watch_start_utc),
        "--watch-end-utc", ([string]$brokerWatch.watch_end_utc),
        "--watch-samples", ([string][int]$brokerWatch.samples),
        "--watch-sample-interval-seconds", ([string][int]$brokerWatch.sample_interval_seconds),
        "--watch-position-count-all-samples", ([string][int]$brokerWatch.position_count_all_samples),
        "--watch-open-order-count-all-samples", ([string][int]$brokerWatch.open_order_count_all_samples),
        "--watch-newest-order-created-at", ([string]$brokerWatch.newest_order_created_at_all_samples),
        "--scheduled-task-json", $scheduledTaskObservationPath,
        "--local-process-count", ([string][int]$localProcessCount),
        "--local-process-note", "broker-capable launch patterns only; inspection commands excluded",
        "--vm-process-note", "VM pre-arm observed trader_process_absent=$($observed.trader_process_absent)",
        "--vm-runner-commit", ([string]$observed.vm_runner_commit),
        "--vm-runner-branch", ([string]$observed.vm_runner_branch)
    )
    if ([bool]$observed.trader_process_absent) {
        $launchSurfaceArgs += "--vm-process-clear"
    }
    if ([bool]$brokerWatch.newest_order_constant) {
        $launchSurfaceArgs += "--watch-newest-order-constant"
    }
    Invoke-PythonScript -PythonCommand $pythonCommand -ScriptPath (Join-Path $PSScriptRoot "build_gcp_execution_launch_surface_audit.py") -Arguments $launchSurfaceArgs

    Invoke-PythonScript -PythonCommand $pythonCommand -ScriptPath (Join-Path $PSScriptRoot "build_gcp_execution_trusted_validation_operator_packet.py") -Arguments @("--report-dir", $reportDir, "--project-id", $ProjectId, "--vm-name", $VmName, "--zone", $Zone, "--gcs-prefix", $GcsPrefix)
    Invoke-PythonScript -PythonCommand $pythonCommand -ScriptPath (Join-Path $PSScriptRoot "build_gcp_execution_prearm_preflight.py") -Arguments @("--report-dir", $reportDir)
    Invoke-PythonScript -PythonCommand $pythonCommand -ScriptPath (Join-Path $PSScriptRoot "build_gcp_execution_launch_authorization.py") -Arguments @("--report-dir", $reportDir)

    if ($MirrorToGcs) {
        $mirrorFiles = @(
            "gcp_vm_prearm_observed.json",
            "gcp_vm_runner_source_manifest_observed.json",
            "gcp_execution_launch_surface_scheduled_tasks_observed.json",
            "gcp_execution_launch_surface_local_processes_observed.json",
            "gcp_execution_launch_surface_broker_watch_observed.json",
            "gcp_execution_launch_surface_audit.json",
            "gcp_execution_launch_surface_audit.md",
            "gcp_execution_launch_surface_audit_handoff.md",
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
            "gcp_execution_prearm_preflight_handoff.md",
            "gcp_execution_launch_authorization.json",
            "gcp_execution_launch_authorization.md",
            "gcp_execution_launch_authorization_handoff.md"
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
        expected_runner_commit = $ExpectedRunnerCommit
        broker_watch_observed_json = $brokerWatchObservationPath
        scheduled_task_observed_json = $scheduledTaskObservationPath
        local_process_observed_json = $localProcessObservationPath
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
