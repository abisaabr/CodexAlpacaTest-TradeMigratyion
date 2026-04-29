# QQQ 30D 1DTE ATM Option Bars Status

## State

- Status: `complete`
- Mode: `research_only_market_data_download`
- Broker-facing: `false`
- Trading effect: `none`
- Live manifest effect: `none`
- Risk policy effect: `none`
- Promotion allowed: `false`

## Scope

- Symbol: `QQQ`
- Window: `2026-03-30` through `2026-04-28`
- DTE definition: strict calendar days to expiration
- DTE filter: `1` to `1`
- Contract selection: ATM call and ATM put per covered trade date
- ATM reference: first intraday stock bar
- Strike steps: `0`
- Option bars: Alpaca `1Min`

## Result

- Active+inactive contract inventory count: `6728`
- Inventory failed chunks: `0`
- Requested weekday dates: `22`
- Strict 1-DTE covered dates: `17`
- Selected contracts: `34`
- Selected contract partitions: `17`
- Option-bar chunks: `17`
- Option-bar failed chunks: `0`
- Option-bar rows: `11369`
- Contracts with any bar: `34/34`
- Contract-day any-bar coverage: `1.0`
- Contract-day bar rows: min `75`, median `369.5`, max `391`

Missing strict calendar 1-DTE selected dates: `2026-04-02`, `2026-04-03`, `2026-04-10`, `2026-04-17`, and `2026-04-24`.

The missing dates are a semantics issue, not an API failure: strict calendar `1 DTE` excludes days where the next listed expiry is not exactly one calendar day away or the market was closed. If we want "next trading-day expiry" instead of strict calendar `1 DTE`, we should build a separate next-expiration selector and compare it to this dataset.

## Durable Roots

- Stock reference: `gs://codexalpaca-data-us/research_stock_data/qqq_30d_1dte_atm_20260428/stock_ref_silver/`
- Contract inventory: `gs://codexalpaca-data-us/research_option_data/qqq_30d_1dte_atm_20260428/contract_inventory_silver/`
- Dense selected contracts: `gs://codexalpaca-control-us/research_results/qqq_30d_1dte_atm_20260428/research_wave/`
- Option bars: `gs://codexalpaca-data-us/research_option_data/qqq_30d_1dte_atm_20260428/option_bars_silver/`
- Download report: `gs://codexalpaca-control-us/research_results/qqq_30d_1dte_atm_20260428/download_report/`

## Next Safe Step

Use this dataset for QQQ-only fill diagnostics and strategy testing. Do not treat it as promotion evidence by itself; promotion still requires the unchanged `0.90` fill gate, positive holdout economics, governed stress packets, and broker-audited bounded paper validation.

## Hard Rules

Do not trade, arm a window, start a broker-facing paper/live session, modify live manifests, change risk policy, or relax the `0.90` fill gate.
