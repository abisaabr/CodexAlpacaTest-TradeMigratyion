# QQQ SQZMOM Buy/Sell Grid

## Grid tested

- Entry thresholds on `red -> maroon`: `-4.0, -2.5, -1.5, -1.0, -0.75, -0.5, -0.35, -0.25, -0.15, -0.1, -0.05, -0.02`.
- Exit thresholds on `lime -> green`: `0.0, 0.02, 0.05, 0.1, 0.15, 0.25, 0.35, 0.5, 0.75, 1.0, 1.5`.
- Two execution modes were tested: `rth_swing` and `rth_intraday`.
- Execution assumption: next-bar-open fills, plus forced end-of-day flattening for the intraday mode.
- Cost assumption: `1.0 bp` per side.

## Headline results

- Total parameter pairs tested: `264`.
- Positive full-history pairs: `36`.
- Positive last-1-year pairs: `11`.
- Positive last-90-day pairs: `19`.
- Positive in all four windows: `2`.

## Best overall rows

| Bucket | Variant | Full return | Max DD | Last 1y | Last 90d | YTD 2026 | Stability score |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Best full history | rth_swing_buy_-0.02_sell_1.5 | 66.00% | 22.44% | 6.67% | 1.92% | 0.01% | 23 |
| Best last 1y | rth_swing_buy_-4_sell_1.5 | 44.83% | 40.85% | 7.23% | -0.81% | -0.19% | 44 |
| Best stability | rth_swing_buy_-0.02_sell_1.5 | 66.00% | 22.44% | 6.67% | 1.92% | 0.01% | 23 |

## Mode summaries

### rth_intraday

- Best full-history pair: buy `>-0.02` on dark red, sell `>1.5` on dark green. Return `8.05%`, max DD `11.73%`, last 1y `-0.01%`.
- Most stable pair: buy `>-0.5` on dark red, sell `>1.5` on dark green. Stability score `41`, full-history return `-13.59%`, last 90d `-0.48%`.

### rth_swing

- Best full-history pair: buy `>-0.02` on dark red, sell `>1.5` on dark green. Return `66.00%`, max DD `22.44%`, last 1y `6.67%`.
- Most stable pair: buy `>-0.02` on dark red, sell `>1.5` on dark green. Stability score `23`, full-history return `66.00%`, last 90d `1.92%`.

## Output files

- Full grid: `C:\Users\rabisaab\Downloads\data\qqq_sqzmom_buy_sell_grid.csv`
- Top full-history rows: `C:\Users\rabisaab\Downloads\data\qqq_sqzmom_buy_sell_top_full_history.csv`
- Top last-1-year rows: `C:\Users\rabisaab\Downloads\data\qqq_sqzmom_buy_sell_top_last_1y.csv`
- Top stability rows: `C:\Users\rabisaab\Downloads\data\qqq_sqzmom_buy_sell_top_stability.csv`
- Trades for the best-stability pair: `C:\Users\rabisaab\Downloads\data\qqq_sqzmom_buy_sell_best_stable_trades.csv`
- Daily equity for the best-stability pair: `C:\Users\rabisaab\Downloads\data\qqq_sqzmom_buy_sell_best_stable_daily_equity.csv`
