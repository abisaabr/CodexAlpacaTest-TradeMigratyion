param(
    [string]$WaitStatusPath,
    [string]$ResearchDir,
    [string]$RepoDir = "C:\Users\rabisaab\OneDrive\CodexAlpaca\downloads_remaining_20260417\folders\codexalpaca_repo",
    [string]$ReadyBaseDir = "C:\Users\rabisaab\OneDrive - First American Corporation\qqq_options_30d_cleanroom\output\backtester_ready",
    [string[]]$Tickers,
    [string]$StrategySet = "family_expansion",
    [string]$SelectionProfile = "balanced",
    [string]$FamilyInclude = "",
    [string]$FamilyExclude = "",
    [string]$PromotionMode = "after_shard",
    [int]$ShardSize = 0,
    [int]$MaxParallelShards = 1,
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
$runRegistryReporterPath = Join-Path $scriptRoot "build_run_registry_report.py"
$defaultOutputRoot = Join-Path $scriptRoot "output"
$defaultRegistryPath = Join-Path $defaultOutputRoot "run_registry.jsonl"
$logsDir = Join-Path $researchPath "logs"
$statusPath = Join-Path $researchPath "queued_familyexp_status.json"
$logPath = Join-Path $logsDir "queued_familyexp.log"
$runRegistryReportDir = Join-Path $researchPath "run_registry_report"
$deadline =
    if ($TimeoutMinutes -gt 0) {
        (Get-Date).AddMinutes($TimeoutMinutes)
    }
    else {
        $null
    }

New-Item -ItemType Directory -Force -Path $researchPath | Out-Null
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
        strategy_set = $StrategySet
        selection_profile = $SelectionProfile
        family_include = $FamilyInclude
        family_exclude = $FamilyExclude
        promotion_mode = $PromotionMode
        max_parallel_shards = $MaxParallelShards
        tickers = $Tickers
        run_registry_report_dir = $runRegistryReportDir
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
    $shardsDir = Join-Path $researchPath "shards"
    if (Test-Path $shardsDir) {
        $reportArgs += @("--manifest-root", $shardsDir)
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

function Get-TournamentLabel {
    switch ($StrategySet) {
        "family_expansion" { return "family-expansion" }
        "down_choppy_only" { return "down/choppy-only" }
        default { return ($StrategySet -replace "_", "-") }
    }
}

$tournamentLabel = Get-TournamentLabel

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

    Write-Log "Launching $tournamentLabel shard $ShardIndex/$ShardCount for $($ShardTickers -join ', ')"
    $launchArgs = @(
        $launcherPath,
        "--tickers", ($ShardTickers -join ","),
        "--ready-base-dir", $readyBasePath,
        "--research-dir", $shardResearchPath,
        "--strategy-set", $StrategySet,
        "--selection-profile", $SelectionProfile
    )
    if (-not [string]::IsNullOrWhiteSpace($FamilyInclude)) {
        $launchArgs += @("--family-include", $FamilyInclude)
    }
    if (-not [string]::IsNullOrWhiteSpace($FamilyExclude)) {
        $launchArgs += @("--family-exclude", $FamilyExclude)
    }
    & python @launchArgs | Out-Null

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

    if ($PromotionMode -eq "none") {
        Write-Log "Shard $ShardIndex/$ShardCount finished research. Promotion is disabled for this run."
        return [ordered]@{
            shard_index = $ShardIndex
            tickers = $ShardTickers
            research_dir = $shardResearchPath
            phase = "completed"
            stage = "research_only"
            exit_code = 0
        }
    }

    Write-Log "Shard $ShardIndex/$ShardCount finished research. Starting promotion flow."
    & powershell -ExecutionPolicy Bypass -File $promotionPath `
        -ResearchDir $shardResearchPath `
        -RepoDir $repoPath `
        -Tickers $ShardTickers `
        -PollSeconds 10 `
        -TimeoutMinutes 60 | Out-Null

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

function Start-FamilyExpansionShardJob {
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
    Write-Log "Queueing $tournamentLabel shard job $ShardIndex/$ShardCount for $($ShardTickers -join ', ')"

    $job = Start-Job -ScriptBlock {
        param(
            [string]$LauncherPath,
            [string]$PromotionPath,
            [string]$ReadyBasePath,
            [string]$RepoPath,
            [string]$ShardResearchPath,
            [string[]]$ShardTickers,
            [string]$StrategySet,
            [string]$SelectionProfile,
            [string]$FamilyInclude,
            [string]$FamilyExclude,
            [string]$PromotionMode,
            [int]$ShardIndex,
            [int]$ShardCount
        )

        $ErrorActionPreference = "Stop"

        function Acquire-PromotionLock {
            param([string]$LockPath)
            while ($true) {
                try {
                    New-Item -ItemType Directory -Path $LockPath -ErrorAction Stop | Out-Null
                    return
                }
                catch {
                    Start-Sleep -Seconds 5
                }
            }
        }

        $result = [ordered]@{
            shard_index = $ShardIndex
            tickers = $ShardTickers
            research_dir = $ShardResearchPath
            phase = "failed"
            stage = "research"
            exit_code = 1
        }

        $launchArgs = @(
            $LauncherPath,
            "--tickers", ($ShardTickers -join ","),
            "--ready-base-dir", $ReadyBasePath,
            "--research-dir", $ShardResearchPath,
            "--strategy-set", $StrategySet,
            "--selection-profile", $SelectionProfile
        )
        if (-not [string]::IsNullOrWhiteSpace($FamilyInclude)) {
            $launchArgs += @("--family-include", $FamilyInclude)
        }
        if (-not [string]::IsNullOrWhiteSpace($FamilyExclude)) {
            $launchArgs += @("--family-exclude", $FamilyExclude)
        }
        & python @launchArgs | Out-Null

        if ($LASTEXITCODE -ne 0) {
            $result.exit_code = $LASTEXITCODE
            return [pscustomobject]$result
        }

        if ($PromotionMode -eq "none") {
            $result.phase = "completed"
            $result.stage = "research_only"
            $result.exit_code = 0
            return [pscustomobject]$result
        }

        $lockPath = Join-Path $RepoPath ".codex_manifest_promotion_lock"
        Acquire-PromotionLock -LockPath $lockPath
        try {
            & powershell -ExecutionPolicy Bypass -File $PromotionPath `
                -ResearchDir $ShardResearchPath `
                -RepoDir $RepoPath `
                -Tickers $ShardTickers `
                -PollSeconds 10 `
                -TimeoutMinutes 60 | Out-Null
            if ($LASTEXITCODE -ne 0) {
                $result.stage = "promotion"
                $result.exit_code = $LASTEXITCODE
                return [pscustomobject]$result
            }
        }
        finally {
            if (Test-Path $lockPath) {
                Remove-Item -Recurse -Force $lockPath
            }
        }

        $result.phase = "completed"
        $result.stage = "completed"
        $result.exit_code = 0
        return [pscustomobject]$result
    } -ArgumentList @(
        $launcherPath,
        $promotionPath,
        $readyBasePath,
        $repoPath,
        $shardResearchPath,
        $ShardTickers,
        $StrategySet,
        $SelectionProfile,
        $FamilyInclude,
        $FamilyExclude,
        $PromotionMode,
        $ShardIndex,
        $ShardCount
    )

    return [pscustomobject]@{
        job = $job
        shard_index = $ShardIndex
        tickers = $ShardTickers
        research_dir = $shardResearchPath
    }
}

