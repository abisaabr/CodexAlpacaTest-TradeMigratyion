param(
    [string]$ResearchDir = "C:\Users\rabisaab\Downloads\qqq_options_30d_cleanroom\output\candidate_batch_research_20260417_coreexp5_exhaustive_overnight",
    [string]$RepoDir = "C:\Users\rabisaab\OneDrive\CodexAlpaca\downloads_remaining_20260417\folders\codexalpaca_repo",
    [string[]]$Tickers = @("qqq", "spy", "iwm", "nvda", "tsla"),
    [int]$PollSeconds = 30,
    [int]$TimeoutMinutes = 360
)

$ErrorActionPreference = "Stop"

$researchPath = [System.IO.Path]::GetFullPath($ResearchDir)
$repoPath = [System.IO.Path]::GetFullPath($RepoDir)
$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$exporterPath = Join-Path $scriptRoot "export_promoted_strategies.py"
$runRegistryReporterPath = Join-Path $scriptRoot "build_run_registry_report.py"
$defaultOutputRoot = Join-Path $scriptRoot "output"
$defaultRegistryPath = Join-Path $defaultOutputRoot "run_registry.jsonl"
$syncScriptPath = Join-Path $repoPath "scripts\sync_live_strategy_manifest.py"
$logPath = Join-Path $researchPath "promotion_followon.log"
$statusPath = Join-Path $researchPath "promotion_followon_status.json"
$runRegistryReportDir = Join-Path $researchPath "run_registry_report"
$promotedYamlPath = Join-Path $researchPath "promoted_strategies.yaml"
$deadline = (Get-Date).AddMinutes($TimeoutMinutes)

New-Item -ItemType Directory -Force -Path $researchPath | Out-Null
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
        research_dir = $researchPath
        repo_dir = $repoPath
        promoted_yaml_path = $promotedYamlPath
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
        "--manifest-root", $researchPath
    )
    & python @reportArgs | Out-Null
}

function Test-TournamentReady {
    $requiredPaths = @(
        (Join-Path $researchPath "master_summary.json"),
        (Join-Path $researchPath "master_report.md")
    )
    foreach ($ticker in $Tickers) {
        $requiredPaths += Join-Path $researchPath ("{0}_summary.json" -f $ticker.ToLower())
    }
    foreach ($path in $requiredPaths) {
        if (-not (Test-Path $path)) {
            return $false
        }
    }
    return $true
}

function Get-TournamentProcess {
    Get-CimInstance Win32_Process | Where-Object {
        $_.CommandLine -like '*run_multiticker_cleanroom_portfolio.py*' -and
        $_.CommandLine -like "*$researchPath*"
    }
}

Write-Log "Waiting for tournament outputs in $researchPath"
Write-Status -Phase "waiting" -Message "Waiting for tournament outputs."
Invoke-RunRegistryReport

while ((Get-Date) -lt $deadline) {
    if (Test-TournamentReady) {
        Write-Log "Tournament outputs detected. Starting export and live manifest sync."
        Write-Status -Phase "exporting" -Message "Tournament outputs detected. Exporting promoted strategies."
        Invoke-RunRegistryReport
        break
    }

    $process = Get-TournamentProcess
    if (-not $process) {
        Write-Log "Tournament process is no longer running before required outputs were written."
        Write-Status -Phase "failed" -Message "Tournament stopped before all expected outputs were available."
        Invoke-RunRegistryReport
        exit 2
    }
    Start-Sleep -Seconds $PollSeconds
}

if (-not (Test-TournamentReady)) {
    Write-Log "Timed out waiting for tournament outputs."
    Write-Status -Phase "failed" -Message "Timed out waiting for tournament outputs."
    Invoke-RunRegistryReport
    exit 3
}

& python $exporterPath --research-dir $researchPath
if ($LASTEXITCODE -ne 0) {
    Write-Log "Exporter failed with exit code $LASTEXITCODE."
    Write-Status -Phase "failed" -Message "Exporter failed."
    Invoke-RunRegistryReport
    exit $LASTEXITCODE
}
Write-Log "Exporter completed successfully."

Write-Status -Phase "syncing" -Message "Syncing promoted strategies into the live manifest."
Invoke-RunRegistryReport
& python $syncScriptPath --source $promotedYamlPath --merge-base current
if ($LASTEXITCODE -ne 0) {
    Write-Log "Live manifest sync failed with exit code $LASTEXITCODE."
    Write-Status -Phase "failed" -Message "Live manifest sync failed."
    Invoke-RunRegistryReport
    exit $LASTEXITCODE
}
Write-Log "Live manifest sync completed successfully."

& python $syncScriptPath --validate-only
if ($LASTEXITCODE -ne 0) {
    Write-Log "Live manifest validation failed with exit code $LASTEXITCODE."
    Write-Status -Phase "failed" -Message "Live manifest validation failed."
    Invoke-RunRegistryReport
    exit $LASTEXITCODE
}
Write-Log "Live manifest validation completed successfully."

Push-Location $repoPath
try {
    git add config/strategy_manifests/multi_ticker_portfolio_live.yaml
    if ($LASTEXITCODE -ne 0) {
        throw "git add failed"
    }
    git diff --cached --quiet
    if ($LASTEXITCODE -eq 0) {
        Write-Log "No live manifest changes detected after sync."
        Write-Status -Phase "completed" -Message "Exporter and sync completed. No manifest changes to commit."
        Invoke-RunRegistryReport
        exit 0
    }
    git commit -m "Promote tournament winners into live manifest"
    if ($LASTEXITCODE -ne 0) {
        throw "git commit failed"
    }
    git push origin codex/qqq-paper-portfolio
    if ($LASTEXITCODE -ne 0) {
        throw "git push failed"
    }
}
finally {
    Pop-Location
}

Write-Log "Live manifest changes committed and pushed."
Write-Status -Phase "completed" -Message "Exporter, sync, validation, commit, and push completed."
Invoke-RunRegistryReport
exit 0
