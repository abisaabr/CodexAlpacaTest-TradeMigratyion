# GCP Execution Startup Preflight Status

## Snapshot

- Generated at: `2026-04-27T11:27:17.208780-04:00`
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

## Issues

- none

## Operator Read

- This packet distills read-only VM startup-preflight evidence; raw broker output should remain in ignored runtime evidence or GCS.
- If status is not `startup_preflight_passed`, do not arm the exclusive window or launch a VM session.
- The preflight must be rerun immediately before any sanctioned launch because market-data freshness is time-sensitive.
- Passing this packet is necessary but not sufficient; exclusive-window, runtime, provenance, launch-surface, and pre-arm gates must also pass.
