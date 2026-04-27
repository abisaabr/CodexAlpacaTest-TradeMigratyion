# GCP Execution Startup Preflight Status

## Snapshot

- Generated at: `2026-04-27T11:33:27.462143-04:00`
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

## Issues

- `error` `startup_preflight_not_passed`: The VM startup preflight reported `startup_preflight_failed`.
- `error` `startup_check_not_passed`: The runner startup check reported `failed`.
- `error` `startup_preflight_would_not_allow_trading`: The startup preflight says the runner would not allow trading.
- `error` `startup_preflight_failure`: SHOP stock data stale at 473s

## Operator Read

- This packet distills read-only VM startup-preflight evidence; raw broker output should remain in ignored runtime evidence or GCS.
- If status is not `startup_preflight_passed`, do not arm the exclusive window or launch a VM session.
- The preflight must be rerun immediately before any sanctioned launch because market-data freshness is time-sensitive.
- Passing this packet is necessary but not sufficient; exclusive-window, runtime, provenance, launch-surface, and pre-arm gates must also pass.
