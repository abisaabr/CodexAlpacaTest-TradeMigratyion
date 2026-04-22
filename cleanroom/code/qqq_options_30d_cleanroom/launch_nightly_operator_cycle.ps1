param(
    [string]$CycleRoot = "",
    [string]$ProgramRoot = "",
    [string]$RunnerRepoRoot = "",
    [string]$ReadyBaseDir = "",
    [string]$LiveManifestPath = "",
    [string]$PaperRunnerGatePath = "",
    [string]$PaperRunnerTargetDate = "",
    [string]$PythonExe = "python",
    [switch]$Execute,
    [switch]$BootstrapReadyUniverse = $true,
    [ValidateSet("auto", "down_choppy_coverage_ranked", "down_choppy_full_ready", "opening_30m_premium_defense", "balanced_family_expansion_benchmark")]
    [string]$TournamentProfile = "auto",
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

$discoverySourceWasExplicit = $PSBoundParameters.ContainsKey("DiscoverySource")
$bootstrapReadyWasExplicit = $PSBoundParameters.ContainsKey("BootstrapReadyUniverse")

$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = [System.IO.Path]::GetFullPath((Join-Path $scriptRoot "..\..\.."))
$workspaceRoot = Split-Path -Parent $repoRoot
$siblingRunnerRepoRoot = Join-Path $workspaceRoot "codexalpaca_repo"
$siblingCleanroomRoot = Join-Path $workspaceRoot "qqq_options_30d_cleanroom"
$siblingOutputRoot = Join-Path $siblingCleanroomRoot "output"
$oneDriveOutputRoot = "C:\Users\rabisaab\OneDrive - First American Corporation\qqq_options_30d_cleanroom\output"
$oneDriveReadyBaseDir = Join-Path $oneDriveOutputRoot "backtester_ready"
$siblingReadyBaseDir = Join-Path $siblingOutputRoot "backtester_ready"
$siblingLiveManifestPath = Join-Path $workspaceRoot "codexalpaca_repo\config\strategy_manifests\multi_ticker_portfolio_live.yaml"
$fallbackLiveManifestPath = "C:\Users\rabisaab\OneDrive\CodexAlpaca\downloads_remaining_20260417\folders\codexalpaca_repo\config\strategy_manifests\multi_ticker_portfolio_live.yaml"

$familyRegistryBuilderPath = Join-Path $scriptRoot "build_strategy_family_registry.py"
$familyHandoffBuilderPath = Join-Path $scriptRoot "build_strategy_family_handoff.py"
$sessionReconciliationBuilderPath = Join-Path $scriptRoot "build_session_reconciliation_registry.py"
$sessionReconciliationHandoffBuilderPath = Join-Path $scriptRoot "build_session_reconciliation_handoff.py"
$executionCalibrationBuilderPath = Join-Path $scriptRoot "build_execution_calibration_registry.py"
$executionCalibrationHandoffBuilderPath = Join-Path $scriptRoot "build_execution_calibration_handoff.py"
$tournamentProfileBuilderPath = Join-Path $scriptRoot "build_tournament_profile_registry.py"
$tournamentProfileHandoffBuilderPath = Join-Path $scriptRoot "build_tournament_profile_handoff.py"
$tournamentUnlockBuilderPath = Join-Path $scriptRoot "build_tournament_unlock_registry.py"
$tournamentUnlockHandoffBuilderPath = Join-Path $scriptRoot "build_tournament_unlock_handoff.py"
$tournamentUnlockWorkplanBuilderPath = Join-Path $scriptRoot "build_tournament_unlock_workplan.py"
$tournamentUnlockWorkplanHandoffBuilderPath = Join-Path $scriptRoot "build_tournament_unlock_workplan_handoff.py"
$executionEvidenceContractBuilderPath = Join-Path $scriptRoot "build_execution_evidence_contract.py"
$executionEvidenceContractHandoffBuilderPath = Join-Path $scriptRoot "build_execution_evidence_contract_handoff.py"
$overnightPhasedPlanBuilderPath = Join-Path $scriptRoot "build_overnight_phased_plan.py"
$overnightPhasedPlanHandoffBuilderPath = Join-Path $scriptRoot "build_overnight_phased_plan_handoff.py"
$coverageBuilderPath = Join-Path $scriptRoot "build_ticker_family_coverage.py"
$defaultProgramLauncherPath = Join-Path $scriptRoot "launch_down_choppy_program.ps1"
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
        session_reconciliation_dir = $sessionReconciliationRoot
        session_reconciliation_handoff_json =
            if (Test-Path $sessionReconciliationHandoffJsonPath) {
                $sessionReconciliationHandoffJsonPath
            }
            else {
                ""
            }
        execution_calibration_dir = $executionCalibrationRoot
        execution_calibration_handoff_json =
            if (Test-Path $executionCalibrationHandoffJsonPath) {
                $executionCalibrationHandoffJsonPath
            }
            else {
                ""
            }
        family_refresh_dir = $familyRefreshRoot
        tournament_profile_dir = $tournamentProfileRoot
        tournament_profile_handoff_json =
            if (Test-Path $tournamentProfileHandoffJsonPath) {
                $tournamentProfileHandoffJsonPath
            }
            else {
                ""
            }
        tournament_unlock_dir = $tournamentUnlockRoot
        tournament_unlock_handoff_json =
            if (Test-Path $tournamentUnlockHandoffJsonPath) {
                $tournamentUnlockHandoffJsonPath
            }
            else {
                ""
            }
        tournament_unlock_workplan_json =
            if (Test-Path $tournamentUnlockWorkplanJsonPath) {
                $tournamentUnlockWorkplanJsonPath
            }
            else {
                ""
            }
        tournament_unlock_workplan_handoff_json =
            if (Test-Path $tournamentUnlockWorkplanHandoffJsonPath) {
                $tournamentUnlockWorkplanHandoffJsonPath
            }
            else {
                ""
            }
        execution_evidence_contract_dir = $executionEvidenceRoot
        execution_evidence_contract_handoff_json =
            if (Test-Path $executionEvidenceContractHandoffJsonPath) {
                $executionEvidenceContractHandoffJsonPath
            }
            else {
                ""
            }
        overnight_plan_dir = $overnightPlanRoot
        overnight_plan_handoff_json =
            if (Test-Path $overnightPlanHandoffJsonPath) {
                $overnightPlanHandoffJsonPath
            }
            else {
                ""
            }
        requested_tournament_profile = $TournamentProfile
        resolved_tournament_profile = $resolvedTournamentProfile
        tournament_profile_resolution_mode = $tournamentProfileResolutionMode
        tournament_profile_resolution_warning = $tournamentProfileResolutionWarning
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

function Read-JsonFile {
    param(
        [string]$Path
    )

    return Get-Content -Path $Path -Raw | ConvertFrom-Json
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

if ([string]::IsNullOrWhiteSpace($RunnerRepoRoot)) {
    $RunnerRepoRoot = Resolve-PreferredPath -Candidates @($siblingRunnerRepoRoot) -Fallback $siblingRunnerRepoRoot
}
else {
    $RunnerRepoRoot = [System.IO.Path]::GetFullPath($RunnerRepoRoot)
}

if ([string]::IsNullOrWhiteSpace($LiveManifestPath)) {
    $runnerLiveManifestPath = Join-Path $RunnerRepoRoot "config\strategy_manifests\multi_ticker_portfolio_live.yaml"
    $LiveManifestPath = Resolve-PreferredPath -Candidates @($runnerLiveManifestPath, $siblingLiveManifestPath, $fallbackLiveManifestPath) -Fallback $runnerLiveManifestPath
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
$sessionReconciliationRoot = Join-Path $cycleRootPath "session_reconciliation"
$executionCalibrationRoot = Join-Path $cycleRootPath "execution_calibration"
$tournamentProfileRoot = Join-Path $cycleRootPath "tournament_profiles"
$tournamentUnlockRoot = Join-Path $cycleRootPath "tournament_unlocks"
$executionEvidenceRoot = Join-Path $cycleRootPath "execution_evidence"
$overnightPlanRoot = Join-Path $cycleRootPath "overnight_plan"
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
$sessionReconciliationHandoffJsonPath = Join-Path $sessionReconciliationRoot "session_reconciliation_handoff.json"
$executionCalibrationHandoffJsonPath = Join-Path $executionCalibrationRoot "execution_calibration_handoff.json"
$tournamentProfileHandoffJsonPath = Join-Path $tournamentProfileRoot "tournament_profile_handoff.json"
$tournamentUnlockHandoffJsonPath = Join-Path $tournamentUnlockRoot "tournament_unlock_handoff.json"
$tournamentUnlockWorkplanJsonPath = Join-Path $tournamentUnlockRoot "tournament_unlock_workplan.json"
$tournamentUnlockWorkplanHandoffJsonPath = Join-Path $tournamentUnlockRoot "tournament_unlock_workplan_handoff.json"
$executionEvidenceContractJsonPath = Join-Path $executionEvidenceRoot "execution_evidence_contract.json"
$executionEvidenceContractHandoffJsonPath = Join-Path $executionEvidenceRoot "execution_evidence_contract_handoff.json"
$overnightPlanJsonPath = Join-Path $overnightPlanRoot "overnight_phased_plan.json"
$overnightPlanHandoffJsonPath = Join-Path $overnightPlanRoot "overnight_phased_plan_handoff.json"
$programStatusPath = Join-Path $programRootPath "program_status.json"
$phase2PackPath = Join-Path $programRootPath "phase2\launch_pack\phase2_agent_wave_pack.json"
$phase2PackStatusPath = Join-Path $programRootPath "phase2\launch_pack\launch_status.json"
$validationJsonPath = Join-Path $validationRoot "live_book_validation.json"
$reviewJsonPath = Join-Path $reviewRoot "live_book_hardening_review.json"
$replacementPlanJsonPath = Join-Path $replacementPlanRoot "live_book_replacement_plan.json"
$morningHandoffJsonPath = Join-Path $morningHandoffRoot "live_book_morning_handoff.json"
$resolvedTournamentProfile = ""
$tournamentProfileResolutionMode = ""
$tournamentProfileResolutionWarning = ""
$resolvedProgramLauncherPath = $defaultProgramLauncherPath
$resolvedProgramLauncherName = [System.IO.Path]::GetFileName($defaultProgramLauncherPath)
$resolvedProgramExtraArgs = @()

New-Item -ItemType Directory -Force -Path $cycleRootPath | Out-Null
New-Item -ItemType Directory -Force -Path $programRootPath | Out-Null
New-Item -ItemType Directory -Force -Path $sessionReconciliationRoot | Out-Null
New-Item -ItemType Directory -Force -Path $executionCalibrationRoot | Out-Null
New-Item -ItemType Directory -Force -Path $familyRefreshRoot | Out-Null
New-Item -ItemType Directory -Force -Path $tournamentProfileRoot | Out-Null
New-Item -ItemType Directory -Force -Path $tournamentUnlockRoot | Out-Null
New-Item -ItemType Directory -Force -Path $executionEvidenceRoot | Out-Null
New-Item -ItemType Directory -Force -Path $overnightPlanRoot | Out-Null
New-Item -ItemType Directory -Force -Path $coverageRefreshRoot | Out-Null
New-Item -ItemType Directory -Force -Path $runRegistryReportDir | Out-Null
New-Item -ItemType Directory -Force -Path $activeProgramReportDir | Out-Null

$cycleManifest = [ordered]@{
    created_at = (Get-Date).ToString("o")
    execute = [bool]$Execute
    repo_root = $repoRoot
    workspace_root = $workspaceRoot
    runner_repo_root = $RunnerRepoRoot
    cycle_root = $cycleRootPath
    program_root = $programRootPath
    research_output_root = $researchOutputRoot
    ready_base_dir = $ReadyBaseDir
    secondary_output_dir = $secondaryOutputDir
    backtester_registry_path = $backtesterRegistryPath
    live_manifest_path = $LiveManifestPath
    paper_runner_gate_path = $PaperRunnerGatePath
    paper_runner_target_date = $PaperRunnerTargetDate
    requested_tournament_profile = $TournamentProfile
    resolved_tournament_profile = ""
    tournament_profile_resolution_mode = ""
    tournament_profile_resolution_warning = ""
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
        session_reconciliation_builder = $sessionReconciliationBuilderPath
        session_reconciliation_handoff_builder = $sessionReconciliationHandoffBuilderPath
        execution_calibration_builder = $executionCalibrationBuilderPath
        execution_calibration_handoff_builder = $executionCalibrationHandoffBuilderPath
        family_registry_builder = $familyRegistryBuilderPath
        family_handoff_builder = $familyHandoffBuilderPath
        tournament_profile_builder = $tournamentProfileBuilderPath
        tournament_profile_handoff_builder = $tournamentProfileHandoffBuilderPath
        overnight_plan_builder = $overnightPhasedPlanBuilderPath
        overnight_plan_handoff_builder = $overnightPhasedPlanHandoffBuilderPath
        coverage_builder = $coverageBuilderPath
        program_launcher = $defaultProgramLauncherPath
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

Write-Status -Phase "refreshing_session_reconciliation" -Message "Refreshing the session reconciliation registry from paper-runner session bundles."

$sessionReconciliationArgs = @(
    "--runner-repo-root", $RunnerRepoRoot,
    "--reports-root", (Join-Path $RunnerRepoRoot "reports\multi_ticker_portfolio\runs"),
    "--report-dir", $sessionReconciliationRoot
)
Invoke-PythonStep -ScriptPath $sessionReconciliationBuilderPath -Arguments $sessionReconciliationArgs -FailureMessage "Failed to refresh session reconciliation registry."

$sessionReconciliationJsonPath = Join-Path $sessionReconciliationRoot "session_reconciliation_registry.json"
if (-not (Test-Path $sessionReconciliationJsonPath)) {
    throw "Session reconciliation registry JSON was not created at $sessionReconciliationJsonPath"
}

Write-Status -Phase "refreshing_session_reconciliation_handoff" -Message "Refreshing the session reconciliation steward handoff."

$sessionReconciliationHandoffArgs = @(
    "--registry-json", $sessionReconciliationJsonPath,
    "--report-dir", $sessionReconciliationRoot
)
Invoke-PythonStep -ScriptPath $sessionReconciliationHandoffBuilderPath -Arguments $sessionReconciliationHandoffArgs -FailureMessage "Failed to refresh session reconciliation handoff."

if (-not (Test-Path $sessionReconciliationHandoffJsonPath)) {
    throw "Session reconciliation handoff JSON was not created at $sessionReconciliationHandoffJsonPath"
}

Write-Status -Phase "refreshing_execution_calibration" -Message "Refreshing the execution calibration registry from paper-runner artifacts."

$executionCalibrationArgs = @(
    "--runner-repo-root", $RunnerRepoRoot,
    "--reports-root", (Join-Path $RunnerRepoRoot "reports\multi_ticker_portfolio"),
    "--report-dir", $executionCalibrationRoot,
    "--session-reconciliation-registry-json", (Join-Path $sessionReconciliationRoot "session_reconciliation_registry.json"),
    "--session-reconciliation-handoff-json", $sessionReconciliationHandoffJsonPath
)
Invoke-PythonStep -ScriptPath $executionCalibrationBuilderPath -Arguments $executionCalibrationArgs -FailureMessage "Failed to refresh execution calibration registry."

$executionCalibrationJsonPath = Join-Path $executionCalibrationRoot "execution_calibration_registry.json"
if (-not (Test-Path $executionCalibrationJsonPath)) {
    throw "Execution calibration registry JSON was not created at $executionCalibrationJsonPath"
}

Write-Status -Phase "refreshing_execution_calibration_handoff" -Message "Refreshing the execution calibration steward handoff."

$executionCalibrationHandoffArgs = @(
    "--registry-json", $executionCalibrationJsonPath,
    "--report-dir", $executionCalibrationRoot
)
Invoke-PythonStep -ScriptPath $executionCalibrationHandoffBuilderPath -Arguments $executionCalibrationHandoffArgs -FailureMessage "Failed to refresh execution calibration handoff."

if (-not (Test-Path $executionCalibrationHandoffJsonPath)) {
    throw "Execution calibration handoff JSON was not created at $executionCalibrationHandoffJsonPath"
}

Write-Status -Phase "refreshing_tournament_profiles" -Message "Refreshing the tournament profile registry."

$tournamentProfileArgs = @(
    "--report-dir", $tournamentProfileRoot
)
Invoke-PythonStep -ScriptPath $tournamentProfileBuilderPath -Arguments $tournamentProfileArgs -FailureMessage "Failed to refresh tournament profile registry."

$tournamentProfileJsonPath = Join-Path $tournamentProfileRoot "tournament_profile_registry.json"
if (-not (Test-Path $tournamentProfileJsonPath)) {
    throw "Tournament profile registry JSON was not created at $tournamentProfileJsonPath"
}

Write-Status -Phase "resolving_tournament_profile" -Message "Resolving the nightly tournament profile from the tournament registry and execution calibration handoff."

$tournamentProfileHandoffArgs = @(
    "--registry-json", $tournamentProfileJsonPath,
    "--execution-handoff-json", $executionCalibrationHandoffJsonPath,
    "--requested-profile", $TournamentProfile,
    "--report-dir", $tournamentProfileRoot
)
Invoke-PythonStep -ScriptPath $tournamentProfileHandoffBuilderPath -Arguments $tournamentProfileHandoffArgs -FailureMessage "Failed to build tournament profile handoff."

if (-not (Test-Path $tournamentProfileHandoffJsonPath)) {
    throw "Tournament profile handoff JSON was not created at $tournamentProfileHandoffJsonPath"
}

$tournamentProfileRegistry = Read-JsonFile -Path $tournamentProfileJsonPath
$tournamentProfileHandoff = Read-JsonFile -Path $tournamentProfileHandoffJsonPath
$resolvedTournamentProfile = [string]$tournamentProfileHandoff.resolved_profile
$tournamentProfileResolutionMode = [string]$tournamentProfileHandoff.resolution_mode
$tournamentProfileResolutionWarning = [string]$tournamentProfileHandoff.resolution_warning

if ([string]::IsNullOrWhiteSpace($resolvedTournamentProfile)) {
    throw "Tournament profile handoff did not resolve a nightly profile."
}

$resolvedProfileSpec = $null
foreach ($profile in @($tournamentProfileRegistry.profiles)) {
    if ([string]$profile.profile_id -eq $resolvedTournamentProfile) {
        $resolvedProfileSpec = $profile
        break
    }
}
if ($null -eq $resolvedProfileSpec) {
    throw "Resolved tournament profile '$resolvedTournamentProfile' was not present in the tournament registry."
}
if (-not [bool]$resolvedProfileSpec.executable_now) {
    throw "Resolved tournament profile '$resolvedTournamentProfile' is not executable now."
}

$resolvedProgramLauncherName = [string]$resolvedProfileSpec.underlying_program
if ([string]::IsNullOrWhiteSpace($resolvedProgramLauncherName) -or $resolvedProgramLauncherName -eq "not_yet_wired") {
    throw "Resolved tournament profile '$resolvedTournamentProfile' does not have a governed underlying program."
}
$resolvedProgramLauncherPath = Join-Path $scriptRoot $resolvedProgramLauncherName
if (-not (Test-Path $resolvedProgramLauncherPath)) {
    throw "Resolved tournament profile '$resolvedTournamentProfile' points at a missing underlying program: $resolvedProgramLauncherPath"
}

$resolvedProgramExtraArgs = @()
switch ($resolvedTournamentProfile) {
    "opening_30m_premium_defense" {
        $resolvedProgramExtraArgs += @(
            "-Phase1StrategySet", "opening_window_premium_defense",
            "-Phase1SelectionProfile", "opening_window_defensive",
            "-Phase2StrategySet", "down_choppy_exhaustive",
            "-Phase2SelectionProfile", "down_choppy_focus",
            "-Phase1AllowedFamilies", "credit_call_spread,debit_put_spread,iron_condor,iron_butterfly,put_butterfly"
        )
    }
}

if (-not $discoverySourceWasExplicit) {
    $DiscoverySource = [string]$resolvedProfileSpec.discovery_source
}
if (-not $bootstrapReadyWasExplicit) {
    $BootstrapReadyUniverse = [bool]$resolvedProfileSpec.bootstrap_ready_universe
}

$cycleManifest.requested_tournament_profile = $TournamentProfile
$cycleManifest.resolved_tournament_profile = $resolvedTournamentProfile
$cycleManifest.tournament_profile_resolution_mode = $tournamentProfileResolutionMode
$cycleManifest.tournament_profile_resolution_warning = $tournamentProfileResolutionWarning
$cycleManifest.discovery_source = $DiscoverySource
$cycleManifest.bootstrap_ready_universe = [bool]$BootstrapReadyUniverse
$cycleManifest.execution_posture = [string]$tournamentProfileHandoff.execution_posture
$cycleManifest.execution_evidence_strength = [string]$tournamentProfileHandoff.execution_evidence_strength
$cycleManifest.tournament_profile_handoff_json = $tournamentProfileHandoffJsonPath
$cycleManifest.resolved_profile_strategy_sets = @($resolvedProfileSpec.strategy_sets)
$cycleManifest.resolved_profile_selection_profiles = @($resolvedProfileSpec.selection_profiles)
$cycleManifest.control_plane.program_launcher = $resolvedProgramLauncherPath
$cycleManifest.control_plane.profile_program_launcher = $resolvedProgramLauncherName
$cycleManifest.control_plane.profile_program_extra_args = @($resolvedProgramExtraArgs)
Write-JsonFile -Path $manifestPath -Payload $cycleManifest

Write-Status -Phase "resolved_tournament_profile" -Message "Resolved the nightly tournament profile from execution-aware policy." -Extra @{
    tournament_profile_json = $tournamentProfileJsonPath
    tournament_profile_handoff_json = $tournamentProfileHandoffJsonPath
    resolved_tournament_profile = $resolvedTournamentProfile
    tournament_profile_resolution_mode = $tournamentProfileResolutionMode
    tournament_profile_resolution_warning = $tournamentProfileResolutionWarning
    underlying_program = $resolvedProgramLauncherName
}

Write-Status -Phase "refreshing_tournament_unlocks" -Message "Refreshing the tournament unlock registry from current execution, session trust, and tournament policy."

$tournamentUnlockArgs = @(
    "--profile-registry-json", $tournamentProfileJsonPath,
    "--profile-handoff-json", $tournamentProfileHandoffJsonPath,
    "--execution-handoff-json", $executionCalibrationHandoffJsonPath,
    "--session-handoff-json", $sessionReconciliationHandoffJsonPath,
    "--report-dir", $tournamentUnlockRoot
)
Invoke-PythonStep -ScriptPath $tournamentUnlockBuilderPath -Arguments $tournamentUnlockArgs -FailureMessage "Failed to refresh tournament unlock registry."

$tournamentUnlockJsonPath = Join-Path $tournamentUnlockRoot "tournament_unlock_registry.json"
if (-not (Test-Path $tournamentUnlockJsonPath)) {
    throw "Tournament unlock registry JSON was not created at $tournamentUnlockJsonPath"
}

Write-Status -Phase "refreshing_tournament_unlock_handoff" -Message "Refreshing the tournament unlock steward handoff."

$tournamentUnlockHandoffArgs = @(
    "--registry-json", $tournamentUnlockJsonPath,
    "--report-dir", $tournamentUnlockRoot
)
Invoke-PythonStep -ScriptPath $tournamentUnlockHandoffBuilderPath -Arguments $tournamentUnlockHandoffArgs -FailureMessage "Failed to build tournament unlock handoff."

if (-not (Test-Path $tournamentUnlockHandoffJsonPath)) {
    throw "Tournament unlock handoff JSON was not created at $tournamentUnlockHandoffJsonPath"
}

Write-Status -Phase "refreshing_tournament_unlock_workplan" -Message "Refreshing the two-machine tournament unlock workplan."

$tournamentUnlockWorkplanArgs = @(
    "--unlock-registry-json", $tournamentUnlockJsonPath,
    "--unlock-handoff-json", $tournamentUnlockHandoffJsonPath,
    "--report-dir", $tournamentUnlockRoot
)
Invoke-PythonStep -ScriptPath $tournamentUnlockWorkplanBuilderPath -Arguments $tournamentUnlockWorkplanArgs -FailureMessage "Failed to refresh tournament unlock workplan."

if (-not (Test-Path $tournamentUnlockWorkplanJsonPath)) {
    throw "Tournament unlock workplan JSON was not created at $tournamentUnlockWorkplanJsonPath"
}

Write-Status -Phase "refreshing_tournament_unlock_workplan_handoff" -Message "Refreshing the tournament unlock workplan handoff."

$tournamentUnlockWorkplanHandoffArgs = @(
    "--workplan-json", $tournamentUnlockWorkplanJsonPath,
    "--report-dir", $tournamentUnlockRoot
)
Invoke-PythonStep -ScriptPath $tournamentUnlockWorkplanHandoffBuilderPath -Arguments $tournamentUnlockWorkplanHandoffArgs -FailureMessage "Failed to build tournament unlock workplan handoff."

if (-not (Test-Path $tournamentUnlockWorkplanHandoffJsonPath)) {
    throw "Tournament unlock workplan handoff JSON was not created at $tournamentUnlockWorkplanHandoffJsonPath"
}

Write-Status -Phase "refreshing_execution_evidence_contract" -Message "Refreshing the execution evidence contract for the next trusted paper session."

$executionEvidenceContractArgs = @(
    "--workplan-json", $tournamentUnlockWorkplanJsonPath,
    "--session-registry-json", $sessionReconciliationJsonPath,
    "--session-handoff-json", $sessionReconciliationHandoffJsonPath,
    "--execution-handoff-json", $executionCalibrationHandoffJsonPath,
    "--report-dir", $executionEvidenceRoot
)
Invoke-PythonStep -ScriptPath $executionEvidenceContractBuilderPath -Arguments $executionEvidenceContractArgs -FailureMessage "Failed to refresh execution evidence contract."

if (-not (Test-Path $executionEvidenceContractJsonPath)) {
    throw "Execution evidence contract JSON was not created at $executionEvidenceContractJsonPath"
}

Write-Status -Phase "refreshing_execution_evidence_contract_handoff" -Message "Refreshing the execution evidence contract handoff."

$executionEvidenceContractHandoffArgs = @(
    "--contract-json", $executionEvidenceContractJsonPath,
    "--report-dir", $executionEvidenceRoot
)
Invoke-PythonStep -ScriptPath $executionEvidenceContractHandoffBuilderPath -Arguments $executionEvidenceContractHandoffArgs -FailureMessage "Failed to refresh execution evidence contract handoff."

if (-not (Test-Path $executionEvidenceContractHandoffJsonPath)) {
    throw "Execution evidence contract handoff JSON was not created at $executionEvidenceContractHandoffJsonPath"
}

$cycleManifest.execution_evidence_contract_json = $executionEvidenceContractJsonPath
$cycleManifest.execution_evidence_contract_handoff_json = $executionEvidenceContractHandoffJsonPath
Write-JsonFile -Path $manifestPath -Payload $cycleManifest

Write-Status -Phase "refreshing_overnight_phased_plan" -Message "Refreshing the governed overnight phased plan from repo update, unlock, workplan, and execution evidence packets."

$overnightPhasedPlanArgs = @(
    "--repo-update-handoff-json", (Join-Path $repoRoot "docs\repo_updates\repo_update_handoff.json"),
    "--unlock-handoff-json", $tournamentUnlockHandoffJsonPath,
    "--workplan-handoff-json", $tournamentUnlockWorkplanHandoffJsonPath,
    "--execution-evidence-handoff-json", $executionEvidenceContractHandoffJsonPath,
    "--report-dir", $overnightPlanRoot
)
Invoke-PythonStep -ScriptPath $overnightPhasedPlanBuilderPath -Arguments $overnightPhasedPlanArgs -FailureMessage "Failed to refresh overnight phased plan."

if (-not (Test-Path $overnightPlanJsonPath)) {
    throw "Overnight phased plan JSON was not created at $overnightPlanJsonPath"
}

Write-Status -Phase "refreshing_overnight_phased_plan_handoff" -Message "Refreshing the overnight phased plan handoff."

$overnightPhasedPlanHandoffArgs = @(
    "--plan-json", $overnightPlanJsonPath,
    "--report-dir", $overnightPlanRoot
)
Invoke-PythonStep -ScriptPath $overnightPhasedPlanHandoffBuilderPath -Arguments $overnightPhasedPlanHandoffArgs -FailureMessage "Failed to refresh overnight phased plan handoff."

if (-not (Test-Path $overnightPlanHandoffJsonPath)) {
    throw "Overnight phased plan handoff JSON was not created at $overnightPlanHandoffJsonPath"
}

$cycleManifest.tournament_unlock_handoff_json = $tournamentUnlockHandoffJsonPath
$cycleManifest.tournament_unlock_workplan_handoff_json = $tournamentUnlockWorkplanHandoffJsonPath
$cycleManifest.execution_evidence_contract_handoff_json = $executionEvidenceContractHandoffJsonPath
$cycleManifest.overnight_phased_plan_json = $overnightPlanJsonPath
$cycleManifest.overnight_phased_plan_handoff_json = $overnightPlanHandoffJsonPath
Write-JsonFile -Path $manifestPath -Payload $cycleManifest

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
    $programArgs += @($resolvedProgramExtraArgs)
    Invoke-PowerShellStep -ScriptPath $resolvedProgramLauncherPath -Arguments $programArgs -FailureMessage "Failed to build nightly research program plan."

    Refresh-ActiveProgramReport
    Invoke-RunRegistryReport -ReportDir $runRegistryReportDir -ManifestRoots @($cycleRootPath, $programRootPath)

Write-Status -Phase "planned" -Message "Nightly operator cycle planned successfully." -Extra @{
        session_reconciliation_json = $sessionReconciliationJsonPath
        session_reconciliation_handoff_json = $sessionReconciliationHandoffJsonPath
        execution_calibration_json = $executionCalibrationJsonPath
        execution_calibration_handoff_json = $executionCalibrationHandoffJsonPath
        family_registry_json = $familyRegistryJsonPath
        family_handoff_json = $familyHandoffJsonPath
        tournament_profile_json = $tournamentProfileJsonPath
        tournament_profile_handoff_json = $tournamentProfileHandoffJsonPath
        tournament_unlock_json = $tournamentUnlockJsonPath
        tournament_unlock_handoff_json = $tournamentUnlockHandoffJsonPath
        tournament_unlock_workplan_json = $tournamentUnlockWorkplanJsonPath
        tournament_unlock_workplan_handoff_json = $tournamentUnlockWorkplanHandoffJsonPath
        execution_evidence_contract_json = $executionEvidenceContractJsonPath
        execution_evidence_contract_handoff_json = $executionEvidenceContractHandoffJsonPath
        resolved_tournament_profile = $resolvedTournamentProfile
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
$programArgs += @($resolvedProgramExtraArgs)
Invoke-PowerShellStep -ScriptPath $resolvedProgramLauncherPath -Arguments $programArgs -FailureMessage "Nightly discovery/exhaustive program failed."

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
    requested_tournament_profile = $TournamentProfile
    resolved_tournament_profile = $resolvedTournamentProfile
    tournament_profile_resolution_mode = $tournamentProfileResolutionMode
    tournament_profile_resolution_warning = $tournamentProfileResolutionWarning
    program_phase = $programPhase
    execution_calibration_json = $executionCalibrationJsonPath
    execution_calibration_handoff_json = $executionCalibrationHandoffJsonPath
    family_registry_json = $familyRegistryJsonPath
    family_handoff_json = $familyHandoffJsonPath
    tournament_profile_json = $tournamentProfileJsonPath
    tournament_profile_handoff_json = $tournamentProfileHandoffJsonPath
    tournament_unlock_json = $tournamentUnlockJsonPath
    tournament_unlock_handoff_json = $tournamentUnlockHandoffJsonPath
    tournament_unlock_workplan_json = $tournamentUnlockWorkplanJsonPath
    tournament_unlock_workplan_handoff_json = $tournamentUnlockWorkplanHandoffJsonPath
    execution_evidence_contract_json = $executionEvidenceContractJsonPath
    execution_evidence_contract_handoff_json = $executionEvidenceContractHandoffJsonPath
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
        session_reconciliation_json = $sessionReconciliationJsonPath
        session_reconciliation_handoff_json = $sessionReconciliationHandoffJsonPath
        execution_calibration_json = $executionCalibrationJsonPath
        execution_calibration_handoff_json = $executionCalibrationHandoffJsonPath
        family_registry_json = $familyRegistryJsonPath
        family_handoff_json = $familyHandoffJsonPath
        tournament_profile_json = $tournamentProfileJsonPath
        tournament_profile_handoff_json = $tournamentProfileHandoffJsonPath
        tournament_unlock_json = $tournamentUnlockJsonPath
        tournament_unlock_handoff_json = $tournamentUnlockHandoffJsonPath
        tournament_unlock_workplan_json = $tournamentUnlockWorkplanJsonPath
        tournament_unlock_workplan_handoff_json = $tournamentUnlockWorkplanHandoffJsonPath
        execution_evidence_contract_json = $executionEvidenceContractJsonPath
        execution_evidence_contract_handoff_json = $executionEvidenceContractHandoffJsonPath
        resolved_tournament_profile = $resolvedTournamentProfile
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
