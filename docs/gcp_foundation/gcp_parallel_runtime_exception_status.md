# GCP Parallel Runtime Exception

## Snapshot

- Generated at: `2026-04-23T15:08:55.928427-04:00`
- Project ID: `codexalpaca`
- Exception ID: `parallel-runtime-exception-2026-04-23`
- Exception state: `active_temporary_exception`

## Sanctioned Path

- Primary asset: `vm-execution-paper-01`
- The codified execution-validation path under the governed rollout.

## Temporary Exception Assets

- `multi-ticker-trader-v1`
- `multi-ticker-vm@codexalpaca.iam.gserviceaccount.com`
- `multi-ticker-vm-env`
- `codexalpaca-runtime-us-central1`
- `codexalpaca-containers`

## Reason

- A currently running parallel runner path will remain in place for now while it is documented, frozen, and evaluated for migration or decommission.

## Compensating Controls

- Do not create any additional runner VM, runtime secret, runtime bucket, or runtime service account for the parallel path.
- Do not widen IAM privileges for the parallel path while the exception is active.
- Record every material change related to the parallel path in GitHub main and in the GCS control bucket.
- Do not promote vm-execution-paper-01 to canonical execution while the exception remains unresolved.
- Do not run broker-facing sessions concurrently across the sanctioned path and the temporary exception path.
- Use an explicit exclusive execution window for any broker-facing session while the shared execution lease is still missing.

## Required Documentation

- The other machine must publish any changes to the parallel path into GitHub main.
- The other machine must mirror control-plane status into gs://codexalpaca-control-us.
- Any change to the parallel path must include what changed, why it changed, and whether it increases or reduces convergence risk.

## Promotion Blockers

- The temporary exception is still active.
- Project-level Owner remains on service accounts.
- The shared execution lease is still missing.
- The first trusted validation paper session on vm-execution-paper-01 has not yet been used to clear promotion by evidence.

## Exit Criteria

- A clear keep/migrate/decommission decision exists for multi-ticker-trader-v1.
- Any surviving runtime path is represented in the codified control plane.
- Project-level Owner is removed from service accounts.
- A cloud-backed shared execution lease exists.
- The sanctioned execution VM has a clean trusted validation session and assimilation packet.
