# Broad-Participation Input Digest

## Exact files

- `C:\Users\rabisaab\Downloads\master_strategy_memo.txt`: opened successfully
- `C:\Users\rabisaab\Downloads\tournament_master_report.md`: opened successfully
- `C:\Users\rabisaab\Downloads\monday_paper_plan.md`: opened successfully
- `C:\Users\rabisaab\Downloads\megacap_ex_nvda_branch_decision.md`: opened successfully
- `C:\Users\rabisaab\Downloads\leader_vs_breadth_report.md`: opened successfully
- `C:\Users\rabisaab\Downloads\megacap_ex_nvda_forensics_report.md`: opened successfully
- `C:\Users\rabisaab\Downloads\megacap_ex_nvda_paper_watch_recheck.md`: opened successfully
- `C:\Users\rabisaab\Downloads\ex_tsla_branch_redecision.md`: opened successfully
- `C:\Users\rabisaab\Downloads\ex_tsla_leader_report.md`: opened successfully
- `C:\Users\rabisaab\Downloads\ex_tsla_forensics_report.md`: opened successfully
- `C:\Users\rabisaab\Downloads\ex_tsla_paper_watch_recheck.md`: opened successfully
- `C:\Users\rabisaab\Downloads\next_post_ex_tsla_experiments.md`: opened successfully
- `C:\Users\rabisaab\Downloads\best_day_autopsy_report.md`: opened successfully
- `C:\Users\rabisaab\Downloads\non_extreme_day_edge_report.md`: opened successfully
- `C:\Users\rabisaab\Downloads\canonical_edge_hypothesis.md`: opened successfully
- `C:\Users\rabisaab\Downloads\ex_tsla_metrics.csv`: opened successfully
- `C:\Users\rabisaab\Downloads\ex_tsla_leader_diagnostic.csv`: opened successfully
- `C:\Users\rabisaab\Downloads\day_type_symbol_regime_map.csv`: opened successfully
- `C:\Users\rabisaab\Downloads\day_level_pnl_decomposition.csv`: opened successfully
- `C:\Users\rabisaab\Downloads\underlying_trade_ledger.csv`: opened successfully
- `C:\Users\rabisaab\Downloads\underlying_tournament_metrics.csv`: opened successfully
- `C:\Users\rabisaab\Downloads\trade_cluster_edge_map.csv`: opened successfully

## Exact implementations tested

- Canonical branch: `cross_sectional_momentum::csm_native` via `csm_native`.
- Immediate challenger: `relative_strength_vs_benchmark::rs_top3_native` via `rs_top3_native`.
- Control: `down_streak_exhaustion` via `dse_control_native`.

## Exact universe used

- Narrowed mega-cap ex-NVDA ex-TSLA universe used in this test: `AAPL, AMZN, GOOGL, META, NFLX`.
- `GOOG` vs `GOOGL` affects the run: local data uses `GOOGL`.

## Breadth fields available

- `top_symbol_pct_of_day_pnl`, `number_of_symbols_traded`, `positive_symbols_count`, `participation_type`, `primary_day_class`, and `gap_continuation_label` come from the existing day-level reconstruction.
- `rising_market`, `falling_or_volatile`, and `calm_low_vol` (`calmer`) come from the same SPY-tagged regime logic used in the prior falsification passes.
- `strong_momentum_participation` is derived honestly from the ex-TSLA universe itself: rising-market days whose participation score is in the top quartile of rising-market days.
- Ex-TSLA strong participation threshold: `0.9000` with `269` qualifying days.

## Remaining data limits

- This remains a daily underlying backtest with modeled slippage and no live validation packet.
- The non-extreme-day slice is an equity-path audit, not a separate signal-generation rerun.
- The single-leader and broad-participation slices are derived from reconstructed day-level PnL decomposition, which is honest but still post-trade forensic filtering.
