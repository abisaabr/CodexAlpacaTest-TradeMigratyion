# Execution Evidence Contract

## Snapshot

- Generated at: `2026-04-27T10:53:30.125279`
- Current unlocked profile: `down_choppy_coverage_ranked`
- Execution mission title: Produce the next trusted broker-audited execution evidence package.
- Contract status: `gapped`
- Latest traded session used: `2026-04-23`
- Latest traded session age days: `4`

## Required Checks

- `traded_session_exists`: passed `true`, required `session_kind = traded`, current `traded`
- `shutdown_reconciled`: passed `true`, required `shutdown_reconciled = true`, current `True`
- `trust_tier_not_review_required`: passed `true`, required `trust_tier in {trusted, caution}`, current `caution`
- `broker_order_audit`: passed `false`, required `broker_order_audit_available = true`, current `False`
- `broker_activity_audit`: passed `false`, required `broker_activity_audit_available = true`, current `False`
- `ending_positions_flat`: passed `true`, required `ending_broker_position_count = 0`, current `0`
- `broker_local_cashflow_comparable`: passed `false`, required `broker_local_cashflow_comparable = true`, current `False`
- `completed_trade_count_positive`: passed `true`, required `completed_trade_count > 0`, current `14`
- `runner_unlock_baseline`: passed `false`, required `runner_unlock_baseline_met = true`, current `False`
- `review_scope_preserved`: passed `true`, required `trusted_learning_scope in {trusted_and_cautious_sessions, all_recent_sessions}`, current `trusted_and_cautious_sessions`
- `latest_session_fresh_for_unlock`: passed `true`, required `latest_traded_session_age_days <= 5`, current `4`
- `evidence_strength_progress`: passed `true`, required `execution_evidence_strength != limited_entry_only`, current `limited`

## Immediate Gaps

- `broker_order_audit`: Broker-order audit coverage must be present in the session bundle.
- `broker_activity_audit`: Broker account-activity audit coverage must be present in the session bundle.
- `broker_local_cashflow_comparable`: Broker/local economics comparison must be available when broker activity audit exists.
- `runner_unlock_baseline`: The session must be produced by a clean runner checkout that stamps the current unlock baseline.
