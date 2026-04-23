# GCP Shared Execution Lease Contract

## Snapshot

- Generated at: `2026-04-23T15:17:09.919351-04:00`
- Project ID: `codexalpaca`
- Contract readiness: `ready_for_helper_implementation`
- Recommended lease: `gcs_generation_match_lease`
- Lease object: `gs://codexalpaca-control-us/leases/paper-execution/lease.json`

## Code Alignment

- current ownership module: `alpaca_lab/execution/ownership.py`
- current failover module: `alpaca_lab/execution/failover.py`
- current example config: `config/multi_ticker_paper_portfolio.yaml`

## Compatibility Mapping

- `owner_id` -> `owner_id`
  - decision: `preserve`
  - rationale: Existing runner logic already uses owner_id as the core holder identity.
- `owner_label` -> `owner_label`
  - decision: `preserve`
  - rationale: Useful for operator visibility and debugging across machines.
- `heartbeat_at` -> `heartbeat_at`
  - decision: `preserve`
  - rationale: Needed for liveness inspection and stale-lease analysis.
- `expires_at` -> `expires_at`
  - decision: `preserve`
  - rationale: TTL-based fail-closed behavior already exists conceptually and should remain first-class.
- `roles` -> `roles`
  - decision: `preserve`
  - rationale: Allows one holder to describe role-scoped subclaims without inventing a second coordination model.
- `(new)` -> `machine_label`
  - decision: `add`
  - rationale: Explicit machine_label improves cross-machine debugging and aligns with current runtime env conventions.
- `(new)` -> `runner_path`
  - decision: `add`
  - rationale: Needed to distinguish workstation, VM, and future workflow execution paths.
- `(new)` -> `git_commit`
  - decision: `add`
  - rationale: Supports forensic traceability between lease holder and code revision.
- `(new)` -> `audit_context`
  - decision: `add`
  - rationale: Supports future cloud-native audit packets and differentiated control handling.

## Operation Contract

- `acquire`
  - mechanism: GCS object create with ifGenerationMatch=0
  - success: object did not previously exist and caller becomes the sole current holder
  - failure: precondition failure if object already exists
- `renew`
  - mechanism: GCS object rewrite with ifGenerationMatch=<last_seen_generation>
  - success: caller still owns the current generation and extends heartbeat/expires_at
  - failure: precondition failure if another holder replaced or stole the lease
- `release`
  - mechanism: GCS object delete with ifGenerationMatch=<last_seen_generation>
  - success: lease removed only by the current holder
  - failure: precondition failure if generation has changed
- `steal_after_expiry`
  - mechanism: read current object, verify expiry, then rewrite with ifGenerationMatch=<expired_generation>
  - success: expired lease is replaced atomically by the new holder
  - failure: precondition failure if another actor renewed or stole first

## Validation Matrix

- Acquire succeeds when no lease object exists.
- Concurrent acquire attempts result in exactly one success and one precondition failure.
- Renew succeeds for the current holder and bumps heartbeat/expires_at.
- Renew fails when the caller uses a stale generation.
- Release succeeds only for the current holder generation.
- Release fails for a stale generation.
- Steal after expiry succeeds only when the observed generation still matches the expired lease.
- Steal after expiry fails if the original holder renewed before the replace.
- Audit artifact is written for acquire, renew, release, and steal events.
- Dry-run mode exercises the state machine without enabling broker-facing execution.

## Rollout Steps

- Publish the lease contract and validation matrix.
- Implement helper functions in the sanctioned runner code paths without enforcing them yet.
- Add dry-run tests for contention, stale renewal, release mismatch, and expired steal.
- Enable audit artifact emission for every lease transition.
- Turn on enforcement only after dry-run validation is green on both workstation and VM paths.
