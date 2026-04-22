# Tournament Unlock Workplan

## Snapshot

- Generated at: `2026-04-22T18:00:40.231183`
- Current unlocked profile: `down_choppy_coverage_ranked`
- Available but not preferred: `down_choppy_full_ready`

## Research Plane Mission

- Owner: `current_research_machine`
- Title: No research-plane unlock wiring is immediately required.
- Primary target profile: `none`

## Execution Plane Mission

- Owner: `new_machine_execution_plane`
- Title: Produce the next trusted broker-audited execution evidence package.
- Primary target profiles: `opening_30m_premium_defense, balanced_family_expansion_benchmark`
- Action: Run the current unlocked profile without changing live strategy selection, risk policy, or the live manifest.
- Action: Ensure the session bundle captures broker-order audit, broker account-activity audit, and ending broker-position snapshot artifacts.
- Action: Immediately rerun session reconciliation, execution calibration, tournament unlock registry, and tournament unlock handoff after the next trusted session lands.
- Action: Treat trusted broker-order and broker-activity audit coverage as the primary missing evidence package.
- Action: Aim to improve execution evidence beyond `limited_entry_only` by landing a trusted, fully reconciled paper session.
- Success: At least one fresh trusted paper session lands with broker-order audit coverage.
- Success: At least one fresh trusted paper session lands with broker account-activity audit coverage.
- Success: The refreshed session reconciliation handoff remains `trusted_and_cautious_sessions` or better without flipping the new session to `review_required`.
- Success: The refreshed execution calibration handoff improves the evidence floor or removes audit-gap blockers for the nearest unlock target.

## Completion Gates

- `opening_30m_premium_defense`: clear `execution_evidence_floor, unlock_session_count_floor, unlock_evidence_freshness, broker_order_audit_coverage, broker_activity_audit_coverage` via `upgrade_execution_evidence_to_entry_and_reconciliation, land_1_trusted_unlock_sessions, refresh_unlock_evidence_within_7_days, land_trusted_broker_order_audit_sessions, land_trusted_broker_activity_audit_sessions`
- `balanced_family_expansion_benchmark`: clear `execution_evidence_floor, unlock_session_count_floor, unlock_evidence_freshness, broker_order_audit_coverage, broker_activity_audit_coverage` via `upgrade_execution_evidence_to_entry_and_reconciliation, land_1_trusted_unlock_sessions, refresh_unlock_evidence_within_7_days, land_trusted_broker_order_audit_sessions, land_trusted_broker_activity_audit_sessions`
- `opening_30m_convexity_butterfly`: clear `execution_evidence_floor, unlock_session_count_floor, unlock_evidence_freshness, risk_tier_cap, broker_order_audit_coverage, broker_activity_audit_coverage, exit_telemetry` via `upgrade_execution_evidence_to_broad, land_2_trusted_unlock_sessions, refresh_unlock_evidence_within_5_days, raise_execution_risk_ceiling_to_aggressive, land_trusted_broker_order_audit_sessions, land_trusted_broker_activity_audit_sessions, land_reliable_exit_telemetry`
