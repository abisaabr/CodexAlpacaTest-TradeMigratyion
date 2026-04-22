# Strategy Family Handoff

## Snapshot

- Generated at: `2026-04-22T15:54:34.769990-04:00`
- Ready tickers: `0`
- Live strategies: `94` across `21` underlyings

## Immediate Focus

- Keep the live manifest stable unless a validated add/replace packet says otherwise.
- Use `priority_discovery` families for new broad waves.
- Use `priority_validation` families for exhaustive follow-up.
- Use `promotion_follow_up` families for manual live-book review, not automatic promotion.

## Priority Discovery

- none

## Priority Validation

- `Credit call spread`: lane `push_family_into_exhaustive_validation`, ready gap `0`, live strategies `0`
- `Iron condor`: lane `push_family_into_exhaustive_validation`, ready gap `0`, live strategies `0`
- `Credit put spread`: lane `push_family_into_exhaustive_validation`, ready gap `0`, live strategies `0`
- `Long strangle`: lane `push_family_into_exhaustive_validation`, ready gap `0`, live strategies `0`
- `Put butterfly`: lane `push_family_into_exhaustive_validation`, ready gap `0`, live strategies `0`

## Promotion Follow-Up

- `Long straddle`: lane `review_for_live_manifest_addition`, ready gap `0`, live strategies `0`
- `Put backspread`: lane `review_for_live_manifest_addition`, ready gap `0`, live strategies `0`

## Live Benchmarks

- `Single-leg long put`: lane `benchmark_against_current_live_book`, ready gap `0`, live strategies `42`
- `Single-leg long call`: lane `benchmark_against_current_live_book`, ready gap `0`, live strategies `48`
- `Iron butterfly`: lane `benchmark_against_current_live_book`, ready gap `0`, live strategies `2`
- `Call backspread`: lane `benchmark_against_current_live_book`, ready gap `0`, live strategies `2`

## Suggested Next Tournaments

- `Convexity And Long-Vol Follow-Up`: Pushes the best bear/choppy convexity families toward live-book review using exhaustive validation.
  Families: `Long strangle`, `Long straddle`, `Put backspread`

