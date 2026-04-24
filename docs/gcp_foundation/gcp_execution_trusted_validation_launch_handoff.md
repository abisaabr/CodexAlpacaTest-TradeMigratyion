# GCP Execution Trusted Validation Launch Handoff

- Launch pack state: `awaiting_window_arm`
- VM name: `vm-execution-paper-01`
- Runner commit: `f0080066c68d883286f4cb1b9c9e0edc601adf8d`
- Exclusive window state: `awaiting_operator_attestation`
- Exclusive window status: `awaiting_operator_confirmation`

## Operator Rule

- This pack prepares the first sanctioned trusted validation session but does not auto-start it.
- Do not use this pack unless the exclusive-window packet says `ready_for_launch` and this packet says `ready_to_launch`.
- Build and read `docs/gcp_foundation/gcp_execution_launch_authorization_handoff.md` before running the VM session command.
- Run post-session assimilation immediately after the broker-facing session ends.
