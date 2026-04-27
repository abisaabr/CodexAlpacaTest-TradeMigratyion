[CmdletBinding()]
param(
    [string]$ControlPlaneRoot = "",
    [string]$ProjectId = "codexalpaca",
    [string]$VmName = "vm-execution-paper-01",
    [string]$Zone = "us-east1-b",
    [string]$VmRunnerPath = "/opt/codexalpaca/codexalpaca_repo",
    [string]$PortfolioConfig = "config/multi_ticker_paper_portfolio.yaml",
    [switch]$MirrorToGcs,
    [string]$GcsPrefix = "gs://codexalpaca-control-us/gcp_foundation",
    [int]$MaxAgeSeconds = 600,
    [switch]$FailOnBlock
)

$ErrorActionPreference = "Stop"

function Resolve-ControlPlaneRoot {
    param([string]$ProvidedRoot)
    if ($ProvidedRoot) {
        return (Resolve-Path $ProvidedRoot).Path
    }
    $scriptPath = $PSCommandPath
    $scriptDir = Split-Path $scriptPath -Parent
    return (Resolve-Path (Join-Path $scriptDir "..\..\..")).Path
}

function Resolve-PythonCommand {
    param([string]$ControlPlaneRoot)
    $venvPython = Join-Path $ControlPlaneRoot ".venv\Scripts\python.exe"
    if (Test-Path $venvPython) {
        return @($venvPython)
    }
    if (Get-Command py -ErrorAction SilentlyContinue) {
        return @("py", "-3")
    }
    if (Get-Command python -ErrorAction SilentlyContinue) {
        return @("python")
    }
    throw "No Python interpreter found."
}

function Invoke-PythonScript {
    param(
        [string[]]$PythonCommand,
        [string]$ScriptPath,
        [string[]]$Arguments
    )
    $command = @($PythonCommand + @($ScriptPath) + $Arguments)
    if ($command.Count -eq 1) {
        & $command[0]
    } else {
        & $command[0] $command[1..($command.Count - 1)]
    }
    if ($LASTEXITCODE -ne 0) {
        throw "Python script failed with exit code $LASTEXITCODE`: $ScriptPath"
    }
}

function Invoke-Gcloud {
    param([string[]]$Arguments)
    & gcloud @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "gcloud failed with exit code $LASTEXITCODE`: gcloud $($Arguments -join ' ')"
    }
}

$ControlPlaneRoot = Resolve-ControlPlaneRoot -ProvidedRoot $ControlPlaneRoot
$ReportDir = Join-Path $ControlPlaneRoot "docs\gcp_foundation"
$TimestampUtc = (Get-Date).ToUniversalTime().ToString("yyyyMMddTHHmmssZ")
$EvidenceDir = Join-Path $ReportDir "runtime_evidence\startup_preflight\$TimestampUtc"
New-Item -ItemType Directory -Path $EvidenceDir -Force | Out-Null

$LocalJson = Join-Path $EvidenceDir "startup_preflight.json"
$LocalStderr = Join-Path $EvidenceDir "startup_preflight.stderr"
$LocalSourceStamp = Join-Path $EvidenceDir "source_stamp.json"
$LocalSshLog = Join-Path $EvidenceDir "gcloud_ssh.log"

$RemoteBase = "reports/gcp_trusted_validation"
$RemoteJson = "$RemoteBase/startup_preflight_$TimestampUtc.json"
$RemoteStderr = "$RemoteBase/startup_preflight_$TimestampUtc.stderr"
$RemoteSourceStamp = "$RemoteBase/source_stamp_$TimestampUtc.json"
$RemoteJsonAbs = "$VmRunnerPath/$RemoteJson"
$RemoteStderrAbs = "$VmRunnerPath/$RemoteStderr"
$RemoteSourceStampAbs = "$VmRunnerPath/$RemoteSourceStamp"

$RemoteCommand = @"
cd "$VmRunnerPath"
mkdir -p "$RemoteBase"
set +e
./.venv/bin/python scripts/run_multi_ticker_portfolio_paper_trader.py --portfolio-config "$PortfolioConfig" --startup-preflight > "$RemoteJson" 2> "$RemoteStderr"
code=`$?
if [ -f .codexalpaca_source_stamp.json ]; then
  cp .codexalpaca_source_stamp.json "$RemoteSourceStamp"
else
  printf '{}\n' > "$RemoteSourceStamp"
fi
printf '__STARTUP_PREFLIGHT_EXIT_CODE__=%s\n' "`$code"
exit 0
"@

