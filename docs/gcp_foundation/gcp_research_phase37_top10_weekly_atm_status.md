# Phase37 Top10 Weekly ATM Status

## State

- Phase ID: `phase37_top10_weekly_atm_20260428183723`
- Batch job: `phase37-top10-atm-20260428183723`
- Latest state: `RUNNING`
- Latest task counts: `4` succeeded / `5` running / `1` pending
- Location: `codexalpaca/us-central1`
- Tasks: `10`
- Parallelism: `5`
- Broker-facing: `false`
- Trading effect: `none`
- Live manifest effect: `none`
- Risk policy effect: `none`

## Scope

Phase37 runs a research-only top-10 liquid-underlying sweep across:

`SPY`, `NVDA`, `QQQ`, `AMZN`, `TSLA`, `MSFT`, `IWM`, `AAPL`, `META`, and `MU`.

The option universe is intentionally tight: ATM-only contracts, `0-7` DTE, then `entry_liquidity_first_research_only` replay chooses the contract with the strongest entry-window prints/volume. This is designed to test whether fill coverage improves when contract choice is liquidity-first from the start.

Visible completed shard count at this checkpoint: `4`. Completed shards must be aggregated before any promotion-board change.

## Gate

No Phase37 output can be promoted directly. Completed shards must enter portfolio-level aggregation and promotion review. The `0.90` fill-coverage gate remains mandatory.

## Hard Rules

Do not trade, arm a window, start a broker-facing session, modify live manifests, change risk policy, or relax the `0.90` fill gate.
