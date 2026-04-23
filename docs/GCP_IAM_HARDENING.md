# GCP IAM Hardening

This packet defines **Phase 1** of the GCP institutionalization plan: step down bootstrap-era privilege and leave only explicit, minimal operator and runtime access.

## Objective

- remove project-level `Owner` from service accounts
- preserve operator access through explicit minimal roles
- prevent quarantined runtime identities from becoming accidental sanctioned identities

## Why This Matters

Bootstrap projects often use broad privilege to move quickly. That is acceptable for setup, but it is not institutional steady state.

In `codexalpaca`, the primary IAM hardening goal is straightforward:

- runtime and operator identities should be narrow
- bootstrap identities should not remain standing owners

## Target Direction

### `ramzi-service-account`

Treat as an operator automation principal, not a project owner. It should keep only the roles it actually needs for:

- IAP access
- OS Login
- Compute visibility
- service-account use on sanctioned runtime identities when necessary

### `sa-bootstrap-admin`

Treat as temporary or break-glass only. It should not remain a standing project owner after bootstrap is complete.

### Runtime service accounts

Keep these narrow and purpose-specific:

- `sa-execution-runner`
- `sa-research-batch`
- `sa-orchestrator`
- `sa-ci-deployer`

### Quarantined identities

Do not expand these while the drift decision is unresolved:

- `multi-ticker-vm@codexalpaca.iam.gserviceaccount.com`

## Change Discipline

IAM hardening should happen only in a deliberate change window:

1. take a policy snapshot
2. confirm no bootstrap work is still in flight
3. remove one broad role at a time
4. rerun the audit packet immediately after
5. stop if operator or runtime access changes unexpectedly

## Hard Rules

- do not widen runtime identities to solve operator-access issues
- do not grant new broad privilege to quarantined identities
- do not remove access blindly without a rollback path
- rerun the project-state audit after every IAM hardening step
