# Options Combo Target Analysis

Generated: 2026-04-06T12:20:42.603740-04:00
Target average daily PnL: `200.00`

## Candidate Setups
- `options_optimization | SPY | failed_breakout_mean_reversion_option_buyer | atm` | pnl/day `24.82` | expectancy `5.62` | max drawdown `-218.59` | positive-day ratio `54.17%`
- `options_optimization | QQQ | failed_breakout_mean_reversion_option_buyer | atm` | pnl/day `10.64` | expectancy `2.09` | max drawdown `-335.52` | positive-day ratio `62.50%`

## Top Raw Combinations
- `options_optimization | SPY | failed_breakout_mean_reversion_option_buyer | atm || options_optimization | QQQ | failed_breakout_mean_reversion_option_buyer | atm` | avg/day `35.46` | drawdown `-295.47` | positive-day ratio `58.33%` | scale-to-target ``6``
- `options_optimization | SPY | failed_breakout_mean_reversion_option_buyer | atm` | avg/day `24.82` | drawdown `-144.91` | positive-day ratio `54.17%` | scale-to-target ``9``
- `options_optimization | QQQ | failed_breakout_mean_reversion_option_buyer | atm` | avg/day `10.64` | drawdown `-268.07` | positive-day ratio `62.50%` | scale-to-target ``19``

## Practical Read
- No 1x combo hit `200.00` average daily PnL. The best observed 1x combo averaged `35.46` per day.
- Reaching the target by simple scaling would need about `6x` size, which linearly projects drawdown toward `-1772.84` and the worst observed day toward `-1630.26`.

## Files
- Candidate setups CSV: `C:\Users\rabisaab\Downloads\reports\options_combo_target_20260406_122042\candidate_setups.csv`
- Combination leaderboard CSV: `C:\Users\rabisaab\Downloads\reports\options_combo_target_20260406_122042\combo_leaderboard.csv`
