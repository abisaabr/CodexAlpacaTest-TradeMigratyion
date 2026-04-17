# NVDA Truth-Test Input Digest

## Exact files

- `C:\Users\rabisaab\Downloads\master_strategy_memo.txt`: opened successfully
- `C:\Users\rabisaab\Downloads\top10_authoritative_inventory.txt`: opened successfully
- `C:\Users\rabisaab\Downloads\strategy_chat_seed.txt`: opened successfully
- `C:\Users\rabisaab\Downloads\tournament_master_report.md`: opened successfully
- `C:\Users\rabisaab\Downloads\monday_paper_plan.md`: opened successfully

## Family implementations used

- Daily reruns use the local `alpaca_stock_research` engine and `build_signals` templates that reproduced the prior tournament rows exactly.
- `qqq_led_tqqq_sqqq_pair_opening_range_intraday_system` stays a control/reference from the prior report and Monday plan rather than a new daily rerun.

## Baseline references

- `relative_strength_vs_benchmark`: strategy_id `relative_strength_vs_benchmark_rep_user_subset_5y`, family `Momentum / Relative-Strength Family`, final_equity `246108.30`, return `884.43%`, max_dd `46.37%`, win_rate `0.64%`.
- `cross_sectional_momentum`: strategy_id `cross_sectional_momentum_rep_user_subset_5y`, family `Momentum / Relative-Strength Family`, final_equity `228570.54`, return `814.28%`, max_dd `43.76%`, win_rate `0.65%`.
- `breakout_consolidation`: strategy_id `breakout_consolidation_rep_user_subset_5y`, family `Breakout / Trend-Continuation Family`, final_equity `37130.13`, return `48.52%`, max_dd `19.13%`, win_rate `0.63%`.
- `volatility_contraction_breakout`: strategy_id `volatility_contraction_breakout_rep_user_subset_5y`, family `Breakout / Trend-Continuation Family`, final_equity `39426.35`, return `57.71%`, max_dd `20.27%`, win_rate `0.63%`.
- `pullback_in_trend`: strategy_id `pullback_in_trend_rep_user_subset_5y`, family `Pullback in Trend Family`, final_equity `121238.03`, return `385.00%`, max_dd `74.55%`, win_rate `0.60%`.
- `down_streak_exhaustion`: strategy_id `dse_exact_user_subset_5y`, family `Down Streak Exhaustion`, final_equity `31116.04`, return `24.46%`, max_dd `5.93%`, win_rate `0.50%`.

## Data coverage limits

- Daily truth test uses the same 5-year window as the prior tournament: 2021-03-24 through 2026-03-24 UTC.
- Local daily feature data extends beyond the user subset, but the native benchmark slice preserves the prior 9-symbol subset.
- `GOOG` is still absent from the prior user-subset run; local features carry `GOOGL`, which is used only where the test matrix explicitly allows `GOOG or GOOGL, whichever exists locally`.
- Historical options replay remains blocked and is intentionally out of scope for this task.

## Conflicts or trust notes

- Memo says Momentum / Relative-Strength and Breakout / Trend-Continuation remain promising but unconfirmed. Top-10 inventory and tournament report preserve upside, but both still carry concentration and trust warnings.
- Memo keeps Down Streak Exhaustion as the best confirmed daily control. Monday plan keeps the QQQ pair as the best current paper candidate.