Write-Log "Waiting for upstream status file $waitStatusFile"
Write-Status -Phase "waiting" -Message "Waiting for the upstream tournament flow to complete."
Invoke-RunRegistryReport

while ($true) {
    if ($deadline -ne $null -and (Get-Date) -ge $deadline) {
        break
    }
    $phase = Get-WaitPhase
    if ($phase -eq "completed") {
        Write-Log "Upstream status file reports completed."
        break
    }
    if ($phase -in @("failed", "blocked")) {
        Write-Log "Upstream status file reports phase '$phase'. Aborting queued $tournamentLabel run."
        Write-Status -Phase "failed" -Message "Upstream tournament failed before this queued $tournamentLabel batch could start."
        Invoke-RunRegistryReport
        exit 2
    }
    Start-Sleep -Seconds $PollSeconds
}

if ((Get-WaitPhase) -ne "completed") {
    Write-Log "Timed out waiting for upstream completion."
    Write-Status -Phase "failed" -Message "Timed out waiting for the upstream tournament to complete."
    Invoke-RunRegistryReport
    exit 3
}

$shards = Build-Shards
$shardCount = $shards.Count
$allShardResults = @()

Write-Log "Launching queued $tournamentLabel tournament for $($Tickers -join ', ') in $shardCount shard(s)."
Write-Status -Phase "running_family_expansion" -Message "Launching queued $tournamentLabel tournament." -Shards $allShardResults
Invoke-RunRegistryReport

