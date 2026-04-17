# QQQ cRSI First-Hour Backtest Report

This test re-runs the best per-timeframe settings from the dominant-cycle grid, but only on the first trading hour of each regular-hours session (`09:30` to `10:29` ET).

| Timeframe | Settings source | Family | Domcycle | Leveling | Entry buffer | Exit ratio | Full-session return | First-hour return | First-hour max DD | Sharpe | PF | Trades |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1m | `qqq_crsi_domcycle_best_per_timeframe.csv` | breakout | 60 | 5.0 | 4.0 | 1.0 | -64.39% | -26.67% | 32.10% | -0.99 | 0.79 | 648 |
| 2m | `qqq_crsi_domcycle_best_per_timeframe.csv` | breakout | 60 | 5.0 | 4.0 | 0.5 | -25.79% | -20.57% | 22.11% | -0.87 | 0.75 | 374 |
| 5m | `qqq_crsi_domcycle_best_per_timeframe.csv` | breakout | 60 | 5.0 | 4.0 | 0.5 | 10.22% | -4.67% | 9.61% | -0.31 | 0.86 | 154 |
| 15m | `qqq_crsi_domcycle_best_per_timeframe.csv` | breakout | 48 | 20.0 | 0.0 | 1.0 | 40.81% | -7.34% | 9.82% | -0.84 | 0.62 | 126 |
| 30m | `qqq_crsi_domcycle_best_per_timeframe.csv` | breakout | 16 | 5.0 | 2.0 | 1.0 | 39.64% | 0.00% | 0.00% | 0.00 | 0.00 | 0 |
| 60m | `qqq_crsi_domcycle_best_per_timeframe.csv` | breakout | 18 | 10.0 | 4.0 | 0.5 | 32.44% | 0.00% | 0.00% | 0.00 | 0.00 | 0 |

## Readout

- Best first-hour result among timeframes that actually traded: `5m` at `-4.67%`.
- That setup used `breakout` with `domcycle=60`, `leveling=5.0`, `entry_buffer=4.0`, `exit_ratio=0.5`.
- `30m` and `60m` produced zero trades because the first-hour window leaves too few bars for a close-to-close signal and subsequent holding period.
- This is not a first-hour re-optimization. It is a first-hour replay of the settings that won on the full-session grid.
