# GCP Foundation Bootstrap

This runbook defines the exact bootstrap work that should be performed by a higher-privilege Google Cloud principal when the current project is only `bootstrap_storage_only`.

Use this after:

- `docs/GCP_FOUNDATION_READINESS.md`

and before:

- execution-plane cut-in
- research-plane migration
- cloud orchestration rollout

## Purpose

Turn project `codexalpaca` from storage/bootstrap access only into a cloud foundation that can support:

- Compute Engine execution
- Secret Manager
- Artifact Registry
- Cloud Batch
- Workflows
- Cloud Scheduler

## Required Bootstrap APIs

Enable at minimum:

- `cloudresourcemanager.googleapis.com`
- `compute.googleapis.com`
- `secretmanager.googleapis.com`
- `artifactregistry.googleapis.com`
- `batch.googleapis.com`
- `workflows.googleapis.com`
- `cloudscheduler.googleapis.com`
- `logging.googleapis.com`
- `monitoring.googleapis.com`
- `cloudbilling.googleapis.com`

## Target Resource Names

Project:
- `codexalpaca`

Network:
- VPC: `vpc-codex-core`
- subnet: `subnet-us-east1-core`

Execution:
- VM: `vm-execution-paper-01`
- static IP: `ip-execution-paper-us-east1`

Storage:
- `gs://codexalpaca-data-us`
- `gs://codexalpaca-artifacts-us`
- `gs://codexalpaca-control-us`
- `gs://codexalpaca-backups-us`

Packaging:
- Artifact Registry repo: `trading`

Service accounts:
- `sa-execution-runner`
- `sa-research-batch`
- `sa-orchestrator`
- `sa-ci-deployer`

Orchestration:
- `workflow-nightly-research`
- `workflow-post-session-assimilation`
- `scheduler-nightly-research`
- `scheduler-post-session-assimilation`

## Bootstrap Sequence

### 1. Enable APIs

Enable the required APIs first. Do not create resources before the API layer is ready.

### 2. Create Network Foundation

Create:

- `vpc-codex-core`
- `subnet-us-east1-core`
- `ip-execution-paper-us-east1`

Goal:
- execution plane can later run from a stable outbound IP

### 3. Create Storage Buckets

Create the four long-term buckets and keep them separate by role:

- data
- artifacts
- control
- backups

Recommended controls:
- uniform bucket-level access
- versioning on control and backups
- lifecycle rules after initial validation

### 4. Create Service Accounts

Create:

- `sa-execution-runner`
- `sa-research-batch`
- `sa-orchestrator`
- `sa-ci-deployer`

Do not reuse the bootstrap-transfer service account for all runtime roles.

### 5. Grant IAM By Plane

Institutional boundary:

- execution service account:
  - can read required runtime secrets
  - can write artifacts and control outputs
  - should not own research provisioning

- research service account:
  - can read datasets
  - can write research artifacts
  - should not mutate live execution resources

- orchestrator service account:
  - can trigger jobs and workflows
  - can refresh control packets
  - should not own live-manifest mutation

### 6. Create Secret Manager Foundation

Create secret containers for:

- Alpaca paper key ID
- Alpaca paper secret key
- notification tokens
- future GitHub sync or operator credentials if needed

Do not place secret values into repo files during bootstrap.

### 7. Create Artifact Registry

Create:

- repo `trading` in `us-east1`

Goal:
- future research and utility jobs can be containerized cleanly

### 8. Create Execution VM

Create:

- `vm-execution-paper-01`

Initial intent:
- bootstrap and validate only
- do not cut over immediately

### 9. Create Budget And Monitoring Baseline

Set:

- billing budget alerts
- basic logging visibility
- basic monitoring alerts

At minimum, monitor:
- VM uptime
- job failures
- basic storage growth

## Exit Criteria

The bootstrap is complete when:

- the readiness audit no longer reports `bootstrap_storage_only`
- required APIs are enabled
- foundation resources exist with the agreed names
- dedicated service accounts exist
- the execution VM can be prepared for validation

## Hard Rules

- do not start trading as part of foundation bootstrap
- do not mix bootstrap-transfer storage with long-term runtime buckets
- do not overgrant the bootstrap principal to ongoing runtime services
- do not treat a newly created VM as production-ready until the execution cut-in checklist passes
