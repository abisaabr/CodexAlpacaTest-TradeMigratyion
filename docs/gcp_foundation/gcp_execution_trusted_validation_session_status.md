# GCP Execution Trusted Validation Session Status

## Snapshot

- Generated at: `2026-04-23T14:50:38.694104-04:00`
- Project ID: `codexalpaca`
- VM name: `vm-execution-paper-01`
- Readiness: `awaiting_exclusive_execution_window`
- Runner branch: `codex/qqq-paper-portfolio`
- Runner commit: `d440c5d631aeb979d2ba5cebd5bbef7e83253d31`

## Gates

- `operator_access_ready`: `passed`
- `headless_validation_green`: `passed`
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

- An operator still needs to confirm that no other machine is actively running the shared paper account before the VM session starts.
- We do not yet have a cloud-backed shared execution lease, so this first trusted validation session should happen in an explicitly exclusive operator window.
- The session must be followed immediately by governed post-session assimilation before any promotion decision.

## Next Actions

- Use the VM only in an explicitly exclusive paper-account window for the first trusted validation session.
- Run governed post-session assimilation immediately after the session finishes.
- Do not promote the VM to canonical execution until the trusted session evidence is reviewed cleanly.
