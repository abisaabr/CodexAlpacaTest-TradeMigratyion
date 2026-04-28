# Phase28 Wide-Lag Candidate Recheck Handoff

## Current State

- State: `succeeded`
- Job: `phase28-widelag-recheck-20260428110100`
- Phase id: `phase28_widelag_candidate_recheck_20260428110100`
- Project/location: `codexalpaca/us-central1`
- Source runner archive: `gs://codexalpaca-control-us/research_source/codexalpaca_runner_source_95379e4166b4.zip`
- Control packet: `docs/gcp_foundation/gcp_research_phase28_widelag_candidate_recheck_status.md`
- Control JSON: `docs/gcp_foundation/gcp_research_phase28_widelag_candidate_recheck_status.json`

## Why This Is Running

Phase27 produced one bounded validation candidate, `AAPL` exit-360 baseline. Phase28 does not retest that candidate. Instead, it targets the remaining profitable but fill-blocked AAPL/NVDA candidates with explicitly wider and costlier lag profiles to decide whether any can join the research-review queue or should be killed/quarantined.

## Result

- Decision: `ready_for_governed_validation_review`
- Eligible candidate: `NVDA` `b150__nvda__long_call__tight_reward__exit_300__liq_tight`
- Minimum net PnL: `$1593.1625`
- Minimum holdout/test net PnL: `$484.1825`
- Fill coverage: `0.9254-0.9701`
- Minimum option trades: `62`
- Worst drawdown: `$-4769.23`
- Positive net profiles: `6/6`
- Positive holdout/test profiles: `6/6`

Blocked:

- `AAPL` exit-210 stayed blocked by `fill_coverage_below_0.90`.
- `NVDA` exit-360 stayed blocked by `test_net_pnl_not_above_0`.

## Scope

- `AAPL` exit-210 wide-reward tight-liquidity candidate.
- `NVDA` exit-300 tight-reward tight-liquidity candidate.
- `NVDA` exit-360 tight-reward tight-liquidity candidate.

## Next Review Step

Run isolated NVDA governance stress before any bounded validation discussion. Do not add this candidate to a broker-facing paper run from Phase28 alone.

## Hard Rules

Do not trade, arm a window, start a broker-facing paper/live session, modify live manifests, change risk policy, or relax the `0.90` fill gate.
