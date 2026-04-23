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
Before running the paper runner or a governed nightly cycle, also read `docs/REPO_UPDATE_CONTROL.md` and inspect `docs/repo_updates/repo_update_handoff.md` so the machine does not drift behind GitHub or run from the wrong branch silently.
Before refreshing execution policy from paper-runner evidence, also read `docs/SESSION_RECONCILIATION_REGISTRY.md` and inspect `docs/session_reconciliation/session_reconciliation_handoff.md` so review-required sessions do not loosen research policy or promotion conclusions.
Before choosing or running a major nightly cycle, also read `docs/EXECUTION_CALIBRATION_REGISTRY.md` and inspect `docs/execution_calibration/execution_calibration_handoff.md` so current paper-runner fill, guardrail, and loss evidence can feed the next research run instead of being ignored.
Before choosing a nightly research cycle, also read `docs/TOURNAMENT_PROFILE_REGISTRY.md` and inspect `docs/tournament_profiles/tournament_profile_handoff.md` so the machine uses an approved executable tournament profile that is also aligned with the current execution posture.
Before choosing or escalating to a more aggressive nightly research cycle, also read `docs/TOURNAMENT_UNLOCK_REGISTRY.md` and inspect `docs/tournament_unlocks/tournament_unlock_handoff.md` so the machine can explain exactly what evidence or implementation work still blocks the next profile tier.
Before deciding what the new machine should do next, also read `docs/TOURNAMENT_UNLOCK_WORKPLAN.md` and inspect `docs/tournament_unlocks/tournament_unlock_workplan_handoff.md` so the execution plane follows the current evidence mission instead of improvising one.
Before trying to produce the next trusted paper session, also read `docs/EXECUTION_EVIDENCE_CONTRACT.md` and inspect `docs/execution_evidence/execution_evidence_contract_handoff.md` so the machine knows exactly what the next session must leave behind to count as unlock-worthy evidence.
Before treating the cloud shared execution lease as ready, also read `docs/GCP_SHARED_EXECUTION_LEASE_IMPLEMENTATION.md` and inspect `docs/gcp_foundation/gcp_shared_execution_lease_implementation_handoff.md` so the machine understands whether the runner only has dry-run helpers or a fully wired lease path.
Before trying to validate the live GCS-backed execution lease on the sanctioned VM, also read `docs/GCP_SHARED_EXECUTION_LEASE_RUNTIME_WIRING.md` and inspect `docs/gcp_foundation/gcp_shared_execution_lease_runtime_wiring_handoff.md` so the machine knows whether the runner has an optional wired backend or only a design/helper seam.
Before moving the sanctioned VM toward a trusted validation paper session, also read `docs/GCP_EXECUTION_VM_LEASE_DRY_RUN_VALIDATION.md`, `docs/GCP_EXECUTION_VM_LEASE_DRY_RUN_VALIDATION_REVIEW.md`, and inspect `docs/gcp_foundation/gcp_execution_vm_lease_dry_run_validation_handoff.md` so the machine treats the cloud lease as proven only after the headless dry-run packet is clean.
Before launching the first broker-facing VM paper session, also read `docs/GCP_EXECUTION_EXCLUSIVE_WINDOW.md`, `docs/GCP_EXECUTION_TRUSTED_VALIDATION_LAUNCH_PACK.md`, and inspect `docs/gcp_foundation/gcp_execution_exclusive_window_handoff.md` plus `docs/gcp_foundation/gcp_execution_trusted_validation_launch_handoff.md` so the machine treats the exclusive execution window and assimilation follow-through as governed prerequisites instead of operator memory.
Before starting an overnight mission, also read `docs/OVERNIGHT_PHASED_PLAN.md` and inspect `docs/overnight_plan/overnight_phased_plan_handoff.md` so the new machine can align itself with tonight's current unlocked profile, execution evidence mission, and by-morning success definition instead of improvising its own night plan.
Do not treat a planned or executable profile as automatically safe to activate just because it is listed in the registry; also respect the profile's execution evidence floor, broker-audit requirements, and exit-telemetry requirements from the current tournament profile handoff.
Treat a paper session as unlock-grade evidence only if its session summary is stamped with the current runner unlock baseline from a clean runner checkout; older or dirty-runner sessions are still useful for calibration, but not for clearing blocked tournament tiers.

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
If a multi-lane program is already running, use `build_active_program_report.py --program-root <program_root>` to get a live operator packet with lane PIDs, active tickers, heartbeat age, lane health, recent log tails, and attention items such as `exited_without_master_summary`, `missing_activity_heartbeat`, or `activity_stale`.
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
- refreshes the execution calibration registry and execution calibration handoff from paper-runner evidence
- refreshes the family registry and family handoff packet
- refreshes coverage
- materializes missing priority symbols when needed
- runs the next discovery wave
- runs exhaustive follow-up on survivors
- runs shared-account validation
- builds hardening review, replacement plan, and morning handoff packets
- keeps the live manifest unchanged unless a reviewed approval step happens

