[CmdletBinding()]
param(
    [string]$ControlPlaneRoot = "",
    [string]$VmName = "vm-execution-paper-01",
    [switch]$MirrorToGcs,
    [string]$GcsPrefix = "gs://codexalpaca-control-us/gcp_foundation"
)

$ErrorActionPreference = "Stop"

function Resolve-PythonCommand {
    if (Get-Command py -ErrorAction SilentlyContinue) {
        return @("py", "-3")
    }
    if (Get-Command python -ErrorAction SilentlyContinue) {
        return @("python")
    }
    throw "No Python interpreter found on PATH. Install Python or expose `py`/`python` before closing the exclusive window."
}

function Invoke-PythonScript {
    param(
        [string[]]$PythonCommand,
        [string]$ScriptPath,
        [string[]]$Arguments
    )
    $command = @($PythonCommand + @($ScriptPath) + $Arguments)
    & $command[0] $command[1..($command.Length - 1)]
}

if (-not $ControlPlaneRoot) {
    $ControlPlaneRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..\..")).Path
}

$reportDir = Join-Path $ControlPlaneRoot "docs\gcp_foundation"
$attestationPath = Join-Path $reportDir "gcp_execution_exclusive_window_attestation.json"
$archiveDir = Join-Path $reportDir "exclusive_window_archive"
$pythonCommand = Resolve-PythonCommand

$builders = @(
    Join-Path $PSScriptRoot "build_gcp_execution_exclusive_window_status.py",
    Join-Path $PSScriptRoot "build_gcp_execution_trusted_validation_session_status.py",
    Join-Path $PSScriptRoot "build_gcp_execution_trusted_validation_launch_pack.py",
    Join-Path $PSScriptRoot "build_gcp_execution_closeout_status.py"
)

foreach ($builder in $builders) {
    if (-not (Test-Path $builder)) {
        throw "Builder not found: $builder"
    }
}

$archivedAttestationPath = $null
if (Test-Path $attestationPath) {
    $timestamp = Get-Date -Format "yyyyMMddTHHmmss"
    New-Item -ItemType Directory -Path $archiveDir -Force | Out-Null
    $archivedAttestationPath = Join-Path $archiveDir ("gcp_execution_exclusive_window_attestation_" + $timestamp + ".json")
    Move-Item -LiteralPath $attestationPath -Destination $archivedAttestationPath -Force
}

foreach ($builder in $builders) {
    Invoke-PythonScript -PythonCommand $pythonCommand -ScriptPath $builder -Arguments @(
        "--report-dir", $reportDir,
        "--vm-name", $VmName
    )
}

if ($MirrorToGcs) {
    if (-not (Get-Command gcloud -ErrorAction SilentlyContinue)) {
        throw "gcloud CLI not found on PATH. Install/authenticate gcloud or omit -MirrorToGcs."
    }
    $mirrorFiles = @(
        (Join-Path $reportDir "gcp_execution_exclusive_window_status.json"),
        (Join-Path $reportDir "gcp_execution_exclusive_window_status.md"),
        (Join-Path $reportDir "gcp_execution_exclusive_window_handoff.md"),
        (Join-Path $reportDir "gcp_execution_trusted_validation_session_status.json"),
        (Join-Path $reportDir "gcp_execution_trusted_validation_session_status.md"),
        (Join-Path $reportDir "gcp_execution_trusted_validation_launch_pack.json"),
        (Join-Path $reportDir "gcp_execution_trusted_validation_launch_pack.md"),
        (Join-Path $reportDir "gcp_execution_trusted_validation_launch_handoff.md"),
        (Join-Path $reportDir "gcp_execution_closeout_status.json"),
        (Join-Path $reportDir "gcp_execution_closeout_status.md"),
        (Join-Path $reportDir "gcp_execution_closeout_handoff.md")
    )
    & gcloud storage cp @mirrorFiles $GcsPrefix
}

$summary = @{
    generated_at = [datetime]::Now.ToString("o")
    control_plane_root = $ControlPlaneRoot
    attestation_json = $attestationPath
    attestation_archived_to = $archivedAttestationPath
    exclusive_window_status_json = Join-Path $reportDir "gcp_execution_exclusive_window_status.json"
    trusted_validation_status_json = Join-Path $reportDir "gcp_execution_trusted_validation_session_status.json"
    trusted_launch_pack_json = Join-Path $reportDir "gcp_execution_trusted_validation_launch_pack.json"
    closeout_status_json = Join-Path $reportDir "gcp_execution_closeout_status.json"
    mirrored_to_gcs = [bool]$MirrorToGcs
    gcs_prefix = $GcsPrefix
}

$summary | ConvertTo-Json -Depth 4
