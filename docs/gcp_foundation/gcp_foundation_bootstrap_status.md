# GCP Foundation Bootstrap Status

## Snapshot

- Generated at: `2026-04-23T13:39:29.360788-04:00`
- Project ID: `codexalpaca`
- Project number: `922745393036`
- Bootstrap service account: `sa-bootstrap-admin@codexalpaca.iam.gserviceaccount.com`
- Region: `us-east1`

## Resource Results

- `network` `vpc-codex-core`: `created`
- `subnet` `subnet-us-east1-core`: `created` (cidr `10.10.0.0/20`)
- `bucket` `codexalpaca-data-us`: `created` (versioning `false`)
- `bucket` `codexalpaca-artifacts-us`: `created` (versioning `false`)
- `bucket` `codexalpaca-control-us`: `created` (versioning `true`)
- `bucket` `codexalpaca-backups-us`: `created` (versioning `true`)
- `service_account` `sa-execution-runner@codexalpaca.iam.gserviceaccount.com`: `created`
- `service_account` `sa-research-batch@codexalpaca.iam.gserviceaccount.com`: `created`
- `service_account` `sa-orchestrator@codexalpaca.iam.gserviceaccount.com`: `created`
- `service_account` `sa-ci-deployer@codexalpaca.iam.gserviceaccount.com`: `created`
- `artifact_registry` `trading`: `created` (region `us-east1`)

## Next Actions

- Reserve the execution static IP and create the validation-only execution VM next.
- Create runtime secrets in Secret Manager before cloud execution cut-in.
- Sync the current control-plane packet into the long-term control bucket.
- Rerun the GCP foundation readiness audit after any IAM or resource changes.