Prefer using `cleanroom/code/qqq_options_30d_cleanroom/launch_nightly_operator_cycle.ps1` as the top-level entrypoint. Treat GitHub-backed docs and packets as the source of truth. Keep discovery parallel, keep production decisions serialized, and treat any lane without `master_summary.json` as failed. Let the nightly operator resolve the tournament profile in `auto` mode unless I explicitly ask for a different executable profile.

If a governed nightly cycle completed Phase 1 but failed specifically while building the Phase 2 launch pack, prefer the governed recovery path in `resume_program_phase2_from_phase1.ps1` over rerunning discovery. When appropriate, the nightly operator may use its `-AllowPhase2ResumeFromArtifacts` path to fall into that recovery mode automatically.
```

## 9. Apply The Current Runner Execution Upgrades

```text
Open these sibling folders and use them together:

1. C:\Users\<you>\Downloads\codexalpaca_repo
2. C:\Users\<you>\Downloads\CodexAlpacaTest-TradeMigratyion

Read first:
- docs/INSTITUTIONAL_OPERATING_BLUEPRINT.md
- docs/RUNNER_EXECUTION_UPGRADE_HANDOFF.md

Then, in C:\Users\<you>\Downloads\codexalpaca_repo, act as the execution-plane Codex operator and bring the paper runner up to the current execution baseline.

Fetch `origin/codex/qqq-paper-portfolio`, verify whether commits `50764cf`, `4292514`, `f6d6168`, `8037710`, `bdd7663`, `1e72e18`, and `3d1de76` are present, and if not, integrate them deliberately from that branch without changing unrelated strategy logic or risk settings.

Verify that the runner now includes:
- combo-native Alpaca `mleg` entry and exit routing in `alpaca_lab/multi_ticker_portfolio/trader.py`
- Alpaca-aligned option fee modeling in the same file
- cleanup fallback for not-filled multi-leg combo exits in the same file
- leg-aware close-order detection for open Alpaca `mleg` exits in the same file
- broker-position-aware cleanup sizing for partially filled combo exits in the same file
- a broker-order audit in the session summary output path
- a broker account-activity audit in the session summary output path
- an ending broker-position snapshot in the session summary output path
- runner capability metadata in the session summary output path, including the current unlock-baseline stamp and clean repo state

Then run:
- `python -m pytest -q`

At the end, report:
- whether the runner now supports true multi-leg combo execution
- whether the fee model is aligned with Alpaca's current options fee posture
- whether a not-filled combo exit now degrades into cleanup instead of stalling
- whether open combo close orders and partial-fill cleanup are reconciled safely enough for paper-runner use
- whether the runner now leaves behind a broker-order audit, broker account-activity audit, and ending broker-position snapshot for post-session reconciliation
- whether local runner order events, Alpaca order state, and Alpaca account activity reconcile cleanly enough for execution-plane use
- whether the full suite is green
- whether the machine is safe to keep using as the execution-plane paper runner

Hard rules:
- do not modify the live manifest
- do not start trading
- do not change strategy selection or risk policy in this step
```

## 10. Plan The GCP Foundation

```text
Open these sibling folders and use them together:

1. C:\Users\<you>\Downloads\CodexAlpacaTest-TradeMigratyion
2. C:\Users\<you>\Downloads\codexalpaca_repo

Read first:
- docs/INSTITUTIONAL_OPERATING_BLUEPRINT.md
- docs/GCP_OPERATING_BLUEPRINT.md
- docs/GCP_MIGRATION_PLAN.md

Act as the GCP foundation steward for project `codexalpaca`.

Your goal is to prepare an institutional-grade Google Cloud foundation for this project without changing live strategy logic or starting trading.

Plan and report the exact target resources for:
- execution VM
- static outbound execution IP
- VPC and subnet
- Artifact Registry
- Secret Manager
- Cloud Storage bucket separation for bootstrap transfer, data, artifacts, control packets, and backups
- service accounts for execution, research, orchestration, and deployment
- budget alerts and basic logging/monitoring

Use the following operating principles:
- execution plane on Compute Engine
- research plane on Cloud Batch
- control-plane sequencing on Scheduler + Workflows
- GitHub remains the governance source of truth
- GCS becomes the runtime artifact and dataset substrate
- Secret Manager becomes the canonical secret source

At the end, report:
- exact target resource names
- the recommended rollout order
- the first no-risk implementation step
- any permission or credential gaps that would block real deployment

Hard rules:
- do not modify the live manifest
- do not start trading
- do not change strategy selection or risk policy in this step
```

## 11. Prepare The GCP Execution Cut-In

```text
Open these sibling folders and use them together:

1. C:\Users\<you>\Downloads\CodexAlpacaTest-TradeMigratyion
2. C:\Users\<you>\Downloads\codexalpaca_repo

Read first:
- docs/GCP_OPERATING_BLUEPRINT.md
- docs/GCP_MIGRATION_PLAN.md
- docs/RUNNER_EXECUTION_UPGRADE_HANDOFF.md
- docs/SESSION_RECONCILIATION_REGISTRY.md
- docs/EXECUTION_EVIDENCE_CONTRACT.md

