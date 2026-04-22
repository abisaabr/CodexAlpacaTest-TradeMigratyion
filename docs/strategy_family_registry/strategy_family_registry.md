# Strategy Family Registry

## Snapshot

- Generated at: `2026-04-22T10:04:03.951944-04:00`
- Ready tickers: 140
- Cataloged families: 16
- Cataloged base strategies: 92
- Research ticker summaries found: 107
- Unique researched tickers: 50

## Live Manifest Overlay

- Manifest path: `C:\Users\rabisaab\OneDrive\CodexAlpaca\downloads_remaining_20260417\folders\codexalpaca_repo\config\strategy_manifests\multi_ticker_portfolio_live.yaml`
- Live strategies: 94
- Live underlyings: 21
- Live families:
  - `Single-leg long call`: 48
  - `Single-leg long put`: 42
  - `Call backspread`: 2
  - `Iron butterfly`: 2

## Priority Families

- `Broken-wing call butterfly`: `priority_discovery`; live strategies `0`; selected bases `0`; ready gap `140`
- `Broken-wing put butterfly`: `priority_discovery`; live strategies `0`; selected bases `0`; ready gap `140`
- `Call butterfly`: `priority_discovery`; live strategies `0`; selected bases `0`; ready gap `140`
- `Debit call spread`: `priority_discovery`; live strategies `0`; selected bases `0`; ready gap `140`
- `Debit put spread`: `priority_discovery`; live strategies `0`; selected bases `0`; ready gap `140`
- `Credit call spread`: `priority_validation`; live strategies `0`; selected bases `1`; ready gap `139`
- `Iron condor`: `priority_validation`; live strategies `0`; selected bases `1`; ready gap `139`
- `Long strangle`: `priority_validation`; live strategies `0`; selected bases `1`; ready gap `139`
- `Credit put spread`: `priority_validation`; live strategies `0`; selected bases `2`; ready gap `138`
- `Put butterfly`: `priority_validation`; live strategies `0`; selected bases `2`; ready gap `138`
- `Put backspread`: `promotion_follow_up`; live strategies `0`; selected bases `4`; ready gap `134`
- `Long straddle`: `promotion_follow_up`; live strategies `0`; selected bases `4`; ready gap `133`

## Registry

### Broken-wing call butterfly

- Bucket: `broken_wing_butterfly`; bias: `bull_or_choppy`; leg range: `4-4`
- Priority: `priority_discovery`; steward action: `collect_and_rank_new_family_candidates`
- Base strategies: 3; selected `0`; promoted `0`
- Selected tickers: 0; promoted tickers: 0; ready gap: 140
- Live overlay: strategies `0` across `0` tickers
- Strategy sets: `down_choppy_exhaustive`, `family_expansion`
- Signals: `trend_call`
- DTE modes: `next_expiry`
- Note: Broken-wing call butterfly is still structurally under-tested across the ready universe and should stay in discovery rotation.

### Broken-wing put butterfly

- Bucket: `broken_wing_butterfly`; bias: `bear_or_choppy`; leg range: `4-4`
- Priority: `priority_discovery`; steward action: `collect_and_rank_new_family_candidates`
- Base strategies: 3; selected `0`; promoted `0`
- Selected tickers: 0; promoted tickers: 0; ready gap: 140
- Live overlay: strategies `0` across `0` tickers
- Strategy sets: `down_choppy_exhaustive`, `down_choppy_only`, `family_expansion`
- Signals: `trend_put`
- DTE modes: `next_expiry`
- Note: Broken-wing put butterfly is still structurally under-tested across the ready universe and should stay in discovery rotation.

### Call backspread

- Bucket: `backspread`; bias: `bull_convexity`; leg range: `3-3`
- Priority: `live_benchmark`; steward action: `benchmark_against_current_live_book`
- Base strategies: 2; selected `2`; promoted `2`
- Selected tickers: 1; promoted tickers: 1; ready gap: 139
- Live overlay: strategies `2` across `1` tickers
- Strategy sets: `family_expansion`
- Signals: `trend_call`
- DTE modes: `next_expiry`
- Note: Call backspread is already live and should be benchmarked for replacement or diversification, not re-added blindly.

### Call butterfly

