# Phase31 Repair-Target Wide-Lag Economics Status

## State

- State: `queued`
- Batch job: `phase31-widelag-econ-20260428112900`
- Batch location: `codexalpaca/us-central1`
- Phase id: `phase31_repair_target_widelag_economics_20260428112900`
- Broker-facing: `false`
- Live manifest effect: `none`
- Risk policy effect: `none`
- Exclusive-window effect: `none`

## Objective

Phase31 runs focused wide-lag economics for the seven Phase29 candidates across `AMZN`, `AVGO`, `MSFT`, and `MU`.

Phase29 showed these candidates are not full-stack fill feasible, but all can pass the `0.90` fill gate at 60-90 minute exit lags. Phase31 tests whether that wide-lag execution policy still has positive holdout economics under hardened costs.

## Artifact Roots

- Launch root: `gs://codexalpaca-control-us/research_results/top100_liquidity_research_20260426/portfolio_event_driven_data/phase31_repair_target_widelag_economics_20260428112900/launch/`
- Result root: `gs://codexalpaca-control-us/research_results/top100_liquidity_research_20260426/portfolio_event_driven_data/phase31_repair_target_widelag_economics_20260428112900/`

## Operator Guardrails

Do not trade, arm an exclusive window, start a broker-facing paper/live session, modify live manifests, change risk policy, or relax the `0.90` fill gate from this packet.
