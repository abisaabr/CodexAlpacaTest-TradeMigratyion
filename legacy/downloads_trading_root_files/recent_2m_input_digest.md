# Recent 2-Month Input Digest

## Exact files opened

- `C:\Users\rabisaab\Downloads\master_strategy_memo.txt`: opened
- `C:\Users\rabisaab\Downloads\tournament_master_report.md`: opened
- `C:\Users\rabisaab\Downloads\monday_paper_plan.md`: opened
- `C:\Users\rabisaab\Downloads\remaining_carrier_branch_redecision.md`: opened
- `C:\Users\rabisaab\Downloads\remaining_carrier_dependency_report.md`: opened
- `C:\Users\rabisaab\Downloads\remaining_carrier_forensics_report.md`: opened
- `C:\Users\rabisaab\Downloads\remaining_carrier_paper_watch_recheck.md`: opened
- `C:\Users\rabisaab\Downloads\broad_participation_branch_decision.md`: opened
- `C:\Users\rabisaab\Downloads\ex_aapl_meta_branch_redecision.md`: opened
- `C:\Users\rabisaab\Downloads\ex_tsla_branch_redecision.md`: opened
- `C:\Users\rabisaab\Downloads\rs_canonical_branch_decision.md`: opened
- `C:\Users\rabisaab\Downloads\rs_branch_paper_watch_decision.md`: opened
- `C:\Users\rabisaab\Downloads\best_day_autopsy_report.md`: opened
- `C:\Users\rabisaab\Downloads\non_extreme_day_edge_report.md`: opened
- `C:\Users\rabisaab\Downloads\underlying_trade_ledger.csv`: opened
- `C:\Users\rabisaab\Downloads\underlying_tournament_metrics.csv`: opened

## Strategy implementation status

- `qqq_led_tqqq_sqqq_pair_opening_range_intraday_system`: exact runnable via `nasdaq-etf-intraday-alpaca/src/app/paper_promotion.py` and `best_config.yaml`.
- `down_streak_exhaustion`: partial recent-window runnable via `alpaca-stock-strategy-research` exact baseline params; local daily data stops at `2026-03-24`.
- `relative_strength_vs_benchmark::rs_top3_native`: partial recent-window runnable via the daily backtest engine plus the current top-3 wrapper on `AAPL/AMZN/GOOGL/META/NFLX`; local daily data stops at `2026-03-24`.
- `cross_sectional_momentum::csm_native`: partial recent-window runnable via the daily backtest engine on `AAPL/AMZN/GOOGL/META/NFLX`; local daily data stops at `2026-03-24`.

## Exact 2-month window used

- Official recent window target: `2026-02-02` through `2026-03-31`.
- Daily-strategy coverage actually available locally: `2026-02-02` through `2026-03-24`.
- Pair-strategy coverage actually available locally: `2026-02-02` through `2026-03-31`.

## Remaining data limitations

- Daily features do not currently extend through 2026-03-31, so the daily strategies are partial for the final seven calendar days of the target window.
- Options remain out of scope and blocked by prior instructions.