Act as the GCP execution cut-in steward.

Your goal is to prepare the paper runner to move onto a dedicated Google Cloud execution VM with a static outbound IP and Secret Manager-backed credentials.

Verify and report what the execution VM must support before cutover:
- current runner execution baseline
- broker-order audit
- broker account-activity audit
- ending broker-position snapshot
- runner unlock-baseline stamping
- post-session assimilation compatibility
- local artifact paths that must be preserved or synced to GCS

Then produce a cut-in checklist covering:
- VM bootstrap
- secret injection
- code sync
- test/doctor validation
- dry-run verification
- trusted session evidence requirements before the VM becomes the canonical execution host

At the end, report:
- whether the runner is cloud-cutover ready in code
- what still needs to be externalized from local-machine assumptions
- the exact go/no-go checks before the first cloud-hosted paper session

Hard rules:
- do not modify the live manifest
- do not start trading
- do not change strategy selection or risk policy in this step
```

## 12. Audit GCP Foundation Readiness

```text
Open:

1. C:\Users\<you>\Downloads\CodexAlpacaTest-TradeMigratyion

Read first:
- docs/GCP_OPERATING_BLUEPRINT.md
- docs/GCP_MIGRATION_PLAN.md
- docs/GCP_FOUNDATION_READINESS.md

Act as the GCP readiness steward for project `codexalpaca`.

Use the provided Google Cloud service-account credential to build the current readiness packet for:
- Cloud Storage
- Compute Engine
- Secret Manager
- Artifact Registry
- Cloud Batch
- Workflows
- Cloud Scheduler

Run the GCP foundation readiness builders, then inspect:
- `docs/gcp_foundation/gcp_foundation_readiness.md`
- `docs/gcp_foundation/gcp_foundation_readiness_handoff.md`

Report:
- whether the current credential is only suitable for storage/bootstrap use or is actually foundation-ready
- which cloud capabilities are available now
- which capabilities are still blocked
- whether the project should proceed with Phase 0 foundation provisioning now or first switch to a stronger bootstrap identity

Hard rules:
- do not modify the live manifest
- do not start trading
- do not change strategy selection or risk policy in this step
```

## 13. Bootstrap The GCP Foundation With Admin Access

```text
Open:

1. C:\Users\<you>\Downloads\CodexAlpacaTest-TradeMigratyion

Read first:
- docs/GCP_OPERATING_BLUEPRINT.md
- docs/GCP_MIGRATION_PLAN.md
- docs/GCP_FOUNDATION_READINESS.md
- docs/GCP_FOUNDATION_BOOTSTRAP.md
- docs/gcp_foundation/gcp_foundation_readiness_handoff.md

Act as the GCP bootstrap steward for project `codexalpaca`.

Assume you are using a higher-privilege bootstrap identity, not the storage-only bootstrap key.

Your job is to bootstrap the cloud foundation for the institutional target architecture:
- enable required Google Cloud APIs
- create the target VPC, subnet, and reserved execution static IP
- create the role-separated long-term Cloud Storage buckets
- create dedicated service accounts for execution, research, orchestration, and deployment
- create Secret Manager and Artifact Registry foundations
- create the initial execution VM in validation-only posture
- establish basic budget and monitoring guardrails

Use the exact naming and sequencing in:
- docs/GCP_FOUNDATION_BOOTSTRAP.md

At the end, report:
- what resources were created
- what APIs were enabled
- what is still blocked
- whether the project is now foundation-ready for execution-plane cut-in

Hard rules:
- do not modify the live manifest
- do not start trading
- do not change strategy selection or risk policy in this step
```

## 14. Bootstrap GCP Runtime Security

```text
Open:

1. C:\Users\<you>\Downloads\CodexAlpacaTest-TradeMigratyion
2. C:\Users\<you>\Downloads\codexalpaca_repo

Read first:
- docs/GCP_OPERATING_BLUEPRINT.md
- docs/GCP_MIGRATION_PLAN.md
- docs/GCP_RUNTIME_SECURITY.md
- docs/gcp_foundation/gcp_foundation_bootstrap_status.md

Act as the GCP runtime security steward for project `codexalpaca`.

Your job is to:
- create the runtime Secret Manager containers
- seed the currently available paper-only secret values from the local `.env`
- bind the runtime service accounts only to the secrets and buckets they need
- grant the minimal current project-level runtime roles for logging, metrics, and artifact access

Then inspect:
- `docs/gcp_foundation/gcp_runtime_security_status.md`

Report:
- which secrets were created
- which secrets were seeded versus still pending
- what runtime IAM bindings now exist for execution, research, orchestration, and deployer identities
- what remains before the execution VM can safely cut in

Hard rules:
- do not print secret values
- do not modify the live manifest
- do not start trading
- do not change strategy selection or risk policy in this step
```

## 15. Bootstrap The GCP Execution Validation VM

```text
Open:

1. C:\Users\<you>\Downloads\CodexAlpacaTest-TradeMigratyion

