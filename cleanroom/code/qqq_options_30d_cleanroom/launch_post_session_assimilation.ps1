[CmdletBinding()]
param(
    [string]$ControlPlaneRoot = "",
    [string]$RunnerRepoRoot = "",
    [string]$RuntimeRoot = "",
    [string]$SessionReconciliationDir = "",
    [string]$ExecutionCalibrationDir = "",
    [string]$TournamentProfileDir = "",
    [string]$TournamentUnlockDir = "",
    [string]$ExecutionEvidenceDir = "",
    [string]$OvernightPlanDir = "",
    [string]$MorningBriefDir = "",
    [switch]$MirrorToGcs,
    [string]$GcsPrefix = "gs://codexalpaca-control-us/gcp_foundation"
)

$ErrorActionPreference = "Stop"

function Resolve-PythonCommand {
    if (Get-Command py -ErrorAction SilentlyContinue) {
        return @("py", "-3")
    }
    if (Get-Command python -ErrorAction SilentlyContinue) {
        return @("python")
    }
    throw "No Python interpreter found on PATH. Install Python or expose `py`/`python` before post-session assimilation."
}

function Invoke-PythonScript {
    param(
        [string[]]$PythonCommand,
        [string]$ScriptPath,
        [string[]]$Arguments
    )
    $command = @($PythonCommand + @($ScriptPath) + $Arguments)
    & $command[0] $command[1..($command.Length - 1)]
}

if (-not $ControlPlaneRoot) {
    $ControlPlaneRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..\..")).Path
}

$workspaceRoot = Split-Path $ControlPlaneRoot -Parent
if (-not $RunnerRepoRoot) {
    $runnerCandidates = @(
        (Join-Path $workspaceRoot "codexalpaca_repo_gcp_lease_lane_refreshed"),
        (Join-Path $workspaceRoot "codexalpaca_repo")
    )
    foreach ($candidate in $runnerCandidates) {
        if (Test-Path $candidate) {
            $RunnerRepoRoot = (Resolve-Path $candidate).Path
            break
        }
    }
}
if (-not $RuntimeRoot) {
    $runtimeCandidate = Join-Path $workspaceRoot "codexalpaca_runtime\multi_ticker_portfolio_live"
    if (Test-Path $runtimeCandidate) {
        $RuntimeRoot = (Resolve-Path $runtimeCandidate).Path
    } else {
        $RuntimeRoot = $runtimeCandidate
    }
}

if (-not $RunnerRepoRoot) {
    throw "Runner repo root could not be resolved automatically."
}

if (-not $SessionReconciliationDir) {
    $SessionReconciliationDir = Join-Path $ControlPlaneRoot "docs\session_reconciliation"
}
if (-not $ExecutionCalibrationDir) {
    $ExecutionCalibrationDir = Join-Path $ControlPlaneRoot "docs\execution_calibration"
}
if (-not $TournamentProfileDir) {
    $TournamentProfileDir = Join-Path $ControlPlaneRoot "docs\tournament_profiles"
}
if (-not $TournamentUnlockDir) {
    $TournamentUnlockDir = Join-Path $ControlPlaneRoot "docs\tournament_unlocks"
}
if (-not $ExecutionEvidenceDir) {
    $ExecutionEvidenceDir = Join-Path $ControlPlaneRoot "docs\execution_evidence"
}
if (-not $OvernightPlanDir) {
    $OvernightPlanDir = Join-Path $ControlPlaneRoot "docs\overnight_plan"
}
if (-not $MorningBriefDir) {
    $MorningBriefDir = Join-Path $ControlPlaneRoot "docs\morning_brief"
}

