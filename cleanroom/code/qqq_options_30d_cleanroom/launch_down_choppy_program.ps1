param(
    [string]$ReadyBaseDir = "C:\Users\rabisaab\OneDrive - First American Corporation\qqq_options_30d_cleanroom\output\backtester_ready",
    [string]$ProgramRoot = "",
    [string]$PythonExe = "python",
    [switch]$Execute,
    [switch]$RunPhase2 = $true,
    [switch]$BootstrapReadyUniverse = $true,
    [ValidateSet("full_ready", "coverage_ranked")]
    [string]$DiscoverySource = "full_ready",
    [string]$CoveragePlannerPath = "",
    [string]$CoverageReportDir = "",
    [int]$TopPerLane = 8,
    [int]$MaxPerPhase2Lane = 12,
    [double]$MinReturnPct = 0.0,
    [double]$MaxDrawdownPct = 25.0,
    [double]$MaxAvgFrictionPct = 95.0,
    [double]$MaxCheapSharePct = 85.0,
    [int]$MinTradeCount = 20,
    [int]$PollSeconds = 30
)

$ErrorActionPreference = "Stop"

$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$familyWaveLauncherPath = Join-Path $scriptRoot "launch_down_choppy_family_wave.ps1"
$shortlistBuilderPath = Join-Path $scriptRoot "build_family_wave_shortlist.py"
$phase2PackBuilderPath = Join-Path $scriptRoot "build_phase2_agent_wave_pack.py"
$agentWaveLauncherPath = Join-Path $scriptRoot "launch_agent_wave.ps1"
$defaultCoveragePlannerPath = Join-Path $scriptRoot "build_ticker_family_coverage.py"
$materializerPath = Join-Path $scriptRoot "materialize_backtester_ready.py"
$runnerPath = Join-Path $scriptRoot "run_core_strategy_expansion_overnight.py"

function Write-JsonFile {
    param(
        [string]$Path,
        [object]$Payload
    )
    $directory = Split-Path -Parent $Path
    if (-not [string]::IsNullOrWhiteSpace($directory)) {
        New-Item -ItemType Directory -Force -Path $directory | Out-Null
    }
    $Payload | ConvertTo-Json -Depth 8 | Set-Content -Path $Path
}

function Normalize-ExitCode {
    param([System.Diagnostics.Process]$Process)
    try {
        return [int]$Process.ExitCode
    }
    catch {
        return -1
    }
}

