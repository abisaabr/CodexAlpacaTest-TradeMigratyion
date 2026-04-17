# Best-Day Autopsy Input Digest

## Exact files

- `C:\Users\rabisaab\Downloads\master_strategy_memo.txt`: opened successfully
- `C:\Users\rabisaab\Downloads\tournament_master_report.md`: opened successfully
- `C:\Users\rabisaab\Downloads\monday_paper_plan.md`: opened successfully
- `C:\Users\rabisaab\Downloads\rs_canonical_branch_decision.md`: opened successfully
- `C:\Users\rabisaab\Downloads\rs_branch_paper_watch_decision.md`: opened successfully
- `C:\Users\rabisaab\Downloads\rs_final_head_to_head_report.md`: opened successfully
- `C:\Users\rabisaab\Downloads\rs_hardening_forensics_report.md`: opened successfully
- `C:\Users\rabisaab\Downloads\rs_hardening_metrics.csv`: opened successfully
- `C:\Users\rabisaab\Downloads\rs_hardening_forensics.csv`: opened successfully
- `C:\Users\rabisaab\Downloads\rs_final_head_to_head.csv`: opened successfully
- `C:\Users\rabisaab\Downloads\best_day_dependence_report.md`: opened successfully
- `C:\Users\rabisaab\Downloads\best_day_dependence_metrics.csv`: opened successfully
- `C:\Users\rabisaab\Downloads\rs_edge_quality_scorecard.csv`: opened successfully
- `C:\Users\rabisaab\Downloads\underlying_trade_ledger.csv`: opened successfully
- `C:\Users\rabisaab\Downloads\underlying_tournament_metrics.csv`: opened successfully
- `C:\Users\rabisaab\Downloads\trade_cluster_edge_map.csv`: opened successfully

## Exact implementations under audit

- `relative_strength_vs_benchmark::reduced_selection_top3`: `relative_strength_vs_benchmark` on the prior 9-symbol daily subset with the `reduced_selection_top3` wrapper from the hardening pass.
- `cross_sectional_momentum`: native `cross_sectional_momentum` on the same daily subset.
- `down_streak_exhaustion`: native confirmed `down_streak_exhaustion` daily control.

## Day-level PnL availability

- Native strategy ledgers exist for RS, CSM, and DSE, but the canonical RS top-3 sleeve requires direct reconstruction.
- This autopsy reconstructs day-level trade contributions from the exact local daily engine so the day-removal logic matches the prior best-day dependence tests.

## Remaining local limits

- Day-type labels are derived from the local daily feature set only: gap size, SPY regime tags, rolling volatility bucket, symbol family, breadth proxy, and participation concentration.
- No earnings calendar or news feed is joined, so `earnings-like` means large-gap single-name reaction rather than a verified earnings event.
- `GOOG` is still absent from the native subset; local `GOOGL` only affects interpretation outside the prior 9-symbol slice.
