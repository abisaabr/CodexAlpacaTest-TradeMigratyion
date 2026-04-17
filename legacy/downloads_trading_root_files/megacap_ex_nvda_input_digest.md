# Mega-Cap Ex-NVDA Input Digest

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
- `C:\Users\rabisaab\Downloads\ex_nvda_core_edge_report.md`: opened successfully
- `C:\Users\rabisaab\Downloads\supportive_regime_day_profile_report.md`: opened successfully
- `C:\Users\rabisaab\Downloads\rs_branch_recheck_after_ex_nvda.md`: opened successfully
- `C:\Users\rabisaab\Downloads\rs_vs_csm_recheck.md`: opened successfully
- `C:\Users\rabisaab\Downloads\next_falsification_steps.md`: opened successfully
- `C:\Users\rabisaab\Downloads\ex_nvda_regime_metrics.csv`: opened successfully
- `C:\Users\rabisaab\Downloads\day_type_symbol_regime_map.csv`: opened successfully
- `C:\Users\rabisaab\Downloads\day_level_pnl_decomposition.csv`: opened successfully
- `C:\Users\rabisaab\Downloads\underlying_trade_ledger.csv`: opened successfully
- `C:\Users\rabisaab\Downloads\underlying_tournament_metrics.csv`: opened successfully
- `C:\Users\rabisaab\Downloads\trade_cluster_edge_map.csv`: opened successfully

## Exact implementations tested

- `relative_strength_vs_benchmark::reduced_selection_top3` via `rs_top3_native`, with audit wrappers `rs_top2_native`, `rs_top3_equal_weight`, `rs_top3_cap20`, and `rs_top2_equal_weight`.
- `cross_sectional_momentum` via `csm_native`, with audit wrappers `csm_equal_weight` and `csm_cap20`.
- `down_streak_exhaustion` via `dse_control_native` as control only.

## Canonical comparison universe

- Mega-cap ex-NVDA symbols used in this rerun: `AAPL, AMZN, GOOGL, META, NFLX, TSLA`.
- `GOOG` vs `GOOGL` does affect the run: local data provides `GOOGL` and this rerun uses that symbol in the canonical comparison universe.

## Regime tags available

- `rising_market`, `falling_or_volatile`, and `calm_low_vol` (`calmer`) come from the same SPY-tagged regime logic used in prior falsification passes.
- `strong_momentum_participation` is derived honestly from the mega-cap ex-NVDA universe itself: rising-market days whose mega-cap participation score is in the top quartile of rising-market days.
- Strong participation threshold on this narrowed universe: `0.8333` with `230` qualifying days.

## Remaining limits

- This is still a research-only daily backtest with modeled slippage and no live validation packet.
- The cap20 wrapper is an ex-post audit wrapper, not a live-executable rule set.
- The non-extreme-day slice is an equity-path audit rather than a separate trade-generation rerun.
