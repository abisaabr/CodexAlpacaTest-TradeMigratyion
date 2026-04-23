# GCP Shared Execution Lease Contract Handoff

## Current Read

- The lease design is now implementation-ready.
- The cloud lease should preserve the current ownership semantics instead of inventing a second coordination model.
- The next step is helper implementation in the sanctioned runner paths with enforcement still off by default.

## Key Rule

- Preserve `owner_id`, `owner_label`, `heartbeat_at`, `expires_at`, and `roles` semantics from the current file lease.
- Add `machine_label`, `runner_path`, and `git_commit` for cloud traceability.

## Next Build Step

- Implement `acquire`, `renew`, `release`, and `steal_after_expiry` helpers against GCS generation preconditions in dry-run mode first.
