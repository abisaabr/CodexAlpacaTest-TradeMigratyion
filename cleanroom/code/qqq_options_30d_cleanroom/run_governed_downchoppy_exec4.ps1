param()

$ErrorActionPreference = "Stop"

$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$cycleRoot = "G:\My Drive\CodexAlpaca\governed_takeover_20260423\nightly_operator_cycle_20260423_exec4"
$runnerRepoRoot = "C:\Users\abisa\Downloads\codexalpaca_repo_takeover_20260423"
$readyBaseDir = "G:\My Drive\CodexAlpaca\governed_takeover_20260423\backtester_ready"
$liveManifestPath = Join-Path $runnerRepoRoot "config\strategy_manifests\multi_ticker_portfolio_live.yaml"
$paperRunnerGatePath = "G:\My Drive\CodexAlpaca\governed_takeover_20260423\paper_runner_gate.json"

New-Item -ItemType Directory -Force -Path $cycleRoot | Out-Null
Set-Location $scriptRoot

& (Join-Path $scriptRoot "launch_nightly_operator_cycle.ps1") `
    -CycleRoot $cycleRoot `
    -RunnerRepoRoot $runnerRepoRoot `
    -ReadyBaseDir $readyBaseDir `
    -LiveManifestPath $liveManifestPath `
    -PaperRunnerGatePath $paperRunnerGatePath `
    -TournamentProfile "down_choppy_coverage_ranked" `
    -PythonExe "python" `
    -Execute

exit $LASTEXITCODE
