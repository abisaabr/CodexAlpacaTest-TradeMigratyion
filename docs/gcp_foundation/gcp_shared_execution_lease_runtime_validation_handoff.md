# GCP Shared Execution Lease Runtime Validation Handoff

## Current Read

- Runtime validation status: `validated_not_enforced`.
- Latest review state: `passed`.
- The cloud shared execution lease is still off by default.

## Operator Rule

- Treat runtime validation as a governance gate, not as automatic permission to switch the trader onto the cloud lease.
- Keep broker-facing execution on the sanctioned path only after the dry-run and trusted-session gates are both clean.
