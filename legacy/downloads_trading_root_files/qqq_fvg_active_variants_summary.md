# QQQ Active FVG Variant Study

## Variants Tested

- `event_baseline`: only trade the new FVG formation event.
- `active_latest_*`: follow the newest still-active gap bias.
- `active_uncontested_*`: only trade if all currently active gaps point the same way.
- `active_dominant_count_*`: trade the side with more active gaps.
- `active_dominant_width_*`: trade the side with the larger summed active-gap width.
- `active_nearest_mid_*`: trade the active gap whose midpoint is closest to current price.
- `*_carry`: gaps stay active across sessions until invalidated.
- `*_session_reset`: clear the active gap stack at each new trading session.

## Best Realistic Variant (`2.0` Bps Per Side)

- Variant: `active_dominant_count_session_reset`.
- Timeframe: `10m`.
- Stop loss: `1.50%`.
- Take profit: `3.00%`.
- Total return: `44.18%`.
- CAGR: `7.69%`.
- Max drawdown: `17.53%`.
- Sharpe: `0.57`.
- Profit factor: `1.24`.
- Trades: `1556` with win rate `46.02%`.

## Best Setting By Variant And Cost

| variant                             | cost_bps_per_side | timeframe_label | stop_loss_pct | take_profit_pct | total_return_pct | max_drawdown_pct | sharpe | trade_count |
| ----------------------------------- | ----------------- | --------------- | ------------- | --------------- | ---------------- | ---------------- | ------ | ----------- |
| active_dominant_count_carry         | 0.0               | 60m             | 0.25%         | 2.00%           | 11.24%           | 17.48%           | 0.25   | 3027        |
| active_dominant_count_carry         | 2.0               | 60m             | 1.50%         | 2.00%           | -49.43%          | 50.92%           | -0.91  | 1379        |
| active_dominant_count_session_reset | 0.0               | 10m             | 1.50%         | 1.50%           | 171.67%          | 13.15%           | 1.45   | 1703        |
| active_dominant_count_session_reset | 2.0               | 10m             | 1.50%         | 3.00%           | 44.18%           | 17.53%           | 0.57   | 1556        |
| active_dominant_width_carry         | 0.0               | 60m             | 0.25%         | 3.00%           | 10.58%           | 17.68%           | 0.23   | 3047        |
| active_dominant_width_carry         | 2.0               | 60m             | 1.50%         | 2.00%           | -43.81%          | 45.46%           | -0.74  | 1398        |
| active_dominant_width_session_reset | 0.0               | 10m             | 1.50%         | 1.50%           | 147.27%          | 17.01%           | 1.31   | 1768        |
| active_dominant_width_session_reset | 2.0               | 10m             | 1.50%         | 3.00%           | 27.05%           | 23.70%           | 0.39   | 1622        |
| active_latest_carry                 | 0.0               | 10m             | 0.25%         | 3.00%           | 130.62%          | 14.14%           | 1.14   | 5689        |
| active_latest_carry                 | 2.0               | 30m             | 1.50%         | 3.00%           | -28.36%          | 39.21%           | -0.36  | 1957        |
| active_latest_session_reset         | 0.0               | 10m             | 1.50%         | 1.50%           | 176.81%          | 12.27%           | 1.50   | 2128        |
| active_latest_session_reset         | 2.0               | 10m             | 1.50%         | 3.00%           | 22.05%           | 18.12%           | 0.34   | 1984        |
| active_nearest_mid_carry            | 0.0               | 2m              | 0.25%         | 3.00%           | 98.68%           | 16.85%           | 0.90   | 27880       |
| active_nearest_mid_carry            | 2.0               | 60m             | 1.50%         | 2.00%           | -28.51%          | 37.19%           | -0.44  | 1913        |
| active_nearest_mid_session_reset    | 0.0               | 10m             | 0.25%         | 4.00%           | 144.69%          | 11.15%           | 1.49   | 2928        |
| active_nearest_mid_session_reset    | 2.0               | 60m             | 1.50%         | 3.00%           | 18.08%           | 13.82%           | 0.52   | 469         |
| active_uncontested_carry            | 0.0               | 3m              | 0.50%         | 0.25%           | 9.00%            | 7.02%            | 0.36   | 1278        |
| active_uncontested_carry            | 2.0               | 3m              | 1.50%         | 2.00%           | -9.64%           | 17.37%           | -0.32  | 352         |
| active_uncontested_session_reset    | 0.0               | 10m             | 1.50%         | 1.50%           | 144.77%          | 15.49%           | 1.30   | 1682        |
| active_uncontested_session_reset    | 2.0               | 15m             | 0.50%         | 3.00%           | 37.47%           | 13.94%           | 0.60   | 1394        |
| event_baseline                      | 0.0               | 10m             | 0.25%         | 4.00%           | 185.88%          | 11.35%           | 1.84   | 2104        |
| event_baseline                      | 2.0               | 10m             | 0.25%         | 4.00%           | 23.21%           | 18.27%           | 0.41   | 2104        |

