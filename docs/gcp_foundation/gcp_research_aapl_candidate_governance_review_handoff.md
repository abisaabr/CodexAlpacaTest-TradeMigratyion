# AAPL Candidate Governance Review Handoff

## Current State

- Candidate: `AAPL` `b150__aapl__long_call__wide_reward__exit_360__liq_baseline`
- State: `research_review_ready_for_governance_decision`
- Broker-facing status: `not_broker_facing`
- Live manifest effect: `none`
- Risk policy effect: `none`
- Current control-plane packet: `docs/gcp_foundation/gcp_research_aapl_candidate_governance_review_packet.md`
- Current control-plane JSON: `docs/gcp_foundation/gcp_research_aapl_candidate_governance_review_packet.json`
- Bounded validation plan: `docs/gcp_foundation/gcp_research_aapl_bounded_paper_validation_plan.md`
- Non-live manifest candidate: `docs/gcp_foundation/gcp_research_aapl_bounded_validation_manifest_candidate.yaml`
- Runner-compatible runtime config: `docs/gcp_foundation/gcp_research_aapl_bounded_validation_runtime_config.yaml`
- Latest startup preflight: `docs/gcp_foundation/gcp_research_aapl_bounded_validation_preflight_status.md`
- Operator checklist: `docs/gcp_foundation/gcp_research_aapl_bounded_validation_operator_checklist.md`

## Why This Candidate Matters

Phase26 found one candidate that cleared the current research-review gates under the wide-lag exit-policy diagnostic. The candidate had positive minimum net economics, positive holdout/test economics, and fill coverage above the `0.90` gate across the Phase26 profile set.

## Why It Is Not Activated

This is still research evidence, not broker-audited execution evidence. It has not run inside the sanctioned VM paper session, has not produced broker order/activity reconciliation, and has not produced loser-trade classification from live paper fills.

Do not change live manifests, live strategy selection, or risk policy from this packet.

## Phase27 Result

- Job: `phase27-aapl-governance-stress-20260428141000`
- State: `SUCCEEDED`
- Phase id: `phase27_aapl_governance_stress_20260428141000`
- Result root: `gs://codexalpaca-control-us/research_results/top100_liquidity_research_20260426/portfolio_event_driven_data/phase27_aapl_governance_stress_20260428141000/`
- Launch packet: `gs://codexalpaca-control-us/research_results/top100_liquidity_research_20260426/portfolio_event_driven_data/phase27_aapl_governance_stress_20260428141000/launch/`
- Decision: `ready_for_governed_validation_review`
- Minimum net PnL: `$1715.93`
- Minimum holdout/test net PnL: `$341.155`
- Fill coverage: `0.9474-1.0`
- Minimum option trades: `36`
- Worst drawdown: `$-4167.955`
- Promotion blockers: `none`

## Next Operator Action

Classify the AAPL candidate against `docs/STRATEGY_PROMOTION_POLICY.md` as a possible `governed_validation` paper-session candidate. That still does not authorize live trading or manifest changes; it only prepares a bounded paper validation discussion.

Do not activate the strategy until an explicit governance packet says the candidate is allowed into a bounded paper validation run and an exclusive execution window is armed.

A bounded paper-validation plan, non-live governance manifest, runner-compatible runtime config, passed startup preflight, and operator checklist now exist. The next implementation step is not another research run for this candidate; it is an operator decision whether to arm an exclusive execution window for bounded broker-facing paper validation. Do not run broker-facing paper validation until an exclusive execution window is armed and explicitly authorized.
