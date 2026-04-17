MASTER STRATEGY REGISTRY
Date: 2026-04-04

Total registry rows: 33

Status counts:
- blocked: 9
- exact: 20
- partial: 4

Rows

down_streak_exhaustion
- Family name: Down Streak Exhaustion
- Registry type: canonical_family
- Source provenance: master_memo
- Source repo/folder: C:\Users\rabisaab\Downloads\alpaca-stock-strategy-research
- Reconstruction status: exact
- Evidence quality: high
- Asset universe: 74-symbol explicit liquid stock and ETF universe
- Timeframe: Daily
- Directionality: long_only
- Execution assumptions: Fixed 5-bar hold in the confirmed finalist; no profit target
- Exact known parameters: Long-only exhaustion entry inside an uptrend; require uptrend_regime true, down_streak >= threshold, and RSI(5) <= cap
- Prior audited metrics: Test ending equity 125394.19; total return 25.41%; CAGR 20.50%; win rate 55.93%; expectancy 0.72% per trade; profit factor 1.6426; Sharpe 1.4177; Sortino 2.0604; max drawdown 6.05%; 354 trades; beat SPY, equal_weight_full, and equal_weight_etf
- Major risks: Uneven subset robustness, uneven regime robustness, explicit current-list universe still has survivorship limitations, execution realism on daily entries remains open
- Eligible for underlying tournament: yes
- Eligible for options single-leg translation: partial
- Eligible for multi-leg translation: no
- Source file(s): best_strategies_consolidated.txt; alpaca-stock-strategy-research/reports/confirmation_report.md; alpaca-stock-strategy-research/reports/research_report_phase5.md; alpaca-stock-strategy-research/reports/decision_table_phase5.csv

qqq_led_tqqq_sqqq_pair_opening_range_intraday_system
- Family name: QQQ-Led TQQQ/SQQQ Pair Opening-Range Intraday System
- Registry type: canonical_family
- Source provenance: master_memo
- Source repo/folder: C:\Users\rabisaab\Downloads\nasdaq-etf-intraday-alpaca
- Reconstruction status: exact
- Evidence quality: high
- Asset universe: QQQ leader; TQQQ for bull regime; SQQQ for bear regime
- Timeframe: 1-minute execution; validated finalists use 10-minute opening range and 15-minute decision intervals
- Directionality: long_short
- Execution assumptions: Stop, take profit, trailing stop, time stop, regime invalidation, and forced flat before the close
- Exact known parameters: Regime classification from QQQ EMA alignment, EMA slopes, VWAP relation, opening-range relation, relative volume, spread, and quote freshness; enter TQQQ on bullish opening-range breakout or SQQQ on bearish breakdown when threshold, VWAP, EMA, and RVOL filters pass
- Prior audited metrics: Paper-promotion baseline adverse validate/test net PnL 922.21 / 1441.14; combined expectancy 16.06; adverse max drawdown 9.23%; median daily test PnL 61.08; best day / best month share 38.93% / 66.16%; finalist-validation best adverse validate/test 1066.18 / 2140.93 with best adverse max drawdown 9.25%
- Major risks: Concentration is still too high, modeled versus realized slippage gap remains unresolved, no live promotion approval, Saturday 2026-04-04 paper window was closed so no same-day shadow session ran
- Eligible for underlying tournament: yes
- Eligible for options single-leg translation: partial
- Eligible for multi-leg translation: partial
- Source file(s): best_strategies_consolidated.txt; nasdaq-etf-intraday-alpaca/best_summary.md; nasdaq-etf-intraday-alpaca/artifacts/finalist_validation/20260403_222107/best_summary.md; nasdaq-etf-intraday-alpaca/artifacts/paper_promotion/20260404_133736/best_summary.md; nasdaq-etf-intraday-alpaca/docs/paper_runbook.md; nasdaq-etf-intraday-alpaca/src/app/strategy.py; nasdaq-etf-intraday-alpaca/src/app/regime.py

durable_crsi_family
- Family name: Durable cRSI Family
- Registry type: canonical_family
- Source provenance: master_memo
- Source repo/folder: C:\Users\rabisaab\Downloads\alpaca-stock-strategy-research
- Reconstruction status: exact
- Evidence quality: high
- Asset universe: BE, FCX, GE, RKLB durable set; CAT, HOOD, XBI, XLY watchlist set
- Timeframe: 30-minute and 60-minute
- Directionality: mixed
- Execution assumptions: Preset-specific stop-loss or take-profit overlays; flat-at-close was explicitly not part of the durable survivors
- Exact known parameters: Symbol-specific cRSI preset triggers frozen by domcycle, leveling, and trend_window configuration; all surviving durable presets retain overnight holding
- Prior audited metrics: Durable shortlist winners were FCX 60m test equity 1114.29 at 10 bps, GE 60m test equity 1120.51 at 10 bps with max drawdown 4.30%, RKLB 30m test equity 1188.89 at 15 bps with 82.61% win rate and 23 trades, and BE 60m test equity 1121.09 at 15 bps; FCX had the strongest 10 bps robustness score, GE had the cleanest drawdown, RKLB had the best 15 bps headline test equity
- Major risks: Paper track record too short, sample too small, overnight gap dependency is core to the edge, stale-data operational risk, recent no-trade evidence, and alert burden is still elevated on some presets
- Eligible for underlying tournament: yes
- Eligible for options single-leg translation: no
- Eligible for multi-leg translation: no
- Source file(s): best_strategies_consolidated.txt; alpaca-stock-strategy-research/reports/strategy_zoo/crsi_durable_shortlist_summary.md; alpaca-stock-strategy-research/reports/strategy_zoo/crsi_execution_stress_summary.md; alpaca-stock-strategy-research/reports/strategy_zoo/durable_crsi_ops/durable_registry.csv; alpaca-stock-strategy-research/reports/strategy_zoo/durable_crsi_ops/durable_crsi_promotion_blockers.md

