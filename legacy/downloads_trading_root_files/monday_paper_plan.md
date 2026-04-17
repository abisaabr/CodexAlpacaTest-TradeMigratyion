# Monday Paper Plan

## Ranked operational recommendation

1. Run `qqq_led_tqqq_sqqq_pair_opening_range_intraday_system` in paper now, but only as the underlying ETF workflow with exact adverse-baseline settings: opening window `10`, threshold `15 bps`, decision interval `15m`, start delay `25m`, flat before close `40m`, notional `50%`, blocked hours `[]`, minimum relative volume `1.0`.
2. Shadow-record option candidates off that same intraday signal only. First structures to shadow are `2 DTE 1-strike OTM long calls/puts` and, secondarily, simple debit spreads. Do not count those option shadows as promoted strategy PnL yet.
3. Keep `down_streak_exhaustion` and `durable_crsi_family` out of the Monday promoted paper sleeve. Use them only as research/watchlist comparisons.
4. Exclude `tv_squeeze_top5_finalists :: TSLA_30m`, `flux_signal_engine_top20_2025 :: MSFT residual survivor`, and the blocked top-10 variants from Monday paper until exact lineage is recovered and rerun.

## Direct answers

1. Which exact strategies should be run in paper now?
   `qqq_led_tqqq_sqqq_pair_opening_range_intraday_system` only, and only as the underlying ETF workflow plus option shadow capture.
2. Which should stay research-only?
   `down_streak_exhaustion`, `durable_crsi_family`, `momentum_relative_strength_family`, `breakout_trend_continuation_family`, `rsi_pullback_z_score_pullback_gap_reversion_family`, `pullback_in_trend_family`.
3. Which should be excluded entirely?
   `tv_squeeze_top5_finalists :: TSLA_30m`, `flux_signal_engine_top20_2025 :: MSFT residual survivor`, incomplete `luxalgo_fvg_backtest_family` promotion attempts, and any blocked top-10 variant that still lacks exact lineage.
4. Which symbols and option structures should be used first?
   Symbols: `QQQ` as the signal leader, executed through `TQQQ` for bull signals and `SQQQ` for bear signals on the underlying side. Option structures: shadow only, starting with `2 DTE 1-strike OTM calls/puts`; secondary shadow structure `simple debit spreads` when liquidity is clearly acceptable.
5. What is the daily risk budget?
   Operational cap for Monday paper: `1.0%` of account equity (`$250`) as a daily stop for the paper engine, while preserving the native `50%` notional cap inside the pair-system baseline. This is an operational wrapper for paper discipline, not a rewritten strategy rule.
6. What is the expected trade count per day?
   For the pair-system adverse baseline, about `2.15` trade events per active day. Expect a practical Monday range of roughly `1 to 3` paper trades if the opening-drive conditions trigger.
7. What exact blockers still prevent promotion?
   `historical options quotes unavailable`, `no full 5-year timestamp-aligned options archive`, `top-day concentration still too high`, `modeled versus realized slippage gap still unresolved`, `blocked top-10 source lineage still missing`, and `DSE still fragile in regime/subset diagnostics`.