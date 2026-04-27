# GCP Execution Trusted Validation Operator Handoff

- Operator packet state: `blocked`
- Exclusive window status: `awaiting_operator_confirmation`
- Launch pack state: `awaiting_window_arm`
- Closeout status: `window_already_closed`
- Runner provenance status: `provenance_matched`
- Runner provenance blocks launch: `False`
- Runtime readiness status: `runtime_ready`
- Runtime readiness blocks launch: `False`
- Runtime trader process absent: `True`
- Runtime ownership enabled: `True`
- Runtime ownership backend: `file`
- Runtime ownership lease class: `FileOwnershipLease`
- Runtime shared execution lease enforced: `False`
- Session completion gate: `evidence_gapped`
- Launch-surface audit status: `local_broker_capable_surfaces_fenced_broker_flat`
- Launch-surface audit blocks launch: `False`
- Launch-surface broker flat: `True`
- Launch-surface no-new-order watch clean: `True`
- Startup preflight status: `startup_preflight_blocked`
- Startup preflight startup-check status: `failed`
- Startup preflight freshness status: `fresh`
- Startup preflight age seconds: `54`
- Startup preflight max age seconds: `600`
- Startup preflight blocks launch: `True`
- Startup preflight broker position count: `0`
- Startup preflight open order count: `0`

## Operator Rule

- Use this packet as the single top-level checklist for the first sanctioned VM trusted validation session.
- If the packet state is `blocked`, resolve the blocking gate and refresh packets before arming the window.
- If the launch-surface audit blocks launch, do not arm the window even if older packets looked ready.
- If the startup preflight blocks launch, do not arm or launch; rerun it immediately before any new launch attempt.
- If the packet says `ready_to_arm_window`, arm the window first and re-read the refreshed packets before launching anything.
- Do not start the VM session unless the refreshed launch packet says `ready_to_launch`.
- Always follow with post-session assimilation and exclusive-window closeout.
