# Options Combo Target Analysis

Generated: 2026-04-06T12:20:58.863720-04:00
Target average daily PnL: `200.00`

## Candidate Setups
- `options_recent_otm_focus | SPY | failed_breakout_mean_reversion_option_buyer_otm_focus | otm_1` | pnl/day `56.54` | expectancy `16.37` | max drawdown `-161.30` | positive-day ratio `63.64%`
- `options_recent_otm_focus | QQQ | failed_breakout_mean_reversion_option_buyer_otm_focus | otm_1` | pnl/day `28.91` | expectancy `6.24` | max drawdown `-227.98` | positive-day ratio `63.64%`
- `options_optimization | SPY | failed_breakout_mean_reversion_option_buyer | atm` | pnl/day `24.82` | expectancy `5.62` | max drawdown `-218.59` | positive-day ratio `54.17%`
- `options_optimization | QQQ | failed_breakout_mean_reversion_option_buyer | atm` | pnl/day `10.64` | expectancy `2.09` | max drawdown `-335.52` | positive-day ratio `62.50%`

## Top Raw Combinations
- `options_recent_otm_focus | SPY | failed_breakout_mean_reversion_option_buyer_otm_focus | otm_1 || options_recent_otm_focus | QQQ | failed_breakout_mean_reversion_option_buyer_otm_focus | otm_1 || options_optimization | SPY | failed_breakout_mean_reversion_option_buyer | atm` | avg/day `63.99` | drawdown `-434.55` | positive-day ratio `62.50%` | scale-to-target ``4``
- `options_recent_otm_focus | SPY | failed_breakout_mean_reversion_option_buyer_otm_focus | otm_1 || options_optimization | SPY | failed_breakout_mean_reversion_option_buyer | atm || options_optimization | QQQ | failed_breakout_mean_reversion_option_buyer | atm` | avg/day `61.37` | drawdown `-324.31` | positive-day ratio `62.50%` | scale-to-target ``4``
- `options_recent_otm_focus | SPY | failed_breakout_mean_reversion_option_buyer_otm_focus | otm_1 || options_optimization | SPY | failed_breakout_mean_reversion_option_buyer | atm` | avg/day `50.73` | drawdown `-245.41` | positive-day ratio `54.17%` | scale-to-target ``4``
- `options_recent_otm_focus | SPY | failed_breakout_mean_reversion_option_buyer_otm_focus | otm_1 || options_recent_otm_focus | QQQ | failed_breakout_mean_reversion_option_buyer_otm_focus | otm_1 || options_optimization | QQQ | failed_breakout_mean_reversion_option_buyer | atm` | avg/day `49.80` | drawdown `-379.26` | positive-day ratio `62.50%` | scale-to-target ``5``
- `options_recent_otm_focus | QQQ | failed_breakout_mean_reversion_option_buyer_otm_focus | otm_1 || options_optimization | SPY | failed_breakout_mean_reversion_option_buyer | atm || options_optimization | QQQ | failed_breakout_mean_reversion_option_buyer | atm` | avg/day `48.71` | drawdown `-402.23` | positive-day ratio `58.33%` | scale-to-target ``5``
- `options_recent_otm_focus | SPY | failed_breakout_mean_reversion_option_buyer_otm_focus | otm_1 || options_recent_otm_focus | QQQ | failed_breakout_mean_reversion_option_buyer_otm_focus | otm_1` | avg/day `39.16` | drawdown `-300.36` | positive-day ratio `33.33%` | scale-to-target ``6``
- `options_recent_otm_focus | QQQ | failed_breakout_mean_reversion_option_buyer_otm_focus | otm_1 || options_optimization | SPY | failed_breakout_mean_reversion_option_buyer | atm` | avg/day `38.07` | drawdown `-323.33` | positive-day ratio `54.17%` | scale-to-target ``6``
- `options_recent_otm_focus | SPY | failed_breakout_mean_reversion_option_buyer_otm_focus | otm_1 || options_optimization | QQQ | failed_breakout_mean_reversion_option_buyer | atm` | avg/day `36.55` | drawdown `-237.65` | positive-day ratio `66.67%` | scale-to-target ``6``
- `options_optimization | SPY | failed_breakout_mean_reversion_option_buyer | atm || options_optimization | QQQ | failed_breakout_mean_reversion_option_buyer | atm` | avg/day `35.46` | drawdown `-295.47` | positive-day ratio `58.33%` | scale-to-target ``6``
- `options_recent_otm_focus | SPY | failed_breakout_mean_reversion_option_buyer_otm_focus | otm_1` | avg/day `25.91` | drawdown `-111.22` | positive-day ratio `29.17%` | scale-to-target ``8``

## Practical Read
- No 1x combo hit `200.00` average daily PnL. The best observed 1x combo averaged `63.99` per day.
- Reaching the target by simple scaling would need about `4x` size, which linearly projects drawdown toward `-1738.21` and the worst observed day toward `-1002.66`.

## Files
- Candidate setups CSV: `C:\Users\rabisaab\Downloads\reports\options_combo_target_20260406_122058\candidate_setups.csv`
- Combination leaderboard CSV: `C:\Users\rabisaab\Downloads\reports\options_combo_target_20260406_122058\combo_leaderboard.csv`
