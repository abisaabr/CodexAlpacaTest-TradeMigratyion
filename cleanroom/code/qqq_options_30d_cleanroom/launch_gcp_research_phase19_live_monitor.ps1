[CmdletBinding()]
param(
    [string]$ControlPlaneRoot = "",
    [string]$ProjectId = "codexalpaca",
    [string]$Location = "us-central1",
    [string]$Zone = "us-central1-f",
    [string]$JobId = "phase19-targeted-fill-diagnostic-20260427022000",
    [string]$WaveId = "top100_liquidity_research_20260426",
    [string]$PhaseId = "phase19_targeted_fill_diagnostic_20260427022000",
    [string]$BatchVmName = "phase19-targeted-f-8f0eaf56-aa9c-40b50-group0-0-ths5",
    [string]$ContainerName = "",
    [string]$WorkDir = "/tmp/phase19_targeted_fill_diagnostic_20260427022000",
    [string]$BuildName = "top100_phase19_targeted_fill_options_20260302_20260423",
    [switch]$MirrorToGcs,
    [string]$GcsFoundationPrefix = "gs://codexalpaca-control-us/gcp_foundation",
    [string]$GcsResearchPrefix = "gs://codexalpaca-control-us/research_results/top100_liquidity_research_20260426/phase19_live_monitor",
    [string]$GcsFinalArtifactPrefix = "gs://codexalpaca-control-us/research_results/top100_liquidity_research_20260426/portfolio_event_driven_data/phase19_targeted_fill_diagnostic_20260427022000",
    [string]$GcsCheckpointPrefix = "gs://codexalpaca-control-us/research_results/top100_liquidity_research_20260426/phase19_live_checkpoints"
)

$ErrorActionPreference = "Stop"

function Resolve-ControlPlaneRoot {
    param([string]$ProvidedRoot)
    if ($ProvidedRoot) {
        return (Resolve-Path $ProvidedRoot).Path
    }
    $scriptDir = Split-Path $PSCommandPath -Parent
    return (Resolve-Path (Join-Path $scriptDir "..\..\..")).Path
}

function Resolve-PythonCommand {
    param([string]$ControlPlaneRoot)
    $workspaceRoot = Split-Path $ControlPlaneRoot -Parent
    $candidates = @(
        (Join-Path $ControlPlaneRoot ".venv\Scripts\python.exe"),
        (Join-Path $workspaceRoot "codexalpaca_repo_gcp_lease_lane_refreshed\.venv\Scripts\python.exe"),
        (Join-Path $workspaceRoot "codexalpaca_repo\.venv\Scripts\python.exe")
    )
    foreach ($candidate in $candidates) {
        if (Test-Path $candidate) {
            return @($candidate)
        }
    }
    if (Get-Command py -ErrorAction SilentlyContinue) {
        return @("py", "-3")
    }
    if (Get-Command python -ErrorAction SilentlyContinue) {
        return @("python")
    }
    throw "No Python interpreter found."
}

function Invoke-PythonScript {
    param(
        [string[]]$PythonCommand,
        [string]$ScriptPath,
        [string[]]$Arguments
    )
    $command = @($PythonCommand + @($ScriptPath) + $Arguments)
    if ($command.Count -eq 1) {
        & $command[0]
    } else {
        & $command[0] $command[1..($command.Count - 1)]
    }
    if ($LASTEXITCODE -ne 0) {
        throw "Python script failed with exit code $LASTEXITCODE`: $ScriptPath"
    }
}

function Invoke-Gcloud {
    param([string[]]$Arguments)
    & gcloud @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "gcloud failed with exit code $LASTEXITCODE`: gcloud $($Arguments -join ' ')"
    }
}

$ControlPlaneRoot = Resolve-ControlPlaneRoot -ProvidedRoot $ControlPlaneRoot
$ReportDir = Join-Path $ControlPlaneRoot "docs\gcp_foundation"
$TimestampUtc = (Get-Date).ToUniversalTime().ToString("yyyyMMddTHHmmssZ")
$EvidenceDir = Join-Path $ReportDir "runtime_evidence\research_phase19_live_monitor\$TimestampUtc"
New-Item -ItemType Directory -Path $EvidenceDir -Force | Out-Null

$BatchStatusPath = Join-Path $EvidenceDir "batch_status.json"
$RemoteRawPath = Join-Path $EvidenceDir "remote_observation.raw.txt"
$RemoteStderrPath = Join-Path $EvidenceDir "remote_observation.stderr.txt"
$RemoteJsonPath = Join-Path $EvidenceDir "remote_observation.json"
$RemoteScriptPathLocal = Join-Path $EvidenceDir "collect_remote_observation.sh"
$ObservationPath = Join-Path $EvidenceDir "phase19_live_monitor_observation.json"