momentum_relative_strength_family
- Family name: Momentum / Relative-Strength Family
- Registry type: canonical_family
- Source provenance: master_memo
- Source repo/folder: C:\Users\rabisaab\Downloads\alpaca-stock-strategy-research
- Reconstruction status: exact
- Evidence quality: medium
- Asset universe: 74-symbol liquid stock and ETF universe
- Timeframe: Daily
- Directionality: long_only
- Execution assumptions: Fixed holding periods in the tested variants
- Exact known parameters: Long-only rank-based selection inside uptrend_regime; choose names by excess return versus SPY or cross-sectional rank over a lookback window
- Prior audited metrics: Authoritative phase-5 summary highlights relative_strength_vs_benchmark test CAGR 49.03% on one 10-bar row and 123.15% on one 20-bar row; raw final search table contains even larger rows up to ending equity 355356.67 and CAGR 184.13%, but those rows also show extreme drawdowns above 100% and conflict with the report's own benchmark-gate summary and final conclusion
- Major risks: Decision conflict, high drawdowns in raw-table outliers, likely concentration/capacity risk, no final confirmation artifact
- Eligible for underlying tournament: yes
- Eligible for options single-leg translation: partial
- Eligible for multi-leg translation: partial
- Source file(s): best_strategies_consolidated.txt; alpaca-stock-strategy-research/reports/research_report_phase5.md; alpaca-stock-strategy-research/reports/search_results_phase5_final.csv

rsi_pullback_z_score_pullback_gap_reversion_family
- Family name: RSI Pullback / Z-Score Pullback / Gap Reversion Family
- Registry type: canonical_family
- Source provenance: master_memo
- Source repo/folder: C:\Users\rabisaab\Downloads\alpaca-stock-strategy-research
- Reconstruction status: exact
- Evidence quality: medium
- Asset universe: Liquid stock and ETF universes across the two stock research repos
- Timeframe: Daily
- Directionality: mixed
- Execution assumptions: Fixed hold in the main search framework; optional profit target in some variants
- Exact known parameters: Mean-reversion entries in higher-timeframe uptrends; RSI and z-score variants buy weakness; gap_reversion buys downside gaps inside an uptrend
- Prior audited metrics: In the newer repo, best raw-table RSI pullback row reached ending equity 130886.87 with CAGR 24.83%, Sharpe 0.7582, profit factor 1.2195, and max drawdown 38.99%; best z-score row reached ending equity 129327.49 with CAGR 23.60%, Sharpe 0.9452, profit factor 1.3136, and max drawdown 25.34%; authoritative phase-5 text also cites an RSI pullback example with validation win rate 65.38% but weak test CAGR 5.38%; frozen phase-1 gap_reversion ended 99913.70 with test CAGR -0.07% and failed the benchmark gate
- Major risks: Uneven performance across versions, weaker final evidence than Down Streak Exhaustion, and no deployment packet
- Eligible for underlying tournament: yes
- Eligible for options single-leg translation: partial
- Eligible for multi-leg translation: no
- Source file(s): best_strategies_consolidated.txt; alpaca-stock-strategy-research/reports/research_report_phase5.md; alpaca-stock-strategy-research/reports/search_results_phase5_final.csv; alpaca-stock-strategy-research/reports/baselines/phase1_mean_reversion/backtest_results.csv

