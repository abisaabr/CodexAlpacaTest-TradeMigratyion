[CmdletBinding()]
param(
    [string]$ControlPlaneRoot = "",
    [string]$RunnerRepoRoot = "",
    [string]$SessionReconciliationDir = "",
    [string]$ExecutionCalibrationDir = "",
    [string]$TournamentProfileDir = "",
    [string]$TournamentUnlockDir = "",
    [string]$ExecutionEvidenceDir = "",
    [string]$OvernightPlanDir = "",
    [string]$MorningBriefDir = ""
)

$ErrorActionPreference = "Stop"

if (-not $ControlPlaneRoot) {
    $ControlPlaneRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..\..")).Path
}

if (-not $RunnerRepoRoot) {
    $candidate = Join-Path (Split-Path $ControlPlaneRoot -Parent) "codexalpaca_repo"
    if (Test-Path $candidate) {
        $RunnerRepoRoot = (Resolve-Path $candidate).Path
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

$reportsRoot = Join-Path $RunnerRepoRoot "reports\multi_ticker_portfolio"
$sessionReportsRoot = Join-Path $reportsRoot "runs"

$builders = @{
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

python $builders.SessionRegistry `
    --runner-repo-root $RunnerRepoRoot `
    --reports-root $sessionReportsRoot `
    --report-dir $SessionReconciliationDir

python $builders.SessionHandoff `
    --registry-json (Join-Path $SessionReconciliationDir "session_reconciliation_registry.json") `
    --report-dir $SessionReconciliationDir

python $builders.ExecutionRegistry `
    --runner-repo-root $RunnerRepoRoot `
    --reports-root $reportsRoot `
    --report-dir $ExecutionCalibrationDir `
    --session-reconciliation-registry-json (Join-Path $SessionReconciliationDir "session_reconciliation_registry.json") `
    --session-reconciliation-handoff-json (Join-Path $SessionReconciliationDir "session_reconciliation_handoff.json")

python $builders.ExecutionHandoff `
    --registry-json (Join-Path $ExecutionCalibrationDir "execution_calibration_registry.json") `
    --report-dir $ExecutionCalibrationDir

python $builders.TournamentProfileRegistry `
    --report-dir $TournamentProfileDir

python $builders.TournamentProfileHandoff `
    --registry-json (Join-Path $TournamentProfileDir "tournament_profile_registry.json") `
    --execution-handoff-json (Join-Path $ExecutionCalibrationDir "execution_calibration_handoff.json") `
    --requested-profile auto `
    --report-dir $TournamentProfileDir

python $builders.TournamentUnlockRegistry `
    --profile-registry-json (Join-Path $TournamentProfileDir "tournament_profile_registry.json") `
    --profile-handoff-json (Join-Path $TournamentProfileDir "tournament_profile_handoff.json") `
    --execution-handoff-json (Join-Path $ExecutionCalibrationDir "execution_calibration_handoff.json") `
    --session-handoff-json (Join-Path $SessionReconciliationDir "session_reconciliation_handoff.json") `
    --report-dir $TournamentUnlockDir

python $builders.TournamentUnlockHandoff `
    --registry-json (Join-Path $TournamentUnlockDir "tournament_unlock_registry.json") `
    --report-dir $TournamentUnlockDir

python $builders.TournamentUnlockWorkplan `
    --unlock-registry-json (Join-Path $TournamentUnlockDir "tournament_unlock_registry.json") `
    --unlock-handoff-json (Join-Path $TournamentUnlockDir "tournament_unlock_handoff.json") `
    --report-dir $TournamentUnlockDir

python $builders.TournamentUnlockWorkplanHandoff `
    --workplan-json (Join-Path $TournamentUnlockDir "tournament_unlock_workplan.json") `
    --report-dir $TournamentUnlockDir

python $builders.ExecutionEvidenceContract `
    --workplan-json (Join-Path $TournamentUnlockDir "tournament_unlock_workplan.json") `
    --session-registry-json (Join-Path $SessionReconciliationDir "session_reconciliation_registry.json") `
    --session-handoff-json (Join-Path $SessionReconciliationDir "session_reconciliation_handoff.json") `
    --execution-handoff-json (Join-Path $ExecutionCalibrationDir "execution_calibration_handoff.json") `
    --report-dir $ExecutionEvidenceDir

python $builders.ExecutionEvidenceContractHandoff `
    --contract-json (Join-Path $ExecutionEvidenceDir "execution_evidence_contract.json") `
    --report-dir $ExecutionEvidenceDir

python $builders.OvernightPlan `
    --repo-update-handoff-json (Join-Path $ControlPlaneRoot "docs\repo_updates\repo_update_handoff.json") `
    --unlock-handoff-json (Join-Path $TournamentUnlockDir "tournament_unlock_handoff.json") `
    --workplan-handoff-json (Join-Path $TournamentUnlockDir "tournament_unlock_workplan_handoff.json") `
    --execution-evidence-handoff-json (Join-Path $ExecutionEvidenceDir "execution_evidence_contract_handoff.json") `
    --report-dir $OvernightPlanDir

python $builders.OvernightPlanHandoff `
    --plan-json (Join-Path $OvernightPlanDir "overnight_phased_plan.json") `
    --report-dir $OvernightPlanDir

python $builders.MorningBrief `
    --repo-update-handoff-json (Join-Path $ControlPlaneRoot "docs\repo_updates\repo_update_handoff.json") `
    --session-handoff-json (Join-Path $SessionReconciliationDir "session_reconciliation_handoff.json") `
    --execution-handoff-json (Join-Path $ExecutionCalibrationDir "execution_calibration_handoff.json") `
    --profile-handoff-json (Join-Path $TournamentProfileDir "tournament_profile_handoff.json") `
    --unlock-handoff-json (Join-Path $TournamentUnlockDir "tournament_unlock_handoff.json") `
    --workplan-handoff-json (Join-Path $TournamentUnlockDir "tournament_unlock_workplan_handoff.json") `
    --evidence-handoff-json (Join-Path $ExecutionEvidenceDir "execution_evidence_contract_handoff.json") `
    --overnight-plan-handoff-json (Join-Path $OvernightPlanDir "overnight_phased_plan_handoff.json") `
    --report-dir $MorningBriefDir

python $builders.MorningBriefHandoff `
    --brief-json (Join-Path $MorningBriefDir "morning_operator_brief.json") `
    --report-dir $MorningBriefDir

$status = @{
    generated_at = [datetime]::Now.ToString("o")
    control_plane_root = $ControlPlaneRoot
    runner_repo_root = $RunnerRepoRoot
    session_reconciliation_handoff_json = Join-Path $SessionReconciliationDir "session_reconciliation_handoff.json"
    execution_calibration_handoff_json = Join-Path $ExecutionCalibrationDir "execution_calibration_handoff.json"
    tournament_profile_handoff_json = Join-Path $TournamentProfileDir "tournament_profile_handoff.json"
    tournament_unlock_handoff_json = Join-Path $TournamentUnlockDir "tournament_unlock_handoff.json"
    tournament_unlock_workplan_handoff_json = Join-Path $TournamentUnlockDir "tournament_unlock_workplan_handoff.json"
    execution_evidence_contract_handoff_json = Join-Path $ExecutionEvidenceDir "execution_evidence_contract_handoff.json"
    overnight_plan_handoff_json = Join-Path $OvernightPlanDir "overnight_phased_plan_handoff.json"
    morning_operator_brief_handoff_json = Join-Path $MorningBriefDir "morning_operator_brief_handoff.json"
}

$statusPath = Join-Path $MorningBriefDir "post_session_assimilation_status.json"
$status | ConvertTo-Json -Depth 4 | Set-Content -Path $statusPath -Encoding utf8
Get-Content $statusPath
