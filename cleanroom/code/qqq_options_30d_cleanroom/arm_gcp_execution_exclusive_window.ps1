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
    [string]$Notes = "Bounded exclusive window for the first sanctioned GCP trusted validation session."
)

$ErrorActionPreference = "Stop"

if (-not $ControlPlaneRoot) {
    $ControlPlaneRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..\..")).Path
}

$reportDir = Join-Path $ControlPlaneRoot "docs\gcp_foundation"
$attestationPath = Join-Path $reportDir "gcp_execution_exclusive_window_attestation.json"

$builders = @{
    ExclusiveWindow = Join-Path $PSScriptRoot "build_gcp_execution_exclusive_window_status.py"
    TrustedValidation = Join-Path $PSScriptRoot "build_gcp_execution_trusted_validation_session_status.py"
    TrustedLaunch = Join-Path $PSScriptRoot "build_gcp_execution_trusted_validation_launch_pack.py"
}

foreach ($builder in $builders.GetEnumerator()) {
    if (-not (Test-Path $builder.Value)) {
        throw "Builder not found: $($builder.Value)"
    }
}

$startsAt = [datetimeoffset]::Parse($WindowStartsAt).ToString("o")
$expiresAt = [datetimeoffset]::Parse($WindowExpiresAt).ToString("o")
$confirmedAt = [datetimeoffset]::Now.ToString("o")

$attestation = @{
    window_id = "trusted-validation-session-$VmName"
    confirmed_by = $ConfirmedBy
    confirmed_at = $confirmedAt
    window_starts_at = $startsAt
    window_expires_at = $expiresAt
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

python $builders.ExclusiveWindow --report-dir $reportDir --project-id codexalpaca --vm-name $VmName
python $builders.TrustedValidation --report-dir $reportDir --project-id codexalpaca --vm-name $VmName
python $builders.TrustedLaunch --report-dir $reportDir --project-id codexalpaca --vm-name $VmName

$summary = @{
    attestation_json = $attestationPath
    exclusive_window_status_json = Join-Path $reportDir "gcp_execution_exclusive_window_status.json"
    trusted_validation_status_json = Join-Path $reportDir "gcp_execution_trusted_validation_session_status.json"
    trusted_launch_pack_json = Join-Path $reportDir "gcp_execution_trusted_validation_launch_pack.json"
}

$summary | ConvertTo-Json -Depth 4
