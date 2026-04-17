# Historical Downloader

This repo includes the clean-room Alpaca historical options downloader without shipping any option datasets.

Downloader code lives here:
- [`cleanroom/code/qqq_options_30d_cleanroom/download_qqq_options.py`](../cleanroom/code/qqq_options_30d_cleanroom/download_qqq_options.py)
- [`cleanroom/code/qqq_options_30d_cleanroom/download_qqq_options_365d_streaming.py`](../cleanroom/code/qqq_options_30d_cleanroom/download_qqq_options_365d_streaming.py)
- [`cleanroom/code/qqq_options_30d_cleanroom/neighbor_fill_empty_days.py`](../cleanroom/code/qqq_options_30d_cleanroom/neighbor_fill_empty_days.py)
- [`cleanroom/code/qqq_options_30d_cleanroom/run_symbol_batch_365.py`](../cleanroom/code/qqq_options_30d_cleanroom/run_symbol_batch_365.py)

## What You Need On A New Windows Machine

1. Python 3.11 or newer
2. Alpaca market data credentials
3. The Python packages listed in:
   [`cleanroom/code/qqq_options_30d_cleanroom/requirements_historical_downloader.txt`](../cleanroom/code/qqq_options_30d_cleanroom/requirements_historical_downloader.txt)

## Setup

From PowerShell:

```powershell
cd .\cleanroom\code\qqq_options_30d_cleanroom
pip install -r .\requirements_historical_downloader.txt
```

Set your Alpaca environment variables:

```powershell
setx ALPACA_API_KEY "YOUR_KEY"
setx ALPACA_SECRET_KEY "YOUR_SECRET"
setx ALPACA_API_BASE_URL "https://paper-api.alpaca.markets"
setx ALPACA_PAPER_TRADE "true"
setx LIVE_TRADING "false"
```

Close and reopen PowerShell after running `setx`.

## Quick Commands

Download one symbol for the last 365 days:

```powershell
python .\download_qqq_options_365d_streaming.py --underlying QQQ --today 2026-04-10 --lookback-days 365 --workers 4 --requests-per-second 1.6 --tag 365d --output-dir .\output
```

Run a multi-symbol 365-day batch with automatic per-symbol bundle zips:

```powershell
python .\run_symbol_batch_365.py --symbols "QQQ,SPY,IWM" --today 2026-04-10 --lookback-days 365 --concurrency 3 --job-workers 4 --requests-per-second 1.6 --tag 365d --output-dir .\output
```

Resume the prepared batches we were already using:

```powershell
.\resume_historical_downloads.ps1
```

## Output Behavior

- All output lands under `.\output`
- `run_symbol_batch_365.py` skips symbols that already have a matching `*_365d_audit_report.json`
- Completed symbols are bundled automatically into `<symbol>_365d_bundle.zip`
- Audit JSON files stay outside the bundle for quick resume checks

## Notes

- This GitHub repo is code-only for the downloader path
- The stock feed fallback order is currently `sip,iex`
- To add new tickers, just change the symbol list passed to `run_symbol_batch_365.py`
