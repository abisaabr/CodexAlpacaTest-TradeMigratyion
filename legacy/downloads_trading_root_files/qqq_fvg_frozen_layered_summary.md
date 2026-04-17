# QQQ Frozen Winner Layered Filter Study

## Scope

- Frozen baselines defined in `C:\Users\rabisaab\Downloads\qqq_fvg_frozen_winners.md`.
- Base engines were not re-optimized. Only entry wrappers were added on top.
- Layer families tested:
  - Session start delay: `0`, `30`, and `60` minutes after the regular session open.
  - Entry cutoff: none or `14:30` ET.
  - Trend gating: `none`, `vwap`, `ema10`, and `vwap_ema10`.
- Timing filters use the actual next-bar entry time, not the signal bar timestamp.
- Exit behavior remains frozen: stop loss, take profit, reverse-on-next-open when allowed, and flat by session close.
- Costs tested: `0.0, 2.0` bps per side.

## Best Realistic Result (`2.0` Bps Per Side)

- Winner: `dominant_count_10m_always_on`.
- Variant: `active_dominant_count_session_reset`.
- Entry mode: `always_on_active`.
- Layer: `start_00_cutoff_none_trend_none`.
- Timeframe: `10m`.
- Stop loss: `1.25%`.
- Take profit: `3.50%`.
- Total return: `50.77%`.
- CAGR: `8.67%`.
- Max drawdown: `16.72%`.
- Sharpe: `0.63`.
- Profit factor: `1.25`.
- Trades: `1560` with win rate `45.96%`.

## Incremental Improvement

- Best verified improvement vs frozen baseline: `uncontested_15m_hybrid` with layer `start_00_cutoff_1430_trend_none`.
- Return delta: `1.91%`.
- Sharpe delta: `0.03`.
- Drawdown delta: `-3.28%`.

## Winner-Level Comparison At `2.0` Bps

- `dominant_count_10m_always_on` best layer: `baseline_no_extra_filter`, return `50.77%` vs frozen `50.77%`, delta `0.00%`, Sharpe delta `0.00`, drawdown delta `0.00%`.
- `uncontested_15m_hybrid` best layer: `start_00_cutoff_1430_trend_none`, return `45.31%` vs frozen `43.40%`, delta `1.91%`, Sharpe delta `0.03`, drawdown delta `-3.28%`.

| winner_id                    | timeframe_label | entry_mode          | layer_id                        | start_offset_min | cutoff | trend_filter | baseline_total_return_pct | total_return_pct | delta_total_return_pct | baseline_sharpe | sharpe | delta_sharpe | baseline_max_drawdown_pct | max_drawdown_pct | delta_max_drawdown_pct | baseline_trade_count | trade_count | delta_trade_count |
| ---------------------------- | --------------- | ------------------- | ------------------------------- | ---------------- | ------ | ------------ | ------------------------- | ---------------- | ---------------------- | --------------- | ------ | ------------ | ------------------------- | ---------------- | ---------------------- | -------------------- | ----------- | ----------------- |
| dominant_count_10m_always_on | 10m             | always_on_active    | start_00_cutoff_none_trend_none | 0                | none   | none         | 50.77%                    | 50.77%           | 0.00%                  | 0.63            | 0.63   | 0.00         | 16.72%                    | 16.72%           | 0.00%                  | 1560                 | 1560        | 0                 |
| uncontested_15m_hybrid       | 15m             | hybrid_reentry_once | start_00_cutoff_1430_trend_none | 0                | 14:30  | none         | 43.40%                    | 45.31%           | 1.91%                  | 0.68            | 0.71   | 0.03         | 13.70%                    | 10.41%           | -3.28%                 | 1328                 | 1205        | -123              |

## Top 16 Layered Results Under `2.0` Bps

