# Phase31 Repair-Target Wide-Lag Economics Status

## State

- State: `succeeded`
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

## Result

- Decision: `research_only_blocked`
- Candidate count: `7`
- Eligible for promotion review: `0`
- Blockers: `fill_coverage_below_0.90=5`, `min_net_pnl_not_positive=2`, `test_net_pnl_not_above_0=3`

Notable results:

- `AMZN` exit-360 candidates had adequate fill coverage (`0.9333-0.9783`) but failed holdout/test PnL.
- `MU` candidates had positive net/test economics but severe fill shortfall (`0.4231-0.4538`).
- `AVGO` candidates had fill below the `0.90` gate and one negative minimum-net profile.
- `MSFT` failed economics and had fill instability.

The wide-lag repair-target cluster is not promotion-ready. Do not rerun this cluster without strategy redesign or a materially different data/contract-selection hypothesis.

## Operator Guardrails

Do not trade, arm an exclusive window, start a broker-facing paper/live session, modify live manifests, change risk policy, or relax the `0.90` fill gate from this packet.
