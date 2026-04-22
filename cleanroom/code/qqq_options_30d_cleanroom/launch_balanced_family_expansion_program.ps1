param(
    [string]$ReadyBaseDir = "C:\Users\rabisaab\OneDrive - First American Corporation\qqq_options_30d_cleanroom\output\backtester_ready",
    [string]$SecondaryOutputDir = "",
    [string]$RegistryPath = "",
    [string]$ProgramRoot = "",
    [string]$PythonExe = "python",
    [switch]$Execute,
    [switch]$BootstrapReadyUniverse = $true,
    [ValidateSet("full_ready", "coverage_ranked")]
    [string]$DiscoverySource = "coverage_ranked",
    [string]$CoveragePlannerPath = "",
    [string]$CoverageReportDir = "",
    [int]$TopPerLane = 8,
    [int]$MaxPerPhase2Lane = 12,
    [double]$MinReturnPct = 0.0,
    [double]$MaxDrawdownPct = 25.0,
    [double]$MaxAvgFrictionPct = 95.0,
    [double]$MaxCheapSharePct = 85.0,
    [int]$MinTradeCount = 20,
    [int]$PollSeconds = 30,
    [string]$BenchmarkCoreTickers = "qqq,spy,iwm,nvda,tsla",
    [int]$BenchmarkPerLaneCount = 1,
    [int]$BenchmarkMaxTickerCount = 10
)

$ErrorActionPreference = "Stop"

$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$runnerPath = Join-Path $scriptRoot "run_core_strategy_expansion_overnight.py"
$defaultCoveragePlannerPath = Join-Path $scriptRoot "build_ticker_family_coverage.py"
$runRegistryReporterPath = Join-Path $scriptRoot "build_run_registry_report.py"
$defaultOutputRoot = Join-Path $scriptRoot "output"
$defaultRegistryPath = Join-Path $defaultOutputRoot "run_registry.jsonl"

function Write-JsonFile {
    param(
        [string]$Path,
        [object]$Payload
    )

    $directory = Split-Path -Parent $Path
    if (-not [string]::IsNullOrWhiteSpace($directory)) {
        New-Item -ItemType Directory -Force -Path $directory | Out-Null
    }
    $Payload | ConvertTo-Json -Depth 10 | Set-Content -Path $Path
}

function Invoke-RunRegistryReport {
    param(
        [string]$ReportDir,
        [string[]]$ManifestRoots
    )

    if (-not (Test-Path $runRegistryReporterPath)) {
        return
    }

    $reportArgs = @(
        $runRegistryReporterPath,
        "--output-root", $defaultOutputRoot,
        "--registry-path", $defaultRegistryPath,
        "--report-dir", $ReportDir
    )

    $uniqueRoots = New-Object System.Collections.Generic.HashSet[string]
    foreach ($root in @($ManifestRoots)) {
        if (-not [string]::IsNullOrWhiteSpace($root) -and (Test-Path $root)) {
            [void]$uniqueRoots.Add([System.IO.Path]::GetFullPath($root))
        }
    }

    foreach ($root in $uniqueRoots) {
        $reportArgs += @("--manifest-root", $root)
    }

    & $PythonExe @reportArgs | Out-Null
}

function Invoke-PythonStep {
    param(
        [string]$ScriptPath,
        [object[]]$Arguments,
        [string]$FailureMessage
    )

    & $PythonExe $ScriptPath @Arguments | Out-Null
    if ($LASTEXITCODE -ne 0) {
        throw $FailureMessage
    }
}

function Convert-ArgumentListToCommandLine {
    param([object[]]$Arguments)

    $tokens = foreach ($argument in @($Arguments)) {
        $text = [string]$argument
        if ($text.Length -eq 0) {
            '""'
            continue
        }
        if ($text -match '[\s"]') {
            $escaped = $text -replace '(\\*)"', '$1$1\"'
            $escaped = $escaped -replace '(\\+)$', '$1$1'
            '"' + $escaped + '"'
        }
        else {
            $text
        }
    }

    return ($tokens -join ' ')
}

function Test-TickerReady {
    param(
        [string]$Ticker
    )

    $tickerLower = $Ticker.Trim().ToLower()
    if ([string]::IsNullOrWhiteSpace($tickerLower)) {
        return $false
    }

    $tickerDir = Join-Path $ReadyBaseDir $tickerLower
    if (Test-Path $tickerDir) {
        return $true
    }

    $widePath = Join-Path $tickerDir ("{0}_365d_option_1min_wide_backtest.parquet" -f $tickerLower)
    return (Test-Path $widePath)
}