$pythonCommand = Resolve-PythonCommand
$reportDir = Join-Path $ControlPlaneRoot "docs\gcp_foundation"
$builders = @{
    AssimilationStatus = Join-Path $PSScriptRoot "build_gcp_post_session_assimilation_status.py"
    SessionRegistry = Join-Path $PSScriptRoot "build_session_reconciliation_registry.py"
    SessionHandoff = Join-Path $PSScriptRoot "build_session_reconciliation_handoff.py"
    ExecutionRegistry = Join-Path $PSScriptRoot "build_execution_calibration_registry.py"
    ExecutionHandoff = Join-Path $PSScriptRoot "build_execution_calibration_handoff.py"
    TournamentProfileRegistry = Join-Path $PSScriptRoot "build_tournament_profile_registry.py"
    TournamentProfileHandoff = Join-Path $PSScriptRoot "build_tournament_profile_handoff.py"
    TournamentUnlockRegistry = Join-Path $PSScriptRoot "build_tournament_unlock_registry.py"
    TournamentUnlockHandoff = Join-Path $PSScriptRoot "build_tournament_unlock_handoff.py"
    TournamentUnlockWorkplan = Join-Path $PSScriptRoot "build_tournament_unlock_workplan.py"
    TournamentUnlockWorkplanHandoff = Join-Path $PSScriptRoot "build_tournament_unlock_workplan_handoff.py"
    ExecutionEvidenceContract = Join-Path $PSScriptRoot "build_execution_evidence_contract.py"
    ExecutionEvidenceContractHandoff = Join-Path $PSScriptRoot "build_execution_evidence_contract_handoff.py"
    OvernightPlan = Join-Path $PSScriptRoot "build_overnight_phased_plan.py"
    OvernightPlanHandoff = Join-Path $PSScriptRoot "build_overnight_phased_plan_handoff.py"
    MorningBrief = Join-Path $PSScriptRoot "build_morning_operator_brief.py"
    MorningBriefHandoff = Join-Path $PSScriptRoot "build_morning_operator_brief_handoff.py"
}

foreach ($builder in $builders.GetEnumerator()) {
    if (-not (Test-Path $builder.Value)) {
        throw "Builder not found: $($builder.Value)"
    }
}

$repoReportsRoot = Join-Path $RunnerRepoRoot "reports\multi_ticker_portfolio"
$preferredReportsRoot = $repoReportsRoot
$evidenceSourcePreference = "repo_mirror"
if ($RuntimeRoot -and (Test-Path (Join-Path $RuntimeRoot "runs")) -and (Test-Path (Join-Path $RuntimeRoot "state"))) {
    $preferredReportsRoot = $RuntimeRoot
    $evidenceSourcePreference = "runtime_live"
}
$sessionReportsRoot = Join-Path $preferredReportsRoot "runs"

Invoke-PythonScript -PythonCommand $pythonCommand -ScriptPath $builders.AssimilationStatus -Arguments @(
    "--runner-repo-root", $RunnerRepoRoot,
    "--runtime-root", $RuntimeRoot,
    "--report-dir", $reportDir,
    "--gcs-prefix", $GcsPrefix
)

Invoke-PythonScript -PythonCommand $pythonCommand -ScriptPath $builders.SessionRegistry -Arguments @(
    "--runner-repo-root", $RunnerRepoRoot,
    "--reports-root", $sessionReportsRoot,
    "--report-dir", $SessionReconciliationDir
)

Invoke-PythonScript -PythonCommand $pythonCommand -ScriptPath $builders.SessionHandoff -Arguments @(
    "--registry-json", (Join-Path $SessionReconciliationDir "session_reconciliation_registry.json"),
    "--report-dir", $SessionReconciliationDir
)

Invoke-PythonScript -PythonCommand $pythonCommand -ScriptPath $builders.ExecutionRegistry -Arguments @(
    "--runner-repo-root", $RunnerRepoRoot,
    "--reports-root", $preferredReportsRoot,
    "--report-dir", $ExecutionCalibrationDir,
    "--session-reconciliation-registry-json", (Join-Path $SessionReconciliationDir "session_reconciliation_registry.json"),
    "--session-reconciliation-handoff-json", (Join-Path $SessionReconciliationDir "session_reconciliation_handoff.json")
)

Invoke-PythonScript -PythonCommand $pythonCommand -ScriptPath $builders.ExecutionHandoff -Arguments @(
    "--registry-json", (Join-Path $ExecutionCalibrationDir "execution_calibration_registry.json"),
    "--report-dir", $ExecutionCalibrationDir
)

Invoke-PythonScript -PythonCommand $pythonCommand -ScriptPath $builders.TournamentProfileRegistry -Arguments @(
    "--report-dir", $TournamentProfileDir
)

