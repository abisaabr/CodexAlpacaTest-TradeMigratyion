# QQQ Dense Downloader Status

## State

- State: `completed`
- Broker-facing: `false`
- Trading effect: `none`
- Live manifest effect: `none`
- Risk policy effect: `none`
- Fill gate effect: `none`
- Run location: local cleanroom checkout
- Run path: `C:\Users\abisa\Downloads\CodexAlpacaTest-TradeMigratyion\cleanroom\code\qqq_options_30d_cleanroom`
- Output path: `C:\Users\abisa\Downloads\CodexAlpacaTest-TradeMigratyion\cleanroom\code\qqq_options_30d_cleanroom\output\qqq_30d`

## Command

The requested downloader was run with the supported CLI flags:

```powershell
python download_qqq_options.py --today 2026-04-17 --lookback-days 30 --workers 2 --requests-per-second 1.0 --output-dir "C:\Users\abisa\Downloads\CodexAlpacaTest-TradeMigratyion\cleanroom\code\qqq_options_30d_cleanroom\output\qqq_30d"
```

The checked-in downloader does not support `--tag`; the `qqq_30d` tag is represented by the output directory.

## Results

- Underlying: `QQQ`
- Window: `2026-03-18` through `2026-04-17`
- Trading days: `22`
- Stock feed used: `sip`
- Contracts total: `8022`
- Unique selected contracts: `1646`
- Selected contract-days: `2794`
- Successful contract-day requests: `2794`
- Failed contract-day requests: `0`
- Request fill rate: `100.0%`
- Nonempty contract-day ratio: `96.242%`
- Dense minute fill on selected contract-days: `96.242%`
- Dense minute fill on nonempty contract-days: `100.0%`
- Raw option bar rows: `506924`

## Created Files

- `audit_report.json`
- `fetch_manifest.csv`
- `qqq_underlying_1min.parquet`
- `qqq_option_contracts.parquet`
- `qqq_option_daily_universe.parquet`
- `qqq_option_1min_bars.parquet`
- `qqq_option_1min_dense.parquet`

Aggregate output size is approximately `19.27 MB`.

## Institutional Read

The QQQ cleanroom flow proves the project already has a high-fill historical options data path when the downloader builds a dense single-symbol option universe. This differs from the broad top100 research lane, where selected event contracts and exit timestamps often create fill gaps below the mandatory `0.90` promotion gate.

The next research-safe use is to adapt the dense single-symbol universe pattern for the most liquid underlyings and compare it against Phase37's top-10 weekly ATM lane. Do not relax the `0.90` fill gate and do not use this local data pull as a deployment or broker-facing signal by itself.