function Normalize-TickerList {
    param(
        [object[]]$Values
    )

    $tickers = New-Object System.Collections.Generic.List[string]
    foreach ($value in @($Values)) {
        if ([string]::IsNullOrWhiteSpace([string]$value)) {
            continue
        }
        foreach ($token in ([string]$value -split ",")) {
            $clean = $token.Trim().ToLower()
            if (-not [string]::IsNullOrWhiteSpace($clean)) {
                $tickers.Add($clean)
            }
        }
    }
    return @($tickers)
}

function Select-BalancedBenchmarkTickers {
    param(
        [object]$CoveragePlan
    )

    $selected = New-Object System.Collections.Generic.List[string]
    $selectedReasons = @()
    $selectedSet = New-Object System.Collections.Generic.HashSet[string]
    $missingCore = New-Object System.Collections.Generic.List[string]

    foreach ($ticker in (Normalize-TickerList -Values @($BenchmarkCoreTickers))) {
        if ($selected.Count -ge $BenchmarkMaxTickerCount) {
            break
        }
        if (-not (Test-TickerReady -Ticker $ticker)) {
            $missingCore.Add($ticker.ToUpper())
            continue
        }
        if ($selectedSet.Add($ticker)) {
            $selected.Add($ticker)
            $selectedReasons += [ordered]@{
                ticker = $ticker.ToUpper()
                source = "core_benchmark"
                lane_id = ""
                gap_score = $null
            }
        }
    }

    $laneTemplates =
        if ($null -ne $CoveragePlan -and $CoveragePlan.PSObject.Properties.Name -contains "lane_templates") {
            @($CoveragePlan.lane_templates)
        }
        else {
            @()
        }

    foreach ($lane in $laneTemplates) {
        if ($selected.Count -ge $BenchmarkMaxTickerCount) {
            break
        }
        $laneId = [string]$lane["lane_id"]
        $readyRows = @($lane["ready_discovery"])
        $addedForLane = 0
        foreach ($row in $readyRows) {
            if ($selected.Count -ge $BenchmarkMaxTickerCount -or $addedForLane -ge $BenchmarkPerLaneCount) {
                break
            }
            $ticker = [string]$row["ticker"]
            $tickerLower = $ticker.Trim().ToLower()
            if ([string]::IsNullOrWhiteSpace($tickerLower) -or -not (Test-TickerReady -Ticker $tickerLower)) {
                continue
            }
            if ($selectedSet.Add($tickerLower)) {
                $selected.Add($tickerLower)
                $selectedReasons += [ordered]@{
                    ticker = $tickerLower.ToUpper()
                    source = "coverage_ranked_ready"
                    lane_id = $laneId
                    gap_score = $row["gap_score"]
                }
                $addedForLane += 1
            }
        }
    }

    return [ordered]@{
        selected_tickers = @($selected | Select-Object -Unique)
        selected_reasons = $selectedReasons
        missing_core_tickers = @($missingCore)
    }
}

function Write-ProgramStatus {
    param(
        [string]$Phase,
        [string]$Message,
        [hashtable]$Extra = @{}
    )

    $payload = [ordered]@{
        phase = $Phase
        message = $Message
        updated_at = (Get-Date).ToString("o")
        program_root = $programRootPath
        benchmark_plan_json = $benchmarkPlanPath
        coverage_plan_json = $nextWavePlanPath
        phase2_status_json = $phase2StatusPath
        run_registry_report_dir = $runRegistryReportDir
    }

    foreach ($entry in $Extra.GetEnumerator()) {
        $payload[$entry.Key] = $entry.Value
    }

    Write-JsonFile -Path $programStatusPath -Payload $payload
}

