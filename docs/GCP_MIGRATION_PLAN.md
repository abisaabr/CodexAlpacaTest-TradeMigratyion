# GCP Migration Plan

This document defines the phased rollout from the current workstation-centered project into the Google Cloud operating model.

## Success Definition

The migration is successful when:

- the paper runner can operate without depending on the local VPN path
- research jobs can run in parallel without depending on a single workstation
- artifacts and handoffs survive machine loss
- secrets are no longer anchored to workstation-local `.env` files
- the control plane can still govern the project without loss of lineage

## Preflight Gate

Before Phase 0 begins, run the GCP foundation readiness builder chain described in:

- `docs/GCP_FOUNDATION_READINESS.md`

Do not confuse storage access with true cloud-foundation readiness.

The rollout should not be called Phase-0 ready until the generated handoff says the project is at least `foundation_partial`, and ideally `foundation_ready`, or until a stronger bootstrap principal is explicitly chosen for provisioning.

## Phase 0: Foundation

Objective:
- establish the minimum cloud substrate without changing trading behavior

Deliverables:
- project APIs enabled
- VPC and subnet created
- static IP reserved for execution
- target buckets created
- Secret Manager enabled
- service accounts created
- Artifact Registry created
- billing budget and alerting created

Resources:
- `vpc-codex-core`
- `subnet-us-east1-core`
- `ip-execution-paper-us-east1`
- `sa-execution-runner`
- `sa-research-batch`
- `sa-orchestrator`
- `gs://codexalpaca-data-us`
- `gs://codexalpaca-artifacts-us`
- `gs://codexalpaca-control-us`
- `gs://codexalpaca-backups-us`

Exit criteria:
- infrastructure exists
- IAM boundaries are in place
- no workloads have moved yet

## Phase 1: Execution Plane Cut-In

Objective:
- move Alpaca-facing execution first

Steps:
- create `vm-execution-paper-01`
- assign the reserved static IP
- bootstrap runner dependencies
- move Alpaca and notification secrets to Secret Manager
- restore the paper-runner codebase onto the VM
- run validation only
- do not start live paper execution until readiness is clean

Required validations:
- tests pass
- runner can read secrets from Secret Manager
- runner writes session summary locally
- runner writes broker-order audit, broker activity audit, and ending broker-position snapshot
- outbound traffic comes from the reserved static IP

Exit criteria:
- the execution VM is ready to become the canonical paper runner

Rollback:
- continue using the current local execution machine
- keep the VM in validation-only mode

## Phase 2: Storage And Artifact Separation

Objective:
- stop treating local disks as the only durable runtime record

Steps:
- sync current control-plane packets into `gs://codexalpaca-control-us`
- sync session and research artifacts into `gs://codexalpaca-artifacts-us`
- move datasets and prepared inputs into `gs://codexalpaca-data-us`

Rules:
- GitHub remains the governance source of truth
- GCS becomes the runtime artifact and data substrate
- raw session exhaust belongs in GCS, not GitHub

Exit criteria:
- loss of one machine no longer means loss of project state

## Phase 3: Research Plane Migration

Objective:
- move heavy research and backtesting off a single workstation

Steps:
- containerize research jobs
- publish images to Artifact Registry
- launch discovery and exhaustive runs through Batch
- write all outputs to GCS
- keep promotion and live-manifest mutation out of the jobs

Recommended priority order:
1. coverage refresh
2. data materialization
3. discovery lanes
4. exhaustive lanes
5. shared-account validation

Exit criteria:
- at least one governed nightly research cycle can complete with research compute in GCP

Rollback:
- rerun the same cycle locally using the existing control-plane entrypoints

## Phase 4: Orchestration Migration

Objective:
- move the repeated job sequencing into managed orchestration

Steps:
- create nightly research workflow
- create post-session assimilation workflow
- create morning brief workflow
- trigger them with Cloud Scheduler
- keep governance packets and status outputs in GCS

Workflow boundaries:
- the workflow can launch and monitor jobs
- the workflow cannot approve live-manifest changes automatically

Exit criteria:
- nightly cycles and morning assimilation can run unattended

## Phase 5: Institutional Hardening

Objective:
- make the cloud stack resilient, observable, and auditable

Steps:
- persistent disk snapshots for execution VM
- bucket versioning and lifecycle policies
- alerting on runner heartbeat and reconciliation failures
- alerting on missing broker-order audit or broker-activity audit
- cost guardrails for Batch usage
- explicit restore runbooks

Exit criteria:
- the project can survive machine loss, job failure, and operator absence better than it can today

## Immediate Recommendation

Do not attempt a "big bang" migration.

The best next move is:

1. build the GCP foundation
2. move the paper runner to Compute Engine
3. keep research local until the execution VM is stable
4. then migrate research into Batch

That gives the highest reliability gain earliest, because the VPN/Alpaca path is the sharpest current risk.

## Bootstrap Bucket Guidance

The existing bucket:

- `gs://codexalpaca-transfer-922745393036`

should be treated as:

- bootstrap transfer
- safety backup
- workspace lift aid

It should not become the permanent control, artifact, or data bucket for the institutional runtime.

## Go / No-Go Rules

Go:
- once the execution VM can validate cleanly with the static IP and Secret Manager

No-Go:
- if the runner still depends on workstation-only secrets
- if the VM cannot produce a full trusted session bundle
- if GCS is being used as a raw dump without bucket role separation
- if research and live execution are still competing for the same runtime host
