# New Machine Codex Prompts

Use these prompts on the destination Windows machine after cloning `codexalpaca_repo`.

## 1. Bootstrap The Machine

```text
Open C:\Users\<you>\Downloads\codexalpaca_repo. Set this machine up for the multi-ticker paper trader on Windows using the native path, not Docker. Run the setup script, verify the Python environment, verify tests and doctor checks, and install the scheduled tasks. Use Google Drive for the shared ownership lease path. Do not start trading yet. Summarize anything I still need to provide locally.
```

## 2. Restore The Live Runtime Handoff

```text
In C:\Users\<you>\Downloads\codexalpaca_repo, restore the latest multi-ticker runtime migration bundle from C:\Users\<you>\Downloads\<runtime-bundle-folder>. Set MULTI_TICKER_MACHINE_LABEL to a new unique label for this machine, keep the shared Google Drive lease path, run the standby failover preflight, and make sure the machine is safe to become the standby or active runner. Do not modify strategy logic or risk settings.
```

## 3. Restore The Cleanroom Research Workspace

```text
Restore the qqq_options_30d_cleanroom handoff bundle from C:\Users\<you>\Downloads\<cleanroom-bundle-folder> so that qqq_options_30d_cleanroom sits beside codexalpaca_repo under the same parent directory. Then verify that the research scripts can run using the codexalpaca_repo virtualenv and summarize the exact command to test a small ticker batch.
```

## 4. Harden And Validate Before Go-Live

```text
Perform a full readiness check for the multi-ticker paper trader on this machine. Verify the shared Google Drive lease path, the scheduled tasks, ntfy configuration, local runtime state, health-check path, EOD close guard, and standby failover safety. If there are safe operational fixes, apply them. Do not change strategy logic or risk settings. Tell me whether this machine is ready to take over trading.
```

## 5. Post-Cutover Verification

```text
Verify that this machine now owns the multi-ticker portfolio lease, that the paper trader is running correctly, that Alpaca positions match the local session ledger, and that the health check reports no issues. If there is a safe operational mismatch, fix it directly and summarize the final state.
```

Before using the prompts below for ongoing research or runner operations, read `docs/INSTITUTIONAL_OPERATING_BLUEPRINT.md` so the machine stays aligned with the project's research / control / execution-plane split and champion/challenger governance.
Before assigning or changing agent work, also read `docs/AGENT_GOVERNANCE.md` so discovery stays split by family cohort, exhaustive follow-up stays split by ticker bundle, and live-book mutation stays with the single-writer steward.

## 6. Run The Family-Expansion Tournament Conveyor

