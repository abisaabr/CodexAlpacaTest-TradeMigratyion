# Agent Sharding Plan

## Machine Profile

- Logical CPUs: 16
- Total RAM: 63.46 GB
- Free RAM at plan time: 35.15 GB
- Lean parallel backtests: 4
- Heavy parallel backtests: 2
- Validation lane concurrency: 1
- Recommended total Codex agents: 8

## Data Universe

- Staged bundle universe: 59 tickers
- Backtester-ready universe: 88 tickers
- Registry-symbol universe: 159 tickers
- Full target universe: 159 tickers

## Strategy Inventory

- Cataloged base strategies: 92
- Ready ticker count in repo snapshot: 88
- Researched ticker count in repo snapshot: 41

### Highest-Value Family Gaps

- `Credit call spread`: 13 base strategies, 1 ever selected, 0 ever promoted
- `Single-leg long put`: 17 base strategies, 7 ever selected, 6 ever promoted
- `Debit put spread`: 7 base strategies, 0 ever selected, 0 ever promoted
- `Iron condor`: 6 base strategies, 1 ever selected, 0 ever promoted
- `Long strangle`: 5 base strategies, 0 ever selected, 0 ever promoted
- `Put backspread`: 5 base strategies, 0 ever selected, 0 ever promoted
- `Long straddle`: 5 base strategies, 1 ever selected, 0 ever promoted
- `Credit put spread`: 5 base strategies, 2 ever selected, 0 ever promoted
- `Call butterfly`: 4 base strategies, 0 ever selected, 0 ever promoted
- `Put butterfly`: 4 base strategies, 0 ever selected, 0 ever promoted

## Immediate Agent Layout

- `Inventory Steward`: Refresh strategy repo, maintain cohort lists, and track family coverage gaps.
- `Promotion Steward`: Serialize shared-account validation and GitHub live-manifest promotion.
- `Bear Directional`: `down_choppy_only` on Single-leg long put, Debit put spread
  - family include args: `single_leg_long_put,debit_put_spread`
- `Bear Premium`: `down_choppy_only` on Credit call spread, Iron condor, Iron butterfly
  - family include args: `credit_call_spread,iron_condor,iron_butterfly`
- `Bear Convexity`: `down_choppy_only` on Put backspread, Long straddle, Long strangle
  - family include args: `put_backspread,long_straddle,long_strangle`
- `Butterfly Lab`: `down_choppy_only` on Put butterfly, Broken-wing put butterfly
  - family include args: `put_butterfly,broken_wing_put_butterfly`
- `Down/Choppy Exhaustive`: `down_choppy_exhaustive` (Top decile discovery survivors only.)
- `Balanced Expansion`: `family_expansion` (Balanced benchmark names and cross-regime validation.)
- `Shared-Account Validator`: Portfolio-level retest before GitHub promotion.

See [AGENT_OPERATING_MODEL.md](./AGENT_OPERATING_MODEL.md) for the stricter ownership model, handoff artifacts, single-writer rules, and agent-by-agent script boundaries.

## Phased Plan

### Phase 0 - Inventory Refresh

- Goal: Refresh strategy repo against the broader ticker lake before launching new waves.
- Max parallel backtests: 0
- Rebuild strategy coverage after the latest 59+ bundle universe is staged.
- Separate currently backtester-ready tickers from full staged-but-not-ready tickers.
- `build_agent_sharding_plan.py` can now auto-discover an existing strategy repo snapshot or auto-build one if the expected JSON is missing.
- Use `cleanroom/code/qqq_options_30d_cleanroom/build_coverage_next_wave_plan.py` to generate the ticker-family coverage matrix, family/ticker gap summaries, and the next-wave discovery/exhaustive lane commands before launching another broad sweep.
- Use `cleanroom/code/qqq_options_30d_cleanroom/build_ticker_family_coverage.py` to build the 159-symbol ticker-family coverage matrix and emit `next_wave_plan.json` / `next_wave_commands.ps1` before starting the next agent wave.
- Use `cleanroom/code/qqq_options_30d_cleanroom/materialize_backtester_ready.py` to bootstrap `staged_only` and `registry_only` symbols into `backtester_ready` before the next discovery wave when the ready universe is too narrow.

### Phase 1 - Down/Choppy Discovery

- Goal: Run fast, low-promotion-risk discovery across the currently backtester-ready universe.
- Max parallel backtests: 4
- Strategy set: `down_choppy_only`
- Selection profile: `down_choppy_focus`
- Promotion mode: `none`
- Prefer coverage-ranked discovery when possible: run `build_ticker_family_coverage.py` first and seed the four Phase 1 lanes from the highest-gap ready symbols instead of blindly using the full ready universe.
- In `coverage_ranked` mode, `launch_down_choppy_program.ps1` can bootstrap the ready universe first by materializing the planner's `staged_materialization` and `registry_download` candidates, then regenerate the discovery plan against the expanded ready set.
- Cohorts:
  - `R01`: 8 tickers
  - `R02`: 8 tickers
  - `R03`: 8 tickers
  - `R04`: 7 tickers

### Phase 2 - Exhaustive Follow-Up

- Goal: Retest only shortlisted tickers/families with the wider down/choppy surface.
- Max parallel backtests: 2
- Strategy set: `down_choppy_exhaustive`
- Selection profile: `down_choppy_focus`
- Promotion mode: `none`
- Only pass survivors from Phase 1 with good friction profile and low cheap-premium dependence.
- Keep shard size smaller than discovery to protect RAM.
- Use `cleanroom/code/qqq_options_30d_cleanroom/build_family_wave_shortlist.py` after the four discovery lanes finish.
- The shortlist builder emits one readable markdown report plus `phase2_plan.json` / `phase2_commands.ps1` so the two exhaustive lanes can start without manual ticker triage.
- Use `cleanroom/code/qqq_options_30d_cleanroom/launch_down_choppy_program.ps1` as the top-level dry-run-safe entrypoint when you want one script to stage discovery, run the shortlist, and launch the two exhaustive follow-up lanes.
- `launch_down_choppy_program.ps1` also supports `coverage_ranked` discovery mode so the same entrypoint can use `build_ticker_family_coverage.py` before staging Phase 1.

### Phase 3 - Balanced Cross-Regime Benchmark

- Goal: Run family_expansion on core symbols and any candidates that look robust beyond down/choppy.
- Max parallel backtests: 2
- Strategy set: `family_expansion`
- Selection profile: `balanced`
- Promotion mode: `none`

### Phase 4 - Shared-Account Validation

- Goal: Retest winners in portfolio context and reject standalone-only false positives.
- Max parallel backtests: 1
- Strategy set: `shared_account_validation`
- Selection profile: `portfolio_first`
- Promotion mode: `merge_only`

### Phase 5 - Promotion

- Goal: Serialize GitHub manifest updates so the paper runner never races on live state.
- Max parallel backtests: 0
- Exactly one promotion steward.
- No concurrent manifest writers.

## Full 159-Ticker Queue Shape

- Build 12 queued cohorts and run 4 at a time.
- Total waves: 3
- The runner now supports family include/exclude filters, so agents can own disjoint family lanes.
- Use ticker cohorts plus family-lane filters together for the cleanest parallelization.
- For the full 159-ticker universe, queue all cohorts but keep only the recommended concurrency active at once.