gcloud batch jobs describe $JobId --project $ProjectId --location $Location --format=json |
    Set-Content -Path $BatchStatusPath -Encoding utf8
if ($LASTEXITCODE -ne 0) {
    throw "Failed to describe Batch job $JobId"
}
$BatchStatus = Get-Content -Path $BatchStatusPath -Raw | ConvertFrom-Json
$BatchState = [string]$BatchStatus.status.state
$BatchRunDuration = [string]$BatchStatus.status.runDuration

$RemoteTemplate = @'
set -eu
CONTAINER_NAME="__CONTAINER_NAME__"
WORK_DIR="__WORK_DIR__"
PHASE_ID="__PHASE_ID__"
BUILD_NAME="__BUILD_NAME__"
if [ -z "$CONTAINER_NAME" ]; then
  CONTAINER_NAME="$(sudo docker ps --format '{{.Names}}' | head -n 1)"
fi
CONTAINER_STATUS="$(sudo docker ps --filter "name=$CONTAINER_NAME" --format '{{.Status}}' | head -n 1)"
echo "__PHASE_MONITOR_JSON_BEGIN__"
sudo docker exec -i \
  -e WORK_DIR="$WORK_DIR" \
  -e PHASE_ID="$PHASE_ID" \
  -e BUILD_NAME="$BUILD_NAME" \
  -e CONTAINER_NAME="$CONTAINER_NAME" \
  -e CONTAINER_STATUS="$CONTAINER_STATUS" \
  "$CONTAINER_NAME" python3 - <<'PY'
from __future__ import annotations

import json
import os
import re
from pathlib import Path

root = Path(os.environ["WORK_DIR"])
phase_id = os.environ["PHASE_ID"]
build_name = os.environ["BUILD_NAME"]


def count_tree(path: Path) -> tuple[int, int]:
    if not path.exists():
        return 0, 0
    files = 0
    size = 0
    for child in path.rglob("*"):
        if child.is_file():
            files += 1
            size += child.stat().st_size
    return files, size


def tail_text(path: Path, limit: int = 20000) -> str:
    if not path.exists():
        return ""
    data = path.read_bytes()
    text = data[-limit:].decode("utf-8", errors="replace")
    text = re.sub(r"[A-Z0-9]{20,}", "<redacted>", text)
    return text


selected_files, selected_bytes = count_tree(root / "event_driven_contracts" / "selected_option_contracts")
raw_files, raw_bytes = count_tree(root / "repo" / "data" / "raw" / "historical" / build_name)
silver_files, silver_bytes = count_tree(root / "repo" / "data" / "silver" / "historical" / build_name)
download_report_files, download_report_bytes = count_tree(root / "repo" / "reports" / build_name)
replay_files, replay_bytes = count_tree(root / "event_driven_replay")
portfolio_files, portfolio_bytes = count_tree(root / "portfolio_report")
promotion_files, promotion_bytes = count_tree(root / "promotion_review_packet")
log_path = root / f"{phase_id}.out.log"
err_path = root / f"{phase_id}.err.log"

payload = {
    "container_name": os.environ.get("CONTAINER_NAME"),
    "container_status": os.environ.get("CONTAINER_STATUS"),
    "container_found": bool(os.environ.get("CONTAINER_NAME")),
    "selected_contract_files": selected_files,
    "selected_contract_bytes": selected_bytes,
    "raw_download_files": raw_files,
    "raw_download_bytes": raw_bytes,
    "silver_download_files": silver_files,
    "silver_download_bytes": silver_bytes,
    "download_report_files": download_report_files,
    "download_report_bytes": download_report_bytes,
    "replay_files": replay_files,
    "replay_bytes": replay_bytes,
    "portfolio_report_files": portfolio_files,
    "portfolio_report_bytes": portfolio_bytes,
    "promotion_review_files": promotion_files,
    "promotion_review_bytes": promotion_bytes,
    "run_log_bytes": log_path.stat().st_size if log_path.exists() else 0,
    "run_err_bytes": err_path.stat().st_size if err_path.exists() else 0,
    "log_tail_redacted": tail_text(log_path),
}
print(json.dumps(payload, indent=2))
PY
echo "__PHASE_MONITOR_JSON_END__"
'@

$RemoteCommand = $RemoteTemplate.
    Replace("__CONTAINER_NAME__", $ContainerName).
    Replace("__WORK_DIR__", $WorkDir).
    Replace("__PHASE_ID__", $PhaseId).
    Replace("__BUILD_NAME__", $BuildName)

