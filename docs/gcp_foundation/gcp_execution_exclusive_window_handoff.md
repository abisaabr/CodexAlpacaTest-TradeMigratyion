# GCP Execution Exclusive Window Handoff

- Window state: `awaiting_operator_attestation`
- Window status: `awaiting_operator_confirmation`
- VM name: `vm-execution-paper-01`
- Attestation path: `docs/gcp_foundation/gcp_execution_exclusive_window_attestation.json`

## Operator Rule

- Do not start the first trusted validation paper session unless this packet says `ready_for_launch`.
- Keep the window bounded to a single sanctioned writer on `vm-execution-paper-01`.
- Run governed post-session assimilation immediately after the session ends.
