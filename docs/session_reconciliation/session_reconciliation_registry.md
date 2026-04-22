# Session Reconciliation Registry

## Snapshot

- Generated at: `2026-04-22T17:53:44.961631`
- Sessions scanned: `3`
- Trade sessions: `1`
- Trusted trade sessions: `0`
- Caution sessions: `1`
- Review-required sessions: `0`
- Sessions with broker-order audit: `0`
- Sessions with broker-activity audit: `0`
- Sessions with broker/local cashflow comparison: `0`
- Sessions meeting runner unlock baseline: `0`
- Trusted traded sessions meeting full audit + runner unlock baseline: `0`
- Residual broker positions: `0`
- Mean absolute realized reconciliation delta: `0.0`
- Mean absolute broker/local cashflow delta: `0.0`

## Institutional Findings

- `broker_order_audit_gap`: Broker-order audit is missing for traded session(s): `2026-04-16`.
- `broker_activity_audit_gap`: Broker-activity audit is missing for traded session(s): `2026-04-16`.
- `runner_unlock_baseline_gap`: No trusted traded session currently satisfies the full broker-audited unlock baseline on a clean, stamped runner checkout, so blocked tournament profiles should remain blocked.

## Review-Required Sessions

- none

## Caution Sessions

- `2026-04-16`: quality `70`, completed trades `5`, reasons `broker_order_audit_gap, broker_activity_audit_gap, runner_unlock_baseline_gap, guardrail_manual_review, severe_loss_flatten_triggered`

## Data Quality

- Missing broker-order audit on traded sessions: `2026-04-16`
- Missing broker-activity audit on traded sessions: `2026-04-16`
- Missing broker/local cashflow comparison on broker-audited traded sessions: `none`
- Missing runner unlock baseline on traded sessions: `2026-04-16`

