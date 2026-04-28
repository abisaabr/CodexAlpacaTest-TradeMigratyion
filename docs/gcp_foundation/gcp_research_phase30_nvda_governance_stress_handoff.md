# Phase30 NVDA Governance Stress Handoff

## Current State

- State: `succeeded`
- Job: `phase30-nvda-governance-20260428112200`
- Phase id: `phase30_nvda_governance_stress_20260428112200`
- Project/location: `codexalpaca/us-central1`
- Source runner archive: `gs://codexalpaca-control-us/research_source/codexalpaca_runner_source_95379e4166b4.zip`
- Control packet: `docs/gcp_foundation/gcp_research_phase30_nvda_governance_stress_status.md`
- Control JSON: `docs/gcp_foundation/gcp_research_phase30_nvda_governance_stress_status.json`

## Why This Is Running

Phase28 found one new non-broker-facing research-review candidate: `NVDA` exit-300 tight-reward tight-liquidity. Phase30 applies isolated, harsher governance stress before the candidate can be discussed for any bounded paper validation packet.

## Result

- Decision: `research_only_blocked`
- Eligible candidates: `0/1`
- Blocker: `min_net_pnl_not_positive`
- Minimum net PnL: `$-782.9625`
- Minimum holdout/test net PnL: `$393.2`
- Fill coverage: `0.9254-0.9701`
- Worst drawdown: `$-6083.3875`

The candidate remains research-only. Do not include it in bounded paper validation without redesign and a new governance stress pass.

## Next Review Step

Keep NVDA exit-300 in research-only status unless a redesigned, cost-sensitive variant passes a new governance stress pass.

## Hard Rules

Do not trade, arm a window, start a broker-facing paper/live session, modify live manifests, change risk policy, or relax the `0.90` fill gate.
