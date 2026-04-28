# Phase41 Dense Coverage On Phase40 Inventory Status

## State

- Phase ID: `phase41_dense_coverage_on_phase40_inventory_20260428181000`
- Batch job: `phase41-dense-coverage-20260428181000`
- Latest state: `SUCCEEDED`
- Latest task counts: `10` succeeded
- Location: `codexalpaca/us-central1`
- Tasks: `10`
- Parallelism: `5`
- Broker-facing: `false`
- Trading effect: `none`
- Live manifest effect: `none`
- Risk policy effect: `none`

## Scope

Phase41 is a research-only dense selected-contract coverage preflight. It uses the repaired Phase40 active+inactive contract inventory and the curated top-150 stock reference parquet.

Symbols:

`SPY`, `NVDA`, `QQQ`, `AMZN`, `TSLA`, `MSFT`, `IWM`, `AAPL`, `META`, and `MU`.

Dense selected-contract rules:

- window: `2026-04-01` through `2026-04-23`
- DTE: `0-7`
- strikes: ATM +/- `5`
- reference bar: first RTH stock bar

## Inputs

- source archive: `gs://codexalpaca-control-us/research_source/codexalpaca_runner_source_91d75fb36c7c.zip`
- stock reference source: `gs://codexalpaca-data-us/curated/stocks/research_150_1min_20260401_20260423_stock_only.parquet`
- contract inventory source: `gs://codexalpaca-data-us/research_option_data/top100_liquidity_research_20260426/phase40_active_inactive_contract_inventory_20260428175500/data_shards/<SYMBOL>/silver/option_contract_inventory/`

## Gate

## Result

Phase41 passed the dense selected-contract coverage gate for all ten top-liquid symbols.

Every symbol reached `16/17` requested weekdays (`0.941176`) for dense selected contracts. The remaining weekday gap is the market holiday/non-trading date, not an option-inventory failure.

Selected contract counts:

- `SPY`: `2068` selected rows, `1088` unique contracts
- `QQQ`: `2068` selected rows, `1228` unique contracts
- `IWM`: `2068` selected rows, `834` unique contracts
- `AAPL`: `1254` selected rows, `352` unique contracts
- `AMZN`: `1254` selected rows, `406` unique contracts
- `NVDA`: `1254` selected rows, `372` unique contracts
- `META`: `1210` selected rows, `616` unique contracts
- `MSFT`: `1210` selected rows, `456` unique contracts
- `TSLA`: `1210` selected rows, `512` unique contracts
- `MU`: `396` selected rows, `180` unique contracts

## Gate

Phase42 is now launched for option bar/trade download and strategy replay. Promotion remains gated by `>=0.90` fill coverage, sufficient option trades, positive holdout/test economics, and stress survival.

## Hard Rules

Do not trade, arm a window, start a broker-facing session, modify live manifests, change risk policy, or relax the `0.90` fill gate.
