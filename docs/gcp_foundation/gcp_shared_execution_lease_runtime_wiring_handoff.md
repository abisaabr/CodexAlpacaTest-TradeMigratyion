# GCP Shared Execution Lease Runtime Wiring Handoff

## Current Read

- The sanctioned runner now has a real optional GCS-backed execution lease path.
- The default trader path is still unchanged and remains on the file lease.
- Health-check supports the non-default GCS backend, while standby failover still rejects non-file backends by design.

## Operator Rule

- Treat the GCS runtime wiring as VM-only dry-run ready, not broker-facing ready.
- Do not flip the backend globally.
- Do not widen the temporary parallel-runtime exception onto the cloud lease path.

## Next Step

- Install the runner with the `gcp` extra on `vm-execution-paper-01` and validate the live GCS lease object in dry-run mode before any broker-facing promotion decision.