Read first:
- docs/GCP_OPERATING_BLUEPRINT.md
- docs/GCP_MIGRATION_PLAN.md
- docs/GCP_EXECUTION_CUTIN.md
- docs/gcp_foundation/gcp_foundation_bootstrap_status.md
- docs/gcp_foundation/gcp_runtime_security_status.md

Act as the GCP execution cut-in steward for project `codexalpaca`.

Your job is to:
- reserve the execution static IP
- create the IAP-only SSH firewall rule for the execution host
- create the validation-only execution VM
- leave the VM in validation-only posture with no automatic trading start

Then inspect:
- `docs/gcp_foundation/gcp_execution_validation_vm_status.md`

Report:
- the reserved execution IP
- whether the VM is running
- what service account and machine type the VM uses
- what remains before the VM can safely host the paper runner

Hard rules:
- do not start trading
- do not modify the live manifest
- do not change strategy selection or risk policy in this step
- do not treat VM creation as cutover
```

## 16. Prepare The GCP Execution VM Runtime Bootstrap

```text
Open:

1. C:\Users\<you>\Downloads\CodexAlpacaTest-TradeMigratyion
2. C:\Users\<you>\Downloads\codexalpaca_repo

Read first:
- docs/GCP_OPERATING_BLUEPRINT.md
- docs/GCP_MIGRATION_PLAN.md
- docs/GCP_EXECUTION_CUTIN.md
- docs/GCP_EXECUTION_VM_RUNTIME_BOOTSTRAP.md
- docs/gcp_foundation/gcp_execution_validation_vm_status.md
- docs/gcp_foundation/gcp_runtime_security_status.md

Act as the GCP execution runtime bootstrap steward for project `codexalpaca`.

Your job is to:
- package the execution repo into a code-only bootstrap bundle
- publish that bundle to GCS
- publish the VM runtime bootstrap script to GCS
- keep the VM in validation-only posture

Then inspect:
- `docs/gcp_foundation/gcp_execution_vm_runtime_bootstrap_status.md`

Report:
- the GCS URI for the code bundle
- the GCS URI for the VM bootstrap script
- the non-secret validation config keys being rendered
- the required and optional Secret Manager mappings
- what exact operator step should happen on the VM next

Hard rules:
- do not print secret values
- do not start trading
- do not modify the live manifest
- do not change strategy selection or risk policy in this step
```

## 17. Run The GCP Execution VM Validation Gate

```text
Open:

1. C:\Users\<you>\Downloads\CodexAlpacaTest-TradeMigratyion

Read first:
- docs/GCP_OPERATING_BLUEPRINT.md
- docs/GCP_MIGRATION_PLAN.md
- docs/GCP_EXECUTION_CUTIN.md
- docs/GCP_EXECUTION_VM_RUNTIME_BOOTSTRAP.md
- docs/GCP_EXECUTION_VM_VALIDATION.md
- docs/gcp_foundation/gcp_execution_validation_vm_status.md
- docs/gcp_foundation/gcp_execution_vm_runtime_bootstrap_status.md

Act as the GCP execution validation steward for project `codexalpaca`.

Your job is to:
- publish the VM validation script if needed
- connect to the validation VM through OS Login and IAP
- run the validation script on the VM
- inspect the resulting local validation packet and pytest log on the VM

Then inspect:
- `docs/gcp_foundation/gcp_execution_vm_validation_status.md`

Report:
- whether the observed VM external IP matches the reserved execution IP
- whether the runtime bootstrap completed cleanly on the VM
- whether doctor passed in paper-only mode
- whether pytest passed
- whether the VM is ready for the next step toward a trusted validation session

Hard rules:
- do not start trading
- do not enable ownership leasing
- do not modify the live manifest
- do not change strategy selection or risk policy in this step
```

## 18. Audit GCP Execution Access Readiness

```text
Open:

1. C:\Users\<you>\Downloads\CodexAlpacaTest-TradeMigratyion

Read first:
- docs/GCP_OPERATING_BLUEPRINT.md
- docs/GCP_EXECUTION_CUTIN.md
- docs/GCP_EXECUTION_ACCESS_READINESS.md
- docs/gcp_foundation/gcp_execution_validation_vm_status.md

Act as the GCP execution access steward for project `codexalpaca`.

Your job is to:
- verify the execution VM is ready for OS Login and IAP-based SSH access
- enable any missing access-plane APIs if needed
- confirm the VM and firewall posture still matches the institutional access model
- if an operator principal is provided, grant the minimum required IAM access for VM operation

Then inspect:
- `docs/gcp_foundation/gcp_execution_access_readiness_status.md`

Report:
- whether access readiness is blocked or ready
- whether `iap.googleapis.com` and `oslogin.googleapis.com` are enabled
- whether the VM and firewall still match the expected access posture
- whether operator IAM is still pending

Hard rules:
- do not open inbound SSH to the internet
- do not grant broad owner-style access just to make SSH work
- do not start trading
- do not modify the live manifest
```

## 19. Refresh Post-Session Reconciliation And Execution Policy

```text
Open these sibling folders and use them together:

