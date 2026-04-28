# Phase37 Top10 Weekly ATM Status

## State

- Phase ID: `phase37_top10_weekly_atm_20260428183723`
- Batch job: `phase37-top10-atm-20260428183723`
- Latest state: `SUCCEEDED`
- Latest task counts: `10` succeeded / `0` failed
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

All `10` shards completed. The completed shard reports were aggregated in the Phase37 rollup packet.

## Rollup Result

- Source reports: `10`
- Candidates scanned: `183`
- Eligible for promotion review: `0`
- Research-only capital-plan rows: `0`
- Fill-failure map: `selected_contract_universe_gap=183`
- Maximum minimum-fill coverage: `0.1111`
- Median minimum-fill coverage: `0.0676`

The tight ATM-only `0-7` DTE lane did not repair fill. It made the contract universe too narrow for the current strategy repo and should not be used as the promotion path.

## Gate

No Phase37 output can be promoted directly. Completed shards must enter portfolio-level aggregation and promotion review. The `0.90` fill-coverage gate remains mandatory.

## Hard Rules

Do not trade, arm a window, start a broker-facing session, modify live manifests, change risk policy, or relax the `0.90` fill gate.