function Start-LaneProcess {
    param(
        [pscustomobject]$Lane,
        [string]$Label,
        [string]$LogsRoot
    )

    $laneDir = [System.IO.Path]::GetFullPath([string]$Lane.research_dir)
    New-Item -ItemType Directory -Force -Path $laneDir | Out-Null
    $laneLogsDir = Join-Path $LogsRoot ([string]$Lane.lane_id)
    New-Item -ItemType Directory -Force -Path $laneLogsDir | Out-Null

    $stdoutPath = Join-Path $laneLogsDir "$Label`_stdout.log"
    $stderrPath = Join-Path $laneLogsDir "$Label`_stderr.log"
    $args = @(
        $runnerPath,
        "--tickers", ((@($Lane.tickers) | ForEach-Object { [string]$_ }) -join ","),
        "--ready-base-dir", [System.IO.Path]::GetFullPath($ReadyBaseDir),
        "--research-dir", $laneDir,
        "--strategy-set", [string]$Lane.strategy_set,
        "--selection-profile", [string]$Lane.selection_profile
    )
    if (-not [string]::IsNullOrWhiteSpace([string]$Lane.family_include)) {
        $args += @("--family-include", [string]$Lane.family_include)
    }
    if ($Lane.PSObject.Properties.Name -contains "family_exclude") {
        $familyExclude = [string]$Lane.family_exclude
        if (-not [string]::IsNullOrWhiteSpace($familyExclude)) {
            $args += @("--family-exclude", $familyExclude)
        }
    }

    $process = Start-Process -FilePath $PythonExe `
        -ArgumentList $args `
        -WorkingDirectory $scriptRoot `
        -RedirectStandardOutput $stdoutPath `
        -RedirectStandardError $stderrPath `
        -PassThru

    return [pscustomobject]@{
        lane_id = [string]$Lane.lane_id
        description = [string]$Lane.description
        research_dir = $laneDir
        strategy_set = [string]$Lane.strategy_set
        selection_profile = [string]$Lane.selection_profile
        family_include = [string]$Lane.family_include
        family_exclude =
            if ($Lane.PSObject.Properties.Name -contains "family_exclude") {
                [string]$Lane.family_exclude
            }
            else {
                ""
            }
        tickers = @($Lane.tickers)
        stdout_path = $stdoutPath
        stderr_path = $stderrPath
        process = $process
    }
}

function Wait-LaneProcesses {
    param(
        [object[]]$LaneProcesses,
        [string]$PhaseName,
        [string]$StatusPath
    )

    while ($true) {
        $statusRows = @()
        $allExited = $true
        foreach ($laneProcess in $LaneProcesses) {
            $proc = $laneProcess.process
            if (-not $proc.HasExited) {
                $allExited = $false
            }
            $statusRows += [ordered]@{
                lane_id = $laneProcess.lane_id
                pid = $proc.Id
                has_exited = $proc.HasExited
                exit_code = if ($proc.HasExited) { Normalize-ExitCode -Process $proc } else { $null }
                research_dir = $laneProcess.research_dir
                stdout_path = $laneProcess.stdout_path
                stderr_path = $laneProcess.stderr_path
            }
        }

        Write-JsonFile -Path $StatusPath -Payload ([ordered]@{
            phase = $PhaseName
            execute = [bool]$Execute
            updated_at = (Get-Date).ToString("o")
            lanes = $statusRows
        })

        if ($allExited) {
            break
        }

        Start-Sleep -Seconds $PollSeconds
    }

    $results = @()
    foreach ($laneProcess in $LaneProcesses) {
        $proc = $laneProcess.process
        $proc.WaitForExit()
        $masterSummaryPath = Join-Path $laneProcess.research_dir "master_summary.json"
        $results += [ordered]@{
            lane_id = $laneProcess.lane_id
            description = $laneProcess.description
            pid = $proc.Id
            exit_code = Normalize-ExitCode -Process $proc
            has_master_summary = Test-Path $masterSummaryPath
            master_summary_path = $masterSummaryPath
            research_dir = $laneProcess.research_dir
            stdout_path = $laneProcess.stdout_path
            stderr_path = $laneProcess.stderr_path
        }
    }
    return $results
}

function Convert-CoveragePlanToWavePlan {
    param(
        [string]$NextWavePlanPath,
        [string]$DiscoveryRootPath
    )

    $payload = Get-Content -Path $NextWavePlanPath -Raw | ConvertFrom-Json
    $laneTemplates =
        if ($payload.PSObject.Properties.Name -contains "lane_templates") {
            @($payload.lane_templates)
        }
        else {
            @()
        }

    $wavePlan = @()
    foreach ($lane in $laneTemplates) {
        $readyRows =
            if ($lane.PSObject.Properties.Name -contains "ready_discovery") {
                @($lane.ready_discovery)
            }
            else {
                @()
            }
        $tickers = @($readyRows | ForEach-Object { [string]$_.ticker } | Where-Object { -not [string]::IsNullOrWhiteSpace($_) })
        $families = @($lane.families | ForEach-Object { [string]$_ } | Where-Object { -not [string]::IsNullOrWhiteSpace($_) })
        $wavePlan += [ordered]@{
            lane_id = [string]$lane.lane_id
            description = [string]$lane.description
            strategy_set = "down_choppy_only"
            selection_profile = "down_choppy_focus"
            family_include = (($families | ForEach-Object {
                        ($_ -replace '[^A-Za-z0-9]+', '_').Trim('_').ToLower()
                    }) -join ",")
            tickers = $tickers
            research_dir = (Join-Path $DiscoveryRootPath ([string]$lane.lane_id))
            command = ""
        }
    }

    return $wavePlan
}

function Get-CoveragePrepTickers {
    param(
        [string]$NextWavePlanPath
    )

    $payload = Get-Content -Path $NextWavePlanPath -Raw | ConvertFrom-Json
    $laneTemplates =
        if ($payload.PSObject.Properties.Name -contains "lane_templates") {
            @($payload.lane_templates)
        }
        else {
            @()
        }

    $tickers = New-Object System.Collections.Generic.HashSet[string]
    foreach ($lane in $laneTemplates) {
        foreach ($bucket in @("staged_materialization", "registry_download")) {
            $rows =
                if ($lane.PSObject.Properties.Name -contains $bucket) {
                    @($lane.$bucket)
                }
                else {
                    @()
                }
            foreach ($row in $rows) {
                $ticker = [string]$row.ticker
                if (-not [string]::IsNullOrWhiteSpace($ticker)) {
                    [void]$tickers.Add($ticker.ToUpper())
                }
            }
        }
    }

    return @($tickers | Sort-Object)
}

function Invoke-ReadyUniverseBootstrap {
    param(
        [string[]]$Tickers,
        [string]$BootstrapReportDir
    )

    if (-not $Tickers -or @($Tickers).Count -eq 0) {
        return [ordered]@{
            executed = $false
            exit_code = 0
            tickers = @()
            report_dir = $BootstrapReportDir
        }
    }

    & $PythonExe $materializerPath `
        --tickers (@($Tickers) -join ",") `
        --report-dir $BootstrapReportDir `
        --only-missing `
        --update-registry | Out-Null

    return [ordered]@{
        executed = $true
        exit_code = $LASTEXITCODE
        tickers = @($Tickers)
        report_dir = $BootstrapReportDir
    }
}

if ([string]::IsNullOrWhiteSpace($ProgramRoot)) {
    $ProgramRoot = Join-Path $scriptRoot ("output\down_choppy_program_" + (Get-Date -Format "yyyyMMdd_HHmmss"))
}

$programRootPath = [System.IO.Path]::GetFullPath($ProgramRoot)
$discoveryRoot = Join-Path $programRootPath "discovery"
$shortlistRoot = Join-Path $programRootPath "shortlist"
$phase2Root = Join-Path $programRootPath "phase2"
$phase2PackRoot = Join-Path $phase2Root "launch_pack"
$coverageRoot = Join-Path $programRootPath "coverage"
$logsRoot = Join-Path $programRootPath "logs"
$statusPath = Join-Path $programRootPath "program_status.json"
$manifestPath = Join-Path $programRootPath "program_manifest.json"
$phase1StatusPath = Join-Path $programRootPath "phase1_status.json"
$phase2StatusPath = Join-Path $programRootPath "phase2_status.json"

New-Item -ItemType Directory -Force -Path $programRootPath | Out-Null
New-Item -ItemType Directory -Force -Path $discoveryRoot | Out-Null
New-Item -ItemType Directory -Force -Path $shortlistRoot | Out-Null
New-Item -ItemType Directory -Force -Path $phase2Root | Out-Null
New-Item -ItemType Directory -Force -Path $phase2PackRoot | Out-Null
New-Item -ItemType Directory -Force -Path $coverageRoot | Out-Null
New-Item -ItemType Directory -Force -Path $logsRoot | Out-Null

if ([string]::IsNullOrWhiteSpace($CoveragePlannerPath)) {
    $CoveragePlannerPath = $defaultCoveragePlannerPath
}
else {
    $CoveragePlannerPath = [System.IO.Path]::GetFullPath($CoveragePlannerPath)
}

if ([string]::IsNullOrWhiteSpace($CoverageReportDir)) {
    $CoverageReportDir = $coverageRoot
}
else {
    $CoverageReportDir = [System.IO.Path]::GetFullPath($CoverageReportDir)
}

Write-JsonFile -Path $statusPath -Payload ([ordered]@{
    phase = "planning"
    execute = [bool]$Execute
    updated_at = (Get-Date).ToString("o")
})

if ($DiscoverySource -eq "coverage_ranked") {
    & $PythonExe $CoveragePlannerPath --report-dir $CoverageReportDir | Out-Null
    if ($LASTEXITCODE -ne 0) {
        throw "failed to generate coverage-ranked discovery plan"
    }

    $nextWavePlanPath = Join-Path $CoverageReportDir "next_wave_plan.json"
    if (-not (Test-Path $nextWavePlanPath)) {
        throw "coverage planner did not create next_wave_plan.json at $nextWavePlanPath"
    }

    $bootstrapCandidates = @(Get-CoveragePrepTickers -NextWavePlanPath $nextWavePlanPath)
    $bootstrapReportDir = Join-Path $CoverageReportDir "bootstrap_materialization"

    if ($Execute -and $BootstrapReadyUniverse -and @($bootstrapCandidates).Count -gt 0) {
        Write-JsonFile -Path $statusPath -Payload ([ordered]@{
            phase = "bootstrap_ready_materialization"
            execute = $true
            updated_at = (Get-Date).ToString("o")
            tickers = $bootstrapCandidates
            bootstrap_report_dir = $bootstrapReportDir
        })

        $bootstrapResult = Invoke-ReadyUniverseBootstrap -Tickers $bootstrapCandidates -BootstrapReportDir $bootstrapReportDir
        if ([int]$bootstrapResult.exit_code -ne 0) {
            throw "failed to bootstrap ready-universe materialization"
        }

        & $PythonExe $CoveragePlannerPath --report-dir $CoverageReportDir | Out-Null
        if ($LASTEXITCODE -ne 0) {
            throw "failed to regenerate coverage-ranked discovery plan after bootstrap"
        }
    }
    else {
        $bootstrapResult = [ordered]@{
            executed = $false
            exit_code = 0
            tickers = $bootstrapCandidates
            report_dir = $bootstrapReportDir
        }
    }

    if (-not (Test-Path $nextWavePlanPath)) {
        throw "coverage planner did not recreate next_wave_plan.json at $nextWavePlanPath"
    }

    $wavePlan = Convert-CoveragePlanToWavePlan -NextWavePlanPath $nextWavePlanPath -DiscoveryRootPath $discoveryRoot
    $wavePlanPath = Join-Path $discoveryRoot "family_wave_plan.json"
    Write-JsonFile -Path $wavePlanPath -Payload $wavePlan
}
else {
    & powershell -NoProfile -ExecutionPolicy Bypass -File $familyWaveLauncherPath `
        -ReadyBaseDir $ReadyBaseDir `
        -ResearchRoot $discoveryRoot `
        -PythonExe $PythonExe | Out-Null

    if ($LASTEXITCODE -ne 0) {
        throw "failed to generate discovery family-wave plan"
    }

    $wavePlanPath = Join-Path $discoveryRoot "family_wave_plan.json"
    if (-not (Test-Path $wavePlanPath)) {
        throw "family wave plan was not created at $wavePlanPath"
    }

    $wavePlan = Get-Content -Path $wavePlanPath -Raw | ConvertFrom-Json
}

