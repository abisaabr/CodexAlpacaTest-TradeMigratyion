# AAPL Bounded Validation Launch Gate Handoff

## Current State

- State: `ready_for_exclusive_window_operator_decision`
- Broker-facing session started: `false`
- Exclusive window armed: `false`
- Candidate: `AAPL` `b150__aapl__long_call__wide_reward__exit_360__liq_baseline`
- Runtime config: `docs/gcp_foundation/gcp_research_aapl_bounded_validation_runtime_config.yaml`
- Latest preflight: `docs/gcp_foundation/gcp_research_aapl_bounded_validation_preflight_status.md`
- Launch gate packet: `docs/gcp_foundation/gcp_research_aapl_bounded_validation_launch_gate.json`

## Operator Rule

The next decision is whether to reserve a bounded exclusive execution window for AAPL paper validation. If the answer is no, continue research-only candidate discovery. If the answer is yes, rerun the no-order preflight immediately before arming, arm the window, run only the bounded AAPL runtime config, copy VM evidence into the AAPL runtime root, and run post-session assimilation before any promotion discussion.

Do not use the global live multi-ticker manifest for this AAPL validation and do not count the session unless broker order audit, broker account activity audit, ending broker-position snapshot, shutdown reconciliation, and trade reconciliation are present.
