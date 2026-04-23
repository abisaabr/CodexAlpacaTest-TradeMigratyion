# GCP IAM Change Window Pack

## Snapshot

- Generated at: `2026-04-23T15:11:03.600885-04:00`
- Project ID: `codexalpaca`
- Change ID: `gcp-iam-change-window-20260423`
- Change state: `prepared_not_executed`
- Scope: `project_level_owner_removal_for_service_accounts_only`

## Target Removals

- `serviceAccount:ramzi-service-account@codexalpaca.iam.gserviceaccount.com` -> `roles/owner`
  - reason: Step down operator automation principal from project-wide Owner to minimal operator access.
- `serviceAccount:sa-bootstrap-admin@codexalpaca.iam.gserviceaccount.com` -> `roles/owner`
  - reason: Convert bootstrap identity away from standing Owner after foundation setup.

## Prechecks

- Confirm the temporary parallel-runtime exception is still understood and no migration/decommission work is in flight.
- Confirm no bootstrap or provisioning task is currently depending on project-wide Owner through ramzi-service-account or sa-bootstrap-admin.
- Confirm operator access is already present through IAP, OS Login, and Compute Viewer for ramzi-service-account.
- Capture a fresh project IAM policy snapshot before any mutation.
- Use an explicit change window and do not combine this step with broker-facing execution changes.

## Execution Commands

- `gcloud projects get-iam-policy codexalpaca --format=json > codexalpaca_iam_policy_before.json`
- `gcloud projects remove-iam-policy-binding codexalpaca --member="serviceAccount:ramzi-service-account@codexalpaca.iam.gserviceaccount.com" --role="roles/owner"`
- `gcloud projects remove-iam-policy-binding codexalpaca --member="serviceAccount:sa-bootstrap-admin@codexalpaca.iam.gserviceaccount.com" --role="roles/owner"`
- `gcloud projects get-iam-policy codexalpaca --format=json > codexalpaca_iam_policy_after.json`

## Rollback Commands

- `gcloud projects add-iam-policy-binding codexalpaca --member="serviceAccount:ramzi-service-account@codexalpaca.iam.gserviceaccount.com" --role="roles/owner"`
- `gcloud projects add-iam-policy-binding codexalpaca --member="serviceAccount:sa-bootstrap-admin@codexalpaca.iam.gserviceaccount.com" --role="roles/owner"`

## Postchecks

- Rebuild gcp_iam_hardening_status and confirm the two service accounts no longer appear in project_owner_principals.
- Rebuild gcp_project_state_audit_status and confirm audit posture improves or at minimum does not regress.
- Rebuild gcp_parallel_runtime_exception_status and confirm the exception is still documented and bounded.
- Publish the post-change packets to GitHub main and gs://codexalpaca-control-us before resuming broader work.

## Hard Rules

- Do not include the human owner principal in this first cutover unless separately reviewed.
- Do not change quarantined multi-ticker-vm privileges during this change window.
- Do not combine IAM hardening with first trusted validation-session execution.
- Always take before-and-after IAM snapshots.
