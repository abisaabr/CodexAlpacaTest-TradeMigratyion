# Ex-NVDA Regime Test Input Digest

## Exact files

- `C:\Users\rabisaab\Downloads\master_strategy_memo.txt`: opened successfully
- `C:\Users\rabisaab\Downloads\tournament_master_report.md`: opened successfully
- `C:\Users\rabisaab\Downloads\monday_paper_plan.md`: opened successfully
- `C:\Users\rabisaab\Downloads\rs_canonical_branch_decision.md`: opened successfully
- `C:\Users\rabisaab\Downloads\rs_branch_paper_watch_decision.md`: opened successfully
- `C:\Users\rabisaab\Downloads\rs_final_head_to_head_report.md`: opened successfully
- `C:\Users\rabisaab\Downloads\best_day_autopsy_report.md`: opened successfully
- `C:\Users\rabisaab\Downloads\non_extreme_day_edge_report.md`: opened successfully
- `C:\Users\rabisaab\Downloads\rs_vs_csm_day_profile_report.md`: opened successfully
- `C:\Users\rabisaab\Downloads\canonical_edge_hypothesis.md`: opened successfully
- `C:\Users\rabisaab\Downloads\next_micro_experiments.md`: opened successfully
- `C:\Users\rabisaab\Downloads\day_type_symbol_regime_map.csv`: opened successfully
- `C:\Users\rabisaab\Downloads\day_level_pnl_decomposition.csv`: opened successfully
- `C:\Users\rabisaab\Downloads\underlying_trade_ledger.csv`: opened successfully
- `C:\Users\rabisaab\Downloads\underlying_tournament_metrics.csv`: opened successfully
- `C:\Users\rabisaab\Downloads\trade_cluster_edge_map.csv`: opened successfully

## Exact implementations used

- `relative_strength_vs_benchmark::reduced_selection_top3`: local `relative_strength_vs_benchmark` with the canonical `reduced_selection_top3` wrapper from the RS hardening pass.
- `cross_sectional_momentum`: local native `cross_sectional_momentum` on the same daily 9-symbol user subset.
- `down_streak_exhaustion`: local native `down_streak_exhaustion` daily control on the same user subset.

## Regime tags available locally

- `rising_market`, `falling_or_volatile`, and `calmer` come from the SPY-tagged regime map already used in prior truth tests.
- `strong_momentum_participation` is approximated honestly from local fields only: `rising_market` days whose cross-sectional participation score (average of uptrend breadth and trend-stack breadth across the 9-symbol user subset) lands in the top quartile of rising-market days.
- Strong participation threshold on this 5-year window: `0.8889` with `198` qualifying days out of `695` rising-market days.

## Symbol coverage

- Native falsification run uses the same 9-symbol daily subset as the prior tournament: `SPY, QQQ, IWM, NVDA, META, AAPL, AMZN, NFLX, TSLA`.
- Mega-cap tech ex-NVDA symbols actually available inside that native subset: `AAPL, AMZN, META, NFLX, TSLA`.
- `GOOG/GOOGL` still affects interpretation only as a coverage note. Local features have `GOOGL`, but the canonical RS/CSM user-subset methodology does not include it, so the ex-NVDA mega-cap slice stays inside the native subset rather than silently broadening the universe.

## Slice mechanics

- This falsification preserves native signal generation and holding periods first, then retains only the realized trades whose entry dates and symbols belong to each slice.
- That choice is deliberate: deleting whole calendar rows or silently reranking without NVDA would change the strategy mechanics instead of falsifying the realized branch.
