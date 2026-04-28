# Phase31 Repair-Target Wide-Lag Economics Handoff

## Current State

- State: `succeeded`
- Job: `phase31-widelag-econ-20260428112900`
- Phase id: `phase31_repair_target_widelag_economics_20260428112900`
- Project/location: `codexalpaca/us-central1`
- Source runner archive: `gs://codexalpaca-control-us/research_source/codexalpaca_runner_source_95379e4166b4.zip`
- Control packet: `docs/gcp_foundation/gcp_research_phase31_repair_target_widelag_economics_status.md`
- Control JSON: `docs/gcp_foundation/gcp_research_phase31_repair_target_widelag_economics_status.json`

## Why This Is Running

Phase29 found that all seven remaining `AMZN`/`AVGO`/`MSFT`/`MU` repair targets are wide-lag-only. Phase31 tests the economics of that explicit wide-lag policy rather than relaxing the fill gate or rerunning known bad short-lag profiles.

## Result

- Decision: `research_only_blocked`
- Eligible candidates: `0/7`
- Blocker counts: `fill_coverage_below_0.90=5`, `min_net_pnl_not_positive=2`, `test_net_pnl_not_above_0=3`
- AMZN: fill passed, holdout/test economics failed.
- MU: economics looked positive, fill coverage failed badly.
- AVGO/MSFT: failed fill and/or economics.

This cluster should be quarantined unless a redesigned strategy or materially different contract-selection/data hypothesis is introduced.

## Next Review Step

Next safe action is to stop rerunning this cluster and redirect research compute toward new candidate discovery or strategy redesign.

## Hard Rules

Do not trade, arm a window, start a broker-facing paper/live session, modify live manifests, change risk policy, or relax the `0.90` fill gate.
