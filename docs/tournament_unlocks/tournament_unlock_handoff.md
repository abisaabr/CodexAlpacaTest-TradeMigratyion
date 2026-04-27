# Tournament Unlock Handoff

## Snapshot

- Generated at: `2026-04-27T10:53:29.646277`
- Current resolved profile: `down_choppy_coverage_ranked`
- Execution posture: `caution`
- Session reconciliation posture: `caution`
- Trusted learning scope: `trusted_and_cautious_sessions`
- Unlocked now: `down_choppy_coverage_ranked`
- Available but not preferred: `down_choppy_full_ready`

## Closest Next Unlock Targets

- `opening_30m_premium_defense`: state `policy_blocked`, blockers `execution_evidence_floor, unlock_session_count_floor, unlock_evidence_freshness, broker_order_audit_coverage, broker_activity_audit_coverage`, next objectives `upgrade_execution_evidence_to_entry_and_reconciliation, land_1_trusted_unlock_sessions, refresh_unlock_evidence_within_7_days, land_trusted_broker_order_audit_sessions, land_trusted_broker_activity_audit_sessions`
- `balanced_family_expansion_benchmark`: state `policy_blocked`, blockers `execution_evidence_floor, unlock_session_count_floor, unlock_evidence_freshness, broker_order_audit_coverage, broker_activity_audit_coverage`, next objectives `upgrade_execution_evidence_to_entry_and_reconciliation, land_1_trusted_unlock_sessions, refresh_unlock_evidence_within_7_days, land_trusted_broker_order_audit_sessions, land_trusted_broker_activity_audit_sessions`
- `opening_30m_convexity_butterfly`: state `policy_blocked`, blockers `execution_evidence_floor, unlock_session_count_floor, unlock_evidence_freshness, risk_tier_cap, broker_order_audit_coverage, broker_activity_audit_coverage`, next objectives `upgrade_execution_evidence_to_broad, land_2_trusted_unlock_sessions, refresh_unlock_evidence_within_5_days, raise_execution_risk_ceiling_to_aggressive, land_trusted_broker_order_audit_sessions, land_trusted_broker_activity_audit_sessions`
- `opening_30m_single_vs_multileg`: state `policy_blocked`, blockers `execution_evidence_floor, unlock_session_count_floor, unlock_evidence_freshness, risk_tier_cap, broker_order_audit_coverage, broker_activity_audit_coverage`, next objectives `upgrade_execution_evidence_to_broad, land_2_trusted_unlock_sessions, refresh_unlock_evidence_within_5_days, raise_execution_risk_ceiling_to_aggressive, land_trusted_broker_order_audit_sessions, land_trusted_broker_activity_audit_sessions`

## Immediate Unlock Objectives

- `upgrade_execution_evidence_to_entry_and_reconciliation`: Upgrade execution evidence from `no_recent_trade_sessions` to at least `entry_and_reconciliation` through fresh trusted paper sessions and reconciliation artifacts. Affects `2` profiles.
- `land_1_trusted_unlock_sessions`: Land at least `1` fresh trusted unlock-grade session(s) before activating this profile. Affects `2` profiles.
- `refresh_unlock_evidence_within_7_days`: Land fresh trusted unlock-grade paper evidence no older than `7` day(s) before activating this profile. Affects `2` profiles.
- `land_trusted_broker_order_audit_sessions`: Land fresh trusted paper sessions with broker-order audit coverage so broker-audited profiles can activate. Affects `4` profiles.

## Operator Actions

- Run `down_choppy_coverage_ranked` while higher-tier profiles remain blocked by execution evidence or implementation gates.
- Keep `down_choppy_full_ready` as fallback executable profiles, not the default nightly choice.
- Upgrade execution evidence from `no_recent_trade_sessions` to at least `entry_and_reconciliation` through fresh trusted paper sessions and reconciliation artifacts.
- Land at least `1` fresh trusted unlock-grade session(s) before activating this profile.
- Land fresh trusted unlock-grade paper evidence no older than `7` day(s) before activating this profile.
- Land fresh trusted paper sessions with broker-order audit coverage so broker-audited profiles can activate.
