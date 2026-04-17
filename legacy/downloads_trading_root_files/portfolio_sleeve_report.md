# Portfolio Sleeve Report

- Method note: completed sleeves use a weighted realized exit-date PnL approximation, not a synchronized mark-to-market portfolio backtest. That keeps lineage honest but means the sleeve output is still a screening layer rather than a promotion-ready portfolio audit.

- `intraday_plus_daily_hybrid`: blocked. Blocked. No synchronized full-window intraday pair trade ledger was exported into the standardized tournament ledger.
- `options_only_sleeve`: blocked. Blocked. The options realism gate excluded all trades.
- `mixed_underlying_and_options_sleeve`: blocked. Blocked. Honest options replay was not available, so there is nothing credible to mix with the underlying sleeve results.
- `daily_momentum_aggressive`: final equity `$214996.03`, drawdown `41.56%`, approx trades/day `2.17`, reached $100k `True`.
- `tier1_plus_challenger`: final equity `$128174.84`, drawdown `26.46%`, approx trades/day `1.30`, reached $100k `True`.
- `daily_balanced_mix`: final equity `$118026.63`, drawdown `24.68%`, approx trades/day `1.21`, reached $100k `True`.
- `daily_conservative_quality`: final equity `$38643.93`, drawdown `9.37%`, approx trades/day `0.61`, reached $100k `False`.
- `daily_meanrev_only`: final equity `$37379.34`, drawdown `10.20%`, approx trades/day `0.69`, reached $100k `False`.
- `daily_trend_only`: final equity `$37505.64`, drawdown `10.39%`, approx trades/day `0.33`, reached $100k `False`.