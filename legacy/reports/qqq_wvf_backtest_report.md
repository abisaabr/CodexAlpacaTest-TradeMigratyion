# QQQ Williams Vix Fix Backtest

## Setup

- Source data: `C:\Users\rabisaab\Downloads\QQQ_1min_20210308-20260308_sip (1).csv`.
- Source bars loaded: `489,130` regular-session 1-minute bars from `2021-03-08 11:08:00-05:00` through `2026-03-06 15:59:00-05:00`.
- Pine inputs held at the pasted defaults unless noted: `pd=22`, `bbl=20`, `lb=50`, `pl=1.01`.
- Optimized fields: timeframe `(15, 30, 60)`, `mult` `(2.0, 2.5, 3.0)`, `ph` `(0.85, 0.9)`, trigger mode `('band', 'percentile', 'either')`, confirmation, trend filter, and hold bars `(4, 8)`.
- Orders fill on the next bar open after the signal bar. Open positions are marked to each bar close and closed on the final sample close if still open.
- Transaction cost assumption: `1.0` bp per side.

## Best Long Variant

- Chosen for stability: `long_60m_mult2.5_ph0.9_either_none_ema0_hold8 | 60m | mult 2.50 | ph 0.90 | either | none | trend 0 | hold 8`.
- Full-history return `10.95%`, max drawdown `22.82%`, daily Sharpe `0.26`, trades `271`.
- Last 1y `12.19%`, last 90d `6.91%`, YTD 2026 `7.55%`, stability score `53`.

## Best Short Variant

- Chosen for stability: `short_15m_mult3_ph0.85_band_red_bar_ema0_hold4 | 15m | mult 3.00 | ph 0.85 | band | red_bar | trend 0 | hold 4`.
- Full-history return `9.60%`, max drawdown `4.61%`, daily Sharpe `0.47`, trades `271`.
- Last 1y `0.19%`, last 90d `2.53%`, YTD 2026 `2.15%`, stability score `559`.

## Coverage

- Total variants tested: `1944`.
- Long variants positive in all four windows: `115`.
- Short variants positive in all four windows: `20`.

## Full-History Leaders

| Side | Variant | Full return | Max DD | Last 1y | Last 90d | YTD 2026 | Trades | Stability score |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Long | long_30m_mult2.5_ph0.9_either_green_bar_ema0_hold8 | 24.52% | 2.97% | 4.43% | 0.92% | 1.35% | 126 | 208 |
| Short | short_15m_mult2_ph0.9_band_red_bar_ema50_hold8 | 41.41% | 12.09% | -2.31% | 3.47% | 2.74% | 395 | 359 |

## Output Files

- Full grid: `C:\Users\rabisaab\Downloads\data\qqq_wvf_long_short_grid.csv`
- Long full-history leaderboard: `C:\Users\rabisaab\Downloads\data\qqq_wvf_top_full_history_long.csv`
- Short full-history leaderboard: `C:\Users\rabisaab\Downloads\data\qqq_wvf_top_full_history_short.csv`
- Long stability leaderboard: `C:\Users\rabisaab\Downloads\data\qqq_wvf_top_stability_long.csv`
- Short stability leaderboard: `C:\Users\rabisaab\Downloads\data\qqq_wvf_top_stability_short.csv`
- Best stable long trades: `C:\Users\rabisaab\Downloads\data\qqq_wvf_best_stable_long_trades.csv`
- Best stable short trades: `C:\Users\rabisaab\Downloads\data\qqq_wvf_best_stable_short_trades.csv`
- Best stable long daily equity: `C:\Users\rabisaab\Downloads\data\qqq_wvf_best_stable_long_daily_equity.csv`
- Best stable short daily equity: `C:\Users\rabisaab\Downloads\data\qqq_wvf_best_stable_short_daily_equity.csv`
