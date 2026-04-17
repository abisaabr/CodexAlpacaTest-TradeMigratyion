param(
    [string]$TargetParent = (Split-Path -Parent $PSScriptRoot),
    [string]$MainRepoPath = "",
    [switch]$Force
)

$ErrorActionPreference = "Stop"

$migrationRepo = Split-Path -Parent $PSScriptRoot
if ([string]::IsNullOrWhiteSpace($MainRepoPath)) {
    $MainRepoPath = Join-Path $TargetParent "codexalpaca_repo"
}

$runtimeZip = Join-Path $migrationRepo "runtime\public_runtime_migration_20260417.zip"
$cleanroomCodeSource = Join-Path $migrationRepo "cleanroom\code\qqq_options_30d_cleanroom"
$cleanroomSummaryZip = Join-Path $migrationRepo "cleanroom\qqq_options_30d_cleanroom_summaries_20260417.zip"
$cleanroomTarget = Join-Path $TargetParent "qqq_options_30d_cleanroom"

if (-not (Test-Path $MainRepoPath)) {
    throw "Main repo path not found at $MainRepoPath. Clone abisaabr/CodexAlpacaTest-Trade first."
}

if (-not (Test-Path $runtimeZip)) {
    throw "Missing runtime bundle at $runtimeZip"
}

if ((Test-Path $cleanroomTarget) -and -not $Force) {
    throw "Cleanroom target already exists at $cleanroomTarget. Re-run with -Force to overwrite."
}

if (Test-Path $cleanroomTarget) {
    Remove-Item -LiteralPath $cleanroomTarget -Recurse -Force
}

$runtimeExtractRoot = Join-Path ([System.IO.Path]::GetTempPath()) ("codexalpaca_runtime_restore_" + [System.Guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Force -Path $runtimeExtractRoot | Out-Null

try {
    New-Item -ItemType Directory -Force -Path $cleanroomTarget | Out-Null
    Copy-Item -LiteralPath (Join-Path $cleanroomCodeSource '*') -Destination $cleanroomTarget -Recurse -Force
    Expand-Archive -LiteralPath $cleanroomSummaryZip -DestinationPath $TargetParent -Force
    Expand-Archive -LiteralPath $runtimeZip -DestinationPath $runtimeExtractRoot -Force

    $payloadRoot = Join-Path $runtimeExtractRoot "public_runtime_migration_20260417\payload"
    if (-not (Test-Path $payloadRoot)) {
        throw "Expected runtime payload not found at $payloadRoot"
    }
    Copy-Item -LiteralPath (Join-Path $payloadRoot '*') -Destination $MainRepoPath -Recurse -Force
}
finally {
    if (Test-Path $runtimeExtractRoot) {
        Remove-Item -LiteralPath $runtimeExtractRoot -Recurse -Force
    }
}

Write-Host "Restored public runtime state into $MainRepoPath"
Write-Host "Restored cleanroom code into $cleanroomTarget"
Write-Host ""
Write-Host "Next steps:"
Write-Host "  1. Fill the local .env in $MainRepoPath"
Write-Host "  2. Point ownership lease settings at your shared drive path"
Write-Host "  3. Run the standby failover check from the main repo"
Write-Host "  4. Review docs\\NEW_MACHINE_CODEX_PROMPTS.md for the Codex setup prompts"
