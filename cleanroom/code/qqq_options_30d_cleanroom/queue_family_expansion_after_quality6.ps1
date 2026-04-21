param(
    [string]$WaitResearchDir = "C:\Users\rabisaab\Downloads\qqq_options_30d_cleanroom\output\candidate_batch_research_20260419_quality6_followon",
    [string]$FamilyResearchDir = "C:\Users\rabisaab\Downloads\qqq_options_30d_cleanroom\output\candidate_batch_research_20260419_familyexp_core5_overnight",
    [string]$RepoDir = "C:\Users\rabisaab\OneDrive\CodexAlpaca\downloads_remaining_20260417\folders\codexalpaca_repo",
    [string]$ReadyBaseDir = "C:\Users\rabisaab\OneDrive - First American Corporation\qqq_options_30d_cleanroom\output\backtester_ready",
    [string[]]$Tickers = @("qqq", "spy", "iwm", "nvda", "tsla"),
    [int]$PollSeconds = 60,
    [int]$TimeoutMinutes = 720
)

$ErrorActionPreference = "Stop"

$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$waitResearchPath = [System.IO.Path]::GetFullPath($WaitResearchDir)
$familyResearchPath = [System.IO.Path]::GetFullPath($FamilyResearchDir)
$repoPath = [System.IO.Path]::GetFullPath($RepoDir)
$readyBasePath = [System.IO.Path]::GetFullPath($ReadyBaseDir)
$launcherPath = Join-Path $scriptRoot "run_core_strategy_expansion_overnight.py"
$promotionPath = Join-Path $scriptRoot "wait_and_sync_live_manifest.ps1"
$runRegistryReporterPath = Join-Path $scriptRoot "build_run_registry_report.py"
$defaultOutputRoot = Join-Path $scriptRoot "output"
$defaultRegistryPath = Join-Path $defaultOutputRoot "run_registry.jsonl"
$waitSummaryPath = Join-Path $waitResearchPath "master_summary.json"
$waitStatusPath = Join-Path $waitResearchPath "followon_status.json"
$logsDir = Join-Path $familyResearchPath "logs"
$statusPath = Join-Path $familyResearchPath "familyexp_queue_status.json"
$logPath = Join-Path $logsDir "familyexp_queue.log"
$runRegistryReportDir = Join-Path $familyResearchPath "run_registry_report"
$deadline = (Get-Date).AddMinutes($TimeoutMinutes)

New-Item -ItemType Directory -Force -Path $familyResearchPath | Out-Null
New-Item -ItemType Directory -Force -Path $logsDir | Out-Null
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
        wait_research_dir = $waitResearchPath
        family_research_dir = $familyResearchPath
        repo_dir = $repoPath
        ready_base_dir = $readyBasePath
        tickers = $Tickers
        run_registry_report_dir = $runRegistryReportDir
    }
    $payload | ConvertTo-Json | Set-Content -Path $statusPath
}

function Invoke-RunRegistryReport {
    if (-not (Test-Path $runRegistryReporterPath)) {
        return
    }
    $reportArgs = @(
        $runRegistryReporterPath,
        "--output-root", $defaultOutputRoot,
        "--registry-path", $defaultRegistryPath,
        "--report-dir", $runRegistryReportDir,
        "--manifest-root", $familyResearchPath
    )
    if (Test-Path $waitResearchPath) {
        $reportArgs += @("--manifest-root", $waitResearchPath)
    }
    & python @reportArgs | Out-Null
}

function Test-WaitBatchBlocked {
    if (-not (Test-Path $waitStatusPath)) {
        return $false
    }
    $payload = Get-Content $waitStatusPath -Raw | ConvertFrom-Json
    return $payload.phase -in @("blocked", "failed")
}

Write-Log "Waiting for queued quality batch outputs in $waitResearchPath"
Write-Status -Phase "waiting" -Message "Waiting for the queued quality batch to finish."
Invoke-RunRegistryReport

while ((Get-Date) -lt $deadline) {
    if (Test-Path $waitSummaryPath) {
        Write-Log "Detected quality batch success artifact at $waitSummaryPath"
        break
    }
    if (Test-WaitBatchBlocked) {
        Write-Log "Quality batch reported a blocked/failed status before producing master_summary.json"
        Write-Status -Phase "failed" -Message "Quality batch failed before the family expansion run could start."
        Invoke-RunRegistryReport
        exit 2
    }
    Start-Sleep -Seconds $PollSeconds
}

if (-not (Test-Path $waitSummaryPath)) {
    Write-Log "Timed out waiting for the quality batch success artifact."
    Write-Status -Phase "failed" -Message "Timed out waiting for the queued quality batch to finish."
    Invoke-RunRegistryReport
    exit 3
}

Write-Status -Phase "running_family_expansion" -Message "Launching the family-expansion overnight tournament."
Write-Log "Launching family-expansion overnight run for $($Tickers -join ', ')"
Invoke-RunRegistryReport

& python $launcherPath `
    --tickers ($Tickers -join ",") `
    --ready-base-dir $readyBasePath `
    --research-dir $familyResearchPath `
    --strategy-set "family_expansion"

if ($LASTEXITCODE -ne 0) {
    $familyExitCode = $LASTEXITCODE
    Write-Log "Family-expansion overnight run failed with exit code $familyExitCode"
    Write-Status -Phase "failed" -Message "Family-expansion overnight run failed."
    Invoke-RunRegistryReport
    exit $familyExitCode
}

Write-Log "Family-expansion overnight run finished. Starting GitHub promotion flow."
Write-Status -Phase "promoting" -Message "Exporting and syncing family-expansion winners into the live manifest."
Invoke-RunRegistryReport

& powershell -ExecutionPolicy Bypass -File $promotionPath `
    -ResearchDir $familyResearchPath `
    -RepoDir $repoPath `
    -Tickers $Tickers `
    -PollSeconds 10 `
    -TimeoutMinutes 60

if ($LASTEXITCODE -ne 0) {
    $promotionExitCode = $LASTEXITCODE
    Write-Log "Promotion flow failed with exit code $promotionExitCode"
    Write-Status -Phase "failed" -Message "Family-expansion run completed, but promotion to GitHub failed."
    Invoke-RunRegistryReport
    exit $promotionExitCode
}

Write-Log "Family-expansion run and promotion flow completed successfully."
Write-Status -Phase "completed" -Message "Family-expansion run completed and winners were promoted to GitHub."
Invoke-RunRegistryReport
exit 0
