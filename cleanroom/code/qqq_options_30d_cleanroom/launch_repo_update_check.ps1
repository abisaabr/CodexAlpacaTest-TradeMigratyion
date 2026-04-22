[CmdletBinding()]
param(
    [string]$ControlPlaneRoot = "",
    [string]$ExecutionRepoRoot = "",
    [string]$ReportDir = "",
    [switch]$SkipFetch
)

$ErrorActionPreference = "Stop"

if (-not $ControlPlaneRoot) {
    $ControlPlaneRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..\..")).Path
}

$builder = Join-Path $PSScriptRoot "build_repo_update_registry.py"
if (-not (Test-Path $builder)) {
    throw "Builder not found: $builder"
}

if (-not $ExecutionRepoRoot) {
    $candidate = Join-Path (Split-Path $ControlPlaneRoot -Parent) "codexalpaca_repo"
    if (Test-Path $candidate) {
        $ExecutionRepoRoot = (Resolve-Path $candidate).Path
    }
}

if (-not $ReportDir) {
    $ReportDir = Join-Path $ControlPlaneRoot "docs\repo_updates"
}

$args = @(
    $builder,
    "--control-plane-root", $ControlPlaneRoot,
    "--report-dir", $ReportDir
)

if ($ExecutionRepoRoot) {
    $args += @("--execution-repo-root", $ExecutionRepoRoot)
}

if ($SkipFetch) {
    $args += "--skip-fetch"
}

python @args