```text
Open these sibling folders and use them together:

1. C:\Users\<you>\Downloads\codexalpaca_repo
2. C:\Users\<you>\Downloads\CodexAlpacaTest-TradeMigratyion
3. C:\Users\<you>\Downloads\qqq_options_30d_cleanroom

Treat qqq_options_30d_cleanroom as the research workspace. Verify that the cleanroom contains the conveyor scripts:
- materialize_backtester_ready.py
- build_ticker_family_coverage.py
- build_strategy_family_registry.py
- build_agent_operating_model.py
- build_run_registry_report.py
- build_agent_wave_launch_pack.py
- build_phase2_agent_wave_pack.py
- validate_agent_wave_pack.py
- run_core_strategy_expansion_overnight.py
- launch_down_choppy_program.ps1
- launch_down_choppy_family_wave.ps1
- launch_agent_wave.ps1
- build_family_wave_shortlist.py
- queue_bundle_candidate_batch.py
- queue_family_expansion_after_quality6.ps1
- queue_ready_family_expansion_after_status.ps1
- export_promoted_strategies.py
- wait_and_sync_live_manifest.ps1

Then set up and run a chained overnight family-expansion tournament that:
- uses only complete backtester_ready datasets
- avoids shrinking the current live manifest
- benchmarks on the current core live symbols when useful
- searches for new edge on complete-data symbols not already live
- exports winners
- merges approved winners into the live manifest
- validates and pushes only if the manifest truly improved

Use the GitHub live manifest as the source of truth for what is already promoted. Prefer discovery on complete-data symbols that are not already live before retesting live symbols. Keep promotion serialized so only one promotion lane writes the manifest at a time.

Prefer using launch_down_choppy_program.ps1 as the operator entrypoint for the down/choppy program. It should be able to dry-run the full workflow first, then execute the four discovery lanes, build the shortlist, and stage the two exhaustive lanes without manual glue code. When appropriate, have it use the coverage-ranked discovery path so Phase 1 starts from the highest-gap ready symbols instead of the full ready universe.

If the ready universe is smaller than the staged/registry universe, use materialize_backtester_ready.py or the bootstrap path inside launch_down_choppy_program.ps1 to materialize the planner's highest-priority staged/registry symbols into backtester_ready before launching the next discovery wave.

Before launching the next large wave, run build_ticker_family_coverage.py to refresh the 159-symbol ticker-family coverage matrix and use its `next_wave_plan.json` / `next_wave_commands.ps1` outputs to choose under-tested families and symbols instead of repeating already-covered combinations.
Before designing a new family-expansion wave, run `build_strategy_family_registry.py` and inspect `docs/strategy_family_registry/strategy_family_registry.md` plus `docs/STRATEGY_FAMILY_STEWARD.md` so family priorities come from the current codebase plus the current live-manifest overlay instead of memory.

Each large batch should leave behind a `run_manifest.json` inside its `research_dir` plus an append-only `run_registry.jsonl` under the cleanroom `output` root. Use those files to verify machine lineage, code lineage, input fingerprints, ticker completion state, and the final shared-account snapshot before trusting or promoting results.

After any large wave or validation pass, run `build_run_registry_report.py` so you have a clean operator packet showing run status, recent runs, attention items, code refs, ticker-state counts, and the exact research directories tied to each `run_id`.
When you use `launch_agent_wave.ps1` or `launch_down_choppy_program.ps1`, expect them to refresh a sibling `run_registry_report/` directory automatically; inspect that packet before deciding whether a wave is healthy, stuck, or ready for promotion review.
The follow-on queue and promotion watcher scripts should do the same on blocked, failed, and completed transitions, so you can inspect a fresh `run_registry_report/` packet even when a queued handoff stops before a full wave ever launches.
If a multi-lane program is already running, use `build_active_program_report.py --program-root <program_root>` to get a live operator packet with lane PIDs, active tickers, recent log tails, and attention items such as `exited_without_master_summary`.
Treat any lane that exits without `master_summary.json` as failed even when the wrapper process says exit code `0`; do not let shortlisting or validation consume wrapper-only success.
The same expectation now applies to direct launchers and orchestrators like `launch_down_choppy_family_wave.ps1` and `run_core_strategy_expansion_overnight.py`, so ad hoc program runs still leave behind the same audit packet.
Once a down/choppy program finishes, use `queue_live_book_validation_after_program.ps1` or `validate_program_live_book.py` to turn the completed program root into an incremental shared-account review packet before touching the live manifest.
If that program produces zero shortlist or phase-2 survivors, treat the follow-on validation and hardening review as a successful no-op: write the packets, keep the live manifest unchanged, and use the shortlist diagnostics to decide whether to relax thresholds or broaden the next wave.
After validation and hardening review, build a non-destructive replacement plan with `build_live_book_replacement_plan.py` so the next morning’s live-book decision is an explicit `review_add` / `review_replace` packet instead of an ad hoc interpretation of the review JSON.
Then build a single morning handoff packet with `build_live_book_morning_handoff.py` so the operator has one clean summary of validation, review, replacement recommendations, and paper-runner guidance before market open.
Expect the resumed Phase 2 follow-on watcher to run the full chain `validation -> hardening review -> replacement plan -> morning handoff`; `build_active_program_report.py` should surface all four statuses while the program is still active.

Before assigning subagents for a new large wave, refresh the current operating model with `build_agent_operating_model.py` and use `docs/AGENT_OPERATING_MODEL.md` as the source of truth for role ownership, handoff artifacts, and the rule that only the Promotion Steward may write the live manifest.
Before assigning family-specific discovery work, refresh the GitHub-backed family registry with `build_strategy_family_registry.py` and inspect `docs/strategy_family_registry/strategy_family_registry.md` so both machines use the same family-level source of truth for gaps, live overlap, and steward actions.

Before executing Phase 1 discovery, use `build_agent_wave_launch_pack.py` to generate an exact launch pack from the current operating model plus the current coverage-ranked plan, then use `launch_agent_wave.ps1` against that pack so lane commands, logs, and research directories stay reproducible. `launch_agent_wave.ps1` should run `validate_agent_wave_pack.py` automatically so missing ready datasets, mismatched command args, duplicate output paths, or governance drift fail before any lane starts. For the strictest workflow, pass explicit source files into the pack builder and add `--require-explicit-sources` so the build never silently falls back to the latest matching artifact. For a breadth-first discovery wave, prefer `--refresh-coverage --allocation-mode breadth --coverage-top-ready-per-lane 40` so the four lanes spread across more unique ready symbols instead of reusing the same small cohort.

After `build_family_wave_shortlist.py` generates `phase2_plan.json`, build a second exact launch pack with `build_phase2_agent_wave_pack.py` and run that pack through `launch_agent_wave.ps1` for the exhaustive follow-up lanes. That keeps the shortlist thresholds, wave lineage, logs, research directories, and agent ownership reproducible instead of relying on ad hoc `phase2_commands.ps1` execution, and it should fail fast if the Phase 2 agent mapping no longer matches the operating model exactly.

At the end, report:
- what tournament lane is running now
- what lanes are queued
- which tickers are in each lane
- which scripts are orchestrating the conveyor
- whether GitHub promotion is armed correctly
```

