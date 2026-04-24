# GCP Strategy Registry Bootstrap

## Snapshot

- Generated at: `2026-04-23T22:15:39.987919-04:00`
- Status: `ready_with_concentration_warning`
- Strategy count: `94`
- Single-leg strategy share: `95.7%`
- Manifest path: `C:\Users\abisa\Downloads\codexalpaca_repo\config\strategy_manifests\multi_ticker_portfolio_live.yaml`
- GCS prefix: `gs://codexalpaca-control-us/strategy_registry`

## Family Counts

- Call backspread: `2`
- Iron butterfly: `2`
- Single-leg long call: `48`
- Single-leg long put: `42`

## Strategy Class Counts

- Class A: liquid single-leg next-expiry directional: `82`
- Class B: same-day or opening-window single-leg: `8`
- Class C: defined-risk multi-leg debit structure: `2`
- Class D: complex choppy, premium, or convexity-sensitive: `2`

## Issues

- `warning` `single_leg_concentration`: Single-leg families represent 95.7% of manifest strategies.

## Research Guidance

- Use this registry as the identity layer for brute-force variants and promotion packets.
- Prioritize under-covered defined-risk and choppy/premium families before adding more single-leg variants.
- Keep generated variants out of the live manifest until they pass research promotion review.

## Registry Preview

- `qqq__reactive__call_backspread_next_expiry` QQQ Call backspread reactive bull
- `qqq__reactive__trend_long_call_next_expiry_d70` QQQ Single-leg long call reactive bull
- `qqq__reactive__call_backspread_next_expiry_aggressive` QQQ Call backspread reactive bull
- `qqq__reactive__trend_long_call_next_expiry` QQQ Single-leg long call reactive bull
- `qqq__base__orb_long_put_next_expiry` QQQ Single-leg long put base bear
- `qqq__slow__orb_long_put_next_expiry` QQQ Single-leg long put slow bear
- `qqq__patient__orb_long_put_next_expiry` QQQ Single-leg long put patient bear
- `qqq__patient__orb_long_put_same_day_d60` QQQ Single-leg long put patient bear
- `qqq__reactive__iron_butterfly_same_day` QQQ Iron butterfly reactive choppy
- `qqq__fast__iron_butterfly_same_day` QQQ Iron butterfly fast choppy
- `spy__slow__trend_long_call_next_expiry_d70` SPY Single-leg long call slow bull
- `spy__base__trend_long_call_next_expiry_d70` SPY Single-leg long call base bull
- `spy__fast__orb_long_put_next_expiry` SPY Single-leg long put fast bear
- `spy__base__orb_long_put_next_expiry` SPY Single-leg long put base bear
- `spy__slow__trend_long_put_next_expiry_d70` SPY Single-leg long put slow bear
- `iwm__fast__trend_long_call_next_expiry_d70` IWM Single-leg long call fast bull
- `iwm__fast__trend_long_call_next_expiry` IWM Single-leg long call fast bull
- `iwm__slow__trend_long_call_next_expiry_d70` IWM Single-leg long call slow bull
- `iwm__base__orb_long_put_next_expiry` IWM Single-leg long put base bear
- `iwm__fast__orb_long_put_next_expiry` IWM Single-leg long put fast bear
- `iwm__fast__trend_long_put_next_expiry_d70` IWM Single-leg long put fast bear
- `nvda__fast__trend_long_call_next_expiry_d70` NVDA Single-leg long call fast bull
- `nvda__base__trend_long_put_next_expiry` NVDA Single-leg long put base bear
- `tsla__base__trend_long_call_next_expiry_d70` TSLA Single-leg long call base bull
- `tsla__fast__trend_long_call_next_expiry_d70` TSLA Single-leg long call fast bull
