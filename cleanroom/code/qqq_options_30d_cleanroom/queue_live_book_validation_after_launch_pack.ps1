param(
    [string]$PackPath,
    [string]$ProgramRoot,
    [string]$ValidationOutputDir = "",
    [string]$ReviewOutputDir = "",
    [string]$LiveManifestPath = "C:\Users\rabisaab\Downloads\codexalpaca_repo\config\strategy_manifests\multi_ticker_portfolio_live.yaml",
    [string]$PaperRunnerGatePath = "",
    [string]$PaperRunnerTargetDate = "",
    [int]$PollSeconds = 60,
    [int]$TimeoutMinutes = 720
)

$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($PackPath)) {
    throw "PackPath is required."
}
if ([string]::IsNullOrWhiteSpace($ProgramRoot)) {
    throw "ProgramRoot is required."
}

$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = [System.IO.Path]::GetFullPath((Join-Path $scriptRoot "..\..\.."))
$packFile = [System.IO.Path]::GetFullPath($PackPath)
$packRoot = Split-Path -Parent $packFile
$launchStatusPath = Join-Path $packRoot "launch_status.json"
$programRootPath = [System.IO.Path]::GetFullPath($ProgramRoot)
$cycleRootPath = Split-Path -Parent $programRootPath

$validatorPath = Join-Path $scriptRoot "validate_program_live_book.py"
$hardeningBuilderPath = Join-Path $scriptRoot "build_live_book_hardening_review.py"
$replacementBuilderPath = Join-Path $scriptRoot "build_live_book_replacement_plan.py"
$morningHandoffBuilderPath = Join-Path $scriptRoot "build_live_book_morning_handoff.py"
$runRegistryReporterPath = Join-Path $scriptRoot "build_run_registry_report.py"
$activeProgramReporterPath = Join-Path $scriptRoot "build_active_program_report.py"
$defaultOutputRoot = Join-Path $repoRoot "output"
$defaultRegistryPath = Join-Path $defaultOutputRoot "run_registry.jsonl"
$programStatusPath = Join-Path $programRootPath "program_status.json"
$cycleStatusPath = Join-Path $cycleRootPath "nightly_operator_cycle_status.json"

if ([string]::IsNullOrWhiteSpace($ValidationOutputDir)) {
    $validationRoot = Join-Path $programRootPath "live_book_validation"
}
else {
    $validationRoot = [System.IO.Path]::GetFullPath($ValidationOutputDir)
}

if ([string]::IsNullOrWhiteSpace($ReviewOutputDir)) {
    $reviewRoot = Join-Path $validationRoot "hardening_review"
}
else {
    $reviewRoot = [System.IO.Path]::GetFullPath($ReviewOutputDir)
}
$replacementPlanRoot = Join-Path $reviewRoot "replacement_plan"
$morningHandoffRoot = Join-Path $reviewRoot "morning_handoff"

$statusPath = Join-Path $programRootPath "phase2_resume_followon_status.json"
$logPath = Join-Path $programRootPath "phase2_resume_followon.log"
$runRegistryReportDir = Join-Path $programRootPath "phase2_resume_run_registry_report"
$activeProgramReportDir = Join-Path $cycleRootPath "active_program_report"
$deadline = (Get-Date).AddMinutes($TimeoutMinutes)

New-Item -ItemType Directory -Force -Path $validationRoot | Out-Null
New-Item -ItemType Directory -Force -Path $reviewRoot | Out-Null
New-Item -ItemType Directory -Force -Path $replacementPlanRoot | Out-Null
New-Item -ItemType Directory -Force -Path $morningHandoffRoot | Out-Null
New-Item -ItemType Directory -Force -Path $runRegistryReportDir | Out-Null
New-Item -ItemType Directory -Force -Path $activeProgramReportDir | Out-Null

