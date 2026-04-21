param(
    [string]$WaitStatusPath,
    [string]$ResearchDir,
    [string]$RepoDir = "C:\Users\rabisaab\OneDrive\CodexAlpaca\downloads_remaining_20260417\folders\codexalpaca_repo",
    [string]$ReadyBaseDir = "C:\Users\rabisaab\OneDrive - First American Corporation\qqq_options_30d_cleanroom\output\backtester_ready",
    [string[]]$Tickers,
    [string]$SelectionProfile = "balanced",
    [int]$ShardSize = 0,
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
        [string]$Message,
        [object[]]$Shards = @(),
        [string[]]$SuccessfulTickers = @(),
        [string[]]$FailedTickers = @()
    )
    $payload = [ordered]@{
        phase = $Phase
        message = $Message
        updated_at = (Get-Date).ToString("o")
        wait_status_path = $waitStatusFile
        research_dir = $researchPath
        repo_dir = $repoPath
        ready_base_dir = $readyBasePath
        selection_profile = $SelectionProfile
        tickers = $Tickers
    }
    if ($Shards.Count -gt 0) {
        $payload.shards = $Shards
    }
    if ($SuccessfulTickers.Count -gt 0) {
        $payload.successful_tickers = $SuccessfulTickers
    }
    if ($FailedTickers.Count -gt 0) {
        $payload.failed_tickers = $FailedTickers
    }
    $payload | ConvertTo-Json -Depth 8 | Set-Content -Path $statusPath
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

function Invoke-FamilyExpansionShard {
    param(
        [string[]]$ShardTickers,
        [int]$ShardIndex,
        [int]$ShardCount
    )

    $shardSuffix = "{0:D2}_{1}" -f $ShardIndex, ($ShardTickers -join "_")
    $shardResearchPath =
        if ($ShardCount -gt 1) {
            Join-Path $researchPath ("shards\" + $shardSuffix)
        }
        else {
            $researchPath
        }
    New-Item -ItemType Directory -Force -Path $shardResearchPath | Out-Null

    Write-Log "Launching family-expansion shard $ShardIndex/$ShardCount for $($ShardTickers -join ', ')"
    & python $launcherPath `
        --tickers ($ShardTickers -join ",") `
        --ready-base-dir $readyBasePath `
        --research-dir $shardResearchPath `
        --strategy-set "family_expansion" `
        --selection-profile $SelectionProfile

    if ($LASTEXITCODE -ne 0) {
        Write-Log "Shard $ShardIndex/$ShardCount failed with exit code $LASTEXITCODE."
        return [ordered]@{
            shard_index = $ShardIndex
            tickers = $ShardTickers
            research_dir = $shardResearchPath
            phase = "failed"
            stage = "research"
            exit_code = $LASTEXITCODE
        }
    }

    Write-Log "Shard $ShardIndex/$ShardCount finished research. Starting promotion flow."
    & powershell -ExecutionPolicy Bypass -File $promotionPath `
        -ResearchDir $shardResearchPath `
        -RepoDir $repoPath `
        -Tickers $ShardTickers `
        -PollSeconds 10 `
        -TimeoutMinutes 60

    if ($LASTEXITCODE -ne 0) {
        Write-Log "Shard $ShardIndex/$ShardCount promotion failed with exit code $LASTEXITCODE."
        return [ordered]@{
            shard_index = $ShardIndex
            tickers = $ShardTickers
            research_dir = $shardResearchPath
            phase = "failed"
            stage = "promotion"
            exit_code = $LASTEXITCODE
        }
    }

    Write-Log "Shard $ShardIndex/$ShardCount completed successfully."
    return [ordered]@{
        shard_index = $ShardIndex
        tickers = $ShardTickers
        research_dir = $shardResearchPath
        phase = "completed"
        stage = "completed"
        exit_code = 0
    }
}

function Build-Shards {
    if ($ShardSize -le 0 -or $Tickers.Count -le $ShardSize) {
        return @(@($Tickers))
    }

    $shards = @()
    for ($index = 0; $index -lt $Tickers.Count; $index += $ShardSize) {
        $endIndex = [Math]::Min($index + $ShardSize - 1, $Tickers.Count - 1)
        $chunk = @($Tickers[$index..$endIndex])
        $shards += ,$chunk
    }
    return $shards
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

$shards = Build-Shards
$shardCount = $shards.Count
$allShardResults = @()

Write-Log "Launching queued family-expansion tournament for $($Tickers -join ', ') in $shardCount shard(s)."
Write-Status -Phase "running_family_expansion" -Message "Launching queued family-expansion tournament." -Shards $allShardResults

for ($shardIndex = 0; $shardIndex -lt $shardCount; $shardIndex++) {
    $result = Invoke-FamilyExpansionShard -ShardTickers $shards[$shardIndex] -ShardIndex ($shardIndex + 1) -ShardCount $shardCount
    $allShardResults += $result

    $successfulTickers = @(
        $allShardResults |
            Where-Object { $_.phase -eq "completed" } |
            ForEach-Object { $_.tickers } |
            ForEach-Object { $_ }
    )
    $failedTickers = @(
        $allShardResults |
            Where-Object { $_.phase -ne "completed" } |
            ForEach-Object { $_.tickers } |
            ForEach-Object { $_ }
    )

    Write-Status `
        -Phase "running_family_expansion" `
        -Message "Processed $($shardIndex + 1) of $shardCount family-expansion shard(s)." `
        -Shards $allShardResults `
        -SuccessfulTickers $successfulTickers `
        -FailedTickers $failedTickers
}

$completedShards = @($allShardResults | Where-Object { $_.phase -eq "completed" })
$failedShards = @($allShardResults | Where-Object { $_.phase -ne "completed" })
$successfulTickers = @(
    $completedShards |
        ForEach-Object { $_.tickers } |
        ForEach-Object { $_ }
)
$failedTickers = @(
    $failedShards |
        ForEach-Object { $_.tickers } |
        ForEach-Object { $_ }
)

$shardSummaryPath = Join-Path $researchPath "shard_run_summary.json"
[ordered]@{
    tickers = $Tickers
    shard_size = $ShardSize
    shard_count = $shardCount
    completed_shard_count = $completedShards.Count
    failed_shard_count = $failedShards.Count
    successful_tickers = $successfulTickers
    failed_tickers = $failedTickers
    shards = $allShardResults
} | ConvertTo-Json -Depth 8 | Set-Content -Path $shardSummaryPath

if ($completedShards.Count -eq 0) {
    Write-Log "All queued family-expansion shards failed."
    Write-Status `
        -Phase "failed" `
        -Message "All queued family-expansion shards failed." `
        -Shards $allShardResults `
        -SuccessfulTickers $successfulTickers `
        -FailedTickers $failedTickers
    exit 4
}

$message =
    if ($failedShards.Count -gt 0) {
        "Queued family-expansion shards completed with partial failures, and successful winners were promoted to GitHub."
    }
    else {
        "Queued family-expansion run completed and winners were promoted to GitHub."
    }

Write-Log $message
Write-Status `
    -Phase "completed" `
    -Message $message `
    -Shards $allShardResults `
    -SuccessfulTickers $successfulTickers `
    -FailedTickers $failedTickers
exit 0
