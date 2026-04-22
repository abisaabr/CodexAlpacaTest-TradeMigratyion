# Tournament Unlock Registry

This repo keeps a machine-readable tournament unlock registry so operators can see not just which profile is recommended now, but what concrete evidence or implementation work is still missing before the next class of profiles can activate.

## Source Of Truth

- Builders:
  - `cleanroom/code/qqq_options_30d_cleanroom/build_tournament_unlock_registry.py`
  - `cleanroom/code/qqq_options_30d_cleanroom/build_tournament_unlock_handoff.py`
- Inputs:
  - `docs/tournament_profiles/tournament_profile_registry.json`
  - `docs/tournament_profiles/tournament_profile_handoff.json`
  - `docs/execution_calibration/execution_calibration_handoff.json`
  - `docs/session_reconciliation/session_reconciliation_handoff.json`
- Generated artifacts:
  - `docs/tournament_unlocks/tournament_unlock_registry.json`
  - `docs/tournament_unlocks/tournament_unlock_registry.csv`
  - `docs/tournament_unlocks/tournament_unlock_registry.md`
  - `docs/tournament_unlocks/tournament_unlock_handoff.json`
  - `docs/tournament_unlocks/tournament_unlock_handoff.md`

## Why It Exists

The tournament profile registry tells us which profiles exist and which one the nightly operator should resolve tonight.

The tournament unlock registry tells us:

- which profiles are unlocked now
- which profiles are available but not preferred
- which profiles are blocked by implementation gaps versus execution-policy gaps
- the smallest next evidence package needed to unlock the next tier
- whether the new machine should focus on producing broker-audited sessions, exit telemetry, or implementation wiring next

## Institutional Use

Use this registry when you want a precise answer to:

- what is actually unlocked tonight?
- what is the closest next profile we could unlock?
- what exact evidence still blocks opening-window or aggressive profiles?
- should the new machine spend the next session producing trusted broker audits or should the research machine spend the next session wiring a profile?
- when do we want that blocker-clearing work split explicitly into a research-plane mission and an execution-plane mission?

## Refresh Command

From the repo root:

```powershell
python .\cleanroom\code\qqq_options_30d_cleanroom\build_tournament_unlock_registry.py
python .\cleanroom\code\qqq_options_30d_cleanroom\build_tournament_unlock_handoff.py
```

## Current Policy

- treat the unlock registry as the control-plane answer to "what evidence unlocks the next tournament tier?"
- do not activate a profile just because it appears in the tournament profile registry; confirm its blockers are cleared in the unlock handoff
- use the unlock handoff to choose the next evidence milestone for the new machine after each paper-runner session
- use the unlock workplan when you want that blocker-clearing work split cleanly between the research plane and the execution plane
