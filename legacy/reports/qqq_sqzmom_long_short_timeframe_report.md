# QQQ SQZMOM Long/Short Timeframe Grid

## What was tested

- Long/short reversal engine on QQQ regular-session bars only.
- Long signal: `red -> maroon` with `val > buy_threshold`.
- Short signal / long exit / short flip: `lime -> green` with `val > sell_threshold`.
- If already short, a new long signal flips the position to long on the next bar open.
- If already long, a new short signal flips the position to short on the next bar open.
- Timeframes tested: `1m`, `2m`, `5m`, `15m`, `60m`.
- Modes tested: swing and end-of-day-flat intraday.
- Friction: `1.0` bp per side.

## Headline findings

- Total rows tested: `300`.
- Positive full-history rows: `11`.
- Positive in all four windows: `3`.
- Best full-history row: `1m_swing_buy_-0.1_sell_1.5` with full-history return `28.43%`, CAGR `5.14%`, max DD `30.67%`, last 1y `-19.80%`, last 90d `-6.63%`, YTD 2026 `-3.33%`.

## Top rows

| Variant | TF | Mode | Buy threshold | Sell threshold | Full return | Max DD | Last 1y | Last 90d | YTD 2026 | Stability |
| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1m_swing_buy_-0.1_sell_1.5 | 1m | swing | -0.1 | 1.5 | 28.43% | 30.67% | -19.80% | -6.63% | -3.33% | 41 |
| 1m_swing_buy_-0.02_sell_1.5 | 1m | swing | -0.02 | 1.5 | 23.33% | 28.08% | -7.89% | 8.32% | 3.06% | 9 |
| 5m_swing_buy_-0.5_sell_0.75 | 5m | swing | -0.5 | 0.75 | 22.06% | 36.40% | 6.99% | 6.46% | 7.48% | 14 |
| 5m_swing_buy_-0.5_sell_1 | 5m | swing | -0.5 | 1.0 | 18.87% | 37.11% | 20.31% | 1.22% | 2.57% | 53 |
| 2m_swing_buy_-0.5_sell_1.5 | 2m | swing | -0.5 | 1.5 | 14.07% | 41.69% | -14.48% | 2.85% | 1.72% | 18 |
| 1m_swing_buy_-0.05_sell_1.5 | 1m | swing | -0.05 | 1.5 | 10.37% | 33.68% | -20.21% | -9.08% | -8.13% | 62 |
| 5m_intraday_buy_-0.5_sell_1.5 | 5m | intraday | -0.5 | 1.5 | 9.08% | 15.65% | -5.11% | -0.64% | -2.60% | 46 |
| 5m_swing_buy_-0.5_sell_1.5 | 5m | swing | -0.5 | 1.5 | 7.68% | 42.51% | 14.87% | 2.44% | 1.59% | 56 |
| 2m_swing_buy_-0.25_sell_1.5 | 2m | swing | -0.25 | 1.5 | 7.61% | 46.68% | -9.27% | -2.58% | -3.99% | 56 |
| 1m_swing_buy_-0.5_sell_1.5 | 1m | swing | -0.5 | 1.5 | 4.32% | 41.25% | -9.56% | -9.03% | -7.51% | 54 |

## Positive In All Windows

| Variant | TF | Mode | Full return | Max DD | Last 1y | Last 90d | YTD 2026 |
| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: |
| 5m_swing_buy_-0.5_sell_0.75 | 5m | swing | 22.06% | 36.40% | 6.99% | 6.46% | 7.48% |
| 5m_swing_buy_-0.5_sell_1 | 5m | swing | 18.87% | 37.11% | 20.31% | 1.22% | 2.57% |
| 5m_swing_buy_-0.5_sell_1.5 | 5m | swing | 7.68% | 42.51% | 14.87% | 2.44% | 1.59% |

## Per-timeframe summary

### 1m

- Best row: `1m_swing_buy_-0.1_sell_1.5`.
- Mode `swing`, buy `>-0.1` on dark red, short/flip on dark green `>1.5`.
- Full-history return `28.43%`, CAGR `5.14%`, max DD `30.67%`, last 1y `-19.80%`, last 90d `-6.63%`.

### 2m

- Best row: `2m_swing_buy_-0.5_sell_1.5`.
- Mode `swing`, buy `>-0.5` on dark red, short/flip on dark green `>1.5`.
- Full-history return `14.07%`, CAGR `2.67%`, max DD `41.69%`, last 1y `-14.48%`, last 90d `2.85%`.

### 5m

- Best row: `5m_swing_buy_-0.5_sell_0.75`.
- Mode `swing`, buy `>-0.5` on dark red, short/flip on dark green `>0.75`.
- Full-history return `22.06%`, CAGR `4.07%`, max DD `36.40%`, last 1y `6.99%`, last 90d `6.46%`.

### 15m

- Best row: `15m_intraday_buy_-0.25_sell_0.35`.
- Mode `intraday`, buy `>-0.25` on dark red, short/flip on dark green `>0.35`.
- Full-history return `-6.29%`, CAGR `-1.29%`, max DD `28.55%`, last 1y `4.82%`, last 90d `3.56%`.

### 60m

- Best row: `60m_intraday_buy_-0.1_sell_0.75`.
- Mode `intraday`, buy `>-0.1` on dark red, short/flip on dark green `>0.75`.
- Full-history return `-11.32%`, CAGR `-2.38%`, max DD `24.82%`, last 1y `-11.32%`, last 90d `1.08%`.

## Important options note

- This is still an honest underlying-signal backtest, not a quote-accurate options replay.
- Local project notes repeatedly mark full historical options replay as blocked by incomplete expired-contract quote coverage and chain reconstruction gaps.
- That means calls, puts, verticals, and iron condors can be shadow-mapped from these signals, but not fairly execution-tested across the whole 2021-2026 sample with the data currently in this workspace.

## Output files

- Full grid: `C:\Users\rabisaab\Downloads\data\qqq_sqzmom_long_short_timeframe_grid.csv`
- Top full-history rows: `C:\Users\rabisaab\Downloads\data\qqq_sqzmom_long_short_timeframe_top.csv`
- Positive-all-window rows: `C:\Users\rabisaab\Downloads\data\qqq_sqzmom_long_short_timeframe_positive_all_windows.csv`
- Winner trades: `C:\Users\rabisaab\Downloads\data\qqq_sqzmom_long_short_timeframe_winner_trades.csv`
- Winner daily equity: `C:\Users\rabisaab\Downloads\data\qqq_sqzmom_long_short_timeframe_winner_daily_equity.csv`