## Top 15 Under `2.0` Bps Per Side

| variant                             | timeframe_label | stop_loss_pct | take_profit_pct | total_return_pct | max_drawdown_pct | sharpe | profit_factor | trade_count | win_rate_pct | exposure_pct |
| ----------------------------------- | --------------- | ------------- | --------------- | ---------------- | ---------------- | ------ | ------------- | ----------- | ------------ | ------------ |
| active_dominant_count_session_reset | 10m             | 1.50%         | 3.00%           | 44.18%           | 17.53%           | 0.57   | 1.24          | 1556        | 46.02%       | 60.50%       |
| active_dominant_count_session_reset | 10m             | 1.50%         | 4.00%           | 41.29%           | 17.73%           | 0.55   | 1.24          | 1547        | 45.90%       | 60.53%       |
| active_dominant_count_session_reset | 10m             | 1.50%         | 2.00%           | 39.11%           | 18.29%           | 0.52   | 1.23          | 1618        | 46.66%       | 60.35%       |
| active_dominant_count_session_reset | 10m             | 2.00%         | 3.00%           | 39.05%           | 19.13%           | 0.51   | 1.23          | 1555        | 46.05%       | 60.58%       |
| active_uncontested_session_reset    | 15m             | 0.50%         | 3.00%           | 37.47%           | 13.94%           | 0.60   | 1.26          | 1394        | 41.61%       | 42.60%       |
| active_dominant_count_session_reset | 10m             | 1.50%         | 1.50%           | 37.46%           | 17.23%           | 0.51   | 1.22          | 1703        | 47.21%       | 60.13%       |
| active_dominant_count_session_reset | 15m             | 0.50%         | 3.00%           | 36.67%           | 12.44%           | 0.59   | 1.26          | 1411        | 41.46%       | 42.78%       |
| active_dominant_count_session_reset | 10m             | 2.00%         | 4.00%           | 36.24%           | 19.25%           | 0.50   | 1.23          | 1546        | 45.92%       | 60.60%       |
| active_uncontested_session_reset    | 15m             | 0.50%         | 4.00%           | 35.81%           | 13.78%           | 0.58   | 1.26          | 1372        | 41.91%       | 42.70%       |
| active_dominant_count_session_reset | 15m             | 0.50%         | 4.00%           | 35.02%           | 12.08%           | 0.57   | 1.26          | 1389        | 41.76%       | 42.86%       |
| active_dominant_count_session_reset | 10m             | 1.00%         | 4.00%           | 34.90%           | 15.88%           | 0.49   | 1.23          | 1566        | 45.40%       | 59.60%       |
| active_dominant_count_session_reset | 10m             | 1.00%         | 3.00%           | 32.88%           | 15.29%           | 0.47   | 1.22          | 1578        | 45.50%       | 59.57%       |
| active_dominant_count_session_reset | 10m             | 2.00%         | 2.00%           | 32.59%           | 19.79%           | 0.46   | 1.22          | 1612        | 46.65%       | 60.44%       |
| active_dominant_count_session_reset | 10m             | 2.00%         | 1.50%           | 32.44%           | 18.44%           | 0.46   | 1.21          | 1700        | 47.24%       | 60.21%       |
| active_uncontested_session_reset    | 10m             | 1.50%         | 3.00%           | 32.01%           | 20.03%           | 0.45   | 1.22          | 1536        | 45.70%       | 60.43%       |

