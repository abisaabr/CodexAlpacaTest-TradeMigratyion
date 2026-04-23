# GCP Foundation Readiness

This guide defines how to measure whether the current Google Cloud project and credential set are actually ready for the institutional cloud rollout.

The purpose is to avoid confusing:

- "we can upload files to Cloud Storage"

with:

- "we can provision and operate the institutional cloud stack"

## Why This Matters

A storage-capable service account is useful for bootstrap transfer and backups, but it is not automatically sufficient for:

- Compute Engine
- Secret Manager
- Artifact Registry
- Cloud Batch
- Workflows
- Cloud Scheduler

Those capabilities need to be checked explicitly before we call the project cloud-ready.

## Builder Chain

Use:

- `cleanroom/code/qqq_options_30d_cleanroom/build_gcp_foundation_readiness.py`
- `cleanroom/code/qqq_options_30d_cleanroom/build_gcp_foundation_readiness_handoff.py`

Outputs:

- `docs/gcp_foundation/gcp_foundation_readiness.json`
- `docs/gcp_foundation/gcp_foundation_readiness.md`
- `docs/gcp_foundation/gcp_foundation_readiness_handoff.json`
- `docs/gcp_foundation/gcp_foundation_readiness_handoff.md`

## Status Meanings

### `credentials_blocked`

The provided service-account key cannot mint a token or is otherwise unusable.

### `bootstrap_storage_only`

The credential can work with Cloud Storage but cannot currently support the broader institutional foundation.

This usually means:

- bootstrap transfer is possible
- durable backup is possible
- foundation provisioning still requires a higher-privilege bootstrap identity

### `foundation_partial`

Some required cloud services are available, but the foundation is still incomplete.

### `foundation_ready`

The credential or current project access is broad enough to proceed with the defined Phase 0 foundation rollout.

## Hard Rule

Do not treat the bootstrap transfer bucket as proof that the project is ready for cloud cutover.

The correct readiness check is the generated handoff, not intuition.
