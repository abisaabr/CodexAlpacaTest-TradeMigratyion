# GCP Runtime Security

This guide defines the institutional runtime-security layer for the Google Cloud deployment.

The goal is:

- move secret values out of workstation-local `.env`
- bind runtime identities only to the buckets and secrets they need
- seed the initial cloud runtime safely from the current paper-only local environment

## Runtime Secret Scope

The first cloud runtime should treat these as secrets:

- Alpaca paper API key
- Alpaca paper secret key
- Discord webhook URL
- ntfy access token if used
- email password if used

Non-secret config such as:

- paper endpoint URL
- timezone
- topics
- email addresses
- ownership lease path

can remain in config files, instance metadata, or control packets unless we later decide to centralize all runtime config.

## Secret Manager Naming

Current target names:

- `execution-alpaca-paper-api-key`
- `execution-alpaca-paper-secret-key`
- `notification-discord-webhook-url`
- `notification-ntfy-access-token`
- `notification-email-password`

## Runtime Identities

### `sa-execution-runner`

Should have:

- Secret Manager access to execution and notification secrets it actually uses
- artifact write access
- control write access
- backup write access
- logging and metrics write access

### `sa-research-batch`

Should have:

- data read access
- artifact write access
- control read access
- logging and metrics write access
- Artifact Registry read access for research images

### `sa-orchestrator`

Should have:

- control write access
- artifact read access
- logging and metrics write access

Batch-launch and service-account impersonation bindings can be added when workflows and Batch jobs are actually created.

### `sa-ci-deployer`

Should have:

- Artifact Registry write access

## Builder

Use:

- `cleanroom/code/qqq_options_30d_cleanroom/bootstrap_gcp_runtime_security.py`

Outputs:

- `docs/gcp_foundation/gcp_runtime_security_status.json`
- `docs/gcp_foundation/gcp_runtime_security_status.md`

## Current Phase 0 Note

The current bootstrap path seeds the secrets correctly, but the Secret Manager REST IAM method for per-secret bindings is returning `404` in this environment. Until we move that binding path to a client flow that supports per-secret IAM cleanly, the bootstrap falls back to:

- project-level `roles/secretmanager.secretAccessor` for `sa-execution-runner`

That is acceptable for the current narrow runtime because the project is still in bootstrap mode and the runtime secret set is intentionally small. It should still be revisited once the execution VM is live and the runtime footprint is stable.

## Hard Rules

- never print or commit secret values
- do not store long-lived secrets in GitHub
- do not overgrant the runtime service accounts just because the bootstrap identity is broad
- treat the bootstrap service account as temporary setup power, not as the final runtime identity
