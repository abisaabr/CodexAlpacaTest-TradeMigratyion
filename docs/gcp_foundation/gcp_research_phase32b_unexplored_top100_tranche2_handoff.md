# Phase32b Unexplored Top100 Tranche2 Handoff

## Current Read

Phase32b is active as a non-broker-facing research Batch job:

- Job: `phase32b-unexplored-top100-tranche2-20260428122500`
- Phase: `phase32b_unexplored_top100_tranche2_20260428122500`
- Latest status: `SCHEDULED`
- Latest task counts: `3` pending
- Task count: `15`
- Parallelism: `3`
- Symbols: `NOW`, `BKNG`, `MA`, `CSCO`, `JNJ`, `CVX`, `WMT`, `HOOD`, `KRE`, `CAT`, `GS`, `IBM`, `SLV`, `XLK`, `BA`

## Monitor Commands

```powershell
gcloud batch jobs describe phase32b-unexplored-top100-tranche2-20260428122500 --project codexalpaca --location us-central1 --format=json
gcloud storage ls gs://codexalpaca-control-us/research_results/top100_liquidity_research_20260426/portfolio_event_driven_data/phase32b_unexplored_top100_tranche2_20260428122500/data_shards/
```

## Completion Handling

If shards succeed, include their per-symbol replay, portfolio, and promotion-review outputs in the Phase33 portfolio-level aggregation. If a shard fails, inspect its `logs/run.err.log` and repair only that affected symbol.

No Phase32b result is allowed to alter live manifests, risk policy, or broker-facing execution without a separate governed packet.

Note: the Phase32b worker reuses the Phase32 build-name template, so per-symbol data roots use `top100_phase32_<SYMBOL>_unexplored_options_20260302_20260423` even though the report root is under `phase32b_unexplored_top100_tranche2_20260428122500`.
