# QQQ cRSI Dominant Cycle Grid Report

This report runs a dedicated dominant-cycle grid while re-optimizing the other cRSI settings inside each cycle-length bucket.

- Dominant cycle values tested: `10` through `60` in steps of `2`.
- Other settings re-optimized inside each dominant-cycle bucket: `leveling (5.0, 10.0, 15.0, 20.0)`, `entry buffer (0.0, 2.0, 4.0)`, `exit ratio (0.0, 0.5, 1.0)`, families `('mean_reversion', 'breakout')`.

| Timeframe | Best domcycle | Family | Leveling | Entry buffer | Exit ratio | Return | Max DD | Sharpe | PF | Trades |
| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1m | 60 | breakout | 5.0 | 4.0 | 1.0 | -64.39% | 65.47% | -1.50 | 0.84 | 3351 |
| 2m | 60 | breakout | 5.0 | 4.0 | 0.5 | -25.79% | 36.97% | -0.53 | 0.92 | 1876 |
| 5m | 60 | breakout | 5.0 | 4.0 | 0.5 | 10.22% | 17.42% | 0.26 | 1.06 | 777 |
| 15m | 48 | breakout | 20.0 | 0.0 | 1.0 | 40.81% | 11.78% | 0.71 | 1.17 | 900 |
| 30m | 16 | breakout | 5.0 | 2.0 | 1.0 | 39.64% | 11.52% | 0.97 | 1.27 | 636 |
| 60m | 18 | breakout | 10.0 | 4.0 | 0.5 | 32.44% | 4.97% | 1.29 | 1.66 | 297 |

## Top 5 Dominant Cycles By Timeframe

### 1m

| Rank | Domcycle | Family | Return | Max DD | Sharpe | PF |
| ---: | ---: | --- | ---: | ---: | ---: | ---: |
| 1 | 60 | breakout | -64.39% | 65.47% | -1.50 | 0.84 |
| 2 | 58 | breakout | -66.05% | 67.25% | -1.60 | 0.84 |
| 3 | 56 | breakout | -68.07% | 68.74% | -1.65 | 0.84 |
| 4 | 54 | breakout | -69.28% | 69.56% | -1.71 | 0.83 |
| 5 | 52 | breakout | -75.00% | 75.23% | -1.99 | 0.81 |

### 2m

| Rank | Domcycle | Family | Return | Max DD | Sharpe | PF |
| ---: | ---: | --- | ---: | ---: | ---: | ---: |
| 1 | 60 | breakout | -25.79% | 36.97% | -0.53 | 0.92 |
| 2 | 58 | breakout | -28.12% | 47.88% | -0.42 | 0.94 |
| 3 | 56 | breakout | -30.31% | 50.54% | -0.45 | 0.93 |
| 4 | 48 | breakout | -41.80% | 53.29% | -0.72 | 0.90 |
| 5 | 50 | breakout | -43.87% | 57.06% | -0.77 | 0.89 |

### 5m

| Rank | Domcycle | Family | Return | Max DD | Sharpe | PF |
| ---: | ---: | --- | ---: | ---: | ---: | ---: |
| 1 | 60 | breakout | 10.22% | 17.42% | 0.26 | 1.06 |
| 2 | 40 | breakout | 9.87% | 22.91% | 0.22 | 1.04 |
| 3 | 58 | breakout | 5.22% | 19.42% | 0.16 | 1.03 |
| 4 | 44 | breakout | 5.22% | 27.96% | 0.15 | 1.03 |
| 5 | 56 | breakout | 3.35% | 19.71% | 0.12 | 1.03 |

### 15m

| Rank | Domcycle | Family | Return | Max DD | Sharpe | PF |
| ---: | ---: | --- | ---: | ---: | ---: | ---: |
| 1 | 48 | breakout | 40.81% | 11.78% | 0.71 | 1.17 |
| 2 | 38 | breakout | 35.33% | 11.70% | 0.77 | 1.22 |
| 3 | 46 | breakout | 31.40% | 15.25% | 0.56 | 1.13 |
| 4 | 60 | breakout | 29.18% | 12.86% | 0.63 | 1.16 |
| 5 | 58 | breakout | 27.96% | 14.56% | 0.60 | 1.15 |

### 30m

| Rank | Domcycle | Family | Return | Max DD | Sharpe | PF |
| ---: | ---: | --- | ---: | ---: | ---: | ---: |
| 1 | 16 | breakout | 39.64% | 11.52% | 0.97 | 1.27 |
| 2 | 32 | breakout | 39.41% | 4.78% | 1.21 | 1.51 |
| 3 | 34 | breakout | 37.05% | 6.16% | 1.07 | 1.42 |
| 4 | 36 | breakout | 35.34% | 7.69% | 0.96 | 1.31 |
| 5 | 28 | breakout | 32.04% | 13.28% | 0.73 | 1.23 |

### 60m

| Rank | Domcycle | Family | Return | Max DD | Sharpe | PF |
| ---: | ---: | --- | ---: | ---: | ---: | ---: |
| 1 | 18 | breakout | 32.44% | 4.97% | 1.29 | 1.66 |
| 2 | 16 | breakout | 25.55% | 5.37% | 0.95 | 1.45 |
| 3 | 10 | breakout | 21.65% | 8.45% | 0.70 | 1.22 |
| 4 | 36 | breakout | 20.98% | 3.85% | 1.21 | 1.81 |
| 5 | 20 | breakout | 20.84% | 5.75% | 0.82 | 1.33 |

