# GCP Research Overnight 365D Bruteforce 20260429 Launch Status

## Current Read

- Status: `launched`
- Mode: `research_only_overnight_365d_bruteforce`
- Broker-facing: `false`
- Trading effect: `none`
- Live manifest effect: `none`
- Risk policy effect: `none`
- Promotion scope: `research_governed_validation_review_only`

## Top-10 Replay

- Dataset source: `option_fill_ladder_20260429/365d_5x5`
- Symbols: `SPY`, `IWM`, `NVDA`, `AAPL`, `META`, `TSLA`, `AMD`, `INTC`, `AMZN`, `MSFT`
- Strategy variants: `36` per symbol, `360` total
- Batch job: `overnight-top10-365d-replay-20260429023003`
- State at launch check: `SCHEDULED`
- Parallelism: `4`

Profiles:

- `liq_lag10_slip10_fee065`
- `liq_lag30_slip25_fee100`
- `nearest_lag10_slip10_fee065`

## Next-10 Data

- Symbols: `QQQ`, `MU`, `AVGO`, `GOOGL`, `NFLX`, `TSM`, `PLTR`, `XLE`, `ORCL`, `XOM`
- Selection rule: next 10 by existing top100 liquidity rank after excluding the current 10-symbol set
- Dataset campaign: `option_fill_ladder_next10_20260429`
- Stage: `365d_5x5`
- Batch job: `overnight-next10-365d-data-20260429023003`
- State at launch check: `SCHEDULED`
- Parallelism: `3`

## Durable Roots

- Research waves: `gs://codexalpaca-control-us/research_waves/overnight_365d_bruteforce_20260429/`
- Bruteforce results: `gs://codexalpaca-control-us/research_results/overnight_365d_bruteforce_20260429/`
- Next-10 data results: `gs://codexalpaca-control-us/research_results/option_fill_ladder_next10_20260429/`
- Next-10 option data: `gs://codexalpaca-data-us/research_option_data/option_fill_ladder_next10_20260429/`
- Next-10 stock data: `gs://codexalpaca-data-us/research_stock_data/option_fill_ladder_next10_20260429/`

## Guardrails

- Research-only jobs.
- Do not trade from raw research output.
- Do not arm an execution window from this packet.
- Do not modify live manifests, strategy selection, or risk policy from this packet.
- Do not relax the `0.90` fill gate for promotion review.
- Tomorrow's paper-session use requires a separate operator/control-plane decision after promotion-review packets are clean.

## Next Safe Step

Monitor top-10 replay and next-10 data jobs. When next-10 data passes fill gates, launch next-10 replay with the same profile stack, then aggregate promotion-review candidates.
