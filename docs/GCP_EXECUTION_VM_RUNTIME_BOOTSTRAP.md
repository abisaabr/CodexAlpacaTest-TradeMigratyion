# GCP Execution VM Runtime Bootstrap

This runbook defines the next institutional step after the validation VM exists: prepare a reproducible runtime bootstrap for that VM without starting trading.

The goal is:

- give the execution VM a deterministic code bundle
- materialize a validation-only `.env` from Secret Manager plus non-secret config
- reuse the repo's native Linux bootstrap flow instead of inventing a cloud-only install path
- keep the workstation runner as rollback until the VM clears validation

## Current Bootstrap Model

The execution VM runtime bootstrap should:

- download a code bundle from GCS
- extract the repo into `/opt/codexalpaca/codexalpaca_repo`
- create `.env` from:
  - Secret Manager values for secrets
  - generated non-secret validation config
- run `scripts/bootstrap_linux.sh`
- stop before any trader or watchdog service is started

## Validation-Only Config Rules

The validation VM should override:

- `MULTI_TICKER_MACHINE_LABEL=vm-execution-paper-01`
- `MULTI_TICKER_OWNERSHIP_ENABLED=false`

This keeps the VM from competing for the current Google Drive lease while it is still proving out its environment.

## Canonical Secret Source

The runtime bootstrap must read secrets from Secret Manager, not from a copied workstation `.env`.

Current secret targets:

- `execution-alpaca-paper-api-key`
- `execution-alpaca-paper-secret-key`
- `notification-discord-webhook-url`
- `notification-ntfy-access-token`
- `notification-email-password`

## Artifact Targets

Recommended GCS split:

- code bundle in `gs://codexalpaca-backups-us/...`
- bootstrap script and status packet in `gs://codexalpaca-control-us/...`

That keeps the bootstrap traceable from the control plane while leaving the larger code archive in the backup/restore plane.

## Builder

Use:

- `cleanroom/code/qqq_options_30d_cleanroom\bootstrap_gcp_execution_vm_runtime.py`

Outputs:

- `docs/gcp_foundation/gcp_execution_vm_runtime_bootstrap_status.json`
- `docs/gcp_foundation/gcp_execution_vm_runtime_bootstrap_status.md`

## Hard Rules

- do not embed secret values in the code bundle
- do not turn the runtime bootstrap into an auto-start cutover
- do not enable ownership leasing on the VM until promotion is intentional
- do not delete the workstation runner until the VM clears a trusted validation session
