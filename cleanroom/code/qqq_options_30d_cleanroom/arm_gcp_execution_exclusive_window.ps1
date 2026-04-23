[CmdletBinding()]
param(
    [string]$ControlPlaneRoot = "",
    [string]$VmName = "vm-execution-paper-01",
    [Parameter(Mandatory = $true)]
    [string]$ConfirmedBy,
    [Parameter(Mandatory = $true)]
    [string]$WindowStartsAt,
    [Parameter(Mandatory = $true)]
    [string]$WindowExpiresAt,
    [ValidateSet("paused", "none")]
    [string]$ParallelPathState = "paused",
    [string]$Notes = "Bounded exclusive window for the first sanctioned GCP trusted validation session.",
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
    throw "No Python interpreter found on PATH. Install Python or expose `py`/`python` before arming the exclusive window."
}

if (-not $ControlPlaneRoot) {
    $ControlPlaneRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..\..")).Path
}

$reportDir = Join-Path $ControlPlaneRoot "docs\gcp_foundation"
$attestationPath = Join-Path $reportDir "gcp_execution_exclusive_window_attestation.json"
$pythonCommand = Resolve-PythonCommand

$builders = @(
    Join-Path $PSScriptRoot "build_gcp_execution_exclusive_window_status.py",
    Join-Path $PSScriptRoot "build_gcp_execution_trusted_validation_session_status.py",
    Join-Path $PSScriptRoot "build_gcp_execution_trusted_validation_launch_pack.py"
)

foreach ($builder in $builders) {
    if (-not (Test-Path $builder)) {
        throw "Builder not found: $builder"
    }
}

$startsAt = [datetimeoffset]::Parse($WindowStartsAt)
$expiresAt = [datetimeoffset]::Parse($WindowExpiresAt)
if ($expiresAt -le $startsAt) {
    throw "WindowExpiresAt must be later than WindowStartsAt."
}

$confirmedAt = [datetimeoffset]::Now.ToString("o")
$attestation = @{
    window_id = "trusted-validation-session-$VmName"
    confirmed_by = $ConfirmedBy
    confirmed_at = $confirmedAt
    window_starts_at = $startsAt.ToString("o")
    window_expires_at = $expiresAt.ToString("o")
    target_vm_name = $VmName
    scope = "paper_account_single_writer"
    assertions = @{
        no_other_machine_active = $true
        parallel_exception_path_not_running_broker_session = ($ParallelPathState -in @("paused", "none"))
        session_starts_only_on_sanctioned_vm = $true
        post_session_assimilation_reserved = $true
    }
    notes = $Notes
}

$attestation | ConvertTo-Json -Depth 6 | Set-Content -Path $attestationPath -Encoding utf8

foreach ($builder in $builders) {
    $command = @($pythonCommand + @($builder, "--report-dir", $reportDir, "--project-id", "codexalpaca", "--vm-name", $VmName))
    & $command[0] $command[1..($command.Length - 1)]
}

if ($MirrorToGcs) {
    if (-not (Get-Command gcloud -ErrorAction SilentlyContinue)) {
        throw "gcloud CLI not found on PATH. Install/authenticate gcloud or omit -MirrorToGcs."
    }
    $mirrorFiles = @(
        "gcp_execution_exclusive_window_status.json",
        "gcp_execution_exclusive_window_status.md",
        "gcp_execution_exclusive_window_handoff.md",
        "gcp_execution_trusted_validation_session_status.json",
        "gcp_execution_trusted_validation_session_status.md",
        "gcp_execution_trusted_validation_launch_pack.json",
        "gcp_execution_trusted_validation_launch_pack.md",
        "gcp_execution_trusted_validation_launch_handoff.md"
    )
    $fileArgs = @()
    foreach ($file in $mirrorFiles) {
        $fileArgs += (Join-Path $reportDir $file)
    }
    & gcloud storage cp @fileArgs $GcsPrefix
}

$summary = @{
    attestation_json = $attestationPath
    exclusive_window_status_json = Join-Path $reportDir "gcp_execution_exclusive_window_status.json"
    trusted_validation_status_json = Join-Path $reportDir "gcp_execution_trusted_validation_session_status.json"
    trusted_launch_pack_json = Join-Path $reportDir "gcp_execution_trusted_validation_launch_pack.json"
    mirrored_to_gcs = [bool]$MirrorToGcs
    gcs_prefix = $GcsPrefix
}

$summary | ConvertTo-Json -Depth 4
