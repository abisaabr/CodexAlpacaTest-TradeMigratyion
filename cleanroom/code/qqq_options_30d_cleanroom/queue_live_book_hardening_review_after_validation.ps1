param(
    [string]$ValidationDir,
    [string]$ReviewOutputDir = "",
    [string]$LiveManifestPath = "C:\Users\rabisaab\Downloads\codexalpaca_repo\config\strategy_manifests\multi_ticker_portfolio_live.yaml",
    [int]$PollSeconds = 60,
    [int]$TimeoutMinutes = 720
)

$ErrorActionPreference = "Stop"

$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$validationRoot = [System.IO.Path]::GetFullPath($ValidationDir)
$statusFile = Join-Path $validationRoot "validation_followon_status.json"
$builderPath = Join-Path $scriptRoot "build_live_book_hardening_review.py"
$runRegistryReporterPath = Join-Path $scriptRoot "build_run_registry_report.py"
$defaultOutputRoot = Join-Path $scriptRoot "output"
$defaultRegistryPath = Join-Path $defaultOutputRoot "run_registry.jsonl"

if ([string]::IsNullOrWhiteSpace($ReviewOutputDir)) {
    $reviewRoot = Join-Path $validationRoot "hardening_review"
}
else {
    $reviewRoot = [System.IO.Path]::GetFullPath($ReviewOutputDir)
}

$logPath = Join-Path $reviewRoot "hardening_review_followon.log"
$followonStatusPath = Join-Path $reviewRoot "hardening_review_followon_status.json"
$runRegistryReportDir = Join-Path $reviewRoot "run_registry_report"
$deadline = (Get-Date).AddMinutes($TimeoutMinutes)

New-Item -ItemType Directory -Force -Path $reviewRoot | Out-Null
New-Item -ItemType Directory -Force -Path $runRegistryReportDir | Out-Null

function Write-Log {
    param([string]$Message)
    $timestamp = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
    Add-Content -Path $logPath -Value "[$timestamp] $Message"
}

function Write-Status {
    param(
        [string]$Phase,
        [string]$Message
    )
    $payload = [ordered]@{
        phase = $Phase
        message = $Message
        updated_at = (Get-Date).ToString("o")
        validation_dir = $validationRoot
        validation_status_file = $statusFile
        review_output_dir = $reviewRoot
        run_registry_report_dir = $runRegistryReportDir
    }
    $payload | ConvertTo-Json -Depth 6 | Set-Content -Path $followonStatusPath
}

function Invoke-RunRegistryReport {
    if (-not (Test-Path $runRegistryReporterPath)) {
        return
    }
    $reportArgs = @(
        $runRegistryReporterPath,
        "--output-root", $defaultOutputRoot,
        "--registry-path", $defaultRegistryPath,
        "--report-dir", $runRegistryReportDir
    )
    foreach ($root in @($validationRoot, $reviewRoot)) {
        if (Test-Path $root) {
            $reportArgs += @("--manifest-root", $root)
        }
    }
    & python @reportArgs | Out-Null
}

function Get-ValidationPhase {
    if (-not (Test-Path $statusFile)) {
        return $null
    }
    try {
        $payload = Get-Content $statusFile -Raw | ConvertFrom-Json
        return [string]$payload.phase
    }
    catch {
        return $null
    }
}

Write-Log "Waiting for validation completion in $validationRoot"
Write-Status -Phase "waiting" -Message "Waiting for live-book validation to reach a terminal state."
Invoke-RunRegistryReport

while ((Get-Date) -lt $deadline) {
    $phase = Get-ValidationPhase
    if ($phase -eq "completed") {
        Write-Log "Validation reached completed status. Starting hardening review build."
        break
    }
    if ($phase -eq "failed") {
        Write-Log "Validation reported failed status before hardening review could start."
        Write-Status -Phase "failed" -Message "Validation failed before hardening review could start."
        Invoke-RunRegistryReport
        exit 2
    }
    Start-Sleep -Seconds $PollSeconds
}

if ((Get-ValidationPhase) -ne "completed") {
    Write-Log "Timed out waiting for validation completion."
    Write-Status -Phase "failed" -Message "Timed out waiting for validation completion."
    Invoke-RunRegistryReport
    exit 3
}

Write-Status -Phase "reviewing" -Message "Building live-book hardening review packet."
Invoke-RunRegistryReport

& python $builderPath `
    --validation-dir $validationRoot `
    --output-dir $reviewRoot `
    --live-manifest $LiveManifestPath

if ($LASTEXITCODE -ne 0) {
    $reviewExitCode = $LASTEXITCODE
    Write-Log "Hardening review build failed with exit code $reviewExitCode."
    Write-Status -Phase "failed" -Message "Hardening review build failed."
    Invoke-RunRegistryReport
    exit $reviewExitCode
}

Write-Log "Hardening review build completed successfully."
Write-Status -Phase "completed" -Message "Hardening review build completed successfully."
Invoke-RunRegistryReport
exit 0
