param(
    [string]$PackPath,
    [string]$ProgramRoot,
    [string]$ValidationOutputDir = "",
    [string]$ReviewOutputDir = "",
    [string]$LiveManifestPath = "C:\Users\rabisaab\Downloads\codexalpaca_repo\config\strategy_manifests\multi_ticker_portfolio_live.yaml",
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
$packFile = [System.IO.Path]::GetFullPath($PackPath)
$packRoot = Split-Path -Parent $packFile
$launchStatusPath = Join-Path $packRoot "launch_status.json"
$programRootPath = [System.IO.Path]::GetFullPath($ProgramRoot)

$validatorPath = Join-Path $scriptRoot "validate_program_live_book.py"
$hardeningBuilderPath = Join-Path $scriptRoot "build_live_book_hardening_review.py"
$runRegistryReporterPath = Join-Path $scriptRoot "build_run_registry_report.py"
$defaultOutputRoot = Join-Path $scriptRoot "output"
$defaultRegistryPath = Join-Path $defaultOutputRoot "run_registry.jsonl"

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

$statusPath = Join-Path $programRootPath "phase2_resume_followon_status.json"
$logPath = Join-Path $programRootPath "phase2_resume_followon.log"
$runRegistryReportDir = Join-Path $programRootPath "phase2_resume_run_registry_report"
$deadline = (Get-Date).AddMinutes($TimeoutMinutes)

New-Item -ItemType Directory -Force -Path $validationRoot | Out-Null
New-Item -ItemType Directory -Force -Path $reviewRoot | Out-Null
New-Item -ItemType Directory -Force -Path $runRegistryReportDir | Out-Null

function Write-Log {
    param([string]$Message)
    $timestamp = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
    Add-Content -Path $logPath -Value "[$timestamp] $Message"
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
        run_registry_report_dir = $runRegistryReportDir
    }
    $payload | ConvertTo-Json -Depth 6 | Set-Content -Path $statusPath
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
    & python @reportArgs | Out-Null
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

Write-Log "Waiting for phase 2 launch pack completion in $packRoot"
Write-Status -Phase "waiting" -Message "Waiting for the Phase 2 launch pack to reach a terminal state."
Invoke-RunRegistryReport

$launchPayload = $null
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
            Invoke-RunRegistryReport
            exit 2
        }
        Write-Log "Phase 2 launch pack completed successfully. Starting live-book validation."
        break
    }
    if ($phase -in @("started", "running")) {
        $rows = @($launchPayload.rows)
        if ($rows.Count -gt 0) {
            $runningRows = @($rows | Where-Object { Test-LaneProcessRunning $_ })
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
                    Invoke-RunRegistryReport
                    exit 5
                }
                Write-Log "Phase 2 lane runners exited cleanly with master_summary artifacts. Starting live-book validation."
                break
            }
        }
    }
    if ($phase -eq "preflight_failed") {
        Write-Log "Phase 2 launch pack failed preflight."
        Write-Status -Phase "failed" -Message "Phase 2 launch pack failed preflight."
        Invoke-RunRegistryReport
        exit 3
    }
    Start-Sleep -Seconds $PollSeconds
}

if ($null -eq $launchPayload -or [string]$launchPayload.phase -ne "completed") {
    Write-Log "Timed out waiting for the Phase 2 launch pack to complete."
    Write-Status -Phase "failed" -Message "Timed out waiting for the Phase 2 launch pack to complete."
    Invoke-RunRegistryReport
    exit 4
}

Write-Status -Phase "validating" -Message "Running live-book validation against the current manifest."
Invoke-RunRegistryReport

& python $validatorPath `
    --program-root $programRootPath `
    --output-dir $validationRoot `
    --live-manifest $LiveManifestPath

if ($LASTEXITCODE -ne 0) {
    $validationExitCode = $LASTEXITCODE
    Write-Log "Live-book validation failed with exit code $validationExitCode."
    Write-Status -Phase "failed" -Message "Live-book validation failed."
    Invoke-RunRegistryReport
    exit $validationExitCode
}

Write-Status -Phase "reviewing" -Message "Building live-book hardening review packet."
Invoke-RunRegistryReport

& python $hardeningBuilderPath `
    --validation-dir $validationRoot `
    --output-dir $reviewRoot `
    --live-manifest $LiveManifestPath

if ($LASTEXITCODE -ne 0) {
    $reviewExitCode = $LASTEXITCODE
    Write-Log "Hardening review build failed with exit code $reviewExitCode."
    Write-Status -Phase "failed" -Message "Hardening review build failed."
    Invoke-RunRegistryReport
    exit $reviewExitCode
}

Write-Log "Phase 2 follow-on validation and hardening review completed successfully."
Write-Status -Phase "completed" -Message "Phase 2 follow-on validation and hardening review completed successfully."
Invoke-RunRegistryReport
exit 0
