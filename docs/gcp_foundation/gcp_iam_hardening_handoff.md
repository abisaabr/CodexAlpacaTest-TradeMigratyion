# GCP IAM Hardening Handoff

## Current Read

- Phase 1 readiness: `change_window_required`
- We are ready to plan IAM hardening, but actual privilege removal should happen in an explicit change window.

## Immediate Goal

- Remove project-level `Owner` from service accounts.
- Preserve operator access through explicit minimal roles.
- Keep quarantined identities frozen until drift is resolved.

## First Principals To Change

- `serviceAccount:ramzi-service-account@codexalpaca.iam.gserviceaccount.com`
- `serviceAccount:sa-bootstrap-admin@codexalpaca.iam.gserviceaccount.com`

## Do Not Change Yet

- `sa-execution-runner`, `sa-research-batch`, `sa-orchestrator`, and `sa-ci-deployer` should stay narrowly scoped as they are unless a codified plane actually needs more.
- `multi-ticker-vm@codexalpaca.iam.gserviceaccount.com` should not receive new privileges while the parallel runtime path is quarantined.

## Rule

- Do not perform the IAM cutover casually. Take a fresh policy snapshot, use a planned change window, and rerun the audit immediately after each privilege drop.
