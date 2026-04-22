# Tournament Profile Registry

This registry is the control-plane source of truth for which institutional tournaments exist, which are executable today, and which are still planned.

## Defaults

- Default profile: `down_choppy_coverage_ranked`
- Active profiles: `down_choppy_coverage_ranked, down_choppy_full_ready`
- Executable profiles: `balanced_family_expansion_benchmark, down_choppy_coverage_ranked, down_choppy_full_ready, opening_30m_convexity_butterfly, opening_30m_premium_defense, opening_30m_single_vs_multileg`

## Profiles

### down_choppy_coverage_ranked

- Status: `active`
- Executable now: `true`
- Objective: Primary institutional nightly challenger cycle for down and choppy markets.
- Regime focus: `down, choppy`
- Session focus: `full_session`
- Execution window: `all_day`
- Entrypoint: `launch_nightly_operator_cycle.ps1`
- Underlying program: `launch_down_choppy_program.ps1`
- Discovery source: `coverage_ranked`
- Bootstrap ready universe: `true`
- Strategy sets: `down_choppy_only, down_choppy_exhaustive`
- Selection profiles: `down_choppy_focus`
- Phase 1 split axis: `family_cohort`
- Phase 2 split axis: `ticker_bundle`
- Validation split axis: `portfolio_context`
- Promotion mode: `review_only`
- Execution risk tier: `moderate`
- Entry friction sensitivity: `medium`
- Exit model dependency: `medium`
- Research bias: `premium_defense_mixed`
- Minimum execution evidence strength: `limited_entry_only`
- Requires broker-order audit coverage: `false`
- Requires broker-activity audit coverage: `false`
- Requires exit telemetry: `false`
- Preferred machine now: `current_research_machine`
- Preferred machine target: `either_machine`
- Families: `Single-leg long put`, `Debit put spread`, `Credit call spread`, `Iron condor`, `Iron butterfly`, `Put backspread`, `Long straddle`, `Long strangle`, `Put butterfly`, `Broken-wing put butterfly`
- Notes: Default nightly operator profile because it exercises the full discovery-to-morning-handoff chain without auto-promoting the live book.

### down_choppy_full_ready

- Status: `active`
- Executable now: `true`
- Objective: Fallback nightly challenger cycle when breadth over the current ready universe matters more than gap-ranked precision.
- Regime focus: `down, choppy`
- Session focus: `full_session`
- Execution window: `all_day`
- Entrypoint: `launch_nightly_operator_cycle.ps1`
- Underlying program: `launch_down_choppy_program.ps1`
- Discovery source: `full_ready`
- Bootstrap ready universe: `false`
- Strategy sets: `down_choppy_only, down_choppy_exhaustive`
- Selection profiles: `down_choppy_focus`
- Phase 1 split axis: `family_cohort`
- Phase 2 split axis: `ticker_bundle`
- Validation split axis: `portfolio_context`
- Promotion mode: `review_only`
- Execution risk tier: `moderate`
- Entry friction sensitivity: `medium`
- Exit model dependency: `medium`
- Research bias: `premium_defense_mixed`
- Minimum execution evidence strength: `limited_entry_only`
- Requires broker-order audit coverage: `false`
- Requires broker-activity audit coverage: `false`
- Requires exit telemetry: `false`
- Preferred machine now: `current_research_machine`
- Preferred machine target: `either_machine`
- Families: `Single-leg long put`, `Debit put spread`, `Credit call spread`, `Iron condor`, `Iron butterfly`, `Put backspread`, `Long straddle`, `Long strangle`, `Put butterfly`, `Broken-wing put butterfly`
- Notes: Use when the ready universe is already broad enough and we want a direct run without extra bootstrap materialization.

### opening_30m_single_vs_multileg

- Status: `partial`
- Executable now: `true`
- Objective: Institutional opening-window shootout between directional single-legs and defined-risk multi-leg structures.
- Regime focus: `bull, bear, choppy`
- Session focus: `opening_30m`
- Execution window: `first_30_minutes`
- Entrypoint: `launch_nightly_operator_cycle.ps1`
- Underlying program: `launch_down_choppy_program.ps1`
- Discovery source: `coverage_ranked`
- Bootstrap ready universe: `true`
- Strategy sets: `opening_window_single_vs_multileg`
- Selection profiles: `opening_window_balanced`
- Phase 1 split axis: `family_cohort`
- Phase 2 split axis: `ticker_bundle`
- Validation split axis: `portfolio_context`
- Promotion mode: `review_only`
- Execution risk tier: `aggressive`
- Entry friction sensitivity: `high`
- Exit model dependency: `high`
- Research bias: `balanced_directional_vs_multileg`
- Minimum execution evidence strength: `broad`
- Requires broker-order audit coverage: `true`
- Requires broker-activity audit coverage: `true`
- Requires exit telemetry: `true`
- Preferred machine now: `current_research_machine`
- Preferred machine target: `new_machine`
- Families: `Single-leg long call`, `Single-leg long put`, `Debit call spread`, `Debit put spread`, `Credit call spread`, `Credit put spread`, `Iron condor`, `Iron butterfly`, `Call butterfly`, `Put butterfly`, `Call backspread`, `Put backspread`
- Notes: Governed execution is now wired through the nightly operator, but activation still depends on broad broker-audited execution evidence, reliable exit telemetry, and a higher execution-risk ceiling.