## 7. Run The Strategy Family Steward

```text
Open these sibling folders and use them together:

1. C:\Users\<you>\Downloads\codexalpaca_repo
2. C:\Users\<you>\Downloads\CodexAlpacaTest-TradeMigratyion
3. C:\Users\<you>\Downloads\qqq_options_30d_cleanroom

Act as the Strategy Family Steward. Refresh the formal family registry with `build_strategy_family_registry.py`, then refresh the shorter handoff packet with `build_strategy_family_handoff.py`. Use `docs/strategy_family_registry/strategy_family_registry.md`, `docs/strategy_family_registry/strategy_family_handoff.md`, `docs/STRATEGY_FAMILY_REGISTRY.md`, and `docs/STRATEGY_FAMILY_STEWARD.md` as the source of truth.

Summarize:
- which families are currently live and concentrated
- which families are priority_discovery
- which families are priority_validation
- which families are promotion_follow_up
- the top 3 family gaps most likely to improve the paper runner by diversifying away from the current single-leg-heavy book

Then recommend the next 2-4 tournaments to run, and map those families into the current lane system when possible. Do not modify the live manifest and do not auto-promote strategies.
```

## 8. Run The Full Nightly Operator Cycle

```text
Open these sibling folders and use them together:

1. C:\Users\<you>\Downloads\codexalpaca_repo
2. C:\Users\<you>\Downloads\CodexAlpacaTest-TradeMigratyion
3. C:\Users\<you>\Downloads\qqq_options_30d_cleanroom

Operate under:
- docs/INSTITUTIONAL_OPERATING_BLUEPRINT.md
- docs/NIGHTLY_OPERATOR_PLAYBOOK.md
- docs/AGENT_OPERATING_MODEL.md

Run one full nightly research cycle that:
- refreshes the family registry and family handoff packet
- refreshes coverage
- materializes missing priority symbols when needed
- runs the next discovery wave
- runs exhaustive follow-up on survivors
- runs shared-account validation
- builds hardening review, replacement plan, and morning handoff packets
- keeps the live manifest unchanged unless a reviewed approval step happens

Prefer using `cleanroom/code/qqq_options_30d_cleanroom/launch_nightly_operator_cycle.ps1` as the top-level entrypoint. Treat GitHub-backed docs and packets as the source of truth. Keep discovery parallel, keep production decisions serialized, and treat any lane without `master_summary.json` as failed.
```
