# GCP Foundation Readiness

## Snapshot

- Generated at: `2026-04-23T13:36:31.265819-04:00`
- Foundation status: `foundation_ready`
- Project ID: `codexalpaca`
- Service account: `sa-bootstrap-admin@codexalpaca.iam.gserviceaccount.com`
- Token mint status: `ok`

## Available Capabilities

- `project_metadata`
- `cloud_storage_bucket_list`
- `bootstrap_bucket_access`
- `compute_engine`
- `secret_manager`
- `artifact_registry`
- `cloud_batch`
- `workflows`
- `cloud_scheduler`

## Blocked Capabilities

- none

## Capability Checks

- `project_metadata`: status `available`, http `200`, summary `API call succeeded.`
- `cloud_storage_bucket_list`: status `available`, http `200`, summary `API call succeeded.`
- `bootstrap_bucket_access`: status `available`, http `200`, summary `API call succeeded.`
- `compute_engine`: status `available`, http `200`, summary `API call succeeded.`
- `secret_manager`: status `available`, http `200`, summary `API call succeeded.`
- `artifact_registry`: status `available`, http `200`, summary `API call succeeded.`
- `cloud_batch`: status `available`, http `200`, summary `API call succeeded.`
- `workflows`: status `available`, http `200`, summary `API call succeeded.`
- `cloud_scheduler`: status `available`, http `200`, summary `API call succeeded.`

## Next Actions

- Proceed to Phase 0 foundation creation and then Phase 1 execution-plane cut-in.
- Keep the bootstrap transfer bucket separate from the long-term data, artifacts, control, and backup buckets.
- Provision dedicated service accounts for execution, research, orchestration, and deployment rather than overloading the current bootstrap key.