- Bucket: `butterfly`; bias: `bull_or_choppy`; leg range: `4-4`
- Priority: `priority_discovery`; steward action: `collect_and_rank_new_family_candidates`
- Base strategies: 4; selected `0`; promoted `0`
- Selected tickers: 0; promoted tickers: 0; ready gap: 140
- Live overlay: strategies `0` across `0` tickers
- Strategy sets: `down_choppy_exhaustive`, `down_choppy_only`, `family_expansion`
- Signals: `iron_condor`
- DTE modes: `same_day`
- Note: Call butterfly is still structurally under-tested across the ready universe and should stay in discovery rotation.

### Credit call spread

- Bucket: `credit_spread`; bias: `bear`; leg range: `2-2`
- Priority: `priority_validation`; steward action: `push_family_into_exhaustive_validation`
- Base strategies: 13; selected `1`; promoted `0`
- Selected tickers: 1; promoted tickers: 0; ready gap: 139
- Live overlay: strategies `0` across `0` tickers
- Strategy sets: `down_choppy_exhaustive`, `down_choppy_only`, `family_expansion`, `standard`
- Signals: `credit_bear`
- DTE modes: `next_expiry`, `same_day`
- Note: Credit call spread has produced selections but no approved live sleeves yet, so it belongs in exhaustive validation.

### Credit put spread

- Bucket: `credit_spread`; bias: `bull`; leg range: `2-2`
- Priority: `priority_validation`; steward action: `push_family_into_exhaustive_validation`
- Base strategies: 5; selected `2`; promoted `0`
- Selected tickers: 2; promoted tickers: 0; ready gap: 138
- Live overlay: strategies `0` across `0` tickers
- Strategy sets: `family_expansion`, `standard`
- Signals: `credit_bull`
- DTE modes: `next_expiry`, `same_day`
- Note: Credit put spread has produced selections but no approved live sleeves yet, so it belongs in exhaustive validation.

### Debit call spread

- Bucket: `debit_spread`; bias: `bull`; leg range: `2-2`
- Priority: `priority_discovery`; steward action: `collect_and_rank_new_family_candidates`
- Base strategies: 3; selected `0`; promoted `0`
- Selected tickers: 0; promoted tickers: 0; ready gap: 140
- Live overlay: strategies `0` across `0` tickers
- Strategy sets: `family_expansion`, `standard`
- Signals: `trend_call`
- DTE modes: `next_expiry`
- Note: Debit call spread is still structurally under-tested across the ready universe and should stay in discovery rotation.

### Debit put spread

- Bucket: `debit_spread`; bias: `bear`; leg range: `2-2`
- Priority: `priority_discovery`; steward action: `collect_and_rank_new_family_candidates`
- Base strategies: 7; selected `0`; promoted `0`
- Selected tickers: 0; promoted tickers: 0; ready gap: 140
- Live overlay: strategies `0` across `0` tickers
- Strategy sets: `down_choppy_exhaustive`, `down_choppy_only`, `family_expansion`, `standard`
- Signals: `trend_put`
- DTE modes: `next_expiry`
- Note: Debit put spread is still structurally under-tested across the ready universe and should stay in discovery rotation.

### Iron butterfly

- Bucket: `neutral_premium`; bias: `choppy`; leg range: `4-4`
- Priority: `live_benchmark`; steward action: `benchmark_against_current_live_book`
- Base strategies: 3; selected `2`; promoted `2`
- Selected tickers: 5; promoted tickers: 5; ready gap: 135
- Live overlay: strategies `2` across `1` tickers
- Strategy sets: `down_choppy_exhaustive`, `down_choppy_only`, `family_expansion`, `standard`
- Signals: `iron_condor`
- DTE modes: `same_day`
- Note: Iron butterfly is already live and should be benchmarked for replacement or diversification, not re-added blindly.

### Iron condor

- Bucket: `neutral_premium`; bias: `choppy`; leg range: `4-4`
- Priority: `priority_validation`; steward action: `push_family_into_exhaustive_validation`
- Base strategies: 6; selected `1`; promoted `0`
- Selected tickers: 1; promoted tickers: 0; ready gap: 139
- Live overlay: strategies `0` across `0` tickers
- Strategy sets: `down_choppy_exhaustive`, `down_choppy_only`, `family_expansion`, `standard`
- Signals: `iron_condor`
- DTE modes: `same_day`
- Note: Iron condor has produced selections but no approved live sleeves yet, so it belongs in exhaustive validation.

