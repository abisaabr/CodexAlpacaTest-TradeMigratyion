# GCP Option-Aware Backtest Status

- Generated at: `2026-04-24T00:58:28.692573-04:00`
- Status: `hold_option_economics_review`
- Run id: `option_aware_research_20260424_slv_put_top50`
- Candidate count: `50`
- Option trade count: `98`
- Max fill coverage: `0.3333`
- Mean fill coverage: `0.2113`
- Promotion allowed: `False`
- Broker facing: `False`

## Recommendation Counts

- `hold_insufficient_option_fills`: `32`
- `hold_option_fill_coverage`: `18`

## Issues

- `warning` `insufficient_option_fills`: At least one candidate lacks enough option-priced trades for promotion-grade economics.

## Next Step Contract

- Keep candidates research-only while option-aware economics remains under review.
- Inspect fill coverage, loser clusters, and train/test splits before any governance action.
