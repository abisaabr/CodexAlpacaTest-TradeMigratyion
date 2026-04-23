# GCP Shared Execution Lease

This packet defines the recommended cloud coordination mechanism for shared paper execution.

## Objective

Replace the current human-memory rule:

"make sure the other machine is not running"

with a real cloud-backed lease that both sanctioned execution paths honor.

## Recommendation

Use a **Cloud Storage generation-match lease** first, backed by:

- `gs://codexalpaca-control-us/leases/paper-execution/lease.json`

## Why This Is The Right First Choice

- the control bucket already exists
- execution safety is needed now
- Firestore is not enabled in this project today
- Cloud Storage generation preconditions provide the compare-and-set behavior we need for a single-holder lease

## Lease Shape

The lease object should include:

- `owner_id`
- `machine_label`
- `runner_path`
- `git_commit`
- `acquired_at`
- `expires_at`

## Required Semantics

- acquire only if absent
- renew only if the caller still owns the current generation
- release only if the caller still owns the current generation
- stale takeover only through a controlled compare-and-set flow after expiry
- audit every lease state transition into the control bucket

## Future Upgrade Path

If the orchestration plane grows into Workflow/Scheduler/Batch-led coordination, we can revisit a Firestore transaction-based lease later. That is a future upgrade, not the first blocking dependency.
