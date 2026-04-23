# GCP Execution Trusted Validation Operator Handoff

- Operator packet state: `ready_to_arm_window`
- Exclusive window status: `awaiting_operator_confirmation`
- Launch pack state: `awaiting_window_arm`
- Closeout status: `window_already_closed`

## Operator Rule

- Use this packet as the single top-level checklist for the first sanctioned VM trusted validation session.
- If the packet says `ready_to_arm_window`, arm the window first and re-read the refreshed packets before launching anything.
- Do not start the VM session unless the refreshed launch packet says `ready_to_launch`.
- Always follow with post-session assimilation and exclusive-window closeout.
