# QQQ Active FVG Fine Optimization

## Scope

- Candidate 1: `active_dominant_count_session_reset` on `10m`.
- Candidate 2: `active_uncontested_session_reset` on `15m`.
- Entry modes:
  - `always_on_active`: current active-bias behavior.
  - `change_only`: only emit an entry when active bias changes to a new non-zero state.
- Costs tested: `0.0` and `2.0` bps per side.

## Best Realistic Result (`2.0` Bps Per Side)

- Candidate: `dominant_count_10m`.
- Variant: `active_dominant_count_session_reset`.
- Entry mode: `always_on_active`.
- Timeframe: `10m`.
- Stop loss: `1.25%`.
- Take profit: `3.50%`.
- Total return: `50.77%`.
- CAGR: `8.67%`.
- Max drawdown: `16.72%`.
- Sharpe: `0.63`.
- Profit factor: `1.25`.
- Trades: `1560` with win rate `45.96%`.

## Best By Candidate, Entry Mode, And Cost

| candidate_id       | entry_mode       | cost_bps_per_side | timeframe_label | stop_loss_pct | take_profit_pct | total_return_pct | max_drawdown_pct | sharpe | trade_count |
| ------------------ | ---------------- | ----------------- | --------------- | ------------- | --------------- | ---------------- | ---------------- | ------ | ----------- |
| dominant_count_10m | always_on_active | 0.0               | 10m             | 1.25%         | 3.50%           | 181.41%          | 12.40%           | 1.48   | 1560        |
| dominant_count_10m | always_on_active | 2.0               | 10m             | 1.25%         | 3.50%           | 50.77%           | 16.72%           | 0.63   | 1560        |
| dominant_count_10m | change_only      | 0.0               | 10m             | 1.50%         | 3.50%           | 160.15%          | 10.68%           | 1.44   | 1510        |
| dominant_count_10m | change_only      | 2.0               | 10m             | 1.50%         | 3.50%           | 42.20%           | 15.76%           | 0.57   | 1510        |
| uncontested_15m    | always_on_active | 0.0               | 15m             | 0.50%         | 4.50%           | 140.71%          | 9.67%            | 1.55   | 1364        |
| uncontested_15m    | always_on_active | 2.0               | 15m             | 0.50%         | 4.50%           | 39.48%           | 13.36%           | 0.62   | 1364        |
| uncontested_15m    | change_only      | 0.0               | 15m             | 1.25%         | 3.75%           | 118.03%          | 11.77%           | 1.34   | 1191        |
| uncontested_15m    | change_only      | 2.0               | 15m             | 1.25%         | 3.75%           | 35.40%           | 14.51%           | 0.55   | 1191        |

## Top 20 Under `2.0` Bps Per Side

