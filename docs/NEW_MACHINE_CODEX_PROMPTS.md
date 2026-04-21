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

## 6. Run The Family-Expansion Tournament Conveyor

```text
Open these sibling folders and use them together:

1. C:\Users\<you>\Downloads\codexalpaca_repo
2. C:\Users\<you>\Downloads\CodexAlpacaTest-TradeMigratyion
3. C:\Users\<you>\Downloads\qqq_options_30d_cleanroom

Treat qqq_options_30d_cleanroom as the research workspace. Verify that the cleanroom contains the conveyor scripts:
- materialize_backtester_ready.py
- build_ticker_family_coverage.py
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

Each large batch should leave behind a `run_manifest.json` inside its `research_dir` plus an append-only `run_registry.jsonl` under the cleanroom `output` root. Use those files to verify machine lineage, code lineage, input fingerprints, ticker completion state, and the final shared-account snapshot before trusting or promoting results.

After any large wave or validation pass, run `build_run_registry_report.py` so you have a clean operator packet showing run status, recent runs, attention items, code refs, ticker-state counts, and the exact research directories tied to each `run_id`.

Before assigning subagents for a new large wave, refresh the current operating model with `build_agent_operating_model.py` and use `docs/AGENT_OPERATING_MODEL.md` as the source of truth for role ownership, handoff artifacts, and the rule that only the Promotion Steward may write the live manifest.

Before executing Phase 1 discovery, use `build_agent_wave_launch_pack.py` to generate an exact launch pack from the current operating model plus the current coverage-ranked plan, then use `launch_agent_wave.ps1` against that pack so lane commands, logs, and research directories stay reproducible. `launch_agent_wave.ps1` should run `validate_agent_wave_pack.py` automatically so missing ready datasets, mismatched command args, duplicate output paths, or governance drift fail before any lane starts. For the strictest workflow, pass explicit source files into the pack builder and add `--require-explicit-sources` so the build never silently falls back to the latest matching artifact. For a breadth-first discovery wave, prefer `--refresh-coverage --allocation-mode breadth --coverage-top-ready-per-lane 40` so the four lanes spread across more unique ready symbols instead of reusing the same small cohort.

After `build_family_wave_shortlist.py` generates `phase2_plan.json`, build a second exact launch pack with `build_phase2_agent_wave_pack.py` and run that pack through `launch_agent_wave.ps1` for the exhaustive follow-up lanes. That keeps the shortlist thresholds, wave lineage, logs, research directories, and agent ownership reproducible instead of relying on ad hoc `phase2_commands.ps1` execution, and it should fail fast if the Phase 2 agent mapping no longer matches the operating model exactly.

At the end, report:
- what tournament lane is running now
- what lanes are queued
- which tickers are in each lane
- which scripts are orchestrating the conveyor
- whether GitHub promotion is armed correctly
```