Invoke-PythonScript -PythonCommand $pythonCommand -ScriptPath $builders.TournamentProfileHandoff -Arguments @(
    "--registry-json", (Join-Path $TournamentProfileDir "tournament_profile_registry.json"),
    "--execution-handoff-json", (Join-Path $ExecutionCalibrationDir "execution_calibration_handoff.json"),
    "--requested-profile", "auto",
    "--report-dir", $TournamentProfileDir
)

Invoke-PythonScript -PythonCommand $pythonCommand -ScriptPath $builders.TournamentUnlockRegistry -Arguments @(
    "--profile-registry-json", (Join-Path $TournamentProfileDir "tournament_profile_registry.json"),
    "--profile-handoff-json", (Join-Path $TournamentProfileDir "tournament_profile_handoff.json"),
    "--execution-handoff-json", (Join-Path $ExecutionCalibrationDir "execution_calibration_handoff.json"),
    "--session-handoff-json", (Join-Path $SessionReconciliationDir "session_reconciliation_handoff.json"),
    "--report-dir", $TournamentUnlockDir
)

Invoke-PythonScript -PythonCommand $pythonCommand -ScriptPath $builders.TournamentUnlockHandoff -Arguments @(
    "--registry-json", (Join-Path $TournamentUnlockDir "tournament_unlock_registry.json"),
    "--report-dir", $TournamentUnlockDir
)

Invoke-PythonScript -PythonCommand $pythonCommand -ScriptPath $builders.TournamentUnlockWorkplan -Arguments @(
    "--unlock-registry-json", (Join-Path $TournamentUnlockDir "tournament_unlock_registry.json"),
    "--unlock-handoff-json", (Join-Path $TournamentUnlockDir "tournament_unlock_handoff.json"),
    "--report-dir", $TournamentUnlockDir
)

Invoke-PythonScript -PythonCommand $pythonCommand -ScriptPath $builders.TournamentUnlockWorkplanHandoff -Arguments @(
    "--workplan-json", (Join-Path $TournamentUnlockDir "tournament_unlock_workplan.json"),
    "--report-dir", $TournamentUnlockDir
)

Invoke-PythonScript -PythonCommand $pythonCommand -ScriptPath $builders.ExecutionEvidenceContract -Arguments @(
    "--workplan-json", (Join-Path $TournamentUnlockDir "tournament_unlock_workplan.json"),
    "--session-registry-json", (Join-Path $SessionReconciliationDir "session_reconciliation_registry.json"),
    "--session-handoff-json", (Join-Path $SessionReconciliationDir "session_reconciliation_handoff.json"),
    "--execution-handoff-json", (Join-Path $ExecutionCalibrationDir "execution_calibration_handoff.json"),
    "--report-dir", $ExecutionEvidenceDir
)

Invoke-PythonScript -PythonCommand $pythonCommand -ScriptPath $builders.ExecutionEvidenceContractHandoff -Arguments @(
    "--contract-json", (Join-Path $ExecutionEvidenceDir "execution_evidence_contract.json"),
    "--report-dir", $ExecutionEvidenceDir
)

Invoke-PythonScript -PythonCommand $pythonCommand -ScriptPath $builders.OvernightPlan -Arguments @(
    "--repo-update-handoff-json", (Join-Path $ControlPlaneRoot "docs\repo_updates\repo_update_handoff.json"),
    "--unlock-handoff-json", (Join-Path $TournamentUnlockDir "tournament_unlock_handoff.json"),
    "--workplan-handoff-json", (Join-Path $TournamentUnlockDir "tournament_unlock_workplan_handoff.json"),
    "--execution-evidence-handoff-json", (Join-Path $ExecutionEvidenceDir "execution_evidence_contract_handoff.json"),
    "--report-dir", $OvernightPlanDir
)

Invoke-PythonScript -PythonCommand $pythonCommand -ScriptPath $builders.OvernightPlanHandoff -Arguments @(
    "--plan-json", (Join-Path $OvernightPlanDir "overnight_phased_plan.json"),
    "--report-dir", $OvernightPlanDir
)