if ($MaxParallelShards -le 1 -or $shardCount -le 1) {
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
            -Message "Processed $($shardIndex + 1) of $shardCount $tournamentLabel shard(s)." `
            -Shards $allShardResults `
            -SuccessfulTickers $successfulTickers `
            -FailedTickers $failedTickers
        Invoke-RunRegistryReport
    }
}
else {
    $activeJobs = @()
    $nextShardIndex = 0

    while ($nextShardIndex -lt $shardCount -or $activeJobs.Count -gt 0) {
        while ($nextShardIndex -lt $shardCount -and $activeJobs.Count -lt $MaxParallelShards) {
            $activeJobs += Start-FamilyExpansionShardJob `
                -ShardTickers $shards[$nextShardIndex] `
                -ShardIndex ($nextShardIndex + 1) `
                -ShardCount $shardCount
            $nextShardIndex += 1
        }

        $jobsToWait = @($activeJobs | ForEach-Object { $_.job })
        if (-not $jobsToWait) {
            break
        }
        Wait-Job -Job $jobsToWait -Any -Timeout $PollSeconds | Out-Null

        $stillActive = @()
        foreach ($entry in $activeJobs) {
            if ($entry.job.State -in @("Completed", "Failed", "Stopped")) {
                $result = Receive-Job -Job $entry.job -Wait -AutoRemoveJob
                if ($result -is [System.Array]) {
                    $result = $result[-1]
                }
                if ($null -eq $result) {
                    $result = [pscustomobject]@{
                        shard_index = $entry.shard_index
                        tickers = $entry.tickers
                        research_dir = $entry.research_dir
                        phase = "failed"
                        stage = "unknown"
                        exit_code = 99
                    }
                }
                $allShardResults += $result
                if ($result.phase -eq "completed") {
                    Write-Log "Parallel shard $($result.shard_index)/$shardCount completed successfully."
                }
                else {
                    Write-Log "Parallel shard $($result.shard_index)/$shardCount failed during $($result.stage) with exit code $($result.exit_code)."
                }
            }
            else {
                $stillActive += $entry
            }
        }
        $activeJobs = $stillActive

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
            -Message "Processed $($allShardResults.Count) of $shardCount $tournamentLabel shard(s)." `
            -Shards $allShardResults `
            -SuccessfulTickers $successfulTickers `
            -FailedTickers $failedTickers
        Invoke-RunRegistryReport
    }
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
    Write-Log "All queued $tournamentLabel shards failed."
    Write-Status `
        -Phase "failed" `
        -Message "All queued $tournamentLabel shards failed." `
        -Shards $allShardResults `
        -SuccessfulTickers $successfulTickers `
        -FailedTickers $failedTickers
    Invoke-RunRegistryReport
    exit 4
}

$message =
    if ($failedShards.Count -gt 0) {
        if ($PromotionMode -eq "none") {
            "Queued $tournamentLabel shards completed with partial failures. Promotion was skipped for this exploratory run."
        }
        else {
            "Queued $tournamentLabel shards completed with partial failures, and successful winners were promoted to GitHub."
        }
    }
    else {
        if ($PromotionMode -eq "none") {
            "Queued $tournamentLabel run completed. Promotion was skipped for this exploratory run."
        }
        else {
            "Queued $tournamentLabel run completed and winners were promoted to GitHub."
        }
    }

Write-Log $message
Write-Status `
    -Phase "completed" `
    -Message $message `
    -Shards $allShardResults `
    -SuccessfulTickers $successfulTickers `
    -FailedTickers $failedTickers
Invoke-RunRegistryReport
exit 0
