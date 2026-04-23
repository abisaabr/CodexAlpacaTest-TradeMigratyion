# GCP Shared Execution Lease

## Snapshot

- Generated at: `2026-04-23T15:14:22.962775-04:00`
- Project ID: `codexalpaca`
- Lease readiness: `design_ready_not_implemented`
- Recommended lease: `gcs_generation_match_lease`
- Firestore enabled: `False`
- Control bucket present: `True`

## Recommendation

- Use a Cloud Storage generation-match lease in `codexalpaca-control-us` first.
- Do not wait for Firestore to solve the immediate execution-safety problem.

## Lease Options

- `gcs_generation_match_lease`
  - status: `recommended_now`
  - pro: Uses infrastructure already present in the codified control plane.
  - pro: Does not require enabling a new stateful database service.
  - pro: Supports compare-and-set semantics through Cloud Storage generation preconditions.
  - pro: Fits well with the existing control bucket and packet model.
  - con: Requires careful lease content design and expiry handling.
  - con: Is less expressive than a transactional document store for multi-step orchestration later.
  - bucket: `codexalpaca-control-us`
  - object: `gs://codexalpaca-control-us/leases/paper-execution/lease.json`
  - acquire: Create only if absent using ifGenerationMatch=0.
  - renew: Rewrite only if the stored generation matches the caller's last-seen generation.
  - release: Delete only if the stored generation matches the caller's last-seen generation.
  - expiry field: `expires_at`
- `firestore_transaction_lease`
  - status: `future_upgrade_only`
  - pro: Offers richer transactional semantics for orchestration-heavy coordination.
  - pro: Would be a cleaner long-term fit if Workflows, Scheduler, and multi-step cloud orchestration become primary.
  - con: Cloud Firestore API is not enabled in this project today.
  - con: Adds a new operational surface area before the basic lease problem is solved.
  - con: Would slow down convergence on the immediate execution-safety control.

## Immediate Design Rules

- Only one broker-facing paper execution holder may own the lease at a time.
- Lease acquisition must be atomic and must fail closed on contention.
- Lease records must include expiry and ownership metadata.
- Expired leases may be stolen only through an explicit compare-and-set flow, never by blind overwrite.
- Every acquire, renew, release, and steal event should write an audit artifact into the control bucket.

## Phased Rollout

- Phase A: design and publish the GCS lease contract.
- Phase B: implement lease helpers in both workstation and VM runners without enabling them by default.
- Phase C: validate acquire, renew, release, stale-expiry, and conflict handling in dry-run mode.
- Phase D: turn lease enforcement on for broker-facing paper execution.
- Phase E: reassess whether Firestore is needed after orchestration matures.
