# Tournament Unlock Handoff

## Snapshot

- Generated at: `2026-04-22T16:07:00.501558`
- Current resolved profile: `down_choppy_coverage_ranked`
- Execution posture: `caution`
- Session reconciliation posture: `caution`
- Trusted learning scope: `trusted_and_cautious_sessions`
- Unlocked now: `down_choppy_coverage_ranked`
- Available but not preferred: `down_choppy_full_ready`

## Closest Next Unlock Targets

- `opening_30m_premium_defense`: state `policy_blocked`, blockers `execution_evidence_floor, broker_order_audit_coverage, broker_activity_audit_coverage`, next objectives `upgrade_execution_evidence_to_entry_and_reconciliation, land_trusted_broker_order_audit_sessions, land_trusted_broker_activity_audit_sessions`
- `balanced_family_expansion_benchmark`: state `policy_blocked`, blockers `execution_evidence_floor, broker_order_audit_coverage, broker_activity_audit_coverage`, next objectives `upgrade_execution_evidence_to_entry_and_reconciliation, land_trusted_broker_order_audit_sessions, land_trusted_broker_activity_audit_sessions`
- `opening_30m_convexity_butterfly`: state `implementation_and_policy_blocked`, blockers `implementation_not_wired, execution_evidence_floor, risk_tier_cap, broker_order_audit_coverage, broker_activity_audit_coverage, exit_telemetry`, next objectives `wire_profile_entrypoint, upgrade_execution_evidence_to_broad, raise_execution_risk_ceiling_to_aggressive, land_trusted_broker_order_audit_sessions, land_trusted_broker_activity_audit_sessions, land_reliable_exit_telemetry`
- `opening_30m_single_vs_multileg`: state `implementation_and_policy_blocked`, blockers `implementation_not_wired, execution_evidence_floor, risk_tier_cap, broker_order_audit_coverage, broker_activity_audit_coverage, exit_telemetry`, next objectives `wire_profile_entrypoint, upgrade_execution_evidence_to_broad, raise_execution_risk_ceiling_to_aggressive, land_trusted_broker_order_audit_sessions, land_trusted_broker_activity_audit_sessions, land_reliable_exit_telemetry`

## Immediate Unlock Objectives

- `upgrade_execution_evidence_to_entry_and_reconciliation`: Upgrade execution evidence from `limited_entry_only` to at least `entry_and_reconciliation` through fresh trusted paper sessions and reconciliation artifacts. Affects `2` profiles.
- `land_trusted_broker_order_audit_sessions`: Land fresh trusted paper sessions with broker-order audit coverage so broker-audited profiles can activate. Affects `4` profiles.
- `land_trusted_broker_activity_audit_sessions`: Land fresh trusted paper sessions with broker account-activity audit coverage so broker-audited profiles can activate. Affects `4` profiles.
- `wire_profile_entrypoint`: Wire this profile into an executable governed entrypoint and launch path before trying to activate it. Affects `2` profiles.

## Operator Actions

- Run `down_choppy_coverage_ranked` while higher-tier profiles remain blocked by execution evidence or implementation gates.
- Keep `down_choppy_full_ready` as fallback executable profiles, not the default nightly choice.
- Upgrade execution evidence from `limited_entry_only` to at least `entry_and_reconciliation` through fresh trusted paper sessions and reconciliation artifacts.
- Land fresh trusted paper sessions with broker-order audit coverage so broker-audited profiles can activate.
- Land fresh trusted paper sessions with broker account-activity audit coverage so broker-audited profiles can activate.
- Wire this profile into an executable governed entrypoint and launch path before trying to activate it.
