# GCP Research Data Readiness

## Snapshot

- Generated at: `2026-04-24T00:48:11.942549-04:00`
- Status: `ready_for_real_bar_research_with_warnings`
- Build name: `research_preferred_1min_20260421_20260423_stock_contracts`
- Stock symbols: `5`
- Stock rows: `10912`
- GCS prefix: `gs://codexalpaca-data-us`

## Stock Rows

- `GLD` rows `1947` `2026-04-21 13:30:00+00:00` to `2026-04-23 20:00:00+00:00`
- `MSFT` rows `2218` `2026-04-21 13:30:00+00:00` to `2026-04-23 20:00:00+00:00`
- `QQQ` rows `2276` `2026-04-21 13:30:00+00:00` to `2026-04-23 20:00:00+00:00`
- `SLV` rows `2171` `2026-04-21 13:30:00+00:00` to `2026-04-23 20:00:00+00:00`
- `TSLA` rows `2300` `2026-04-21 13:30:00+00:00` to `2026-04-23 20:00:00+00:00`

## Option Contract Inventory Rows

- `GLD`: `1470`
- `MSFT`: `624`
- `QQQ`: `2622`
- `SLV`: `936`
- `TSLA`: `1258`

## Selected Contract Rows

- `GLD`: `238`
- `MSFT`: `196`
- `QQQ`: `420`
- `SLV`: `238`
- `TSLA`: `238`

## Sample Backtest Baseline

- Trade count: `136`
- Net PnL: `-1712.9154744795487`
- Expectancy: `-12.594966724114329`
- Win rate: `0.18382352941176472`

## GCS Artifacts

- `raw_manifest`: `gs://codexalpaca-data-us/raw/manifests/research_preferred_1min_20260421_20260423_stock_contracts.json`
- `raw_historical_prefix`: `gs://codexalpaca-data-us/raw/historical/research_preferred_1min_20260421_20260423_stock_contracts/`
- `curated_historical_prefix`: `gs://codexalpaca-data-us/curated/historical/research_preferred_1min_20260421_20260423_stock_contracts/`
- `combined_stock_panel`: `gs://codexalpaca-data-us/curated/stocks/research_preferred_1min_20260421_20260423_stock_contracts.parquet`
- `combined_stock_panel_manifest`: `gs://codexalpaca-data-us/curated/stocks/research_preferred_1min_20260421_20260423_stock_contracts.manifest.json`
- `reports_prefix`: `gs://codexalpaca-data-us/reports/historical/research_preferred_1min_20260421_20260423_stock_contracts/`
- `sample_backtest_prefix`: `gs://codexalpaca-data-us/reports/sample_backtest/research_preferred_1min_20260421_20260423_stock_contracts/`

## Issues

- `warning` `negative_sample_backtest_expectancy`: The real-bar sample stock baseline has negative expectancy and should be treated as a loser-learning baseline.

## Next Research Step

- Use this dataset for real-bar single-leg repair smoke backtests first.
- Treat the negative stock baseline as loser-learning evidence, not as a deployment candidate.
- Add historical option bars/trades only after the stock-bar and selected-contract workflow remains stable.