1. C:\Users\<you>\Downloads\codexalpaca_repo
2. C:\Users\<you>\Downloads\CodexAlpacaTest-TradeMigratyion

Read first:
- docs/SESSION_RECONCILIATION_REGISTRY.md
- docs/EXECUTION_CALIBRATION_REGISTRY.md

Then act as the Session Reconciliation Steward and Execution Calibration Steward for the new machine.

In C:\Users\<you>\Downloads\CodexAlpacaTest-TradeMigratyion:

1. Rebuild the session reconciliation registry and handoff from the latest runner session bundles.
2. Rebuild the execution calibration registry and handoff from the same runner evidence.
3. Inspect:
   - `docs/session_reconciliation/session_reconciliation_registry.md`
   - `docs/session_reconciliation/session_reconciliation_handoff.md`
   - `docs/execution_calibration/execution_calibration_registry.md`
   - `docs/execution_calibration/execution_calibration_handoff.md`
4. Determine:
   - whether recent sessions are trusted, caution, or review-required
   - whether execution posture should tighten, stay the same, or improve
   - whether any broker-order, broker-activity, cleanup, or residual-position mismatches need human review
   - whether any broker/local cashflow drift is large enough that those sessions should not automatically teach research policy
   - whether the latest traded session satisfies the runner unlock baseline or remains calibration-only evidence
   - whether any review-required sessions should be excluded from automatic research learning before calibration is refreshed
5. If the reconciliation or calibration artifacts changed materially, prepare only those distilled artifacts for commit.
6. Do not commit raw session exhaust, raw order logs, or raw intraday trade activity.

At the end, report:
- latest session bundle used
- session reconciliation posture
- execution calibration posture
- whether research policy should tighten or loosen
- whether broker/local economics drift is affecting session trust
- whether the control-plane artifacts are ready to commit
- any reconciliation anomalies that need human review

Hard rules:
- do not modify the live manifest
- do not start trading
- do not commit raw trade logs or raw session exhaust
```

## 20. Resume A Failed Phase 2 Program From Completed Phase 1

```text
Open these sibling folders and use them together:

1. C:\Users\<you>\Downloads\CodexAlpacaTest-TradeMigratyion
2. C:\Users\<you>\Downloads\codexalpaca_repo

Read first:
- docs/PHASE2_RESUME_FROM_PHASE1.md
- docs/NIGHTLY_OPERATOR_PLAYBOOK.md

Act as the research-plane recovery steward for the machine that owns the affected governed research workspace.

Goal:
- resume a failed governed program from completed Phase 1 artifacts without rerunning discovery

In C:\Users\<you>\Downloads\CodexAlpacaTest-TradeMigratyion:

1. Verify:
   - `program_manifest.json` exists
   - `phase1_status.json` says `phase1_discovery_complete`
   - `shortlist/phase2_plan.json` exists
   - `shortlist/family_wave_shortlist.json` exists
2. Run a dry rebuild first:
   - `powershell -NoProfile -ExecutionPolicy Bypass -File "C:\Users\<you>\Downloads\CodexAlpacaTest-TradeMigratyion\cleanroom\code\qqq_options_30d_cleanroom\resume_program_phase2_from_phase1.ps1" -ProgramRoot "C:\Users\<you>\Downloads\CodexAlpacaTest-TradeMigratyion\output\<cycle>\program"`
3. Inspect:
   - `program/phase2_resume_status.json`
   - `program/phase2/launch_pack/pack_validation.json`
4. If the rebuilt pack is valid, execute the resume:
   - `powershell -NoProfile -ExecutionPolicy Bypass -File "C:\Users\<you>\Downloads\CodexAlpacaTest-TradeMigratyion\cleanroom\code\qqq_options_30d_cleanroom\resume_program_phase2_from_phase1.ps1" -ProgramRoot "C:\Users\<you>\Downloads\CodexAlpacaTest-TradeMigratyion\output\<cycle>\program" -Execute`
5. Confirm:
   - `program/program_status.json` reflects resumed Phase 2
   - `nightly_operator_cycle_status.json` reflects resumed Phase 2
   - `program/phase2/launch_pack/launch_status.json` shows active or completed exhaustive lanes
   - `program/phase2_resume_followon_status.json` exists so validation and morning-handoff work are queued

Hard rules:
- do not rerun Phase 1 if its artifacts are complete
- do not bypass pack validation
- do not modify the live manifest
- do not start trading
```

## 21. Review Tonight's Overnight Mission

```text
Open these sibling folders and use them together:

1. C:\Users\<you>\Downloads\codexalpaca_repo
2. C:\Users\<you>\Downloads\CodexAlpacaTest-TradeMigratyion

Read first:
- docs/OVERNIGHT_PHASED_PLAN.md
- docs/EXECUTION_EVIDENCE_CONTRACT.md
- docs/TOURNAMENT_UNLOCK_WORKPLAN.md

Then act as the overnight execution steward for the new machine.

1. Refresh:
   - `docs/overnight_plan/overnight_phased_plan_handoff.md`
   - `docs/execution_evidence/execution_evidence_contract_handoff.md`
   - `docs/tournament_unlocks/tournament_unlock_workplan_handoff.md`
