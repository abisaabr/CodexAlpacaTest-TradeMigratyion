param(
    [string]$ProgramRoot,
    [string]$CycleRoot = "",
    [string]$PythonExe = "python",
    [string]$LiveManifestPath = "C:\Users\rabisaab\Downloads\codexalpaca_repo\config\strategy_manifests\multi_ticker_portfolio_live.yaml",
    [switch]$Execute,
    [switch]$Wait,
    [switch]$StartFollowon = $true
)

$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($ProgramRoot)) {
    throw "ProgramRoot is required."
}

$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = [System.IO.Path]::GetFullPath((Join-Path $scriptRoot "..\..\.."))
$programRootPath = [System.IO.Path]::GetFullPath($ProgramRoot)
$cycleRootPath =
    if ([string]::IsNullOrWhiteSpace($CycleRoot)) {
        Split-Path -Parent $programRootPath
    }
    else {
        [System.IO.Path]::GetFullPath($CycleRoot)
    }

$programManifestPath = Join-Path $programRootPath "program_manifest.json"
$programStatusPath = Join-Path $programRootPath "program_status.json"
$cycleStatusPath = Join-Path $cycleRootPath "nightly_operator_cycle_status.json"
$phase1StatusPath = Join-Path $programRootPath "phase1_status.json"
$phase2StatusPath = Join-Path $programRootPath "phase2_status.json"
$phase2Root = Join-Path $programRootPath "phase2"
$phase2PackRoot = Join-Path $phase2Root "launch_pack"
$phase2PackPath = Join-Path $phase2PackRoot "phase2_agent_wave_pack.json"
$phase2LaunchStatusPath = Join-Path $phase2PackRoot "launch_status.json"
$phase2PlanPath = Join-Path $programRootPath "shortlist\phase2_plan.json"
$shortlistJsonPath = Join-Path $programRootPath "shortlist\family_wave_shortlist.json"
$agentShardingPlanRoot = Join-Path $programRootPath "agent_sharding_plan"
$agentOperatingModelRoot = Join-Path $programRootPath "agent_operating_model"
$agentShardingPlanPath = Join-Path $agentShardingPlanRoot "agent_sharding_plan.json"
$agentOperatingModelPath = Join-Path $agentOperatingModelRoot "agent_operating_model.json"
$resumeLogPath = Join-Path $programRootPath "phase2_resume.log"
$resumeStatusPath = Join-Path $programRootPath "phase2_resume_status.json"
$resumeFollowonStatusPath = Join-Path $programRootPath "phase2_resume_followon_status.json"

$agentShardingPlanBuilderPath = Join-Path $scriptRoot "build_agent_sharding_plan.py"
$agentOperatingModelBuilderPath = Join-Path $scriptRoot "build_agent_operating_model.py"
$phase2PackBuilderPath = Join-Path $scriptRoot "build_phase2_agent_wave_pack.py"
$launchAgentWavePath = Join-Path $scriptRoot "launch_agent_wave.ps1"
$queueFollowonPath = Join-Path $scriptRoot "queue_live_book_validation_after_launch_pack.ps1"

