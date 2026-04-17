# Baseline Reproduction Report

## Completed exact reproductions
- `down_streak_exhaustion`: exact native test-split rerun completed. Ending equity, CAGR, win rate, expectancy, profit factor, Sharpe, Sortino, drawdown, and trade count all matched the saved phase-5 row with zero drift.
- `qqq_led_tqqq_sqqq_pair_opening_range_intraday_system`: exact adverse baseline row reproduced. The preserved baseline spec with 10-minute opening window, 15 bps threshold, 15-minute decisions, 25-minute start delay, 40-minute flat-before-close, and 50% notional matched the earlier paper-promotion leaderboard exactly.

## Partial or pending baselines
- `durable_crsi_family`: Runnable local family exists, but only the standardized 5-year user-subset tournament was executed; the native baseline rerun remains pending.
- `momentum_relative_strength_family`: Runnable local family exists, but only the standardized 5-year user-subset tournament was executed; the native baseline rerun remains pending.
- `rsi_pullback_z_score_pullback_gap_reversion_family`: Runnable local family exists, but only the standardized 5-year user-subset tournament was executed; the native baseline rerun remains pending.
- `breakout_trend_continuation_family`: Runnable local family exists, but only the standardized 5-year user-subset tournament was executed; the native baseline rerun remains pending.
- `pullback_in_trend_family`: Runnable local family exists, but only the standardized 5-year user-subset tournament was executed; the native baseline rerun remains pending.
- `turn_of_month_trend_family`: Runnable local family exists, but only the standardized 5-year user-subset tournament was executed; the native baseline rerun remains pending.
- `stacked_ensemble_family`: Runnable local family exists, but only the standardized 5-year user-subset tournament was executed; the native baseline rerun remains pending.
- `older_corrected_mean_reversion_baseline`: Runnable local family exists, but only the standardized 5-year user-subset tournament was executed; the native baseline rerun remains pending.
- `older_corrected_day_of_week_vol_regime_breakout_baseline_cluster`: Runnable local family exists, but only the standardized 5-year user-subset tournament was executed; the native baseline rerun remains pending.
- `options_vertical_spread_wrappers`: Local artifacts exist, but this turn did not have enough exact code/config coverage to claim a true baseline rerun.
- `tradingview_reference_ideation_scripts_cluster`: Local artifacts exist, but this turn did not have enough exact code/config coverage to claim a true baseline rerun.
- `tv_pvt_top5_finalists_tsla_30m`: Exact local source code, config, or lineage is missing, so a 1:1 rerun is not currently possible.
- `index_opening_drive_lab_fb_or15_w09351000_dlong_only_ema0_vwap0_voloff_xtime_stop_1030`: Exact local source code, config, or lineage is missing, so a 1:1 rerun is not currently possible.
- `tv_pvt_top5_finalists_nvda_30m`: Exact local source code, config, or lineage is missing, so a 1:1 rerun is not currently possible.
- `tv_pvt_top5_finalists_vix_vxx_30m`: Exact local source code, config, or lineage is missing, so a 1:1 rerun is not currently possible.
- `index_opening_drive_lab_fb_or5_w09351000_dlong_only_ema0_vwap0_voloff_xtime_stop_1030`: Exact local source code, config, or lineage is missing, so a 1:1 rerun is not currently possible.
- `tv_pvt_top5_finalists_vix_vxx_60m`: Exact local source code, config, or lineage is missing, so a 1:1 rerun is not currently possible.
- `tv_pvt_top5_finalists_iwm_15m`: Exact local source code, config, or lineage is missing, so a 1:1 rerun is not currently possible.
- `codex_leveraged_pipeline_out_base_20260103_122420`: Exact local source code, config, or lineage is missing, so a 1:1 rerun is not currently possible.
- `tv_squeeze_top5_finalists_tsla_30m`: Local artifacts exist, but this turn did not have enough exact code/config coverage to claim a true baseline rerun.
- `flux_signal_engine_top20_2025_msft_residual_survivor`: Exact local source code, config, or lineage is missing, so a 1:1 rerun is not currently possible.
- `project_smart_money_concepts_family`: Runnable local family exists, but only the standardized 5-year user-subset tournament was executed; the native baseline rerun remains pending.
- `project_sqzmom_lb_family`: Runnable local family exists, but only the standardized 5-year user-subset tournament was executed; the native baseline rerun remains pending.
- `project_supertrend_family`: Runnable local family exists, but only the standardized 5-year user-subset tournament was executed; the native baseline rerun remains pending.
- `project_rsi_cyclic_smoothed_family`: Runnable local family exists, but only the standardized 5-year user-subset tournament was executed; the native baseline rerun remains pending.
- `project_combo_consensus_family`: Runnable local family exists, but only the standardized 5-year user-subset tournament was executed; the native baseline rerun remains pending.
- `luxalgo_fvg_backtest_family`: Local artifacts exist, but this turn did not have enough exact code/config coverage to claim a true baseline rerun.
- `qqq_gap_prob_tool_signal_layer`: Runnable local family exists, but only the standardized 5-year user-subset tournament was executed; the native baseline rerun remains pending.
- `qqq_range_engine_signal_layer`: Runnable local family exists, but only the standardized 5-year user-subset tournament was executed; the native baseline rerun remains pending.
- `qqq_same_day_scan_signal_layer`: Runnable local family exists, but only the standardized 5-year user-subset tournament was executed; the native baseline rerun remains pending.
- `qqq_today_nowcast_signal_layer`: Runnable local family exists, but only the standardized 5-year user-subset tournament was executed; the native baseline rerun remains pending.

## Drift verdict
- Completed baseline reproductions with decision-grade confidence: `2`.
- Material unexplained drift cases: `0`.
- Full native reruns remain blocked or pending for the other families because exact local configs, exact lineage, or native exported ledgers are still incomplete.