2. Report:
   - the current unlocked profile that must remain in use tonight
   - the current execution-plane overnight mission
   - the exact next-session evidence artifacts tonight's paper session must leave behind
   - what must remain blocked tonight
   - the by-morning success definition
3. Do not modify the live manifest, do not change risk policy, and do not start trading in this step.
```

## 22. Check GitHub Updates Before Open Or Nightly Work

```text
Open these sibling folders and use them together:

1. C:\Users\<you>\Downloads\codexalpaca_repo
2. C:\Users\<you>\Downloads\CodexAlpacaTest-TradeMigratyion

Read first:
- docs/INSTITUTIONAL_OPERATING_BLUEPRINT.md
- docs/REPO_UPDATE_CONTROL.md

Then act as the Repo Update Steward for the new machine.

In C:\Users\<you>\Downloads\CodexAlpacaTest-TradeMigratyion:

1. Run:
   - `powershell -NoProfile -ExecutionPolicy Bypass -File "C:\Users\<you>\Downloads\CodexAlpacaTest-TradeMigratyion\cleanroom\code\qqq_options_30d_cleanroom\launch_repo_update_check.ps1" -ControlPlaneRoot "C:\Users\<you>\Downloads\CodexAlpacaTest-TradeMigratyion" -ExecutionRepoRoot "C:\Users\<you>\Downloads\codexalpaca_repo"`
2. Inspect:
   - `docs/repo_updates/repo_update_registry.md`
   - `docs/repo_updates/repo_update_handoff.md`
3. If the handoff says updates are required for `codexalpaca_repo`, integrate them deliberately from `origin/codex/qqq-paper-portfolio` without changing live strategy selection, risk policy, or the live manifest.
4. If the handoff says updates are required for the control-plane repo, summarize the exact gap and whether the machine should pause governed nightly work until the control plane is current.
5. If either repo is dirty, on the wrong branch, or missing required commits, treat that as an attention item and explain the safest next step instead of guessing.

At the end, report:
- overall repo update status
- whether the control plane is current enough for governed nightly work
- whether the execution repo is current enough for the paper runner
- whether any required runner commits are missing
- whether the machine is safe to proceed unchanged

Hard rules:
- do not modify the live manifest
- do not start trading
- do not change strategy selection or risk policy in this step
```

## 23. Report Which Tournament Profiles Are Actually Unlocked

```text
Open these sibling folders and use them together:

1. C:\Users\<you>\Downloads\codexalpaca_repo
2. C:\Users\<you>\Downloads\CodexAlpacaTest-TradeMigratyion

Read first:
- docs/EXECUTION_CALIBRATION_REGISTRY.md
- docs/TOURNAMENT_PROFILE_REGISTRY.md

Then act as the Tournament Policy Steward for the new machine.

1. Refresh:
   - `docs/execution_calibration/execution_calibration_handoff.md`
   - `docs/tournament_profiles/tournament_profile_handoff.md`
   - `docs/tournament_unlocks/tournament_unlock_handoff.md`
2. Report:
   - which tournament profile is allowed tonight
   - which executable profiles are available but not preferred
   - which planned or partial profiles are still policy-blocked
   - the specific missing evidence or audit gates blocking each higher-risk profile
   - what the new machine needs to produce next so those blocked profiles can be reconsidered
3. Do not start trading, do not modify the live manifest, and do not change strategy or risk policy in this step.
```

## 24. Report What Unlocks The Next Tournament Tier

```text
Open these sibling folders and use them together:

1. C:\Users\<you>\Downloads\codexalpaca_repo
2. C:\Users\<you>\Downloads\CodexAlpacaTest-TradeMigratyion

Read first:
- docs/SESSION_RECONCILIATION_REGISTRY.md
- docs/EXECUTION_CALIBRATION_REGISTRY.md
- docs/TOURNAMENT_PROFILE_REGISTRY.md
- docs/TOURNAMENT_UNLOCK_REGISTRY.md

Then act as the Tournament Unlock Steward for the new machine.

1. Refresh:
   - `docs/session_reconciliation/session_reconciliation_handoff.md`
   - `docs/execution_calibration/execution_calibration_handoff.md`
   - `docs/tournament_profiles/tournament_profile_handoff.md`
   - `docs/tournament_unlocks/tournament_unlock_handoff.md`
2. Report:
   - which profile is unlocked now
   - which profiles are available but not preferred
   - the closest next unlock targets
   - the exact missing evidence, audit coverage, telemetry, risk-ceiling, or implementation work blocking each target
   - the smallest next evidence package the new machine should try to produce to unlock the next tier
3. Do not start trading, do not modify the live manifest, and do not change strategy or risk policy in this step.
```

## 25. Run The Current Execution Evidence Mission

```text
Open these sibling folders and use them together:

1. C:\Users\<you>\Downloads\codexalpaca_repo
2. C:\Users\<you>\Downloads\CodexAlpacaTest-TradeMigratyion