breakout_trend_continuation_family
- Family name: Breakout / Trend-Continuation Family
- Registry type: canonical_family
- Source provenance: master_memo
- Source repo/folder: C:\Users\rabisaab\Downloads\alpaca-stock-strategy-research
- Reconstruction status: exact
- Evidence quality: low
- Asset universe: Liquid stock and ETF universes
- Timeframe: Daily
- Directionality: mixed
- Execution assumptions: Fixed holding periods in the search framework
- Exact known parameters: Breakouts from consolidation, continuation inside bullish MA regime, and post-compression breakout logic
- Prior audited metrics: Newer raw search table shows breakout_consolidation ending equity up to 141675.84 with CAGR 33.23%, Sharpe 0.8201, profit factor 1.3654, max drawdown 43.72%, and benchmark_outcome both; volatility_contraction_breakout reached ending equity 139993.07 with CAGR 31.92%, Sharpe 0.8535, profit factor 1.5045, max drawdown 32.72%, and benchmark_outcome both; ma_regime_continuation reached ending equity 131125.44 with CAGR 25.00%, Sharpe 0.7538, and benchmark_outcome both; older corrected breakout baseline ended 98443.60 with CAGR -2.14%
- Major risks: No final confirmation packet, raw-table risk still high, and the older repo is a cautionary counterexample
- Eligible for underlying tournament: yes
- Eligible for options single-leg translation: partial
- Eligible for multi-leg translation: partial
- Source file(s): best_strategies_consolidated.txt; alpaca-stock-strategy-research/reports/search_results_phase5_final.csv; alpaca-stock-strategy-research/reports/research_report_phase5.md; alpaca-strategy-research/data/reports/breakout_stock_audit.md; alpaca-strategy-research/data/reports/research_report.md

pullback_in_trend_family
- Family name: Pullback in Trend Family
- Registry type: canonical_family
- Source provenance: master_memo
- Source repo/folder: C:\Users\rabisaab\Downloads\alpaca-stock-strategy-research
- Reconstruction status: exact
- Evidence quality: medium
- Asset universe: Expanded daily-stock universe in the stock repo; related intraday implementation uses QQQ/TQQQ/SQQQ
- Timeframe: Daily in research tables; intraday variant exists in code
- Directionality: mixed
- Execution assumptions: Fixed hold in daily research; stop, target, trailing, time, regime invalidation, and EOD exits in the intraday implementation
- Exact known parameters: Daily family buys pullbacks inside established uptrends; intraday relative uses pullback depth, resume score, relative volume, and trend alignment
- Prior audited metrics: Raw daily search table shows very high headline rows, including ending equity 197448.06 with CAGR 75.13%, Sharpe 0.9518, profit factor 1.3813, max drawdown 80.69%, and ending equity 310992.48 with CAGR 154.58% but max drawdown 140.42% and negative Sharpe
- Major risks: Extreme drawdowns, no confirmation artifact, and confusion risk with the separate intraday pullback_resume module
- Eligible for underlying tournament: yes
- Eligible for options single-leg translation: partial
- Eligible for multi-leg translation: partial
- Source file(s): best_strategies_consolidated.txt; alpaca-stock-strategy-research/reports/search_results_phase5_final.csv; nasdaq-etf-intraday-alpaca/src/app/strategy.py

turn_of_month_trend_family
- Family name: Turn of Month Trend Family
- Registry type: canonical_family
- Source provenance: master_memo
- Source repo/folder: C:\Users\rabisaab\Downloads\alpaca-stock-strategy-research
- Reconstruction status: exact
- Evidence quality: low
- Asset universe: Expanded daily-stock universe
- Timeframe: Daily
- Directionality: mixed
- Execution assumptions: Fixed holding periods
- Exact known parameters: Long seasonal turn-of-month bias gated by uptrend_regime
- Prior audited metrics: Validation occasionally looked attractive, but top inspected rows ended with test equity 95652.47 to 87467.97 and test CAGR -3.59% to -10.43%; all inspected rows failed the benchmark gate
- Major risks: Negative test results, no benchmark support, no deployment case
- Eligible for underlying tournament: yes
- Eligible for options single-leg translation: partial
- Eligible for multi-leg translation: no
- Source file(s): best_strategies_consolidated.txt; alpaca-stock-strategy-research/reports/search_results_phase5_final.csv

stacked_ensemble_family
- Family name: Stacked Ensemble Family
- Registry type: canonical_family
- Source provenance: master_memo
- Source repo/folder: C:\Users\rabisaab\Downloads\alpaca-stock-strategy-research
- Reconstruction status: exact
- Evidence quality: low
- Asset universe: Expanded daily-stock universe
- Timeframe: Daily
- Directionality: mixed
- Execution assumptions: Fixed-hold stacked composition
- Exact known parameters: Combine component signals and require a SPY uptrend market filter
- Prior audited metrics: Best decision-grade row ended at 106637 with CAGR 5.44%, Sharpe 0.3654, profit factor 1.1091, max drawdown 22.07%, and benchmark_outcome neither
- Major risks: Added complexity without clear edge improvement
- Eligible for underlying tournament: yes
- Eligible for options single-leg translation: partial
- Eligible for multi-leg translation: no
- Source file(s): best_strategies_consolidated.txt; alpaca-stock-strategy-research/reports/research_report_phase5.md; alpaca-stock-strategy-research/reports/decision_table_phase5.csv

