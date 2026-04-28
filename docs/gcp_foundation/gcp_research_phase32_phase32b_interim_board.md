# Phase32/Phase32b Interim Board

## State

- Generated at: `2026-04-28T17:20:33Z`
- Completed shards scanned: `11`
- New governed-validation candidates: `0`
- Dominant blocker: `fill_coverage_below_0.90`
- Broker-facing: `false`
- Live manifest effect: `none`
- Risk policy effect: `none`

## Active Jobs

- `phase32-unexplored-top100-tranche1-20260428120500`: `RUNNING`, `9` succeeded / `5` running / `1` pending.
- `phase32b-unexplored-top100-tranche2-20260428122500`: `RUNNING`, `2` succeeded / `2` running / `11` pending.

## Best Research-Only Leads

- `AMD` `b150__amd__long_call__balanced_reward__exit_360__liq_tight`: min net `$5834.6425`, min test `$2713.1575`, fill `0.6923`, worst drawdown `$-1435.7275`.
- `GE` `b150__ge__long_put__tight_reward__exit_360__liq_tight`: min net `$4128.955`, min test `$2747.52`, fill `0.2703`, worst drawdown `$-1331.36`.
- `ORCL` `b150__orcl__long_call__balanced_reward__exit_360__liq_tight`: min net `$3584.26`, min test `$4254.38`, fill `0.4865`, worst drawdown `$-5076.86`.
- `PLTR` `b150__pltr__long_put__balanced_reward__exit_300__liq_tight`: min net `$2860.17`, min test `$2353.3925`, fill `0.625`, worst drawdown `$-1832.59`.

## Decision

No new candidate is eligible for governed validation from the completed shards. Positive-economics names are fill-repair research leads only.

## Next Safe Step

Wait for the remaining shards to complete, then build Phase33 portfolio-level aggregation from completed promotion packets. Do not trade, arm a window, start broker-facing execution, modify live manifests, change risk policy, or relax the `0.90` fill gate.
