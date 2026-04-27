# GCP Execution Incident Handoff

Generated: 2026-04-27T10:32:00-04:00

## Status

Incident state: `rogue_runner_fenced_account_flat_prearm_clean`

The sanctioned execution VM `vm-execution-paper-01` was not running the paper trader. During governed pre-arm broker watches, fresh paper-account option orders appeared without an armed exclusive window or authorized VM launch. The active unsanctioned writer was identified as GCP VM `multi-ticker-trader-v1` in `us-central1-a`, labeled `role=runner`.

`multi-ticker-trader-v1` was stopped at 2026-04-27 during the incident response. After stopping it, the paper account was flattened and remained at zero positions / zero open orders through the post-flatten watch.

A follow-up governed pre-arm preflight was then run against the VM-matching runner checkout at `f0080066c68d883286f4cb1b9c9e0edc601adf8d`. That pre-arm passed: source provenance matched, sanctioned VM runtime readiness passed, and the broker no-new-order watch stayed clean for 301 seconds.

## What Happened

- The first pre-arm run matched VM source provenance only after using runner commit `f0080066c68d883286f4cb1b9c9e0edc601adf8d`.
- VM runtime readiness passed on `vm-execution-paper-01`: tests green, no trader process present, file lease enabled.
- The broker launch-surface audit failed because fresh orders and positions appeared during the no-new-order watch.
- A first emergency flatten cleared QQQ/IWM exposure, but new NVDA/PLTR/SCHW/TSLA orders appeared afterward.
- A retry flatten cleared those, but BAC/NKE orders appeared during the post-flatten watch.
- GCP inventory then showed `multi-ticker-trader-v1` running outside the sanctioned execution path.
- After stopping `multi-ticker-trader-v1`, BAC/NKE were flattened and the account stayed flat.
- A fresh post-fence pre-arm preflight returned `ready_to_arm_window`; launch authorization remains blocked until an exclusive window is deliberately armed.

## Current Posture

- `vm-execution-paper-01`: running, sanctioned execution path, no trader launched by this handoff.
- `multi-ticker-trader-v1`: stopped / fenced; do not restart without an explicit governance decision.
- Phase19 research job: still running as non-broker-facing Batch work.
- Paper account: flat at last check, zero open broker orders, clean 301-second no-new-order watch.
- Exclusive execution window: not armed.
- Pre-arm status: `ready_to_arm_window`.
- Launch authorization: blocked until the exclusive execution window is armed.

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

Do not launch a paper trader from any path unless the latest fresh pre-arm preflight remains current and the exclusive execution window is deliberately armed. The current next operator action is:

- Arm a bounded exclusive window only if the project is ready to run the sanctioned VM session now.
- Build launch authorization after arming and require `ready_to_launch_session`.
- Run only the sanctioned VM command on `vm-execution-paper-01`.
- Run post-session assimilation and closeout immediately afterward.

If rechecking before launch, require:

- `multi-ticker-trader-v1` still stopped,
- broker account flat,
- zero open orders,
- no-new-order watch clean for at least 300 seconds,
- sanctioned VM source provenance matched,
- sanctioned VM runtime readiness passed,
- exclusive window still unarmed until the pre-arm packet says `ready_to_arm_window`.

If any new paper order appears before an explicit exclusive-window arm and launch authorization, stop and treat it as a continuing rogue-writer incident.
