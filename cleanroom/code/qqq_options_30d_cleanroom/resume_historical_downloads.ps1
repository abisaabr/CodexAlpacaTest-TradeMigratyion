Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$requiredEnv = @(
    "ALPACA_API_KEY",
    "ALPACA_SECRET_KEY",
    "ALPACA_API_BASE_URL"
)

$missing = $requiredEnv | Where-Object { -not $env:$_ }
if ($missing.Count -gt 0) {
    throw "Missing required environment variables: $($missing -join ', '). Open a new PowerShell window after running setx."
}

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location -LiteralPath $root

if (-not (Test-Path -LiteralPath ".\output")) {
    New-Item -ItemType Directory -Path ".\output" | Out-Null
}

function Invoke-HistoricalBatch {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Symbols,
        [int]$Concurrency = 5
    )

    Write-Host "Starting batch for symbols: $Symbols"
    & python .\run_symbol_batch_365.py `
        --symbols $Symbols `
        --today 2026-04-10 `
        --lookback-days 365 `
        --concurrency $Concurrency `
        --job-workers 4 `
        --requests-per-second 1.6 `
        --tag 365d `
        --output-dir .\output
}

# Safe to rerun because completed symbols are skipped once their audit file exists.
Invoke-HistoricalBatch -Symbols "HTZ,DAL,NKE,AAL,GOOG,WULF,IREN,SMCI,CRWV,SNDK,HIMS,NIO,RKLB,AMC,NOK,SPCE,CCL,AI,IONQ,VZ" -Concurrency 5
Invoke-HistoricalBatch -Symbols "UVXY,LABU,BOIL,TNA,SPXS,SPXU,SOXS,LQD,IYR,KOLD,BE,NBIS,CVNA,ASTS,CRWD,NVO,UAL,TTD,CSCO,KO" -Concurrency 5
