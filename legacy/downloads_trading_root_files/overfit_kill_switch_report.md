# Overfit Kill Switch Report

## Failed

- `down_streak_exhaustion`: Top 10% of realized days drove more than 40% of total positive PnL on the 5-year user-subset tournament.; The exact confirmation report still classifies the strategy as fragile and notes a failed regime slice plus weak subset-specific benchmark robustness. Usable as `promotion_ineligible`.
- `qqq_led_tqqq_sqqq_pair_opening_range_intraday_system`: Top 10% of daily PnL observations in the adverse baseline contributed more than 40% of positive PnL.; Concentration and modeled-versus-realized slippage gaps remain unresolved, so promotion is not justified yet. Usable as `paper_only`.
- `momentum_relative_strength_family`: The strongest raw rows conflict with the decision-grade summary and still rely on concentrated winners such as NVDA.; The 5-year user-subset tournament also shows top-day concentration above the hard kill-switch threshold. Usable as `research_only`.
- `rsi_pullback_z_score_pullback_gap_reversion_family`: The reproduced user-subset variants still show top-day concentration above the hard 40% threshold.; Gap reversion remains weaker than the family label suggests, and there is no clean deployment packet overturning that weakness. Usable as `research_only`.
- `breakout_trend_continuation_family`: User-subset breakout variants exceed the top-day concentration threshold.; The newer raw-table strength still conflicts with the older corrected breakout audit, so the evidence stack is not clean enough. Usable as `research_only`.
- `pullback_in_trend_family`: Max drawdown in the 5-year user-subset tournament is extreme at roughly 74.55%.; The strongest rows remain concentration-heavy and rely on unstable raw-table upside. Usable as `research_only`.
- `turn_of_month_trend_family`: Top-day concentration exceeds the hard threshold and total edge is too small to survive the stricter screen. Usable as `research_only`.
- `tv_squeeze_top5_finalists_tsla_30m`: The authoritative inventory itself says to treat the artifact as likely overfit until independently validated. Usable as `promotion_ineligible`.
- `luxalgo_fvg_backtest_family`: The local run is explicitly partial, and the minute-resolution path collapses badly enough that the family is not promotion-safe. Usable as `research_only`.

## Blocked

- `tv_pvt_top5_finalists_tsla_30m`: Exact local source/config lineage is missing, so the kill switch cannot be adjudicated honestly on a runnable reconstruction. Usable as `blocked`.
- `index_opening_drive_lab_fb_or15_w09351000_dlong_only_ema0_vwap0_voloff_xtime_stop_1030`: Exact local source/config lineage is missing, so the kill switch cannot be adjudicated honestly on a runnable reconstruction. Usable as `blocked`.
- `tv_pvt_top5_finalists_nvda_30m`: Exact local source/config lineage is missing, so the kill switch cannot be adjudicated honestly on a runnable reconstruction. Usable as `blocked`.
- `tv_pvt_top5_finalists_vix_vxx_30m`: Exact local source/config lineage is missing, so the kill switch cannot be adjudicated honestly on a runnable reconstruction. Usable as `blocked`.
- `index_opening_drive_lab_fb_or5_w09351000_dlong_only_ema0_vwap0_voloff_xtime_stop_1030`: Exact local source/config lineage is missing, so the kill switch cannot be adjudicated honestly on a runnable reconstruction. Usable as `blocked`.
- `tv_pvt_top5_finalists_vix_vxx_60m`: Exact local source/config lineage is missing, so the kill switch cannot be adjudicated honestly on a runnable reconstruction. Usable as `blocked`.
- `tv_pvt_top5_finalists_iwm_15m`: Exact local source/config lineage is missing, so the kill switch cannot be adjudicated honestly on a runnable reconstruction. Usable as `blocked`.
- `codex_leveraged_pipeline_out_base_20260103_122420`: Exact local source/config lineage is missing, so the kill switch cannot be adjudicated honestly on a runnable reconstruction. Usable as `blocked`.
- `flux_signal_engine_top20_2025_msft_residual_survivor`: Exact local source/config lineage is missing, so the kill switch cannot be adjudicated honestly on a runnable reconstruction. Usable as `blocked`.

## Passed

- `durable_crsi_family`: No explicit kill-switch trigger was reproduced locally, but the family remains overnight-dependent and sample-thin for promotion. Usable as `watchlist_only`.
- `stacked_ensemble_family`: No direct kill-switch trigger was logged, but evidence quality is not strong enough for promotion. Usable as `research_only`.
- `older_corrected_mean_reversion_baseline`: No direct kill-switch trigger was logged, but evidence quality is not strong enough for promotion. Usable as `research_only`.
- `older_corrected_day_of_week_vol_regime_breakout_baseline_cluster`: No direct kill-switch trigger was logged, but evidence quality is not strong enough for promotion. Usable as `research_only`.
- `options_vertical_spread_wrappers`: No direct kill-switch trigger was logged, but evidence quality is not strong enough for promotion. Usable as `research_only`.
- `tradingview_reference_ideation_scripts_cluster`: No direct kill-switch trigger was logged, but evidence quality is not strong enough for promotion. Usable as `research_only`.
- `project_smart_money_concepts_family`: No direct kill-switch trigger was logged, but evidence quality is not strong enough for promotion. Usable as `research_only`.
- `project_sqzmom_lb_family`: No direct kill-switch trigger was logged, but evidence quality is not strong enough for promotion. Usable as `research_only`.
- `project_supertrend_family`: No direct kill-switch trigger was logged, but evidence quality is not strong enough for promotion. Usable as `research_only`.
- `project_rsi_cyclic_smoothed_family`: No direct kill-switch trigger was logged, but evidence quality is not strong enough for promotion. Usable as `research_only`.
- `project_combo_consensus_family`: No direct kill-switch trigger was logged, but evidence quality is not strong enough for promotion. Usable as `research_only`.
- `qqq_gap_prob_tool_signal_layer`: No direct kill-switch trigger was logged, but evidence quality is not strong enough for promotion. Usable as `research_only`.
- `qqq_range_engine_signal_layer`: Supporting model layer, not a standalone strategy engine. Usable as `supporting_signal_layer`.
- `qqq_same_day_scan_signal_layer`: No direct kill-switch trigger was logged, but evidence quality is not strong enough for promotion. Usable as `research_only`.
- `qqq_today_nowcast_signal_layer`: Supporting model layer, not a standalone strategy engine. Usable as `supporting_signal_layer`.