$manifest = [ordered]@{
    created_at = (Get-Date).ToString("o")
    execute = [bool]$Execute
    run_phase2 = [bool]$RunPhase2
    bootstrap_ready_universe = [bool]$BootstrapReadyUniverse
    discovery_source = $DiscoverySource
    ready_base_dir = [System.IO.Path]::GetFullPath($ReadyBaseDir)
    discovery_root = $discoveryRoot
    shortlist_root = $shortlistRoot
    phase2_root = $phase2Root
    coverage_report_dir = $CoverageReportDir
    coverage_planner_path = $CoveragePlannerPath
    materializer_path = $materializerPath
    wave_plan_path = $wavePlanPath
    shortlist_builder_path = $shortlistBuilderPath
    runner_path = $runnerPath
    filters = [ordered]@{
        top_per_lane = $TopPerLane
        max_per_phase2_lane = $MaxPerPhase2Lane
        min_return_pct = $MinReturnPct
        max_drawdown_pct = $MaxDrawdownPct
        max_avg_friction_pct = $MaxAvgFrictionPct
        max_cheap_share_pct = $MaxCheapSharePct
        min_trade_count = $MinTradeCount
    }
    discovery_lanes = @($wavePlan)
}
if ($DiscoverySource -eq "coverage_ranked") {
    $manifest.bootstrap = [ordered]@{
        executed = [bool]$bootstrapResult.executed
        exit_code = [int]$bootstrapResult.exit_code
        tickers = @($bootstrapResult.tickers)
        report_dir = [string]$bootstrapResult.report_dir
    }
}
Write-JsonFile -Path $manifestPath -Payload $manifest

