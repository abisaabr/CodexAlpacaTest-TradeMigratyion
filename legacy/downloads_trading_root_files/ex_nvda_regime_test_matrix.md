# Ex-NVDA Regime Test Matrix

## Slice definitions

- `native_baseline`: full canonical/native realized book on the 9-symbol user subset.
- `ex_nvda_full`: same realized book with NVDA trades removed ex post.
- `rising_market`: trades entered on SPY-tagged rising-market days.
- `rising_market_ex_nvda`: rising-market trades with NVDA removed ex post.
- `calmer`: trades entered on SPY-tagged calmer / low-vol days.
- `calmer_ex_nvda`: calmer / low-vol trades with NVDA removed ex post.
- `strong_momentum_participation`: trades entered on rising-market days whose cross-sectional participation score is in the top quartile of rising-market days.
- `strong_momentum_participation_ex_nvda`: the same strong-participation days with NVDA removed ex post.
- `megacap_ex_nvda`: realized trades restricted to native subset mega-cap tech ex-NVDA symbols: `AAPL, AMZN, META, NFLX, TSLA`.
- `megacap_ex_nvda_supportive`: native mega-cap ex-NVDA trades restricted to rising-market entry days.
- `etf_only`: realized trades restricted to SPY / QQQ / IWM.

## Honest limits

- The matrix does not create a new ex-NVDA RS or CSM signal engine. It falsifies the canonical branch by stripping NVDA out of the realized native book inside the same regimes that previously carried the upside.
- `GOOGL` is available locally but excluded from these canonical slices because the prior RS/CSM methodology used the fixed 9-symbol subset without it.