& gcloud compute ssh $VmName --project $ProjectId --zone $Zone --tunnel-through-iap --command $RemoteCommand *>&1 |
    Tee-Object -FilePath $LocalSshLog | Out-Host
if ($LASTEXITCODE -ne 0) {
    throw "gcloud compute ssh failed with exit code $LASTEXITCODE"
}

Invoke-Gcloud -Arguments @(
    "compute", "scp",
    "--project", $ProjectId,
    "--zone", $Zone,
    "--tunnel-through-iap",
    "${VmName}:$RemoteJsonAbs",
    $LocalJson
)
Invoke-Gcloud -Arguments @(
    "compute", "scp",
    "--project", $ProjectId,
    "--zone", $Zone,
    "--tunnel-through-iap",
    "${VmName}:$RemoteStderrAbs",
    $LocalStderr
)
Invoke-Gcloud -Arguments @(
    "compute", "scp",
    "--project", $ProjectId,
    "--zone", $Zone,
    "--tunnel-through-iap",
    "${VmName}:$RemoteSourceStampAbs",
    $LocalSourceStamp
)

$GcsEvidenceUri = ""
if ($MirrorToGcs) {
    $GcsEvidenceRoot = "$GcsPrefix/startup_preflight_evidence/$TimestampUtc"
    Invoke-Gcloud -Arguments @("storage", "cp", $LocalJson, "$GcsEvidenceRoot/startup_preflight.json")
    Invoke-Gcloud -Arguments @("storage", "cp", $LocalStderr, "$GcsEvidenceRoot/startup_preflight.stderr")
    Invoke-Gcloud -Arguments @("storage", "cp", $LocalSourceStamp, "$GcsEvidenceRoot/source_stamp.json")
    Invoke-Gcloud -Arguments @("storage", "cp", $LocalSshLog, "$GcsEvidenceRoot/gcloud_ssh.log")
    $GcsEvidenceUri = "$GcsEvidenceRoot/startup_preflight.json"
}

$PythonCommand = Resolve-PythonCommand -ControlPlaneRoot $ControlPlaneRoot
$BuilderPath = Join-Path $ControlPlaneRoot "cleanroom\code\qqq_options_30d_cleanroom\build_gcp_execution_startup_preflight_status.py"
Invoke-PythonScript -PythonCommand $PythonCommand -ScriptPath $BuilderPath -Arguments @(
    "--preflight-json", $LocalJson,
    "--stderr-path", $LocalStderr,
    "--source-stamp-json", $LocalSourceStamp,
    "--report-dir", $ReportDir,
    "--gcs-evidence-uri", $GcsEvidenceUri,
    "--max-age-seconds", ([string]$MaxAgeSeconds)
)

if ($MirrorToGcs) {
    Invoke-Gcloud -Arguments @("storage", "cp", (Join-Path $ReportDir "gcp_execution_startup_preflight_status.json"), "$GcsPrefix/gcp_execution_startup_preflight_status.json")
    Invoke-Gcloud -Arguments @("storage", "cp", (Join-Path $ReportDir "gcp_execution_startup_preflight_status.md"), "$GcsPrefix/gcp_execution_startup_preflight_status.md")
    Invoke-Gcloud -Arguments @("storage", "cp", (Join-Path $ReportDir "gcp_execution_startup_preflight_handoff.md"), "$GcsPrefix/gcp_execution_startup_preflight_handoff.md")
}

$StatusPacket = Get-Content -Path (Join-Path $ReportDir "gcp_execution_startup_preflight_status.json") -Raw | ConvertFrom-Json
Write-Host ("startup_preflight_status={0}" -f $StatusPacket.status)
Write-Host ("blocks_launch={0}" -f $StatusPacket.blocks_launch)
Write-Host ("broker_position_count={0}" -f $StatusPacket.broker_position_count)
Write-Host ("open_order_count={0}" -f $StatusPacket.open_order_count)
if ($FailOnBlock -and $StatusPacket.blocks_launch) {
    exit 43
}
