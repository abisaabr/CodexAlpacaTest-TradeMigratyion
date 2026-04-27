# GCP Execution Startup Preflight Handoff

- Status: `startup_preflight_blocked`
- Blocks launch: `True`
- Freshness status: `fresh`
- Preflight observed at UTC: `2026-04-27T15:32:33+00:00`
- Preflight age seconds: `54`
- Max age seconds: `600`
- Raw status: `startup_preflight_failed`
- Startup check status: `failed`
- Would allow trading: `False`
- Broker cleanup allowed: `False`
- Submit paper orders: `False`
- Broker position count: `0`
- Open order count: `0`
- Underlying count: `21`
- Runner branch: `codex/qqq-paper-portfolio`
- Runner commit: `a3b5e926d9bfec0ec83603770a778e7974e38398`
- GCS evidence URI: `gs://codexalpaca-control-us/gcp_foundation/startup_preflight_evidence/20260427T153233Z/startup_preflight.json`

## Operator Rule

- This is a read-only VM startup check; it must not submit orders or flatten broker positions.
- If status is not `startup_preflight_passed`, do not arm the exclusive window or start a VM session.
- Rerun this preflight immediately before launch because broker/account state and market-data freshness change minute to minute.

## Blocking Issues

- `startup_preflight_not_passed`: The VM startup preflight reported `startup_preflight_failed`.
- `startup_check_not_passed`: The runner startup check reported `failed`.
- `startup_preflight_would_not_allow_trading`: The startup preflight says the runner would not allow trading.
- `startup_preflight_failure`: SHOP stock data stale at 473s
