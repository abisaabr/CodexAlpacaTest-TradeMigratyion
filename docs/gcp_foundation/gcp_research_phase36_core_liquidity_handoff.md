# Phase36 Core Liquidity Handoff

## Current Read

Phase36 is active as a non-broker-facing research Batch job:

- Job: `phase36-core-liq-20260428180637`
- Phase: `phase36_core_liquidity_tranche_20260428180637`
- Latest status: `RUNNING`
- Latest task counts: `5` succeeded / `4` running / `6` pending
- Task count: `15`
- Parallelism: `4`
- Symbols: `SPY`, `QQQ`, `IWM`, `TSLA`, `TSM`, `EFA`, `EEM`, `XLF`, `XLV`, `EWZ`, `WFC`, `GLD`, `NKE`, `XLP`, `XBI`
- Visible completed shards: `GLD`, `IWM`, `QQQ`, `SPY`, `TSLA`, `WFC`

## Monitor Commands

```powershell
gcloud batch jobs describe phase36-core-liq-20260428180637 --project codexalpaca --location us-central1 --format=json
gcloud storage ls gs://codexalpaca-control-us/research_results/top100_liquidity_research_20260426/portfolio_event_driven_data/phase36_core_liquidity_tranche_20260428180637/data_shards/
```

## Completion Handling

If shards succeed, include their per-symbol replay, portfolio, and promotion-review outputs in the next portfolio-level aggregation. If a shard fails, inspect its `logs/run.err.log` and repair only that affected symbol.

No Phase36 result is allowed to alter live manifests, risk policy, or broker-facing execution without a separate governed packet.
