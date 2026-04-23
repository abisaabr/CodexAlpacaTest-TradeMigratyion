# Phase 2 Resume From Phase 1

Use this procedure when a governed overnight program completed Phase 1 discovery and shortlist generation, but failed before Phase 2 exhaustive lanes launched cleanly.

Preferred entrypoint:
- `cleanroom/code/qqq_options_30d_cleanroom/resume_program_phase2_from_phase1.ps1`

## When To Use It

This is the right recovery path when all of the following are true:
- `program/phase1_status.json` says `phase1_discovery_complete`
- `program/shortlist/phase2_plan.json` exists
- `program/shortlist/family_wave_shortlist.json` exists
- the original program failed at or before Phase 2 pack launch

Typical example:
- `program/program_status.json` says `failed to build phase 2 launch pack`

## What It Does

The resume entrypoint:
- reads `program_manifest.json` to recover the original ready-universe and runner paths
- rebuilds the agent sharding plan under the affected `program/` root
- rebuilds the agent operating model under the affected `program/` root
- rebuilds the exact Phase 2 launch pack under `program/phase2/launch_pack`
- updates `program_status.json` and the cycle status so the run root reflects resumed truth
- optionally relaunches Phase 2
- optionally starts the resumed follow-on watcher for validation, hardening review, replacement planning, and morning handoff

## Dry Run

Use a dry run first when you want to verify the pack can be rebuilt safely without launching new work:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "C:\Users\rabisaab\Downloads\CodexAlpacaTest-TradeMigratyion\cleanroom\code\qqq_options_30d_cleanroom\resume_program_phase2_from_phase1.ps1" -ProgramRoot "C:\Users\rabisaab\Downloads\CodexAlpacaTest-TradeMigratyion\output\<cycle>\program"
```

Expected result:
- `program/phase2_resume_status.json`
- rebuilt `program/phase2/launch_pack/phase2_agent_wave_pack.json`
- no new lanes launched

## Execute

Use execution mode once the rebuilt pack looks correct:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "C:\Users\rabisaab\Downloads\CodexAlpacaTest-TradeMigratyion\cleanroom\code\qqq_options_30d_cleanroom\resume_program_phase2_from_phase1.ps1" -ProgramRoot "C:\Users\rabisaab\Downloads\CodexAlpacaTest-TradeMigratyion\output\<cycle>\program" -Execute
```

Add `-Wait` if you want the launcher step to block until Phase 2 lanes finish.

## Follow-On Behavior

When `-Execute` is used, the resume entrypoint will:
- reuse an already-running or completed Phase 2 launch when one exists
- otherwise relaunch Phase 2 from the rebuilt pack
- start the resumed follow-on watcher unless one is already active

That watcher writes:
- `program/phase2_resume_followon_status.json`
- `program/phase2_resume_followon.log`

## Safety Rules

- Do not rerun Phase 1 if its artifacts are complete and trustworthy.
- Do not modify the live manifest from this recovery step.
- Do not bypass pack validation just to get Phase 2 moving.
- If `program_manifest.json` points at a missing ready universe or runner path, stop and fix that first.

## Expected Outputs

The recovery is healthy when you see:
- `program/program_status.json` move to `phase2_exhaustive_running`
- `cycle/nightly_operator_cycle_status.json` move to `phase2_resume_running`
- `program/phase2/launch_pack/pack_validation.json` report `ok = true`
- `program/phase2/launch_pack/launch_status.json` show active or completed exhaustive lanes
- `program/phase2_resume_followon_status.json` advance through validation and morning-handoff stages after Phase 2 finishes
