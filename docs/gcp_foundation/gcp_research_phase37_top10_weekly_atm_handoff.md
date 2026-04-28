# Phase37 Top10 Weekly ATM Handoff

## Current Read

Phase37 is active as a non-broker-facing research Batch job:

- Job: `phase37-top10-atm-20260428183723`
- Phase: `phase37_top10_weekly_atm_20260428183723`
- Latest status: `SCHEDULED`
- Latest task counts: `6` pending
- Task count: `10`
- Parallelism: `5`
- Symbols: `SPY`, `NVDA`, `QQQ`, `AMZN`, `TSLA`, `MSFT`, `IWM`, `AAPL`, `META`, `MU`
- Contract scope: ATM-only, `0-7` DTE, liquidity-first replay

## Monitor Commands

```powershell
gcloud batch jobs describe phase37-top10-atm-20260428183723 --project codexalpaca --location us-central1 --format=json
gcloud storage ls gs://codexalpaca-control-us/research_results/top100_liquidity_research_20260426/portfolio_event_driven_data/phase37_top10_weekly_atm_20260428183723/data_shards/
```

## Completion Handling

If shards succeed, include their per-symbol replay, portfolio, and promotion-review outputs in the next portfolio-level aggregation. If a shard fails, inspect its `logs/run.err.log` and repair only that affected symbol.

No Phase37 result is allowed to alter live manifests, risk policy, or broker-facing execution without a separate governed packet.
