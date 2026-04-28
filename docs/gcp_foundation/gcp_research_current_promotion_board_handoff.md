# Current Research Promotion Board Handoff

## Current State

- Control packet: `docs/gcp_foundation/gcp_research_current_promotion_board.md`
- Control JSON: `docs/gcp_foundation/gcp_research_current_promotion_board.json`
- State: `current_after_phase31`
- Active research Batch jobs: `none`
- Broker-facing status: `not_started`

## Canonical Candidate State

`AAPL` exit-360 is the only current bounded-validation candidate. It is not live-promoted and has not yet produced broker-audited paper evidence.

`NVDA` exit-300 looked promising in Phase28 but failed Phase30 governance stress, so it is research-only.

The `AMZN`/`AVGO`/`MSFT`/`MU` wide-lag cluster failed Phase31 economics and should not be replayed unchanged.

## Next Safe Research Step

Redirect compute to either:

- New candidate discovery outside the failed wide-lag cluster.
- Strategy redesign for cost/fill sensitivity.
- Loser-trade and severe-loser exclusion hardening.

Do not broaden broker-facing paper validation beyond the current AAPL candidate without a new governed packet.

## Next Safe Execution Step

Only if explicitly authorized: arm a bounded exclusive execution window and run the existing AAPL bounded validation process. Otherwise keep research non-broker-facing.

## Hard Rules

Do not trade, arm a window, start a broker-facing paper/live session, modify live manifests, change risk policy, or relax the `0.90` fill gate.
