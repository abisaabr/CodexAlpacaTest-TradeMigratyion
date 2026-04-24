# GCP Option-Aware Backtest Status

- Generated at: `2026-04-23T23:38:17.266891-04:00`
- Status: `blocked_insufficient_option_fills`
- Run id: `option_aware_research_20260424_gld_put_top25_lag60_diagnostic`
- Candidate count: `25`
- Option trade count: `20`
- Max fill coverage: `0.3333`
- Mean fill coverage: `0.1368`
- Promotion allowed: `False`
- Broker facing: `False`

## Recommendation Counts

- `hold_insufficient_option_fills`: `25`

## Issues

- `warning` `insufficient_option_fills`: At least one candidate lacks enough option-priced trades for promotion-grade economics.

## Next Step Contract

- Do not promote or deploy any option-aware candidate from this packet.
- Expand option quote/bar coverage for queued contracts before rerunning economics.
- Treat sparse positive PnL as diagnostic only until minimum-fill and out-of-sample gates pass.
