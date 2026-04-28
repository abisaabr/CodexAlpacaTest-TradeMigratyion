# Phase30 NVDA Governance Stress Handoff

## Current State

- State: `queued`
- Job: `phase30-nvda-governance-20260428112200`
- Phase id: `phase30_nvda_governance_stress_20260428112200`
- Project/location: `codexalpaca/us-central1`
- Source runner archive: `gs://codexalpaca-control-us/research_source/codexalpaca_runner_source_95379e4166b4.zip`
- Control packet: `docs/gcp_foundation/gcp_research_phase30_nvda_governance_stress_status.md`
- Control JSON: `docs/gcp_foundation/gcp_research_phase30_nvda_governance_stress_status.json`

## Why This Is Running

Phase28 found one new non-broker-facing research-review candidate: `NVDA` exit-300 tight-reward tight-liquidity. Phase30 applies isolated, harsher governance stress before the candidate can be discussed for any bounded paper validation packet.

## Next Review Step

When the Batch job reaches `SUCCEEDED`, inspect:

- `portfolio_report/research_portfolio_report.json`
- `promotion_review_packet/research_promotion_review_packet.json`
- `logs/run.err.log`
- `logs/run.out.log`

If the candidate clears all profiles with fill coverage at least `0.90` and positive holdout/test economics, create an NVDA governed-validation review packet. If not, keep it research-only and record the blocker.

## Hard Rules

Do not trade, arm a window, start a broker-facing paper/live session, modify live manifests, change risk policy, or relax the `0.90` fill gate.
