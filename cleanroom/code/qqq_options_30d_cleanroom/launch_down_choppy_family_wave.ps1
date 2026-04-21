param(
    [string]$ReadyBaseDir = "C:\Users\rabisaab\OneDrive - First American Corporation\qqq_options_30d_cleanroom\output\backtester_ready",
    [string]$ResearchRoot = "",
    [string]$PythonExe = "python",
    [switch]$Execute
)

$ErrorActionPreference = "Stop"

$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$runnerPath = Join-Path $scriptRoot "run_core_strategy_expansion_overnight.py"
$runRegistryReporterPath = Join-Path $scriptRoot "build_run_registry_report.py"
$defaultOutputRoot = Join-Path $scriptRoot "output"
$defaultRegistryPath = Join-Path $defaultOutputRoot "run_registry.jsonl"
$readyBasePath = [System.IO.Path]::GetFullPath($ReadyBaseDir)

if (-not (Test-Path $readyBasePath)) {
    throw "ready base directory not found: $readyBasePath"
}

if ([string]::IsNullOrWhiteSpace($ResearchRoot)) {
    $ResearchRoot = Join-Path $scriptRoot ("output\down_choppy_family_wave_" + (Get-Date -Format "yyyyMMdd_HHmmss"))
}
$researchRootPath = [System.IO.Path]::GetFullPath($ResearchRoot)
New-Item -ItemType Directory -Force -Path $researchRootPath | Out-Null
$runRegistryReportDir = Join-Path $researchRootPath "run_registry_report"
New-Item -ItemType Directory -Force -Path $runRegistryReportDir | Out-Null

function Invoke-RunRegistryReport {
    if (-not (Test-Path $runRegistryReporterPath)) {
        return
    }
    $reportArgs = @(
        $runRegistryReporterPath,
        "--output-root", $defaultOutputRoot,
        "--registry-path", $defaultRegistryPath,
        "--report-dir", $runRegistryReportDir,
        "--manifest-root", $researchRootPath
    )
    & python @reportArgs | Out-Null
}

$tickers = @(
    Get-ChildItem $readyBasePath -Directory |
        Where-Object { $_.Name -ne "collections" -and (Test-Path (Join-Path $_.FullName "manifest.json")) } |
        ForEach-Object { $_.Name.Trim().ToLower() } |
        Sort-Object -Unique
)

if (-not $tickers) {
    throw "no ready tickers found in $readyBasePath"
}

$laneConfigs = @(
    [ordered]@{
        lane_id = "01_bear_directional"
        strategy_set = "down_choppy_only"
        selection_profile = "down_choppy_focus"
        family_include = "single_leg_long_put,debit_put_spread"
        description = "Bear directional lane: single-leg puts plus debit put spreads."
    },
    [ordered]@{
        lane_id = "02_bear_premium"
        strategy_set = "down_choppy_only"
        selection_profile = "down_choppy_focus"
        family_include = "credit_call_spread,iron_condor,iron_butterfly"
        description = "Bear premium lane: credit call spreads and neutral premium structures."
    },
    [ordered]@{
        lane_id = "03_bear_convexity"
        strategy_set = "down_choppy_only"
        selection_profile = "down_choppy_focus"
        family_include = "put_backspread,long_straddle,long_strangle"
        description = "Bear convexity lane: long-vol and put backspread structures."
    },
    [ordered]@{
        lane_id = "04_butterfly_lab"
        strategy_set = "down_choppy_only"
        selection_profile = "down_choppy_focus"
        family_include = "put_butterfly,broken_wing_put_butterfly"
        description = "Butterfly lane: put butterflies and broken-wing put butterflies."
    }
)

$planRows = @()
$commandLines = @()

foreach ($lane in $laneConfigs) {
    $laneResearchDir = Join-Path $researchRootPath $lane.lane_id
    New-Item -ItemType Directory -Force -Path $laneResearchDir | Out-Null

    $args = @(
        $runnerPath,
        "--tickers", ($tickers -join ","),
        "--ready-base-dir", $readyBasePath,
        "--research-dir", $laneResearchDir,
        "--strategy-set", $lane.strategy_set,
        "--selection-profile", $lane.selection_profile,
        "--family-include", $lane.family_include
    )

    $commandLine = "$PythonExe " + (($args | ForEach-Object { if ($_ -match '\s') { '"' + $_ + '"' } else { $_ } }) -join " ")

    $planRows += [ordered]@{
        lane_id = $lane.lane_id
        description = $lane.description
        strategy_set = $lane.strategy_set
        selection_profile = $lane.selection_profile
        family_include = $lane.family_include
        tickers = $tickers
        research_dir = $laneResearchDir
        command = $commandLine
    }
    $commandLines += $commandLine
}

$planPath = Join-Path $researchRootPath "family_wave_plan.json"
$commandsPath = Join-Path $researchRootPath "family_wave_commands.ps1"
$readmePath = Join-Path $researchRootPath "README.md"

$planRows | ConvertTo-Json -Depth 6 | Set-Content -Path $planPath
$commandLines | Set-Content -Path $commandsPath

$readme = @(
    "# Down/Choppy Family Wave",
    "",
    "- Ready base dir: $readyBasePath",
    "- Ticker count: $($tickers.Count)",
    "- Execute mode: $Execute",
    "",
    "## Lanes",
    ""
)

foreach ($row in $planRows) {
    $readme += "- $($row.lane_id): $($row.description)"
    $readme += "  - family include: $($row.family_include)"
    $readme += "  - research dir: $($row.research_dir)"
}

$readme -join "`r`n" | Set-Content -Path $readmePath
Invoke-RunRegistryReport

if ($Execute) {
    foreach ($row in $planRows) {
        Start-Process -FilePath $PythonExe -ArgumentList @(
            $runnerPath,
            "--tickers", ($tickers -join ","),
            "--ready-base-dir", $readyBasePath,
            "--research-dir", $row.research_dir,
            "--strategy-set", $row.strategy_set,
            "--selection-profile", $row.selection_profile,
            "--family-include", $row.family_include
        ) -WorkingDirectory $scriptRoot
    }
    Invoke-RunRegistryReport
}

Write-Output ($planRows | ConvertTo-Json -Depth 6)
