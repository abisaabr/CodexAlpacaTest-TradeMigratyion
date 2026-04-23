# GCP Runtime Security Status

## Snapshot

- Generated at: `2026-04-23T13:49:10.379123-04:00`
- Project ID: `codexalpaca`
- Bootstrap service account: `sa-bootstrap-admin@codexalpaca.iam.gserviceaccount.com`

## Secrets

- `execution-alpaca-paper-api-key`: secret `existing`, seeded `true`, version action `existing_version_present`
- `execution-alpaca-paper-secret-key`: secret `created`, seeded `true`, version action `seeded_initial_version`
- `notification-discord-webhook-url`: secret `created`, seeded `true`, version action `seeded_initial_version`
- `notification-ntfy-access-token`: secret `created`, seeded `false`, version action `pending_value`
- `notification-email-password`: secret `created`, seeded `false`, version action `pending_value`

## Secret Access Bindings

- `execution-alpaca-paper-api-key` -> `serviceAccount:sa-execution-runner@codexalpaca.iam.gserviceaccount.com`: `queued_project_scope_fallback` at `project` scope
- `execution-alpaca-paper-secret-key` -> `serviceAccount:sa-execution-runner@codexalpaca.iam.gserviceaccount.com`: `queued_project_scope_fallback` at `project` scope
- `notification-discord-webhook-url` -> `serviceAccount:sa-execution-runner@codexalpaca.iam.gserviceaccount.com`: `queued_project_scope_fallback` at `project` scope
- `notification-ntfy-access-token` -> `serviceAccount:sa-execution-runner@codexalpaca.iam.gserviceaccount.com`: `queued_project_scope_fallback` at `project` scope
- `notification-email-password` -> `serviceAccount:sa-execution-runner@codexalpaca.iam.gserviceaccount.com`: `queued_project_scope_fallback` at `project` scope

## Project IAM

- `roles/logging.logWriter` -> `serviceAccount:sa-execution-runner@codexalpaca.iam.gserviceaccount.com`: `bound`
- `roles/monitoring.metricWriter` -> `serviceAccount:sa-execution-runner@codexalpaca.iam.gserviceaccount.com`: `bound`
- `roles/logging.logWriter` -> `serviceAccount:sa-research-batch@codexalpaca.iam.gserviceaccount.com`: `bound`
- `roles/monitoring.metricWriter` -> `serviceAccount:sa-research-batch@codexalpaca.iam.gserviceaccount.com`: `bound`
- `roles/logging.logWriter` -> `serviceAccount:sa-orchestrator@codexalpaca.iam.gserviceaccount.com`: `bound`
- `roles/monitoring.metricWriter` -> `serviceAccount:sa-orchestrator@codexalpaca.iam.gserviceaccount.com`: `bound`
- `roles/artifactregistry.writer` -> `serviceAccount:sa-ci-deployer@codexalpaca.iam.gserviceaccount.com`: `bound`
- `roles/artifactregistry.reader` -> `serviceAccount:sa-research-batch@codexalpaca.iam.gserviceaccount.com`: `bound`
- `roles/artifactregistry.reader` -> `serviceAccount:sa-execution-runner@codexalpaca.iam.gserviceaccount.com`: `bound`
- `roles/secretmanager.secretAccessor` -> `serviceAccount:sa-execution-runner@codexalpaca.iam.gserviceaccount.com`: `bound`

## Bucket IAM

- `codexalpaca-data-us` `roles/storage.objectViewer` -> `serviceAccount:sa-research-batch@codexalpaca.iam.gserviceaccount.com`: `bound`
- `codexalpaca-artifacts-us` `roles/storage.objectAdmin` -> `serviceAccount:sa-research-batch@codexalpaca.iam.gserviceaccount.com`: `bound`
- `codexalpaca-artifacts-us` `roles/storage.objectAdmin` -> `serviceAccount:sa-execution-runner@codexalpaca.iam.gserviceaccount.com`: `bound`
- `codexalpaca-artifacts-us` `roles/storage.objectViewer` -> `serviceAccount:sa-orchestrator@codexalpaca.iam.gserviceaccount.com`: `bound`
- `codexalpaca-control-us` `roles/storage.objectAdmin` -> `serviceAccount:sa-execution-runner@codexalpaca.iam.gserviceaccount.com`: `bound`
- `codexalpaca-control-us` `roles/storage.objectAdmin` -> `serviceAccount:sa-orchestrator@codexalpaca.iam.gserviceaccount.com`: `bound`
- `codexalpaca-control-us` `roles/storage.objectViewer` -> `serviceAccount:sa-research-batch@codexalpaca.iam.gserviceaccount.com`: `bound`
- `codexalpaca-backups-us` `roles/storage.objectAdmin` -> `serviceAccount:sa-execution-runner@codexalpaca.iam.gserviceaccount.com`: `bound`
- `codexalpaca-backups-us` `roles/storage.objectViewer` -> `serviceAccount:sa-orchestrator@codexalpaca.iam.gserviceaccount.com`: `bound`

## Next Actions

- Create the reserved execution static IP and the validation-only execution VM next.
- Teach the execution VM bootstrap to pull Secret Manager values into its runtime environment.
- Add Workflow and Batch-specific service-account impersonation bindings when the orchestrator resources are created.
- Sync the runtime security status packet into the control bucket and GitHub so the other machine can follow the exact cloud state.
