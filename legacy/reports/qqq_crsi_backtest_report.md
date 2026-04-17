# QQQ cRSI Backtest Report

This sweep optimized how the fuchsia `cRSI` line should be compared to the aqua dynamic bands on regular-hours QQQ data.

| Timeframe | Winning family | Domcycle | Leveling | Entry buffer | Exit ratio | Return | Max DD | Sharpe | PF | Trades | Typical long trigger | Typical short trigger |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| 1m | mean_reversion | 40 | 5.0 | 4.0 | 1.0 | -87.94% | 88.82% | -3.13 | 0.75 | 5264 | buy `34.47` / sell `62.70` | short `66.70` / cover `38.47` |
| 2m | breakout | 40 | 5.0 | 4.0 | 1.0 | -48.23% | 53.61% | -0.94 | 0.89 | 2663 | buy `67.04` / sell `38.45` | short `34.45` / cover `63.04` |
| 5m | breakout | 40 | 5.0 | 4.0 | 1.0 | 9.87% | 22.91% | 0.22 | 1.04 | 1117 | buy `68.04` / sell `38.28` | short `34.28` / cover `64.04` |
| 15m | breakout | 40 | 15.0 | 4.0 | 1.0 | 25.36% | 14.62% | 0.58 | 1.15 | 636 | buy `65.39` / sell `42.19` | short `38.19` / cover `61.39` |
| 30m | breakout | 30 | 5.0 | 4.0 | 0.5 | 29.23% | 7.35% | 1.09 | 1.49 | 286 | buy `71.41` / sell `51.80` | short `32.20` / cover `51.80` |
| 60m | breakout | 10 | 10.0 | 2.0 | 0.5 | 21.65% | 8.45% | 0.70 | 1.22 | 505 | buy `73.55` / sell `52.85` | short `32.14` / cover `52.85` |

## Readout

- Best winning timeframe in this sweep: `30m` with the `breakout` interpretation.
- Typical winning long rule on that timeframe: compare the fuchsia line to the aqua band trigger at about `71.41` and exit near `51.80`.
- Typical winning short rule on that timeframe: short around `32.20` and cover near `51.80`.
- `leveling` changes the aqua bands themselves. Lower values make the bands more extreme, higher values pull them closer to the middle.
- `entry_buffer` is an extra offset beyond the aqua band. `0.0` means trade exactly at the band; `2.0` means wait for cRSI to move 2 points farther.
- `exit_ratio` controls where inside the channel the position exits. `0.0` exits when cRSI re-crosses the entry-side aqua band, `0.5` exits near the middle, and `1.0` exits at the opposite aqua band.
