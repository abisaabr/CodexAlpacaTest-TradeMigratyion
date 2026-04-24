# GCP Research Asset Inventory

## Snapshot

- Generated at: `2026-04-24T00:48:10.372733-04:00`
- Status: `ready_for_research_bootstrap`
- Runner repo root: `C:\Users\abisa\Downloads\codexalpaca_repo_gcp_lease_lane_refreshed`
- Runtime root: `C:\Users\abisa\Downloads\codexalpaca_runtime\multi_ticker_portfolio_live`
- GCS prefix: `gs://codexalpaca-control-us/research_manifests`

## Counts

- runner_file_count_sampled: `539`
- downloader_script_count: `1`
- backtest_script_count: `2`
- research_script_count: `5`
- strategy_config_count: `5`
- backtest_report_count: `52`
- runtime_session_date_count: `3`

## April 23 Evidence

- session_summary: `True`
- completed_trades: `True`
- evidence_contract: `True`
- teaching_gate: `True`
- trade_review: `True`
- postmortem: `True`
- quality_scorecard: `True`

## Key Assets

### Downloader Scripts

- `build_historical_dataset.py`

### Backtest Scripts

- `run_option_aware_research_backtest.py`
- `run_sample_backtest.py`

### Strategy Configs

- `backtest.example.yaml`
- `multi_ticker_paper_portfolio.yaml`
- `qqq_paper_portfolio.yaml`
- `risk_controls/multi_ticker_portfolio.yaml`
- `strategy_manifests/multi_ticker_portfolio_live.yaml`

### Runtime Session Dates

- `2026-04-21`
- `2026-04-22`
- `2026-04-23`

## Next Actions

- Publish this inventory to GCS before launching broader research sweeps.
- Normalize April 22 and April 23 paper-session evidence into derived research tables.
- Run data-quality checks over the governed 11-name universe before trusting any scorecard expansion.
- Keep all research outputs advisory until control-plane promotion review.
