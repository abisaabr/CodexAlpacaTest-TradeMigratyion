# GCP Execution Launch Authorization Handoff

- Status: `blocked`
- Next operator action: `resolve_launch_blockers`
- VM name: `vm-execution-paper-01`
- Operator packet state: `ready_to_arm_window`
- Launch pack state: `awaiting_window_arm`
- Exclusive window status: `awaiting_operator_confirmation`
- Runtime readiness status: `runtime_ready`
- Runner provenance status: `provenance_matched`
- Source fingerprint status: `source_fingerprint_matched`
- Launch-surface audit status: `local_broker_capable_surfaces_fenced_broker_flat`
- Launch-surface broker flat: `True`
- Launch-surface no-new-order watch clean: `True`
- Trader process absent: `True`
- Ownership backend: `file`

## Operator Rule

- This is the final non-broker-facing go/no-go packet before running the VM session command.
- If status is `blocked`, do not run the VM session command.
- If status is `ready_to_launch_session`, run only the listed VM session command inside the active exclusive window.
- After the session ends, run post-session assimilation and close the exclusive window.

## Blocking Issues

- `operator_packet_not_ready_to_launch`: The top-level operator packet must be `ready_to_launch_session` before launch.
- `launch_pack_not_ready`: The launch pack must be `ready_to_launch` before the broker-facing session command is authorized.
- `trusted_validation_not_ready`: Trusted validation readiness must be `ready_for_manual_launch` before launch.
- `exclusive_window_not_ready`: The exclusive-window packet must say `ready_for_launch` before launch.
- `closeout_not_reserved`: Closeout must be reserved as `ready_to_close_window` before launch.
