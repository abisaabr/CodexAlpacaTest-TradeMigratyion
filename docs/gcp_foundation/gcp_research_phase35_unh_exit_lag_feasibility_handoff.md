# Phase35 UNH Exit-Lag Feasibility Handoff

## Current Read

Phase35 is active as a non-broker-facing research Batch diagnostic:

- Job: `phase35-unh-exitlag-20260428174200`
- Phase: `phase35_unh_exit_lag_feasibility_20260428174200`
- Latest status: `SUCCEEDED`
- Latest task counts: `1` succeeded
- Candidate: `UNH` `b150__unh__long_call__tight_reward__exit_360__liq_baseline`

## Why This Exists

The expanded Phase32 scan found UNH as the highest positive research-only lead so far, with strong minimum net and test PnL but fill coverage below the mandatory `0.90` gate. Phase35 checks whether the fill gap is exit-timing repairable before spending compute on economic stress.

## Monitor Commands

```powershell
gcloud batch jobs describe phase35-unh-exitlag-20260428174200 --project codexalpaca --location us-central1 --format=json
gcloud storage ls gs://codexalpaca-control-us/research_results/top100_liquidity_research_20260426/portfolio_event_driven_data/phase35_unh_exit_lag_feasibility_20260428174200/data_shards/
```

## Completion Handling

UNH did not pass the `0.90` fill gate under any tested exit lag. Maximum fill coverage was `0.6792`, so UNH remains research-only blocked.

Treat UNH as a research-only lead requiring liquidity/data/strategy redesign. Do not run economic stress or governed-validation promotion from this result.

No Phase35 result is allowed to alter live manifests, risk policy, or broker-facing execution without a separate governed packet.
