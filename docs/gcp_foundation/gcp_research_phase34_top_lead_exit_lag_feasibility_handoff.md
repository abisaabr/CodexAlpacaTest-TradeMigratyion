# Phase34 Top-Lead Exit-Lag Feasibility Handoff

## Current Read

Phase34 is active as a non-broker-facing research Batch diagnostic:

- Job: `phase34-top-lead-exitlag-20260428172500`
- Phase: `phase34_top_lead_exit_lag_feasibility_20260428172500`
- Latest status: `SUCCEEDED`
- Latest task counts: `4` succeeded
- Task count: `4`
- Parallelism: `4`
- Symbols: `AMD`, `GE`, `ORCL`, `PLTR`

## Why This Exists

Phase32 found several candidates with strong research-only economics but sub-`0.90` fill coverage. Replaying broader research unchanged is lower value than identifying whether these candidates fail because of data sparsity, exit timing, or strategy design.

## Monitor Commands

```powershell
gcloud batch jobs describe phase34-top-lead-exitlag-20260428172500 --project codexalpaca --location us-central1 --format=json
gcloud storage ls gs://codexalpaca-control-us/research_results/top100_liquidity_research_20260426/portfolio_event_driven_data/phase34_top_lead_exit_lag_feasibility_20260428172500/data_shards/
```

## Completion Result

All four tested candidates remain research-only blocked:

- `AMD`: max fill `0.8333`, no passing exit lag.
- `GE`: max fill `0.5811`, no passing exit lag.
- `ORCL`: max fill `0.6757`, no passing exit lag.
- `PLTR`: max fill `0.75`, no passing exit lag.

## Completion Handling

Inspect each shard's `exit_lag_feasibility` output and classify candidates as:

- `fill_feasible_short_lag`: candidate may proceed to isolated economic stress.
- `wide_lag_only`: candidate needs an explicit exit-policy design packet before any stress.
- `not_fill_feasible`: quarantine or redesign; do not rerun unchanged.

No Phase34 result is allowed to alter live manifests, risk policy, or broker-facing execution. The safe follow-up is new candidate search or targeted diagnostics for stronger leads such as Phase35 UNH.