Read first:
- docs/SESSION_RECONCILIATION_REGISTRY.md
- docs/EXECUTION_CALIBRATION_REGISTRY.md
- docs/TOURNAMENT_UNLOCK_REGISTRY.md
- docs/TOURNAMENT_UNLOCK_WORKPLAN.md

Then act as the execution-plane mission operator for the new machine.

1. Refresh:
   - `docs/session_reconciliation/session_reconciliation_handoff.md`
   - `docs/execution_calibration/execution_calibration_handoff.md`
   - `docs/tournament_unlocks/tournament_unlock_handoff.md`
   - `docs/tournament_unlocks/tournament_unlock_workplan_handoff.md`
2. Read the current execution-plane mission from the workplan handoff.
3. Report:
   - the current unlocked profile that should remain in use
   - the current execution-plane evidence mission
   - the execution evidence contract for the next trusted session
   - the exact artifacts the next trusted session must leave behind
   - the completion gates that would let the control plane reconsider the next blocked profile
4. Do not modify the live manifest, do not change strategy or risk policy, and do not start trading in this step.
```

## 26. Run Governed Post-Session Assimilation

```text
Open these sibling folders and use them together:

1. C:\Users\<you>\Downloads\codexalpaca_repo
2. C:\Users\<you>\Downloads\CodexAlpacaTest-TradeMigratyion

Read first:
- docs/POST_SESSION_ASSIMILATION.md
- docs/SESSION_RECONCILIATION_REGISTRY.md
- docs/EXECUTION_CALIBRATION_REGISTRY.md
- docs/TOURNAMENT_UNLOCK_WORKPLAN.md
- docs/EXECUTION_EVIDENCE_CONTRACT.md

Then act as the post-session assimilation steward for the new machine.

1. Run:
   - `powershell -NoProfile -ExecutionPolicy Bypass -File "C:\Users\<you>\Downloads\CodexAlpacaTest-TradeMigratyion\cleanroom\code\qqq_options_30d_cleanroom\launch_post_session_assimilation.ps1" -ControlPlaneRoot "C:\Users\<you>\Downloads\CodexAlpacaTest-TradeMigratyion" -RunnerRepoRoot "C:\Users\<you>\Downloads\codexalpaca_repo"`
2. Inspect:
   - `docs/morning_brief/morning_operator_brief.md`
   - `docs/morning_brief/morning_operator_brief_handoff.md`
   - `docs/morning_brief/post_session_assimilation_status.json`
3. Report:
   - the morning decision posture
   - the current unlocked profile
   - what remains blocked
   - the nearest unlock targets
   - the exact next-session artifacts still missing, if any
   - whether the refreshed evidence is strong enough to reassess the next blocked profile
4. Do not modify the live manifest, do not change risk policy, and do not commit raw session exhaust or raw trade logs in this step.
```

## 27. Launch Headless GCP Execution VM Validation

```text
Open:

1. C:\Users\<you>\Downloads\CodexAlpacaTest-TradeMigratyion

Read first:
- docs\GCP_EXECUTION_ACCESS_READINESS.md
- docs\GCP_EXECUTION_VM_VALIDATION.md
- docs\GCP_EXECUTION_VM_HEADLESS_VALIDATION.md
- docs\gcp_foundation\gcp_execution_access_readiness_status.md
- docs\gcp_foundation\gcp_execution_vm_validation_status.md

Then act as the cloud execution validation steward.

1. Confirm the access gate is `ready_for_operator_validation`.
2. Launch the governed headless validation run for `vm-execution-paper-01`.
3. Report:
   - the launched validation run id
   - the GCS result prefix
   - whether the VM reset was triggered successfully
   - which artifacts should appear before the run is considered reviewable
4. Do not start trading, do not change the live manifest, and do not promote the VM to canonical execution in this step.
```

## 28. Review Headless GCP Execution VM Validation

```text
Open:

1. C:\Users\<you>\Downloads\CodexAlpacaTest-TradeMigratyion

Read first:
- docs\GCP_EXECUTION_VM_HEADLESS_VALIDATION.md
- docs\GCP_EXECUTION_VM_HEADLESS_VALIDATION_REVIEW.md
- docs\gcp_foundation\gcp_execution_vm_headless_validation_status.md

Then act as the cloud execution validation reviewer.

1. Refresh the headless validation review packet.
2. Report:
   - the current review state
   - which result objects are present in the GCS prefix
   - whether the VM validation gate is still pending, passed, or failed
   - what must happen next before the VM can move toward a trusted validation session
3. Do not start trading and do not promote the VM to canonical execution in this step.
```

## 29. Review GCP Trusted Validation Session Readiness

```text
Open:

1. C:\Users\<you>\Downloads\CodexAlpacaTest-TradeMigratyion

Read first:
- docs\GCP_EXECUTION_TRUSTED_VALIDATION_SESSION.md
- docs\gcp_foundation\gcp_execution_trusted_validation_session_status.md
- docs\gcp_foundation\gcp_execution_vm_headless_validation_review_status.md
- docs\gcp_foundation\gcp_execution_vm_lease_dry_run_validation_handoff.md

