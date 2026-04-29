# QQQ 365D Next-Trading-Day 5x5 Option Bars Status

Generated: `2026-04-29T01:00:38Z`

## Decision State

- Status: `complete`
- Mode: `research_only_market_data_download`
- Broker-facing: `false`
- Trading effect: `none`
- Promotion allowed: `false`
- Live manifest effect: `none`
- Risk policy effect: `none`

## Dataset

- Dataset id: `qqq_365d_next_trading_day_5x5_20260428`
- Symbol: `QQQ`
- Window: `2025-04-29` through `2026-04-28`
- Expiration selection: nearest listed expiration after the trade date
- DTE search window: `1` to `7` calendar days
- Strike range: `5` strike steps ITM and `5` strike steps OTM around ATM
- Option types: `call`, `put`
- Stock reference bar: `first`
- Runner commit: `d3bbdbb`

## Execution Lane

- Lane used: local machine
- Parallel cloud machines used: `false`
- Reason: the selected-contract workload was request-limited and completed faster locally than a GCP Batch fanout setup would have completed.

## Coverage Verdict

- Stock bars: `200994` rows, `73` chunks, `0` failed chunks
- Contract inventory: `69376` contracts, `27` chunks, `0` failed chunks
- Inventory weekday coverage: `261/261`, coverage ratio `1.0`
- Selected contracts: `5522`
- Selected trade dates: `251`
- Missing selected weekdays: `10`, all market holidays with no stock reference session
- Option-bar chunks: `251`
- Failed option-bar chunks: `0`
- Option-bar rows: `1593974`
- Contract-day coverage: `5515/5522`, ratio `0.998732`
- Missing selected contract-days: `7`
- Bars per selected contract-day: min `0`, median `336.0`, max `391`

Missing contract-days:

- `2025-07-31` `QQQ250801P00595000`
- `2025-09-10` `QQQ250911P00577000`
- `2025-11-14` `QQQ251117C00601000`
- `2025-11-14` `QQQ251117C00602000`
- `2025-11-14` `QQQ251117P00601000`
- `2025-11-14` `QQQ251117P00602000`
- `2026-03-23` `QQQ260324C00571000`

## Durable Locations

- Stock bars: `gs://codexalpaca-data-us/research_stock_data/qqq_365d_next_trading_day_5x5_20260428/stock_ref_silver/`
- Contract inventory: `gs://codexalpaca-data-us/research_option_data/qqq_365d_next_trading_day_5x5_20260428/contract_inventory_silver/`
- Option bars: `gs://codexalpaca-data-us/research_option_data/qqq_365d_next_trading_day_5x5_20260428/option_bars_silver/`
- Research wave: `gs://codexalpaca-control-us/research_results/qqq_365d_next_trading_day_5x5_20260428/research_wave/`
- Download report: `gs://codexalpaca-control-us/research_results/qqq_365d_next_trading_day_5x5_20260428/download_report/`

## Guardrails

- This is a research-only market data artifact.
- Do not trade from this packet.
- Do not arm an execution window from this packet.
- Do not modify live manifests, strategy selection, or risk policy from this packet.
- Keep the `0.90` fill gate for promotion review.

## Next Safe Step

Use this `0.998732` contract-day coverage QQQ 365-day next-trading-day dataset for QQQ-only research replay, edge search, and promotion diagnostics before any governed validation review.
