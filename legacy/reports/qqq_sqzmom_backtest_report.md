# QQQ Squeeze Momentum Backtest

## Rule interpretation used

- Indicator recreated from the LazyBear histogram `val`; the squeeze-state cross was not used for entries or exits.
- `dark red` was treated as the `maroon` histogram state: `val <= 0` and `val >= val[1]`.
- `dark green` was treated as the `green` histogram state: `val > 0` and `val <= val[1]`.
- To match `turns dark red` / `turns dark green`, signals only fire on color transitions: `red -> maroon` for entry and `lime -> green` for exit.
- Orders execute on the next bar open. The intraday variant also forces a flat exit on the last regular-session bar.
- Transaction cost assumption: `1.0` bp per side.

## Exact `>-4` rule

| Variant | Full return | CAGR | Max DD | Daily Sharpe | Trades | Win rate | Exposure | Last 1y return | Last 90d return |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| RTH swing | -86.83% | -33.37% | 87.19% | -2.53 | 11057 | 45.45% | 48.19% | -36.32% | -12.06% |
| RTH intraday | -90.68% | -37.82% | 90.80% | -3.72 | 11254 | 44.67% | 47.11% | -42.51% | -11.31% |

## Cost sensitivity for the exact `>-4` rule

| Variant | Cost/side (bps) | Full return | CAGR | Max DD | Daily Sharpe |
| --- | ---: | ---: | ---: | ---: | ---: |
| RTH swing | 0.00 | 20.21% | 3.76% | 27.79% | 0.31 |
| RTH swing | 0.25 | -30.84% | -7.12% | 39.80% | -0.39 |
| RTH swing | 0.50 | -60.21% | -16.85% | 62.95% | -1.10 |
| RTH swing | 0.75 | -77.11% | -25.57% | 77.82% | -1.82 |
| RTH swing | 1.00 | -86.83% | -33.37% | 87.19% | -2.53 |
| RTH intraday | 0.00 | -11.47% | -2.41% | 24.59% | -0.13 |
| RTH intraday | 0.25 | -49.57% | -12.81% | 52.40% | -1.02 |
| RTH intraday | 0.50 | -71.27% | -22.10% | 71.89% | -1.92 |
| RTH intraday | 0.75 | -83.63% | -30.40% | 83.91% | -2.82 |
| RTH intraday | 1.00 | -90.68% | -37.82% | 90.80% | -3.72 |

## Threshold sweep takeaways

- On regular-session bars, the `>-4` filter passed `99.70%` of all dark-red turns, so it behaves almost like an unfiltered `red -> maroon` entry rule.
- The swing version is only mildly positive at zero assumed friction: `20.21%` total return with `27.79%` max drawdown.
- It is already negative by `0.25` bp per side: `-30.84%` total return. That means the raw edge is too thin for real-world execution unless fills are unusually favorable.
- Best full-history return in this sweep: `rth_swing_threshold_-0.05` at `-26.53%` with `28.50%` max drawdown.
- Best last-1-year return in this sweep: `rth_intraday_threshold_-0.05` at `-6.00%`.
- If the full-history winner and recent winner differ, that is a warning that the threshold is not especially stable and may be getting fit to one slice of the sample.

## Output files

- Sweep metrics: `C:\Users\rabisaab\Downloads\data\qqq_sqzmom_threshold_sweep.csv`
- Exact `>-4` swing trades: `C:\Users\rabisaab\Downloads\data\qqq_sqzmom_trades_threshold_neg4_rth_swing.csv`
- Exact `>-4` intraday trades: `C:\Users\rabisaab\Downloads\data\qqq_sqzmom_trades_threshold_neg4_rth_intraday.csv`
- Exact `>-4` swing daily equity: `C:\Users\rabisaab\Downloads\data\qqq_sqzmom_daily_equity_threshold_neg4_rth_swing.csv`
- Exact `>-4` intraday daily equity: `C:\Users\rabisaab\Downloads\data\qqq_sqzmom_daily_equity_threshold_neg4_rth_intraday.csv`
- Year-by-year stats for both exact-rule variants: `C:\Users\rabisaab\Downloads\data\qqq_sqzmom_yearly_stats.csv`
- Cost sensitivity for the exact `>-4` rule: `C:\Users\rabisaab\Downloads\data\qqq_sqzmom_cost_sensitivity.csv`