older_corrected_mean_reversion_baseline
- Family name: Older Corrected Mean Reversion Baseline
- Registry type: canonical_family
- Source provenance: master_memo
- Source repo/folder: C:\Users\rabisaab\Downloads\alpaca-strategy-research
- Reconstruction status: exact
- Evidence quality: medium
- Asset universe: SPY and QQQ stock-only universe
- Timeframe: Daily
- Directionality: long_short
- Execution assumptions: Average corrected hold length 3 bars
- Exact known parameters: Mean reversion on z-score and RSI; long on oversold and short on overbought conditions
- Prior audited metrics: Ending equity 102029.85; CAGR 2.81%; Sharpe 2.2262; max drawdown 0.39%; expectancy 1.07% per trade; 19 trades
- Major risks: Too small economically, too little exposure, benchmark failure
- Eligible for underlying tournament: yes
- Eligible for options single-leg translation: partial
- Eligible for multi-leg translation: no
- Source file(s): best_strategies_consolidated.txt; alpaca-strategy-research/data/reports/research_report.md; alpaca-strategy-research/data/reports/decision_table_corrected.csv

older_corrected_day_of_week_vol_regime_breakout_baseline_cluster
- Family name: Older Corrected Day-of-Week / Vol-Regime / Breakout Baseline Cluster
- Registry type: canonical_family
- Source provenance: master_memo
- Source repo/folder: C:\Users\rabisaab\Downloads\alpaca-strategy-research
- Reconstruction status: exact
- Evidence quality: low
- Asset universe: SPY and QQQ
- Timeframe: Daily
- Directionality: mixed
- Execution assumptions: Corrected holds of about 1 bar for day_of_week and 5 bars for vol_regime and breakout
- Exact known parameters: Weekday pattern rules, volatility-regime switching, and simple breakout trend-following
- Prior audited metrics: day_of_week ending equity 100303.16; vol_regime 99835.00; breakout 98443.60; none beat benchmarks; corrected breakout was clearly negative
- Major risks: Weak or negative out-of-sample returns, no benchmark edge
- Eligible for underlying tournament: yes
- Eligible for options single-leg translation: partial
- Eligible for multi-leg translation: no
- Source file(s): best_strategies_consolidated.txt; alpaca-strategy-research/data/reports/research_report.md

options_vertical_spread_wrappers
- Family name: Options Vertical-Spread Wrappers
- Registry type: canonical_family
- Source provenance: master_memo
- Source repo/folder: C:\Users\rabisaab\Downloads\alpaca-strategy-research
- Reconstruction status: partial
- Evidence quality: medium
- Asset universe: SPY and QQQ options
- Timeframe: Very short overlap windows in 2026
- Directionality: mixed
- Execution assumptions: Spread payoff over narrow overlap windows; detailed exit mechanics were not the reliable point of this packet
- Exact known parameters: Defined-risk option spreads wrapped around frozen stock strategies
- Prior audited metrics: Some rows showed spectacular headline returns over 5 to 13 trading days, but the same report says they are not economically meaningful after costs
- Major risks: Data validity problem overwhelms the strategy results
- Eligible for underlying tournament: no
- Eligible for options single-leg translation: no
- Eligible for multi-leg translation: no
- Source file(s): best_strategies_consolidated.txt; alpaca-strategy-research/data/reports/options_research_results.csv; alpaca-strategy-research/PHASE2_STOP.md; alpaca-strategy-research/data/reports/research_report.md

tradingview_reference_ideation_scripts_cluster
- Family name: TradingView Reference / Ideation Scripts Cluster
- Registry type: canonical_family
- Source provenance: master_memo
- Source repo/folder: C:\Users\rabisaab\Downloads\TV Strategies
- Reconstruction status: partial
- Evidence quality: low
- Asset universe: Mostly generic; one explicit SQQQ 1-minute script
- Timeframe: Mostly script-level; LogNormal explicitly targets 1-minute
- Directionality: mixed
- Execution assumptions: Script-defined stops, targets, and time exits where present
- Exact known parameters: Varies by script; examples include log-return z-score extremes, Hull direction flips, and ATR-based SuperTrend reversals
- Prior audited metrics: No trustworthy result packets were found alongside the scripts
- Major risks: No validated reports, no operational packet, and unclear provenance of backtests
- Eligible for underlying tournament: no
- Eligible for options single-leg translation: no
- Eligible for multi-leg translation: no
- Source file(s): best_strategies_consolidated.txt; TV Strategies/LogNormal SQQQ 1min Strategy v6.pine; TV Strategies/Hull Suite Strategy by DashTrader.txt; TV Strategies/SuperTrend Strategy.txt; TV Strategies/Strategy.txt

