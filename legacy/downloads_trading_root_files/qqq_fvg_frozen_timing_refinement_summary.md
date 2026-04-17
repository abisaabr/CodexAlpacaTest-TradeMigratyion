# QQQ Frozen Winner Timing Refinement

## Scope

- Frozen winners only. No changes to variant, timeframe, entry mode, stop, or target.
- Timing refinements tested:
  - Session start delays: `0`, `15`, `30`, `45`, `60` minutes.
  - Entry cutoffs: none, `13:30`, `14:00`, `14:15`, `14:30`, `14:45`, `15:00`.
  - Block windows: none, `11:30-12:30`, `11:30-13:00`, `12:00-13:30`.
- Timing rules use actual next-bar entry times.
- Costs tested: `0.0, 2.0` bps per side.

## Best Realistic Result (`2.0` Bps Per Side)

- Winner: `dominant_count_10m_always_on`.
- Layer: `start_00_cutoff_none_block_lunch_1130_1300`.
- Total return: `116.84%`.
- CAGR: `16.96%`.
- Max drawdown: `14.53%`.
- Sharpe: `1.15`.
- Trades: `1423`.

## Incremental Improvement

- `dominant_count_10m_always_on` improved by `66.07%` with layer `start_00_cutoff_none_block_lunch_1130_1300`. Sharpe delta `0.52`, drawdown delta `-2.20%`.
- `uncontested_15m_hybrid` improved by `9.62%` with layer `start_00_cutoff_1445_block_lunch_1130_1300`. Sharpe delta `0.20`, drawdown delta `-5.39%`.

## Winner-Level Comparison At `2.0` Bps

| winner_id                    | timeframe_label | entry_mode          | layer_id                                   | start_offset_min | cutoff | block_window    | baseline_total_return_pct | total_return_pct | delta_total_return_pct | baseline_sharpe | sharpe | delta_sharpe | baseline_max_drawdown_pct | max_drawdown_pct | delta_max_drawdown_pct | baseline_trade_count | trade_count | delta_trade_count |
| ---------------------------- | --------------- | ------------------- | ------------------------------------------ | ---------------- | ------ | --------------- | ------------------------- | ---------------- | ---------------------- | --------------- | ------ | ------------ | ------------------------- | ---------------- | ---------------------- | -------------------- | ----------- | ----------------- |
| dominant_count_10m_always_on | 10m             | always_on_active    | start_00_cutoff_none_block_lunch_1130_1300 | 0                | none   | lunch_1130_1300 | 50.77%                    | 116.84%          | 66.07%                 | 0.63            | 1.15   | 0.52         | 16.72%                    | 14.53%           | -2.20%                 | 1560                 | 1423        | -137              |
| uncontested_15m_hybrid       | 15m             | hybrid_reentry_once | start_00_cutoff_1445_block_lunch_1130_1300 | 0                | 14:45  | lunch_1130_1300 | 43.40%                    | 53.02%           | 9.62%                  | 0.68            | 0.88   | 0.20         | 13.70%                    | 8.30%            | -5.39%                 | 1328                 | 1015        | -313              |

## Top 16 Timing Layers Under `2.0` Bps