function Write-Log {
    param([string]$Message)
    $timestamp = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
    Add-Content -Path $resumeLogPath -Value "[$timestamp] $Message"
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

function Invoke-PythonStep {
    param(
        [string]$ScriptPath,
        [string[]]$Arguments,
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
        [string[]]$Arguments,
        [string]$FailureMessage
    )
    & powershell -NoProfile -ExecutionPolicy Bypass -File $ScriptPath @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw $FailureMessage
    }
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

function Update-ProgramAndCycleStatus {
    param(
        [string]$Phase,
        [string]$Message
    )

    $timestamp = (Get-Date).ToString("o")
    $repairContext = [pscustomobject]@{
        resumed_from_phase1_artifacts = $true
        phase2_pack_path = $phase2PackPath
        phase2_launch_status_path = $phase2LaunchStatusPath
        phase2_resume_status_path = $resumeStatusPath
        phase2_resume_followon_status_path = $resumeFollowonStatusPath
    }

    $resumePayload = [ordered]@{
        phase = $Phase
        message = $Message
        updated_at = $timestamp
        execute = [bool]$Execute
        wait = [bool]$Wait
        program_root = $programRootPath
        cycle_root = $cycleRootPath
        phase1_status_path = $phase1StatusPath
        phase2_plan_path = $phase2PlanPath
        phase2_pack_path = $phase2PackPath
        phase2_launch_status_path = $phase2LaunchStatusPath
        phase2_resume_followon_status_path = $resumeFollowonStatusPath
    }
    Write-JsonFile -Path $resumeStatusPath -Payload $resumePayload

    if (Test-Path $programStatusPath) {
        $programStatus = Get-Content -Path $programStatusPath -Raw | ConvertFrom-Json
    }
    else {
        $programStatus = [pscustomobject]@{}
    }
    Ensure-Property -Target $programStatus -Name "phase" -Value $Phase
    Ensure-Property -Target $programStatus -Name "updated_at" -Value $timestamp
    Ensure-Property -Target $programStatus -Name "message" -Value $Message
    Ensure-Property -Target $programStatus -Name "phase2_status_path" -Value $phase2StatusPath
    Ensure-Property -Target $programStatus -Name "phase2_plan_path" -Value $phase2PlanPath
    Ensure-Property -Target $programStatus -Name "phase2_pack_path" -Value $phase2PackPath
    Ensure-Property -Target $programStatus -Name "repair_context" -Value $repairContext
    Write-JsonFile -Path $programStatusPath -Payload $programStatus

    if (Test-Path $cycleStatusPath) {
        $cycleStatus = Get-Content -Path $cycleStatusPath -Raw | ConvertFrom-Json
    }
    else {
        $cycleStatus = [pscustomobject]@{}
    }
    Ensure-Property -Target $cycleStatus -Name "phase" -Value $Phase
    Ensure-Property -Target $cycleStatus -Name "updated_at" -Value $timestamp
    Ensure-Property -Target $cycleStatus -Name "message" -Value $Message
    Ensure-Property -Target $cycleStatus -Name "program_status_path" -Value $programStatusPath
    Ensure-Property -Target $cycleStatus -Name "phase2_status_path" -Value $phase2StatusPath
    Ensure-Property -Target $cycleStatus -Name "phase2_pack_path" -Value $phase2PackPath
    Ensure-Property -Target $cycleStatus -Name "phase2_resume_status_path" -Value $resumeStatusPath
    Ensure-Property -Target $cycleStatus -Name "phase2_resume_followon_status_path" -Value $resumeFollowonStatusPath
    Ensure-Property -Target $cycleStatus -Name "recovered_from_program_failure" -Value $true
    Write-JsonFile -Path $cycleStatusPath -Payload $cycleStatus
}

function Update-Phase2StatusFromLaunch {
    if (-not (Test-Path $phase2LaunchStatusPath)) {
        return
    }
    $launchStatus = Get-Content -Path $phase2LaunchStatusPath -Raw | ConvertFrom-Json
    $payload = [ordered]@{
        phase = "phase2_exhaustive_running"
        updated_at = (Get-Date).ToString("o")
        launch_status_path = $phase2LaunchStatusPath
        phase2_pack_path = $phase2PackPath
        rows = @($launchStatus.rows)
    }
    Write-JsonFile -Path $phase2StatusPath -Payload $payload
}

if (-not (Test-Path $programManifestPath)) {
    throw "program manifest was not found at $programManifestPath"
}
if (-not (Test-Path $phase1StatusPath)) {
    throw "phase1 status was not found at $phase1StatusPath"
}
if (-not (Test-Path $phase2PlanPath)) {
    throw "phase2 plan was not found at $phase2PlanPath"
}
if (-not (Test-Path $shortlistJsonPath)) {
    throw "family-wave shortlist was not found at $shortlistJsonPath"
}

$programManifest = Get-Content -Path $programManifestPath -Raw | ConvertFrom-Json
$phase1Status = Get-Content -Path $phase1StatusPath -Raw | ConvertFrom-Json

if ([string]$phase1Status.phase -ne "phase1_discovery_complete") {
    throw "phase1 discovery is not complete in $phase1StatusPath"
}

$readyBaseDir = [string]$programManifest.ready_base_dir
$secondaryOutputDir = [string]$programManifest.secondary_output_dir
$registryPath = [string]$programManifest.registry_path
$runnerPath = [string]$programManifest.runner_path

if ([string]::IsNullOrWhiteSpace($readyBaseDir) -or -not (Test-Path $readyBaseDir)) {
    throw "ready_base_dir from program manifest is missing or does not exist: $readyBaseDir"
}
if ([string]::IsNullOrWhiteSpace($secondaryOutputDir) -or -not (Test-Path $secondaryOutputDir)) {
    throw "secondary_output_dir from program manifest is missing or does not exist: $secondaryOutputDir"
}
if ([string]::IsNullOrWhiteSpace($registryPath) -or -not (Test-Path $registryPath)) {
    throw "registry_path from program manifest is missing or does not exist: $registryPath"
}
if ([string]::IsNullOrWhiteSpace($runnerPath) -or -not (Test-Path $runnerPath)) {
    throw "runner_path from program manifest is missing or does not exist: $runnerPath"
}

Write-Log "Rebuilding Phase 2 pack from completed Phase 1 artifacts in $programRootPath"
Update-ProgramAndCycleStatus -Phase "phase2_resume_planning" -Message "Rebuilding the Phase 2 launch pack from completed Phase 1 artifacts."

Invoke-PythonStep -ScriptPath $agentShardingPlanBuilderPath -Arguments @(
    "--primary-output-dir", (Join-Path $repoRoot "output"),
    "--secondary-output-dir", $secondaryOutputDir,
    "--backtester-ready-dir", $readyBaseDir,
    "--strategy-repo-json", (Join-Path (Join-Path $repoRoot "output") "strategy_repo_build_strategy_repo_20260421\strategy_repo.json"),
    "--output-dir", $agentShardingPlanRoot
) -FailureMessage "failed to build agent sharding plan for phase 2 resume"

Invoke-PythonStep -ScriptPath $agentOperatingModelBuilderPath -Arguments @(
    "--agent-plan-json", $agentShardingPlanPath,
    "--output-dir", $agentOperatingModelRoot
) -FailureMessage "failed to build agent operating model for phase 2 resume"

Invoke-PythonStep -ScriptPath $phase2PackBuilderPath -Arguments @(
    "--phase2-plan-json", $phase2PlanPath,
    "--shortlist-json", $shortlistJsonPath,
    "--operating-model-json", $agentOperatingModelPath,
    "--output-dir", $phase2PackRoot,
    "--research-root", (Join-Path $phase2Root "lanes"),
    "--runner-path", $runnerPath,
    "--ready-base-dir", $readyBaseDir,
    "--python-exe", $PythonExe,
    "--require-explicit-sources"
) -FailureMessage "failed to rebuild phase 2 launch pack from phase 1 artifacts"

if (-not (Test-Path $phase2PackPath)) {
    throw "phase2 launch pack was not created at $phase2PackPath"
}

Update-ProgramAndCycleStatus -Phase "phase2_resume_ready" -Message "Phase 2 launch pack rebuilt successfully from completed Phase 1 artifacts."

if (-not $Execute) {
    Write-Output ([ordered]@{
        phase = "phase2_resume_ready"
        phase2_pack_path = $phase2PackPath
        agent_sharding_plan_path = $agentShardingPlanPath
        agent_operating_model_path = $agentOperatingModelPath
        next_step = "Run again with -Execute to launch the resumed Phase 2 wave."
    } | ConvertTo-Json -Depth 8)
    exit 0
}

$launchAlreadyTerminal = $false
if (Test-Path $phase2LaunchStatusPath) {
    $existingLaunch = Get-Content -Path $phase2LaunchStatusPath -Raw | ConvertFrom-Json
    $existingPhase = [string]$existingLaunch.phase
    if ($existingPhase -in @("running", "completed")) {
        $launchAlreadyTerminal = $true
        Write-Log "Phase 2 launch status already exists in state $existingPhase; reusing existing launch."
    }
}

if (-not $launchAlreadyTerminal) {
    Update-ProgramAndCycleStatus -Phase "phase2_resume_launching" -Message "Launching Phase 2 from the rebuilt launch pack."
    $launchArgs = @(
        "-PackPath", $phase2PackPath,
        "-Execute"
    )
    if ($Wait) {
        $launchArgs += "-Wait"
    }
    Invoke-PowerShellStep -ScriptPath $launchAgentWavePath -Arguments $launchArgs -FailureMessage "phase 2 resume launch failed"
}

if (Test-Path $phase2LaunchStatusPath) {
    Update-Phase2StatusFromLaunch
    Update-ProgramAndCycleStatus -Phase "phase2_exhaustive_running" -Message "Phase 2 exhaustive resume is running from completed Phase 1 artifacts."
}

if ($StartFollowon) {
    $followonAlreadyActive = $false
    if (Test-Path $resumeFollowonStatusPath) {
        $followonStatus = Get-Content -Path $resumeFollowonStatusPath -Raw | ConvertFrom-Json
        $followonPhase = [string]$followonStatus.phase
        if ($followonPhase -and $followonPhase -notin @("failed", "completed")) {
            $followonAlreadyActive = $true
            Write-Log "Phase 2 follow-on watcher already active in state $followonPhase; not starting a duplicate watcher."
        }
    }

    if (-not $followonAlreadyActive) {
        Write-Log "Starting resumed Phase 2 follow-on watcher."
        Start-Process -FilePath powershell -ArgumentList @(
            "-NoProfile",
            "-ExecutionPolicy", "Bypass",
            "-File", $queueFollowonPath,
            "-PackPath", $phase2PackPath,
            "-ProgramRoot", $programRootPath,
            "-LiveManifestPath", $LiveManifestPath
        ) -WindowStyle Hidden | Out-Null
    }
}

Write-Output ([ordered]@{
    phase = "phase2_exhaustive_running"
    phase2_pack_path = $phase2PackPath
    phase2_launch_status_path = $phase2LaunchStatusPath
    phase2_resume_followon_status_path = $resumeFollowonStatusPath
} | ConvertTo-Json -Depth 8)
