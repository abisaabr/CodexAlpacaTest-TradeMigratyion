# Phase30 NVDA Governance Stress Status

## State

- State: `succeeded`
- Batch job: `phase30-nvda-governance-20260428112200`
- Batch location: `codexalpaca/us-central1`
- Phase id: `phase30_nvda_governance_stress_20260428112200`
- Broker-facing: `false`
- Live manifest effect: `none`
- Risk policy effect: `none`
- Exclusive-window effect: `none`

## Objective

Phase30 isolates the Phase28 NVDA review candidate:

- `NVDA` `b150__nvda__long_call__tight_reward__exit_300__liq_tight`

This is a governance-stress replay with harsher lag, slippage, and fee profiles before any bounded-validation packet is considered.

## Source Evidence

- Phase28 decision: `ready_for_governed_validation_review`
- Phase28 minimum net PnL: `$1593.1625`
- Phase28 minimum holdout/test net PnL: `$484.1825`
- Phase28 fill coverage: `0.9254-0.9701`

## Result

- Decision: `research_only_blocked`
- Candidate count: `1`
- Eligible for review: `0`
- Blocker: `min_net_pnl_not_positive`
- Minimum net PnL: `$-782.9625`
- Minimum holdout/test net PnL: `$393.2`
- Fill coverage: `0.9254-0.9701`
- Minimum option trades: `62`
- Worst drawdown: `$-6083.3875`

The NVDA exit-300 candidate is not a bounded-validation candidate after Phase30. It is a cost-sensitive research lead only.

## Artifact Roots

- Launch root: `gs://codexalpaca-control-us/research_results/top100_liquidity_research_20260426/portfolio_event_driven_data/phase30_nvda_governance_stress_20260428112200/launch/`
- Result root: `gs://codexalpaca-control-us/research_results/top100_liquidity_research_20260426/portfolio_event_driven_data/phase30_nvda_governance_stress_20260428112200/`

## Operator Guardrails

Do not trade, arm an exclusive window, start a broker-facing paper/live session, modify live manifests, change risk policy, or relax the `0.90` fill gate from this packet.
