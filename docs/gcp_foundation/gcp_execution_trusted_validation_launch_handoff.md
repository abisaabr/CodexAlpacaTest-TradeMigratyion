# GCP Execution Trusted Validation Launch Handoff

- Launch pack state: `awaiting_window_arm`
- VM name: `vm-execution-paper-01`
- Runner commit: `8acef9ec83d6a89e043201e2aa67e2a3f92870ca`
- Exclusive window state: `awaiting_operator_attestation`
- Exclusive window status: `awaiting_operator_confirmation`

## Operator Rule

- This pack prepares the first sanctioned trusted validation session but does not auto-start it.
- Do not use this pack unless the exclusive-window packet says `ready_for_launch` and this packet says `ready_to_launch`.
- Build and read `docs/gcp_foundation/gcp_execution_launch_authorization_handoff.md` before running the VM session command.
- Run post-session assimilation immediately after the broker-facing session ends.
