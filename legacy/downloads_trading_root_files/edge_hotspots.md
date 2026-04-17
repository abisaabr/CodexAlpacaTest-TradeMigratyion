# Edge Hotspots

These hotspots come from the standardized 5-year daily user-subset ledger unless noted otherwise. They show where the realized edge concentrated, not where it is automatically trustworthy.

## Daily-tournament hotspots

- `breakout_consolidation_rep_user_subset_5y` on `NVDA`: expectancy `$419.15`, payoff `10.73`, win rate `80.00%`, trades `10`, stability `0.75`.
- `cross_sectional_momentum_rep_user_subset_5y` on `NVDA`: expectancy `$169.81`, payoff `1.88`, win rate `67.06%`, trades `586`, stability `0.80`.
- `volatility_contraction_breakout_rep_user_subset_5y` on `NVDA`: expectancy `$163.78`, payoff `2.40`, win rate `66.67%`, trades `36`, stability `1.00`.
- `relative_strength_vs_benchmark_rep_user_subset_5y` on `NVDA`: expectancy `$159.95`, payoff `1.81`, win rate `65.92%`, trades `625`, stability `0.67`.
- `dse_exact_user_subset_5y` on `NVDA`: expectancy `$105.12`, payoff `3.16`, win rate `68.42%`, trades `19`, stability `0.83`.
- `relative_strength_vs_benchmark_rep_user_subset_5y` on `NFLX`: expectancy `$96.21`, payoff `1.39`, win rate `66.67%`, trades `483`, stability `0.80`.
- `dse_exact_user_subset_5y` on `META`: expectancy `$73.40`, payoff `3.05`, win rate `60.71%`, trades `28`, stability `0.75`.
- `pullback_in_trend_rep_user_subset_5y` on `NVDA`: expectancy `$95.46`, payoff `1.32`, win rate `63.16%`, trades `437`, stability `0.67`.
- `ma_regime_continuation_rep_user_subset_5y` on `NFLX`: expectancy `$129.96`, payoff `1.53`, win rate `68.18%`, trades `22`, stability `0.80`.
- `cross_sectional_momentum_rep_user_subset_5y` on `NFLX`: expectancy `$76.51`, payoff `1.24`, win rate `64.69%`, trades `439`, stability `0.80`.
- `relative_strength_vs_benchmark_rep_user_subset_5y` on `META`: expectancy `$76.90`, payoff `1.25`, win rate `67.67%`, trades `464`, stability `0.75`.
- `ma_regime_continuation_rep_user_subset_5y` on `META`: expectancy `$80.00`, payoff `1.49`, win rate `68.75%`, trades `32`, stability `1.00`.

## Intraday pair-system hotspots

- `qqq_led_tqqq_sqqq_pair_opening_range_intraday_system` adverse baseline: the strongest hour bucket was `10:00`, while `11:00` was the clearest drag. Positive PnL was still split across both `TQQQ` and `SQQQ`, but the pair remained concentrated enough to fail the stricter top-day kill-switch threshold.
- The pair-system adverse baseline kept test win rate near 59.32% and positive expectancy under conservative slippage, but concentration and slippage realism still block promotion.