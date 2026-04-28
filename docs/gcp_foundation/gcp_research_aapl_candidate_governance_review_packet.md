# AAPL Candidate Governance Review Packet

## Snapshot

- Packet id: `gcp_research_aapl_candidate_governance_review_20260428`
- State: `research_review_ready_for_governance_decision`
- Broker facing: `false`
- Live manifest effect: `none`
- Risk policy effect: `none`
- Promotion scope: `research_governed_validation_review_only`

## Candidate

- Symbol: `AAPL`
- Candidate variant: `b150__aapl__long_call__wide_reward__exit_360__liq_baseline`
- Source strategy: `aapl__broad150__trend_long_call_research`
- Strategy class: `Class A liquid single-leg directional`
- Directional option type: `call`
- Research-only allocation used by the Phase26 capital plan: `25%`
- Research-only dollars on a `$25,000` account: `$6,250`

## Evidence So Far

Phase26 opened this candidate for research/governed-validation review only:

- Phase26 job: `phase26-widelag-policy-20260428100000`
- Phase id: `phase26_widelag_exit_policy_20260428100000`
- Decision: `ready_for_governed_validation_review`
- Minimum net PnL across Phase26 profiles: `$1715.93`
- Minimum holdout/test net PnL: `$591.28`
- Fill coverage: `0.9474-1.0`
- Minimum option trades: `36`
- Worst drawdown: `$-3330.115`
- Promotion blockers in Phase26 packet: `none`

## Current Blockers

This candidate is not approved for paper-runner activation from research evidence alone.

- `not_broker_audited`
- `not_validated_in_sanctioned_vm_paper_session`
- `not_approved_for_live_manifest_or_risk_policy_change`

## Phase27 Confirmation Result

Phase27 completed the non-broker-facing confirmation step:

- Job: `phase27-aapl-governance-stress-20260428141000`
- State: `SUCCEEDED`
- Phase id: `phase27_aapl_governance_stress_20260428141000`
- Purpose: test the AAPL candidate under harsher slippage, fee, entry-lag, and exit-lag assumptions before any activation discussion.
- Result root: `gs://codexalpaca-control-us/research_results/top100_liquidity_research_20260426/portfolio_event_driven_data/phase27_aapl_governance_stress_20260428141000/`
- Decision: `ready_for_governed_validation_review`
- Minimum net PnL across Phase27 profiles: `$1715.93`
- Minimum holdout/test net PnL: `$341.155`
- Fill coverage: `0.9474-1.0`
- Minimum option trades: `36`
- Worst drawdown: `$-4167.955`
- Positive net profiles: `5/5`
- Positive holdout/test profiles: `5/5`
- Promotion blockers in Phase27 packet: `none`

## Required Next Evidence

- Governance review against `docs/STRATEGY_PROMOTION_POLICY.md`.
- Bounded broker-audited VM paper session only after explicit exclusive execution window.
- Broker order audit.
- Broker account activity audit.
- Ending broker-position snapshot.
- Shutdown reconciliation.
- Completed trade table with broker/local cashflow comparison.
- Loser-trade classification coverage.

## Decision Rule

Default to `hold` until a governance decision explicitly moves this candidate into a bounded paper validation plan and a later sanctioned VM paper session produces clean broker-audited evidence. Do not modify live manifests, live strategy selection, or risk policy from this packet alone.