tv_pvt_top5_finalists_tsla_30m
- Family name: tv_pvt_top5_finalists :: tsla_30m
- Registry type: authoritative_top10_variant
- Source provenance: top10_file
- Source repo/folder: not found locally
- Reconstruction status: blocked
- Evidence quality: high
- Asset universe: TSLA
- Timeframe: 30m
- Directionality: mixed
- Execution assumptions: next_open, RTH only, no_lookahead, 2 bps per side
- Exact known parameters: 
- Prior audited metrics: trades=487; win_rate=0.511294; profit_factor=2.584840; expectancy=20.677012; max_drawdown_pct=0.003959; consistency=6/6 positive years; validation=validation_pass=True, test_pass=True
- Major risks: best direct-underlying stock paper candidate
- Eligible for underlying tournament: yes
- Eligible for options single-leg translation: partial
- Eligible for multi-leg translation: partial
- Source file(s): C:\Users\rabisaab\Downloads\top10_authoritative_inventory.txt

index_opening_drive_lab_fb_or15_w09351000_dlong_only_ema0_vwap0_voloff_xtime_stop_1030
- Family name: index_opening_drive_lab :: FB_OR15_W09351000_Dlong_only_EMA0_VWAP0_VOLoff_Xtime_stop_1030
- Registry type: authoritative_top10_variant
- Source provenance: top10_file
- Source repo/folder: not found locally
- Reconstruction status: blocked
- Evidence quality: high
- Asset universe: SPY/QQQ/IWM opening-drive workflow
- Timeframe: 1m opening drive
- Directionality: mixed
- Execution assumptions: next-bar, RTH only, no overnight holds
- Exact known parameters: 
- Prior audited metrics: combined_trades=221; combined_profit_factor=2.247960; combined_return_pct=16.880584; combined_sharpe=4.803461; combined_max_drawdown_pct=2.807224; validation=passes_final_credibility=True
- Major risks: strongest process discipline, not promoted yet
- Eligible for underlying tournament: yes
- Eligible for options single-leg translation: partial
- Eligible for multi-leg translation: partial
- Source file(s): C:\Users\rabisaab\Downloads\top10_authoritative_inventory.txt

tv_pvt_top5_finalists_nvda_30m
- Family name: tv_pvt_top5_finalists :: nvda_30m
- Registry type: authoritative_top10_variant
- Source provenance: top10_file
- Source repo/folder: not found locally
- Reconstruction status: blocked
- Evidence quality: high
- Asset universe: NVDA
- Timeframe: 30m
- Directionality: mixed
- Execution assumptions: next_open, RTH only, no_lookahead, 2 bps per side
- Exact known parameters: 
- Prior audited metrics: trades=520; win_rate=0.530769; profit_factor=2.441635; expectancy=18.171218; max_drawdown_pct=0.004030; consistency=5/6 positive years; validation=validation_pass=True, test_pass=True
- Major risks: credible secondary finalist
- Eligible for underlying tournament: yes
- Eligible for options single-leg translation: partial
- Eligible for multi-leg translation: partial
- Source file(s): C:\Users\rabisaab\Downloads\top10_authoritative_inventory.txt

tv_pvt_top5_finalists_vix_vxx_30m
- Family name: tv_pvt_top5_finalists :: vix_vxx_30m
- Registry type: authoritative_top10_variant
- Source provenance: top10_file
- Source repo/folder: not found locally
- Reconstruction status: blocked
- Evidence quality: high
- Asset universe: VIX signal -> VXX trade proxy
- Timeframe: 30m
- Directionality: mixed
- Execution assumptions: next_open, RTH only, no_lookahead, 2 bps per side
- Exact known parameters: 
- Prior audited metrics: trades=264; win_rate=0.636364; profit_factor=6.903371; expectancy=59.519560; max_drawdown_pct=0.001946; consistency=6/6 positive years; validation=validation_pass=True, test_pass=True
- Major risks: best proxy-based experimental candidate
- Eligible for underlying tournament: yes
- Eligible for options single-leg translation: partial
- Eligible for multi-leg translation: partial
- Source file(s): C:\Users\rabisaab\Downloads\top10_authoritative_inventory.txt

index_opening_drive_lab_fb_or5_w09351000_dlong_only_ema0_vwap0_voloff_xtime_stop_1030
- Family name: index_opening_drive_lab :: FB_OR5_W09351000_Dlong_only_EMA0_VWAP0_VOLoff_Xtime_stop_1030
- Registry type: authoritative_top10_variant
- Source provenance: top10_file
- Source repo/folder: not found locally
- Reconstruction status: blocked
- Evidence quality: high
- Asset universe: SPY/QQQ/IWM opening-drive workflow
- Timeframe: 1m opening drive
- Directionality: mixed
- Execution assumptions: next-bar, RTH only, no overnight holds
- Exact known parameters: 
- Prior audited metrics: combined_trades=205; combined_profit_factor=2.247361; combined_return_pct=15.144497; combined_sharpe=4.745713; combined_max_drawdown_pct=2.844462; validation=passes_final_credibility=True
- Major risks: strong shadow benchmark, not promoted
- Eligible for underlying tournament: yes
- Eligible for options single-leg translation: partial
- Eligible for multi-leg translation: partial
- Source file(s): C:\Users\rabisaab\Downloads\top10_authoritative_inventory.txt