## Robustness By Variant At `2.0` Bps

| variant                             | positive | median_return | best_return | median_dd | best_sharpe |
| ----------------------------------- | -------- | ------------- | ----------- | --------- | ----------- |
| active_dominant_count_session_reset | 85/384   | -43.74%       | 44.18%      | 46.25%    | 0.59        |
| active_uncontested_session_reset    | 82/384   | -43.82%       | 37.47%      | 48.26%    | 0.60        |
| active_dominant_width_session_reset | 70/384   | -48.78%       | 27.05%      | 52.75%    | 0.52        |
| event_baseline                      | 74/384   | -47.41%       | 23.21%      | 48.64%    | 0.41        |
| active_latest_session_reset         | 66/384   | -63.10%       | 22.05%      | 64.48%    | 0.34        |
| active_nearest_mid_session_reset    | 53/384   | -74.67%       | 18.08%      | 75.34%    | 0.52        |
| active_uncontested_carry            | 0/384    | -30.83%       | -9.64%      | 33.14%    | -0.32       |
| active_latest_carry                 | 0/384    | -85.99%       | -28.36%     | 86.12%    | -0.36       |
| active_nearest_mid_carry            | 0/384    | -98.18%       | -28.51%     | 98.22%    | -0.44       |
| active_dominant_width_carry         | 0/384    | -74.51%       | -43.81%     | 76.09%    | -0.70       |
| active_dominant_count_carry         | 0/384    | -74.17%       | -49.43%     | 75.77%    | -0.77       |

## Selector And Persistence Comparison At `2.0` Bps

| selector       | persistence   | positive | median_return | best_return | median_dd |
| -------------- | ------------- | -------- | ------------- | ----------- | --------- |
| dominant_count | session_reset | 85/384   | -43.74%       | 44.18%      | 46.25%    |
| uncontested    | session_reset | 82/384   | -43.82%       | 37.47%      | 48.26%    |
| dominant_width | session_reset | 70/384   | -48.78%       | 27.05%      | 52.75%    |
| latest         | session_reset | 66/384   | -63.10%       | 22.05%      | 64.48%    |
| nearest_mid    | session_reset | 53/384   | -74.67%       | 18.08%      | 75.34%    |
| uncontested    | carry         | 0/384    | -30.83%       | -9.64%      | 33.14%    |
| latest         | carry         | 0/384    | -85.99%       | -28.36%     | 86.12%    |
| nearest_mid    | carry         | 0/384    | -98.18%       | -28.51%     | 98.22%    |
| dominant_width | carry         | 0/384    | -74.51%       | -43.81%     | 76.09%    |
| dominant_count | carry         | 0/384    | -74.17%       | -49.43%     | 75.77%    |

## Output Files

- Full grid: `C:\Users\rabisaab\Downloads\qqq_fvg_active_variants_grid_results.csv`.
- Best-by-variant leaderboard: `C:\Users\rabisaab\Downloads\qqq_fvg_active_variants_best_by_variant.csv`.
- Best realistic trades: `C:\Users\rabisaab\Downloads\qqq_fvg_active_variants_best_realistic_trades.csv`.
- Best realistic daily equity: `C:\Users\rabisaab\Downloads\qqq_fvg_active_variants_best_realistic_daily_equity.csv`.
- Runtime: `66.31` seconds.

