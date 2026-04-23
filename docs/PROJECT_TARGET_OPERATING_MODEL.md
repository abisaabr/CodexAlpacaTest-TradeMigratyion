# Project Target Operating Model

This document is the canonical target-state packet for the `codexalpaca` project.

It defines what we are building in Google Cloud, how the planes should interact, what "institutional grade" means for this project, and how to judge progress without confusing partial infrastructure for a finished operating model.

## Mission

Build a governed cloud-native paper-trading lab that:

- scales research breadth and backtesting speed
- preserves strict execution discipline
- turns broker-facing evidence into policy updates
- minimizes operational ambiguity and dual-writer risk
- can survive workstation loss, VPN instability, and operator absence

## Core Loop

The project should operate as:

1. research
2. validate
3. trade
4. assimilate
5. repeat

Each loop should leave behind enough evidence that the next cycle can be governed by observed reality instead of memory or optimism.

## Target Architecture

The project should be a five-plane system.

### 1. Governance Plane

System of record:

- GitHub

Purpose:

- policies
- manifests
- promotion decisions
- handoffs
- operating runbooks
- canonical architecture and control packets

Rules:

- GitHub is the governance truth
- no raw trade exhaust belongs here
- no cloud job approves live-manifest mutation automatically

### 2. Control Plane

Primary services:

- Cloud Scheduler
- Workflows

Purpose:

- launch and gate nightly research
- launch and gate post-session assimilation
- launch and gate morning brief refresh
- sequence jobs based on artifact presence and status outputs

Rules:

- orchestration executes the plan, not the policy
- workflows may launch and monitor, but not auto-promote live strategy changes

### 3. Research Plane

Primary service:

- Cloud Batch

Purpose:

- ticker research
- option research
- strategy research
- backtesting
- coverage refresh
- discovery waves
- exhaustive validation waves

Rules:

- jobs are reproducible and stateless except for declared inputs and outputs
- outputs land in GCS
- research jobs do not mutate the live manifest

### 4. Execution Plane

Primary service:

- Compute Engine

Purpose:

- run the sanctioned paper trader
- maintain stable outbound identity to Alpaca
- produce trusted broker-audited session evidence

Rules:

- exactly one sanctioned execution path
- exactly one effective writer at a time
- outbound traffic should come from the reserved static IP
- secrets must come from Secret Manager
- execution is promoted by evidence, not by existence of a VM

### 5. Storage And Observability Plane

Primary services:

- Cloud Storage
- Cloud Logging
- Cloud Monitoring

Purpose:

- datasets
- artifacts
- control packets
- backups
- alerts
- health and reconciliation visibility

Rules:

- GCS is the runtime artifact and data substrate
- GitHub is not the raw artifact store
- control and backup buckets should be versioned

## Institutional Definition Of Success

The project is institutional grade when all of the following are true:

- research is parallel, reproducible, and cloud-backed
- execution is singular, auditable, and cloud-governed
- session evidence flows back into calibration and unlock policy automatically
- secrets are no longer anchored to workstation-local `.env` files
- architecture drift is either codified or explicitly quarantined
- cloud promotion decisions are made by gates and evidence, not operator convenience

## Current Reality

Current project posture:

- `foundation_present_with_material_drift`

Strongest controlled assets:

- `vm-execution-paper-01`
- role-separated buckets
- Secret Manager foundation
- sanctioned runtime service accounts
- green headless validation gate
- trusted validation-session gate
- shared execution lease design and implementation seam

Current material weaknesses:

- temporary parallel runtime exception remains active
- project-level `Owner` is still granted to service accounts
- the default network remains present and permissive
- Workflows, Scheduler, and Batch are enabled but not yet the real operating backbone
- the cloud-backed shared execution lease is not yet live
- trusted unlock-grade execution evidence is still missing

## Decision Rules

### Promote Execution Only If

- architecture drift is frozen or resolved
- IAM is narrowed appropriately
- the shared execution lease is live and validated
- the sanctioned execution VM produces a clean trusted validation session
- post-session assimilation confirms the evidence is trustworthy

### Do Not Promote Execution Because

- a VM exists
- a static IP exists
- secrets are in Secret Manager
- headless validation passed

Those are necessary but not sufficient.

### Migrate Research Only After

- execution governance is stable enough that research migration will not distract from execution safety
- Artifact Registry and Batch packaging are in sanctioned use
- control packets can govern Batch output the same way they govern local output now

## Phase Model

### Phase 0: Foundation And Drift Freeze

Goal:

- know exactly what exists
- freeze unmanaged sprawl

Exit:

- sanctioned path is identified
- parallel path is either quarantined or codified

### Phase 1: IAM Hardening

Goal:

- remove bootstrap-era privilege from steady-state identities

Exit:

- service accounts no longer hold project-level `Owner`
- least-privilege runtime posture is real

### Phase 2: Shared Execution Control

Goal:

- eliminate operator-memory exclusivity

Exit:

- cloud-backed shared execution lease is live
- acquire / renew / release / stale takeover are validated

### Phase 3: Trusted Validation Session

Goal:

- prove the sanctioned execution VM can generate trustworthy broker-audited evidence

Exit:

- trusted validation session bundle exists
- reconciliation and assimilation packets are clean enough to inform policy

### Phase 4: Canonical Execution Promotion

Goal:

- make one cloud execution path primary

Exit:

- one sanctioned execution path
- any surviving parallel path is either decommissioned or explicitly temporary and bounded

### Phase 5: Research Migration

Goal:

- move research and backtesting into Batch without increasing execution risk

Exit:

- at least one governed nightly cycle completes with research compute in GCP

### Phase 6: Orchestration Migration

Goal:

- make the daily loop managed and repeatable

Exit:

- Workflows + Scheduler operate the core cycle

### Phase 7: Hardening And DR

Goal:

- survive failures cleanly

Exit:

- alerts, snapshots, retention, budgets, restore paths, and runbooks are in place

## Optimization Priorities

The project should optimize in this order:

1. execution safety
2. evidence quality
3. research throughput
4. orchestration automation
5. cost efficiency

That ordering matters because raw speed without execution governance just creates faster drift and faster mistakes.

## What Maximizes Profit

- broader governed research search in Batch
- better family diversification beyond current live concentration
- execution evidence feeding tournament unlock and calibration
- promotion of higher-value profiles only when they are truly executable

## What Minimizes Loss

- single sanctioned execution writer
- broker-audited session bundles
- strict session reconciliation
- conservative posture while evidence is weak
- explicit unlock floors before activating higher-risk profiles

## What Both Machines Should Assume

- the sanctioned cloud execution path is `vm-execution-paper-01`
- the parallel runner is tolerated only under explicit exception control
- the shared execution lease is not live until a sanctioned GCS-backed store is wired and validated
- the next major promotion step is execution governance, not architecture expansion
- every material change should be logged to GitHub `main` and `gs://codexalpaca-control-us`

## Practical North Star

The finished project should feel like this:

- research runs anywhere appropriate
- execution runs in one governed place
- evidence comes back automatically
- policy updates from evidence
- higher-risk profiles unlock only when execution proves them
- every major decision is traceable

That is what we are building.
