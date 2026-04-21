param(
    [string]$PackPath,
    [string]$PythonExe = "",
    [int]$PollSeconds = 15,
    [switch]$Execute,
    [switch]$Wait,
    [switch]$SkipValidation
)

$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($PackPath)) {
    throw "PackPath is required."
}

$packFile = [System.IO.Path]::GetFullPath($PackPath)
if (-not (Test-Path $packFile)) {
    throw "launch pack not found: $packFile"
}

$pack = Get-Content -Path $packFile -Raw | ConvertFrom-Json
if ([string]::IsNullOrWhiteSpace($PythonExe)) {
    $PythonExe = [string]$pack.python_exe
}

$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$statusPath = Join-Path (Split-Path -Parent $packFile) "launch_status.json"
$validationPath = Join-Path (Split-Path -Parent $packFile) "pack_validation.json"
$runRegistryReportDir = Join-Path (Split-Path -Parent $packFile) "run_registry_report"
$validatorPath = Join-Path $scriptRoot "validate_agent_wave_pack.py"
$reporterPath = Join-Path $scriptRoot "build_run_registry_report.py"
$defaultOutputRoot = Join-Path $scriptRoot "output"
$defaultRegistryPath = Join-Path $defaultOutputRoot "run_registry.jsonl"

function Convert-ArgumentListToCommandLine {
    param([object[]]$Arguments)

    $tokens = foreach ($argument in @($Arguments)) {
        $text = [string]$argument
        if ($text.Length -eq 0) {
            '""'
            continue
        }
        if ($text -match '[\s"]') {
            $escaped = $text -replace '(\\*)"', '$1$1\"'
            $escaped = $escaped -replace '(\\+)$', '$1$1'
            '"' + $escaped + '"'
        }
        else {
            $text
        }
    }

    return ($tokens -join ' ')
}

function Invoke-RunRegistryReport {
    param(
        [object[]]$Rows
    )
    if (-not (Test-Path $reporterPath)) {
        return
    }

    $reportArgs = @(
        $reporterPath,
        "--output-root", $defaultOutputRoot,
        "--registry-path", $defaultRegistryPath,
        "--report-dir", $runRegistryReportDir
    )

    $manifestRoots = New-Object System.Collections.Generic.HashSet[string]
    foreach ($row in @($Rows)) {
        if ($null -eq $row) {
            continue
        }
        $researchDir = [string]$row.research_dir
        if (-not [string]::IsNullOrWhiteSpace($researchDir)) {
            [void]$manifestRoots.Add([System.IO.Path]::GetFullPath($researchDir))
        }
    }
    foreach ($manifestRoot in $manifestRoots) {
        $reportArgs += @("--manifest-root", $manifestRoot)
    }

    & $PythonExe @reportArgs | Out-Null
}

if (-not $SkipValidation) {
    if (-not (Test-Path $validatorPath)) {
        throw "pack validator not found: $validatorPath"
    }
    & $PythonExe $validatorPath --pack-json $packFile --report-path $validationPath | Out-Null
    if ($LASTEXITCODE -ne 0) {
        [ordered]@{
            pack_path = $packFile
            phase = "preflight_failed"
            updated_at = (Get-Date).ToString("o")
            execute = [bool]$Execute
            wait = [bool]$Wait
            validation_path = $validationPath
            rows = @()
        } | ConvertTo-Json -Depth 8 | Set-Content -Path $statusPath
        throw "launch pack validation failed: $validationPath"
    }
}

function Write-Status {
    param(
        [string]$Phase,
        [object[]]$Rows
    )
    [ordered]@{
        pack_path = $packFile
        phase = $Phase
        updated_at = (Get-Date).ToString("o")
        execute = [bool]$Execute
        wait = [bool]$Wait
        validation_path = if (Test-Path $validationPath) { $validationPath } else { $null }
        run_registry_report_dir = if (Test-Path $runRegistryReportDir) { $runRegistryReportDir } else { $null }
        rows = $Rows
    } | ConvertTo-Json -Depth 8 | Set-Content -Path $statusPath
}

