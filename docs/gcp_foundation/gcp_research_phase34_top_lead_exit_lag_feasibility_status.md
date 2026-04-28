# Phase34 Top-Lead Exit-Lag Feasibility Status

## State

- Phase ID: `phase34_top_lead_exit_lag_feasibility_20260428172500`
- Batch job: `phase34-top-lead-exitlag-20260428172500`
- Latest state: `SCHEDULED`
- Latest task counts: `4` pending
- Location: `codexalpaca/us-central1`
- Tasks: `4`
- Parallelism: `4`
- Broker-facing: `false`
- Trading effect: `none`
- Live manifest effect: `none`
- Risk policy effect: `none`

## Scope

Phase34 is a candidate-only diagnostic for the best positive-economics Phase32 leads that are still blocked by `fill_coverage_below_0.90`.

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

## Decision Boundary

No candidate can be promoted directly from Phase34. Phase34 only classifies whether the fill gap is repairable by exit-policy timing, wide-lag-only behavior, or a strategy/data-design issue.

## Next Safe Step

Monitor the four shard outputs. If a candidate passes the `0.90` fill gate under practical lags, run isolated economic stress before any governed-validation recommendation.

Do not trade, arm a window, start broker-facing execution, modify live manifests, change risk policy, or relax the `0.90` fill gate.