Invoke-PythonScript -PythonCommand $pythonCommand -ScriptPath $builders.MorningBrief -Arguments @(
    "--repo-update-handoff-json", (Join-Path $ControlPlaneRoot "docs\repo_updates\repo_update_handoff.json"),
    "--session-handoff-json", (Join-Path $SessionReconciliationDir "session_reconciliation_handoff.json"),
    "--execution-handoff-json", (Join-Path $ExecutionCalibrationDir "execution_calibration_handoff.json"),
    "--profile-handoff-json", (Join-Path $TournamentProfileDir "tournament_profile_handoff.json"),
    "--unlock-handoff-json", (Join-Path $TournamentUnlockDir "tournament_unlock_handoff.json"),
    "--workplan-handoff-json", (Join-Path $TournamentUnlockDir "tournament_unlock_workplan_handoff.json"),
    "--evidence-handoff-json", (Join-Path $ExecutionEvidenceDir "execution_evidence_contract_handoff.json"),
    "--overnight-plan-handoff-json", (Join-Path $OvernightPlanDir "overnight_phased_plan_handoff.json"),
    "--report-dir", $MorningBriefDir
)

Invoke-PythonScript -PythonCommand $pythonCommand -ScriptPath $builders.MorningBriefHandoff -Arguments @(
    "--brief-json", (Join-Path $MorningBriefDir "morning_operator_brief.json"),
    "--report-dir", $MorningBriefDir
)

$status = @{
    generated_at = [datetime]::Now.ToString("o")
    control_plane_root = $ControlPlaneRoot
    runner_repo_root = $RunnerRepoRoot
    runtime_root = $RuntimeRoot
    preferred_reports_root = $preferredReportsRoot
    session_reports_root = $sessionReportsRoot
    evidence_source_preference = $evidenceSourcePreference
    session_reconciliation_handoff_json = Join-Path $SessionReconciliationDir "session_reconciliation_handoff.json"
    execution_calibration_handoff_json = Join-Path $ExecutionCalibrationDir "execution_calibration_handoff.json"
    tournament_profile_handoff_json = Join-Path $TournamentProfileDir "tournament_profile_handoff.json"
    tournament_unlock_handoff_json = Join-Path $TournamentUnlockDir "tournament_unlock_handoff.json"
    tournament_unlock_workplan_handoff_json = Join-Path $TournamentUnlockDir "tournament_unlock_workplan_handoff.json"
    execution_evidence_contract_handoff_json = Join-Path $ExecutionEvidenceDir "execution_evidence_contract_handoff.json"
    overnight_plan_handoff_json = Join-Path $OvernightPlanDir "overnight_phased_plan_handoff.json"
    morning_operator_brief_handoff_json = Join-Path $MorningBriefDir "morning_operator_brief_handoff.json"
    gcs_prefix = $GcsPrefix
}

$statusPath = Join-Path $MorningBriefDir "post_session_assimilation_status.json"
$status | ConvertTo-Json -Depth 4 | Set-Content -Path $statusPath -Encoding utf8

if ($MirrorToGcs) {
    if (-not (Get-Command gcloud -ErrorAction SilentlyContinue)) {
        throw "gcloud CLI not found on PATH. Install/authenticate gcloud or omit -MirrorToGcs."
    }
    $mirrorFiles = @(
        (Join-Path $reportDir "gcp_post_session_assimilation_status.json"),
        (Join-Path $reportDir "gcp_post_session_assimilation_status.md"),
        (Join-Path $reportDir "gcp_post_session_assimilation_handoff.md"),
        (Join-Path $reportDir "gcp_execution_exclusive_window_status.json"),
        (Join-Path $reportDir "gcp_execution_exclusive_window_status.md"),
        (Join-Path $reportDir "gcp_execution_exclusive_window_handoff.md"),
        (Join-Path $reportDir "gcp_execution_trusted_validation_session_status.json"),
        (Join-Path $reportDir "gcp_execution_trusted_validation_session_status.md"),
        (Join-Path $reportDir "gcp_execution_trusted_validation_launch_pack.json"),
        (Join-Path $reportDir "gcp_execution_trusted_validation_launch_pack.md"),
        (Join-Path $reportDir "gcp_execution_trusted_validation_launch_handoff.md")
    )
    & gcloud storage cp @mirrorFiles $GcsPrefix
}

Get-Content $statusPath
