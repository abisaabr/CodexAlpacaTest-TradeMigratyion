# Current Research Promotion Board Handoff

## Current State

- Control packet: `docs/gcp_foundation/gcp_research_current_promotion_board.md`
- Control JSON: `docs/gcp_foundation/gcp_research_current_promotion_board.json`
- State: `phase42_dense_download_replay_complete_promotion_blocked_exit_policy_redesign_required`
- Active research Batch jobs: `none` from this monitor
- Broker-facing status: `not_started`
- Latest Phase42 rollup: `gs://codexalpaca-control-us/research_results/top100_liquidity_research_20260426/rollups/phase42_dense_download_replay_20260428232000/output/`

## Canonical Candidate State

`AAPL` exit-360 remains the only current bounded-validation candidate. It is not live-promoted and has not produced broker-audited paper evidence in this lane.

Phase42 scanned `183` candidates across ten dense top-liquid symbols and found `0` eligible for governed promotion review. The result is `research_only_blocked`.

The fill-foundation repair worked:

- Phase40 active+inactive contract inventory reached `17/17` requested weekday coverage for all ten symbols.
- Phase41 dense selected-contract coverage reached `16/17` selected weekdays (`0.941176`).
- Phase42 then downloaded/replayed option bars and trades against that repaired foundation.

The remaining blocker is strategy design/execution timing, not missing selected-contract inventory. Phase42 blocker counts are `{'fill_coverage_below_0.90': 183, 'min_net_pnl_not_positive': 17, 'option_trades_below_20': 120, 'test_net_pnl_not_above_0': 89}`, and all `183` candidates were classified as `exit_bar_gap_or_exit_policy_mismatch`.

## Next Safe Research Step

Run research-only exit-policy redesign/repair against the highest-positive Phase42 candidates. Use the dense top-10 data to test exits that can actually find bars under realistic lag/cost assumptions. In parallel, build the stock/ETF fallback portfolio lane so the project can pursue daily PnL while option candidates continue to require the `0.90` fill gate.

Do not promote from individual shard packets or from the Phase42 research-only capital plan.

## Next Safe Execution Step

Only if explicitly authorized: arm a bounded exclusive execution window and run the existing AAPL bounded validation process. Otherwise keep research non-broker-facing.

## Hard Rules

Do not trade, arm a window, start a broker-facing paper/live session, modify live manifests, change risk policy, or relax the `0.90` fill gate.
