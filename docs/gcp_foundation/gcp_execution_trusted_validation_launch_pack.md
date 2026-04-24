# GCP Execution Trusted Validation Launch Pack

## Snapshot

- Generated at: `2026-04-24T12:20:17.919366-04:00`
- Project ID: `codexalpaca`
- VM name: `vm-execution-paper-01`
- Launch pack state: `awaiting_window_arm`
- Runner branch: `codex/qqq-paper-portfolio`
- Runner commit: `f0080066c68d883286f4cb1b9c9e0edc601adf8d`
- Exclusive window state: `awaiting_operator_attestation`
- Exclusive window status: `awaiting_operator_confirmation`
- Lease runtime validation: `validated_not_enforced`

## Commands

### Operator SSH

```bash
gcloud compute ssh vm-execution-paper-01 --project codexalpaca --zone us-east1-b --tunnel-through-iap
```

### VM Session Command

```bash
cd /opt/codexalpaca/codexalpaca_repo && ./.venv/bin/python scripts/run_multi_ticker_portfolio_paper_trader.py --portfolio-config config/multi_ticker_paper_portfolio.yaml --submit-paper-orders
```

### Post-Session Assimilation

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "<control-plane-root>\cleanroom\code\qqq_options_30d_cleanroom\launch_post_session_assimilation.ps1" -ControlPlaneRoot "<control-plane-root>" -RunnerRepoRoot "<runner-repo-root>"
```

## Operator Steps

- Do not start the session yet; this pack is in preparation mode until the exclusive execution window is actively confirmed.
- Confirm the exclusive-window packet says `ready_for_launch` and this launch pack says `ready_to_launch`.
- Build the launch-authorization packet and require `ready_to_launch_session` before running the VM session command.
- SSH to `vm-execution-paper-01` through IAP.
- Run the trusted validation session command on the VM without changing strategy selection or risk policy.
- When the session ends, run governed post-session assimilation from the control-plane machine.
- Review the refreshed morning brief, execution calibration handoff, tournament unlock handoff, and execution evidence contract before any promotion decision.

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

## Guardrails

- Do not auto-start trading from this packet.
- Do not run the VM session command unless the launch-authorization packet says `ready_to_launch_session`.
- Keep the shared execution lease in dry-run posture for the first trusted validation session.
- Do not widen the temporary parallel-runtime exception.
- Do not promote the VM to canonical execution from this launch alone.
