# Phase29 Repair-Target Exit Feasibility Handoff

## Current State

- State: `succeeded`
- Job: `phase29-repair-exit-feas-20260428110900`
- Phase id: `phase29_repair_target_exit_feasibility_20260428110900`
- Project/location: `codexalpaca/us-central1`
- Source runner archive: `gs://codexalpaca-control-us/research_source/codexalpaca_runner_source_95379e4166b4.zip`
- Control packet: `docs/gcp_foundation/gcp_research_phase29_repair_target_exit_feasibility_status.md`
- Control JSON: `docs/gcp_foundation/gcp_research_phase29_repair_target_exit_feasibility_status.json`

## Why This Is Running

Phase27 gave us one usable bounded-validation lead, AAPL exit-360. Phase28 is already retesting the AAPL/NVDA profitable fill-blocked candidates. Phase29 adds a non-overlapping diagnostic lane for the remaining Phase22 repair targets across `AMZN`, `AVGO`, `MSFT`, and `MU`.

The goal is speed and discipline: find whether exit data feasibility exists before spending larger compute on economics or promotion review.

## Result

- Decision: `research_only_blocked_exit_lag`
- Full-stack fill-feasible candidates: `0/7`
- Wide-lag-only candidates: `7/7`
- Shortest passing exit lag range: `60-90` minutes

No Phase29 candidate is promotion-ready from feasibility alone. The next research-only step is a focused wide-lag economics replay using explicit wider exit policies and hardened costs.

## Next Review Step

Launch a separate economics stress replay before any governed-validation packet. If wide-lag economics fail, quarantine the candidate cluster rather than relaxing the fill gate.

## Hard Rules

Do not trade, arm a window, start a broker-facing paper/live session, modify live manifests, change risk policy, or relax the `0.90` fill gate.
