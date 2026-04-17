# QQQ SQZMOM Best Settings First-Hour Backtest

## Settings used

- Best corrected indicator inputs from the prior sweep: BB Length `20`, BB Mult `2.0`, KC Length `20`, KC Mult `1.0`, Use TrueRange `False`.
- Entry rule: buy on `red -> maroon` when `val > -0.02` and `sqzOff` is true.
- Exit rule: sell on `lime -> green` when `val > 1.5`.
- Execution: next-bar-open fills, 1 bp per side.
- First-hour window: `09:30` through `10:29:59` America/New_York.
- `first_hour_entry_only` means the entry signal must occur inside the first hour, but the position can exit later.
- `first_hour_flat` means entries are only taken from first-hour signals and any open position is forcibly closed on the last bar that starts before `10:30`.

## Results

| Mode | TF | Full return | CAGR | Max DD | Trades | Last 1y | Last 90d | YTD 2026 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| first_hour_entry_only | 15m | 2.68% | 0.53% | 0.64% | 2 | 0.00% | 0.00% | 0.00% |
| first_hour_entry_only | 5m | 0.94% | 0.19% | 2.06% | 7 | -0.09% | -0.27% | 0.00% |
| first_hour_entry_only | 60m | 0.00% | 0.00% | 0.00% | 0 | 0.00% | 0.00% | 0.00% |
| first_hour_entry_only | 1m | -0.88% | -0.18% | 11.18% | 58 | 0.93% | 0.79% | 0.79% |
| first_hour_entry_only | 2m | -3.83% | -0.78% | 12.44% | 24 | -1.60% | 0.00% | 0.00% |
| first_hour_flat | 15m | 0.56% | 0.11% | 0.36% | 2 | 0.00% | 0.00% | 0.00% |
| first_hour_flat | 60m | 0.00% | 0.00% | 0.00% | 0 | 0.00% | 0.00% | 0.00% |
| first_hour_flat | 5m | -0.16% | -0.03% | 0.62% | 7 | -0.20% | -0.14% | 0.00% |
| first_hour_flat | 2m | -1.71% | -0.35% | 2.63% | 24 | -0.02% | 0.00% | 0.00% |
| first_hour_flat | 1m | -2.91% | -0.59% | 5.06% | 63 | 0.61% | 0.79% | 0.79% |
| full_session_reference | 1m | 74.47% | 11.79% | 20.81% | 275 | 4.65% | 1.52% | 0.64% |
| full_session_reference | 5m | 10.73% | 2.06% | 6.16% | 49 | -1.60% | -0.20% | 0.00% |
| full_session_reference | 2m | 9.81% | 1.89% | 25.51% | 177 | -6.71% | 0.37% | 0.64% |
| full_session_reference | 15m | 5.57% | 1.09% | 2.61% | 10 | 0.49% | 0.00% | 0.00% |
| full_session_reference | 60m | 0.37% | 0.07% | 0.98% | 1 | 0.00% | 0.00% | 0.00% |

## Best Full-History Row

- Mode `full_session_reference`, timeframe `1m`.
- Full-history return `74.47%`, CAGR `11.79%`, max DD `20.81%`, trades `275`.
- Last 1y `4.65%`, last 90d `1.52%`, YTD 2026 `0.64%`.

## Output files

- Metrics: `C:\Users\rabisaab\Downloads\data\qqq_sqzmom_best_settings_first_hour_timeframes.csv`
- Trades for the best full-history row: `C:\Users\rabisaab\Downloads\data\qqq_sqzmom_best_settings_first_hour_best_trades.csv`
- Daily equity for the best full-history row: `C:\Users\rabisaab\Downloads\data\qqq_sqzmom_best_settings_first_hour_best_daily_equity.csv`
