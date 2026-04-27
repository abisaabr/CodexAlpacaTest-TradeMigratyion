# GCP Execution Pre-Arm Preflight Handoff

- Status: `blocked`
- Next operator action: `resolve_prearm_blockers`
- VM name: `vm-execution-paper-01`
- Operator packet state: `blocked`
- Runtime readiness status: `runtime_ready`
- Runner provenance status: `provenance_matched`
- Source fingerprint status: `source_fingerprint_matched`
- Startup preflight status: `startup_preflight_blocked`
- Startup preflight freshness status: `fresh`
- Startup preflight age seconds: `54`
- Startup preflight max age seconds: `600`
- Startup preflight blocks launch: `True`
- Launch-surface audit status: `local_broker_capable_surfaces_fenced_broker_flat`
- Launch-surface broker flat: `True`
- Launch-surface no-new-order watch clean: `True`
- Launch-surface newest order timestamp constant: `True`
- Trader process absent: `True`
- Ownership backend: `file`
- Shared execution lease enforced: `False`

## Operator Rule

- This is the last non-broker-facing go/no-go check before arming the exclusive execution window.
- If status is `blocked`, do not arm the window.
- If status is `ready_to_arm_window`, the next safe action is to arm a bounded exclusive window, then refresh packets before launch.

## Blocking Issues

- `operator_packet_not_ready_to_arm`: The top-level operator packet must be `ready_to_arm_window` before arming.
- `startup_preflight_not_clean`: The read-only VM startup preflight must be fresh and passed before arming.