| candidate_id       | entry_mode       | timeframe_label | stop_loss_pct | take_profit_pct | total_return_pct | max_drawdown_pct | sharpe | profit_factor | trade_count | win_rate_pct | exposure_pct |
| ------------------ | ---------------- | --------------- | ------------- | --------------- | ---------------- | ---------------- | ------ | ------------- | ----------- | ------------ | ------------ |
| dominant_count_10m | always_on_active | 10m             | 1.25%         | 3.50%           | 50.77%           | 16.72%           | 0.63   | 1.25          | 1560        | 45.96%       | 60.26%       |
| dominant_count_10m | always_on_active | 10m             | 1.25%         | 3.75%           | 46.86%           | 18.33%           | 0.59   | 1.25          | 1555        | 45.92%       | 60.28%       |
| dominant_count_10m | always_on_active | 10m             | 1.25%         | 4.50%           | 46.15%           | 17.24%           | 0.59   | 1.25          | 1550        | 45.87%       | 60.29%       |
| dominant_count_10m | always_on_active | 10m             | 1.50%         | 3.25%           | 45.93%           | 16.99%           | 0.58   | 1.25          | 1555        | 45.98%       | 60.50%       |
| dominant_count_10m | always_on_active | 10m             | 1.50%         | 4.50%           | 45.56%           | 16.90%           | 0.58   | 1.25          | 1546        | 45.92%       | 60.53%       |
| dominant_count_10m | always_on_active | 10m             | 1.25%         | 3.00%           | 44.29%           | 17.65%           | 0.57   | 1.24          | 1561        | 45.93%       | 60.26%       |
| dominant_count_10m | always_on_active | 10m             | 1.25%         | 4.25%           | 44.28%           | 17.87%           | 0.58   | 1.25          | 1550        | 45.87%       | 60.29%       |
| dominant_count_10m | always_on_active | 10m             | 1.50%         | 3.00%           | 44.18%           | 17.53%           | 0.57   | 1.24          | 1556        | 46.02%       | 60.50%       |
| dominant_count_10m | always_on_active | 10m             | 1.25%         | 3.25%           | 44.08%           | 17.87%           | 0.57   | 1.24          | 1563        | 45.81%       | 60.26%       |
| dominant_count_10m | always_on_active | 10m             | 1.50%         | 3.50%           | 43.86%           | 16.59%           | 0.57   | 1.24          | 1555        | 45.98%       | 60.50%       |
| dominant_count_10m | always_on_active | 10m             | 1.50%         | 4.25%           | 43.71%           | 17.54%           | 0.57   | 1.24          | 1546        | 45.92%       | 60.53%       |
| dominant_count_10m | change_only      | 10m             | 1.50%         | 3.50%           | 42.20%           | 15.76%           | 0.57   | 1.25          | 1510        | 46.03%       | 58.80%       |
| dominant_count_10m | change_only      | 10m             | 1.50%         | 4.50%           | 42.07%           | 16.63%           | 0.57   | 1.25          | 1510        | 46.03%       | 58.90%       |
| dominant_count_10m | always_on_active | 10m             | 1.25%         | 4.00%           | 41.86%           | 18.07%           | 0.56   | 1.24          | 1551        | 45.84%       | 60.29%       |
| dominant_count_10m | change_only      | 10m             | 1.25%         | 3.50%           | 41.55%           | 15.64%           | 0.56   | 1.24          | 1513        | 46.00%       | 58.59%       |
| dominant_count_10m | change_only      | 10m             | 1.25%         | 4.50%           | 41.42%           | 17.86%           | 0.56   | 1.24          | 1513        | 46.00%       | 58.69%       |
| dominant_count_10m | always_on_active | 10m             | 1.50%         | 4.00%           | 41.29%           | 17.73%           | 0.55   | 1.24          | 1547        | 45.90%       | 60.53%       |
| dominant_count_10m | always_on_active | 10m             | 2.25%         | 4.50%           | 41.29%           | 17.35%           | 0.54   | 1.24          | 1545        | 45.95%       | 60.63%       |
| dominant_count_10m | always_on_active | 10m             | 2.25%         | 3.25%           | 40.84%           | 18.07%           | 0.53   | 1.24          | 1554        | 46.01%       | 60.61%       |
| dominant_count_10m | change_only      | 10m             | 1.50%         | 4.25%           | 40.81%           | 16.83%           | 0.56   | 1.24          | 1510        | 46.03%       | 58.89%       |

## Entry Mode Comparison At `2.0` Bps

| candidate_id       | entry_mode       | positive | median_return | best_return | median_dd | best_sharpe | median_trades |
| ------------------ | ---------------- | -------- | ------------- | ----------- | --------- | ----------- | ------------- |
| dominant_count_10m | always_on_active | 104/104  | 36.08%        | 50.77%      | 18.08%    | 0.63        | 1570          |
| dominant_count_10m | change_only      | 104/104  | 26.41%        | 42.20%      | 17.88%    | 0.57        | 1513          |
| uncontested_15m    | always_on_active | 86/91    | 24.64%        | 39.48%      | 16.51%    | 0.62        | 1277          |
| uncontested_15m    | change_only      | 90/91    | 20.92%        | 35.40%      | 15.49%    | 0.55        | 1203          |

## Output Files

- Full grid: `C:\Users\rabisaab\Downloads\qqq_fvg_active_fine_grid_results.csv`.
- Best-by-candidate table: `C:\Users\rabisaab\Downloads\qqq_fvg_active_fine_best_by_candidate.csv`.
- Best realistic trades: `C:\Users\rabisaab\Downloads\qqq_fvg_active_fine_best_realistic_trades.csv`.
- Best realistic daily equity: `C:\Users\rabisaab\Downloads\qqq_fvg_active_fine_best_realistic_daily_equity.csv`.
- Runtime: `4.86` seconds.