if (-not $Execute) {
    Write-JsonFile -Path $statusPath -Payload ([ordered]@{
        phase = "planned"
        execute = $false
        updated_at = (Get-Date).ToString("o")
        wave_plan_path = $wavePlanPath
        manifest_path = $manifestPath
        next_step = "Run this script again with -Execute to launch discovery, shortlist, and phase-2 exhaustive lanes."
    })
    Write-Output ($manifest | ConvertTo-Json -Depth 8)
    exit 0
}

Write-JsonFile -Path $statusPath -Payload ([ordered]@{
    phase = "phase1_discovery_running"
    execute = $true
    updated_at = (Get-Date).ToString("o")
    wave_plan_path = $wavePlanPath
})

$phase1LaneProcesses = @()
foreach ($lane in $wavePlan) {
    $phase1LaneProcesses += Start-LaneProcess -Lane $lane -Label "phase1" -LogsRoot $logsRoot
}

$phase1Results = Wait-LaneProcesses -LaneProcesses $phase1LaneProcesses -PhaseName "phase1_discovery_running" -StatusPath $phase1StatusPath

Write-JsonFile -Path $phase1StatusPath -Payload ([ordered]@{
    phase = "phase1_discovery_complete"
    updated_at = (Get-Date).ToString("o")
    results = $phase1Results
})

Write-JsonFile -Path $statusPath -Payload ([ordered]@{
    phase = "phase1_shortlisting"
    execute = $true
    updated_at = (Get-Date).ToString("o")
    wave_plan_path = $wavePlanPath
})

