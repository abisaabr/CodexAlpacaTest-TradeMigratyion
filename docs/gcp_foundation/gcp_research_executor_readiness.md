# GCP Research Executor Readiness

## Snapshot

- Generated at: `2026-04-23T22:27:46.150328-04:00`
- Status: `blocked_full_wave_executor_missing`
- Wave id: `research_wave_20260424_bootstrap`
- Wave variants: `2070`
- Wave chunks: `21`
- GCS prefix: `gs://codexalpaca-control-us/research_executor`

## Runner Asset Status

- `historical_dataset_builder`: `True` `scripts/build_historical_dataset.py`
- `sample_backtest_runner`: `True` `scripts/run_sample_backtest.py`
- `generic_backtest_engine`: `True` `alpaca_lab/backtest/engine.py`
- `option_long_call_skeleton`: `True` `alpaca_lab/strategies/options_skeleton.py`
- `option_candidate_selector`: `True` `alpaca_lab/options/strategies.py`

## Full Wave Executor Candidates

- `run_gcp_research_wave`: `False` `scripts/run_gcp_research_wave.py`
- `run_options_research_wave`: `False` `scripts/run_options_research_wave.py`
- `run_research_wave_backtest`: `False` `scripts/run_research_wave_backtest.py`

## Data Inventory

- Data root exists: `True`
- Parquet files: `0`
- CSV files: `0`
- Has local research bars: `False`

## Sample Backtest

- Trade count: `0`
- Net PnL: `0.0`
- Bars source: `synthetic`

## Issues

- `error` `missing_full_wave_executor`: No runner script exists yet to consume the GCP research wave variants JSONL.
- `warning` `missing_local_research_bars`: No local parquet/csv research bars were found under the runner data root.
- `warning` `sample_backtest_no_trades`: The current synthetic sample backtest completed but produced zero trades.

## Next Build Contract

- Add a research-only runner script that reads gcp_research_wave_variants.jsonl.
- Executor must write research_run_manifest, normalized_backtest_results, train/test or walk-forward summary, after-cost expectancy, drawdown/tail-loss, loser-cluster comparison, and hold/kill/quarantine recommendation.
- Executor must not import broker trading paths, place orders, change live manifests, or change risk policy.
- Start with smoke chunks and single-leg repair diagnostics before treating multi-leg defined-risk variants as promotable.
- Keep raw result exhaust in GCS and compact promotion/rejection summaries in GitHub.
