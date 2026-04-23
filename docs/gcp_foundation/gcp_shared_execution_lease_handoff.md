# GCP Shared Execution Lease Handoff

## Current Read

- The lease design is ready, but not yet implemented.
- The recommended first implementation is a GCS generation-match lease in the control bucket.
- Firestore is not enabled, so it should not be the immediate dependency for execution safety.

## Operator Rule

- Keep using explicit exclusive execution windows until the lease is implemented and enforced.
- Do not run concurrent broker-facing sessions across machines until lease enforcement exists.

## Next Build Step

- Implement lease helpers in the sanctioned runner paths and validate them in dry-run mode before turning on enforcement.