### opening_30m_premium_defense

- Status: `partial`
- Executable now: `true`
- Objective: Focused opening-session premium-defense tournament for bear and choppy regimes.
- Regime focus: `down, choppy`
- Session focus: `opening_30m`
- Execution window: `first_30_minutes`
- Entrypoint: `launch_nightly_operator_cycle.ps1`
- Underlying program: `launch_down_choppy_program.ps1`
- Discovery source: `coverage_ranked`
- Bootstrap ready universe: `true`
- Strategy sets: `opening_window_premium_defense`
- Selection profiles: `opening_window_defensive`
- Phase 1 split axis: `family_cohort`
- Phase 2 split axis: `ticker_bundle`
- Validation split axis: `portfolio_context`
- Promotion mode: `review_only`
- Execution risk tier: `conservative`
- Entry friction sensitivity: `low`
- Exit model dependency: `medium`
- Research bias: `defined_risk_and_premium_defense`
- Minimum execution evidence strength: `entry_and_reconciliation`
- Requires broker-order audit coverage: `true`
- Requires broker-activity audit coverage: `true`
- Requires exit telemetry: `false`
- Preferred machine now: `current_research_machine`
- Preferred machine target: `new_machine`
- Families: `Credit call spread`, `Debit put spread`, `Iron condor`, `Iron butterfly`, `Put butterfly`
- Notes: Governed execution is now wired through the nightly operator, but activation still depends on stronger broker-audited execution evidence.

### opening_30m_convexity_butterfly

- Status: `partial`
- Executable now: `true`
- Objective: Focused opening-session convexity and butterfly profile for early expansion or reversal moves.
- Regime focus: `down, choppy`
- Session focus: `opening_30m`
- Execution window: `first_30_minutes`
- Entrypoint: `launch_nightly_operator_cycle.ps1`
- Underlying program: `launch_down_choppy_program.ps1`
- Discovery source: `coverage_ranked`
- Bootstrap ready universe: `true`
- Strategy sets: `opening_window_convexity_butterfly`
- Selection profiles: `opening_window_convexity`
- Phase 1 split axis: `family_cohort`
- Phase 2 split axis: `ticker_bundle`
- Validation split axis: `portfolio_context`
- Promotion mode: `review_only`
- Execution risk tier: `aggressive`
- Entry friction sensitivity: `high`
- Exit model dependency: `high`
- Research bias: `convexity_and_long_vol`
- Minimum execution evidence strength: `broad`
- Requires broker-order audit coverage: `true`
- Requires broker-activity audit coverage: `true`
- Requires exit telemetry: `true`
- Preferred machine now: `current_research_machine`
- Preferred machine target: `new_machine`
- Families: `Put backspread`, `Long straddle`, `Long strangle`, `Put butterfly`, `Broken-wing put butterfly`
- Notes: Governed execution is now wired through the nightly operator, but activation still depends on broad broker-audited execution evidence and reliable exit telemetry.

### balanced_family_expansion_benchmark

- Status: `partial`
- Executable now: `true`
- Objective: Cross-regime balanced family-expansion benchmark for diversified research and replacement pressure on the live book.
- Regime focus: `bull, bear, choppy`
- Session focus: `full_session`
- Execution window: `all_day`
- Entrypoint: `launch_nightly_operator_cycle.ps1`
- Underlying program: `launch_balanced_family_expansion_program.ps1`
- Discovery source: `coverage_ranked`
- Bootstrap ready universe: `true`
- Strategy sets: `family_expansion`
- Selection profiles: `balanced`
- Phase 1 split axis: `ticker_bundle`
- Phase 2 split axis: `portfolio_context`
- Validation split axis: `portfolio_context`
- Promotion mode: `review_only`
- Execution risk tier: `moderate`
- Entry friction sensitivity: `medium`
- Exit model dependency: `medium`
- Research bias: `balanced`
- Minimum execution evidence strength: `entry_and_reconciliation`
- Requires broker-order audit coverage: `true`
- Requires broker-activity audit coverage: `true`
- Requires exit telemetry: `false`
- Preferred machine now: `current_research_machine`
- Preferred machine target: `either_machine`
- Families: `Single-leg long call`, `Single-leg long put`, `Debit call spread`, `Debit put spread`, `Credit call spread`, `Credit put spread`, `Iron condor`, `Iron butterfly`, `Call butterfly`, `Put butterfly`, `Broken-wing call butterfly`, `Broken-wing put butterfly`, `Call backspread`, `Put backspread`, `Long straddle`, `Long strangle`
- Notes: Governed execution is now wired through the nightly operator as a compact benchmark bundle, but activation still depends on stronger broker-audited execution evidence.

