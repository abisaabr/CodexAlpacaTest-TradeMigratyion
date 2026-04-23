# GCP Shared Execution Lease Contract

This packet turns the shared-execution lease from a design choice into an implementation contract.

## Design Principle

The cloud lease should **extend** the current runner ownership model, not replace it with a second incompatible one.

The current file-based lease already uses:

- `owner_id`
- `owner_label`
- `heartbeat_at`
- `expires_at`
- `roles`

Those semantics should remain the backbone of the cloud lease.

## Cloud Additions

The cloud lease should add only what the distributed environment needs for stronger traceability:

- `machine_label`
- `runner_path`
- `git_commit`
- `audit_context`

## Storage Contract

Recommended object:

- `gs://codexalpaca-control-us/leases/paper-execution/lease.json`

Required preconditions:

- acquire: `ifGenerationMatch=0`
- renew: `ifGenerationMatch=<last_seen_generation>`
- release: `ifGenerationMatch=<last_seen_generation>`
- steal-after-expiry: replace only if the observed expired generation still matches

## Validation Rule

Do not turn lease enforcement on until:

- helper logic exists in both sanctioned runner paths
- dry-run contention tests are green
- audit artifact emission is working for every lease state transition
