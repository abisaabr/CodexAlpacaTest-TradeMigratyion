# GCP VM Runtime Readiness Status

## Snapshot

- Generated at: `2026-04-27T10:25:51.210828-04:00`
- Status: `runtime_ready`
- VM name: `vm-execution-paper-01`
- VM runner path: `/opt/codexalpaca/codexalpaca_repo`
- Source provenance status: `provenance_matched`
- Doctor status: `passed`
- VM pytest status: `passed`
- VM pytest summary: `140 passed in 41.43s`
- Trader process absent: `True`

## Launch Ownership

- Ownership enabled: `True`
- Ownership backend: `file`
- Ownership lease class: `FileOwnershipLease`
- Ownership machine label: `vm-execution-paper-01`
- GCS lease URI: `None`
- Shared execution lease enforced: `False`

## Path Checks

- `data` writable: `True`
- `reports` writable: `True`
- `reports/multi_ticker_portfolio/state` writable: `True`
- `reports/multi_ticker_portfolio/runs` writable: `True`
- `.pytest_cache` writable: `True`

## Issues

- none

## Operator Read

- This packet validates VM runtime output readiness only; it does not start trading or arm the exclusive window.
- The trusted paper session needs writable state and run directories so broker-audited evidence can be left behind.
- No stale trader process may already be running on the VM before the exclusive window is armed.
- Launch ownership must be enabled through the local file lease for the first trusted VM session.
- Source provenance, exclusive-window, and launch-pack gates still control whether a broker-facing session may start.

## Next Actions

- If status is `runtime_ready`, keep source and runtime-output responsibilities separate: source stays stamped, runtime directories stay writable.
- Keep the first trusted VM session on the file lease; only validate GCS shared-lease enforcement under an explicit non-default rollout packet.
- Refresh this packet after any VM source redeploy, permission repair, or runtime bootstrap change.
- Do not use runtime readiness as strategy-promotion evidence; it only supports operational launch readiness.
