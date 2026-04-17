# Recent Options Shadow Comparison

- Dates used: `2026-04-01, 2026-04-02, 2026-04-03`
- Underlying total pnl: `$273.52` across `2` signals.
- Single-leg option shadow pnl: `$227.00` across `2` valid shadows.
- Debit-spread shadow pnl: `$0.00` across `2` valid shadows.
- Over these replay dates, options hurt or failed to beat the underlying on the resolved subset.
- Single legs looked cleaner on the small resolved sample.
- Quote-based spread and midpoint trust is still missing because the historical options-quote endpoint remained unavailable.
- Options should remain shadow-only for now.
- This is good enough to justify continuing options shadow capture next week, provided unresolved trades remain explicitly unresolved.
