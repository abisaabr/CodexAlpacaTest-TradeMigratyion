# Ex-AAPL / Ex-META Input Digest

## Exact files

- `C:\Users\rabisaab\Downloads\master_strategy_memo.txt`: opened successfully
- `C:\Users\rabisaab\Downloads\tournament_master_report.md`: opened successfully
- `C:\Users\rabisaab\Downloads\monday_paper_plan.md`: opened successfully
- `C:\Users\rabisaab\Downloads\broad_participation_branch_decision.md`: opened successfully
- `C:\Users\rabisaab\Downloads\leader_vs_broad_participation_report.md`: opened successfully
- `C:\Users\rabisaab\Downloads\broad_participation_forensics_report.md`: opened successfully
- `C:\Users\rabisaab\Downloads\broad_participation_paper_watch_recheck.md`: opened successfully
- `C:\Users\rabisaab\Downloads\next_after_broad_participation.md`: opened successfully
- `C:\Users\rabisaab\Downloads\megacap_ex_nvda_branch_decision.md`: opened successfully
- `C:\Users\rabisaab\Downloads\ex_tsla_branch_redecision.md`: opened successfully
- `C:\Users\rabisaab\Downloads\best_day_autopsy_report.md`: opened successfully
- `C:\Users\rabisaab\Downloads\non_extreme_day_edge_report.md`: opened successfully
- `C:\Users\rabisaab\Downloads\canonical_edge_hypothesis.md`: opened successfully
- `C:\Users\rabisaab\Downloads\broad_participation_metrics.csv`: opened successfully
- `C:\Users\rabisaab\Downloads\leader_vs_broad_participation_contrast.csv`: opened successfully
- `C:\Users\rabisaab\Downloads\broad_participation_forensics.csv`: opened successfully
- `C:\Users\rabisaab\Downloads\day_type_symbol_regime_map.csv`: opened successfully
- `C:\Users\rabisaab\Downloads\day_level_pnl_decomposition.csv`: opened successfully
- `C:\Users\rabisaab\Downloads\underlying_trade_ledger.csv`: opened successfully
- `C:\Users\rabisaab\Downloads\underlying_tournament_metrics.csv`: opened successfully
- `C:\Users\rabisaab\Downloads\trade_cluster_edge_map.csv`: opened successfully

## Exact implementations tested

- Canonical branch: `relative_strength_vs_benchmark::rs_top3_native` via `rs_top3_native`.
- Main challenger: `cross_sectional_momentum::csm_native` via `csm_native`.
- Control: `down_streak_exhaustion` via `dse_control_native`.

## Exact symbol universe used

- Ex-TSLA baseline universe: `AAPL, AMZN, GOOGL, META, NFLX`.
- Ex-AAPL universe: `AMZN, GOOGL, META, NFLX`.
- Ex-META universe: `AAPL, AMZN, GOOGL, NFLX`.
- `GOOG` vs `GOOGL` affects the run: local data uses `GOOGL`.

## Honest broad-participation fields

- Broad-participation filtering uses only local day-level reconstruction: `participation_type`, `top_symbol_pct_of_day_pnl`, `positive_symbols_count`, and `number_of_symbols_traded`.
- `rising_market` comes from the same SPY-tagged regime logic used in the prior falsification passes.

## Remaining data limits

- These are daily underlying reruns only, with modeled slippage and no live validation packet.
- Non-extreme-day slices are equity-path audits after the reruns, not new signal-generation variants.
- Cross-sectional families are rerun on the reduced universes rather than post-hoc trade deletion so the dependency test stays honest.
