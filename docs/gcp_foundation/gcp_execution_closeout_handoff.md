# GCP Execution Closeout Handoff

- Closeout status: `window_already_closed`
- Attestation present: `False`
- Exclusive window status: `awaiting_operator_confirmation`
- Assimilation status: `ready_for_post_session_assimilation`

## Operator Rule

- After the sanctioned VM session ends, archive and remove the exclusive-window attestation before treating the lane as idle again.
- Refresh the control-plane packets and mirror them to GCS so the cloud control surface shows the closed state.
- Do not open another broker-facing session until a fresh bounded window is armed.
