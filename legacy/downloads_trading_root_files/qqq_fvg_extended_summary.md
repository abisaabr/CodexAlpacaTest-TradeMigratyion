# QQQ FVG Extended Comparison

## What Changed

- Added per-side cost/slippage scenarios: `0.0`, `1.0`, `2.0`, and `5.0` bps per side.
- Added an `active` mode that stays aligned with the most recent still-active unfilled FVG after invalidating gaps the same way the Pine indicator deletes them.
- Kept the earlier assumptions: regular-hours only, next-bar-open entries, one position at a time, session-close flattening, stop-first tie-break, and no leverage.

## Best Realistic Setting (`2.0` bps per side)

- Mode: `event`.
- Timeframe: `10m`.
- Stop loss: `0.25%`.
- Take profit: `4.00%`.
- Total return: `23.21%`.
- CAGR: `4.31%`.
- Max drawdown: `18.27%`.
- Sharpe: `0.41`.
- Profit factor: `1.31`.
- Trades: `2104` with win rate `30.70%`.
- Event signals on this timeframe: `1442` bullish / `1702` bearish.
- Active-state bars on this timeframe: `34242` bullish / `14063` bearish.

## Best Setting By Mode And Cost

| mode   | cost_bps_per_side | timeframe_label | stop_loss_pct | take_profit_pct | total_return_pct | max_drawdown_pct | sharpe | trade_count |
| ------ | ----------------- | --------------- | ------------- | --------------- | ---------------- | ---------------- | ------ | ----------- |
| active | 0.0               | 10m             | 0.25%         | 3.00%           | 130.62%          | 14.14%           | 1.14   | 5689        |
| active | 1.0               | 15m             | 0.50%         | 3.00%           | 7.66%            | 26.01%           | 0.17   | 3446        |
| active | 2.0               | 30m             | 1.50%         | 3.00%           | -28.36%          | 39.21%           | -0.36  | 1957        |
| active | 5.0               | 60m             | 2.00%         | 3.00%           | -75.16%          | 75.40%           | -1.94  | 1568        |
| event  | 0.0               | 10m             | 0.25%         | 4.00%           | 185.88%          | 11.35%           | 1.84   | 2104        |
| event  | 1.0               | 10m             | 0.25%         | 4.00%           | 87.68%           | 14.84%           | 1.12   | 2104        |
| event  | 2.0               | 10m             | 0.25%         | 4.00%           | 23.21%           | 18.27%           | 0.41   | 2104        |
| event  | 5.0               | 60m             | 1.50%         | 2.00%           | -15.99%          | 24.39%           | -0.45  | 468         |

## Top 12 Under `2.0` Bps Per Side

| mode  | timeframe_label | stop_loss_pct | take_profit_pct | total_return_pct | max_drawdown_pct | sharpe | profit_factor | trade_count | win_rate_pct |
| ----- | --------------- | ------------- | --------------- | ---------------- | ---------------- | ------ | ------------- | ----------- | ------------ |
| event | 10m             | 0.25%         | 4.00%           | 23.21%           | 18.27%           | 0.41   | 1.31          | 2104        | 30.70%       |
| event | 10m             | 0.50%         | 4.00%           | 21.30%           | 18.51%           | 0.35   | 1.23          | 1913        | 41.40%       |
| event | 10m             | 1.50%         | 4.00%           | 20.42%           | 20.24%           | 0.33   | 1.21          | 1799        | 45.75%       |
| event | 15m             | 0.50%         | 4.00%           | 19.51%           | 16.97%           | 0.36   | 1.23          | 1422        | 42.26%       |
| event | 10m             | 0.25%         | 3.00%           | 18.34%           | 17.94%           | 0.35   | 1.30          | 2110        | 30.76%       |
| event | 10m             | 1.00%         | 4.00%           | 17.87%           | 20.37%           | 0.30   | 1.20          | 1811        | 45.50%       |
| event | 10m             | 0.50%         | 2.00%           | 17.70%           | 18.23%           | 0.32   | 1.22          | 1946        | 41.73%       |
| event | 15m             | 0.50%         | 3.00%           | 17.02%           | 17.48%           | 0.33   | 1.22          | 1426        | 42.22%       |
| event | 10m             | 0.75%         | 4.00%           | 16.92%           | 20.65%           | 0.29   | 1.21          | 1838        | 44.61%       |
| event | 10m             | 0.50%         | 3.00%           | 16.44%           | 19.28%           | 0.30   | 1.22          | 1919        | 41.43%       |
| event | 10m             | 1.50%         | 3.00%           | 16.01%           | 20.06%           | 0.28   | 1.20          | 1806        | 45.79%       |
| event | 10m             | 2.00%         | 4.00%           | 15.97%           | 21.20%           | 0.28   | 1.20          | 1799        | 45.75%       |

