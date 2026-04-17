UNDERLYING TOURNAMENT LEADERBOARD
Date: 2026-04-04
Window: 2021-03-24 04:00:00+00:00 to 2026-03-24 04:00:00+00:00

Covered symbols: SPY, QQQ, IWM, NVDA, META, AAPL, AMZN, NFLX, TSLA
Coverage gap: GOOG missing from local daily feature set; local repo carries GOOGL instead.

1. relative_strength_vs_benchmark_rep_user_subset_5y
- Family: Momentum / Relative-Strength Family
- Final equity: 246108.30
- Total return pct: 884.43
- CAGR: 0.5822
- Profit factor: 2.3090
- Sharpe: 1.3521
- Max drawdown pct: 46.37
- Win rate: 0.6440
- Scope: experimental_user_subset
- Params: {"excess_return_threshold": 0.05, "holding_bars": 20, "lookback_window": 60, "profit_target_pct": 0.0, "use_profit_target": false}

2. cross_sectional_momentum_rep_user_subset_5y
- Family: Momentum / Relative-Strength Family
- Final equity: 228570.54
- Total return pct: 814.28
- CAGR: 0.5589
- Profit factor: 2.4855
- Sharpe: 1.3448
- Max drawdown pct: 43.76
- Win rate: 0.6486
- Scope: experimental_user_subset
- Params: {"holding_bars": 20, "lookback_window": 60, "profit_target_pct": 0.0, "rank_cutoff": 0.2, "use_profit_target": false}

3. pullback_in_trend_rep_user_subset_5y
- Family: Pullback in Trend Family
- Final equity: 121238.03
- Total return pct: 385.00
- CAGR: 0.3727
- Profit factor: 1.5653
- Sharpe: 0.7995
- Max drawdown pct: 74.55
- Win rate: 0.6030
- Scope: experimental_user_subset
- Params: {"holding_bars": 20, "profit_target_pct": 0.0, "pullback_drawdown_pct": 0.05, "pullback_window": 20, "use_profit_target": false}

4. rsi_pullback_rep_user_subset_5y
- Family: RSI Pullback / Z-Score Pullback / Gap Reversion Family
- Final equity: 45501.16
- Total return pct: 82.02
- CAGR: 0.1277
- Profit factor: 1.4204
- Sharpe: 0.7657
- Max drawdown pct: 21.90
- Win rate: 0.5489
- Scope: experimental_user_subset
- Params: {"holding_bars": 5, "profit_target_pct": 0.0, "rsi_entry": 30, "rsi_window": 5, "use_profit_target": false}

5. volatility_contraction_breakout_rep_user_subset_5y
- Family: Breakout / Trend-Continuation Family
- Final equity: 39426.35
- Total return pct: 57.71
- CAGR: 0.0957
- Profit factor: 1.8654
- Sharpe: 0.7625
- Max drawdown pct: 20.27
- Win rate: 0.6275
- Scope: experimental_user_subset
- Params: {"breakout_window": 55, "holding_bars": 20, "profit_target_pct": 0.0, "use_profit_target": false, "vol_ratio_max": 0.85}

6. breakout_consolidation_rep_user_subset_5y
- Family: Breakout / Trend-Continuation Family
- Final equity: 37130.13
- Total return pct: 48.52
- CAGR: 0.0826
- Profit factor: 1.6318
- Sharpe: 0.7480
- Max drawdown pct: 19.13
- Win rate: 0.6344
- Scope: experimental_user_subset
- Params: {"breakout_window": 20, "consolidation_range_pct": 0.05, "consolidation_window": 5, "holding_bars": 20, "profit_target_pct": 0.0, "use_profit_target": false}

7. zscore_pullback_rep_user_subset_5y
- Family: RSI Pullback / Z-Score Pullback / Gap Reversion Family
- Final equity: 36030.08
- Total return pct: 44.13
- CAGR: 0.0761
- Profit factor: 1.4077
- Sharpe: 0.6792
- Max drawdown pct: 14.62
- Win rate: 0.5525
- Scope: experimental_user_subset
- Params: {"holding_bars": 5, "profit_target_pct": 0.0, "use_profit_target": false, "zscore_entry": 1.5, "zscore_window": 10}

8. ma_regime_continuation_rep_user_subset_5y
- Family: Breakout / Trend-Continuation Family
- Final equity: 35320.21
- Total return pct: 41.28
- CAGR: 0.0718
- Profit factor: 1.6911
- Sharpe: 0.7811
- Max drawdown pct: 12.39
- Win rate: 0.5894
- Scope: experimental_user_subset
- Params: {"continuation_ma": 20, "holding_bars": 20, "profit_target_pct": 0.0, "use_profit_target": false}

9. dse_exact_user_subset_5y
- Family: Down Streak Exhaustion
- Final equity: 31116.04
- Total return pct: 24.46
- CAGR: 0.0449
- Profit factor: 1.8125
- Sharpe: 0.8090
- Max drawdown pct: 5.93
- Win rate: 0.5022
- Scope: experimental_user_subset
- Params: {"holding_bars": 5, "profit_target_pct": 0.0, "rsi_cap": 30, "streak_length": 4, "use_profit_target": false}

10. gap_reversion_rep_user_subset_5y
- Family: RSI Pullback / Z-Score Pullback / Gap Reversion Family
- Final equity: 28827.73
- Total return pct: 15.31
- CAGR: 0.0290
- Profit factor: 1.5006
- Sharpe: 0.5575
- Max drawdown pct: 7.06
- Win rate: 0.5319
- Scope: experimental_user_subset
- Params: {"gap_down_pct": 0.02, "holding_bars": 5, "profit_target_pct": 0.0, "use_profit_target": false}
