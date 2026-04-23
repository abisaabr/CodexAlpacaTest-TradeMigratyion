[CmdletBinding()]
param(
    [string]$ControlPlaneRoot = "",
    [string]$VmName = "vm-execution-paper-01"
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

if (Test-Path $attestationPath) {
    Remove-Item -LiteralPath $attestationPath -Force
}

python $builders.ExclusiveWindow --report-dir $reportDir --project-id codexalpaca --vm-name $VmName
python $builders.TrustedValidation --report-dir $reportDir --project-id codexalpaca --vm-name $VmName
python $builders.TrustedLaunch --report-dir $reportDir --project-id codexalpaca --vm-name $VmName

$summary = @{
    cleared_attestation_json = $attestationPath
    exclusive_window_status_json = Join-Path $reportDir "gcp_execution_exclusive_window_status.json"
    trusted_validation_status_json = Join-Path $reportDir "gcp_execution_trusted_validation_session_status.json"
    trusted_launch_pack_json = Join-Path $reportDir "gcp_execution_trusted_validation_launch_pack.json"
}

$summary | ConvertTo-Json -Depth 4
