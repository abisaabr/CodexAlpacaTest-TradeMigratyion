# AAPL Candidate Governance Review Handoff

## Current State

- Candidate: `AAPL` `b150__aapl__long_call__wide_reward__exit_360__liq_baseline`
- State: `research_review_open_pending_phase27_adversarial_stress`
- Broker-facing status: `not_broker_facing`
- Live manifest effect: `none`
- Risk policy effect: `none`
- Current control-plane packet: `docs/gcp_foundation/gcp_research_aapl_candidate_governance_review_packet.md`
- Current control-plane JSON: `docs/gcp_foundation/gcp_research_aapl_candidate_governance_review_packet.json`

## Why This Candidate Matters

Phase26 found one candidate that cleared the current research-review gates under the wide-lag exit-policy diagnostic. The candidate had positive minimum net economics, positive holdout/test economics, and fill coverage above the `0.90` gate across the Phase26 profile set.

## Why It Is Not Activated

This is still research evidence, not broker-audited execution evidence. It has not run inside the sanctioned VM paper session, has not produced broker order/activity reconciliation, and has not produced loser-trade classification from live paper fills.

Do not change live manifests, live strategy selection, or risk policy from this packet.

## Active Phase27 Job

- Job: `phase27-aapl-governance-stress-20260428141000`
- Initial state: `SCHEDULED`
- Phase id: `phase27_aapl_governance_stress_20260428141000`
- Result root: `gs://codexalpaca-control-us/research_results/top100_liquidity_research_20260426/portfolio_event_driven_data/phase27_aapl_governance_stress_20260428141000/`
- Launch packet: `gs://codexalpaca-control-us/research_results/top100_liquidity_research_20260426/portfolio_event_driven_data/phase27_aapl_governance_stress_20260428141000/launch/`

## Next Operator Action

Monitor Phase27. If it succeeds, inspect:

- promotion review packet
- portfolio report
- minimum fill coverage
- minimum holdout/test net PnL
- worst drawdown
- severe loser clusters or cost sensitivity

If Phase27 stays clean, the next governance step is to classify the AAPL candidate as a possible `governed_validation` paper-session candidate. That still does not authorize live trading or manifest changes; it only prepares a bounded paper validation discussion.
