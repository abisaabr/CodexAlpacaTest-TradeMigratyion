# Execution Evidence Contract Handoff

- Current unlocked profile: `down_choppy_coverage_ranked`
- Contract status: `gapped`
- Latest traded session used: `2026-04-23`

## Required Next Session Artifacts

- broker-order audit
- broker account-activity audit
- ending broker-position snapshot
- shutdown reconciliation
- completed trade table with broker/local economics comparison

## Immediate Gaps

- `broker_order_audit`: Broker-order audit coverage must be present in the session bundle.
- `broker_activity_audit`: Broker account-activity audit coverage must be present in the session bundle.
- `broker_local_cashflow_comparable`: Broker/local economics comparison must be available when broker activity audit exists.
- `runner_unlock_baseline`: The session must be produced by a clean runner checkout that stamps the current unlock baseline.
