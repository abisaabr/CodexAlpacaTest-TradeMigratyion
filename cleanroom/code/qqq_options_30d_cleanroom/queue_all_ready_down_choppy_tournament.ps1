param(
    [string]$WaitStatusPath = "C:\Users\rabisaab\Downloads\qqq_options_30d_cleanroom\output\tournament_conveyor_20260420_summary_sharded\summary_queue_status.json",
    [string]$ReadyBaseDir = "C:\Users\rabisaab\OneDrive - First American Corporation\qqq_options_30d_cleanroom\output\backtester_ready",
    [string]$RepoDir = "C:\Users\rabisaab\OneDrive\CodexAlpaca\downloads_remaining_20260417\folders\codexalpaca_repo",
    [string]$ResearchDir = "",
    [string[]]$IncludeTickers = @(),
    [string[]]$ExcludeTickers = @(),
    [int]$ShardSize = 1,
    [int]$MaxParallelShards = 3,
    [int]$PollSeconds = 60,
    [int]$TimeoutMinutes = 0
)

$ErrorActionPreference = "Stop"

$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$queueScriptPath = Join-Path $scriptRoot "queue_ready_family_expansion_after_status.ps1"
$readyBasePath = [System.IO.Path]::GetFullPath($ReadyBaseDir)
$waitStatusFile = [System.IO.Path]::GetFullPath($WaitStatusPath)
$repoPath = [System.IO.Path]::GetFullPath($RepoDir)

if ([string]::IsNullOrWhiteSpace($ResearchDir)) {
    $defaultName = "candidate_batch_research_{0}_downchop_allready_sharded" -f (Get-Date -Format "yyyyMMdd")
    $researchPath = Join-Path $scriptRoot ("output\" + $defaultName)
}
else {
    $researchPath = [System.IO.Path]::GetFullPath($ResearchDir)
}

if (-not (Test-Path $readyBasePath)) {
    throw "ready base directory not found: $readyBasePath"
}

$availableTickers = @(
    Get-ChildItem $readyBasePath -Directory |
        Where-Object { Test-Path (Join-Path $_.FullName "manifest.json") } |
        ForEach-Object { $_.Name.Trim().ToLower() } |
        Sort-Object -Unique
)

if ($IncludeTickers.Count -gt 0) {
    $normalizedInclude = @(
        $IncludeTickers |
            ForEach-Object { $_ -split "," } |
            ForEach-Object { $_.Trim().ToLower() } |
            Where-Object { -not [string]::IsNullOrWhiteSpace($_) } |
            Sort-Object -Unique
    )
    $availableTickers = @($availableTickers | Where-Object { $_ -in $normalizedInclude })
}

if ($ExcludeTickers.Count -gt 0) {
    $normalizedExclude = @(
        $ExcludeTickers |
            ForEach-Object { $_ -split "," } |
            ForEach-Object { $_.Trim().ToLower() } |
            Where-Object { -not [string]::IsNullOrWhiteSpace($_) } |
            Sort-Object -Unique
    )
    $availableTickers = @($availableTickers | Where-Object { $_ -notin $normalizedExclude })
}

if (-not $availableTickers) {
    throw "no ready tickers matched the requested include/exclude filters"
}

New-Item -ItemType Directory -Force -Path $researchPath | Out-Null

$launchMetadata = [ordered]@{
    created_at = (Get-Date).ToString("o")
    wait_status_path = $waitStatusFile
    ready_base_dir = $readyBasePath
    repo_dir = $repoPath
    research_dir = $researchPath
    strategy_set = "down_choppy_only"
    selection_profile = "down_choppy_focus"
    promotion_mode = "none"
    shard_size = $ShardSize
    max_parallel_shards = $MaxParallelShards
    tickers = $availableTickers
}
$launchMetadata | ConvertTo-Json -Depth 6 | Set-Content -Path (Join-Path $researchPath "launch_request.json")

& powershell -NoProfile -ExecutionPolicy Bypass -File $queueScriptPath `
    -WaitStatusPath $waitStatusFile `
    -ResearchDir $researchPath `
    -RepoDir $repoPath `
    -ReadyBaseDir $readyBasePath `
    -Tickers ($availableTickers -join ",") `
    -StrategySet "down_choppy_only" `
    -SelectionProfile "down_choppy_focus" `
    -PromotionMode "none" `
    -ShardSize $ShardSize `
    -MaxParallelShards $MaxParallelShards `
    -PollSeconds $PollSeconds `
    -TimeoutMinutes $TimeoutMinutes

exit $LASTEXITCODE

