param(
    [string]$CycleRoot = "",
    [string]$ProgramRoot = "",
    [string]$ReadyBaseDir = "",
    [string]$LiveManifestPath = "",
    [string]$PaperRunnerGatePath = "",
    [string]$PaperRunnerTargetDate = "",
    [string]$PythonExe = "python",
    [switch]$Execute,
    [switch]$BootstrapReadyUniverse = $true,
    [ValidateSet("full_ready", "coverage_ranked")]
    [string]$DiscoverySource = "coverage_ranked",
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
$repoRoot = [System.IO.Path]::GetFullPath((Join-Path $scriptRoot "..\..\.."))
$workspaceRoot = Split-Path -Parent $repoRoot
$siblingCleanroomRoot = Join-Path $workspaceRoot "qqq_options_30d_cleanroom"
$siblingOutputRoot = Join-Path $siblingCleanroomRoot "output"
$oneDriveOutputRoot = "C:\Users\rabisaab\OneDrive - First American Corporation\qqq_options_30d_cleanroom\output"
$oneDriveReadyBaseDir = Join-Path $oneDriveOutputRoot "backtester_ready"
$siblingReadyBaseDir = Join-Path $siblingOutputRoot "backtester_ready"
$siblingLiveManifestPath = Join-Path $workspaceRoot "codexalpaca_repo\config\strategy_manifests\multi_ticker_portfolio_live.yaml"
$fallbackLiveManifestPath = "C:\Users\rabisaab\OneDrive\CodexAlpaca\downloads_remaining_20260417\folders\codexalpaca_repo\config\strategy_manifests\multi_ticker_portfolio_live.yaml"

$familyRegistryBuilderPath = Join-Path $scriptRoot "build_strategy_family_registry.py"
$familyHandoffBuilderPath = Join-Path $scriptRoot "build_strategy_family_handoff.py"
$coverageBuilderPath = Join-Path $scriptRoot "build_ticker_family_coverage.py"
$programLauncherPath = Join-Path $scriptRoot "launch_down_choppy_program.ps1"
$validatorPath = Join-Path $scriptRoot "validate_program_live_book.py"
$hardeningBuilderPath = Join-Path $scriptRoot "build_live_book_hardening_review.py"
$replacementBuilderPath = Join-Path $scriptRoot "build_live_book_replacement_plan.py"
$morningHandoffBuilderPath = Join-Path $scriptRoot "build_live_book_morning_handoff.py"
$runRegistryReporterPath = Join-Path $scriptRoot "build_run_registry_report.py"
$activeProgramReporterPath = Join-Path $scriptRoot "build_active_program_report.py"

function Resolve-PreferredPath {
    param(
        [string[]]$Candidates,
        [string]$Fallback
    )

    foreach ($candidate in @($Candidates)) {
        if (-not [string]::IsNullOrWhiteSpace($candidate) -and (Test-Path $candidate)) {
            return [System.IO.Path]::GetFullPath($candidate)
        }
    }

    if (-not [string]::IsNullOrWhiteSpace($Fallback)) {
        return [System.IO.Path]::GetFullPath($Fallback)
    }

    throw "No preferred path candidates were provided."
}

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

function Get-NextWeekdayDate {
    $candidate = (Get-Date).Date.AddDays(1)
    while ($candidate.DayOfWeek -in @([System.DayOfWeek]::Saturday, [System.DayOfWeek]::Sunday)) {
        $candidate = $candidate.AddDays(1)
    }
    return $candidate.ToString("yyyy-MM-dd")
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
        "--output-root", $researchOutputRoot,
        "--registry-path", $runRegistryPath,
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

function Write-Status {
    param(
        [string]$Phase,
        [string]$Message,
        [hashtable]$Extra = @{}
    )

    $payload = [ordered]@{
        phase = $Phase
        execute = [bool]$Execute
        message = $Message
        updated_at = (Get-Date).ToString("o")
        cycle_root = $cycleRootPath
        program_root = $programRootPath
        family_refresh_dir = $familyRefreshRoot
        coverage_refresh_dir = $coverageRefreshRoot
        validation_dir = $validationRoot
        review_dir = $reviewRoot
        replacement_plan_dir = $replacementPlanRoot
        morning_handoff_dir = $morningHandoffRoot
        run_registry_report_dir = $runRegistryReportDir
        active_program_report_dir = $activeProgramReportDir
    }

    foreach ($entry in $Extra.GetEnumerator()) {
        $payload[$entry.Key] = $entry.Value
    }

    Write-JsonFile -Path $statusPath -Payload $payload
}

function Write-PaperRunnerGate {
    param(
        [string]$Status,
        [string]$Phase,
        [string]$Message
    )

    $payload = [ordered]@{
        status = $Status
        phase = $Phase
        message = $Message
        target_trade_date = $PaperRunnerTargetDate
        updated_at = (Get-Date).ToString("o")
        cycle_root = $cycleRootPath
        program_root = $programRootPath
        validation_dir = $validationRoot
        review_dir = $reviewRoot
        replacement_plan_dir = $replacementPlanRoot
        morning_handoff_dir = $morningHandoffRoot
        morning_handoff_json =
            if (Test-Path $morningHandoffJsonPath) {
                $morningHandoffJsonPath
            }
            else {
                ""
            }
        status_path = $statusPath
    }
    Write-JsonFile -Path $PaperRunnerGatePath -Payload $payload
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

function Invoke-PowerShellStep {
    param(
        [string]$ScriptPath,
        [object[]]$Arguments,
        [string]$FailureMessage
    )

    & powershell -NoProfile -ExecutionPolicy Bypass -File $ScriptPath @Arguments | Out-Null
    if ($LASTEXITCODE -ne 0) {
        throw $FailureMessage
    }
}

function Get-ProgramPhase {
    if (-not (Test-Path $programStatusPath)) {
        return ""
    }
    try {
        return [string]((Get-Content -Path $programStatusPath -Raw | ConvertFrom-Json).phase)
    }
    catch {
        return ""
    }
}

function Refresh-ActiveProgramReport {
    if (-not (Test-Path $activeProgramReporterPath)) {
        return
    }
    & $PythonExe $activeProgramReporterPath --program-root $programRootPath --report-dir $activeProgramReportDir | Out-Null
}

if ([string]::IsNullOrWhiteSpace($ReadyBaseDir)) {
    $ReadyBaseDir = Resolve-PreferredPath -Candidates @($siblingReadyBaseDir, $oneDriveReadyBaseDir) -Fallback $siblingReadyBaseDir
}
else {
    $ReadyBaseDir = [System.IO.Path]::GetFullPath($ReadyBaseDir)
}

if ([string]::IsNullOrWhiteSpace($LiveManifestPath)) {
    $LiveManifestPath = Resolve-PreferredPath -Candidates @($siblingLiveManifestPath, $fallbackLiveManifestPath) -Fallback $siblingLiveManifestPath
}
else {
    $LiveManifestPath = [System.IO.Path]::GetFullPath($LiveManifestPath)
}

$researchOutputRoot = Resolve-PreferredPath -Candidates @($siblingOutputRoot, $oneDriveOutputRoot) -Fallback $siblingOutputRoot
$secondaryOutputDir = $researchOutputRoot
$backtesterRegistryPath = Join-Path $secondaryOutputDir "backtester_registry.csv"
$runRegistryPath = Join-Path $researchOutputRoot "run_registry.jsonl"

if ([string]::IsNullOrWhiteSpace($CycleRoot)) {
    $CycleRoot = Join-Path $researchOutputRoot ("nightly_operator_cycle_" + (Get-Date -Format "yyyyMMdd_HHmmss"))
}
$cycleRootPath = [System.IO.Path]::GetFullPath($CycleRoot)

if ([string]::IsNullOrWhiteSpace($ProgramRoot)) {
    $ProgramRoot = Join-Path $cycleRootPath "program"
}
$programRootPath = [System.IO.Path]::GetFullPath($ProgramRoot)

if ([string]::IsNullOrWhiteSpace($PaperRunnerGatePath)) {
    $PaperRunnerGatePath = Join-Path $researchOutputRoot "paper_runner_gate.json"
}
else {
    $PaperRunnerGatePath = [System.IO.Path]::GetFullPath($PaperRunnerGatePath)
}

if ([string]::IsNullOrWhiteSpace($PaperRunnerTargetDate)) {
    $PaperRunnerTargetDate = Get-NextWeekdayDate
}

$familyRefreshRoot = Join-Path $cycleRootPath "family_refresh"
$coverageRefreshRoot = Join-Path $cycleRootPath "coverage_refresh"
$runRegistryReportDir = Join-Path $cycleRootPath "run_registry_report"
$activeProgramReportDir = Join-Path $cycleRootPath "active_program_report"
$validationRoot = Join-Path $programRootPath "live_book_validation"
$reviewRoot = Join-Path $validationRoot "hardening_review"
$replacementPlanRoot = Join-Path $reviewRoot "replacement_plan"
$morningHandoffRoot = Join-Path $reviewRoot "morning_handoff"

$statusPath = Join-Path $cycleRootPath "nightly_operator_cycle_status.json"
$manifestPath = Join-Path $cycleRootPath "nightly_operator_cycle_manifest.json"
$handoffPath = Join-Path $cycleRootPath "nightly_operator_cycle_handoff.json"
$programStatusPath = Join-Path $programRootPath "program_status.json"
$phase2PackPath = Join-Path $programRootPath "phase2\launch_pack\phase2_agent_wave_pack.json"
$phase2PackStatusPath = Join-Path $programRootPath "phase2\launch_pack\launch_status.json"
$validationJsonPath = Join-Path $validationRoot "live_book_validation.json"
$reviewJsonPath = Join-Path $reviewRoot "live_book_hardening_review.json"
$replacementPlanJsonPath = Join-Path $replacementPlanRoot "live_book_replacement_plan.json"
$morningHandoffJsonPath = Join-Path $morningHandoffRoot "live_book_morning_handoff.json"

New-Item -ItemType Directory -Force -Path $cycleRootPath | Out-Null
New-Item -ItemType Directory -Force -Path $programRootPath | Out-Null
New-Item -ItemType Directory -Force -Path $familyRefreshRoot | Out-Null
New-Item -ItemType Directory -Force -Path $coverageRefreshRoot | Out-Null
New-Item -ItemType Directory -Force -Path $runRegistryReportDir | Out-Null
New-Item -ItemType Directory -Force -Path $activeProgramReportDir | Out-Null

$cycleManifest = [ordered]@{
    created_at = (Get-Date).ToString("o")
    execute = [bool]$Execute
    repo_root = $repoRoot
    workspace_root = $workspaceRoot
    cycle_root = $cycleRootPath
    program_root = $programRootPath
    research_output_root = $researchOutputRoot
    ready_base_dir = $ReadyBaseDir
    secondary_output_dir = $secondaryOutputDir
    backtester_registry_path = $backtesterRegistryPath
    live_manifest_path = $LiveManifestPath
    paper_runner_gate_path = $PaperRunnerGatePath
    paper_runner_target_date = $PaperRunnerTargetDate
    discovery_source = $DiscoverySource
    bootstrap_ready_universe = [bool]$BootstrapReadyUniverse
    filters = [ordered]@{
        top_per_lane = $TopPerLane
        max_per_phase2_lane = $MaxPerPhase2Lane
        min_return_pct = $MinReturnPct
        max_drawdown_pct = $MaxDrawdownPct
        max_avg_friction_pct = $MaxAvgFrictionPct
        max_cheap_share_pct = $MaxCheapSharePct
        min_trade_count = $MinTradeCount
    }
    control_plane = [ordered]@{
        family_registry_builder = $familyRegistryBuilderPath
        family_handoff_builder = $familyHandoffBuilderPath
        coverage_builder = $coverageBuilderPath
        program_launcher = $programLauncherPath
        validator = $validatorPath
        hardening_builder = $hardeningBuilderPath
        replacement_builder = $replacementBuilderPath
        morning_handoff_builder = $morningHandoffBuilderPath
        run_registry_reporter = $runRegistryReporterPath
    }
}
Write-JsonFile -Path $manifestPath -Payload $cycleManifest

trap {
    $failureMessage =
        if ($_.Exception -and -not [string]::IsNullOrWhiteSpace([string]$_.Exception.Message)) {
            [string]$_.Exception.Message
        }
        else {
            [string]$_
        }

    Write-Status -Phase "failed" -Message $failureMessage
    if ($Execute) {
        Write-PaperRunnerGate -Status "failed" -Phase "failed" -Message $failureMessage
    }
    Refresh-ActiveProgramReport
    Invoke-RunRegistryReport -ReportDir $runRegistryReportDir -ManifestRoots @(
        $cycleRootPath,
        $programRootPath,
        $validationRoot,
        $reviewRoot,
        $replacementPlanRoot,
        $morningHandoffRoot
    )
    Write-Error $failureMessage
    exit 2
}

Write-Status -Phase "refreshing_family_registry" -Message "Refreshing the strategy family registry."

$familyRegistryArgs = @(
    "--output-root", $researchOutputRoot,
    "--ready-base-dir", $ReadyBaseDir,
    "--live-manifest-path", $LiveManifestPath,
    "--report-dir", $familyRefreshRoot
)
Invoke-PythonStep -ScriptPath $familyRegistryBuilderPath -Arguments $familyRegistryArgs -FailureMessage "Failed to refresh strategy family registry."

$familyRegistryJsonPath = Join-Path $familyRefreshRoot "strategy_family_registry.json"
if (-not (Test-Path $familyRegistryJsonPath)) {
    throw "Strategy family registry JSON was not created at $familyRegistryJsonPath"
}

Write-Status -Phase "refreshing_family_handoff" -Message "Refreshing the strategy family handoff packet."

$familyHandoffArgs = @(
    "--registry-json", $familyRegistryJsonPath,
    "--report-dir", $familyRefreshRoot
)
Invoke-PythonStep -ScriptPath $familyHandoffBuilderPath -Arguments $familyHandoffArgs -FailureMessage "Failed to refresh strategy family handoff."

$familyHandoffJsonPath = Join-Path $familyRefreshRoot "strategy_family_handoff.json"
if (-not (Test-Path $familyHandoffJsonPath)) {
    throw "Strategy family handoff JSON was not created at $familyHandoffJsonPath"
}

Write-Status -Phase "refreshing_coverage" -Message "Refreshing the ticker-family coverage plan."

$coverageArgs = @(
    "--output-root", $researchOutputRoot,
    "--ready-base-dir", $ReadyBaseDir,
    "--secondary-output-dir", $secondaryOutputDir,
    "--registry-path", $backtesterRegistryPath,
    "--report-dir", $coverageRefreshRoot
)
Invoke-PythonStep -ScriptPath $coverageBuilderPath -Arguments $coverageArgs -FailureMessage "Failed to refresh ticker-family coverage."

$coveragePlanPath = Join-Path $coverageRefreshRoot "next_wave_plan.json"
if (-not (Test-Path $coveragePlanPath)) {
    throw "Coverage planner did not create next_wave_plan.json at $coveragePlanPath"
}

Invoke-RunRegistryReport -ReportDir $runRegistryReportDir -ManifestRoots @($cycleRootPath, $programRootPath)

if (-not $Execute) {
    Write-Status -Phase "planning_program" -Message "Building the nightly research program plan without launching it."

    $programArgs = @(
        "-ProgramRoot", $programRootPath,
        "-ReadyBaseDir", $ReadyBaseDir,
        "-SecondaryOutputDir", $secondaryOutputDir,
        "-RegistryPath", $backtesterRegistryPath,
        "-PythonExe", $PythonExe,
        "-DiscoverySource", $DiscoverySource,
        "-CoveragePlannerPath", $coverageBuilderPath,
        "-CoverageReportDir", $coverageRefreshRoot,
        "-TopPerLane", $TopPerLane,
        "-MaxPerPhase2Lane", $MaxPerPhase2Lane,
        "-MinReturnPct", $MinReturnPct,
        "-MaxDrawdownPct", $MaxDrawdownPct,
        "-MaxAvgFrictionPct", $MaxAvgFrictionPct,
        "-MaxCheapSharePct", $MaxCheapSharePct,
        "-MinTradeCount", $MinTradeCount,
        "-PollSeconds", $PollSeconds
    )
    if ($BootstrapReadyUniverse) {
        $programArgs += "-BootstrapReadyUniverse"
    }
    Invoke-PowerShellStep -ScriptPath $programLauncherPath -Arguments $programArgs -FailureMessage "Failed to build nightly research program plan."

    Refresh-ActiveProgramReport
    Invoke-RunRegistryReport -ReportDir $runRegistryReportDir -ManifestRoots @($cycleRootPath, $programRootPath)

    Write-Status -Phase "planned" -Message "Nightly operator cycle planned successfully." -Extra @{
        family_registry_json = $familyRegistryJsonPath
        family_handoff_json = $familyHandoffJsonPath
        coverage_plan_json = $coveragePlanPath
        program_status_path = $programStatusPath
        next_step = "Run again with -Execute to launch the full nightly cycle."
    }
    exit 0
}

Write-PaperRunnerGate -Status "pending" -Phase "planning" -Message "Nightly operator cycle is refreshing governance and planning the research program."

Write-Status -Phase "running_program" -Message "Launching the nightly discovery and exhaustive research program."
Write-PaperRunnerGate -Status "pending" -Phase "running_program" -Message "Nightly discovery and exhaustive research program is running."

$programArgs = @(
    "-ProgramRoot", $programRootPath,
    "-ReadyBaseDir", $ReadyBaseDir,
    "-SecondaryOutputDir", $secondaryOutputDir,
    "-RegistryPath", $backtesterRegistryPath,
    "-PythonExe", $PythonExe,
    "-DiscoverySource", $DiscoverySource,
    "-CoveragePlannerPath", $coverageBuilderPath,
    "-CoverageReportDir", $coverageRefreshRoot,
    "-TopPerLane", $TopPerLane,
    "-MaxPerPhase2Lane", $MaxPerPhase2Lane,
    "-MinReturnPct", $MinReturnPct,
    "-MaxDrawdownPct", $MaxDrawdownPct,
    "-MaxAvgFrictionPct", $MaxAvgFrictionPct,
    "-MaxCheapSharePct", $MaxCheapSharePct,
    "-MinTradeCount", $MinTradeCount,
    "-PollSeconds", $PollSeconds,
    "-Execute"
)
if ($BootstrapReadyUniverse) {
    $programArgs += "-BootstrapReadyUniverse"
}
Invoke-PowerShellStep -ScriptPath $programLauncherPath -Arguments $programArgs -FailureMessage "Nightly discovery/exhaustive program failed."

Refresh-ActiveProgramReport
Invoke-RunRegistryReport -ReportDir $runRegistryReportDir -ManifestRoots @($cycleRootPath, $programRootPath)

$programPhase = Get-ProgramPhase
if ($programPhase -notin @("complete", "complete_phase1_only", "complete_no_phase2_survivors")) {
    throw "Nightly research program did not reach a terminal success state."
}

Write-Status -Phase "validating" -Message "Validating challengers against the current live champion book."
Write-PaperRunnerGate -Status "pending" -Phase "validating" -Message "Validating challengers against the current live champion book."

$validatorArgs = @(
    "--program-root", $programRootPath,
    "--output-dir", $validationRoot,
    "--live-manifest", $LiveManifestPath
)
Invoke-PythonStep -ScriptPath $validatorPath -Arguments $validatorArgs -FailureMessage "Live-book validation failed."

Write-Status -Phase "reviewing" -Message "Building the live-book hardening review packet."
Write-PaperRunnerGate -Status "pending" -Phase "reviewing" -Message "Building the live-book hardening review packet."

$reviewArgs = @(
    "--validation-dir", $validationRoot,
    "--output-dir", $reviewRoot,
    "--live-manifest", $LiveManifestPath
)
Invoke-PythonStep -ScriptPath $hardeningBuilderPath -Arguments $reviewArgs -FailureMessage "Live-book hardening review build failed."

Write-Status -Phase "planning_replacement" -Message "Building the non-destructive live-book replacement plan."
Write-PaperRunnerGate -Status "pending" -Phase "planning_replacement" -Message "Building the non-destructive live-book replacement plan."

$replacementArgs = @(
    "--validation-dir", $validationRoot,
    "--review-dir", $reviewRoot,
    "--output-dir", $replacementPlanRoot,
    "--live-manifest", $LiveManifestPath
)
Invoke-PythonStep -ScriptPath $replacementBuilderPath -Arguments $replacementArgs -FailureMessage "Live-book replacement plan build failed."

Write-Status -Phase "building_morning_handoff" -Message "Building the morning handoff packet."
Write-PaperRunnerGate -Status "pending" -Phase "building_morning_handoff" -Message "Building the morning handoff packet."

$handoffArgs = @(
    "--validation-dir", $validationRoot,
    "--review-dir", $reviewRoot,
    "--replacement-plan-dir", $replacementPlanRoot,
    "--output-dir", $morningHandoffRoot
)
Invoke-PythonStep -ScriptPath $morningHandoffBuilderPath -Arguments $handoffArgs -FailureMessage "Morning handoff build failed."

if (-not (Test-Path $morningHandoffJsonPath)) {
    throw "Morning handoff JSON was not created at $morningHandoffJsonPath"
}

Refresh-ActiveProgramReport
Invoke-RunRegistryReport -ReportDir $runRegistryReportDir -ManifestRoots @(
    $cycleRootPath,
    $programRootPath,
    $validationRoot,
    $reviewRoot,
    $replacementPlanRoot,
    $morningHandoffRoot
)

$handoffPayload = Get-Content -Path $morningHandoffJsonPath -Raw | ConvertFrom-Json
$finalPayload = [ordered]@{
    completed_at = (Get-Date).ToString("o")
    cycle_root = $cycleRootPath
    program_root = $programRootPath
    program_phase = $programPhase
    family_registry_json = $familyRegistryJsonPath
    family_handoff_json = $familyHandoffJsonPath
    coverage_plan_json = $coveragePlanPath
    phase2_pack_json =
        if (Test-Path $phase2PackPath) {
            $phase2PackPath
        }
        else {
            ""
        }
    phase2_pack_status_json =
        if (Test-Path $phase2PackStatusPath) {
            $phase2PackStatusPath
        }
        else {
            ""
        }
    validation_json = $validationJsonPath
    hardening_review_json = $reviewJsonPath
    replacement_plan_json = $replacementPlanJsonPath
    morning_handoff_json = $morningHandoffJsonPath
    morning_decision = [string]$handoffPayload.morning_decision
    operator_message = [string]$handoffPayload.operator_message
    paper_runner_guidance = [string]$handoffPayload.paper_runner_guidance
    paper_runner_gate_path = $PaperRunnerGatePath
    run_registry_report_dir = $runRegistryReportDir
    active_program_report_dir = $activeProgramReportDir
}
Write-JsonFile -Path $handoffPath -Payload $finalPayload

Write-Status -Phase "completed" -Message "Nightly operator cycle completed successfully." -Extra @{
    family_registry_json = $familyRegistryJsonPath
    family_handoff_json = $familyHandoffJsonPath
    coverage_plan_json = $coveragePlanPath
    validation_json = $validationJsonPath
    hardening_review_json = $reviewJsonPath
    replacement_plan_json = $replacementPlanJsonPath
    morning_handoff_json = $morningHandoffJsonPath
    nightly_handoff_json = $handoffPath
}
Write-PaperRunnerGate -Status "completed" -Phase "completed" -Message "Nightly operator cycle completed successfully."

Write-Output ($finalPayload | ConvertTo-Json -Depth 10)
exit 0
