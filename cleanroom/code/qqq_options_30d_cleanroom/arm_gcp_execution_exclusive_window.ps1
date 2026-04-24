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
    [int]$MaxPrearmAgeMinutes = 20,
    [string]$Zone = "us-east1-b",
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

function Assert-PrearmPreflightReady {
    param(
        [string]$PrearmPath,
        [string]$VmName,
        [int]$MaxAgeMinutes
    )
    if (-not (Test-Path $PrearmPath)) {
        throw "Pre-arm preflight packet not found: $PrearmPath. Run launch_gcp_execution_prearm_preflight.ps1 before arming."
    }
    $prearm = Get-Content -Path $PrearmPath -Raw | ConvertFrom-Json
    if ($prearm.status -ne "ready_to_arm_window") {
        throw "Pre-arm preflight status must be ready_to_arm_window before arming; observed: $($prearm.status)"
    }
    if ($prearm.next_operator_action -ne "arm_bounded_exclusive_window") {
        throw "Pre-arm next action must be arm_bounded_exclusive_window; observed: $($prearm.next_operator_action)"
    }
    if ($prearm.vm_name -and $prearm.vm_name -ne $VmName) {
        throw "Pre-arm VM mismatch. Expected $VmName, observed $($prearm.vm_name)."
    }
    if ($prearm.operator_packet_state -ne "ready_to_arm_window") {
        throw "Operator packet state must be ready_to_arm_window; observed: $($prearm.operator_packet_state)"
    }
    if ($prearm.runtime_readiness_status -ne "runtime_ready") {
        throw "Runtime readiness must be runtime_ready; observed: $($prearm.runtime_readiness_status)"
    }
    if ($prearm.runner_provenance_status -ne "provenance_matched") {
        throw "Runner provenance must be provenance_matched; observed: $($prearm.runner_provenance_status)"
    }
    if ($prearm.source_fingerprint_status -ne "source_fingerprint_matched") {
        throw "Source fingerprint must be source_fingerprint_matched; observed: $($prearm.source_fingerprint_status)"
    }
    if ($prearm.exclusive_window_status -ne "awaiting_operator_confirmation") {
        throw "Exclusive-window status must be awaiting_operator_confirmation before arming; observed: $($prearm.exclusive_window_status)"
    }
    if ($prearm.launch_pack_state -ne "awaiting_window_arm") {
        throw "Launch pack must be awaiting_window_arm before arming; observed: $($prearm.launch_pack_state)"
    }
    if ($prearm.launch_surface_audit_status -ne "local_broker_capable_surfaces_fenced_broker_flat") {
        throw "Launch-surface audit must be clean before arming; observed: $($prearm.launch_surface_audit_status)"
    }
    if ($prearm.launch_surface_broker_flat -ne $true) {
        throw "Launch-surface audit did not prove the broker account is flat."
    }
    if ($prearm.launch_surface_no_new_order_watch_clean -ne $true) {
        throw "Launch-surface audit did not prove a clean no-new-order watch."
    }
    if ($prearm.launch_surface_newest_order_constant -ne $true) {
        throw "Launch-surface audit did not prove the newest broker order timestamp stayed constant."
    }
    if ([int]$prearm.launch_surface_watch_duration_seconds -lt 180) {
        throw "Launch-surface no-new-order watch is too short; observed seconds: $($prearm.launch_surface_watch_duration_seconds)"
    }
    if ($prearm.trader_process_absent -ne $true) {
        throw "Pre-arm preflight did not prove the VM trader process is absent."
    }
    if ($prearm.ownership_enabled -ne $true) {
        throw "Pre-arm preflight did not prove runtime ownership is enabled."
    }
    if ($prearm.ownership_backend -ne "file") {
        throw "The first trusted session must use file ownership backend; observed: $($prearm.ownership_backend)"
    }
    if ($prearm.ownership_lease_class -ne "FileOwnershipLease") {
        throw "The first trusted session must use FileOwnershipLease; observed: $($prearm.ownership_lease_class)"
    }
    if ($prearm.shared_execution_lease_enforced -eq $true) {
        throw "GCS shared-lease enforcement is not approved for the first trusted session."
    }
    if ($prearm.broker_facing -ne $false) {
        throw "Pre-arm preflight must be non-broker-facing."
    }
    if ($prearm.live_manifest_effect -ne "none") {
        throw "Pre-arm preflight must not affect the live manifest; observed: $($prearm.live_manifest_effect)"
    }
    if ($prearm.risk_policy_effect -ne "none") {
        throw "Pre-arm preflight must not affect risk policy; observed: $($prearm.risk_policy_effect)"
    }
    $generatedAt = [datetimeoffset]::Parse([string]$prearm.generated_at)
    $age = [datetimeoffset]::Now - $generatedAt
    if ($age.TotalMinutes -gt $MaxAgeMinutes) {
        throw "Pre-arm preflight is stale: $([math]::Round($age.TotalMinutes, 2)) minutes old; maximum allowed is $MaxAgeMinutes."
    }
    if ($age.TotalMinutes -lt -5) {
        throw "Pre-arm preflight generated_at appears to be in the future: $($prearm.generated_at)"
    }
}

