# GCP Execution Trusted Validation Launch Handoff

- Launch pack state: `awaiting_window_arm`
- VM name: `vm-execution-paper-01`
- Runner commit: `a6cf50aa424a51440f5744ec0c634150e82fc7c0`
- Exclusive window state: `awaiting_operator_attestation`
- Exclusive window status: `awaiting_operator_confirmation`

## Operator Rule

- This pack prepares the first sanctioned trusted validation session but does not auto-start it.
- Do not use this pack unless the exclusive-window packet says `confirmed_active_window`.
- Run post-session assimilation immediately after the broker-facing session ends.
