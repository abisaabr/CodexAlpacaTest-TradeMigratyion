# Agent Governance Registry

This registry turns the operating model into machine-readable governance.

## Institutional Rules

- Discovery should be assigned by family cohort to avoid overlap and improve frontier coverage.
- Exhaustive follow-up should be assigned by ticker bundle so symbol-specific fit is validated on survivors instead of on the full universe.
- Shared-account validation must remain serialized and portfolio-context aware.
- Only the Promotion Steward may write the live manifest or finalize production-book mutations.
- Control-plane stewards may publish packets and gates, but not production strategy changes.

## Split Recommendation

- `discovery`: `family_cohort`
- `exhaustive_validation`: `ticker_bundle`
- `shared_account_validation`: `portfolio_context`
- `production_decision`: `live_book_single_writer`

## Agent Contracts

### Inventory Steward

- Plane: `control`
- Lane type: `control_plane`
- Split axis: `governance`
- Automation level: `autonomous`
- Approval level: `packet_only`
- Preferred machine now: `current_research_machine`
- Preferred machine target: `either_machine`
- Writes live state: `false`
- May launch backtests: `false`
- May edit strategy code: `false`
- May materialize data: `false`
- May write live manifest: `false`
- May update runner gate: `false`
- May publish review packets: `true`
- Success gate: Coverage gaps and ready-universe counts are current before any new wave launches.
- Hands off to: Strategy Family Steward, Data Prep Steward, Bear Directional, Bear Premium, Bear Convexity, Butterfly Lab
- Prohibited actions: `write_live_manifest`, `approve_production_changes`, `edit_strategy_family_definitions`
- Notes: Owns universe accounting and under-tested family/ticker ranking.

### Strategy Family Steward

- Plane: `control`
- Lane type: `control_plane`
- Split axis: `family_taxonomy`
- Automation level: `autonomous`
- Approval level: `packet_only`
- Preferred machine now: `current_research_machine`
- Preferred machine target: `either_machine`
- Writes live state: `false`
- May launch backtests: `false`
- May edit strategy code: `false`
- May materialize data: `false`
- May write live manifest: `false`
- May update runner gate: `false`
- May publish review packets: `true`
- Success gate: Family priorities are refreshed before major research or review waves.
- Hands off to: Strategy Architect, Inventory Steward, Reporting Steward
- Prohibited actions: `write_live_manifest`, `approve_production_changes`
- Notes: Single owner of family taxonomy and family-priority labels.

### Execution Calibration Steward

- Plane: `control`
- Lane type: `control_plane`
- Split axis: `execution_feedback`
- Automation level: `autonomous`
- Approval level: `packet_only`
- Preferred machine now: `either_machine`
- Preferred machine target: `new_machine`
- Writes live state: `false`
- May launch backtests: `false`
- May edit strategy code: `false`
- May materialize data: `false`
- May write live manifest: `false`
- May update runner gate: `false`
- May publish review packets: `true`
- Success gate: Execution evidence and posture are refreshed before major research profile or scoring decisions.
- Hands off to: Strategy Family Steward, Reporting Steward
- Prohibited actions: `write_live_manifest`, `approve_production_changes`, `override_execution_evidence_without_packet`
- Notes: Owns the feedback loop from the execution plane back into research and nightly operator policy.

### Data Prep Steward

- Plane: `research`
- Lane type: `control_plane`
- Split axis: `data_readiness`
- Automation level: `autonomous`
- Approval level: `packet_only`
- Preferred machine now: `current_research_machine`
- Preferred machine target: `either_machine`
- Writes live state: `false`
- May launch backtests: `false`
- May edit strategy code: `false`
- May materialize data: `true`
- May write live manifest: `false`
- May update runner gate: `false`
- May publish review packets: `true`
- Success gate: Priority symbols are materialized before discovery consumes them.
- Hands off to: Inventory Steward, Bear Directional, Bear Premium, Bear Convexity, Butterfly Lab
- Prohibited actions: `write_live_manifest`, `approve_production_changes`, `launch_discovery_without_refreshed_coverage`
- Notes: Keeps data prep separate from research execution.