| winner_id                    | timeframe_label | entry_mode       | layer_id                                   | stop_loss_pct | take_profit_pct | total_return_pct | max_drawdown_pct | sharpe | profit_factor | trade_count | win_rate_pct |
| ---------------------------- | --------------- | ---------------- | ------------------------------------------ | ------------- | --------------- | ---------------- | ---------------- | ------ | ------------- | ----------- | ------------ |
| dominant_count_10m_always_on | 10m             | always_on_active | start_00_cutoff_none_block_lunch_1130_1300 | 1.25%         | 3.50%           | 116.84%          | 14.53%           | 1.15   | 1.36          | 1423        | 49.19%       |
| dominant_count_10m_always_on | 10m             | always_on_active | start_00_cutoff_1400_block_lunch_1130_1300 | 1.25%         | 3.50%           | 115.32%          | 12.08%           | 1.17   | 1.38          | 1228        | 49.92%       |
| dominant_count_10m_always_on | 10m             | always_on_active | start_00_cutoff_1415_block_lunch_1130_1300 | 1.25%         | 3.50%           | 113.21%          | 12.19%           | 1.15   | 1.37          | 1239        | 49.88%       |
| dominant_count_10m_always_on | 10m             | always_on_active | start_00_cutoff_1430_block_lunch_1130_1300 | 1.25%         | 3.50%           | 110.66%          | 12.15%           | 1.14   | 1.36          | 1290        | 49.53%       |
| dominant_count_10m_always_on | 10m             | always_on_active | start_00_cutoff_1445_block_lunch_1130_1300 | 1.25%         | 3.50%           | 106.06%          | 13.11%           | 1.11   | 1.35          | 1307        | 49.27%       |
| dominant_count_10m_always_on | 10m             | always_on_active | start_00_cutoff_1500_block_lunch_1130_1300 | 1.25%         | 3.50%           | 104.06%          | 12.96%           | 1.07   | 1.35          | 1345        | 49.07%       |
| dominant_count_10m_always_on | 10m             | always_on_active | start_00_cutoff_1330_block_lunch_1130_1300 | 1.25%         | 3.50%           | 97.27%           | 12.82%           | 1.05   | 1.35          | 1163        | 49.53%       |
| dominant_count_10m_always_on | 10m             | always_on_active | start_45_cutoff_1415_block_lunch_1130_1300 | 1.25%         | 3.50%           | 91.92%           | 13.02%           | 1.09   | 1.38          | 1096        | 51.37%       |
| dominant_count_10m_always_on | 10m             | always_on_active | start_45_cutoff_none_block_lunch_1130_1300 | 1.25%         | 3.50%           | 88.87%           | 16.22%           | 1.03   | 1.36          | 1281        | 50.27%       |
| dominant_count_10m_always_on | 10m             | always_on_active | start_15_cutoff_none_block_lunch_1130_1300 | 1.25%         | 3.50%           | 88.85%           | 15.81%           | 0.96   | 1.33          | 1412        | 49.08%       |
| dominant_count_10m_always_on | 10m             | always_on_active | start_45_cutoff_1400_block_lunch_1130_1300 | 1.25%         | 3.50%           | 88.72%           | 12.18%           | 1.06   | 1.38          | 1084        | 51.38%       |
| dominant_count_10m_always_on | 10m             | always_on_active | start_15_cutoff_1400_block_lunch_1130_1300 | 1.25%         | 3.50%           | 87.85%           | 12.00%           | 0.98   | 1.33          | 1217        | 49.71%       |
| dominant_count_10m_always_on | 10m             | always_on_active | start_15_cutoff_1415_block_lunch_1130_1300 | 1.25%         | 3.50%           | 86.00%           | 12.70%           | 0.97   | 1.33          | 1228        | 49.67%       |
| dominant_count_10m_always_on | 10m             | always_on_active | start_30_cutoff_none_block_lunch_1130_1300 | 1.25%         | 3.50%           | 85.92%           | 15.38%           | 0.96   | 1.33          | 1382        | 49.57%       |
| dominant_count_10m_always_on | 10m             | always_on_active | start_30_cutoff_1400_block_lunch_1130_1300 | 1.25%         | 3.50%           | 83.87%           | 12.52%           | 0.97   | 1.34          | 1186        | 50.34%       |
| dominant_count_10m_always_on | 10m             | always_on_active | start_15_cutoff_1430_block_lunch_1130_1300 | 1.25%         | 3.50%           | 83.80%           | 12.27%           | 0.96   | 1.32          | 1279        | 49.34%       |

## Block Window Snapshot Under `2.0` Bps

| winner_id                    | block_window    | best_return | median_return | best_sharpe | median_trades |
| ---------------------------- | --------------- | ----------- | ------------- | ----------- | ------------- |
| dominant_count_10m_always_on | lunch_1130_1300 | 116.84%     | 82.06%        | 1.17        | 1217          |
| dominant_count_10m_always_on | lunch_1130_1230 | 80.10%      | 53.30%        | 0.90        | 1269          |
| dominant_count_10m_always_on | lunch_1200_1330 | 58.78%      | 34.51%        | 0.72        | 1242          |
| dominant_count_10m_always_on | none            | 50.77%      | 28.05%        | 0.63        | 1355          |
| uncontested_15m_hybrid       | lunch_1130_1300 | 53.02%      | 36.60%        | 0.88        | 868           |
| uncontested_15m_hybrid       | none            | 51.54%      | 23.56%        | 0.78        | 1092          |
| uncontested_15m_hybrid       | lunch_1130_1230 | 46.32%      | 25.77%        | 0.76        | 934           |
| uncontested_15m_hybrid       | lunch_1200_1330 | 31.45%      | 13.13%        | 0.58        | 896           |

## Output Files

- Full grid: `C:\Users\rabisaab\Downloads\qqq_fvg_frozen_timing_refinement_results.csv`.
- Best-by-winner table: `C:\Users\rabisaab\Downloads\qqq_fvg_frozen_timing_refinement_best_by_winner.csv`.
- Best realistic trades: `C:\Users\rabisaab\Downloads\qqq_fvg_frozen_timing_refinement_best_realistic_trades.csv`.
- Best realistic daily equity: `C:\Users\rabisaab\Downloads\qqq_fvg_frozen_timing_refinement_best_realistic_daily_equity.csv`.
- Runtime: `4.48` seconds.
