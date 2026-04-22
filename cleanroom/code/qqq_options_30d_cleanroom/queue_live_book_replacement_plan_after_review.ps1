param(
    [string]$ValidationDir,
    [string]$ReviewDir = "",
    [string]$PlanOutputDir = "",
    [string]$LiveManifestPath = "C:\Users\rabisaab\Downloads\codexalpaca_repo\config\strategy_manifests\multi_ticker_portfolio_live.yaml",
    [int]$PollSeconds = 60,
    [int]$TimeoutMinutes = 720
)

$ErrorActionPreference = "Stop"

$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$validationRoot = [System.IO.Path]::GetFullPath($ValidationDir)
if ([string]::IsNullOrWhiteSpace($ReviewDir)) {
    $reviewRoot = Join-Path $validationRoot "hardening_review"
}
else {
    $reviewRoot = [System.IO.Path]::GetFullPath($ReviewDir)
}
if ([string]::IsNullOrWhiteSpace($PlanOutputDir)) {
    $planRoot = Join-Path $reviewRoot "replacement_plan"
}
else {
    $planRoot = [System.IO.Path]::GetFullPath($PlanOutputDir)
}

$statusFile = Join-Path $reviewRoot "hardening_review_followon_status.json"
$builderPath = Join-Path $scriptRoot "build_live_book_replacement_plan.py"
$runRegistryReporterPath = Join-Path $scriptRoot "build_run_registry_report.py"
$defaultOutputRoot = Join-Path $scriptRoot "output"
$defaultRegistryPath = Join-Path $defaultOutputRoot "run_registry.jsonl"
$deadline = (Get-Date).AddMinutes($TimeoutMinutes)

$logPath = Join-Path $planRoot "replacement_plan_followon.log"
$followonStatusPath = Join-Path $planRoot "replacement_plan_followon_status.json"
$runRegistryReportDir = Join-Path $planRoot "run_registry_report"

New-Item -ItemType Directory -Force -Path $planRoot | Out-Null
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
        review_dir = $reviewRoot
        review_status_file = $statusFile
        plan_output_dir = $planRoot
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
    foreach ($root in @($validationRoot, $reviewRoot, $planRoot)) {
        if (Test-Path $root) {
            $reportArgs += @("--manifest-root", $root)
        }
    }
    & python @reportArgs | Out-Null
}

function Get-ReviewPhase {
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

Write-Log "Waiting for hardening review completion in $reviewRoot"
Write-Status -Phase "waiting" -Message "Waiting for live-book hardening review to reach a terminal state."
Invoke-RunRegistryReport

while ((Get-Date) -lt $deadline) {
    $phase = Get-ReviewPhase
    if ($phase -eq "completed") {
        Write-Log "Hardening review reached completed status. Starting replacement plan build."
        break
    }
    if ($phase -eq "failed") {
        Write-Log "Hardening review reported failed status before replacement plan could start."
        Write-Status -Phase "failed" -Message "Hardening review failed before replacement plan could start."
        Invoke-RunRegistryReport
        exit 2
    }
    Start-Sleep -Seconds $PollSeconds
}

if ((Get-ReviewPhase) -ne "completed") {
    Write-Log "Timed out waiting for hardening review completion."
    Write-Status -Phase "failed" -Message "Timed out waiting for hardening review completion."
    Invoke-RunRegistryReport
    exit 3
}

Write-Status -Phase "planning" -Message "Building live-book replacement plan."
Invoke-RunRegistryReport

& python $builderPath `
    --validation-dir $validationRoot `
    --review-dir $reviewRoot `
    --output-dir $planRoot `
    --live-manifest $LiveManifestPath

if ($LASTEXITCODE -ne 0) {
    $planExitCode = $LASTEXITCODE
    Write-Log "Replacement plan build failed with exit code $planExitCode."
    Write-Status -Phase "failed" -Message "Replacement plan build failed."
    Invoke-RunRegistryReport
    exit $planExitCode
}

Write-Log "Replacement plan build completed successfully."
Write-Status -Phase "completed" -Message "Replacement plan build completed successfully."
Invoke-RunRegistryReport
exit 0
