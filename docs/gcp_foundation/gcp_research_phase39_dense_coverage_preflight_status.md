# Phase39 Dense Coverage Preflight Status

## State

- Phase ID: `phase39_dense_coverage_preflight_20260428214000`
- Batch job: `phase39-dense-coverage-20260428214000`
- Latest state: `SCHEDULED`
- Latest task counts: `4` pending at last check
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

Phase38 exposed a likely input defect: dense-universe packets selected only `4` trade dates. Phase39 tests whether the curated top-150 stock bars produce full selected-date coverage before launching another expensive option download and replay.

## Gate

If Phase39 coverage diagnostics are `ok`, the next safe action is a corrected dense option data download/replay lane using the same complete stock reference source. If diagnostics are not `ok`, repair the stock/reference inputs first.

## Hard Rules

Do not trade, arm a window, start a broker-facing session, modify live manifests, change risk policy, or relax the `0.90` fill gate.
