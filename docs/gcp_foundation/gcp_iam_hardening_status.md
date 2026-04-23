# GCP IAM Hardening Status

## Snapshot

- Generated at: `2026-04-23T15:06:35.659197-04:00`
- Project ID: `codexalpaca`
- Phase 1 readiness: `change_window_required`

## Project Owner Principals

- `serviceAccount:ramzi-service-account@codexalpaca.iam.gserviceaccount.com`
- `serviceAccount:sa-bootstrap-admin@codexalpaca.iam.gserviceaccount.com`
- `user:abisaabr19@gmail.com`

## Current Roles By Principal

- `serviceAccount:ramzi-service-account@codexalpaca.iam.gserviceaccount.com`
  - `roles/compute.osAdminLogin`
  - `roles/compute.viewer`
  - `roles/iap.tunnelResourceAccessor`
  - `roles/owner`
- `serviceAccount:sa-bootstrap-admin@codexalpaca.iam.gserviceaccount.com`
  - `roles/owner`
- `serviceAccount:sa-execution-runner@codexalpaca.iam.gserviceaccount.com`
  - `roles/artifactregistry.reader`
  - `roles/logging.logWriter`
  - `roles/monitoring.metricWriter`
  - `roles/secretmanager.secretAccessor`
- `serviceAccount:sa-research-batch@codexalpaca.iam.gserviceaccount.com`
  - `roles/artifactregistry.reader`
  - `roles/logging.logWriter`
  - `roles/monitoring.metricWriter`
- `serviceAccount:sa-orchestrator@codexalpaca.iam.gserviceaccount.com`
  - `roles/logging.logWriter`
  - `roles/monitoring.metricWriter`
- `serviceAccount:sa-ci-deployer@codexalpaca.iam.gserviceaccount.com`
  - `roles/artifactregistry.writer`
- `serviceAccount:multi-ticker-vm@codexalpaca.iam.gserviceaccount.com`
  - `roles/artifactregistry.reader`
  - `roles/logging.logWriter`
  - `roles/monitoring.metricWriter`
  - `roles/secretmanager.secretAccessor`
  - `roles/storage.objectAdmin`
- `user:abisaabr19@gmail.com`
  - `roles/compute.osAdminLogin`
  - `roles/owner`

## Recommended Actions

- `serviceAccount:ramzi-service-account@codexalpaca.iam.gserviceaccount.com`
  - target state: `operator_access_only`
  - must remove: `roles/owner`
  - recommended standing roles: `roles/iap.tunnelResourceAccessor, roles/compute.osAdminLogin, roles/compute.viewer`
  - rationale: This principal is acting like an operator identity and should not keep project-wide Owner in steady state.
- `serviceAccount:sa-bootstrap-admin@codexalpaca.iam.gserviceaccount.com`
  - target state: `break_glass_only`
  - must remove: `roles/owner`
  - rationale: Bootstrap power should not remain standing after foundation setup. Preserve only as a documented break-glass path if still needed.
- `serviceAccount:sa-execution-runner@codexalpaca.iam.gserviceaccount.com`
  - target state: `runtime_scoped`
  - recommended standing roles: `roles/artifactregistry.reader, roles/logging.logWriter, roles/monitoring.metricWriter, roles/secretmanager.secretAccessor`
  - rationale: This is the sanctioned runtime identity and should remain narrowly scoped to execution runtime needs.
- `serviceAccount:sa-research-batch@codexalpaca.iam.gserviceaccount.com`
  - target state: `research_scoped`
  - recommended standing roles: `roles/artifactregistry.reader, roles/logging.logWriter, roles/monitoring.metricWriter`
  - rationale: This is the sanctioned research runtime identity and should stay limited to research execution needs.
- `serviceAccount:sa-orchestrator@codexalpaca.iam.gserviceaccount.com`
  - target state: `orchestration_scoped`
  - recommended standing roles: `roles/logging.logWriter, roles/monitoring.metricWriter`
  - rationale: This identity should grow only through codified Workflows/Scheduler/Batch orchestration, not bootstrap privilege.
- `serviceAccount:sa-ci-deployer@codexalpaca.iam.gserviceaccount.com`
  - target state: `delivery_scoped`
  - recommended standing roles: `roles/artifactregistry.writer`
  - rationale: This identity is appropriately narrow if Cloud Build or formal CI deployment becomes part of the sanctioned delivery path.
- `serviceAccount:multi-ticker-vm@codexalpaca.iam.gserviceaccount.com`
  - target state: `quarantined_until_decision`
  - rationale: This identity belongs to the unmanaged parallel runtime and should not gain any additional privilege until that path is formally adopted or removed.
- `user:abisaabr19@gmail.com`
  - target state: `human_admin_review`
  - recommended standing roles: `roles/compute.osAdminLogin`
  - rationale: Human admin posture should be reviewed separately from runtime identities. Project Owner on a human can remain temporarily during bootstrap, but it should still be intentionally reviewed.

## Safe Cutover Order

- Take and store a fresh IAM policy snapshot before any mutation.
- Confirm no bootstrap work is still in flight and no operator is depending on service-account Owner access.
- Remove roles/owner from ramzi-service-account after confirming operator access is intact through IAP, OS Login, and serviceAccountUser on sanctioned runtime identities.
- Remove roles/owner from sa-bootstrap-admin or convert it into an explicit break-glass identity with no standing use.
- Re-run the IAM hardening packet and the GCP project-state audit immediately after the role changes.
- Do not touch runtime-scoped service-account roles until the sanctioned execution session and orchestration plan are stable.

## Blockers

- ramzi-service-account still has project-level Owner.
- sa-bootstrap-admin still has project-level Owner.
- The quarantined multi-ticker-vm identity is still live in the project and should not be expanded before drift resolution.

## Hard Rules

- Do not remove Owner from service accounts during an unknown bootstrap or deployment window.
- Do not grant new broad roles to quarantined identities.
- Do not widen runtime identities to solve operator-access problems.
- Re-run the project-state audit after every IAM hardening step.
