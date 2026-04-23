# GCP Execution VM Lease Dry-Run Validation Status

## Snapshot

- Generated at: `2026-04-23T16:01:00.643953-04:00`
- Project ID: `codexalpaca`
- VM name: `vm-execution-paper-01`
- Zone: `us-east1-b`
- Expected static IP: `34.139.193.220`
- Lease URI: `gs://codexalpaca-control-us/leases/paper-execution/lease.json`

## Validation Script

- Local path: `C:\Users\rabisaab\Downloads\CodexAlpacaTest-TradeMigratyion\output\gcp_execution_vm_lease_dry_run_validation\execution_vm_lease_dry_run_validation_vm-execution-paper-01_20260423.sh`
- Control bucket URI: `gs://codexalpaca-control-us/bootstrap/2026-04-23/foundation-phase17-lease-dry-run-validation/execution_vm_lease_dry_run_validation_vm-execution-paper-01_20260423.sh`
- Runtime bootstrap script URI: `gs://codexalpaca-control-us/bootstrap/2026-04-23/foundation-phase2-runtime/execution_vm_runtime_bootstrap_vm-execution-paper-01_20260423.sh`

## Guardrails

- The validation script is non-broker-facing: it does not call trader.run() and constructs the trader with broker=object().
- Ownership remains enabled only inside the validation process through session-scoped env overrides.
- The dry-run aborts immediately if the lease object already exists before validation starts.
- The default runner path remains on the file lease until a later promotion step explicitly changes it.

## Validation Gate

- `Observed VM external IP matches the reserved execution static IP.`
- `Runtime bootstrap completes from the current sanctioned runner bundle.`
- `The VM can install the optional gcp dependency path.`
- `Targeted ownership and trader tests pass on-VM.`
- `Trader-side GCS lease wiring acquires, renews, blocks contention, steals after expiry, and releases cleanly.`
- `The shared lease object is absent again after release.`

## Next Actions

- Launch this validation through the governed headless VM reset path.
- Wait for the result prefix to contain launch_result.json, lease_validation_status.json, doctor.json, pytest_targeted.log, lease_validation.log, and validation-run.log.
- Only if the review packet passes should the next step move toward broker-facing trusted validation.
