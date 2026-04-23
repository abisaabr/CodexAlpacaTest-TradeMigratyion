# GCP Execution VM Headless Validation Status

## Snapshot

- Generated at: `2026-04-23T14:35:24.392917-04:00`
- Project ID: `codexalpaca`
- VM name: `vm-execution-paper-01`
- Zone: `us-east1-b`
- Run ID: `vm-execution-paper-01-20260423-143508`
- Launch state: `headless_validation_triggered`

## Audit Objects

- Composite startup script (local): `C:\Users\rabisaab\Downloads\CodexAlpacaTest-TradeMigratyion\output\gcp_execution_vm_headless_validation\execution_vm_headless_validation_startup_vm-execution-paper-01_vm-execution-paper-01-20260423-143508.sh`
- Composite startup script (GCS): `gs://codexalpaca-control-us/bootstrap/2026-04-23/foundation-phase5-headless-validation/execution_vm_headless_validation_startup_vm-execution-paper-01_vm-execution-paper-01-20260423-143508.sh`
- Validation result prefix: `gs://codexalpaca-control-us/bootstrap/2026-04-23/foundation-phase5-headless-validation/vm-execution-paper-01-20260423-143508`

## Trigger

- Metadata operation: `operation-1776969310756-65024e88b5f32-c8ebc96a-22a46be3`
- Reset operation: `operation-1776969314445-65024e8c3a942-08f2403d-4a94e319`

## Follow-Up

- Wait a few minutes for the VM reset and startup script to complete.
- Inspect the GCS result prefix at gs://codexalpaca-control-us/bootstrap/2026-04-23/foundation-phase5-headless-validation/vm-execution-paper-01-20260423-143508 for launch_result.json, validation_status.json, doctor.json, and pytest.log.
- Only if the headless validation packet is clean should the next step move to a trusted validation session.
