# Phase28 Wide-Lag Candidate Recheck Handoff

## Current State

- State: `scheduled`
- Job: `phase28-widelag-recheck-20260428110100`
- Phase id: `phase28_widelag_candidate_recheck_20260428110100`
- Project/location: `codexalpaca/us-central1`
- Source runner archive: `gs://codexalpaca-control-us/research_source/codexalpaca_runner_source_95379e4166b4.zip`
- Control packet: `docs/gcp_foundation/gcp_research_phase28_widelag_candidate_recheck_status.md`
- Control JSON: `docs/gcp_foundation/gcp_research_phase28_widelag_candidate_recheck_status.json`

## Why This Is Running

Phase27 produced one bounded validation candidate, `AAPL` exit-360 baseline. Phase28 does not retest that candidate. Instead, it targets the remaining profitable but fill-blocked AAPL/NVDA candidates with explicitly wider and costlier lag profiles to decide whether any can join the research-review queue or should be killed/quarantined.

## Scope

- `AAPL` exit-210 wide-reward tight-liquidity candidate.
- `NVDA` exit-300 tight-reward tight-liquidity candidate.
- `NVDA` exit-360 tight-reward tight-liquidity candidate.

## Next Review Step

When the Batch job reaches `SUCCEEDED`, inspect:

- `portfolio_report/research_portfolio_report.json`
- `promotion_review_packet/research_promotion_review_packet.json`
- `logs/run.err.log`
- `logs/run.out.log`

If no candidate clears the `0.90` fill gate and positive holdout economics, record a kill/quarantine packet rather than rerunning the same profile family. If one or more candidates clear, create a bounded governed-validation review packet, still without changing live manifests or risk policy.

## Hard Rules

Do not trade, arm a window, start a broker-facing paper/live session, modify live manifests, change risk policy, or relax the `0.90` fill gate.
