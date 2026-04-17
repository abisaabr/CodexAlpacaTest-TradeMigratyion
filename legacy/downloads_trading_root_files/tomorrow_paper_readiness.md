# Tomorrow Paper Readiness

1. Which exact strategies should run tomorrow on Alpaca paper during RTH?
   `qqq_led_tqqq_sqqq_pair_opening_range_intraday_system` only.
2. Which exact strategies should NOT run tomorrow?
   `down_streak_exhaustion`, `relative_strength_vs_benchmark::rs_top3_native`, and `cross_sectional_momentum::csm_native` should not run as active paper strategies on Monday 2026-04-06.
3. Which should remain research-only?
   `relative_strength_vs_benchmark::rs_top3_native` and `cross_sectional_momentum::csm_native`.
4. Which should remain benchmark/control only?
   `down_streak_exhaustion`.
5. What is the honest reason for each inclusion or exclusion?
   `qqq_led_tqqq_sqqq_pair_opening_range_intraday_system`: included because it is still the only approved operational candidate and it was the only recent-window strategy with positive PnL.
   `down_streak_exhaustion`: excluded from tomorrow trading because the recent window was negative; keep it as the daily control because it remains cleaner than RS/CSM in the broader trust stack.
   `relative_strength_vs_benchmark::rs_top3_native`: excluded because the recent window was negative, sparse, and inconsistent with paper-readiness.
   `cross_sectional_momentum::csm_native`: excluded because the recent window was negative, very sparse, and weaker than RS on the current hierarchy.
