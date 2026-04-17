# QQQ FVG Frozen Winners

These base strategies are frozen as the current winners and should not be changed by later sweeps. New studies may only layer filters or wrappers on top of them.

## Winner A

- ID: `dominant_count_10m_always_on`
- Variant: `active_dominant_count_session_reset`
- Timeframe: `10m`
- Entry mode: `always_on_active`
- Stop loss: `1.25%`
- Take profit: `3.50%`
- Cost assumption used to freeze: `2.0 bps` per side

## Winner B

- ID: `uncontested_15m_hybrid`
- Variant: `active_uncontested_session_reset`
- Timeframe: `15m`
- Entry mode: `hybrid_reentry_once`
- Stop loss: `0.50%`
- Take profit: `4.25%`
- Cost assumption used to freeze: `2.0 bps` per side

## Rule

- Future optimization work should treat these as the base engines.
- Any further search should be done through overlays such as filters, timing rules, or execution wrappers.
