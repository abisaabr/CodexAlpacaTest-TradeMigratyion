# Phase40 Active+Inactive Contract Inventory Status

## State

- Phase ID: `phase40_active_inactive_contract_inventory_20260428175500`
- Batch job: `phase40-active-inactive-inv-20260428175500`
- Latest state: `SUCCEEDED`
- Latest task counts: `10` succeeded
- Location: `codexalpaca/us-central1`
- Tasks: `10`
- Parallelism: `4`
- Broker order/session facing: `false`
- Alpaca metadata endpoint used: `true`
- Trading effect: `none`
- Live manifest effect: `none`
- Risk policy effect: `none`

## Scope

Phase40 is a research-only contract-inventory rebuild for the top liquid diagnostic set:

`SPY`, `NVDA`, `QQQ`, `AMZN`, `TSLA`, `MSFT`, `IWM`, `AAPL`, `META`, and `MU`.

It uses runner commit `91d75fb36c7c`, which adds `scripts/download_historical_option_contract_inventory.py`. The script fetches both `active` and `inactive` Alpaca option contracts, deduplicates them, writes schema-compatible parquet inventory, and emits inventory trade-date coverage diagnostics.

## Inputs

- source archive: `gs://codexalpaca-control-us/research_source/codexalpaca_runner_source_91d75fb36c7c.zip`
- contract window: `2026-04-01` through `2026-04-23`
- DTE window: `0-7`
- contract chunk days: `7`
- statuses: `active,inactive`
- credentials: existing GCP Secret Manager secrets `execution-alpaca-paper-api-key` and `execution-alpaca-paper-secret-key`; no plaintext secrets are committed or staged

## Expected Outputs

- launch root: `gs://codexalpaca-control-us/research_results/top100_liquidity_research_20260426/portfolio_event_driven_data/phase40_active_inactive_contract_inventory_20260428175500/launch/`
- control shard root: `gs://codexalpaca-control-us/research_results/top100_liquidity_research_20260426/portfolio_event_driven_data/phase40_active_inactive_contract_inventory_20260428175500/data_shards/`
- data shard root: `gs://codexalpaca-data-us/research_option_data/top100_liquidity_research_20260426/phase40_active_inactive_contract_inventory_20260428175500/data_shards/`

## Gate

## Result

Phase40 fixed the contract-inventory coverage problem identified by Phase39.

All ten symbols reached `17/17` requested weekday contract coverage for the `0-7` DTE inventory window:

- `SPY`: `8202` contracts, `21` expiration dates
- `QQQ`: `6416` contracts, `21` expiration dates
- `IWM`: `3514` contracts, `21` expiration dates
- `META`: `3404` contracts, `12` expiration dates
- `TSLA`: `2556` contracts, `13` expiration dates
- `NVDA`: `1844` contracts, `13` expiration dates
- `MSFT`: `1594` contracts, `12` expiration dates
- `MU`: `1572` contracts, `4` expiration dates
- `AAPL`: `1342` contracts, `13` expiration dates
- `AMZN`: `1270` contracts, `13` expiration dates

## Gate

Phase40 did not download option bars/trades and cannot promote strategies. Phase41 is now launched to rerun dense selected-contract coverage against this repaired inventory. If dense selected-date coverage also reaches `0.90`, then launch option bar/trade download and strategy replay.

## Hard Rules

Do not trade, arm a window, start a broker-facing session, modify live manifests, change risk policy, or relax the `0.90` fill gate.
