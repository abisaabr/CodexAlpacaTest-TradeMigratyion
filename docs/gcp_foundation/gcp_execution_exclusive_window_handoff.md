# GCP Execution Exclusive Window Handoff

- Exclusive window status: `awaiting_operator_confirmation`
- Window state input: `operator_confirmation_required`
- Confirmed by: `pending`
- Window start: `pending`
- Window end: `pending`

## Operator Rule

- Do not start a broker-facing VM session yet. Record an explicit confirmer, window bounds, and parallel-path pause state first.
