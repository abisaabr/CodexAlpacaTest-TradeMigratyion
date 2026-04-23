# GCP Execution VM Headless Lease Dry-Run Validation Status

## Snapshot

- Generated at: `2026-04-23T16:01:18.372685-04:00`
- Project ID: `codexalpaca`
- VM name: `vm-execution-paper-01`
- Zone: `us-east1-b`
- Run ID: `vm-execution-paper-01-20260423-160102`
- Launch state: `headless_lease_dry_run_validation_triggered`

## Audit Objects

- Composite startup script (local): `C:\Users\rabisaab\Downloads\CodexAlpacaTest-TradeMigratyion\output\gcp_execution_vm_headless_lease_dry_run_validation\execution_vm_headless_lease_dry_run_validation_startup_vm-execution-paper-01_vm-execution-paper-01-20260423-160102.sh`
- Composite startup script (GCS): `gs://codexalpaca-control-us/bootstrap/2026-04-23/foundation-phase17-lease-dry-run-validation/execution_vm_headless_lease_dry_run_validation_startup_vm-execution-paper-01_vm-execution-paper-01-20260423-160102.sh`
- Validation result prefix: `gs://codexalpaca-control-us/bootstrap/2026-04-23/foundation-phase17-lease-dry-run-validation/vm-execution-paper-01-20260423-160102`

## Trigger

- Metadata operation: `operation-1776974464430-650261bba3130-2b74d626-3a495f67`
- Reset operation: `operation-1776974467948-650261befdf48-51d13018-8d63f1cf`

## Follow-Up

- Wait a few minutes for the VM reset and startup script to complete.
- Inspect the GCS result prefix at gs://codexalpaca-control-us/bootstrap/2026-04-23/foundation-phase17-lease-dry-run-validation/vm-execution-paper-01-20260423-160102 for launch_result.json, lease_validation_status.json, doctor.json, pytest_targeted.log, lease_validation.log, and validation-run.log.
- Only if the headless lease dry-run review passes should the next step move toward broker-facing trusted validation.
