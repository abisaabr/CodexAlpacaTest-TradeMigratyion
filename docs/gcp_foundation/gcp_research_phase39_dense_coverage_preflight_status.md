# Phase39 Dense Coverage Preflight Status

## State

- Phase ID: `phase39_dense_coverage_preflight_20260428214000`
- Batch job: `phase39-dense-coverage-20260428214000`
- Latest state: `SUCCEEDED`
- Latest task counts: `10` succeeded
- Location: `codexalpaca/us-central1`
- Tasks: `10`
- Parallelism: `4`
- Broker-facing: `false`
- Trading effect: `none`
- Live manifest effect: `none`
- Risk policy effect: `none`

## Scope

Phase39 is a research-only coverage preflight, not a replay or promotion packet. It uses runner commit `b6e48cddce0f`, which adds dense-universe coverage diagnostics.

The job tests `SPY`, `NVDA`, `QQQ`, `AMZN`, `TSLA`, `MSFT`, `IWM`, `AAPL`, `META`, and `MU` using:

- curated stock reference source: `gs://codexalpaca-data-us/curated/stocks/research_150_1min_20260401_20260423_stock_only.parquet`
- option contract inventory: `top100_contract_inventory_20260302_20260423_shard_01` through `shard_10`
- dense universe: `0-7` DTE, ATM +/- `5` strikes, first RTH stock bar reference
- window: `2026-04-01` through `2026-04-23`

## Purpose

Phase38 exposed a likely input defect: dense-universe packets selected only `4` trade dates. Phase39 tested whether the curated top-150 stock bars produce full selected-date coverage before launching another expensive option download and replay.

## Result

Phase39 confirmed the bottleneck is option contract inventory coverage, not stock reference bars.

Across all ten symbols (`SPY`, `NVDA`, `QQQ`, `AMZN`, `TSLA`, `MSFT`, `IWM`, `AAPL`, `META`, `MU`):

- stock reference coverage was usable: `16/17` requested weekdays for every symbol, with the expected non-trading holiday gap on `2026-04-03`
- selected dense contract coverage failed: most symbols selected only `4/17` requested weekdays (`2026-04-20` through `2026-04-23`)
- `MU` selected `0/17` weekdays
- every packet returned `selected_contract_trade_date_coverage_gap`

The old top100 contract inventory only exposed recent active/future contracts for this dense `0-7` DTE lane. It is not a valid foundation for historical fill-rate testing.

## Gate

The next safe action is Phase40: rebuild top-10 contract inventory with the proven QQQ cleanroom pattern of fetching both `active` and `inactive` contracts, then rerun dense coverage preflight before downloading option bars/trades.

## Hard Rules

Do not trade, arm a window, start a broker-facing session, modify live manifests, change risk policy, or relax the `0.90` fill gate.