| winner_id                    | timeframe_label | entry_mode          | layer_id                         | stop_loss_pct | take_profit_pct | total_return_pct | max_drawdown_pct | sharpe | profit_factor | trade_count | win_rate_pct |
| ---------------------------- | --------------- | ------------------- | -------------------------------- | ------------- | --------------- | ---------------- | ---------------- | ------ | ------------- | ----------- | ------------ |
| dominant_count_10m_always_on | 10m             | always_on_active    | start_00_cutoff_none_trend_none  | 1.25%         | 3.50%           | 50.77%           | 16.72%           | 0.63   | 1.25          | 1560        | 45.96%       |
| dominant_count_10m_always_on | 10m             | always_on_active    | start_00_cutoff_1430_trend_none  | 1.25%         | 3.50%           | 46.01%           | 14.37%           | 0.60   | 1.24          | 1424        | 45.86%       |
| uncontested_15m_hybrid       | 15m             | hybrid_reentry_once | start_00_cutoff_1430_trend_none  | 0.50%         | 4.25%           | 45.31%           | 10.41%           | 0.71   | 1.30          | 1205        | 42.16%       |
| uncontested_15m_hybrid       | 15m             | hybrid_reentry_once | start_00_cutoff_none_trend_none  | 0.50%         | 4.25%           | 43.40%           | 13.70%           | 0.68   | 1.29          | 1328        | 42.47%       |
| uncontested_15m_hybrid       | 15m             | hybrid_reentry_once | start_00_cutoff_1430_trend_ema10 | 0.50%         | 4.25%           | 38.41%           | 12.74%           | 0.65   | 1.29          | 1082        | 42.79%       |
| uncontested_15m_hybrid       | 15m             | hybrid_reentry_once | start_00_cutoff_none_trend_vwap  | 0.50%         | 4.25%           | 37.75%           | 10.49%           | 0.62   | 1.29          | 1171        | 42.19%       |
| uncontested_15m_hybrid       | 15m             | hybrid_reentry_once | start_00_cutoff_none_trend_ema10 | 0.50%         | 4.25%           | 37.63%           | 16.01%           | 0.63   | 1.28          | 1196        | 43.06%       |
| dominant_count_10m_always_on | 10m             | always_on_active    | start_00_cutoff_none_trend_vwap  | 1.25%         | 3.50%           | 36.38%           | 13.55%           | 0.51   | 1.23          | 1435        | 46.69%       |
| uncontested_15m_hybrid       | 15m             | hybrid_reentry_once | start_00_cutoff_1430_trend_vwap  | 0.50%         | 4.25%           | 36.27%           | 8.60%            | 0.62   | 1.29          | 1060        | 41.89%       |
| dominant_count_10m_always_on | 10m             | always_on_active    | start_30_cutoff_none_trend_none  | 1.25%         | 3.50%           | 35.43%           | 17.87%           | 0.49   | 1.23          | 1517        | 46.34%       |
| uncontested_15m_hybrid       | 15m             | hybrid_reentry_once | start_30_cutoff_none_trend_vwap  | 0.50%         | 4.25%           | 34.75%           | 11.31%           | 0.59   | 1.28          | 1144        | 41.96%       |
| uncontested_15m_hybrid       | 15m             | hybrid_reentry_once | start_30_cutoff_1430_trend_none  | 0.50%         | 4.25%           | 34.46%           | 10.18%           | 0.59   | 1.27          | 1157        | 41.75%       |
| uncontested_15m_hybrid       | 15m             | hybrid_reentry_once | start_30_cutoff_1430_trend_vwap  | 0.50%         | 4.25%           | 34.03%           | 9.42%            | 0.60   | 1.28          | 1032        | 41.67%       |
| uncontested_15m_hybrid       | 15m             | hybrid_reentry_once | start_30_cutoff_none_trend_none  | 0.50%         | 4.25%           | 32.72%           | 14.98%           | 0.55   | 1.27          | 1285        | 42.18%       |
| dominant_count_10m_always_on | 10m             | always_on_active    | start_00_cutoff_none_trend_ema10 | 1.25%         | 3.50%           | 31.96%           | 18.67%           | 0.46   | 1.22          | 1481        | 46.73%       |
| dominant_count_10m_always_on | 10m             | always_on_active    | start_30_cutoff_none_trend_vwap  | 1.25%         | 3.50%           | 31.83%           | 16.04%           | 0.46   | 1.22          | 1407        | 46.91%       |

## Trend Filter Snapshot Under `2.0` Bps

| winner_id                    | trend_filter | best_return | median_return | best_sharpe | median_trades |
| ---------------------------- | ------------ | ----------- | ------------- | ----------- | ------------- |
| dominant_count_10m_always_on | none         | 50.77%      | 33.31%        | 0.63        | 1402          |
| dominant_count_10m_always_on | vwap         | 36.38%      | 29.75%        | 0.51        | 1295          |
| dominant_count_10m_always_on | ema10        | 31.96%      | 14.57%        | 0.46        | 1335          |
| dominant_count_10m_always_on | vwap_ema10   | 16.45%      | 12.33%        | 0.29        | 1257          |
| uncontested_15m_hybrid       | none         | 45.31%      | 33.59%        | 0.71        | 1181          |
| uncontested_15m_hybrid       | ema10        | 38.41%      | 29.36%        | 0.65        | 1058          |
| uncontested_15m_hybrid       | vwap         | 37.75%      | 34.39%        | 0.62        | 1046          |
| uncontested_15m_hybrid       | vwap_ema10   | 30.74%      | 28.21%        | 0.56        | 975           |

## Output Files

- Full grid: `C:\Users\rabisaab\Downloads\qqq_fvg_frozen_layered_results.csv`.
- Best-by-winner table: `C:\Users\rabisaab\Downloads\qqq_fvg_frozen_layered_best_by_winner.csv`.
- Best realistic trades: `C:\Users\rabisaab\Downloads\qqq_fvg_frozen_layered_best_realistic_trades.csv`.
- Best realistic daily equity: `C:\Users\rabisaab\Downloads\qqq_fvg_frozen_layered_best_realistic_daily_equity.csv`.
- Runtime: `5.44` seconds.
