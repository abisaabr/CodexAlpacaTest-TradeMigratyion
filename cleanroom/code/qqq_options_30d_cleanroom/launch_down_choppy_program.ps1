param(
    [string]$ReadyBaseDir = "C:\Users\rabisaab\OneDrive - First American Corporation\qqq_options_30d_cleanroom\output\backtester_ready",
    [string]$ProgramRoot = "",
    [string]$PythonExe = "python",
    [switch]$Execute,
    [switch]$RunPhase2 = $true,
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

if ([string]::IsNullOrWhiteSpace($ProgramRoot)) {
    $ProgramRoot = Join-Path $scriptRoot ("output\down_choppy_program_" + (Get-Date -Format "yyyyMMdd_HHmmss"))
}

$programRootPath = [System.IO.Path]::GetFullPath($ProgramRoot)
$discoveryRoot = Join-Path $programRootPath "discovery"
$shortlistRoot = Join-Path $programRootPath "shortlist"
$phase2Root = Join-Path $programRootPath "phase2"
$logsRoot = Join-Path $programRootPath "logs"
$statusPath = Join-Path $programRootPath "program_status.json"
$manifestPath = Join-Path $programRootPath "program_manifest.json"
$phase1StatusPath = Join-Path $programRootPath "phase1_status.json"
$phase2StatusPath = Join-Path $programRootPath "phase2_status.json"

New-Item -ItemType Directory -Force -Path $programRootPath | Out-Null
New-Item -ItemType Directory -Force -Path $discoveryRoot | Out-Null
New-Item -ItemType Directory -Force -Path $shortlistRoot | Out-Null
New-Item -ItemType Directory -Force -Path $phase2Root | Out-Null
New-Item -ItemType Directory -Force -Path $logsRoot | Out-Null

Write-JsonFile -Path $statusPath -Payload ([ordered]@{
    phase = "planning"
    execute = [bool]$Execute
    updated_at = (Get-Date).ToString("o")
})

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

$manifest = [ordered]@{
    created_at = (Get-Date).ToString("o")
    execute = [bool]$Execute
    run_phase2 = [bool]$RunPhase2
    ready_base_dir = [System.IO.Path]::GetFullPath($ReadyBaseDir)
    discovery_root = $discoveryRoot
    shortlist_root = $shortlistRoot
    phase2_root = $phase2Root
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
$phase2Plan = Get-Content -Path $phase2PlanPath -Raw | ConvertFrom-Json

Write-JsonFile -Path $statusPath -Payload ([ordered]@{
    phase = "phase1_shortlisting_complete"
    execute = $true
    updated_at = (Get-Date).ToString("o")
    phase2_plan_path = $phase2PlanPath
})

if (-not $RunPhase2) {
    Write-JsonFile -Path $statusPath -Payload ([ordered]@{
        phase = "complete_phase1_only"
        execute = $true
        updated_at = (Get-Date).ToString("o")
        phase2_plan_path = $phase2PlanPath
        note = "Phase 2 launch disabled."
    })
    exit 0
}

$phase2LanesToRun = @($phase2Plan | Where-Object { @($_.tickers).Count -gt 0 })
if (-not $phase2LanesToRun) {
    Write-JsonFile -Path $statusPath -Payload ([ordered]@{
        phase = "complete_no_phase2_survivors"
        execute = $true
        updated_at = (Get-Date).ToString("o")
        phase2_plan_path = $phase2PlanPath
        note = "No tickers survived into phase 2."
    })
    exit 0
}

foreach ($lane in $phase2LanesToRun) {
    $lane.research_dir = Join-Path $phase2Root ([string]$lane.lane_id)
}

Write-JsonFile -Path $statusPath -Payload ([ordered]@{
    phase = "phase2_exhaustive_running"
    execute = $true
    updated_at = (Get-Date).ToString("o")
    phase2_plan_path = $phase2PlanPath
})

$phase2LaneProcesses = @()
foreach ($lane in $phase2LanesToRun) {
    $phase2LaneProcesses += Start-LaneProcess -Lane $lane -Label "phase2" -LogsRoot $logsRoot
}

$phase2Results = Wait-LaneProcesses -LaneProcesses $phase2LaneProcesses -PhaseName "phase2_exhaustive_running" -StatusPath $phase2StatusPath

Write-JsonFile -Path $phase2StatusPath -Payload ([ordered]@{
    phase = "phase2_exhaustive_complete"
    updated_at = (Get-Date).ToString("o")
    results = $phase2Results
})

Write-JsonFile -Path $statusPath -Payload ([ordered]@{
    phase = "complete"
    execute = $true
    updated_at = (Get-Date).ToString("o")
    wave_plan_path = $wavePlanPath
    phase2_plan_path = $phase2PlanPath
    phase1_status_path = $phase1StatusPath
    phase2_status_path = $phase2StatusPath
})

Write-Output (([ordered]@{
    program_root = $programRootPath
    phase1_status_path = $phase1StatusPath
    shortlist_root = $shortlistRoot
    phase2_status_path = $phase2StatusPath
} | ConvertTo-Json -Depth 6))
