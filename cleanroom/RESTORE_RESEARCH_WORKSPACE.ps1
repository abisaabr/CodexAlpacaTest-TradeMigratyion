param(
    [string]$TargetParent = (Split-Path -Parent $PSScriptRoot),
    [switch]$Force
)

$ErrorActionPreference = "Stop"

$zipPath = Join-Path $PSScriptRoot "qqq_options_30d_cleanroom_snapshot.zip"
$destination = Join-Path $TargetParent "qqq_options_30d_cleanroom"
$repoSibling = Join-Path $TargetParent "codexalpaca_repo"

if (-not (Test-Path $zipPath)) {
    throw "Missing workspace archive at $zipPath"
}

if ((Test-Path $destination) -and -not $Force) {
    throw "Destination already exists at $destination. Rerun with -Force to overwrite."
}

if (Test-Path $destination) {
    Remove-Item -LiteralPath $destination -Recurse -Force
}

Expand-Archive -LiteralPath $zipPath -DestinationPath $TargetParent -Force

Write-Host "Restored research workspace to $destination"
if (-not (Test-Path $repoSibling)) {
    Write-Warning "Expected sibling repo missing at $repoSibling. The cleanroom research scripts assume qqq_options_30d_cleanroom and codexalpaca_repo share the same parent folder."
} else {
    Write-Host "Detected sibling repo at $repoSibling"
}

Write-Host ""
Write-Host "Next steps:"
Write-Host "  1. Verify codexalpaca_repo exists beside the restored workspace."
Write-Host "  2. Use the repo virtualenv when running the cleanroom scripts."
Write-Host "  3. Example:"
Write-Host "     cd $repoSibling"
Write-Host "     .\.venv\Scripts\python.exe ..\qqq_options_30d_cleanroom\research_candidate_ticker_batch.py --tickers aapl,amzn"
