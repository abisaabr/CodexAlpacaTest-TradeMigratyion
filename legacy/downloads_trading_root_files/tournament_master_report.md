# Tournament Master Report

## Executive summary

- Canonical families from the memo: `13`. Total registry rows after adding authoritative variants and repo-backed extras: `33`.
- Exact baseline reproductions completed: `2` (`down_streak_exhaustion`, `qqq_led_tqqq_sqqq_pair_opening_range_intraday_system`).
- Standardized 5-year underlying tournament completed for `11` daily user-subset variants with `11,051` underlying trades. Honest options replay remained blocked, so the options ledgers are empty by design rather than fictional.

## Named winners

- Best overall underlying strategy by raw 5-year user-subset return: `relative_strength_vs_benchmark_rep_user_subset_5y` with final equity `$246108.30`, but it remains speculative because the overfit kill switch failed.
- Best overall options single-leg strategy: `none`. The realism gate excluded every trade because historical option quotes are not honestly available for the required replay.
- Best overall options multi-leg strategy: `none` for the same reason.
- Best lose-small-win-big strategy that is currently reproducible: `down_streak_exhaustion` native confirmed baseline. It keeps drawdown much tighter than the raw-return leaders, but it is still fragile and promotion-ineligible under the strict kill switch.
- Best high-win-rate strategy on the standardized 5-year user-subset run: `cross_sectional_momentum_rep_user_subset_5y` at 64.86%, with the same concentration warning as the broader momentum family.
- Best practical daily paper-engine candidate: `qqq_led_tqqq_sqqq_pair_opening_range_intraday_system`. It is the only candidate that is already operationally organized enough for Monday paper-shadowing, even though it is not promotion-clean yet.
- Best symbol-specific strategy: `durable_crsi_family` as a symbol-specific preset family, though it remains watchlist-only rather than promoted.
- Best portable cross-symbol family by raw tournament output: `momentum_relative_strength_family`, but it stays speculative until the trust and concentration problems are cleared.

## Robust vs speculative vs rejected

- Robust candidates: `none` fully cleared the combined reproduction + kill-switch + options-realism standard.
- Semi-robust / paper-only: `qqq_led_tqqq_sqqq_pair_opening_range_intraday_system`.
- Research-only challengers: `down_streak_exhaustion`, `durable_crsi_family`, `momentum_relative_strength_family`, `daily_balanced_mix` sleeve.
- Overfit / rejected: `tv_squeeze_top5_finalists :: TSLA_30m`, `flux_signal_engine_top20_2025 :: MSFT residual survivor`, `luxalgo_fvg_backtest_family` pending a complete rerun.
- Blocked awaiting artifacts: the blocked `tv_pvt_top5_finalists` variants and the blocked `index_opening_drive_lab` variants.

## Top 10 underlying leaderboard

- `relative_strength_vs_benchmark_rep_user_subset_5y`: final equity `$246108.30`, return `884.43%`, drawdown `46.37%`, Sharpe `1.35`, profit factor `2.31`, win rate `64.40%`.
- `cross_sectional_momentum_rep_user_subset_5y`: final equity `$228570.54`, return `814.28%`, drawdown `43.76%`, Sharpe `1.34`, profit factor `2.49`, win rate `64.86%`.
- `pullback_in_trend_rep_user_subset_5y`: final equity `$121238.03`, return `385.00%`, drawdown `74.55%`, Sharpe `0.80`, profit factor `1.57`, win rate `60.30%`.
- `rsi_pullback_rep_user_subset_5y`: final equity `$45501.16`, return `82.02%`, drawdown `21.90%`, Sharpe `0.77`, profit factor `1.42`, win rate `54.89%`.
- `volatility_contraction_breakout_rep_user_subset_5y`: final equity `$39426.35`, return `57.71%`, drawdown `20.27%`, Sharpe `0.76`, profit factor `1.87`, win rate `62.75%`.
- `breakout_consolidation_rep_user_subset_5y`: final equity `$37130.13`, return `48.52%`, drawdown `19.13%`, Sharpe `0.75`, profit factor `1.63`, win rate `63.44%`.
- `zscore_pullback_rep_user_subset_5y`: final equity `$36030.08`, return `44.13%`, drawdown `14.62%`, Sharpe `0.68`, profit factor `1.41`, win rate `55.25%`.
- `ma_regime_continuation_rep_user_subset_5y`: final equity `$35320.21`, return `41.28%`, drawdown `12.39%`, Sharpe `0.78`, profit factor `1.69`, win rate `58.94%`.
- `dse_exact_user_subset_5y`: final equity `$31116.04`, return `24.46%`, drawdown `5.93%`, Sharpe `0.81`, profit factor `1.81`, win rate `50.22%`.
- `gap_reversion_rep_user_subset_5y`: final equity `$28827.73`, return `15.31%`, drawdown `7.06%`, Sharpe `0.56`, profit factor `1.50`, win rate `53.19%`.

## Options verdict

- Historical option quotes are still unavailable in the verified Alpaca history stack, and the local options lake is only a recent partial archive. Because the required bid/ask spread gate cannot be applied honestly, every options replay remains blocked rather than fabricated.

## Paper-engine call

- Monday recommendation: run only the `qqq_led_tqqq_sqqq_pair_opening_range_intraday_system` as the live paper-shadow priority. Everything else stays in research, watchlist, or blocked status until its evidence stack improves.