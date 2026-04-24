# GCP Research Executor Readiness

## Snapshot

- Generated at: `2026-04-24T00:49:12.781721-04:00`
- Status: `ready_for_research_only_real_bar_smoke_validated`
- Wave id: `research_wave_20260424_bootstrap`
- Wave variants: `2070`
- Wave chunks: `21`
- GCS prefix: `gs://codexalpaca-control-us/research_executor`

## Smoke Run Proof

- Present: `True`
- Valid: `True`
- Run id: `research_wave_20260424_rq002_real_stock_bar_smoke_chunk_0015`
- Evidence mode: `real_stock_bar_smoke`
- Input variants: `82`
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
- Parquet files: `64`
- CSV files: `0`
- Has local research bars: `True`

## Sample Backtest

- Trade count: `136`
- Net PnL: `-1712.9154744795487`
- Bars source: `data\silver\stocks\research_preferred_1min_20260421_20260423_stock_contracts.parquet`

## Issues

- `warning` `sample_backtest_negative_expectancy`: The current sample backtest has negative after-cost expectancy.
- `warning` `real_bar_smoke_negative_mean_expectancy`: The latest real stock-bar smoke has negative mean expectancy; use candidates only for deeper option-aware research.

## Next Build Contract

- Shard the remaining RQ-002 single-leg repair variants into bounded real stock-bar smoke tranches.
- Promote no strategy from smoke output; send only positive candidates into deeper option-aware backtests.
- Convert quarantine clusters into explicit loser filters before any runner eligibility discussion.
- Add option payoff and fill-cost simulation before treating defined-risk variants as promotable.
- Keep raw result exhaust in GCS and compact hold/kill/quarantine summaries in GitHub.
