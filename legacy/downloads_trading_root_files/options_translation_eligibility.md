# Options Translation Eligibility

The table below is semantic eligibility only. Every actual replay remains blocked until there is honest historical quote coverage and full timestamp-aligned chain reconstruction.

- `down_streak_exhaustion`: single-leg `yes`, vertical `yes`, neutral `no`. Directional stock/ETF logic can translate to long options or debit spreads, but neutral structures would be a semantic mismatch.
- `qqq_led_tqqq_sqqq_pair_opening_range_intraday_system`: single-leg `yes`, vertical `yes`, neutral `no`. Directional intraday signal. Long calls/puts and debit spreads fit; neutral structures do not.
- `durable_crsi_family`: single-leg `no`, vertical `no`, neutral `no`. Overnight gap dependence and symbol-specific presets make honest options translation unattractive.
- `momentum_relative_strength_family`: single-leg `yes`, vertical `yes`, neutral `no`. Directional stock/ETF logic can translate to long options or debit spreads, but neutral structures would be a semantic mismatch.
- `rsi_pullback_z_score_pullback_gap_reversion_family`: single-leg `yes`, vertical `yes`, neutral `no`. Directional stock/ETF logic can translate to long options or debit spreads, but neutral structures would be a semantic mismatch.
- `breakout_trend_continuation_family`: single-leg `yes`, vertical `yes`, neutral `no`. Directional stock/ETF logic can translate to long options or debit spreads, but neutral structures would be a semantic mismatch.
- `pullback_in_trend_family`: single-leg `yes`, vertical `yes`, neutral `no`. Directional stock/ETF logic can translate to long options or debit spreads, but neutral structures would be a semantic mismatch.
- `turn_of_month_trend_family`: single-leg `no`, vertical `no`, neutral `no`. No semantic review logged.
- `stacked_ensemble_family`: single-leg `no`, vertical `no`, neutral `no`. No semantic review logged.
- `older_corrected_mean_reversion_baseline`: single-leg `no`, vertical `no`, neutral `no`. No semantic review logged.
- `older_corrected_day_of_week_vol_regime_breakout_baseline_cluster`: single-leg `yes`, vertical `yes`, neutral `no`. Directional stock/ETF logic can translate to long options or debit spreads, but neutral structures would be a semantic mismatch.
- `options_vertical_spread_wrappers`: single-leg `no`, vertical `no`, neutral `no`. No semantic review logged.
- `tradingview_reference_ideation_scripts_cluster`: single-leg `no`, vertical `no`, neutral `no`. No semantic review logged.
- `tv_pvt_top5_finalists_tsla_30m`: single-leg `no`, vertical `no`, neutral `no`. No semantic review logged.
- `index_opening_drive_lab_fb_or15_w09351000_dlong_only_ema0_vwap0_voloff_xtime_stop_1030`: single-leg `no`, vertical `no`, neutral `no`. No semantic review logged.
- `tv_pvt_top5_finalists_nvda_30m`: single-leg `no`, vertical `no`, neutral `no`. No semantic review logged.
- `tv_pvt_top5_finalists_vix_vxx_30m`: single-leg `no`, vertical `no`, neutral `no`. No semantic review logged.
- `index_opening_drive_lab_fb_or5_w09351000_dlong_only_ema0_vwap0_voloff_xtime_stop_1030`: single-leg `no`, vertical `no`, neutral `no`. No semantic review logged.
- `tv_pvt_top5_finalists_vix_vxx_60m`: single-leg `no`, vertical `no`, neutral `no`. No semantic review logged.
- `tv_pvt_top5_finalists_iwm_15m`: single-leg `no`, vertical `no`, neutral `no`. No semantic review logged.
- `codex_leveraged_pipeline_out_base_20260103_122420`: single-leg `no`, vertical `no`, neutral `no`. No semantic review logged.
- `tv_squeeze_top5_finalists_tsla_30m`: single-leg `no`, vertical `no`, neutral `no`. No semantic review logged.
- `flux_signal_engine_top20_2025_msft_residual_survivor`: single-leg `no`, vertical `no`, neutral `no`. No semantic review logged.
- `project_smart_money_concepts_family`: single-leg `no`, vertical `no`, neutral `no`. No semantic review logged.
- `project_sqzmom_lb_family`: single-leg `no`, vertical `no`, neutral `no`. No semantic review logged.
- `project_supertrend_family`: single-leg `no`, vertical `no`, neutral `no`. No semantic review logged.
- `project_rsi_cyclic_smoothed_family`: single-leg `no`, vertical `no`, neutral `no`. No semantic review logged.
- `project_combo_consensus_family`: single-leg `no`, vertical `no`, neutral `no`. No semantic review logged.
- `luxalgo_fvg_backtest_family`: single-leg `partial`, vertical `partial`, neutral `partial`. Some signal layers may support directional or range structures, but the local evidence stack is incomplete.
- `qqq_gap_prob_tool_signal_layer`: single-leg `no`, vertical `no`, neutral `no`. No semantic review logged.
- `qqq_range_engine_signal_layer`: single-leg `partial`, vertical `partial`, neutral `partial`. Some signal layers may support directional or range structures, but the local evidence stack is incomplete.
- `qqq_same_day_scan_signal_layer`: single-leg `no`, vertical `no`, neutral `no`. No semantic review logged.
- `qqq_today_nowcast_signal_layer`: single-leg `partial`, vertical `partial`, neutral `partial`. Some signal layers may support directional or range structures, but the local evidence stack is incomplete.