# Phase34 Top-Lead Exit-Lag Feasibility Status

## State

- Phase ID: `phase34_top_lead_exit_lag_feasibility_20260428172500`
- Batch job: `phase34-top-lead-exitlag-20260428172500`
- Latest state: `SUCCEEDED`
- Latest task counts: `4` succeeded
- Location: `codexalpaca/us-central1`
- Tasks: `4`
- Parallelism: `4`
- Broker-facing: `false`
- Trading effect: `none`
- Live manifest effect: `none`
- Risk policy effect: `none`

## Scope

Phase34 was a candidate-only diagnostic for the best positive-economics Phase32 leads that were still blocked by `fill_coverage_below_0.90`.

- `AMD` `b150__amd__long_call__balanced_reward__exit_360__liq_tight`
- `GE` `b150__ge__long_put__tight_reward__exit_360__liq_tight`
- `ORCL` `b150__orcl__long_call__balanced_reward__exit_360__liq_tight`
- `PLTR` `b150__pltr__long_put__balanced_reward__exit_300__liq_tight`

The job reuses existing Phase32 selected-contract and option bar/trade data. It does not pull broker-facing data, does not place orders, and does not alter any live manifest.

## Diagnostic

The diagnostic tests exit-lag feasibility at `10`, `30`, `60`, `90`, `120`, `180`, and `240` minutes with a `300` minute max probe lag. The mandatory fill gate remains `0.90`.

## Artifacts

- Report root: `gs://codexalpaca-control-us/research_results/top100_liquidity_research_20260426/portfolio_event_driven_data/phase34_top_lead_exit_lag_feasibility_20260428172500/`
- Launch worker: `gs://codexalpaca-control-us/research_results/top100_liquidity_research_20260426/portfolio_event_driven_data/phase34_top_lead_exit_lag_feasibility_20260428172500/launch/phase34_worker.sh`
- Launch config: `gs://codexalpaca-control-us/research_results/top100_liquidity_research_20260426/portfolio_event_driven_data/phase34_top_lead_exit_lag_feasibility_20260428172500/launch/phase34_batch_job.yaml`

## Result

All four candidates remain blocked. None passed the `0.90` fill gate under tested exit lags.

- `AMD` max fill `0.8333`, no passing exit lag.
- `GE` max fill `0.5811`, no passing exit lag.
- `ORCL` max fill `0.6757`, no passing exit lag.
- `PLTR` max fill `0.75`, no passing exit lag.

## Decision Boundary

No candidate can be promoted from Phase34. The four tested candidates should be treated as exit-fill-not-feasible under the current data and timing model.

## Next Safe Step

Prioritize new candidate discovery and targeted diagnostics for stronger new leads, including the Phase35 UNH exit-lag feasibility diagnostic.

Do not trade, arm a window, start broker-facing execution, modify live manifests, change risk policy, or relax the `0.90` fill gate.
