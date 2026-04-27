[CmdletBinding()]
param(
    [string]$ControlPlaneRoot = "",
    [string]$RunnerRepoRoot = "",
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
    if ($LASTEXITCODE -ne 0) {
        throw "Python builder failed with exit code $LASTEXITCODE`: $ScriptPath"
    }
}

if (-not $ControlPlaneRoot) {
    $ControlPlaneRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..\..")).Path
}

$reportDir = Join-Path $ControlPlaneRoot "docs\gcp_foundation"
$attestationPath = Join-Path $reportDir "gcp_execution_exclusive_window_attestation.json"
$prearmPath = Join-Path $reportDir "gcp_execution_prearm_preflight.json"
$archiveDir = Join-Path $reportDir "exclusive_window_archive"
$pythonCommand = Resolve-PythonCommand

if (-not $RunnerRepoRoot) {
    if (Test-Path $prearmPath) {
        $prearmForRunnerRoot = Get-Content -Path $prearmPath -Raw | ConvertFrom-Json
        if ($prearmForRunnerRoot.runner_repo_root) {
            $RunnerRepoRoot = [string]$prearmForRunnerRoot.runner_repo_root
        }
    }
}
if (-not $RunnerRepoRoot) {
    throw "RunnerRepoRoot was not provided and could not be inferred from the pre-arm packet."
}

$builders = @(
    @{
        Path = Join-Path $PSScriptRoot "build_gcp_execution_exclusive_window_status.py"
        Arguments = @("--report-dir", $reportDir, "--vm-name", $VmName)
    },
    @{
        Path = Join-Path $PSScriptRoot "build_gcp_execution_trusted_validation_session_status.py"
        Arguments = @("--report-dir", $reportDir, "--vm-name", $VmName, "--runner-repo-root", $RunnerRepoRoot)
    },
    @{
        Path = Join-Path $PSScriptRoot "build_gcp_execution_trusted_validation_launch_pack.py"
        Arguments = @("--report-dir", $reportDir, "--vm-name", $VmName)
    },
    @{
        Path = Join-Path $PSScriptRoot "build_gcp_execution_closeout_status.py"
        Arguments = @("--report-dir", $reportDir, "--vm-name", $VmName)
    }
)
$postCloseoutBuilders = @{
    SessionCompletionGate = Join-Path $PSScriptRoot "build_gcp_execution_session_completion_gate.py"
    OperatorPacket = Join-Path $PSScriptRoot "build_gcp_execution_trusted_validation_operator_packet.py"
    LaunchAuthorization = Join-Path $PSScriptRoot "build_gcp_execution_launch_authorization.py"
}

foreach ($builder in $builders) {
    if (-not (Test-Path $builder.Path)) {
        throw "Builder not found: $($builder.Path)"
    }
}
foreach ($builder in $postCloseoutBuilders.GetEnumerator()) {
    if (-not (Test-Path $builder.Value)) {
        throw "Builder not found: $($builder.Value)"
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
    Invoke-PythonScript -PythonCommand $pythonCommand -ScriptPath $builder.Path -Arguments $builder.Arguments
}

Invoke-PythonScript -PythonCommand $pythonCommand -ScriptPath $postCloseoutBuilders.SessionCompletionGate -Arguments @(
    "--report-dir", $reportDir
)
Invoke-PythonScript -PythonCommand $pythonCommand -ScriptPath $postCloseoutBuilders.OperatorPacket -Arguments @(
    "--report-dir", $reportDir,
    "--vm-name", $VmName
)
Invoke-PythonScript -PythonCommand $pythonCommand -ScriptPath $postCloseoutBuilders.LaunchAuthorization -Arguments @(
    "--report-dir", $reportDir
)

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
        (Join-Path $reportDir "gcp_execution_closeout_handoff.md"),
        (Join-Path $reportDir "gcp_execution_session_completion_gate.json"),
        (Join-Path $reportDir "gcp_execution_session_completion_gate.md"),
        (Join-Path $reportDir "gcp_execution_session_completion_gate_handoff.md"),
        (Join-Path $reportDir "gcp_execution_trusted_validation_operator_packet.json"),
        (Join-Path $reportDir "gcp_execution_trusted_validation_operator_packet.md"),
        (Join-Path $reportDir "gcp_execution_trusted_validation_operator_handoff.md"),
        (Join-Path $reportDir "gcp_execution_launch_authorization.json"),
        (Join-Path $reportDir "gcp_execution_launch_authorization.md"),
        (Join-Path $reportDir "gcp_execution_launch_authorization_handoff.md")
    )
    $existingMirrorFiles = @($mirrorFiles | Where-Object { Test-Path $_ })
    if ($existingMirrorFiles.Count -gt 0) {
        & gcloud storage cp @existingMirrorFiles $GcsPrefix
    }
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
    session_completion_gate_json = Join-Path $reportDir "gcp_execution_session_completion_gate.json"
    launch_authorization_json = Join-Path $reportDir "gcp_execution_launch_authorization.json"
    mirrored_to_gcs = [bool]$MirrorToGcs
    gcs_prefix = $GcsPrefix
}

$summary | ConvertTo-Json -Depth 4
