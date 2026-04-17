# Ex-AAPL / Ex-META Test Matrix

## Dependency-removal slices

- `ex_tsla_full`: baseline narrowed mega-cap ex-NVDA ex-TSLA universe.
- `broad_participation_only`: baseline ex-TSLA book, filtered to days with multi-symbol participation, top-symbol share <= 60%, at least two profitable symbols, and at least three traded symbols.
- `ex_aapl_full`: full rerun with `AAPL` removed from the ex-TSLA universe.
- `ex_aapl_broad_participation_only`: ex-AAPL rerun filtered to the same honest broad-participation day rules.
- `ex_meta_full`: full rerun with `META` removed from the ex-TSLA universe.
- `ex_meta_broad_participation_only`: ex-META rerun filtered to the same honest broad-participation day rules.
- `ex_aapl_rising_market`: ex-AAPL rerun filtered to `rising_market` entry days.
- `ex_meta_rising_market`: ex-META rerun filtered to `rising_market` entry days.
- `ex_aapl_non_extreme_2_5`: ex-AAPL rerun with both best and worst 2.5% of days removed from the equity-path audit.
- `ex_meta_non_extreme_2_5`: ex-META rerun with both best and worst 2.5% of days removed from the equity-path audit.

## Honest limits

- No new signal logic or parameter search was introduced.
- Cross-sectional books were rerun on reduced universes rather than masked after the fact.
