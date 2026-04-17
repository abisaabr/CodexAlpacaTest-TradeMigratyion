# QQQ FVG Layered Champions

These are the current recommended wrapper-enhanced versions of the frozen base engines. The underlying variant, timeframe, entry mode, stop loss, and take profit remain frozen. Only entry timing layers were added.

## Champion A

- Base engine: `dominant_count_10m_always_on`
- Variant: `active_dominant_count_session_reset`
- Timeframe: `10m`
- Entry mode: `always_on_active`
- Stop loss: `1.25%`
- Take profit: `3.50%`
- Entry layer: `start_00_cutoff_none_block_lunch_1130_1300`
- Interpretation: allow entries all day except block new entries from `11:30` to `13:00` ET
- Cost assumption: `2.0 bps` per side
- Verified result: `+116.84%` total return, `16.96%` CAGR, `14.53%` max drawdown, `1.15` Sharpe

## Champion B

- Base engine: `uncontested_15m_hybrid`
- Variant: `active_uncontested_session_reset`
- Timeframe: `15m`
- Entry mode: `hybrid_reentry_once`
- Stop loss: `0.50%`
- Take profit: `4.25%`
- Entry layer: `start_00_cutoff_1445_block_lunch_1130_1300`
- Interpretation: allow entries from the open through `14:45` ET, but block new entries from `11:30` to `13:00` ET
- Cost assumption: `2.0 bps` per side
- Verified result: `+53.02%` total return, `8.99%` CAGR, `8.30%` max drawdown, `0.88` Sharpe

## Notes

- Keep `qqq_fvg_frozen_winners.md` as the frozen base-engine record.
- Use this file when you want the current best wrapper-enhanced versions.
