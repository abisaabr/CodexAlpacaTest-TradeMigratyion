# Phase29 Repair-Target Exit Feasibility Handoff

## Current State

- State: `scheduled`
- Job: `phase29-repair-exit-feas-20260428110900`
- Phase id: `phase29_repair_target_exit_feasibility_20260428110900`
- Project/location: `codexalpaca/us-central1`
- Source runner archive: `gs://codexalpaca-control-us/research_source/codexalpaca_runner_source_95379e4166b4.zip`
- Control packet: `docs/gcp_foundation/gcp_research_phase29_repair_target_exit_feasibility_status.md`
- Control JSON: `docs/gcp_foundation/gcp_research_phase29_repair_target_exit_feasibility_status.json`

## Why This Is Running

Phase27 gave us one usable bounded-validation lead, AAPL exit-360. Phase28 is already retesting the AAPL/NVDA profitable fill-blocked candidates. Phase29 adds a non-overlapping diagnostic lane for the remaining Phase22 repair targets across `AMZN`, `AVGO`, `MSFT`, and `MU`.

The goal is speed and discipline: find whether exit data feasibility exists before spending larger compute on economics or promotion review.

## Next Review Step

When the Batch job reaches `SUCCEEDED`, inspect:

- `exit_lag_feasibility/exit_lag_feasibility_packet.json`
- `exit_lag_feasibility/exit_lag_candidate_summary.csv`
- `logs/run.err.log`
- `logs/run.out.log`

If candidates only pass at very wide exit windows, route them to exit-policy research, not promotion. If candidates fail the `0.90` fill gate even at wide lags, quarantine them. If candidates pass at defensible lags, launch a separate economics stress replay before any governed-validation packet.

## Hard Rules

Do not trade, arm a window, start a broker-facing paper/live session, modify live manifests, change risk policy, or relax the `0.90` fill gate.
