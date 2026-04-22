# Tournament Unlock Registry

## Snapshot

- Generated at: `2026-04-22T17:36:16.751432`
- Current resolved profile: `down_choppy_coverage_ranked`
- Execution posture: `caution`
- Session reconciliation posture: `caution`
- Trusted learning scope: `trusted_and_cautious_sessions`
- Unlocked preferred profiles: `down_choppy_coverage_ranked`
- Unlocked available profiles: `down_choppy_full_ready`
- Blocked profiles: `4`

## Immediate Unlock Objectives

- `upgrade_execution_evidence_to_entry_and_reconciliation`: Upgrade execution evidence from `no_recent_trade_sessions` to at least `entry_and_reconciliation` through fresh trusted paper sessions and reconciliation artifacts. Affects `2` profiles.
- `land_trusted_broker_order_audit_sessions`: Land fresh trusted paper sessions with broker-order audit coverage so broker-audited profiles can activate. Affects `4` profiles.
- `land_trusted_broker_activity_audit_sessions`: Land fresh trusted paper sessions with broker account-activity audit coverage so broker-audited profiles can activate. Affects `4` profiles.
- `upgrade_execution_evidence_to_broad`: Upgrade execution evidence from `no_recent_trade_sessions` to at least `broad` through fresh trusted paper sessions and reconciliation artifacts. Affects `2` profiles.
- `raise_execution_risk_ceiling_to_aggressive`: Improve execution posture and trusted evidence enough to raise the activation ceiling from `moderate` to `aggressive`. Affects `2` profiles.
- `land_reliable_exit_telemetry`: Capture reliable exit telemetry from fresh broker-audited paper sessions before activating exit-sensitive profiles. Affects `2` profiles.

## Closest Next Unlock Targets

- `opening_30m_premium_defense`: state `policy_blocked`, unmet `3`, blockers `execution_evidence_floor, broker_order_audit_coverage, broker_activity_audit_coverage`, next objectives `upgrade_execution_evidence_to_entry_and_reconciliation, land_trusted_broker_order_audit_sessions, land_trusted_broker_activity_audit_sessions`
- `balanced_family_expansion_benchmark`: state `policy_blocked`, unmet `3`, blockers `execution_evidence_floor, broker_order_audit_coverage, broker_activity_audit_coverage`, next objectives `upgrade_execution_evidence_to_entry_and_reconciliation, land_trusted_broker_order_audit_sessions, land_trusted_broker_activity_audit_sessions`
- `opening_30m_convexity_butterfly`: state `policy_blocked`, unmet `5`, blockers `execution_evidence_floor, risk_tier_cap, broker_order_audit_coverage, broker_activity_audit_coverage, exit_telemetry`, next objectives `upgrade_execution_evidence_to_broad, raise_execution_risk_ceiling_to_aggressive, land_trusted_broker_order_audit_sessions, land_trusted_broker_activity_audit_sessions, land_reliable_exit_telemetry`
- `opening_30m_single_vs_multileg`: state `policy_blocked`, unmet `5`, blockers `execution_evidence_floor, risk_tier_cap, broker_order_audit_coverage, broker_activity_audit_coverage, exit_telemetry`, next objectives `upgrade_execution_evidence_to_broad, raise_execution_risk_ceiling_to_aggressive, land_trusted_broker_order_audit_sessions, land_trusted_broker_activity_audit_sessions, land_reliable_exit_telemetry`

## Profile Detail

### down_choppy_coverage_ranked

- State: `unlocked_preferred`
- Recommendation level: `preferred`
- Executable now: `true`
- Unmet requirements: `0`
- Session focus: `full_session`
- Risk tier: `moderate`
- Minimum evidence strength: `limited_entry_only`
- Preferred machine now: `current_research_machine`
- Preferred machine target: `either_machine`
- Blockers: `none`
- Next unlock objectives: `none`

### down_choppy_full_ready

- State: `unlocked_available`
- Recommendation level: `available`
- Executable now: `true`
- Unmet requirements: `0`
- Session focus: `full_session`
- Risk tier: `moderate`
- Minimum evidence strength: `limited_entry_only`
- Preferred machine now: `current_research_machine`
- Preferred machine target: `either_machine`
- Blockers: `none`
- Next unlock objectives: `none`

### opening_30m_premium_defense

- State: `policy_blocked`
- Recommendation level: `recommended_but_not_yet_unlocked`
- Executable now: `true`
- Unmet requirements: `3`
- Session focus: `opening_30m`
- Risk tier: `conservative`
- Minimum evidence strength: `entry_and_reconciliation`
- Preferred machine now: `current_research_machine`
- Preferred machine target: `new_machine`
- Blockers: `execution_evidence_floor, broker_order_audit_coverage, broker_activity_audit_coverage`
- Next unlock objectives: `upgrade_execution_evidence_to_entry_and_reconciliation, land_trusted_broker_order_audit_sessions, land_trusted_broker_activity_audit_sessions`

### balanced_family_expansion_benchmark

- State: `policy_blocked`
- Recommendation level: `blocked`
- Executable now: `true`
- Unmet requirements: `3`
- Session focus: `full_session`
- Risk tier: `moderate`
- Minimum evidence strength: `entry_and_reconciliation`
- Preferred machine now: `current_research_machine`
- Preferred machine target: `either_machine`
- Blockers: `execution_evidence_floor, broker_order_audit_coverage, broker_activity_audit_coverage`
- Next unlock objectives: `upgrade_execution_evidence_to_entry_and_reconciliation, land_trusted_broker_order_audit_sessions, land_trusted_broker_activity_audit_sessions`

### opening_30m_convexity_butterfly

- State: `policy_blocked`
- Recommendation level: `blocked`
- Executable now: `true`
- Unmet requirements: `5`
- Session focus: `opening_30m`
- Risk tier: `aggressive`
- Minimum evidence strength: `broad`
- Preferred machine now: `current_research_machine`
- Preferred machine target: `new_machine`
- Blockers: `execution_evidence_floor, risk_tier_cap, broker_order_audit_coverage, broker_activity_audit_coverage, exit_telemetry`
- Next unlock objectives: `upgrade_execution_evidence_to_broad, raise_execution_risk_ceiling_to_aggressive, land_trusted_broker_order_audit_sessions, land_trusted_broker_activity_audit_sessions, land_reliable_exit_telemetry`

### opening_30m_single_vs_multileg

- State: `policy_blocked`
- Recommendation level: `blocked`
- Executable now: `true`
- Unmet requirements: `5`
- Session focus: `opening_30m`
- Risk tier: `aggressive`
- Minimum evidence strength: `broad`
- Preferred machine now: `current_research_machine`
- Preferred machine target: `new_machine`
- Blockers: `execution_evidence_floor, risk_tier_cap, broker_order_audit_coverage, broker_activity_audit_coverage, exit_telemetry`
- Next unlock objectives: `upgrade_execution_evidence_to_broad, raise_execution_risk_ceiling_to_aggressive, land_trusted_broker_order_audit_sessions, land_trusted_broker_activity_audit_sessions, land_reliable_exit_telemetry`

