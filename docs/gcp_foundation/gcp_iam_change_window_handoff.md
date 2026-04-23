# GCP IAM Change Window Handoff

## Current Read

- The IAM change pack is ready.
- It is intentionally non-destructive until an explicit change window is opened.
- The first cutover removes project-level Owner only from the two service accounts, not from the human owner principal.

## Execute Only When

- no bootstrap activity is in flight
- the temporary parallel-runtime exception is still frozen
- the operator is ready to rerun the audit immediately after the change

## First Commands

- `gcloud projects get-iam-policy codexalpaca --format=json > codexalpaca_iam_policy_before.json`
- `gcloud projects remove-iam-policy-binding codexalpaca --member="serviceAccount:ramzi-service-account@codexalpaca.iam.gserviceaccount.com" --role="roles/owner"`
- `gcloud projects remove-iam-policy-binding codexalpaca --member="serviceAccount:sa-bootstrap-admin@codexalpaca.iam.gserviceaccount.com" --role="roles/owner"`

## Rule

- Do not mix this IAM cutover with first trusted validation-session execution. Keep privilege hardening and broker-facing validation as separate controlled events.
