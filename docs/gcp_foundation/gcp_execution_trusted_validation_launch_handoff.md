# GCP Execution Trusted Validation Launch Handoff

- Launch pack state: `awaiting_window_arm`
- VM name: `vm-execution-paper-01`
- Runner commit: `f2b9bae7b2af26eefc086189a244e4d5a6c81a83`
- Exclusive window state: `awaiting_operator_attestation`
- Exclusive window status: `awaiting_operator_confirmation`

## Operator Rule

- This pack prepares the first sanctioned trusted validation session but does not auto-start it.
- Do not use this pack unless the exclusive-window packet says `ready_for_launch` and this packet says `ready_to_launch`.
- Run post-session assimilation immediately after the broker-facing session ends.
