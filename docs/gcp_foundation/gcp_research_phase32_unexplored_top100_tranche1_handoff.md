# Phase32 Unexplored Top100 Tranche1 Handoff

## Current Read

Phase32 is active as a non-broker-facing research Batch job:

- Job: `phase32-unexplored-top100-tranche1-20260428120500`
- Phase: `phase32_unexplored_top100_tranche1_20260428120500`
- Latest status: `SUCCEEDED`
- Latest task counts: `15` succeeded
- Task count: `15`
- Parallelism: `5`
- Symbols: `AMD`, `PLTR`, `GOOG`, `ORCL`, `XOM`, `XLE`, `JPM`, `UNH`, `V`, `BAC`, `CRM`, `XLI`, `GE`, `AMAT`, `TQQQ`

## Why This Exists

The top100 campaign had only explored a subset of the candidate universe. AAPL remains the only bounded-validation candidate. Phase32 redirects compute toward new unexplored candidates instead of replaying blocked wide-lag clusters.

## Monitor Commands

```powershell
gcloud batch jobs describe phase32-unexplored-top100-tranche1-20260428120500 --project codexalpaca --location us-central1 --format=json
gcloud storage ls gs://codexalpaca-control-us/research_results/top100_liquidity_research_20260426/portfolio_event_driven_data/phase32_unexplored_top100_tranche1_20260428120500/data_shards/
```

## Completion Handling

All shards succeeded. Build a portfolio-level aggregation packet from the per-symbol replay, portfolio, and promotion-review outputs before any promotion decision.

No Phase32 result is allowed to alter live manifests, risk policy, or broker-facing execution without a separate governed packet.