if ([string]::IsNullOrWhiteSpace($PaperRunnerGatePath)) {
    $PaperRunnerGatePath = Join-Path $defaultOutputRoot "paper_runner_gate.json"
}
else {
    $PaperRunnerGatePath = [System.IO.Path]::GetFullPath($PaperRunnerGatePath)
}

function Get-NextWeekdayDate {
    $candidate = (Get-Date).Date.AddDays(1)
    while ($candidate.DayOfWeek -in @([System.DayOfWeek]::Saturday, [System.DayOfWeek]::Sunday)) {
        $candidate = $candidate.AddDays(1)
    }
    return $candidate.ToString("yyyy-MM-dd")
}

if ([string]::IsNullOrWhiteSpace($PaperRunnerTargetDate)) {
    $PaperRunnerTargetDate = Get-NextWeekdayDate
}

function Write-Log {
    param([string]$Message)
    $timestamp = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
    Add-Content -Path $logPath -Value "[$timestamp] $Message"
}

function Ensure-Property {
    param(
        [object]$Target,
        [string]$Name,
        [object]$Value
    )
    if ($Target.PSObject.Properties.Name -contains $Name) {
        $Target.$Name = $Value
    }
    else {
        $Target | Add-Member -NotePropertyName $Name -NotePropertyValue $Value
    }
}

function Refresh-ActiveProgramReport {
    if (-not (Test-Path $activeProgramReporterPath)) {
        return
    }
    try {
        & python $activeProgramReporterPath --program-root $programRootPath --report-dir $activeProgramReportDir | Out-Null
    }
    catch {
        Write-Log "warning: failed to refresh active program report: $($_.Exception.Message)"
    }
}

function Update-UpstreamStatus {
    param(
        [string]$FollowonPhase,
        [string]$Message
    )

    $timestamp = (Get-Date).ToString("o")
    $upstreamPhase =
        switch ($FollowonPhase) {
            "validating" { "validating" }
            "reviewing" { "reviewing" }
            "planning_replacement" { "planning_replacement" }
            "building_morning_handoff" { "building_morning_handoff" }
            "completed" { "completed" }
            "failed" { "failed" }
            default { "phase2_resume_running" }
        }

    $repairContext = [pscustomobject]@{
        resumed_from_phase1_artifacts = $true
        launch_status_path = $launchStatusPath
        phase2_resume_followon_status_path = $statusPath
    }

    if (Test-Path $programStatusPath) {
        $programStatus = Get-Content -Path $programStatusPath -Raw | ConvertFrom-Json
    }
    else {
        $programStatus = [pscustomobject]@{}
    }
    Ensure-Property -Target $programStatus -Name "phase" -Value $upstreamPhase
    Ensure-Property -Target $programStatus -Name "updated_at" -Value $timestamp
    Ensure-Property -Target $programStatus -Name "message" -Value $Message
    Ensure-Property -Target $programStatus -Name "phase2_resume_followon_status_path" -Value $statusPath
    Ensure-Property -Target $programStatus -Name "repair_context" -Value $repairContext
    ($programStatus | ConvertTo-Json -Depth 8) | Set-Content -Path $programStatusPath

    if (Test-Path $cycleStatusPath) {
        $cycleStatus = Get-Content -Path $cycleStatusPath -Raw | ConvertFrom-Json
    }
    else {
        $cycleStatus = [pscustomobject]@{}
    }
    Ensure-Property -Target $cycleStatus -Name "phase" -Value $upstreamPhase
    Ensure-Property -Target $cycleStatus -Name "updated_at" -Value $timestamp
    Ensure-Property -Target $cycleStatus -Name "message" -Value $Message
    Ensure-Property -Target $cycleStatus -Name "program_status_path" -Value $programStatusPath
    Ensure-Property -Target $cycleStatus -Name "phase2_resume_followon_status_path" -Value $statusPath
    Ensure-Property -Target $cycleStatus -Name "recovered_from_program_failure" -Value $true
    ($cycleStatus | ConvertTo-Json -Depth 8) | Set-Content -Path $cycleStatusPath

    Refresh-ActiveProgramReport
}

