# GCP Execution Incident Handoff

Generated: 2026-04-27T10:24:00-04:00

## Status

Incident state: `rogue_runner_fenced_account_flat`

The sanctioned execution VM `vm-execution-paper-01` was not running the paper trader. During governed pre-arm broker watches, fresh paper-account option orders appeared without an armed exclusive window or authorized VM launch. The active unsanctioned writer was identified as GCP VM `multi-ticker-trader-v1` in `us-central1-a`, labeled `role=runner`.

`multi-ticker-trader-v1` was stopped at 2026-04-27 during the incident response. After stopping it, the paper account was flattened and remained at zero positions / zero open orders through the post-flatten watch.

## What Happened

- The first pre-arm run matched VM source provenance only after using runner commit `f0080066c68d883286f4cb1b9c9e0edc601adf8d`.
- VM runtime readiness passed on `vm-execution-paper-01`: tests green, no trader process present, file lease enabled.
- The broker launch-surface audit failed because fresh orders and positions appeared during the no-new-order watch.
- A first emergency flatten cleared QQQ/IWM exposure, but new NVDA/PLTR/SCHW/TSLA orders appeared afterward.
- A retry flatten cleared those, but BAC/NKE orders appeared during the post-flatten watch.
- GCP inventory then showed `multi-ticker-trader-v1` running outside the sanctioned execution path.
- After stopping `multi-ticker-trader-v1`, BAC/NKE were flattened and the account stayed flat.

## Current Posture

- `vm-execution-paper-01`: running, sanctioned execution path, no trader launched by this handoff.
- `multi-ticker-trader-v1`: stopped / fenced; do not restart without an explicit governance decision.
- Phase19 research job: still running as non-broker-facing Batch work.
- Paper account: flat at last check, zero open broker orders.
- Exclusive execution window: not armed.
- Launch authorization: blocked because the latest governed pre-arm packet captured the incident.

## Durable Evidence

Distilled packets were mirrored to:

- `gs://codexalpaca-control-us/gcp_foundation/gcp_execution_prearm_preflight_handoff.md`
- `gs://codexalpaca-control-us/gcp_foundation/gcp_execution_launch_authorization_handoff.md`
- `gs://codexalpaca-control-us/gcp_foundation/gcp_execution_trusted_validation_operator_handoff.md`
- `gs://codexalpaca-control-us/gcp_foundation/gcp_execution_launch_surface_audit_handoff.md`

Raw safety-flatten evidence was mirrored to GCS but should not be committed to GitHub:

- `gs://codexalpaca-control-us/gcp_foundation/safety_flatten_20260427T135140Z.json`
- `gs://codexalpaca-control-us/gcp_foundation/safety_flatten_20260427T140538Z.json`
- `gs://codexalpaca-control-us/gcp_foundation/safety_flatten_retry_20260427T141024Z.json`
- `gs://codexalpaca-control-us/gcp_foundation/safety_flatten_after_rogue_vm_stop_20260427T141629Z.json`

## Next Safe Action

Do not launch a paper trader from any path until a fresh pre-arm preflight passes with:

- `multi-ticker-trader-v1` still stopped,
- broker account flat,
- zero open orders,
- no-new-order watch clean for at least 300 seconds,
- sanctioned VM source provenance matched,
- sanctioned VM runtime readiness passed,
- exclusive window still unarmed until the pre-arm packet says `ready_to_arm_window`.

If any new paper order appears before an explicit exclusive-window arm and launch authorization, stop and treat it as a continuing rogue-writer incident.
