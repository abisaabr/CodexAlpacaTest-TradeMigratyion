# GCP Research Executor Readiness

## Snapshot

- Generated at: `2026-04-23T22:40:51.159781-04:00`
- Status: `ready_for_research_only_execution_smoke_validated`
- Wave id: `research_wave_20260424_bootstrap`
- Wave variants: `2070`
- Wave chunks: `21`
- GCS prefix: `gs://codexalpaca-control-us/research_executor`

## Smoke Run Proof

- Present: `True`
- Valid: `True`
- Run id: `research_wave_20260424_chunk_0001_smoke`
- Evidence mode: `metadata_proxy_smoke`
- Input variants: `25`
- Broker facing: `False`

## Runner Asset Status

- `historical_dataset_builder`: `True` `scripts/build_historical_dataset.py`
- `sample_backtest_runner`: `True` `scripts/run_sample_backtest.py`
- `generic_backtest_engine`: `True` `alpaca_lab/backtest/engine.py`
- `option_long_call_skeleton`: `True` `alpaca_lab/strategies/options_skeleton.py`
- `option_candidate_selector`: `True` `alpaca_lab/options/strategies.py`

## Full Wave Executor Candidates

- `run_gcp_research_wave`: `True` `scripts/run_gcp_research_wave.py`
- `run_options_research_wave`: `False` `scripts/run_options_research_wave.py`
- `run_research_wave_backtest`: `False` `scripts/run_research_wave_backtest.py`

## Data Inventory

- Data root exists: `True`
- Parquet files: `51`
- CSV files: `0`
- Has local research bars: `True`

## Sample Backtest

- Trade count: `136`
- Net PnL: `-1712.9154744795487`
- Bars source: `data\silver\stocks\research_preferred_1min_20260421_20260423_stock_contracts.parquet`

## Issues

- `warning` `sample_backtest_negative_expectancy`: The current sample backtest has negative after-cost expectancy.

## Next Build Contract

- Run bounded real-bar research chunks from the mounted curated dataset.
- Extend the executor from metadata proxy smoke to real single-leg repair backtests first.
- Treat the negative stock sample baseline as loser-learning evidence, not as a deployment candidate.
- Add multi-leg payoff simulation before treating defined-risk variants as promotable.
- Keep compact promotion/rejection summaries in GitHub and require governance review before runner eligibility.
