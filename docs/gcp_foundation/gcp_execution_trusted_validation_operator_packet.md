# GCP Execution Trusted Validation Operator Packet

## Snapshot

- Generated at: `2026-04-24T12:08:51.974751-04:00`
- Operator packet state: `ready_to_arm_window`
- Project ID: `codexalpaca`
- VM name: `vm-execution-paper-01`
- Runner branch: `codex/qqq-paper-portfolio`
- Runner commit: `f0080066c68d883286f4cb1b9c9e0edc601adf8d`

## Current Gates

- Exclusive window status: `awaiting_operator_confirmation`
- Trusted validation readiness: `awaiting_exclusive_execution_window`
- Launch pack state: `awaiting_window_arm`
- Closeout status: `window_already_closed`
- Runner provenance status: `provenance_matched`
- Runtime readiness status: `runtime_ready`
- Runtime trader process absent: `True`
- Runtime ownership enabled: `True`
- Runtime ownership backend: `file`
- Runtime ownership lease class: `FileOwnershipLease`
- Runtime shared execution lease enforced: `False`
- Session completion gate: `awaiting_launch_authorization`
- Launch-surface audit status: `local_broker_capable_surfaces_fenced_broker_flat`
- Launch-surface broker flat: `True`
- Launch-surface no-new-order watch clean: `True`

## Commands

### Arm Window

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "<control-plane-root>\cleanroom\code\qqq_options_30d_cleanroom\arm_gcp_execution_exclusive_window.ps1" -ControlPlaneRoot "<control-plane-root>" -VmName "vm-execution-paper-01" -ConfirmedBy "<confirmed-by>" -WindowStartsAt "<window-starts-at>" -WindowExpiresAt "<window-expires-at>" -ParallelPathState "paused" -MirrorToGcs
```

### Operator SSH

```bash
gcloud compute ssh vm-execution-paper-01 --project codexalpaca --zone us-east1-b --tunnel-through-iap
```

### VM Session

```bash
cd /opt/codexalpaca/codexalpaca_repo && ./.venv/bin/python scripts/run_multi_ticker_portfolio_paper_trader.py --portfolio-config config/multi_ticker_paper_portfolio.yaml --submit-paper-orders
```

### Post-Session Assimilation

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "<control-plane-root>\cleanroom\code\qqq_options_30d_cleanroom\launch_post_session_assimilation.ps1" -ControlPlaneRoot "<control-plane-root>" -RunnerRepoRoot "<runner-repo-root>"
```

### Close Window

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "<control-plane-root>\cleanroom\code\qqq_options_30d_cleanroom\close_gcp_execution_exclusive_window.ps1" -ControlPlaneRoot "<control-plane-root>" -VmName "vm-execution-paper-01" -MirrorToGcs
```

## Lifecycle Steps

- Read the local launch-surface audit and require broker-flat, task-fenced, no-new-order evidence before arming.
- Run the non-broker pre-arm preflight and require `ready_to_arm_window` before arming the exclusive window.
- Pick a bounded exclusive window and confirm the temporary parallel runtime path is paused for that window.
- Arm the exclusive window from the control-plane root and confirm the refreshed packets move to `ready_for_launch` / `ready_to_launch`.
- Build the non-broker launch authorization packet and require `ready_to_launch_session` before running the VM session command.
- SSH into the sanctioned VM through IAP.
- Run the trusted validation session command on the VM without changing strategy selection or risk policy.
- Run governed post-session assimilation immediately after the session ends.
- Close the exclusive window and mirror the refreshed packet set to GCS.
- Refresh the session-completion evidence gate before treating the session as complete for review.
- Review the morning brief, execution calibration, tournament unlock, and execution evidence packets before any promotion decision.

## Required Evidence

- `broker-order audit`
- `broker account-activity audit`
- `ending broker-position snapshot`
- `shutdown reconciliation`
- `completed trade table with broker/local cashflow comparison`

## Review Targets

- `docs/morning_brief/morning_operator_brief.md`
- `docs/execution_calibration/execution_calibration_handoff.md`
- `docs/tournament_unlocks/tournament_unlock_handoff.md`
- `docs/execution_evidence/execution_evidence_contract_handoff.md`
- `docs/gcp_foundation/gcp_execution_launch_authorization_handoff.md`
- `docs/gcp_foundation/gcp_vm_runner_provenance_handoff.md`
- `docs/gcp_foundation/gcp_vm_runner_source_fingerprint_handoff.md`
- `docs/gcp_foundation/gcp_vm_runtime_readiness_handoff.md`
- `docs/gcp_foundation/gcp_execution_launch_surface_audit_handoff.md`
- `docs/gcp_foundation/gcp_execution_prearm_preflight_handoff.md`
- `docs/gcp_foundation/gcp_execution_session_completion_gate_handoff.md`

## Guardrails

- Do not arm the exclusive window until you are ready to actually reserve the paper-account slot.
- Do not start a broker-facing session unless the refreshed exclusive-window packet says `ready_for_launch` and the launch pack says `ready_to_launch`.
- Do not arm or launch a trusted session while runner provenance status starts with `blocked_`.
- Do not arm or launch a trusted session while VM runtime readiness starts with `blocked_`.
- Do not arm the exclusive window if the non-broker pre-arm preflight is missing or blocked.
- Do not arm the exclusive window if the launch-surface audit is missing, stale, not broker-flat, or not task-fenced.
- Do not run the VM session command if launch authorization is missing or blocked.
- Do not enable shared-lease enforcement by default during the first trusted validation session.
- Do not use unstamped VM runner provenance as strategy-promotion evidence.
- Do not skip post-session assimilation or closeout after the session ends.
- Do not count a raw PnL winner as a qualified winner unless the session-completion evidence gate is complete.
