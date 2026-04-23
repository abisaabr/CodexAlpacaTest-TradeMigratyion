# GCP Operating Blueprint

This document defines the institutional-grade Google Cloud target state for the project.

The goal is not "move everything to one cloud machine." The goal is:

- give Alpaca-facing execution a stable network path and static outbound identity
- separate research compute from live execution risk
- make artifacts, handoffs, and recovery reproducible
- move secrets and runtime state out of ad hoc local-machine handling
- keep GitHub as the governance layer while GCP becomes the execution and compute substrate

## Core Principle

Run different project planes on different Google Cloud primitives:

- execution plane on a dedicated Compute Engine VM
- research plane on Batch jobs
- control-plane orchestration on Scheduler + Workflows
- artifacts and datasets on Cloud Storage
- secrets in Secret Manager

Do not collapse these roles into one long-lived box unless there is a temporary bootstrap reason.

## Target Planes

### 1. Execution Plane

Primary GCP service:
- Compute Engine

Why:
- the paper runner is long-lived
- it needs a stable outbound IP
- it has local runtime state and reconciliation artifacts
- it should not be preempted like research jobs

Recommended initial instance:
- `vm-execution-paper-01`
- region: `us-east1`
- machine: `e2-standard-4`
- boot disk: `pd-ssd`, `100 GB`
- OS: Ubuntu LTS
- external IP: reserved static IPv4

Execution-plane rules:
- single writer for the runner
- no research backtests on the execution VM
- local artifacts first, then sync distilled outputs to GCS
- secrets only via Secret Manager

### 2. Research Plane

Primary GCP service:
- Google Cloud Batch

Why:
- ticker and strategy research are embarrassingly parallel
- batch jobs can scale up and down without keeping idle VMs around
- failures should be isolated per wave or lane

Recommended initial model:
- Batch jobs running containerized research tasks
- prefer Spot capacity for large backtests where retry is acceptable
- use non-Spot for high-priority validation or morning-critical follow-ons

Research-plane rules:
- jobs are stateless except for mounted input/output paths
- artifacts land in GCS, not in ephemeral job disks alone
- promotion decisions remain outside the batch jobs

### 3. Control Plane

Primary GCP services:
- Cloud Scheduler
- Workflows

Why:
- we need governed sequencing, retries, waits, and explicit handoff state
- Workflows is a good fit for multi-step orchestration across jobs and services

Control-plane responsibilities in GCP:
- trigger nightly research waves
- trigger post-session assimilation
- trigger morning brief refresh
- gate phases based on artifact presence and status outputs

Control-plane rules:
- GitHub-backed docs remain the source of governance truth
- GCP orchestrates execution of the plan; it does not replace the plan

### 4. Storage Plane

Primary GCP service:
- Cloud Storage

Buckets should be separated by role:
- `gs://codexalpaca-bootstrap-transfer-922745393036`
- `gs://codexalpaca-data-us`
- `gs://codexalpaca-artifacts-us`
- `gs://codexalpaca-control-us`
- `gs://codexalpaca-backups-us`

Recommended usage:
- `bootstrap-transfer`: one-time or occasional workspace lifts only
- `data`: raw and prepared datasets
- `artifacts`: research runs, reconciliation packets, session bundles
- `control`: distilled handoffs, machine-readable packets, deployment manifests
- `backups`: snapshots and recovery bundles

Storage rules:
- enable uniform bucket-level access
- enable versioning on control and backup buckets
- use lifecycle rules to move stale artifacts to colder storage classes
- do not treat GitHub as the raw artifact store

### 5. Secrets Plane

Primary GCP service:
- Secret Manager

Use it for:
- Alpaca paper key ID
- Alpaca paper secret key
- notification tokens
- GitHub or sync credentials if needed
- future provider credentials

Secrets rules:
- never store long-lived secrets in repo files
- never rely on a workstation-local `.env` as the canonical secret source once GCP is live
- pin runtime services to explicit secret versions when stability matters

## Networking

Institutional target:

- one VPC for the project
- one subnet for execution and one subnet for research if needed
- one reserved static external IP for the execution VM
- no broad inbound exposure
- use OS Login / IAP or equivalent controlled admin access

Recommended network resources:
- VPC: `vpc-codex-core`
- subnet: `subnet-us-east1-core`
- static execution IP: `ip-execution-paper-us-east1`

Execution connectivity rule:
- Alpaca traffic should come from the execution VM's static IP, not from a laptop or unstable VPN path

## Identity And Access

Use separate service accounts:

- `sa-execution-runner`
- `sa-research-batch`
- `sa-orchestrator`
- `sa-ci-deployer`

Principles:
- least privilege
- no shared human/service credentials
- separate "can run" from "can read secrets" from "can deploy"

Suggested boundaries:
- runner reads only its required secrets and writes only artifacts/control outputs
- research jobs read datasets, write artifacts, and read only research-related secrets
- orchestrator can launch jobs and refresh packets, but should not have live runner mutation rights

## Packaging And Deployment

Institutional target:
- do not run the cloud estate from copied working trees
- build deterministic container images for research jobs
- use a fixed VM bootstrap script or image for the execution VM

Recommended services:
- Artifact Registry for research/execution images

Packaging rules:
- the current bootstrap bucket upload is a migration aid and backup
- it is not the desired long-term deployment model
- `.venv`, local caches, and ad hoc machine state should not be the primary runtime package

## Observability

Use:
- Cloud Logging
- Cloud Monitoring
- budget alerts

Track at minimum:
- runner heartbeat
- Alpaca connectivity failures
- order audit coverage
- broker activity audit coverage
- reconciliation posture
- research job success/failure by lane
- morning brief generation success

Alerting should distinguish:
- execution-plane incidents
- research-plane failures
- control-plane orchestration failures

## Recovery Model

### Execution Plane

- daily persistent disk snapshots
- local session artifacts synced to GCS
- explicit runner capability stamp in every session summary
- restore script for rebuilding the execution VM from GCS + Secret Manager

### Research Plane

- rerunnable from data + code + control-plane packets
- no irreplaceable state should live only on ephemeral batch nodes

### Control Plane

- all canonical docs and prompts remain in GitHub
- GCS holds distilled control packets for runtime consumption

## Recommended Initial Resource Set

Start simple but correct:

- `vm-execution-paper-01`
- `ip-execution-paper-us-east1`
- `gs://codexalpaca-data-us`
- `gs://codexalpaca-artifacts-us`
- `gs://codexalpaca-control-us`
- `gs://codexalpaca-backups-us`
- `artifact registry repo: trading`
- `workflow-nightly-research`
- `workflow-post-session-assimilation`
- `scheduler-nightly-research`
- `scheduler-post-session-assimilation`

## Hard Rules

- do not co-locate the paper runner and heavy overnight backtests on the same machine
- do not use the bootstrap-transfer bucket as the permanent runtime artifact bucket
- do not keep Alpaca credentials in repo files once the GCP stack is active
- do not let research jobs mutate the live manifest
- do not let a single cloud job both discover strategies and approve promotion

## Migration Standard

The project should move to GCP in this order:

1. foundation
2. execution plane
3. research plane
4. orchestration
5. observability and hardening

See `docs/GCP_MIGRATION_PLAN.md` for the phased rollout.
