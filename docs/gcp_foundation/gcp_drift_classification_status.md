# GCP Drift Classification

## Snapshot

- Generated at: `2026-04-23T15:03:36.961754-04:00`
- Project ID: `codexalpaca`
- Freeze state: `active`
- Phase 0 readiness: `classification_required`

## Immediate Operator Rules

- Do not create any new runner VM, service account, secret, bucket, or artifact repository until the drift classification is accepted.
- Do not start broker-facing execution from multi-ticker-trader-v1.
- Do not promote vm-execution-paper-01 to canonical execution until Phase 0 and Phase 1 are complete and a trusted validation session is clean.
- Treat the codified execution path as the only sanctioned path under active development.

## Resource Decisions

- `compute_instance` `vm-execution-paper-01`
  - classification: `sanctioned_validation_asset`
  - decision: `keep`
  - rationale: This is the codified validation execution VM on the governed rollout path and it already has a green headless validation gate.
- `compute_instance` `multi-ticker-trader-v1`
  - classification: `parallel_runtime_drift`
  - decision: `quarantine`
  - rationale: It is a second running broker-facing runtime path on default network with its own startup bootstrap, static IP, runtime secret, and container repo outside the codified execution rollout.
- `service_account` `multi-ticker-vm@codexalpaca.iam.gserviceaccount.com`
  - classification: `parallel_runtime_identity`
  - decision: `quarantine`
  - rationale: This service account exists only to support the unmanaged multi-ticker VM path and should not be treated as a sanctioned runtime identity until formally adopted.
- `secret` `multi-ticker-vm-env`
  - classification: `parallel_runtime_secret`
  - decision: `quarantine`
  - rationale: This secret feeds the unmanaged VM runtime path and should not be reused or expanded until the owning architecture decision is made.
- `bucket` `codexalpaca-runtime-us-central1`
  - classification: `parallel_runtime_storage`
  - decision: `quarantine`
  - rationale: This runtime bucket is outside the codified role-separated foundation. It is currently empty, which makes it a good candidate for explicit keep-or-delete review.
- `artifact_repository` `codexalpaca-containers`
  - classification: `parallel_runtime_artifacts`
  - decision: `quarantine`
  - rationale: This repository contains the unmanaged multi-ticker runtime image stream and is not yet governed by the codified execution pipeline.
- `network` `default`
  - classification: `network_drift`
  - decision: `retire_runtime_use`
  - rationale: Default VPC remains broad and currently hosts the unmanaged runtime VM. Institutional promotion requires runtime migration onto vpc-codex-core or explicit decommission.
- `iam_posture` `project_owner_assignments`
  - classification: `bootstrap_privilege_drift`
  - decision: `narrow`
  - rationale: Project-level Owner remains on service accounts, which is acceptable for bootstrap but not for steady-state runtime or operator posture.
- `bucket` `codexalpaca-transfer-922745393036`
  - classification: `bootstrap_transfer_storage`
  - decision: `keep_temporary`
  - rationale: This bucket is useful as a bootstrap transfer archive, but it is not part of the long-term governed runtime storage model and should later be lifecycle-managed or retired.
- `bucket` `codexalpaca_cloudbuild`
  - classification: `build_utility_storage`
  - decision: `formalize_or_retire`
  - rationale: This is a Cloud Build source bucket pattern rather than part of the runtime foundation. Keep it only if Cloud Build becomes part of the sanctioned deployment plane.

## Promotion Blockers

- A second unmanaged runtime path exists in GCP and has not yet been classified.
- Project-level Owner is still granted to service accounts.
- Default network is still active and still hosting runtime compute.
- There is no cloud-backed shared execution lease yet.

## Required Decisions

- Keep, migrate, or decommission multi-ticker-trader-v1.
- Keep or decommission the multi-ticker-vm identity and multi-ticker-vm-env secret.
- Keep or decommission codexalpaca-runtime-us-central1.
- Formalize or retire codexalpaca-containers and codexalpaca_cloudbuild.
- Define when default VPC can be considered empty enough to quarantine.