tv_pvt_top5_finalists_vix_vxx_60m
- Family name: tv_pvt_top5_finalists :: vix_vxx_60m
- Registry type: authoritative_top10_variant
- Source provenance: top10_file
- Source repo/folder: not found locally
- Reconstruction status: blocked
- Evidence quality: high
- Asset universe: VIX signal -> VXX trade proxy
- Timeframe: 60m
- Directionality: mixed
- Execution assumptions: next_open, RTH only, no_lookahead, 2 bps per side
- Exact known parameters: 
- Prior audited metrics: trades=179; win_rate=0.642458; profit_factor=7.267063; expectancy=64.502087; max_drawdown_pct=0.001107; consistency=6/6 positive years; validation=validation_pass=True, test_pass=True
- Major risks: best backup candidate
- Eligible for underlying tournament: yes
- Eligible for options single-leg translation: partial
- Eligible for multi-leg translation: partial
- Source file(s): C:\Users\rabisaab\Downloads\top10_authoritative_inventory.txt

tv_pvt_top5_finalists_iwm_15m
- Family name: tv_pvt_top5_finalists :: iwm_15m
- Registry type: authoritative_top10_variant
- Source provenance: top10_file
- Source repo/folder: not found locally
- Reconstruction status: blocked
- Evidence quality: high
- Asset universe: IWM
- Timeframe: 15m
- Directionality: mixed
- Execution assumptions: next_open, RTH only, no_lookahead, 2 bps per side
- Exact known parameters: 
- Prior audited metrics: trades=118; win_rate=0.525424; profit_factor=1.694151; expectancy=7.876699; max_drawdown_pct=0.002311; consistency=4/6 positive years; validation=validation_pass=True, test_pass=True
- Major risks: weaker but still real research artifact
- Eligible for underlying tournament: yes
- Eligible for options single-leg translation: partial
- Eligible for multi-leg translation: partial
- Source file(s): C:\Users\rabisaab\Downloads\top10_authoritative_inventory.txt

codex_leveraged_pipeline_out_base_20260103_122420
- Family name: codex_leveraged_pipeline :: out_base_20260103_122420
- Registry type: authoritative_top10_variant
- Source provenance: top10_file
- Source repo/folder: not found locally
- Reconstruction status: blocked
- Evidence quality: high
- Asset universe: leveraged ETF basket
- Timeframe: 1m
- Directionality: mixed
- Execution assumptions: 
- Exact known parameters: ema_fast=20; ema_slow=50; atr_len=14; stop_atr=0.45; target_atr=4.0; time_stop_min=45; start_equity=1800; risk_frac=0.05; max_risk_cap=90; max_concurrent_positions=1; slip_bps=3; fee_per_side=0
- Prior audited metrics: trades=2419; win_rate_pct=18.974783; profit_factor=1.244707; return_pct=86.599208; max_drawdown_pct=10.028691; avg_r=0.195182
- Major risks: interesting but still research-only
- Eligible for underlying tournament: yes
- Eligible for options single-leg translation: partial
- Eligible for multi-leg translation: no
- Source file(s): C:\Users\rabisaab\Downloads\top10_authoritative_inventory.txt

tv_squeeze_top5_finalists_tsla_30m
- Family name: tv_squeeze_top5_finalists :: TSLA_30m
- Registry type: authoritative_top10_variant
- Source provenance: top10_file
- Source repo/folder: not found locally
- Reconstruction status: partial
- Evidence quality: high
- Asset universe: TSLA
- Timeframe: 30m
- Directionality: mixed
- Execution assumptions: strict next_open, RTH only, no_lookahead
- Exact known parameters: 
- Prior audited metrics: trades=285; win_rate=0.936842; profit_factor=240.648511; expectancy_pct=0.004678264
- Major risks: recreate exactly, but treat as likely overfit and untrustworthy until independently validated
- Eligible for underlying tournament: yes
- Eligible for options single-leg translation: partial
- Eligible for multi-leg translation: partial
- Source file(s): C:\Users\rabisaab\Downloads\top10_authoritative_inventory.txt

flux_signal_engine_top20_2025_msft_residual_survivor
- Family name: flux_signal_engine_top20_2025 :: MSFT residual survivor
- Registry type: authoritative_top10_variant
- Source provenance: top10_file
- Source repo/folder: not found locally
- Reconstruction status: blocked
- Evidence quality: medium
- Asset universe: MSFT-centered residual survivor from a broader opening-bias signal engine
- Timeframe: 
- Directionality: mixed
- Execution assumptions: offline minute-bar signal engine, no-lookahead alignment, next-bar style execution, portfolio slot management
- Exact known parameters: 
- Prior audited metrics: 
- Major risks: 
- Eligible for underlying tournament: yes
- Eligible for options single-leg translation: no
- Eligible for multi-leg translation: no
- Source file(s): C:\Users\rabisaab\Downloads\top10_authoritative_inventory.txt