function Write-Status {
    param(
        [string]$Phase,
        [string]$Message
    )
    $payload = [ordered]@{
        phase = $Phase
        message = $Message
        updated_at = (Get-Date).ToString("o")
        pack_path = $packFile
        launch_status_path = $launchStatusPath
        program_root = $programRootPath
        validation_output_dir = $validationRoot
        review_output_dir = $reviewRoot
        replacement_plan_output_dir = $replacementPlanRoot
        morning_handoff_output_dir = $morningHandoffRoot
        run_registry_report_dir = $runRegistryReportDir
    }
    $payload | ConvertTo-Json -Depth 6 | Set-Content -Path $statusPath
    Update-UpstreamStatus -FollowonPhase $Phase -Message $Message
}

function Write-PaperRunnerGate {
    param(
        [string]$Status,
        [string]$Phase,
        [string]$Message
    )

    $gateDir = Split-Path -Parent $PaperRunnerGatePath
    if (-not [string]::IsNullOrWhiteSpace($gateDir)) {
        New-Item -ItemType Directory -Force -Path $gateDir | Out-Null
    }

    $payload = [ordered]@{
        status = $Status
        phase = $Phase
        message = $Message
        target_trade_date = $PaperRunnerTargetDate
        updated_at = (Get-Date).ToString("o")
        program_root = $programRootPath
        pack_path = $packFile
        launch_status_path = $launchStatusPath
        validation_output_dir = $validationRoot
        review_output_dir = $reviewRoot
        replacement_plan_output_dir = $replacementPlanRoot
        morning_handoff_output_dir = $morningHandoffRoot
        followon_status_path = $statusPath
    }
    $payload | ConvertTo-Json -Depth 6 | Set-Content -Path $PaperRunnerGatePath
}

function Invoke-RunRegistryReport {
    if (-not (Test-Path $runRegistryReporterPath)) {
        return
    }
    $reportArgs = @(
        $runRegistryReporterPath,
        "--output-root", $defaultOutputRoot,
        "--registry-path", $defaultRegistryPath,
        "--report-dir", $runRegistryReportDir
    )
    foreach ($root in @($programRootPath, $validationRoot, $reviewRoot, $packRoot)) {
        if (Test-Path $root) {
            $reportArgs += @("--manifest-root", $root)
        }
    }
    try {
        & python @reportArgs | Out-Null
    }
    catch {
        Write-Log "warning: failed to refresh run registry report: $($_.Exception.Message)"
    }
}

function Get-LaunchPayload {
    if (-not (Test-Path $launchStatusPath)) {
        return $null
    }
    try {
        return Get-Content $launchStatusPath -Raw | ConvertFrom-Json
    }
    catch {
        return $null
    }
}

function Test-LaneProcessRunning {
    param([object]$Row)
    $pidValue = 0
    try {
        $pidValue = [int]$Row.pid
    }
    catch {
        return $false
    }
    return $null -ne (Get-Process -Id $pidValue -ErrorAction SilentlyContinue)
}

function Summarize-LaneRows {
    param([object[]]$Rows)
    $runningRows = @($Rows | Where-Object { Test-LaneProcessRunning $_ })
    $runningLaneIds = @($runningRows | ForEach-Object { [string]$_.lane_id })
    return [ordered]@{
        running_count = $runningRows.Count
        running_lane_ids = $runningLaneIds
    }
}

Write-Log "Waiting for phase 2 launch pack completion in $packRoot"
Write-Status -Phase "waiting" -Message "Waiting for the Phase 2 launch pack to reach a terminal state."
Write-PaperRunnerGate -Status "pending" -Phase "waiting" -Message "Waiting for the Phase 2 launch pack to reach a terminal state."
Invoke-RunRegistryReport