$planRows = @()
foreach ($lane in @($pack.lanes)) {
    $planRows += [ordered]@{
        lane_id = [string]$lane.lane_id
        agent = [string]$lane.agent
        tickers = @($lane.tickers)
        research_dir = [string]$lane.research_dir
        stdout_path = [string]$lane.stdout_path
        stderr_path = [string]$lane.stderr_path
        command = [string]$lane.command_text
    }
}

if (-not $Execute) {
    Write-Status -Phase "dry_run" -Rows $planRows
    Invoke-RunRegistryReport -Rows $planRows
    Write-Output ($planRows | ConvertTo-Json -Depth 8)
    return
}

$processRows = @()
foreach ($lane in @($pack.lanes)) {
    $researchDir = [System.IO.Path]::GetFullPath([string]$lane.research_dir)
    $logsDir = [System.IO.Path]::GetFullPath([string]$lane.logs_dir)
    New-Item -ItemType Directory -Force -Path $researchDir | Out-Null
    New-Item -ItemType Directory -Force -Path $logsDir | Out-Null

    $argumentLine = Convert-ArgumentListToCommandLine -Arguments @($lane.command_args)
    $process = Start-Process -FilePath $PythonExe `
        -ArgumentList $argumentLine `
        -WorkingDirectory (Split-Path -Parent [string]$pack.runner_path) `
        -RedirectStandardOutput ([string]$lane.stdout_path) `
        -RedirectStandardError ([string]$lane.stderr_path) `
        -PassThru

    $processRows += [pscustomobject]@{
        lane_id = [string]$lane.lane_id
        agent = [string]$lane.agent
        tickers = @($lane.tickers)
        research_dir = $researchDir
        stdout_path = [string]$lane.stdout_path
        stderr_path = [string]$lane.stderr_path
        pid = $process.Id
        process = $process
    }
}

if (-not $Wait) {
    $statusRows = @()
    foreach ($row in $processRows) {
        $statusRows += [ordered]@{
            lane_id = $row.lane_id
            agent = $row.agent
            pid = $row.pid
            has_exited = $false
            exit_code = $null
            research_dir = $row.research_dir
            stdout_path = $row.stdout_path
            stderr_path = $row.stderr_path
        }
    }
    Write-Status -Phase "started" -Rows $statusRows
    Invoke-RunRegistryReport -Rows $statusRows
    Write-Output ($statusRows | ConvertTo-Json -Depth 8)
    return
}

while ($true) {
    $statusRows = @()
    $allExited = $true
    foreach ($row in $processRows) {
        if (-not $row.process.HasExited) {
            $allExited = $false
        }
        $statusRows += [ordered]@{
            lane_id = $row.lane_id
            agent = $row.agent
            pid = $row.pid
            has_exited = $row.process.HasExited
            exit_code = if ($row.process.HasExited) { [int]$row.process.ExitCode } else { $null }
            research_dir = $row.research_dir
            stdout_path = $row.stdout_path
            stderr_path = $row.stderr_path
        }
    }
    Write-Status -Phase "running" -Rows $statusRows
    if ($allExited) {
        break
    }
    Start-Sleep -Seconds $PollSeconds
}

$finalRows = @()
foreach ($row in $processRows) {
    $row.process.WaitForExit()
    $finalRows += [ordered]@{
        lane_id = $row.lane_id
        agent = $row.agent
        pid = $row.pid
        exit_code = [int]$row.process.ExitCode
        has_master_summary = Test-Path (Join-Path $row.research_dir "master_summary.json")
        research_dir = $row.research_dir
        stdout_path = $row.stdout_path
        stderr_path = $row.stderr_path
    }
}

Write-Status -Phase "completed" -Rows $finalRows
Invoke-RunRegistryReport -Rows $finalRows
Write-Output ($finalRows | ConvertTo-Json -Depth 8)

$failedRows = @(
    $finalRows | Where-Object {
        ([int]$_.exit_code) -ne 0 -or (-not [bool]$_.has_master_summary)
    }
)
if ($failedRows.Count -gt 0) {
    $failedLaneIds = @($failedRows | ForEach-Object { [string]$_.lane_id })
    Write-Error ("one or more agent-wave lanes failed or did not write master_summary.json: " + ($failedLaneIds -join ", "))
    exit 2
}
