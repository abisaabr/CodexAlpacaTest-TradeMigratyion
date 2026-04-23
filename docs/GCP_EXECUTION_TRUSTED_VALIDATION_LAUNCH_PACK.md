# GCP Execution Trusted Validation Launch Pack

This runbook prepares the first broker-facing paper session on `vm-execution-paper-01` as a governed launch sequence.

## Goal

Turn the trusted validation-session gate into one exact launch path:

1. confirm the exclusive execution window
2. launch one sanctioned VM paper session
3. run governed post-session assimilation immediately afterward
4. review the refreshed evidence before any promotion discussion

## Inputs

- `docs/gcp_foundation/gcp_execution_trusted_validation_session_status.md`
- `docs/gcp_foundation/gcp_execution_exclusive_window_status.md`
- `docs/gcp_foundation/gcp_execution_vm_lease_dry_run_validation_handoff.md`
- `docs/POST_SESSION_ASSIMILATION.md`

## Required Evidence

- broker-order audit
- broker account-activity audit
- ending broker-position snapshot
- shutdown reconciliation
- completed trade table with broker/local cashflow comparison

## Rules

- keep the checked-in live manifest unchanged
- keep default lease enforcement off for the first trusted validation session
- do not change strategy selection or risk policy as part of this launch
- do not treat a completed session as promotion by itself; promotion still depends on the refreshed evidence packet

## Preferred Packet

- `docs/gcp_foundation/gcp_execution_trusted_validation_launch_pack.md`
- `docs/gcp_foundation/gcp_execution_trusted_validation_launch_handoff.md`
