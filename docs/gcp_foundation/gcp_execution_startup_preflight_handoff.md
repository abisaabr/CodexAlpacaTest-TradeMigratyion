# GCP Execution Startup Preflight Handoff

- Status: `startup_preflight_passed`
- Blocks launch: `False`
- Raw status: `startup_preflight_passed`
- Startup check status: `passed`
- Would allow trading: `True`
- Broker cleanup allowed: `False`
- Submit paper orders: `False`
- Broker position count: `0`
- Open order count: `0`
- Underlying count: `21`
- Runner branch: `codex/qqq-paper-portfolio`
- Runner commit: `a3b5e926d9bfec0ec83603770a778e7974e38398`
- GCS evidence URI: `gs://codexalpaca-control-us/gcp_foundation/startup_preflight_evidence/20260427T152621Z/startup_preflight.json`

## Operator Rule

- This is a read-only VM startup check; it must not submit orders or flatten broker positions.
- If status is not `startup_preflight_passed`, do not arm the exclusive window or start a VM session.
- Rerun this preflight immediately before launch because broker/account state and market-data freshness change minute to minute.