## Cost Sensitivity Of Best Event Spec

| mode  | timeframe_label | stop_loss_pct | take_profit_pct | cost_bps_per_side | total_return_pct | max_drawdown_pct | sharpe | trade_count |
| ----- | --------------- | ------------- | --------------- | ----------------- | ---------------- | ---------------- | ------ | ----------- |
| event | 10m             | 0.25%         | 4.00%           | 0.0               | 185.88%          | 11.35%           | 1.84   | 2104        |
| event | 10m             | 0.25%         | 4.00%           | 1.0               | 87.68%           | 14.84%           | 1.12   | 2104        |
| event | 10m             | 0.25%         | 4.00%           | 2.0               | 23.21%           | 18.27%           | 0.41   | 2104        |
| event | 10m             | 0.25%         | 4.00%           | 5.0               | -65.15%          | 65.49%           | -1.64  | 2104        |

## Cost Sensitivity Of Best Active Spec

| mode   | timeframe_label | stop_loss_pct | take_profit_pct | cost_bps_per_side | total_return_pct | max_drawdown_pct | sharpe | trade_count |
| ------ | --------------- | ------------- | --------------- | ----------------- | ---------------- | ---------------- | ------ | ----------- |
| active | 10m             | 0.25%         | 3.00%           | 0.0               | 130.62%          | 14.14%           | 1.14   | 5689        |
| active | 10m             | 0.25%         | 3.00%           | 1.0               | -26.08%          | 36.78%           | -0.29  | 5689        |
| active | 10m             | 0.25%         | 3.00%           | 2.0               | -76.31%          | 76.36%           | -1.62  | 5689        |
| active | 10m             | 0.25%         | 3.00%           | 5.0               | -99.22%          | 99.22%           | -5.04  | 5689        |

## Robustness Under `2.0` Bps Per Side

| mode   | timeframe_label | positive | median_return | best_return | median_dd | best_sharpe |
| ------ | --------------- | -------- | ------------- | ----------- | --------- | ----------- |
| active | 10m             | 0/48     | -68.79%       | -48.47%     | 68.87%    | -0.67       |
| active | 15m             | 0/48     | -57.87%       | -38.29%     | 58.79%    | -0.54       |
| active | 1m              | 0/48     | -99.98%       | -99.98%     | 99.98%    | -8.61       |
| active | 2m              | 0/48     | -98.77%       | -98.10%     | 98.78%    | -4.37       |
| active | 30m             | 0/48     | -47.15%       | -28.36%     | 50.00%    | -0.36       |
| active | 3m              | 0/48     | -95.44%       | -92.76%     | 95.52%    | -2.97       |
| active | 5m              | 0/48     | -86.55%       | -78.64%     | 86.64%    | -1.62       |
| active | 60m             | 0/48     | -51.43%       | -34.99%     | 52.06%    | -0.57       |
| event  | 10m             | 24/48    | -4.07%        | 23.21%      | 26.69%    | 0.41        |
| event  | 15m             | 18/48    | -10.50%       | 19.51%      | 25.94%    | 0.36        |
| event  | 1m              | 0/48     | -99.71%       | -99.64%     | 99.71%    | -6.10       |
| event  | 2m              | 0/48     | -96.15%       | -95.08%     | 96.17%    | -3.51       |
| event  | 30m             | 0/48     | -14.91%       | -8.02%      | 26.38%    | -0.14       |
| event  | 3m              | 0/48     | -82.35%       | -77.26%     | 83.09%    | -1.77       |
| event  | 5m              | 0/48     | -57.43%       | -41.49%     | 59.63%    | -0.65       |
| event  | 60m             | 32/48    | 1.82%         | 11.26%      | 15.17%    | 0.34        |

## Output Files

- Full comparison grid: `C:\Users\rabisaab\Downloads\qqq_fvg_extended_grid_results.csv`.
- Summary: `C:\Users\rabisaab\Downloads\qqq_fvg_extended_summary.md`.
- Best realistic overall trades: `C:\Users\rabisaab\Downloads\qqq_fvg_best_realistic_trades.csv`.
- Best realistic overall daily equity: `C:\Users\rabisaab\Downloads\qqq_fvg_best_realistic_daily_equity.csv`.
- Best realistic event-mode trades: `C:\Users\rabisaab\Downloads\qqq_fvg_best_event_realistic_trades.csv`.
- Best realistic active-mode trades: `C:\Users\rabisaab\Downloads\qqq_fvg_best_active_realistic_trades.csv`.
- Runtime: `12.53` seconds.

