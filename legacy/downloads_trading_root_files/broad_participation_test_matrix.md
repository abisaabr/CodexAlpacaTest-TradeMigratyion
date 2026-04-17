# Broad-Participation Test Matrix

## Confirmation / falsification slices

- `ex_tsla_full`: narrowed mega-cap ex-NVDA ex-TSLA universe only.
- `broad_participation_only`: entry-day filter requiring `participation_type = multi_symbol_driven`, `top_symbol_pct_of_day_pnl <= 60`, `positive_symbols_count >= 2`, and `number_of_symbols_traded >= 3`.
- `broad_participation_rising_market`: the same broad-participation filter intersected with `rising_market`.
- `broad_participation_strong_momentum`: the same broad-participation filter intersected with `strong_momentum_participation`.
- `broad_participation_non_extreme_2_5`: equity-path audit on the broad-participation slice with both best and worst 2.5% of days removed.
- `leader_dominant_only`: days explicitly classified as `one_dominant_leader_day` or `one_symbol_driven`, or with top-symbol share >= 70%.
- `mixed_unclear_only`: the residual days that are neither clean broad-participation days nor clean leader-dominant days.

## Honest limits

- No new signal logic or parameter optimization was introduced.
- These are post-trade day filters on the exact same ex-TSLA books, not new strategies.
