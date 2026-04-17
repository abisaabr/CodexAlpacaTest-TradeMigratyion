# QQQ WVF Core-Parameter Scan

## What changed from the first pass

- The first pass held the Pine core inputs fixed and optimized the trading archetype around them.
- This pass keeps a small set of the strongest long/short archetypes from the first run and explicitly scans the indicator inputs `pd`, `bbl`, `lb`, `mult`, and `ph`.
- `pl` was held at `1.01` because in the pasted Pine it only affects the optional `rangeLow` display line and does not change the spike condition used for entries.
- Source data: `C:\Users\rabisaab\Downloads\QQQ_1min_20210308-20260308_sip (1).csv`.
- Total variants tested in this pass: `3456`.

## Best Long Core Setting

- `long_stable_60m_pd44_bbl20_lb20_mult1.5_ph0.9 | archetype long_stable_60m | 60m | pd 44 | bbl 20 | lb 20 | mult 1.50 | ph 0.90`.
- Full-history return `13.66%`, max drawdown `25.81%`, trades `395`.
- Last 1y `12.30%`, last 90d `9.68%`, YTD 2026 `10.66%`, stability score `584`.

## Best Short Core Setting

- `short_stable_15m_pd11_bbl30_lb20_mult2.5_ph0.8 | archetype short_stable_15m | 15m | pd 11 | bbl 30 | lb 20 | mult 2.50 | ph 0.80`.
- Full-history return `19.57%`, max drawdown `7.44%`, trades `456`.
- Last 1y `3.41%`, last 90d `3.99%`, YTD 2026 `3.25%`, stability score `832`.

## Output Files

- Full scan grid: `C:\Users\rabisaab\Downloads\data\qqq_wvf_core_params_grid.csv`
- Long leaderboard: `C:\Users\rabisaab\Downloads\data\qqq_wvf_core_params_top_long.csv`
- Short leaderboard: `C:\Users\rabisaab\Downloads\data\qqq_wvf_core_params_top_short.csv`
- Best long trades: `C:\Users\rabisaab\Downloads\data\qqq_wvf_core_params_best_long_trades.csv`
- Best short trades: `C:\Users\rabisaab\Downloads\data\qqq_wvf_core_params_best_short_trades.csv`
- Best long daily equity: `C:\Users\rabisaab\Downloads\data\qqq_wvf_core_params_best_long_daily_equity.csv`
- Best short daily equity: `C:\Users\rabisaab\Downloads\data\qqq_wvf_core_params_best_short_daily_equity.csv`