$RemoteCommand | Set-Content -Path $RemoteScriptPathLocal -Encoding ascii
$RemoteScriptPath = "/tmp/codexalpaca_phase19_live_monitor_$TimestampUtc.sh"
Invoke-Gcloud -Arguments @(
    "compute", "scp",
    "--project", $ProjectId,
    "--zone", $Zone,
    "--tunnel-through-iap",
    $RemoteScriptPathLocal,
    "${BatchVmName}:$RemoteScriptPath"
)

$OldErrorActionPreference = $ErrorActionPreference
$ErrorActionPreference = "Continue"
$RemoteOutput = & gcloud compute ssh $BatchVmName --project $ProjectId --zone $Zone --tunnel-through-iap --command "bash $RemoteScriptPath" 2> $RemoteStderrPath
$RemoteExitCode = $LASTEXITCODE
$ErrorActionPreference = $OldErrorActionPreference
$RemoteOutput | Set-Content -Path $RemoteRawPath -Encoding utf8
$RemoteText = [string]($RemoteOutput | Out-String)
$Match = [regex]::Match($RemoteText, "(?s)__PHASE_MONITOR_JSON_BEGIN__\s*(\{.*\})\s*__PHASE_MONITOR_JSON_END__")
if (-not $Match.Success) {
    if ($RemoteExitCode -ne 0) {
        throw "Failed to collect remote live monitor observation from $BatchVmName. See $RemoteRawPath and $RemoteStderrPath"
    }
    throw "Could not find monitor JSON markers in remote output. See $RemoteRawPath"
}
$RemoteJson = $Match.Groups[1].Value
$RemoteJson | Set-Content -Path $RemoteJsonPath -Encoding utf8
$RemoteObservation = $RemoteJson | ConvertFrom-Json

$GcsFinalArtifactsVisible = $false
$OldErrorActionPreference = $ErrorActionPreference
$ErrorActionPreference = "Continue"
& gcloud storage ls "$GcsFinalArtifactPrefix/" *> $null
$GcsLsExitCode = $LASTEXITCODE
$ErrorActionPreference = $OldErrorActionPreference
if ($GcsLsExitCode -eq 0) {
    $GcsFinalArtifactsVisible = $true
}

$LatestCheckpointPrefix = $null
$OldErrorActionPreference = $ErrorActionPreference
$ErrorActionPreference = "Continue"
$CheckpointListing = & gcloud storage ls "$GcsCheckpointPrefix/" 2> $null
$CheckpointLsExitCode = $LASTEXITCODE
$ErrorActionPreference = $OldErrorActionPreference
if ($CheckpointLsExitCode -eq 0 -and $CheckpointListing) {
    $LatestCheckpointPrefix = [string](($CheckpointListing | Sort-Object | Select-Object -Last 1).TrimEnd("/"))
}

$Observation = [ordered]@{
    project_id = $ProjectId
    location = $Location
    zone = $Zone
    job_id = $JobId
    wave_id = $WaveId
    phase_id = $PhaseId
    batch_vm = $BatchVmName
    batch_state = $BatchState
    batch_run_duration = $BatchRunDuration
    gcs_final_artifacts_visible = $GcsFinalArtifactsVisible
    latest_checkpoint_prefix = $LatestCheckpointPrefix
    artifact_upload_model = "final_exit_trap"
    runtime_evidence_path = $EvidenceDir
    remote_observation = $RemoteObservation
}
$Observation | ConvertTo-Json -Depth 20 | Set-Content -Path $ObservationPath -Encoding utf8

$PythonCommand = Resolve-PythonCommand -ControlPlaneRoot $ControlPlaneRoot
$BuilderPath = Join-Path $ControlPlaneRoot "cleanroom\code\qqq_options_30d_cleanroom\build_gcp_research_phase_live_monitor.py"
Invoke-PythonScript -PythonCommand $PythonCommand -ScriptPath $BuilderPath -Arguments @(
    "--observation-json", $ObservationPath,
    "--report-dir", $ReportDir,
    "--packet-prefix", "gcp_research_phase19_live_monitor"
)

if ($MirrorToGcs) {
    foreach ($leaf in @(
        "gcp_research_phase19_live_monitor.json",
        "gcp_research_phase19_live_monitor.md",
        "gcp_research_phase19_live_monitor_handoff.md"
    )) {
        $localPath = Join-Path $ReportDir $leaf
        Invoke-Gcloud -Arguments @("storage", "cp", $localPath, "$GcsFoundationPrefix/$leaf")
        Invoke-Gcloud -Arguments @("storage", "cp", $localPath, "$GcsResearchPrefix/$leaf")
    }
}

Get-Content -Path (Join-Path $ReportDir "gcp_research_phase19_live_monitor_handoff.md")
