# GCP Execution VM Validation

This runbook defines the governed validation gate for the execution VM before any paper-runner cutover.

The goal is:

- prove the VM can restore code and dependencies
- prove the VM can read its runtime secrets from Secret Manager
- prove the VM is using the reserved static IP
- prove the repo can pass the baseline local validation checks on the VM
- leave behind a durable validation packet

## Validation Sequence

Run these steps in order:

1. connect to the VM through OS Login and IAP
2. confirm the VM external IP matches the reserved execution IP
3. run the published VM runtime bootstrap script
4. run `scripts/doctor.py --skip-connectivity --json`
5. run `python -m pytest -q`
6. write the local validation packet on the VM

## Required Pass Conditions

- VM metadata external IP matches the reserved static IP
- runtime bootstrap completes without error
- doctor reports paper-only compatible configuration
- pytest exits `0`
- validation packet exists on the VM

## Validation Artifact

The validation process should leave behind:

- `/var/lib/codexalpaca/validation/validation_status.json`

That packet should include:

- validation timestamp
- expected static IP
- observed VM external IP
- runtime bootstrap status
- doctor status
- pytest exit code

## Builder

Use:

- `cleanroom/code/qqq_options_30d_cleanroom/bootstrap_gcp_execution_vm_validation.py`

Outputs:

- `docs/gcp_foundation/gcp_execution_vm_validation_status.json`
- `docs/gcp_foundation/gcp_execution_vm_validation_status.md`

## Hard Rules

- do not start trading as part of validation
- do not enable ownership leasing during validation
- do not treat a successful bootstrap alone as enough for cutover
- do not promote the VM until the trusted validation session gate is cleared
