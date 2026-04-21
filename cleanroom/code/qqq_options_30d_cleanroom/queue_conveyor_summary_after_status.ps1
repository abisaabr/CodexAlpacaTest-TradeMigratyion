param(
    [string]$WaitStatusPath,
    [string]$SummaryOutputDir,
    [string]$Quality6ResearchDir,
    [string]$CoreFamilyResearchDir,
    [string]$Ready6ResearchDir,
    [string]$Ready4ResearchDir,
    [string]$Quality6StatusPath,
    [string]$CoreFamilyStatusPath,
    [string]$Ready6StatusPath,
    [string]$Ready4StatusPath,
    [int]$PollSeconds = 60,
    [int]$TimeoutMinutes = 1440
)

$ErrorActionPreference = "Stop"

$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$waitStatusFile = [System.IO.Path]::GetFullPath($WaitStatusPath)
$summaryDir = [System.IO.Path]::GetFullPath($SummaryOutputDir)
$quality6Path = [System.IO.Path]::GetFullPath($Quality6ResearchDir)
$coreFamilyPath = [System.IO.Path]::GetFullPath($CoreFamilyResearchDir)
$ready6Path = [System.IO.Path]::GetFullPath($Ready6ResearchDir)
$ready4Path = [System.IO.Path]::GetFullPath($Ready4ResearchDir)
$quality6StatusFile = [System.IO.Path]::GetFullPath($Quality6StatusPath)
$coreFamilyStatusFile = [System.IO.Path]::GetFullPath($CoreFamilyStatusPath)
$ready6StatusFile = [System.IO.Path]::GetFullPath($Ready6StatusPath)
$ready4StatusFile = [System.IO.Path]::GetFullPath($Ready4StatusPath)
$summaryScriptPath = Join-Path $scriptRoot "summarize_tournament_conveyor.py"
$runRegistryReporterPath = Join-Path $scriptRoot "build_run_registry_report.py"
$defaultOutputRoot = Join-Path $scriptRoot "output"
$defaultRegistryPath = Join-Path $defaultOutputRoot "run_registry.jsonl"
$logsDir = Join-Path $summaryDir "logs"
$statusPath = Join-Path $summaryDir "summary_queue_status.json"
$logPath = Join-Path $logsDir "summary_queue.log"
$runRegistryReportDir = Join-Path $summaryDir "run_registry_report"
$deadline =
    if ($TimeoutMinutes -gt 0) {
        (Get-Date).AddMinutes($TimeoutMinutes)
    }
    else {
        $null
    }

New-Item -ItemType Directory -Force -Path $summaryDir | Out-Null
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
        wait_status_path = $waitStatusFile
        summary_output_dir = $summaryDir
        quality6_research_dir = $quality6Path
        core_family_research_dir = $coreFamilyPath
        ready6_research_dir = $ready6Path
        ready4_research_dir = $ready4Path
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
        "--manifest-root", $summaryDir
    )
    foreach ($manifestRoot in @($quality6Path, $coreFamilyPath, $ready6Path, $ready4Path)) {
        if (Test-Path $manifestRoot) {
            $reportArgs += @("--manifest-root", $manifestRoot)
        }
    }
    & python @reportArgs | Out-Null
}

function Get-WaitPhase {
    if (-not (Test-Path $waitStatusFile)) {
        return $null
    }
    try {
        $payload = Get-Content $waitStatusFile -Raw | ConvertFrom-Json
        return [string]$payload.phase
    }
    catch {
        return $null
    }
}

Write-Log "Waiting for final conveyor status file $waitStatusFile"
Write-Status -Phase "waiting" -Message "Waiting for the final tournament conveyor wave to finish."
Invoke-RunRegistryReport

while ($true) {
    if ($deadline -ne $null -and (Get-Date) -ge $deadline) {
        break
    }
    $phase = Get-WaitPhase
    if ($phase -eq "completed") {
        Write-Log "Final conveyor wave completed successfully."
        break
    }
    if ($phase -in @("failed", "blocked")) {
        Write-Log "Final conveyor wave ended with phase '$phase'. Proceeding to summarize partial results."
        break
    }
    Start-Sleep -Seconds $PollSeconds
}

if (-not (Test-Path $waitStatusFile)) {
    Write-Log "Timed out waiting for the final status file to appear."
    Write-Status -Phase "failed" -Message "Timed out waiting for the final conveyor status file."
    Invoke-RunRegistryReport
    exit 3
}

Write-Log "Launching consolidated conveyor summary."
Write-Status -Phase "summarizing" -Message "Building a consolidated summary across the tournament conveyor."
Invoke-RunRegistryReport

& python $summaryScriptPath `
    --output-dir $summaryDir `
    --wave "quality6=$quality6Path" `
    --wave "core_familyexp=$coreFamilyPath" `
    --wave "ready6_discovery=$ready6Path" `
    --wave "ready4_discovery=$ready4Path" `
    --status-file "quality6=$quality6StatusFile" `
    --status-file "core_familyexp=$coreFamilyStatusFile" `
    --status-file "ready6_discovery=$ready6StatusFile" `
    --status-file "ready4_discovery=$ready4StatusFile"

if ($LASTEXITCODE -ne 0) {
    $summaryExitCode = $LASTEXITCODE
    Write-Log "Summary generation failed with exit code $summaryExitCode."
    Write-Status -Phase "failed" -Message "Consolidated summary generation failed."
    Invoke-RunRegistryReport
    exit $summaryExitCode
}

Write-Log "Consolidated conveyor summary completed successfully."
Write-Status -Phase "completed" -Message "Consolidated tournament conveyor summary completed."
Invoke-RunRegistryReport
exit 0

