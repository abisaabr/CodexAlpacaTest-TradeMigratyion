# GCP Execution Trusted Validation Operator Handoff

- Operator packet state: `ready_to_arm_window`
- Exclusive window status: `awaiting_operator_confirmation`
- Launch pack state: `awaiting_window_arm`
- Closeout status: `window_already_closed`
- Runner provenance status: `provenance_matched`
- Runner provenance blocks launch: `False`
- Runtime readiness status: `runtime_ready`
- Runtime readiness blocks launch: `False`
- Runtime ownership enabled: `True`
- Runtime ownership backend: `file`
- Runtime ownership lease class: `FileOwnershipLease`
- Runtime shared execution lease enforced: `False`

## Operator Rule

- Use this packet as the single top-level checklist for the first sanctioned VM trusted validation session.
- If the packet state is `blocked`, resolve the blocking gate and refresh packets before arming the window.
- If the packet says `ready_to_arm_window`, arm the window first and re-read the refreshed packets before launching anything.
- Do not start the VM session unless the refreshed launch packet says `ready_to_launch`.
- Always follow with post-session assimilation and exclusive-window closeout.
