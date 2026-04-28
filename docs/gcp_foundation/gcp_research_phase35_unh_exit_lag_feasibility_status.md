# Phase35 UNH Exit-Lag Feasibility Status

## State

- Phase ID: `phase35_unh_exit_lag_feasibility_20260428174200`
- Batch job: `phase35-unh-exitlag-20260428174200`
- Latest state: `SCHEDULED`
- Latest task counts: `1` pending
- Location: `codexalpaca/us-central1`
- Tasks: `1`
- Parallelism: `1`
- Broker-facing: `false`
- Trading effect: `none`
- Live manifest effect: `none`
- Risk policy effect: `none`

## Scope

Phase35 is a candidate-only diagnostic for the new highest-economic Phase32 lead:

- `UNH` `b150__unh__long_call__tight_reward__exit_360__liq_baseline`
- Prior minimum net PnL: `$5870.42`
- Prior minimum test net PnL: `$3885.025`
- Prior minimum fill coverage: `0.5472`
- Prior worst drawdown: `$-899.7375`

The job reuses existing Phase32 selected-contract and option bar/trade data. It does not pull broker-facing data, place orders, or alter any live manifest.

## Diagnostic

The diagnostic tests exit-lag feasibility at `10`, `30`, `60`, `90`, `120`, `180`, and `240` minutes with a `300` minute max probe lag. The mandatory fill gate remains `0.90`.

## Next Safe Step

Monitor Phase35. If UNH passes the `0.90` fill gate under practical lags, run isolated economic stress before any governed-validation recommendation.

Do not trade, arm a window, start broker-facing execution, modify live manifests, change risk policy, or relax the `0.90` fill gate.
