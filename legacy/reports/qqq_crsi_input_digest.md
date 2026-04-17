# QQQ cRSI Backtest Input Digest

- Source file: `C:\Users\rabisaab\Downloads\QQQ_1min_20210308-20260308_sip (1).csv`
- Regular-hours one-minute bars after filtering: `485,550`.
- Full regular-hours sessions kept: `1245` days with exactly `390` bars.
- Raw file session size range before filtering: min `512`, median `852`, max `960` bars/day.
- Session window used for backtests: `09:30` to `15:59` America/New_York, no overnight holdings.
- Trading cost assumption: `2.0` bps per side.
- cRSI implementation assumption: `vibration=10`, `phasingLag=4` using truncated indexing from the Pine script's `(vibration - 1) / 2` expression.
- Parameter sweep: domcycle `(10, 14, 20, 30, 40)`, leveling `(5.0, 10.0, 15.0, 20.0)`, entry buffer `(0.0, 2.0, 4.0)`, exit ratio `(0.0, 0.5, 1.0)`, families `('mean_reversion', 'breakout')`.
