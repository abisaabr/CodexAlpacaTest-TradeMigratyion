# GCP Foundation Readiness

## Snapshot

- Generated at: `2026-04-23T13:25:15.380485-04:00`
- Foundation status: `bootstrap_storage_only`
- Project ID: `codexalpaca`
- Service account: `ramzi-service-account@codexalpaca.iam.gserviceaccount.com`
- Token mint status: `ok`

## Available Capabilities

- `cloud_storage_bucket_list`
- `bootstrap_bucket_access`

## Blocked Capabilities

- `project_metadata`
- `compute_engine`
- `secret_manager`
- `artifact_registry`
- `cloud_batch`
- `workflows`
- `cloud_scheduler`

## Capability Checks

- `project_metadata`: status `api_disabled_or_not_enabled`, http `403`, summary `Cloud Resource Manager API has not been used in project 922745393036 before or it is disabled. Enable it by visiting https://console.developers.google.com/apis/api/cloudresourcemanager.googleapis.com/overview?project=922745393036 then retry. If you enabled this API recently, wait a few minutes for the action to propagate to our systems and retry.`
- `cloud_storage_bucket_list`: status `available`, http `200`, summary `API call succeeded.`
- `bootstrap_bucket_access`: status `available`, http `200`, summary `API call succeeded.`
- `compute_engine`: status `api_disabled_or_not_enabled`, http `403`, summary `Compute Engine API has not been used in project codexalpaca before or it is disabled. Enable it by visiting https://console.developers.google.com/apis/api/compute.googleapis.com/overview?project=codexalpaca then retry. If you enabled this API recently, wait a few minutes for the action to propagate to our systems and retry.`
- `secret_manager`: status `api_disabled_or_not_enabled`, http `403`, summary `Secret Manager API has not been used in project codexalpaca before or it is disabled. Enable it by visiting https://console.developers.google.com/apis/api/secretmanager.googleapis.com/overview?project=codexalpaca then retry. If you enabled this API recently, wait a few minutes for the action to propagate to our systems and retry.`
- `artifact_registry`: status `api_disabled_or_not_enabled`, http `403`, summary `Artifact Registry API has not been used in project codexalpaca before or it is disabled. Enable it by visiting https://console.developers.google.com/apis/api/artifactregistry.googleapis.com/overview?project=codexalpaca then retry. If you enabled this API recently, wait a few minutes for the action to propagate to our systems and retry.`
- `cloud_batch`: status `api_disabled_or_not_enabled`, http `403`, summary `Batch API has not been used in project codexalpaca before or it is disabled. Enable it by visiting https://console.developers.google.com/apis/api/batch.googleapis.com/overview?project=codexalpaca then retry. If you enabled this API recently, wait a few minutes for the action to propagate to our systems and retry.`
- `workflows`: status `api_disabled_or_not_enabled`, http `403`, summary `Workflows API has not been used in project codexalpaca before or it is disabled. Enable it by visiting https://console.developers.google.com/apis/api/workflows.googleapis.com/overview?project=codexalpaca then retry. If you enabled this API recently, wait a few minutes for the action to propagate to our systems and retry.`
- `cloud_scheduler`: status `api_disabled_or_not_enabled`, http `403`, summary `Cloud Scheduler API has not been used in project codexalpaca before or it is disabled. Enable it by visiting https://console.developers.google.com/apis/api/cloudscheduler.googleapis.com/overview?project=codexalpaca then retry. If you enabled this API recently, wait a few minutes for the action to propagate to our systems and retry.`

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
