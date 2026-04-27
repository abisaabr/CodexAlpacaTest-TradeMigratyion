# GCP Execution Pre-Arm Preflight

## Snapshot

- Generated at: `2026-04-27T10:30:56.353963-04:00`
- Status: `ready_to_arm_window`
- Next operator action: `arm_bounded_exclusive_window`
- VM name: `vm-execution-paper-01`
- Operator packet state: `ready_to_arm_window`
- Runtime readiness status: `runtime_ready`
- Runner provenance status: `provenance_matched`
- Source fingerprint status: `source_fingerprint_matched`
- Exclusive window status: `awaiting_operator_confirmation`
- Launch pack state: `awaiting_window_arm`
- Launch-surface audit status: `local_broker_capable_surfaces_fenced_broker_flat`
- Launch-surface broker flat: `True`
- Launch-surface no-new-order watch clean: `True`
- Launch-surface watch duration seconds: `301`
- Launch-surface newest order timestamp constant: `True`
- Trader process absent: `True`
- Ownership enabled: `True`
- Ownership backend: `file`
- Ownership lease class: `FileOwnershipLease`
- Shared execution lease enforced: `False`

## Arm Command Template

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "<control-plane-root>\cleanroom\code\qqq_options_30d_cleanroom\arm_gcp_execution_exclusive_window.ps1" -ControlPlaneRoot "<control-plane-root>" -VmName "vm-execution-paper-01" -ConfirmedBy "<confirmed-by>" -WindowStartsAt "<window-starts-at>" -WindowExpiresAt "<window-expires-at>" -ParallelPathState "paused" -MirrorToGcs
```

## Issues

- none

## Operator Read

- This packet is non-broker-facing; it does not arm the window or start a session.
- Use it immediately before arming the bounded exclusive window.
- If status is `blocked`, do not arm; refresh or resolve the named gate first.
- If status is `ready_to_arm_window`, the next action is still a human/operator arm command, not an automatic launch.
- If any new broker order appears without an explicit operator launch, stop instead of arming.

## Review Targets

- `docs/gcp_foundation/gcp_execution_prearm_preflight_handoff.md`
- `docs/gcp_foundation/gcp_execution_trusted_validation_operator_handoff.md`
- `docs/gcp_foundation/gcp_vm_runtime_readiness_handoff.md`
- `docs/gcp_foundation/gcp_vm_runner_provenance_handoff.md`
- `docs/gcp_foundation/gcp_vm_runner_source_fingerprint_handoff.md`
- `docs/gcp_foundation/gcp_execution_exclusive_window_handoff.md`
- `docs/gcp_foundation/gcp_execution_trusted_validation_launch_handoff.md`
- `docs/gcp_foundation/gcp_execution_launch_surface_audit_handoff.md`