& $PythonExe $shortlistBuilderPath `
    --wave-plan $wavePlanPath `
    --output-dir $shortlistRoot `
    --runner-path $runnerPath `
    --python-exe $PythonExe `
    --top-per-lane $TopPerLane `
    --max-per-phase2-lane $MaxPerPhase2Lane `
    --min-return-pct $MinReturnPct `
    --max-drawdown-pct $MaxDrawdownPct `
    --max-avg-friction-pct $MaxAvgFrictionPct `
    --max-cheap-share-pct $MaxCheapSharePct `
    --min-trade-count $MinTradeCount

if ($LASTEXITCODE -ne 0) {
    throw "failed to build family-wave shortlist"
}

$phase2PlanPath = Join-Path $shortlistRoot "phase2_plan.json"
if (-not (Test-Path $phase2PlanPath)) {
    throw "phase 2 plan was not created at $phase2PlanPath"
}

& $PythonExe $phase2PackBuilderPath `
    --phase2-plan-json $phase2PlanPath `
    --output-dir $phase2PackRoot `
    --research-root (Join-Path $phase2Root "lanes") `
    --runner-path $runnerPath `
    --ready-base-dir $ReadyBaseDir `
    --python-exe $PythonExe | Out-Null

if ($LASTEXITCODE -ne 0) {
    throw "failed to build phase 2 launch pack"
}

$phase2PackPath = Join-Path $phase2PackRoot "phase2_agent_wave_pack.json"
if (-not (Test-Path $phase2PackPath)) {
    throw "phase 2 launch pack was not created at $phase2PackPath"
}
$phase2Pack = Get-Content -Path $phase2PackPath -Raw | ConvertFrom-Json

Write-JsonFile -Path $statusPath -Payload ([ordered]@{
    phase = "phase1_shortlisting_complete"
    execute = $true
    updated_at = (Get-Date).ToString("o")
    phase2_plan_path = $phase2PlanPath
    phase2_pack_path = $phase2PackPath
})

if (-not $RunPhase2) {
    Write-JsonFile -Path $statusPath -Payload ([ordered]@{
        phase = "complete_phase1_only"
        execute = $true
        updated_at = (Get-Date).ToString("o")
        phase2_plan_path = $phase2PlanPath
        phase2_pack_path = $phase2PackPath
        note = "Phase 2 launch disabled."
    })
    exit 0
}

$phase2LanesToRun = @($phase2Pack.lanes)
if (-not $phase2LanesToRun) {
    Write-JsonFile -Path $statusPath -Payload ([ordered]@{
        phase = "complete_no_phase2_survivors"
        execute = $true
        updated_at = (Get-Date).ToString("o")
        phase2_plan_path = $phase2PlanPath
        phase2_pack_path = $phase2PackPath
        note = "No tickers survived into phase 2."
    })
    exit 0
}

Write-JsonFile -Path $statusPath -Payload ([ordered]@{
    phase = "phase2_exhaustive_running"
    execute = $true
    updated_at = (Get-Date).ToString("o")
    phase2_plan_path = $phase2PlanPath
    phase2_pack_path = $phase2PackPath
})

& powershell -NoProfile -ExecutionPolicy Bypass -File $agentWaveLauncherPath `
    -PackPath $phase2PackPath `
    -PythonExe $PythonExe `
    -PollSeconds $PollSeconds `
    -Execute `
    -Wait | Out-Null

if ($LASTEXITCODE -ne 0) {
    throw "phase 2 launch pack execution failed"
}

$phase2PackStatusPath = Join-Path $phase2PackRoot "launch_status.json"
$phase2Results =
    if (Test-Path $phase2PackStatusPath) {
        (Get-Content -Path $phase2PackStatusPath -Raw | ConvertFrom-Json).rows
    }
    else {
        @()
    }

Write-JsonFile -Path $phase2StatusPath -Payload ([ordered]@{
    phase = "phase2_exhaustive_complete"
    updated_at = (Get-Date).ToString("o")
    results = $phase2Results
    launch_status_path = $phase2PackStatusPath
})

Write-JsonFile -Path $statusPath -Payload ([ordered]@{
    phase = "complete"
    execute = $true
    updated_at = (Get-Date).ToString("o")
    wave_plan_path = $wavePlanPath
    phase2_plan_path = $phase2PlanPath
    phase2_pack_path = $phase2PackPath
    phase1_status_path = $phase1StatusPath
    phase2_status_path = $phase2StatusPath
})

Write-Output (([ordered]@{
    program_root = $programRootPath
    phase1_status_path = $phase1StatusPath
    shortlist_root = $shortlistRoot
    phase2_status_path = $phase2StatusPath
} | ConvertTo-Json -Depth 6))
