# QQQ Next-Trading-Day 5x5 Option Bars Status

Generated: `2026-04-29T00:50:14Z`

## Decision State

- Status: `complete`
- Mode: `research_only_market_data_download`
- Broker-facing: `false`
- Trading effect: `none`
- Promotion allowed: `false`
- Live manifest effect: `none`
- Risk policy effect: `none`

## Dataset

- Dataset id: `qqq_30d_next_trading_day_5x5_20260428`
- Symbol: `QQQ`
- Window: `2026-03-30` through `2026-04-28`
- Expiration selection: nearest listed expiration after the trade date
- DTE search window: `1` to `7` calendar days
- Strike range: `5` strike steps ITM and `5` strike steps OTM around ATM
- Option types: `call`, `put`
- Stock reference bar: `first`
- Runner commit: `d3bbdbb`

## Coverage Verdict

- Contract inventory: `8174` contracts, `6` chunks, `0` failed chunks
- Inventory weekday coverage: `22/22`, coverage ratio `1.0`
- Selected contracts: `462`
- Selected trade dates: `21`
- Missing selected trade date: `2026-04-03`, because the stock reference has no market session for that holiday
- Option-bar chunks: `21`
- Failed option-bar chunks: `0`
- Option-bar rows: `141043`
- Contract-day coverage: `462/462`, ratio `1.0`
- Missing selected contract-days: `0`
- Bars per selected contract-day: min `15`, median `350.0`, max `391`

## Durable Locations

- Stock bars: `gs://codexalpaca-data-us/research_stock_data/qqq_30d_next_trading_day_5x5_20260428/stock_ref_silver/`
- Contract inventory: `gs://codexalpaca-data-us/research_option_data/qqq_30d_next_trading_day_5x5_20260428/contract_inventory_silver/`
- Option bars: `gs://codexalpaca-data-us/research_option_data/qqq_30d_next_trading_day_5x5_20260428/option_bars_silver/`
- Research wave: `gs://codexalpaca-control-us/research_results/qqq_30d_next_trading_day_5x5_20260428/research_wave/`
- Download report: `gs://codexalpaca-control-us/research_results/qqq_30d_next_trading_day_5x5_20260428/download_report/`

## Guardrails

- This is a research-only market data artifact.
- Do not trade from this packet.
- Do not arm an execution window from this packet.
- Do not modify live manifests, strategy selection, or risk policy from this packet.
- Keep the `0.90` fill gate for promotion review.

## Next Safe Step

Use this `1.0` contract-day coverage QQQ next-trading-day dataset for research-only fill diagnostics and strategy replay before any governed promotion review.
