# GCP Execution VM Headless Validation Status

## Snapshot

- Generated at: `2026-04-23T14:44:37.942557-04:00`
- Project ID: `codexalpaca`
- VM name: `vm-execution-paper-01`
- Zone: `us-east1-b`
- Run ID: `vm-execution-paper-01-20260423-144414`
- Launch state: `headless_validation_triggered`

## Audit Objects

- Composite startup script (local): `C:\Users\rabisaab\Downloads\CodexAlpacaTest-TradeMigratyion\output\gcp_execution_vm_headless_validation\execution_vm_headless_validation_startup_vm-execution-paper-01_vm-execution-paper-01-20260423-144414.sh`
- Composite startup script (GCS): `gs://codexalpaca-control-us/bootstrap/2026-04-23/foundation-phase5-headless-validation/execution_vm_headless_validation_startup_vm-execution-paper-01_vm-execution-paper-01-20260423-144414.sh`
- Validation result prefix: `gs://codexalpaca-control-us/bootstrap/2026-04-23/foundation-phase5-headless-validation/vm-execution-paper-01-20260423-144414`

## Trigger

- Metadata operation: `operation-1776969857343-65025091fa00c-a951aeef-62588348`
- Reset operation: `operation-1776969860981-650250957227c-fecf94b4-ec9e2ae7`

## Follow-Up

- Wait a few minutes for the VM reset and startup script to complete.
- Inspect the GCS result prefix at gs://codexalpaca-control-us/bootstrap/2026-04-23/foundation-phase5-headless-validation/vm-execution-paper-01-20260423-144414 for launch_result.json, validation_status.json, doctor.json, and pytest.log.
- Only if the headless validation packet is clean should the next step move to a trusted validation session.
