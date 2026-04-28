# Phase31 Repair-Target Wide-Lag Economics Handoff

## Current State

- State: `queued`
- Job: `phase31-widelag-econ-20260428112900`
- Phase id: `phase31_repair_target_widelag_economics_20260428112900`
- Project/location: `codexalpaca/us-central1`
- Source runner archive: `gs://codexalpaca-control-us/research_source/codexalpaca_runner_source_95379e4166b4.zip`
- Control packet: `docs/gcp_foundation/gcp_research_phase31_repair_target_widelag_economics_status.md`
- Control JSON: `docs/gcp_foundation/gcp_research_phase31_repair_target_widelag_economics_status.json`

## Why This Is Running

Phase29 found that all seven remaining `AMZN`/`AVGO`/`MSFT`/`MU` repair targets are wide-lag-only. Phase31 tests the economics of that explicit wide-lag policy rather than relaxing the fill gate or rerunning known bad short-lag profiles.

## Next Review Step

When the Batch job reaches `SUCCEEDED`, inspect:

- `portfolio_report/research_portfolio_report.json`
- `promotion_review_packet/research_promotion_review_packet.json`
- `logs/run.err.log`
- `logs/run.out.log`

If candidates pass, they still require separate governance stress before bounded validation discussion. If candidates fail, quarantine the wide-lag cluster.

## Hard Rules

Do not trade, arm a window, start a broker-facing paper/live session, modify live manifests, change risk policy, or relax the `0.90` fill gate.