project_smart_money_concepts_family
- Family name: Project Smart Money Concepts Family
- Registry type: repo_verified_family
- Source provenance: repo_verified
- Source repo/folder: C:\Users\rabisaab\project
- Reconstruction status: exact
- Evidence quality: medium
- Asset universe: Project intraday universe
- Timeframe: 1h highlighted; multiple intraday frames exist
- Directionality: long_short
- Execution assumptions: eod_flatten overlays in deployment packets
- Exact known parameters: {"native_params":{"equal_highs_lows_length":3,"equal_highs_lows_threshold":0.1,"fair_value_gap_auto_threshold":true,"fair_value_gap_extend":1,"internal_confluence_filter":false,"order_block_filter_mode":"Atr","order_block_mitigation_mode":"Close","required_confluence_count":2,"swings_length":20,"use_equal_highs_lows":false,"use_fair_value_gaps":true,"use_internal_structure":true,"use_order_blocks":false,"use_premium_discount_zones":true,"use_swing_structure":false},"overlays":{"cooldown_bars":1,"eod_flatten":true,"exit_policy":"opposite_signal","max_bars_in_trade":5,"side_mode":"long_short","stop_atr_mult":null,"take_profit_atr_mult":null}}
- Prior audited metrics: Best live-like row: META 1h, win_rate=56.6667, profit_factor=519.4958, expectancy=0.004409, trades=21
- Major risks: No GO_PAPER candidate; shadow_only or watchlist only; thin trade counts.
- Eligible for underlying tournament: yes
- Eligible for options single-leg translation: partial
- Eligible for multi-leg translation: partial
- Source file(s): C:\Users\rabisaab\project\outputs\deployment\phase5_candidate_registry.csv

project_sqzmom_lb_family
- Family name: Project SQZMOM LB Family
- Registry type: repo_verified_family
- Source provenance: repo_verified
- Source repo/folder: C:\Users\rabisaab\project
- Reconstruction status: exact
- Evidence quality: medium
- Asset universe: Project intraday universe
- Timeframe: 30m highlighted; multiple intraday frames exist
- Directionality: long_short
- Execution assumptions: eod_flatten overlays in deployment packets
- Exact known parameters: {"native_params":{"bb_length":14,"bb_mult":1.5,"kc_length":20,"kc_mult":1.0,"use_true_range":true},"overlays":{"cooldown_bars":1,"eod_flatten":false,"exit_policy":"opposite_or_eod","max_bars_in_trade":8,"side_mode":"long_short","stop_atr_mult":null,"take_profit_atr_mult":null}}
- Prior audited metrics: Phase-5 TSLA 30m family is watchlist-only with 51.2821% live-like OOS win rate and 16 trades.
- Major risks: Exact identity versus external tv_squeeze finalist is unproven; still watchlist only.
- Eligible for underlying tournament: yes
- Eligible for options single-leg translation: partial
- Eligible for multi-leg translation: partial
- Source file(s): C:\Users\rabisaab\project\outputs\reports\phase5_deployment_report.md

project_supertrend_family
- Family name: Project SuperTrend Family
- Registry type: repo_verified_family
- Source provenance: repo_verified
- Source repo/folder: C:\Users\rabisaab\project
- Reconstruction status: exact
- Evidence quality: low
- Asset universe: Project intraday universe
- Timeframe: Multiple intraday frames
- Directionality: long_short
- Execution assumptions: project overlays
- Exact known parameters: Family implementation and parameter spaces exist locally.
- Prior audited metrics: No final phase-5 leader packet found.
- Major risks: Subordinate family in decision-grade project reports.
- Eligible for underlying tournament: yes
- Eligible for options single-leg translation: partial
- Eligible for multi-leg translation: partial
- Source file(s): C:\Users\rabisaab\project\strategies\supertrend.py

project_rsi_cyclic_smoothed_family
- Family name: Project RSI Cyclic Smoothed Family
- Registry type: repo_verified_family
- Source provenance: repo_verified
- Source repo/folder: C:\Users\rabisaab\project
- Reconstruction status: exact
- Evidence quality: low
- Asset universe: Project intraday universe
- Timeframe: Multiple intraday frames
- Directionality: long_short
- Execution assumptions: project overlays
- Exact known parameters: Family implementation and parameter spaces exist locally.
- Prior audited metrics: No final phase-5 leader packet found.
- Major risks: Subordinate family in decision-grade project reports.
- Eligible for underlying tournament: yes
- Eligible for options single-leg translation: partial
- Eligible for multi-leg translation: partial
- Source file(s): C:\Users\rabisaab\project\strategies\rsi_cyclic_smoothed.py

