# GCP Execution Exclusive Window

This runbook turns the first sanctioned VM paper session into an explicit, serialized operator window instead of an implicit promise.

## Goal

Create one governed execution window for `vm-execution-paper-01` so the first trusted validation session runs without ambiguity about who owns the shared paper account during that session.

## Preferred Entrypoint

- `cleanroom/code/qqq_options_30d_cleanroom/arm_gcp_execution_exclusive_window.ps1`

## Why This Exists

- the sanctioned VM is technically ready enough to attempt the first trusted validation paper session
- the temporary parallel runtime exception is still active
- the cloud shared execution lease is proven only in dry-run mode today

That means the first broker-facing VM session still needs an explicit human-controlled serialization step.

## Required Preconditions

- `docs/gcp_foundation/gcp_execution_trusted_validation_session_status.md` says readiness is `awaiting_exclusive_execution_window`
- `docs/gcp_foundation/gcp_execution_vm_lease_dry_run_validation_handoff.md` says the lease dry-run review is `passed`
- operator access readiness is still `ready_for_operator_validation`
- the temporary parallel runtime path is explicitly paused or ruled out for the session window

## What Must Be Recorded

- who is confirming the window
- window start timestamp
- window end timestamp
- whether the temporary parallel runtime path is paused or absent for the window
- the attestation JSON under `docs/gcp_foundation/gcp_execution_exclusive_window_attestation.json`

## Rules

- do not treat this as permission to enable lease enforcement by default
- do not start a broker-facing session until the exclusive window packet is explicit
- do not run concurrent paper-account sessions across the sanctioned VM and the temporary parallel path
- follow immediately with governed post-session assimilation

## Preferred Packet

- `docs/gcp_foundation/gcp_execution_exclusive_window_status.md`
- `docs/gcp_foundation/gcp_execution_exclusive_window_handoff.md`
