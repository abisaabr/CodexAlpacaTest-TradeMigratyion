# Ex-TSLA Test Matrix

## Universe slices

- `megacap_ex_nvda_baseline`: prior mega-cap ex-NVDA universe including TSLA.
- `ex_tsla_full`: narrowed mega-cap ex-NVDA ex-TSLA universe only.
- `ex_tsla_rising_market`: ex-TSLA trades entered on SPY-tagged rising-market days.
- `ex_tsla_calm_low_vol`: ex-TSLA trades entered on calmer / low-vol days.
- `ex_tsla_strong_momentum_participation`: ex-TSLA trades entered on rising-market days with top-quartile participation across the surviving names.
- `ex_tsla_non_extreme_2_5`: ex-TSLA equity-path audit with both best and worst 2.5% of days removed.
- `remaining_single_leader_stress`: ex-TSLA days still classified as one-dominant-leader days.
- `broad_participation_only`: ex-TSLA days with multi-symbol participation and top-symbol share below 60%.

## Honest limits

- No new signal logic or parameter optimization was introduced.
- The diagnostic stays on the exact narrowed mega-cap ex-NVDA ex-TSLA universe only.
