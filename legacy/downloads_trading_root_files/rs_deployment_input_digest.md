# Relative-Strength Deployment Input Digest

## Exact files

- `C:\Users\rabisaab\Downloads\master_strategy_memo.txt`: opened successfully
- `C:\Users\rabisaab\Downloads\top10_authoritative_inventory.txt`: opened successfully
- `C:\Users\rabisaab\Downloads\strategy_chat_seed.txt`: opened successfully
- `C:\Users\rabisaab\Downloads\tournament_master_report.md`: opened successfully
- `C:\Users\rabisaab\Downloads\monday_paper_plan.md`: opened successfully
- `C:\Users\rabisaab\Downloads\next_edge_research_ranking.md`: opened successfully
- `C:\Users\rabisaab\Downloads\next_edge_action_plan.md`: opened successfully
- `C:\Users\rabisaab\Downloads\truth_test_elimination_report.md`: opened successfully
- `C:\Users\rabisaab\Downloads\concentration_portability_metrics.csv`: opened successfully
- `C:\Users\rabisaab\Downloads\edge_survival_scorecard.csv`: opened successfully
- `C:\Users\rabisaab\Downloads\nvda_edge_hotspots.md`: opened successfully

## Exact implementations under test

- `relative_strength_vs_benchmark`: local `alpaca_stock_research` daily template using the prior tournament params row.
- `cross_sectional_momentum`: local `alpaca_stock_research` daily template using the prior tournament params row.
- `down_streak_exhaustion`: local confirmed finalist params used as the daily control.

## Baseline references

- `relative_strength_vs_benchmark` baseline: strategy_id `relative_strength_vs_benchmark_rep_user_subset_5y`, final_equity `246108.30`, return `884.43%`, drawdown `46.37%`, win_rate `0.64%`.
- `cross_sectional_momentum` baseline: strategy_id `cross_sectional_momentum_rep_user_subset_5y`, final_equity `228570.54`, return `814.28%`, drawdown `43.76%`, win_rate `0.65%`.
- `down_streak_exhaustion` baseline: strategy_id `dse_exact_user_subset_5y`, final_equity `31116.04`, return `24.46%`, drawdown `5.93%`, win_rate `0.50%`.

## Data limitations

- Native slice preserves the same prior 9-symbol user subset: SPY, QQQ, IWM, NVDA, META, AAPL, AMZN, NFLX, TSLA.
- `GOOG` is still absent from the native prior run; local features carry `GOOGL`, which remains documented but is not inserted into the apples-to-apples native head-to-head.
- Daily fills, slippage, and risk controls reuse the same local engine assumptions as the prior tournament: 10% target position fraction, 0 fee per trade, 5 max positions, 50% max portfolio heat, and 3% max daily loss.
- Options are still blocked and intentionally out of scope.