### Strategy Architect

- Plane: `research`
- Lane type: `control_plane`
- Split axis: `strategy_surface`
- Automation level: `human_guided`
- Approval level: `human_gated`
- Preferred machine now: `current_research_machine`
- Preferred machine target: `current_research_machine`
- Writes live state: `false`
- May launch backtests: `false`
- May edit strategy code: `true`
- May materialize data: `false`
- May write live manifest: `false`
- May update runner gate: `false`
- May publish review packets: `false`
- Success gate: New families are wired into reporting before runners use them.
- Hands off to: Inventory Steward, Balanced Expansion
- Prohibited actions: `write_live_manifest`, `auto_promote_new_families`
- Notes: Single editor of strategy-family definitions.

### Bear Directional

- Plane: `research`
- Lane type: `discovery`
- Split axis: `family_cohort`
- Automation level: `autonomous`
- Approval level: `packet_only`
- Preferred machine now: `current_research_machine`
- Preferred machine target: `either_machine`
- Writes live state: `false`
- May launch backtests: `true`
- May edit strategy code: `false`
- May materialize data: `false`
- May write live manifest: `false`
- May update runner gate: `false`
- May publish review packets: `false`
- Strategy set: `down_choppy_only`
- Selection profile: `down_choppy_focus`
- Family filters: `single_leg_long_put,debit_put_spread`
- Success gate: No promotions. Survivors must show friction-aware strength.
- Hands off to: Reporting Steward
- Prohibited actions: `write_live_manifest`, `expand_scope_beyond_assigned_family_lane`
- Notes: Discovery lane for bearish directional structures only.

### Bear Premium

- Plane: `research`
- Lane type: `discovery`
- Split axis: `family_cohort`
- Automation level: `autonomous`
- Approval level: `packet_only`
- Preferred machine now: `current_research_machine`
- Preferred machine target: `either_machine`
- Writes live state: `false`
- May launch backtests: `true`
- May edit strategy code: `false`
- May materialize data: `false`
- May write live manifest: `false`
- May update runner gate: `false`
- May publish review packets: `false`
- Strategy set: `down_choppy_only`
- Selection profile: `down_choppy_focus`
- Family filters: `credit_call_spread,iron_condor,iron_butterfly`
- Success gate: No promotions. Survivors must show friction-aware strength.
- Hands off to: Reporting Steward
- Prohibited actions: `write_live_manifest`, `expand_scope_beyond_assigned_family_lane`
- Notes: Discovery lane for premium-defense structures only.

### Bear Convexity

- Plane: `research`
- Lane type: `discovery`
- Split axis: `family_cohort`
- Automation level: `autonomous`
- Approval level: `packet_only`
- Preferred machine now: `current_research_machine`
- Preferred machine target: `either_machine`
- Writes live state: `false`
- May launch backtests: `true`
- May edit strategy code: `false`
- May materialize data: `false`
- May write live manifest: `false`
- May update runner gate: `false`
- May publish review packets: `false`
- Strategy set: `down_choppy_only`
- Selection profile: `down_choppy_focus`
- Family filters: `put_backspread,long_straddle,long_strangle`
- Success gate: No promotions. Survivors must show friction-aware strength.
- Hands off to: Reporting Steward
- Prohibited actions: `write_live_manifest`, `expand_scope_beyond_assigned_family_lane`
- Notes: Discovery lane for convexity and long-vol structures only.

### Butterfly Lab

- Plane: `research`
- Lane type: `discovery`
- Split axis: `family_cohort`
- Automation level: `autonomous`
- Approval level: `packet_only`
- Preferred machine now: `current_research_machine`
- Preferred machine target: `either_machine`
- Writes live state: `false`
- May launch backtests: `true`
- May edit strategy code: `false`
- May materialize data: `false`
- May write live manifest: `false`
- May update runner gate: `false`
- May publish review packets: `false`
- Strategy set: `down_choppy_only`
- Selection profile: `down_choppy_focus`
- Family filters: `put_butterfly,broken_wing_put_butterfly`
- Success gate: No promotions. Survivors must show friction-aware strength.
- Hands off to: Reporting Steward
- Prohibited actions: `write_live_manifest`, `expand_scope_beyond_assigned_family_lane`
- Notes: Discovery lane for butterfly structures only.