$launchPayload = $null
$recoveredPhase2Completion = $false
while ((Get-Date) -lt $deadline) {
    $launchPayload = Get-LaunchPayload
    if ($null -eq $launchPayload) {
        Start-Sleep -Seconds $PollSeconds
        continue
    }

    $phase = [string]$launchPayload.phase
    if ($phase -eq "completed") {
        $failedRows = @(
            @($launchPayload.rows) | Where-Object {
                ([int]$_.exit_code) -ne 0 -or (-not [bool]$_.has_master_summary)
            }
        )
        if ($failedRows.Count -gt 0) {
            $failedLaneIds = @($failedRows | ForEach-Object { [string]$_.lane_id })
            Write-Log ("Phase 2 launch pack completed with failing lanes: " + ($failedLaneIds -join ", "))
            Write-Status -Phase "failed" -Message ("Phase 2 launch pack completed with failing lanes: " + ($failedLaneIds -join ", "))
            Write-PaperRunnerGate -Status "failed" -Phase "failed" -Message ("Phase 2 launch pack completed with failing lanes: " + ($failedLaneIds -join ", "))
            Invoke-RunRegistryReport
            exit 2
        }
        Write-Log "Phase 2 launch pack completed successfully. Starting live-book validation."
        break
    }
    if ($phase -in @("started", "running")) {
        $rows = @($launchPayload.rows)
        if ($rows.Count -gt 0) {
            $laneSummary = Summarize-LaneRows $rows
            $runningRows = @($rows | Where-Object { Test-LaneProcessRunning $_ })
            if ($laneSummary.running_count -gt 0) {
                $laneText = if ($laneSummary.running_lane_ids.Count -gt 0) { $laneSummary.running_lane_ids -join ", " } else { "active lanes" }
                Write-Status -Phase "phase2_running" -Message ("Phase 2 lanes still running: " + $laneText)
                Write-PaperRunnerGate -Status "pending" -Phase "phase2_running" -Message ("Phase 2 lanes still running: " + $laneText)
            }
            if ($runningRows.Count -eq 0) {
                $failedRows = @(
                    $rows | Where-Object {
                        $researchDir = [string]$_.research_dir
                        -not (Test-Path (Join-Path $researchDir "master_summary.json"))
                    }
                )
                if ($failedRows.Count -gt 0) {
                    $failedLaneIds = @($failedRows | ForEach-Object { [string]$_.lane_id })
                    Write-Log ("Phase 2 lane runners exited without required outputs: " + ($failedLaneIds -join ", "))
                    Write-Status -Phase "failed" -Message ("Phase 2 lane runners exited without required outputs: " + ($failedLaneIds -join ", "))
                    Write-PaperRunnerGate -Status "failed" -Phase "failed" -Message ("Phase 2 lane runners exited without required outputs: " + ($failedLaneIds -join ", "))
                    Invoke-RunRegistryReport
                    exit 5
                }
                Write-Log "Phase 2 lane runners exited cleanly with master_summary artifacts. Starting live-book validation."
                $recoveredPhase2Completion = $true
                break
            }
        }
    }
    if ($phase -eq "preflight_failed") {
        Write-Log "Phase 2 launch pack failed preflight."
        Write-Status -Phase "failed" -Message "Phase 2 launch pack failed preflight."
        Write-PaperRunnerGate -Status "failed" -Phase "failed" -Message "Phase 2 launch pack failed preflight."
        Invoke-RunRegistryReport
        exit 3
    }
    Start-Sleep -Seconds $PollSeconds
}

if ($null -eq $launchPayload -or (([string]$launchPayload.phase -ne "completed") -and (-not $recoveredPhase2Completion))) {
    Write-Log "Timed out waiting for the Phase 2 launch pack to complete."
    Write-Status -Phase "failed" -Message "Timed out waiting for the Phase 2 launch pack to complete."
    Write-PaperRunnerGate -Status "failed" -Phase "failed" -Message "Timed out waiting for the Phase 2 launch pack to complete."
    Invoke-RunRegistryReport
    exit 4
}

