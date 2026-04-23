# GCP Shared Execution Lease Runtime Wiring Handoff

## Current Read

- The sanctioned runner now has a real optional GCS-backed execution lease path.
- The default trader path is still unchanged and remains on the file lease.
- Local safety tooling still points at the file-lease model, which is intentional at this phase.

## Operator Rule

- Treat the GCS runtime wiring as VM-only dry-run ready, not broker-facing ready.
- Do not flip the backend globally.
- Do not migrate workstation health-check or standby tooling to GCS until that move is separately sanctioned.

## Next Step

- Install the runner with the `gcp` extra on `vm-execution-paper-01` and validate the live GCS lease object in dry-run mode before any broker-facing promotion decision.