if (-not $ControlPlaneRoot) {
    $ControlPlaneRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..\..")).Path
}

$reportDir = Join-Path $ControlPlaneRoot "docs\gcp_foundation"
$attestationPath = Join-Path $reportDir "gcp_execution_exclusive_window_attestation.json"
$prearmPath = Join-Path $reportDir "gcp_execution_prearm_preflight.json"
$pythonCommand = Resolve-PythonCommand

$builderSpecs = @(
    @{
        Path = Join-Path $PSScriptRoot "build_gcp_execution_exclusive_window_status.py"
        Arguments = @("--report-dir", $reportDir, "--project-id", "codexalpaca", "--vm-name", $VmName)
    },
    @{
        Path = Join-Path $PSScriptRoot "build_gcp_execution_trusted_validation_session_status.py"
        Arguments = @("--report-dir", $reportDir, "--project-id", "codexalpaca", "--vm-name", $VmName)
    },
    @{
        Path = Join-Path $PSScriptRoot "build_gcp_execution_trusted_validation_launch_pack.py"
        Arguments = @("--report-dir", $reportDir, "--project-id", "codexalpaca", "--vm-name", $VmName, "--zone", $Zone)
    },
    @{
        Path = Join-Path $PSScriptRoot "build_gcp_execution_closeout_status.py"
        Arguments = @("--report-dir", $reportDir, "--vm-name", $VmName, "--gcs-prefix", $GcsPrefix)
    },
    @{
        Path = Join-Path $PSScriptRoot "build_gcp_execution_trusted_validation_operator_packet.py"
        Arguments = @("--report-dir", $reportDir, "--project-id", "codexalpaca", "--vm-name", $VmName, "--zone", $Zone, "--gcs-prefix", $GcsPrefix)
    },
    @{
        Path = Join-Path $PSScriptRoot "build_gcp_execution_launch_authorization.py"
        Arguments = @("--report-dir", $reportDir, "--max-prearm-age-minutes", $MaxPrearmAgeMinutes)
    }
)

foreach ($builder in $builderSpecs.Path) {
    if (-not (Test-Path $builder)) {
        throw "Builder not found: $builder"
    }
}

$startsAt = [datetimeoffset]::Parse($WindowStartsAt)
$expiresAt = [datetimeoffset]::Parse($WindowExpiresAt)
if ($expiresAt -le $startsAt) {
    throw "WindowExpiresAt must be later than WindowStartsAt."
}

Assert-PrearmPreflightReady -PrearmPath $prearmPath -VmName $VmName -MaxAgeMinutes $MaxPrearmAgeMinutes

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

foreach ($builderSpec in $builderSpecs) {
    Invoke-PythonScript -PythonCommand $pythonCommand -ScriptPath $builderSpec.Path -Arguments $builderSpec.Arguments
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
        "gcp_execution_trusted_validation_launch_handoff.md",
        "gcp_execution_closeout_status.json",
        "gcp_execution_closeout_status.md",
        "gcp_execution_closeout_handoff.md",
        "gcp_execution_trusted_validation_operator_packet.json",
        "gcp_execution_trusted_validation_operator_packet.md",
        "gcp_execution_trusted_validation_operator_handoff.md",
        "gcp_execution_launch_authorization.json",
        "gcp_execution_launch_authorization.md",
        "gcp_execution_launch_authorization_handoff.md",
        "gcp_execution_prearm_preflight.json",
        "gcp_execution_prearm_preflight.md",
        "gcp_execution_prearm_preflight_handoff.md",
        "gcp_execution_launch_surface_audit.json",
        "gcp_execution_launch_surface_audit.md",
        "gcp_execution_launch_surface_audit_handoff.md",
        "gcp_execution_launch_surface_broker_watch_observed.json",
        "gcp_execution_launch_surface_local_processes_observed.json",
        "gcp_execution_launch_surface_scheduled_tasks_observed.json"
    )
    $fileArgs = @()
    foreach ($file in $mirrorFiles) {
        $fileArgs += (Join-Path $reportDir $file)
    }
    & gcloud storage cp @fileArgs $GcsPrefix
    if ($LASTEXITCODE -ne 0) {
        throw "gcloud storage cp failed with exit code $LASTEXITCODE."
    }
}

$summary = @{
    attestation_json = $attestationPath
    prearm_preflight_json = $prearmPath
    exclusive_window_status_json = Join-Path $reportDir "gcp_execution_exclusive_window_status.json"
    trusted_validation_status_json = Join-Path $reportDir "gcp_execution_trusted_validation_session_status.json"
    trusted_launch_pack_json = Join-Path $reportDir "gcp_execution_trusted_validation_launch_pack.json"
    trusted_operator_packet_json = Join-Path $reportDir "gcp_execution_trusted_validation_operator_packet.json"
    launch_authorization_json = Join-Path $reportDir "gcp_execution_launch_authorization.json"
    closeout_status_json = Join-Path $reportDir "gcp_execution_closeout_status.json"
    mirrored_to_gcs = [bool]$MirrorToGcs
    gcs_prefix = $GcsPrefix
}

$summary | ConvertTo-Json -Depth 4
