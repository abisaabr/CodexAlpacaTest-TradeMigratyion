# Options Buying Strategies Taxonomy

## Final Counts By Bucket
- core_long_premium: 6
- debit_structure: 6
- stock_hybrid: 2
- manual_review: 4

## Strategies Moved To Manual Review
- `double diagonal spread`: This is an advanced debit structure with strong front-leg management effects, so it is better isolated for manual review than treated as a clean long-premium research primitive. | sources: Fidelity
- `long calendar spread`: Call and put variants were merged in the first pass, and calendar spreads can flip between positive-theta carry and long-vega research depending on strike placement and time horizon. | sources: Fidelity; OIC
- `long diagonal spread`: Directional call and put diagonal variants were merged, but their realized gamma/theta mix can differ materially by strike selection and front-leg management. | sources: Fidelity
- `long ratio backspread`: Backspreads can be opened for either a debit or a credit and the short strike dominates path risk, so they are too structurally mixed for an automatic long-premium bucket. | sources: Fidelity; OIC

## Included Strategies That Are Not Strong Long-Premium Research Candidates
- `debit_structure` bucket: these are debit entries, but practical exposure is often neutral, carry-driven, or short-volatility despite the upfront debit.
- `stock_hybrid` bucket: these require stock plus options and behave more like hedging overlays than standalone long-premium trades.
- `manual_review` bucket: these are structurally mixed and should be normalized further before systematic testing.
- `bear put spread` -> `debit_structure`
- `bull call spread` -> `debit_structure`
- `long butterfly` -> `debit_structure`
- `long christmas tree spread` -> `debit_structure`
- `long christmas tree spread variation` -> `debit_structure`
- `long condor` -> `debit_structure`
- `double diagonal spread` -> `manual_review`
- `long calendar spread` -> `manual_review`
- `long diagonal spread` -> `manual_review`
- `long ratio backspread` -> `manual_review`
- `collar` -> `stock_hybrid`
- `protective put` -> `stock_hybrid`

## Recommended Starter Universe For Systematic Testing
- `long call`: bullish_trend_or_breakout, typical holding period `days_to_weeks`.
- `long put`: bearish_trend_or_breakdown, typical holding period `days_to_weeks`.
- `bull call spread`: moderate_bullish_trend, typical holding period `days_to_weeks`.
- `bear put spread`: moderate_bearish_trend, typical holding period `days_to_weeks`.
- `long straddle`: event_driven_breakout_or_vol_expansion, typical holding period `event_window_to_days`.
- `long strangle`: event_driven_breakout_or_vol_expansion, typical holding period `event_window_to_days`.

## Provenance Notes
- All derived CSVs retain the original source/provenance columns from the first-pass master file.
- The sources table was used here to keep manual-review items visible where source coverage was thin or variant-heavy.
- Adjacent excluded watchlist items worth separate future review:
- `cash-backed call`: Bought-call acquire-stock variant, but its primary use case is stock acquisition rather than premium-buying exposure.
- `long skip-strike butterfly`: Documented as a long butterfly-style structure, but the public source example was not clearly a debit-only buying strategy.