function Write-Phase2Status {
    param(
        [string]$Phase,
        [string]$Message,
        [object[]]$LaneProcesses = @()
    )

    $laneRows = @()
    foreach ($laneProcess in @($LaneProcesses)) {
        $proc = $laneProcess.process
        $hasExited = $proc.HasExited
        $laneRows += [ordered]@{
            lane_id = $laneProcess.lane_id
            description = $laneProcess.description
            tickers = @($laneProcess.tickers)
            research_dir = $laneProcess.research_dir
            strategy_set = $laneProcess.strategy_set
            selection_profile = $laneProcess.selection_profile
            pid = $proc.Id
            has_exited = $hasExited
            exit_code = if ($hasExited) { [int]$proc.ExitCode } else { $null }
            stdout_path = $laneProcess.stdout_path
            stderr_path = $laneProcess.stderr_path
        }
    }

    $payload = [ordered]@{
        phase = $Phase
        message = $Message
        updated_at = (Get-Date).ToString("o")
        benchmark_plan_json = $benchmarkPlanPath
        coverage_plan_json = $nextWavePlanPath
        lanes = $laneRows
    }

    Write-JsonFile -Path $phase2StatusPath -Payload $payload
}

function Start-BenchmarkProcess {
    param(
        [string[]]$Tickers
    )

    $stdoutPath = Join-Path $logsRoot "balanced_family_expansion_stdout.log"
    $stderrPath = Join-Path $logsRoot "balanced_family_expansion_stderr.log"
    $args = @(
        $runnerPath,
        "--tickers", ($Tickers -join ","),
        "--ready-base-dir", $ReadyBaseDir,
        "--research-dir", $researchDir,
        "--strategy-set", "family_expansion",
        "--selection-profile", "balanced"
    )

    $argumentLine = Convert-ArgumentListToCommandLine -Arguments $args
    $process = Start-Process -FilePath $PythonExe `
        -ArgumentList $argumentLine `
        -WorkingDirectory $scriptRoot `
        -RedirectStandardOutput $stdoutPath `
        -RedirectStandardError $stderrPath `
        -PassThru

    return [pscustomobject]@{
        lane_id = "01_balanced_family_expansion"
        description = "Balanced cross-regime family-expansion benchmark."
        research_dir = $researchDir
        strategy_set = "family_expansion"
        selection_profile = "balanced"
        tickers = @($Tickers)
        stdout_path = $stdoutPath
        stderr_path = $stderrPath
        process = $process
    }
}

if ([string]::IsNullOrWhiteSpace($SecondaryOutputDir)) {
    $SecondaryOutputDir = $defaultOutputRoot
}
else {
    $SecondaryOutputDir = [System.IO.Path]::GetFullPath($SecondaryOutputDir)
}

if ([string]::IsNullOrWhiteSpace($RegistryPath)) {
    $RegistryPath = $defaultRegistryPath
}
else {
    $RegistryPath = [System.IO.Path]::GetFullPath($RegistryPath)
}

if ([string]::IsNullOrWhiteSpace($CoveragePlannerPath)) {
    $CoveragePlannerPath = $defaultCoveragePlannerPath
}
else {
    $CoveragePlannerPath = [System.IO.Path]::GetFullPath($CoveragePlannerPath)
}

if ([string]::IsNullOrWhiteSpace($CoverageReportDir)) {
    $CoverageReportDir = Join-Path $ProgramRoot "coverage_refresh"
}

if ([string]::IsNullOrWhiteSpace($ProgramRoot)) {
    $ProgramRoot = Join-Path $defaultOutputRoot ("balanced_family_expansion_program_" + (Get-Date -Format "yyyyMMdd_HHmmss"))
}

$ReadyBaseDir = [System.IO.Path]::GetFullPath($ReadyBaseDir)
$ProgramRoot = [System.IO.Path]::GetFullPath($ProgramRoot)
$CoverageReportDir = [System.IO.Path]::GetFullPath($CoverageReportDir)

$programRootPath = $ProgramRoot
$phase2Root = Join-Path $programRootPath "phase2"
$researchDir = Join-Path $phase2Root "01_balanced_family_expansion"
$logsRoot = Join-Path $programRootPath "logs"
$runRegistryReportDir = Join-Path $programRootPath "run_registry_report"
$programManifestPath = Join-Path $programRootPath "program_manifest.json"
$programStatusPath = Join-Path $programRootPath "program_status.json"
$phase2StatusPath = Join-Path $programRootPath "phase2_status.json"
$benchmarkPlanPath = Join-Path $programRootPath "balanced_benchmark_plan.json"
$benchmarkPlanMarkdownPath = Join-Path $programRootPath "balanced_benchmark_plan.md"
$nextWavePlanPath = Join-Path $CoverageReportDir "next_wave_plan.json"

New-Item -ItemType Directory -Force -Path $programRootPath | Out-Null
New-Item -ItemType Directory -Force -Path $phase2Root | Out-Null
New-Item -ItemType Directory -Force -Path $logsRoot | Out-Null
New-Item -ItemType Directory -Force -Path $runRegistryReportDir | Out-Null
New-Item -ItemType Directory -Force -Path $CoverageReportDir | Out-Null

trap {
    $failureMessage =
        if ($_.Exception -and -not [string]::IsNullOrWhiteSpace([string]$_.Exception.Message)) {
            [string]$_.Exception.Message
        }
        else {
            [string]$_
        }

    Write-ProgramStatus -Phase "failed" -Message $failureMessage
    if (Test-Path $phase2StatusPath) {
        Write-Phase2Status -Phase "failed" -Message $failureMessage
    }
    throw $failureMessage
}

$programManifest = [ordered]@{
    created_at = (Get-Date).ToString("o")
    execute = [bool]$Execute
    program_root = $programRootPath
    research_dir = $researchDir
    ready_base_dir = $ReadyBaseDir
    secondary_output_dir = $SecondaryOutputDir
    registry_path = $RegistryPath
    coverage_planner_path = $CoveragePlannerPath
    coverage_report_dir = $CoverageReportDir
    strategy_set = "family_expansion"
    selection_profile = "balanced"
    discovery_source = $DiscoverySource
    bootstrap_ready_universe = [bool]$BootstrapReadyUniverse
    benchmark_core_tickers = @(Normalize-TickerList -Values @($BenchmarkCoreTickers) | ForEach-Object { $_.ToUpper() })
    benchmark_per_lane_count = $BenchmarkPerLaneCount
    benchmark_max_ticker_count = $BenchmarkMaxTickerCount
    filters = [ordered]@{
        top_per_lane = $TopPerLane
        max_per_phase2_lane = $MaxPerPhase2Lane
        min_return_pct = $MinReturnPct
        max_drawdown_pct = $MaxDrawdownPct
        max_avg_friction_pct = $MaxAvgFrictionPct
        max_cheap_share_pct = $MaxCheapSharePct
        min_trade_count = $MinTradeCount
    }
}
Write-JsonFile -Path $programManifestPath -Payload $programManifest

Write-ProgramStatus -Phase "refreshing_coverage" -Message "Refreshing ticker-family coverage for the balanced family-expansion benchmark."

$coverageArgs = @(
    "--output-root", $defaultOutputRoot,
    "--ready-base-dir", $ReadyBaseDir,
    "--secondary-output-dir", $SecondaryOutputDir,
    "--registry-path", $RegistryPath,
    "--report-dir", $CoverageReportDir,
    "--top-ready-per-lane", $TopPerLane
)
Invoke-PythonStep -ScriptPath $CoveragePlannerPath -Arguments $coverageArgs -FailureMessage "Failed to refresh ticker-family coverage for balanced benchmark."

if (-not (Test-Path $nextWavePlanPath)) {
    throw "Coverage planner did not create next_wave_plan.json at $nextWavePlanPath"
}

$coveragePlan = Get-Content -Path $nextWavePlanPath -Raw | ConvertFrom-Json
$benchmarkSelection = Select-BalancedBenchmarkTickers -CoveragePlan $coveragePlan
$selectedTickers = @($benchmarkSelection.selected_tickers)

if ($selectedTickers.Count -lt 3) {
    throw "Balanced family-expansion benchmark selected too few ready tickers to run safely."
}

$benchmarkPlan = [ordered]@{
    generated_at = (Get-Date).ToString("o")
    strategy_set = "family_expansion"
    selection_profile = "balanced"
    discovery_source = $DiscoverySource
    benchmark_core_tickers = $programManifest.benchmark_core_tickers
    selected_tickers = @($selectedTickers | ForEach-Object { $_.ToUpper() })
    selected_count = $selectedTickers.Count
    selected_reasons = @($benchmarkSelection.selected_reasons)
    missing_core_tickers = @($benchmarkSelection.missing_core_tickers)
    coverage_plan_json = $nextWavePlanPath
    research_dir = $researchDir
}
Write-JsonFile -Path $benchmarkPlanPath -Payload $benchmarkPlan

$selectedTickerMarkdown =
    if ($benchmarkPlan.selected_tickers.Count -gt 0) {
        ($benchmarkPlan.selected_tickers | ForEach-Object { ('`' + $_ + '`') }) -join ", "
    }
    else {
        "none"
    }
$missingCoreMarkdown =
    if ($benchmarkPlan.missing_core_tickers.Count -gt 0) {
        ($benchmarkPlan.missing_core_tickers | ForEach-Object { ('`' + $_ + '`') }) -join ", "
    }
    else {
        "none"
    }

$planLines = @(
    "# Balanced Family Expansion Benchmark Plan",
    "",
    '- Strategy set: `family_expansion`',
    '- Selection profile: `balanced`',
    "- Selected tickers: $selectedTickerMarkdown",
    "- Missing core tickers: $missingCoreMarkdown",
    "",
    "## Selection Reasons",
    ""
)
foreach ($row in @($benchmarkPlan.selected_reasons)) {
    $gapScore =
        if ($null -ne $row.gap_score -and -not [string]::IsNullOrWhiteSpace([string]$row.gap_score)) {
            [string]$row.gap_score
        }
        else {
            "n/a"
        }
    $planLines += ('- `' + [string]$row.ticker + '` from `' + [string]$row.source + '` lane `' + [string]$row.lane_id + '` gap `' + $gapScore + '`')
}
$planLines += ""
$planLines | Set-Content -Path $benchmarkPlanMarkdownPath

$programManifest.selected_tickers = $benchmarkPlan.selected_tickers
$programManifest.benchmark_plan_json = $benchmarkPlanPath
Write-JsonFile -Path $programManifestPath -Payload $programManifest

if (-not $Execute) {
    Write-Phase2Status -Phase "planned" -Message "Balanced family-expansion benchmark planned successfully."
    Write-ProgramStatus -Phase "planned" -Message "Balanced family-expansion benchmark planned successfully." -Extra @{
        selected_tickers = $benchmarkPlan.selected_tickers
        benchmark_plan_markdown = $benchmarkPlanMarkdownPath
    }
    Invoke-RunRegistryReport -ReportDir $runRegistryReportDir -ManifestRoots @($programRootPath, $researchDir)
    exit 0
}

Write-ProgramStatus -Phase "running_phase2" -Message "Launching balanced family-expansion benchmark."
$laneProcess = Start-BenchmarkProcess -Tickers $selectedTickers
Write-Phase2Status -Phase "running_phase2" -Message "Balanced family-expansion benchmark is running." -LaneProcesses @($laneProcess)

while (-not $laneProcess.process.HasExited) {
    Start-Sleep -Seconds ([Math]::Max(5, $PollSeconds))
    Write-Phase2Status -Phase "running_phase2" -Message "Balanced family-expansion benchmark is running." -LaneProcesses @($laneProcess)
}

Write-Phase2Status -Phase "complete" -Message "Balanced family-expansion benchmark finished." -LaneProcesses @($laneProcess)

if ($laneProcess.process.ExitCode -ne 0) {
    Write-ProgramStatus -Phase "failed" -Message "Balanced family-expansion benchmark failed." -Extra @{
        exit_code = [int]$laneProcess.process.ExitCode
        stdout_path = $laneProcess.stdout_path
        stderr_path = $laneProcess.stderr_path
    }
    throw "Balanced family-expansion benchmark failed with exit code $($laneProcess.process.ExitCode)."
}

$masterSummaryPath = Join-Path $researchDir "master_summary.json"
if (-not (Test-Path $masterSummaryPath)) {
    Write-ProgramStatus -Phase "failed" -Message "Balanced family-expansion benchmark exited without master_summary.json." -Extra @{
        stdout_path = $laneProcess.stdout_path
        stderr_path = $laneProcess.stderr_path
    }
    throw "Balanced family-expansion benchmark exited without master_summary.json."
}

Invoke-RunRegistryReport -ReportDir $runRegistryReportDir -ManifestRoots @($programRootPath, $researchDir)

Write-ProgramStatus -Phase "complete" -Message "Balanced family-expansion benchmark completed successfully." -Extra @{
    selected_tickers = $benchmarkPlan.selected_tickers
    master_summary_path = $masterSummaryPath
    benchmark_plan_markdown = $benchmarkPlanMarkdownPath
}

exit 0
