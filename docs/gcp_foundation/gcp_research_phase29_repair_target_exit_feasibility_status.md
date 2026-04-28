# Phase29 Repair-Target Exit Feasibility Status

## State

- State: `scheduled`
- Batch job: `phase29-repair-exit-feas-20260428110900`
- Batch location: `codexalpaca/us-central1`
- Phase id: `phase29_repair_target_exit_feasibility_20260428110900`
- Broker-facing: `false`
- Live manifest effect: `none`
- Risk policy effect: `none`
- Exclusive-window effect: `none`

## Objective

Phase29 is a parallel, non-broker-facing exit-lag feasibility diagnostic for the remaining positive-but-blocked Phase22 repair targets:

- `AMZN` exit-360 wide-reward baseline and tight-liquidity candidates.
- `AVGO` exit-300 wide-reward baseline candidate.
- `AVGO` exit-360 tight-reward baseline candidate.
- `MSFT` exit-360 wide-reward baseline candidate.
- `MU` exit-300 balanced-reward tight-liquidity candidate.
- `MU` exit-360 tight-reward tight-liquidity candidate.

This phase does not run promotion economics. It classifies whether these candidates have feasible option exits across 10, 30, 60, 90, 120, 180, and 240 minute exit windows before heavier replay compute is spent.

## Artifact Roots

- Launch root: `gs://codexalpaca-control-us/research_results/top100_liquidity_research_20260426/portfolio_event_driven_data/phase29_repair_target_exit_feasibility_20260428110900/launch/`
- Result root: `gs://codexalpaca-control-us/research_results/top100_liquidity_research_20260426/portfolio_event_driven_data/phase29_repair_target_exit_feasibility_20260428110900/`

## Parallel Context

Phase28 remains active for the AAPL/NVDA profitable fill-blocked candidates. Phase29 is intentionally non-overlapping and diagnostic-only.

## Operator Guardrails

Do not trade, arm an exclusive window, start a broker-facing paper/live session, modify live manifests, change risk policy, or relax the `0.90` fill gate from this packet.
