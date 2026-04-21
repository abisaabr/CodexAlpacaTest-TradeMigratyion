param(
    [string]$ProgramRoot,
    [string]$ValidationOutputDir = "",
    [string]$LiveManifestPath = "C:\Users\rabisaab\Downloads\codexalpaca_repo\config\strategy_manifests\multi_ticker_portfolio_live.yaml",
    [int]$PollSeconds = 60,
    [int]$TimeoutMinutes = 720
)

$ErrorActionPreference = "Stop"

$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$programRootPath = [System.IO.Path]::GetFullPath($ProgramRoot)
$statusFile = Join-Path $programRootPath "program_status.json"
$validatorPath = Join-Path $scriptRoot "validate_program_live_book.py"
$runRegistryReporterPath = Join-Path $scriptRoot "build_run_registry_report.py"
$defaultOutputRoot = Join-Path $scriptRoot "output"
$defaultRegistryPath = Join-Path $defaultOutputRoot "run_registry.jsonl"

if ([string]::IsNullOrWhiteSpace($ValidationOutputDir)) {
    $validationRoot = Join-Path $programRootPath "live_book_validation"
}
else {
    $validationRoot = [System.IO.Path]::GetFullPath($ValidationOutputDir)
}

$logPath = Join-Path $validationRoot "validation_followon.log"
$followonStatusPath = Join-Path $validationRoot "validation_followon_status.json"
$runRegistryReportDir = Join-Path $validationRoot "run_registry_report"
$deadline = (Get-Date).AddMinutes($TimeoutMinutes)

New-Item -ItemType Directory -Force -Path $validationRoot | Out-Null
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
        program_root = $programRootPath
        status_file = $statusFile
        validation_output_dir = $validationRoot
        run_registry_report_dir = $runRegistryReportDir
    }
    $payload | ConvertTo-Json -Depth 6 | Set-Content -Path $followonStatusPath
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
    foreach ($root in @($programRootPath, $validationRoot)) {
        if (Test-Path $root) {
            $reportArgs += @("--manifest-root", $root)
        }
    }
    & python @reportArgs | Out-Null
}

function Get-ProgramPhase {
    if (-not (Test-Path $statusFile)) {
        return $null
    }
    try {
        $payload = Get-Content $statusFile -Raw | ConvertFrom-Json
        return [string]$payload.phase
    }
    catch {
        return $null
    }
}

Write-Log "Waiting for program completion in $programRootPath"
Write-Status -Phase "waiting" -Message "Waiting for the down/choppy program to reach a terminal state."
Invoke-RunRegistryReport

while ((Get-Date) -lt $deadline) {
    $phase = Get-ProgramPhase
    if ($phase -in @("complete", "complete_phase1_only", "complete_no_phase2_survivors")) {
        Write-Log "Program reached terminal phase '$phase'. Starting live-book validation."
        break
    }
    if ($phase -eq "failed") {
        Write-Log "Program reported failed status before validation could start."
        Write-Status -Phase "failed" -Message "Program failed before live-book validation could start."
        Invoke-RunRegistryReport
        exit 2
    }
    Start-Sleep -Seconds $PollSeconds
}

if ((Get-ProgramPhase) -notin @("complete", "complete_phase1_only", "complete_no_phase2_survivors")) {
    Write-Log "Timed out waiting for program completion."
    Write-Status -Phase "failed" -Message "Timed out waiting for program completion."
    Invoke-RunRegistryReport
    exit 3
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

Write-Log "Live-book validation completed successfully."
Write-Status -Phase "completed" -Message "Live-book validation completed successfully."
Invoke-RunRegistryReport
exit 0
