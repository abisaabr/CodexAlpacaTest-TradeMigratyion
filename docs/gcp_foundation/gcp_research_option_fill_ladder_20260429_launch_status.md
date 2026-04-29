# GCP Research Option Fill Ladder 20260429 Launch Status

## Current Read

- Status: `launched`
- Mode: `research_only_option_fill_ladder`
- Broker-facing: `false`
- Trading effect: `none`
- Live manifest effect: `none`
- Risk policy effect: `none`
- Latest complete market session: `2026-04-28`
- Runner source: `CodexAlpacaTest-Trade` branch `codex/qqq-paper-portfolio`, commit `d1ac3b6`
- Source archive: `gs://codexalpaca-control-us/research_source/codexalpaca_runner_source_d1ac3b6.zip`

## Scope

Symbols are deduped to:

- `SPY`
- `IWM`
- `NVDA`
- `AAPL`
- `META`
- `TSLA`
- `AMD`
- `INTC`
- `AMZN`
- `MSFT`

Stages:

- `7d_atm`: `2026-04-22` through `2026-04-28`, nearest listed expiration after trade date, ATM call/put.
- `30d_atm`: `2026-03-30` through `2026-04-28`, nearest listed expiration after trade date, ATM call/put.
- `30d_5x5`: `2026-03-30` through `2026-04-28`, nearest listed expiration after trade date, 5 strike steps ITM/OTM, calls and puts.
- `365d_5x5`: `2025-04-29` through `2026-04-28`, nearest listed expiration after trade date, 5 strike steps ITM/OTM, calls and puts.

All stages use a `1` to `7` calendar-day DTE search window and select the nearest listed expiration after each trade date.

## Active Batch Jobs

- `fill-ladder-7d-atm-20260429014336`: `SCHEDULED`, `10` tasks, parallelism `10`, `e2-standard-4`, `100GB`.
- `fill-ladder-30d-atm-20260429014336`: `SCHEDULED`, `10` tasks, parallelism `8`, `e2-standard-4`, `100GB`.
- `fill-ladder-30d-5x5-20260429014336`: `SCHEDULED`, `10` tasks, parallelism `6`, `e2-standard-4`, `150GB`.
- `fill-ladder-365d-5x5-20260429014336`: `SCHEDULED`, `10` tasks, parallelism `4`, `e2-standard-4`, `250GB`.

## Durable Roots

- Control results: `gs://codexalpaca-control-us/research_results/option_fill_ladder_20260429/`
- Option data: `gs://codexalpaca-data-us/research_option_data/option_fill_ladder_20260429/`
- Stock data: `gs://codexalpaca-data-us/research_stock_data/option_fill_ladder_20260429/`
- Batch logs: `gs://codexalpaca-control-us/research_results/option_fill_ladder_20260429/logs/`

## Guardrails

- Research-only data download and fill diagnostic.
- Do not trade from this packet.
- Do not arm an execution window from this packet.
- Do not start a broker-facing paper or live session from this packet.
- Do not modify live manifests, strategy selection, or risk policy from this packet.
- Do not relax the `0.90` fill gate for promotion review.

## Next Safe Step

Monitor Batch completion, aggregate per-symbol/per-stage `fill_ladder_status` packets, then decide whether to run strategy replay only on datasets meeting the `0.90` fill gate.
