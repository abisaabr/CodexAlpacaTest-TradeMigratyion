# Mega-Cap Ex-NVDA Test Grid

## Universe / regime slices

- `megacap_full`: narrowed mega-cap ex-NVDA universe only.
- `megacap_rising_market`: native narrowed-universe trades entered on SPY-tagged rising-market days.
- `megacap_calm_low_vol`: native narrowed-universe trades entered on calmer / low-vol days.
- `megacap_strong_momentum_participation`: native narrowed-universe trades entered on rising-market days with top-quartile mega-cap participation.
- `megacap_non_extreme_2_5`: equity-path audit with both best and worst 2.5% of days removed.

## RS wrappers

- `rs_top3_native`: canonical RS top-3 on the narrowed universe.
- `rs_top2_native`: clean rank-depth reduction to top-2.
- `rs_top3_equal_weight`: native top-3 trades with equal-weight symbol budget.
- `rs_top3_cap20`: native top-3 trades with ex-post 20% top-symbol cap audit wrapper.
- `rs_top2_equal_weight`: reduced rank-depth plus equal-weight symbol budget.

## CSM wrappers

- `csm_native`: native CSM on the narrowed universe.
- `csm_equal_weight`: native CSM trades with equal-weight symbol budget.
- `csm_cap20`: native CSM trades with ex-post 20% top-symbol cap audit wrapper.

## Honest limits

- No blind hyperparameter search was run.
- Regime slices are trade-entry filters on realized narrowed-universe books, not separate regime-only signal engines.
