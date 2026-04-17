# QQQ LuxAlgo FVG Backtest

## Extracted Fair Value Gap Logic

The Pine logic used for each timeframe bar was translated as:

```text
bar_delta_pct[t] = (close[t-1] - open[t-1]) / (open[t-1] * 100)
auto_threshold[t] = 2 * cumulative_abs(bar_delta_pct) / bar_index
bullish_fvg[t] = low[t] > high[t-2] and close[t-1] > high[t-2] and bar_delta_pct[t] > auto_threshold[t]
bearish_fvg[t] = high[t] < low[t-2] and close[t-1] < low[t-2] and -bar_delta_pct[t] > auto_threshold[t]
```

## Backtest Assumptions

- Source file: `C:\Users\rabisaab\Downloads\QQQ_1min_20210308-20260308_sip (1).csv`.
- Data window after filtering incomplete sessions: `2021-03-09 09:30:00-05:00` through `2026-03-06 15:59:00-05:00`.
- Session filter: regular trading hours only, `09:30-15:59` ET, and positions are forced flat at each session close.
- Entry timing: next bar open after a new bullish or bearish FVG forms.
- Direction: long on bullish FVG, short on bearish FVG, one position at a time.
- Exit timing: stop loss, take profit, opposite-signal reversal on next bar open, or session close.
- Intrabar tie-break: if both stop and target are touched in the same bar, the stop is assumed to fill first.
- Trading costs and slippage: not included.
- Grid size: `8 timeframes x 6 stop values x 8 target values = 384` combinations.

## Best Overall Setting

- Timeframe: `10m`.
- Stop loss: `0.25%`.
- Take profit: `4.00%`.
- Total return: `185.88%` on `100,000` starting capital.
- CAGR: `23.69%`.
- Max drawdown: `11.35%`.
- Sharpe: `1.84`.
- Profit factor: `1.31`.
- Trades: `2104` with win rate `30.70%`.
- Average trade: `0.052%`.
- Average holding time: `95.7` minutes.
- Bullish signals on this timeframe: `1442`.
- Bearish signals on this timeframe: `1702`.

## Top 15 Overall

| timeframe_label | stop_loss_pct | take_profit_pct | total_return_pct | cagr_pct | max_drawdown_pct | sharpe | profit_factor | trade_count | win_rate_pct |
| --------------- | ------------- | --------------- | ---------------- | -------- | ---------------- | ------ | ------------- | ----------- | ------------ |
| 10m             | 0.25%         | 4.00%           | 185.88%          | 23.69%   | 11.35%           | 1.84   | 1.31          | 2104        | 30.70%       |
| 10m             | 0.25%         | 3.00%           | 175.23%          | 22.74%   | 10.99%           | 1.83   | 1.30          | 2110        | 30.76%       |
| 10m             | 0.25%         | 2.00%           | 166.07%          | 21.91%   | 12.07%           | 1.82   | 1.29          | 2139        | 30.72%       |
| 10m             | 0.50%         | 4.00%           | 160.75%          | 21.41%   | 13.50%           | 1.51   | 1.23          | 1913        | 41.40%       |
| 10m             | 0.50%         | 2.00%           | 156.36%          | 20.99%   | 13.30%           | 1.54   | 1.22          | 1946        | 41.73%       |
| 10m             | 0.25%         | 1.50%           | 151.35%          | 20.51%   | 10.77%           | 1.77   | 1.26          | 2188        | 30.85%       |
| 10m             | 0.50%         | 3.00%           | 150.91%          | 20.47%   | 13.50%           | 1.47   | 1.22          | 1919        | 41.43%       |
| 10m             | 1.50%         | 4.00%           | 147.32%          | 20.12%   | 15.89%           | 1.36   | 1.21          | 1799        | 45.75%       |
| 10m             | 0.75%         | 4.00%           | 143.90%          | 19.78%   | 16.07%           | 1.37   | 1.21          | 1838        | 44.61%       |
| 10m             | 1.00%         | 4.00%           | 143.25%          | 19.71%   | 15.95%           | 1.34   | 1.20          | 1811        | 45.50%       |
| 10m             | 0.75%         | 2.00%           | 139.83%          | 19.37%   | 16.24%           | 1.37   | 1.20          | 1871        | 44.90%       |
| 10m             | 1.50%         | 3.00%           | 138.92%          | 19.28%   | 15.66%           | 1.32   | 1.20          | 1806        | 45.79%       |
| 10m             | 2.00%         | 4.00%           | 138.18%          | 19.20%   | 16.90%           | 1.29   | 1.20          | 1799        | 45.75%       |
| 10m             | 0.50%         | 1.50%           | 137.28%          | 19.11%   | 16.30%           | 1.45   | 1.20          | 2003        | 41.84%       |
| 10m             | 0.75%         | 3.00%           | 135.81%          | 18.96%   | 15.93%           | 1.33   | 1.20          | 1844        | 44.69%       |

## Best By Timeframe

| timeframe_label | stop_loss_pct | take_profit_pct | total_return_pct | max_drawdown_pct | sharpe | trade_count |
| --------------- | ------------- | --------------- | ---------------- | ---------------- | ------ | ----------- |
| 1m              | 0.25%         | 1.50%           | 52.57%           | 23.96%           | 0.63   | 15456       |
| 2m              | 0.25%         | 4.00%           | 17.15%           | 22.09%           | 0.30   | 8416        |
| 3m              | 0.50%         | 2.00%           | 91.63%           | 14.43%           | 0.93   | 5328        |
| 5m              | 0.50%         | 4.00%           | 124.28%          | 15.37%           | 1.20   | 3359        |
| 10m             | 0.25%         | 4.00%           | 185.88%          | 11.35%           | 1.84   | 2104        |
| 15m             | 0.50%         | 4.00%           | 111.08%          | 11.20%           | 1.34   | 1422        |
| 30m             | 1.00%         | 1.50%           | 27.03%           | 17.74%           | 0.57   | 807         |
| 60m             | 1.50%         | 2.00%           | 34.17%           | 12.64%           | 0.87   | 468         |

## Output Files

- Full grid: `C:\Users\rabisaab\Downloads\qqq_fvg_grid_results.csv`.
- Best trade ledger: `C:\Users\rabisaab\Downloads\qqq_fvg_best_trades.csv`.
- Best daily equity: `C:\Users\rabisaab\Downloads\qqq_fvg_best_daily_equity.csv`.
- Runtime: `8.39` seconds.

