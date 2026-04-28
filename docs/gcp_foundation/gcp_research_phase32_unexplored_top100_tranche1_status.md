# Phase32 Unexplored Top100 Tranche1 Status

## State

- Phase ID: `phase32_unexplored_top100_tranche1_20260428120500`
- Batch job: `phase32-unexplored-top100-tranche1-20260428120500`
- Latest state: `RUNNING`
- Latest task counts: `9` succeeded / `5` running / `1` pending
- Location: `codexalpaca/us-central1`
- Tasks: `15`
- Parallelism: `5`
- Broker-facing: `false`
- Trading effect: `none`
- Live manifest effect: `none`
- Risk policy effect: `none`

## Scope

Phase32 expands option-aware research coverage beyond the already-tested top100 symbols. The symbol tranche is:

`AMD`, `PLTR`, `GOOG`, `ORCL`, `XOM`, `XLE`, `JPM`, `UNH`, `V`, `BAC`, `CRM`, `XLI`, `GE`, `AMAT`, `TQQQ`.

Each task filters the canonical top100 queue to one symbol, builds event-driven selected contracts, downloads historical option bars/trades through Alpaca in research-only mode, then runs three option-aware stress profiles.

## Gate

No Phase32 output can be promoted directly. A portfolio-level aggregation packet is required after all shards finish cleanly. The `0.90` fill-coverage gate remains mandatory.

## Next Safe Step

Monitor the Batch job and shard artifacts under:

`gs://codexalpaca-control-us/research_results/top100_liquidity_research_20260426/portfolio_event_driven_data/phase32_unexplored_top100_tranche1_20260428120500/`

If all shards succeed, aggregate per-symbol promotion packets into a portfolio-level review. If any shard fails, repair only the affected symbol shard.

## Hard Rules

Do not trade, arm a window, start a broker-facing session, modify live manifests, change risk policy, or relax the `0.90` fill gate.
