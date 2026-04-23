# GCP Execution Trusted Validation Session

This runbook defines the first broker-facing paper session on the GCP execution VM after the headless validation gate is green.

## Goal

Prove that `vm-execution-paper-01` can produce the full execution evidence package from a real paper session before we consider canonical promotion.

## Required Preconditions

- execution access readiness is `ready_for_operator_validation`
- headless validation review is `passed`
- runtime secrets are seeded
- the runner branch and commit are pinned and published
- the lease dry-run handoff is `passed`
- the exclusive execution window packet is explicit
- an operator confirms that no other machine is actively running the shared Alpaca paper account

## Required Evidence

- broker-order audit
- broker account-activity audit
- ending broker-position snapshot
- shutdown reconciliation
- completed trade table with broker/local cashflow comparison

## Rules

- keep the checked-in live manifest unchanged
- do not change risk policy as part of this session
- treat this as validation, not promotion
- follow immediately with governed post-session assimilation

## Why The Exclusive Window Matters

The current local/portable ownership model is filesystem-based. Until we introduce a cloud-backed shared execution lease, the first trusted validation session should only run when an operator has explicitly confirmed that no workstation or standby runner is active on the same paper account.

## Preferred Companion Packets

- `docs/GCP_EXECUTION_EXCLUSIVE_WINDOW.md`
- `docs/GCP_EXECUTION_TRUSTED_VALIDATION_LAUNCH_PACK.md`
- `docs/gcp_foundation/gcp_execution_exclusive_window_handoff.md`
- `docs/gcp_foundation/gcp_execution_trusted_validation_launch_handoff.md`
