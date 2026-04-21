# Agent Operating Model

## Machine Budget

- Logical CPUs: 16
- Total RAM: 63.46 GB
- Free RAM at plan time: 33.45 GB
- Discovery lanes: 4
- Heavy lanes: 2
- Validation lanes: 1

## Governance

- Parallelize discovery and prep, serialize validation and promotion.
- Never allow concurrent live-manifest writers.
- Every large lane must emit run_manifest.json and append to run_registry.jsonl.
- Promotion requires friction-aware results plus portfolio-context validation.
- Checkpoint reuse is allowed only when the run signature still matches.
- Build a phase-specific launch pack with `build_agent_wave_launch_pack.py` before starting a large wave, then use `launch_agent_wave.ps1` so execution follows the generated pack instead of ad hoc commands.

## Agent Roles

### Inventory Steward

- Lane type: `control_plane`
- Parallelism: `1`
- Writes live state: `false`
- Scripts: `build_strategy_repo.py, build_ticker_family_coverage.py, build_agent_sharding_plan.py, build_agent_operating_model.py`
- Inputs: backtester_registry.csv, backtester_ready manifests, strategy_repo.json snapshots
- Outputs: strategy_repo.json, ticker_family_coverage.md, agent_sharding_plan.json, agent_operating_model.json
- Success gate: Coverage gaps, ready-universe counts, and family priorities are refreshed before any new wave launches.
- Hands off to: Data Prep Steward, Bear Directional, Bear Premium, Bear Convexity, Butterfly Lab
- Notes: Owns universe accounting and decides which families/symbols are still under-tested.

### Data Prep Steward

- Lane type: `control_plane`
- Parallelism: `1`
- Writes live state: `false`
- Scripts: `materialize_backtester_ready.py, launch_down_choppy_program.ps1`
- Inputs: staged bundle zips, registry-only symbols, next_wave_prep_commands.ps1
- Outputs: expanded backtester_ready universe, materialization_status.json
- Success gate: Priority staged/registry symbols are materialized before discovery lanes consume them.
- Hands off to: Inventory Steward, Bear Directional, Bear Premium, Bear Convexity, Butterfly Lab
- Notes: Single owner of prep/bootstrap so discovery runners do not mix data prep with research.

### Strategy Architect

- Lane type: `control_plane`
- Parallelism: `1`
- Writes live state: `false`
- Scripts: `backtest_qqq_greeks_portfolio.py, run_multiticker_cleanroom_portfolio.py, build_strategy_repo.py`
- Inputs: strategy_repo.json, ticker_family_coverage.md, loss/postmortem findings
- Outputs: new or expanded strategy families, parameter-surface changes
- Success gate: Any new family must be wired into the catalog, family filters, and reporting before runners use it.
- Hands off to: Inventory Steward, Balanced Expansion
- Notes: Single editor of strategy-family definitions to avoid conflicting local forks.

### Bear Directional

- Lane type: `discovery`
- Parallelism: `1`
- Writes live state: `false`
- Strategy set: `down_choppy_only`
- Selection profile: `down_choppy_focus`
- Family include filters: `single_leg_long_put,debit_put_spread`
- Scripts: `launch_down_choppy_family_wave.ps1, run_multiticker_cleanroom_portfolio.py`
- Inputs: backtester_ready tickers, coverage-ranked cohort lists, family include filters
- Outputs: per-lane research_dir, per-ticker summaries, run_manifest.json, run_registry.jsonl entries
- Success gate: No promotions. Survivors must show friction-aware strength and acceptable cheap-premium exposure.
- Hands off to: Reporting Steward
- Notes: Owns only the family lane `single_leg_long_put,debit_put_spread` and should not overlap with sibling discovery lanes.

### Bear Premium

- Lane type: `discovery`
- Parallelism: `1`
- Writes live state: `false`
- Strategy set: `down_choppy_only`
- Selection profile: `down_choppy_focus`
- Family include filters: `credit_call_spread,iron_condor,iron_butterfly`
- Scripts: `launch_down_choppy_family_wave.ps1, run_multiticker_cleanroom_portfolio.py`
- Inputs: backtester_ready tickers, coverage-ranked cohort lists, family include filters
- Outputs: per-lane research_dir, per-ticker summaries, run_manifest.json, run_registry.jsonl entries
- Success gate: No promotions. Survivors must show friction-aware strength and acceptable cheap-premium exposure.
- Hands off to: Reporting Steward
- Notes: Owns only the family lane `credit_call_spread,iron_condor,iron_butterfly` and should not overlap with sibling discovery lanes.

### Bear Convexity

- Lane type: `discovery`
- Parallelism: `1`
- Writes live state: `false`
- Strategy set: `down_choppy_only`
- Selection profile: `down_choppy_focus`
- Family include filters: `put_backspread,long_straddle,long_strangle`
- Scripts: `launch_down_choppy_family_wave.ps1, run_multiticker_cleanroom_portfolio.py`
- Inputs: backtester_ready tickers, coverage-ranked cohort lists, family include filters
- Outputs: per-lane research_dir, per-ticker summaries, run_manifest.json, run_registry.jsonl entries
- Success gate: No promotions. Survivors must show friction-aware strength and acceptable cheap-premium exposure.
- Hands off to: Reporting Steward
- Notes: Owns only the family lane `put_backspread,long_straddle,long_strangle` and should not overlap with sibling discovery lanes.

