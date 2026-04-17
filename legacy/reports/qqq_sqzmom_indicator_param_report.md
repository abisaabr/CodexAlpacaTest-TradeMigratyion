# QQQ SQZMOM Indicator Parameter Sweep

## Assumptions

- Market: QQQ 1-minute regular-session bars only.
- Trade rule baseline: buy on `red -> maroon` when `val > -0.02`, sell on `lime -> green` when `val > 1.5`.
- Histogram-only sweep keeps the original long-only rule and varies only `KC Length` because that is the only indicator input that changes `val`.
- Full squeeze-aware sweep adds an entry filter: the long entry is only allowed when `sqzOff` is true on the signal bar.
- Friction: `1.0` bp per side.

## Histogram-only `KC Length` sweep

- Best `KC Length`: `15`.
- Full-history return: `101.36%`.
- Last 1y return: `4.70%`.
- Last 90d return: `-2.98%`.
- YTD 2026 return: `-3.90%`.

## Full squeeze-aware grid, literal pasted code

- Best full-history row: BB Length `20`, BB Mult `2.0`, KC Length `10`, KC Mult `2.0`, Use TrueRange `False`.
- Full-history return: `74.19%`, max DD `9.62%`, last 1y `3.85%`, last 90d `-1.34%`, YTD 2026 `-1.17%`.
- Positive in all four windows: `6` rows.

## Full squeeze-aware grid, corrected BB multiplier

- Best full-history row: BB Length `20`, BB Mult `2.0`, KC Length `20`, KC Mult `1.0`, Use TrueRange `False`.
- Full-history return: `74.47%`, max DD `20.81%`, last 1y `4.65%`, last 90d `1.52%`, YTD 2026 `0.64%`.
- Positive in all four windows: `23` rows.

## Key read

- If the literal-code sweep shows identical performance across different `BB Mult` values, that confirms the pasted script is not actually using `BB MultFactor` in its current form.
- The corrected-BB run is included only to show what changes if that line is fixed to use the BB multiplier the way the original indicator is usually written.

## Output files

- Histogram-only KC sweep: `C:\Users\rabisaab\Downloads\data\qqq_sqzmom_histogram_kc_length_sweep.csv`
- Full squeeze-aware literal grid: `C:\Users\rabisaab\Downloads\data\qqq_sqzmom_squeeze_param_grid_literal.csv`
- Full squeeze-aware corrected-BB grid: `C:\Users\rabisaab\Downloads\data\qqq_sqzmom_squeeze_param_grid_corrected_bbmult.csv`