Then act as the cloud execution readiness steward.

1. Review whether the VM is ready for the first trusted validation paper session.
2. Report:
   - the current readiness state
   - the pinned runner branch and commit
   - the exact remaining gates before the session can start
   - the required evidence the session must produce
3. Do not start the session in this step unless the operator explicitly confirms an exclusive paper-account window.
```

## 30. Prepare The First Sanctioned VM Paper Session

```text
Open:

1. C:\Users\<you>\Downloads\CodexAlpacaTest-TradeMigratyion
2. C:\Users\<you>\Downloads\codexalpaca_repo

Read first:
- docs\GCP_EXECUTION_TRUSTED_VALIDATION_SESSION.md
- docs\GCP_EXECUTION_EXCLUSIVE_WINDOW.md
- docs\GCP_EXECUTION_TRUSTED_VALIDATION_LAUNCH_PACK.md
- docs\POST_SESSION_ASSIMILATION.md
- docs\gcp_foundation\gcp_execution_trusted_validation_session_status.md
- docs\gcp_foundation\gcp_execution_exclusive_window_status.md
- docs\gcp_foundation\gcp_execution_trusted_validation_launch_pack.md

Then act as the sanctioned VM execution steward.

1. Refresh the exclusive execution-window packet.
2. Refresh the trusted validation launch pack.
3. Report:
   - whether the launch pack is blocked, awaiting window arm, or ready to launch
   - the exact trusted validation VM command
   - the exact post-session assimilation command
   - what must be true about the temporary parallel runtime path before launch
   - what by-window success looks like
4. Do not launch the broker-facing session in this step unless the operator explicitly confirms the exclusive window is armed.
```

## 31. Arm The Exclusive VM Execution Window

```text
Open:

1. C:\Users\<you>\Downloads\CodexAlpacaTest-TradeMigratyion

Read first:
- docs\GCP_EXECUTION_EXCLUSIVE_WINDOW.md
- docs\GCP_EXECUTION_TRUSTED_VALIDATION_SESSION.md
- docs\GCP_EXECUTION_TRUSTED_VALIDATION_LAUNCH_PACK.md
- docs\gcp_foundation\gcp_execution_exclusive_window_status.md
- docs\gcp_foundation\gcp_execution_trusted_validation_session_status.md

Then act as the sanctioned VM execution-window steward.

1. Use `cleanroom\code\qqq_options_30d_cleanroom\arm_gcp_execution_exclusive_window.ps1` to record:
   - who is confirming the window
   - window start timestamp
   - window end timestamp
   - that the temporary parallel runtime path is paused or absent for the window
2. Refresh:
   - `docs\gcp_foundation\gcp_execution_exclusive_window_status.md`
   - `docs\gcp_foundation\gcp_execution_trusted_validation_session_status.md`
   - `docs\gcp_foundation\gcp_execution_trusted_validation_launch_pack.md`
3. Report:
   - whether the exclusive window is now `ready_for_launch`
   - whether trusted validation readiness is now `ready_for_manual_launch`
   - whether the launch pack is now `ready_to_launch`
   - the exact trusted validation VM command
   - the exact post-session assimilation command
4. Do not start the broker-facing session in this step unless the operator explicitly says to launch it.
```

## 32. Take Over The Project Cleanly From Another Machine

```text
Open these sibling folders and use them together:

1. C:\Users\<you>\Downloads\CodexAlpacaTest-TradeMigratyion
2. C:\Users\<you>\Downloads\codexalpaca_repo

Read first:
- docs\PROJECT_TARGET_OPERATING_MODEL.md
- docs\MULTI_MACHINE_CONTINUITY_PROTOCOL.md
- docs\gcp_foundation\multi_machine_continuity_handoff.md
- docs\gcp_foundation\research_strategy_governance_handoff.md
- docs\gcp_foundation\gcp_execution_trusted_validation_operator_handoff.md
- docs\gcp_foundation\gcp_execution_trusted_validation_session_status.md
- docs\gcp_foundation\gcp_execution_exclusive_window_handoff.md
- docs\gcp_foundation\gcp_execution_trusted_validation_launch_handoff.md
- docs\gcp_foundation\gcp_execution_closeout_handoff.md

Act as the continuity steward taking over the institutional-grade paper-account project from another machine.

Your job is to:
1. fetch `origin` and inspect canonical `main`
2. identify any open control-plane PRs that are ahead of `main`
3. determine whether the next safe action is:
   - merge an open control-plane PR
   - integrate equivalent changes onto `main`
   - arm the first bounded exclusive execution window
   - or hold because a required packet is still blocked
4. summarize the exact next operator action without relying on local shell history or prior conversation context

Report:
- canonical current branch or commit to trust
- whether takeover can proceed from GitHub alone
- whether the trusted validation operator packet is already canonical or still pending merge
- whether the next step is research work, execution preparation, or an actual bounded execution window
- any blocker that still prevents a clean takeover

Hard rules:
- do not start trading
- do not arm the execution window unless explicitly asked
- do not widen the temporary parallel runtime exception
- do not create new infrastructure in this step
```
