# GCP Execution Trusted Validation Session Status

## Snapshot

- Generated at: `2026-04-24T12:35:59.630574-04:00`
- Project ID: `codexalpaca`
- VM name: `vm-execution-paper-01`
- Readiness: `awaiting_exclusive_execution_window`
- Runner branch: `codex/qqq-paper-portfolio`
- Runner commit: `f0080066c68d883286f4cb1b9c9e0edc601adf8d`
- Exclusive window status: `awaiting_operator_confirmation`
- Lease runtime validation: `validated_not_enforced`

## Gates

- `operator_access_ready`: `passed`
- `headless_validation_green`: `passed`
- `shared_lease_dry_run_green`: `passed`
- `runtime_secret_containers_seeded`: `passed`
- `runner_branch_published`: `passed`
- `exclusive_execution_window_confirmed`: `operator_required`

## Proposed VM Command

```bash
cd /opt/codexalpaca/codexalpaca_repo && ./.venv/bin/python scripts/run_multi_ticker_portfolio_paper_trader.py --portfolio-config config/multi_ticker_paper_portfolio.yaml --submit-paper-orders
```

## Required Evidence

- `broker-order audit`
- `broker account-activity audit`
- `ending broker-position snapshot`
- `shutdown reconciliation`
- `completed trade table with broker/local cashflow comparison`

## Remaining Gates

- An operator still needs to confirm an active exclusive execution window so no other machine is using the shared paper account when the VM session starts.
- The shared execution lease is now proven in dry-run mode on the sanctioned VM, but enforcement is still intentionally off until a separate promotion decision says otherwise.
- The session must be followed immediately by governed post-session assimilation before any promotion decision.

## Next Actions

- Refresh the governed exclusive execution-window packet before the first broker-facing VM session.
- Keep the shared execution lease in dry-run posture; do not switch default enforcement on as part of the first trusted validation session.
- Use the trusted validation launch pack only inside an explicitly exclusive paper-account window.
- Run governed post-session assimilation immediately after the session finishes.
- Do not promote the VM to canonical execution until the trusted session evidence is reviewed cleanly.