### Butterfly Lab

- Lane type: `discovery`
- Parallelism: `1`
- Writes live state: `false`
- Strategy set: `down_choppy_only`
- Selection profile: `down_choppy_focus`
- Family include filters: `put_butterfly,broken_wing_put_butterfly`
- Scripts: `launch_down_choppy_family_wave.ps1, run_multiticker_cleanroom_portfolio.py`
- Inputs: backtester_ready tickers, coverage-ranked cohort lists, family include filters
- Outputs: per-lane research_dir, per-ticker summaries, run_manifest.json, run_registry.jsonl entries
- Success gate: No promotions. Survivors must show friction-aware strength and acceptable cheap-premium exposure.
- Hands off to: Reporting Steward
- Notes: Owns only the family lane `put_butterfly,broken_wing_put_butterfly` and should not overlap with sibling discovery lanes.

### Down/Choppy Exhaustive

- Lane type: `deep_dive`
- Parallelism: `1`
- Writes live state: `false`
- Strategy set: `down_choppy_exhaustive`
- Selection profile: `down_choppy_focus`
- Scripts: `build_family_wave_shortlist.py, launch_down_choppy_program.ps1, run_multiticker_cleanroom_portfolio.py`
- Inputs: Phase 1 shortlist, friction-aware lane summaries
- Outputs: deeper walkforward summaries, family rankings, premium-bucket rankings, run manifests
- Success gate: Top decile discovery survivors only.
- Hands off to: Shared-Account Validator, Reporting Steward
- Notes: Heavy lanes should stay small and resume-safe; no GitHub promotion from this phase.

### Balanced Expansion

- Lane type: `deep_dive`
- Parallelism: `1`
- Writes live state: `false`
- Strategy set: `family_expansion`
- Selection profile: `balanced`
- Scripts: `build_family_wave_shortlist.py, run_core_strategy_expansion_overnight.py, run_multiticker_cleanroom_portfolio.py`
- Inputs: Phase 1 shortlist, friction-aware lane summaries
- Outputs: deeper walkforward summaries, family rankings, premium-bucket rankings, run manifests
- Success gate: Balanced benchmark names and cross-regime validation.
- Hands off to: Shared-Account Validator, Reporting Steward
- Notes: Heavy lanes should stay small and resume-safe; no GitHub promotion from this phase.

### Shared-Account Validator

- Lane type: `validation`
- Parallelism: `1`
- Writes live state: `false`
- Strategy set: `promotion_review`
- Selection profile: `portfolio_first`
- Scripts: `run_multiticker_cleanroom_portfolio.py, export_promoted_strategies.py`
- Inputs: deep-dive winners, current live manifest, shared-account baselines
- Outputs: promotion candidate set, promoted_strategies.yaml, shared-account comparisons
- Success gate: Only strategies that improve portfolio context or clearly replace weaker live sleeves may pass.
- Hands off to: Reporting Steward, Promotion Steward
- Notes: Single validation lane by design so final comparisons stay consistent.

### Reporting Steward

- Lane type: `control_plane`
- Parallelism: `1`
- Writes live state: `false`
- Scripts: `build_family_wave_shortlist.py, summarize_tournament_conveyor.py, build_agent_operating_model.py`
- Inputs: lane summaries, family rankings, friction profiles, run manifests
- Outputs: family_wave_shortlist.md, phase2_plan.json, tournament_conveyor_summary.json, promotion review packet
- Success gate: Reports must separate discovery, exhaustive, validation, and promotion-ready winners.
- Hands off to: Shared-Account Validator, Promotion Steward
- Notes: This lane turns raw results into decision artifacts and keeps auditability readable.

### Promotion Steward

- Lane type: `single_writer`
- Parallelism: `1`
- Writes live state: `true`
- Scripts: `export_promoted_strategies.py, wait_and_sync_live_manifest.ps1, sync_live_strategy_manifest.py`
- Inputs: approved promoted_strategies.yaml, shared-account validation results, current GitHub live manifest
- Outputs: merged live manifest, GitHub commit/push, promotion audit trail
- Success gate: Exactly one writer. Never shrink the live universe accidentally. Only push when the manifest truly improves.
- Notes: No other agent may write the live manifest, merge promotions, or push live-book changes.

## Phase Flow

- `Phase 0 - Inventory Refresh`: Inventory Steward
  - feeds: Data Prep Steward, Strategy Architect, Discovery lanes
- `Phase 0.5 - Data Prep`: Data Prep Steward
  - feeds: Inventory Steward, Discovery lanes
- `Phase 1 - Discovery`: Discovery lanes
  - feeds: Reporting Steward
- `Phase 2 - Exhaustive Follow-Up`: Down/Choppy Exhaustive
  - feeds: Reporting Steward, Shared-Account Validator
- `Phase 3 - Balanced Expansion`: Balanced Expansion
  - feeds: Reporting Steward, Shared-Account Validator
- `Phase 4 - Shared-Account Validation`: Shared-Account Validator
  - feeds: Promotion Steward
- `Phase 5 - Promotion`: Promotion Steward

## Required Artifacts

- Per lane:
  - `run_manifest.json`
  - `run_registry.jsonl entry`
  - `*_summary.json`
  - `family_rankings.csv`
  - `premium_bucket_rankings.csv`
- Promotion inputs:
  - `promoted_strategies.yaml`
  - `shared-account comparison`
  - `current live manifest snapshot`
