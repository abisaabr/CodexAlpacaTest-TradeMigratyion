# GCP Institutionalization Plan

This plan turns the current `codexalpaca` cloud project from a promising foundation into an institutional-grade operating environment.

## Current Read

The project is no longer empty or hypothetical. It has:

- a codified validation-grade execution foundation
- role-separated storage buckets
- runtime identities
- Secret Manager containers
- a green headless validation gate on `vm-execution-paper-01`

But it is **not yet institutional-grade** because the live project also contains unmanaged drift and overly broad permissions.

The two biggest truths are:

1. the codified execution path is strong
2. the total cloud estate is not yet fully governed

## Phase 0: Freeze And Classify Drift

Objective:

- decide what is sanctioned and what is not

Required work:

- classify `multi-ticker-trader-v1`
- classify `multi-ticker-vm`
- classify `multi-ticker-vm-env`
- classify `codexalpaca-runtime-us-central1`
- classify `codexalpaca-containers`
- classify whether the default VPC is still allowed to host anything

Exit criteria:

- every current resource is either:
  - codified and sanctioned
  - quarantined
  - scheduled for decommission

## Phase 1: Identity And IAM Hardening

Objective:

- remove bootstrap-era privilege from steady-state runtime

Required work:

- remove project-level `Owner` from service accounts
- narrow `ramzi-service-account` to the minimum operator roles
- keep `sa-bootstrap-admin` temporary or convert it into a break-glass bootstrap identity only
- split bootstrap roles from runtime roles explicitly
- document which principals are human operators, automation principals, and runtime identities

Exit criteria:

- no runtime service account holds `Owner`
- bootstrap privilege is temporary or break-glass only
- operator access is explicit and minimal

## Phase 2: Network And Host Boundary Hardening

Objective:

- make the network story as governed as the VM story

Required work:

- adopt `vpc-codex-core` as the sanctioned runtime network
- quarantine or retire default-network usage
- define the only allowed public-IP footprint
- keep SSH restricted to IAP
- add explicit firewall and route documentation for every runtime host
- decide whether the old `multi-ticker-trader-v1` host survives, migrates, or is removed

Exit criteria:

- default-network dependence is gone or explicitly quarantined
- every surviving host is on a sanctioned network path

## Phase 3: Execution Plane Promotion Discipline

Objective:

- promote the cloud execution VM only through evidence, not enthusiasm

Required work:

- run the first trusted validation paper session on `vm-execution-paper-01`
- require the full evidence packet:
  - broker-order audit
  - broker account-activity audit
  - ending broker-position snapshot
  - shutdown reconciliation
  - completed trade table with broker/local cashflow comparison
- run governed post-session assimilation immediately after
- only then decide whether the VM becomes canonical paper execution

Important note:

- until we add a cloud-backed shared execution lease, the first trusted session must happen in an explicitly exclusive paper-account window

Exit criteria:

- at least one trusted validation session is clean
- promotion decision is documented

## Phase 4: Shared Execution Control

Objective:

- eliminate operator-memory coordination for shared-account safety

Required work:

- replace the current filesystem-era exclusivity assumption with a cloud-backed execution lease
- choose one sanctioned coordination primitive, for example:
  - GCS lease object with CAS-style semantics
  - Firestore document lease
  - Cloud SQL row lock if broader relational state is introduced later
- make both workstation and VM runners honor the same shared control

Exit criteria:

- exclusive execution no longer depends on a human saying "the other box is off"

## Phase 5: Orchestration Plane

Objective:

- turn enabled APIs into a governed operating system

Required work:

- formalize Cloud Build image publication
- formalize Artifact Registry image lifecycle
- build Workflows for:
  - VM validation launches
  - trusted session launches
  - post-session assimilation
- add Cloud Scheduler triggers for the sanctioned workflows
- formalize Batch-backed research jobs rather than leaving research-cloud capability merely enabled

Exit criteria:

- execution and research launches happen through sanctioned workflows, not ad hoc commands

## Phase 6: Observability And SRE Layer

Objective:

- make failures visible before they become surprises

Required work:

- structured logs for execution and orchestration
- log-based alerts for validation/session failures
- uptime and heartbeat alerts for the execution VM
- budget and billing alerts
- retention and lifecycle rules on buckets
- operator dashboards or compact daily packets

Exit criteria:

- cloud failure modes are observable, alertable, and reviewable

## Phase 7: Disaster Recovery And Decommission Discipline

Objective:

- make continuity and cleanup as intentional as creation

Required work:

- define backup retention for state and evidence
- define rollback path from cloud VM back to workstation if needed
- define decommission procedure for unsanctioned resources
- require asset inventory updates whenever new runtime resources are introduced

Exit criteria:

- rollback and retirement are governed, not improvised

## Recommended Order From Here

1. Finish Phase 0 and classify the drift resources.
2. Execute Phase 1 and remove `Owner` from service accounts.
3. Run the first trusted validation paper session in an exclusive window.
4. Build the shared execution lease.
5. Only then promote the VM to canonical paper execution.
6. After execution is stable, formalize Workflows, Scheduler, and Batch for full cloud operations.
