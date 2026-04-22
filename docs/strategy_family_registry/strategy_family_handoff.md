# Strategy Family Handoff

## Snapshot

- Generated at: `2026-04-22T10:09:07.917839-04:00`
- Ready tickers: `140`
- Live strategies: `94` across `21` underlyings

## Immediate Focus

- Keep the live manifest stable unless a validated add/replace packet says otherwise.
- Use `priority_discovery` families for new broad waves.
- Use `priority_validation` families for exhaustive follow-up.
- Use `promotion_follow_up` families for manual live-book review, not automatic promotion.

## Priority Discovery

- `Debit put spread`: lane `collect_and_rank_new_family_candidates`, ready gap `140`, live strategies `0`
- `Call butterfly`: lane `collect_and_rank_new_family_candidates`, ready gap `140`, live strategies `0`
- `Broken-wing call butterfly`: lane `collect_and_rank_new_family_candidates`, ready gap `140`, live strategies `0`
- `Broken-wing put butterfly`: lane `collect_and_rank_new_family_candidates`, ready gap `140`, live strategies `0`
- `Debit call spread`: lane `collect_and_rank_new_family_candidates`, ready gap `140`, live strategies `0`

## Priority Validation

- `Credit call spread`: lane `push_family_into_exhaustive_validation`, ready gap `139`, live strategies `0`
- `Iron condor`: lane `push_family_into_exhaustive_validation`, ready gap `139`, live strategies `0`
- `Long strangle`: lane `push_family_into_exhaustive_validation`, ready gap `139`, live strategies `0`
- `Credit put spread`: lane `push_family_into_exhaustive_validation`, ready gap `138`, live strategies `0`
- `Put butterfly`: lane `push_family_into_exhaustive_validation`, ready gap `138`, live strategies `0`

## Promotion Follow-Up

- `Put backspread`: lane `review_for_live_manifest_addition`, ready gap `134`, live strategies `0`
- `Long straddle`: lane `review_for_live_manifest_addition`, ready gap `133`, live strategies `0`

## Live Benchmarks

- `Call backspread`: lane `benchmark_against_current_live_book`, ready gap `139`, live strategies `2`
- `Iron butterfly`: lane `benchmark_against_current_live_book`, ready gap `135`, live strategies `2`
- `Single-leg long call`: lane `benchmark_against_current_live_book`, ready gap `101`, live strategies `48`
- `Single-leg long put`: lane `benchmark_against_current_live_book`, ready gap `93`, live strategies `42`

## Suggested Next Tournaments

- `Opening 30-Minute Premium Defense`: Targets our biggest non-live premium-defense gaps in the opening session where execution control matters most.
  Families: `Debit put spread`
- `Opening 30-Minute Butterfly Lab`: Builds evidence in the most under-tested multi-leg structures without mixing them into directional lanes.
  Families: `Call butterfly`, `Broken-wing call butterfly`, `Broken-wing put butterfly`
- `Convexity And Long-Vol Follow-Up`: Pushes the best bear/choppy convexity families toward live-book review using exhaustive validation.
  Families: `Long strangle`, `Put backspread`, `Long straddle`