### Down/Choppy Exhaustive

- Plane: `research`
- Lane type: `deep_dive`
- Split axis: `ticker_bundle`
- Automation level: `autonomous`
- Approval level: `packet_only`
- Preferred machine now: `current_research_machine`
- Preferred machine target: `either_machine`
- Writes live state: `false`
- May launch backtests: `true`
- May edit strategy code: `false`
- May materialize data: `false`
- May write live manifest: `false`
- May update runner gate: `false`
- May publish review packets: `false`
- Strategy set: `down_choppy_exhaustive`
- Selection profile: `down_choppy_focus`
- Success gate: Only shortlisted survivors advance into this phase.
- Hands off to: Shared-Account Validator, Reporting Steward
- Prohibited actions: `write_live_manifest`, `widen_back_to_full_discovery_scope`
- Notes: Exhaustive validation lane for down/choppy survivors.

### Balanced Expansion

- Plane: `research`
- Lane type: `deep_dive`
- Split axis: `ticker_bundle`
- Automation level: `autonomous`
- Approval level: `packet_only`
- Preferred machine now: `current_research_machine`
- Preferred machine target: `either_machine`
- Writes live state: `false`
- May launch backtests: `true`
- May edit strategy code: `false`
- May materialize data: `false`
- May write live manifest: `false`
- May update runner gate: `false`
- May publish review packets: `false`
- Strategy set: `family_expansion`
- Selection profile: `balanced`
- Success gate: Cross-regime benchmark names and validated survivors only.
- Hands off to: Shared-Account Validator, Reporting Steward
- Prohibited actions: `write_live_manifest`, `skip_shortlist_or_validation_provenance`
- Notes: Deep-dive lane for balanced cross-regime validation.

### Shared-Account Validator

- Plane: `research`
- Lane type: `validation`
- Split axis: `portfolio_context`
- Automation level: `autonomous`
- Approval level: `packet_only`
- Preferred machine now: `current_research_machine`
- Preferred machine target: `new_machine`
- Writes live state: `false`
- May launch backtests: `true`
- May edit strategy code: `false`
- May materialize data: `false`
- May write live manifest: `false`
- May update runner gate: `false`
- May publish review packets: `true`
- Strategy set: `promotion_review`
- Selection profile: `portfolio_first`
- Success gate: Only portfolio-improving challengers may advance.
- Hands off to: Reporting Steward, Promotion Steward
- Prohibited actions: `write_live_manifest`, `approve_production_changes`, `treat_standalone_strength_as_production_ready`
- Notes: Single serialized validation lane by design.

### Reporting Steward

- Plane: `control`
- Lane type: `control_plane`
- Split axis: `review_packet`
- Automation level: `autonomous`
- Approval level: `packet_only`
- Preferred machine now: `current_research_machine`
- Preferred machine target: `either_machine`
- Writes live state: `false`
- May launch backtests: `false`
- May edit strategy code: `false`
- May materialize data: `false`
- May write live manifest: `false`
- May update runner gate: `true`
- May publish review packets: `true`
- Success gate: Reports must separate discovery, validation, and production-ready evidence.
- Hands off to: Promotion Steward
- Prohibited actions: `write_live_manifest`, `approve_production_changes`
- Notes: Turns raw results into operator-readable decision packets.

### Promotion Steward

- Plane: `execution`
- Lane type: `single_writer`
- Split axis: `live_book`
- Automation level: `human_gated`
- Approval level: `human_gated`
- Preferred machine now: `new_machine`
- Preferred machine target: `new_machine`
- Writes live state: `true`
- May launch backtests: `false`
- May edit strategy code: `false`
- May materialize data: `false`
- May write live manifest: `true`
- May update runner gate: `true`
- May publish review packets: `false`
- Success gate: Exactly one writer. Never shrink the live universe accidentally.
- Prohibited actions: `run_parallel_live_manifest_writers`, `push_unreviewed_manifest_changes`
- Notes: The only role allowed to mutate the live book.

