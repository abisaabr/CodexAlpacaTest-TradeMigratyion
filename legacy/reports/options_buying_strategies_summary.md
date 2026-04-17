# Options Buying Strategies Summary

## Totals
- Total raw strategies found: 81
- Total included: 18
- Total excluded: 30

## Counts by Source
- Cboe: 2
- Fidelity: 25
- OIC: 48
- Schwab: 6

## Counts by Strategy Family
- backspread: 1
- butterfly: 4
- calendar: 1
- collar: 1
- combo: 1
- condor: 2
- diagonal: 2
- single_leg: 2
- straddle: 1
- strangle: 1
- vertical: 2

## Counts by Classification
- exclude: 30
- hybrid_or_protective: 2
- net_debit_spread: 12
- pure_long_premium: 4

## Duplicate / Alias Merges
- `bull call spread` <= Bull Call Spread; Bull Call Spread (Debit Call Spread)
- `collar` <= Collar; Collar (Protective Collar)
- `long butterfly` <= Long Butterfly Spread with Calls; Long Butterfly Spread with Puts; Long Call Butterfly; Long Put Butterfly
- `long calendar spread` <= Long Calendar Spread with Calls; Long Calendar Spread with Puts; Long Call Calendar Spread (Call Horizontal); Long Put Calendar Spread (Put Horizontal)
- `long call` <= Buying Index Calls; Long Call
- `long christmas tree spread` <= Long Christmas Tree Spread with Calls; Long Christmas Tree Spread with Puts
- `long christmas tree spread variation` <= Long Christmas Tree Spread Variation with Calls; Long Christmas Tree Spread Variation with Puts
- `long condor` <= Long Call Condor; Long Condor Spread with Calls; Long Condor Spread with Puts; Long Put Condor
- `long diagonal spread` <= Long Diagonal Spread with Calls; Long Diagonal Spread with Puts
- `long iron butterfly` <= Long Iron Butterfly; Long Iron Butterfly Spread
- `long iron condor` <= Long Condor; Long Iron Condor Spread
- `long put` <= Buying Index Puts; Long Put
- `long ratio backspread` <= 1x2 Ratio Volatility Spread with Calls; 1x2 Ratio Volatility Spread with Puts; Long Ratio Call Spread; Long Ratio Put Spread
- `long strangle` <= Long Strangle; Long Strangle (Long Combination)
- `protective put` <= Married Put; Protective Put; Protective Put (Married Put)

## Ambiguous Strategies Needing Manual Review
- `collar`: Hybrid stock-plus-options hedge with variable debit/credit economics, so keep separate from pure premium-buying definitions.
- `long calendar spread`: Merged call and put variants have different directional tilts and time-decay behavior away from the strike.
- `long diagonal spread`: Merged call and put variants have different directional tilts and can behave more like theta spreads than pure long-premium trades.
- `double diagonal spread`: Advanced theta-focused debit structure that some researchers may prefer to separate from simpler long-premium trades.
- `long butterfly`: Debit entry does not imply long-volatility; this family is typically neutral and short-volatility despite being included.
- `long condor`: Debit entry does not imply long-volatility; this family is typically neutral and short-volatility despite being included.
- `long ratio backspread`: These structures can be opened for either a debit or a credit, so the 'buying strategy' label is broader here than pure debit-only definitions.
- `long christmas tree spread`: Debit entry notwithstanding, this family is fundamentally a neutral short-volatility/theta structure rather than a pure long-vol trade.
- `long christmas tree spread variation`: Debit entry notwithstanding, this family is fundamentally a neutral short-volatility/theta structure rather than a pure long-vol trade.
- `long skip-strike butterfly`: Documented as a long butterfly-style structure, but the public source example was not clearly a debit-only buying strategy.
- `cash-backed call`: Bought-call acquire-stock variant, but its primary use case is stock acquisition rather than premium-buying exposure.

## Notes
- OIC live strategy pages were used as the primary full inventory and detail source.
- Schwab pages were added as accessible corroborating education articles.
- Cboe's public strategy-based margin page was used for margin-context cross-checking.
- Fidelity public strategy-guide URLs were recorded from search-indexed public pages because direct HTML requests were bot-protected in this environment.
- The catalog is best-effort and intentionally conservative; it should not be read as literally every options strategy online.
