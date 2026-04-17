# NVDA Truth-Test Matrix

## Tested daily families

- `relative_strength_vs_benchmark` -> `Momentum / Relative-Strength Family`
- `cross_sectional_momentum` -> `Momentum / Relative-Strength Family`
- `breakout_consolidation` -> `Breakout / Trend-Continuation Family`
- `volatility_contraction_breakout` -> `Breakout / Trend-Continuation Family`
- `pullback_in_trend` -> `Pullback in Trend Family`
- `down_streak_exhaustion` -> `Down Streak Exhaustion`

## Reference-only operational control

- `qqq_led_tqqq_sqqq_pair_opening_range_intraday_system` is kept for role comparison only; no new daily rerun is forced onto it.

## Slice definitions

- `native_prior_tournament_slice`: same 9-symbol user subset as the prior tournament.
- `nvda_only`: NVDA retained alone.
- `megacap_tech_ex_nvda`: AAPL, AMZN, GOOGL, META, NFLX, TSLA.
- `broad_basket_ex_nvda`: prior user subset excluding NVDA.
- `etf_only`: SPY, QQQ, IWM.
- `top_3_symbol_concentration_capped`: native trades scaled so no symbol keeps more than 25% of positive PnL.
- `equal_risk_symbol_capped`: native trades scaled so high-turnover symbols do not dominate cumulative entry notional.
- `first_half` and `second_half`: split the same 5-year window in half.
- `annual_window_n`: sequential 1-year windows across the same 5-year span.
- `rising_market`, `falling_or_volatile`, `calmer`: SPY-tagged diagnostic regime slices from the local confirmation logic.