Write-Status -Phase "validating" -Message "Running live-book validation against the current manifest."
Write-PaperRunnerGate -Status "pending" -Phase "validating" -Message "Running live-book validation against the current manifest."
Invoke-RunRegistryReport

& python $validatorPath `
    --program-root $programRootPath `
    --output-dir $validationRoot `
    --live-manifest $LiveManifestPath

if ($LASTEXITCODE -ne 0) {
    $validationExitCode = $LASTEXITCODE
    Write-Log "Live-book validation failed with exit code $validationExitCode."
    Write-Status -Phase "failed" -Message "Live-book validation failed."
    Write-PaperRunnerGate -Status "failed" -Phase "failed" -Message "Live-book validation failed."
    Invoke-RunRegistryReport
    exit $validationExitCode
}

Write-Status -Phase "reviewing" -Message "Building live-book hardening review packet."
Write-PaperRunnerGate -Status "pending" -Phase "reviewing" -Message "Building live-book hardening review packet."
Invoke-RunRegistryReport

& python $hardeningBuilderPath `
    --validation-dir $validationRoot `
    --output-dir $reviewRoot `
    --live-manifest $LiveManifestPath

if ($LASTEXITCODE -ne 0) {
    $reviewExitCode = $LASTEXITCODE
    Write-Log "Hardening review build failed with exit code $reviewExitCode."
    Write-Status -Phase "failed" -Message "Hardening review build failed."
    Write-PaperRunnerGate -Status "failed" -Phase "failed" -Message "Hardening review build failed."
    Invoke-RunRegistryReport
    exit $reviewExitCode
}

Write-Status -Phase "planning_replacement" -Message "Building live-book replacement plan."
Write-PaperRunnerGate -Status "pending" -Phase "planning_replacement" -Message "Building live-book replacement plan."
Invoke-RunRegistryReport

& python $replacementBuilderPath `
    --validation-dir $validationRoot `
    --review-dir $reviewRoot `
    --output-dir $replacementPlanRoot `
    --live-manifest $LiveManifestPath

if ($LASTEXITCODE -ne 0) {
    $replacementExitCode = $LASTEXITCODE
    Write-Log "Replacement plan build failed with exit code $replacementExitCode."
    Write-Status -Phase "failed" -Message "Replacement plan build failed."
    Write-PaperRunnerGate -Status "failed" -Phase "failed" -Message "Replacement plan build failed."
    Invoke-RunRegistryReport
    exit $replacementExitCode
}

Write-Status -Phase "building_morning_handoff" -Message "Building morning handoff packet."
Write-PaperRunnerGate -Status "pending" -Phase "building_morning_handoff" -Message "Building morning handoff packet."
Invoke-RunRegistryReport

& python $morningHandoffBuilderPath `
    --validation-dir $validationRoot `
    --review-dir $reviewRoot `
    --replacement-plan-dir $replacementPlanRoot `
    --output-dir $morningHandoffRoot

if ($LASTEXITCODE -ne 0) {
    $handoffExitCode = $LASTEXITCODE
    Write-Log "Morning handoff build failed with exit code $handoffExitCode."
    Write-Status -Phase "failed" -Message "Morning handoff build failed."
    Write-PaperRunnerGate -Status "failed" -Phase "failed" -Message "Morning handoff build failed."
    Invoke-RunRegistryReport
    exit $handoffExitCode
}

Write-Log "Phase 2 follow-on validation, hardening review, replacement plan, and morning handoff completed successfully."
Write-Status -Phase "completed" -Message "Phase 2 follow-on validation, hardening review, replacement plan, and morning handoff completed successfully."
Write-PaperRunnerGate -Status "completed" -Phase "completed" -Message "Phase 2 follow-on validation, hardening review, replacement plan, and morning handoff completed successfully."
Invoke-RunRegistryReport
exit 0
