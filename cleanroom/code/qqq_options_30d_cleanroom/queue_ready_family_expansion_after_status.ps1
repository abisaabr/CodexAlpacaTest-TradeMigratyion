param(
    [string]$WaitStatusPath,
    [string]$ResearchDir,
    [string]$RepoDir = "C:\Users\rabisaab\OneDrive\CodexAlpaca\downloads_remaining_20260417\folders\codexalpaca_repo",
    [string]$ReadyBaseDir = "C:\Users\rabisaab\OneDrive - First American Corporation\qqq_options_30d_cleanroom\output\backtester_ready",
    [string[]]$Tickers,
    [int]$PollSeconds = 60,
    [int]$TimeoutMinutes = 720
)

$ErrorActionPreference = "Stop"

$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$waitStatusFile = [System.IO.Path]::GetFullPath($WaitStatusPath)
$researchPath = [System.IO.Path]::GetFullPath($ResearchDir)
$repoPath = [System.IO.Path]::GetFullPath($RepoDir)
$readyBasePath = [System.IO.Path]::GetFullPath($ReadyBaseDir)
$normalizedTickers = @()
foreach ($tickerArg in $Tickers) {
    if ([string]::IsNullOrWhiteSpace($tickerArg)) {
        continue
    }
    foreach ($ticker in ($tickerArg -split ",")) {
        $clean = $ticker.Trim().ToLower()
        if (-not [string]::IsNullOrWhiteSpace($clean)) {
            $normalizedTickers += $clean
        }
    }
}
$Tickers = $normalizedTickers
$launcherPath = Join-Path $scriptRoot "run_core_strategy_expansion_overnight.py"
$promotionPath = Join-Path $scriptRoot "wait_and_sync_live_manifest.ps1"
$logsDir = Join-Path $researchPath "logs"
$statusPath = Join-Path $researchPath "queued_familyexp_status.json"
$logPath = Join-Path $logsDir "queued_familyexp.log"
$deadline = (Get-Date).AddMinutes($TimeoutMinutes)

New-Item -ItemType Directory -Force -Path $researchPath | Out-Null
New-Item -ItemType Directory -Force -Path $logsDir | Out-Null

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
        research_dir = $researchPath
        repo_dir = $repoPath
        ready_base_dir = $readyBasePath
        tickers = $Tickers
    }
    $payload | ConvertTo-Json | Set-Content -Path $statusPath
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

Write-Log "Waiting for upstream status file $waitStatusFile"
Write-Status -Phase "waiting" -Message "Waiting for the upstream tournament and promotion flow to complete."

while ((Get-Date) -lt $deadline) {
    $phase = Get-WaitPhase
    if ($phase -eq "completed") {
        Write-Log "Upstream status file reports completed."
        break
    }
    if ($phase -in @("failed", "blocked")) {
        Write-Log "Upstream status file reports phase '$phase'. Aborting queued family expansion."
        Write-Status -Phase "failed" -Message "Upstream tournament failed before this queued family-expansion batch could start."
        exit 2
    }
    Start-Sleep -Seconds $PollSeconds
}

if ((Get-WaitPhase) -ne "completed") {
    Write-Log "Timed out waiting for upstream completion."
    Write-Status -Phase "failed" -Message "Timed out waiting for the upstream tournament to complete."
    exit 3
}

Write-Log "Launching queued family-expansion tournament for $($Tickers -join ', ')"
Write-Status -Phase "running_family_expansion" -Message "Launching queued family-expansion tournament."

& python $launcherPath `
    --tickers ($Tickers -join ",") `
    --ready-base-dir $readyBasePath `
    --research-dir $researchPath `
    --strategy-set "family_expansion"

if ($LASTEXITCODE -ne 0) {
    Write-Log "Queued family-expansion run failed with exit code $LASTEXITCODE"
    Write-Status -Phase "failed" -Message "Queued family-expansion run failed."
    exit $LASTEXITCODE
}

Write-Log "Queued family-expansion tournament finished. Starting promotion flow."
Write-Status -Phase "promoting" -Message "Exporting and syncing queued family-expansion winners into the live manifest."

& powershell -ExecutionPolicy Bypass -File $promotionPath `
    -ResearchDir $researchPath `
    -RepoDir $repoPath `
    -Tickers $Tickers `
    -PollSeconds 10 `
    -TimeoutMinutes 60

if ($LASTEXITCODE -ne 0) {
    Write-Log "Promotion flow failed with exit code $LASTEXITCODE"
    Write-Status -Phase "failed" -Message "Queued family-expansion run completed, but promotion to GitHub failed."
    exit $LASTEXITCODE
}

Write-Log "Queued family-expansion run and promotion flow completed successfully."
Write-Status -Phase "completed" -Message "Queued family-expansion run completed and winners were promoted to GitHub."
exit 0
