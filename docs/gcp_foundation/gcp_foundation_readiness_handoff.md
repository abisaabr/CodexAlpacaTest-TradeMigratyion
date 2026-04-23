# GCP Foundation Readiness Handoff

## Snapshot

- Generated at: `2026-04-23T13:25:15.583759-04:00`
- Foundation status: `bootstrap_storage_only`
- Recommended rollout mode: `storage_bootstrap_only`
- Project ID: `codexalpaca`
- Service account: `ramzi-service-account@codexalpaca.iam.gserviceaccount.com`

## Available Now

- `cloud_storage_bucket_list`
- `bootstrap_bucket_access`

## Blocked Now

- `project_metadata`
- `compute_engine`
- `secret_manager`
- `artifact_registry`
- `cloud_batch`
- `workflows`
- `cloud_scheduler`

## Next Actions

- Treat the current service account as a storage/bootstrap principal, not as the foundation-provisioning identity.
- Use a higher-privilege human or bootstrap principal to create the VPC, execution VM, service accounts, Secret Manager resources, Artifact Registry, and orchestration services.
- Enable or grant access to Compute Engine so the execution VM and static IP can be provisioned.
- Enable or grant access to Secret Manager before moving Alpaca credentials out of workstation-local files.
- Enable or grant access to Artifact Registry before containerizing research jobs for Batch.
- Enable or grant access to Cloud Batch before migrating heavy research and backtests.
- Enable or grant access to Workflows and Cloud Scheduler before moving governed orchestration into GCP.
- Keep the bootstrap transfer bucket separate from the long-term data, artifacts, control, and backup buckets.
- Provision dedicated service accounts for execution, research, orchestration, and deployment rather than overloading the current bootstrap key.
