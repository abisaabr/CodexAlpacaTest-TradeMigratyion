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
- build_ticker_family_coverage.py
- run_core_strategy_expansion_overnight.py
- launch_down_choppy_program.ps1
- launch_down_choppy_family_wave.ps1
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

Prefer using launch_down_choppy_program.ps1 as the operator entrypoint for the down/choppy program. It should be able to dry-run the full workflow first, then execute the four discovery lanes, build the shortlist, and stage the two exhaustive lanes without manual glue code.

Before launching the next large wave, run build_ticker_family_coverage.py to refresh the 159-symbol ticker-family coverage matrix and use its next-wave outputs to choose under-tested families and symbols instead of repeating already-covered combinations.

At the end, report:
- what tournament lane is running now
- what lanes are queued
- which tickers are in each lane
- which scripts are orchestrating the conveyor
- whether GitHub promotion is armed correctly
```