project_combo_consensus_family
- Family name: Project Combo Consensus Family
- Registry type: repo_verified_family
- Source provenance: repo_verified
- Source repo/folder: C:\Users\rabisaab\project
- Reconstruction status: exact
- Evidence quality: low
- Asset universe: Project intraday universe
- Timeframe: Multiple intraday frames
- Directionality: mixed
- Execution assumptions: vote_mode and combo overlays
- Exact known parameters: Large combo grids exist locally.
- Prior audited metrics: Many combo rows exist but no GO_PAPER candidate.
- Major risks: Search breadth and overfit risk are high.
- Eligible for underlying tournament: yes
- Eligible for options single-leg translation: no
- Eligible for multi-leg translation: no
- Source file(s): C:\Users\rabisaab\project\strategies\combos.py

luxalgo_fvg_backtest_family
- Family name: LuxAlgo FVG Backtest Family
- Registry type: repo_verified_family
- Source provenance: repo_verified
- Source repo/folder: C:\Users\rabisaab\fvg_backtest
- Reconstruction status: partial
- Evidence quality: medium
- Asset universe: 74-symbol daily stock/ETF universe plus partial SPY/QQQ/VXX minute data
- Timeframe: Daily and partial 1m
- Directionality: long_short
- Execution assumptions: config.yaml uses commission_bps=2 and slippage_bps=1
- Exact known parameters: pine_exact / normalized_htf / trade_safe / pine_visual / lifecycle / exit-style grids exist locally.
- Prior audited metrics: Best daily row net_return=86.802013, profit_factor=1.526498; worst minute row net_return=-0.998235, max_drawdown=-1.000283
- Major risks: Saved run is partial; 77 minute tasks remain incomplete.
- Eligible for underlying tournament: yes
- Eligible for options single-leg translation: partial
- Eligible for multi-leg translation: no
- Source file(s): C:\Users\rabisaab\fvg_backtest\results\summary_by_strategy_daily.csv

qqq_gap_prob_tool_signal_layer
- Family name: QQQ Gap Probability Tool
- Registry type: supporting_signal_layer
- Source provenance: repo_verified
- Source repo/folder: C:\Users\rabisaab\qqq_gap_prob_tool
- Reconstruction status: exact
- Evidence quality: medium
- Asset universe: QQQ
- Timeframe: Daily open-context model
- Directionality: supporting_model
- Execution assumptions: open-known inputs only
- Exact known parameters: shrink_50 smoothing winner
- Prior audited metrics: No validated >60% close-in-range holdout statement with healthy counts.
- Major risks: Supporting layer only, not a standalone strategy engine.
- Eligible for underlying tournament: no
- Eligible for options single-leg translation: no
- Eligible for multi-leg translation: no
- Source file(s): C:\Users\rabisaab\qqq_gap_prob_tool\qqq_gap_prob_tool_report.md

qqq_range_engine_signal_layer
- Family name: QQQ Range Engine
- Registry type: supporting_signal_layer
- Source provenance: repo_verified
- Source repo/folder: C:\Users\rabisaab\qqq_range_engine
- Reconstruction status: exact
- Evidence quality: medium
- Asset universe: QQQ
- Timeframe: Daily open-context model
- Directionality: supporting_model
- Execution assumptions: only information known at the open
- Exact known parameters: gap_only engine
- Prior audited metrics: No validated >60% holdout statement met sample conditions.
- Major risks: Supporting layer only, not a standalone strategy engine.
- Eligible for underlying tournament: no
- Eligible for options single-leg translation: no
- Eligible for multi-leg translation: no
- Source file(s): C:\Users\rabisaab\qqq_range_engine\qqq_range_engine_report.md

qqq_same_day_scan_signal_layer
- Family name: QQQ Same-Day Scan
- Registry type: supporting_signal_layer
- Source provenance: repo_verified
- Source repo/folder: C:\Users\rabisaab\qqq_scan
- Reconstruction status: exact
- Evidence quality: medium
- Asset universe: QQQ
- Timeframe: Daily feature scan
- Directionality: supporting_model
- Execution assumptions: local QQQ daily data only
- Exact known parameters: gap_pct and open-relative features were the strongest descriptive effects.
- Prior audited metrics: Holdout predictive effects were modest.
- Major risks: Signal research only, not a trade engine.
- Eligible for underlying tournament: no
- Eligible for options single-leg translation: no
- Eligible for multi-leg translation: no
- Source file(s): C:\Users\rabisaab\qqq_scan\qqq_same_day_scan_report.md

qqq_today_nowcast_signal_layer
- Family name: QQQ Today Nowcast
- Registry type: supporting_signal_layer
- Source provenance: repo_verified
- Source repo/folder: C:\Users\rabisaab\qqq_today_nowcast
- Reconstruction status: exact
- Evidence quality: low
- Asset universe: QQQ
- Timeframe: Daily snapshot
- Directionality: supporting_model
- Execution assumptions: snapshot output only
- Exact known parameters: Daily nowcast tables and JSON outputs.
- Prior audited metrics: No backtest packet found.
- Major risks: Snapshot helper only, not a strategy engine.
- Eligible for underlying tournament: no
- Eligible for options single-leg translation: no
- Eligible for multi-leg translation: no
- Source file(s): C:\Users\rabisaab\qqq_today_nowcast\today_nowcast.md