### Long straddle

- Bucket: `long_vol`; bias: `choppy_or_expansion`; leg range: `2-2`
- Priority: `promotion_follow_up`; steward action: `review_for_live_manifest_addition`
- Base strategies: 5; selected `4`; promoted `2`
- Selected tickers: 7; promoted tickers: 1; ready gap: 133
- Live overlay: strategies `0` across `0` tickers
- Strategy sets: `down_choppy_exhaustive`, `down_choppy_only`, `family_expansion`, `standard`
- Signals: `long_straddle`
- DTE modes: `next_expiry`, `same_day`
- Note: Long straddle has some evidence already, but there is still room to widen symbol coverage before promotion.

### Long strangle

- Bucket: `long_vol`; bias: `choppy_or_expansion`; leg range: `2-2`
- Priority: `priority_validation`; steward action: `push_family_into_exhaustive_validation`
- Base strategies: 5; selected `1`; promoted `0`
- Selected tickers: 1; promoted tickers: 0; ready gap: 139
- Live overlay: strategies `0` across `0` tickers
- Strategy sets: `down_choppy_exhaustive`, `down_choppy_only`, `family_expansion`, `standard`
- Signals: `long_straddle`
- DTE modes: `next_expiry`, `same_day`
- Note: Long strangle has produced selections but no approved live sleeves yet, so it belongs in exhaustive validation.

### Put backspread

- Bucket: `backspread`; bias: `bear_convexity`; leg range: `3-3`
- Priority: `promotion_follow_up`; steward action: `review_for_live_manifest_addition`
- Base strategies: 5; selected `4`; promoted `4`
- Selected tickers: 6; promoted tickers: 6; ready gap: 134
- Live overlay: strategies `0` across `0` tickers
- Strategy sets: `down_choppy_exhaustive`, `down_choppy_only`, `family_expansion`
- Signals: `trend_put`
- DTE modes: `next_expiry`
- Note: Put backspread has some evidence already, but there is still room to widen symbol coverage before promotion.

### Put butterfly

- Bucket: `butterfly`; bias: `bear_or_choppy`; leg range: `4-4`
- Priority: `priority_validation`; steward action: `push_family_into_exhaustive_validation`
- Base strategies: 4; selected `2`; promoted `0`
- Selected tickers: 2; promoted tickers: 0; ready gap: 138
- Live overlay: strategies `0` across `0` tickers
- Strategy sets: `down_choppy_exhaustive`, `down_choppy_only`, `family_expansion`
- Signals: `iron_condor`
- DTE modes: `same_day`
- Note: Put butterfly has produced selections but no approved live sleeves yet, so it belongs in exhaustive validation.

### Single-leg long call

- Bucket: `single_leg`; bias: `bull`; leg range: `1-1`
- Priority: `live_benchmark`; steward action: `benchmark_against_current_live_book`
- Base strategies: 7; selected `5`; promoted `4`
- Selected tickers: 39; promoted tickers: 38; ready gap: 101
- Live overlay: strategies `48` across `21` tickers
- Strategy sets: `family_expansion`, `standard`
- Signals: `orb_call`, `trend_call`
- DTE modes: `next_expiry`, `same_day`
- Note: Single-leg long call is already live and should be benchmarked for replacement or diversification, not re-added blindly.

### Single-leg long put

- Bucket: `single_leg`; bias: `bear`; leg range: `1-1`
- Priority: `live_benchmark`; steward action: `benchmark_against_current_live_book`
- Base strategies: 17; selected `13`; promoted `11`
- Selected tickers: 47; promoted tickers: 44; ready gap: 93
- Live overlay: strategies `42` across `20` tickers
- Strategy sets: `down_choppy_exhaustive`, `down_choppy_only`, `family_expansion`, `standard`
- Signals: `orb_put`, `trend_put`
- DTE modes: `next_expiry`, `same_day`
- Note: Single-leg long put is already live and should be benchmarked for replacement or diversification, not re-added blindly.

