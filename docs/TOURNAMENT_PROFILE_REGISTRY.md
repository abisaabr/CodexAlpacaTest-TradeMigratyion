# Tournament Profile Registry

This repo keeps a machine-readable tournament profile registry so the nightly operator does not need to infer profile intent from prompts alone.

## Source Of Truth

- Builder:
  - `cleanroom/code/qqq_options_30d_cleanroom/build_tournament_profile_registry.py`
  - `cleanroom/code/qqq_options_30d_cleanroom/build_tournament_profile_handoff.py`
- Generated artifacts:
  - `docs/tournament_profiles/tournament_profile_registry.json`
  - `docs/tournament_profiles/tournament_profile_registry.csv`
  - `docs/tournament_profiles/tournament_profile_registry.md`
  - `docs/tournament_profiles/tournament_profile_handoff.json`
  - `docs/tournament_profiles/tournament_profile_handoff.md`
  - `docs/tournament_unlocks/tournament_unlock_registry.json`
  - `docs/tournament_unlocks/tournament_unlock_handoff.json`

## Why It Exists

The family registry tells us **what** is under-tested.

The tournament profile registry tells us **how** to search for it:

- which regime/session profile to run
- which entrypoint is valid today
- whether the profile is active, partial, or planned
- what execution evidence floor a profile requires before activation
- whether broker-order audit coverage, broker-activity audit coverage, or exit telemetry are required before activation
- how execution posture should bias or downgrade profile choice
- how discovery and validation should be split
- which machine should prefer to own the run now versus later

## Institutional Use

Use this registry before large waves to answer:

- are we running the default active nightly challenger cycle?
- is this profile executable today, or only planned?
- should discovery be split by family or by ticker here?
- is the new machine allowed to own this cycle yet?
- does live execution evidence currently favor safer or more aggressive profiles?
- what exact evidence or implementation work is still missing before the next profile tier can unlock?

## Refresh Command

From the repo root:

```powershell
python .\cleanroom\code\qqq_options_30d_cleanroom\build_tournament_profile_registry.py
python .\cleanroom\code\qqq_options_30d_cleanroom\build_tournament_profile_handoff.py
python .\cleanroom\code\qqq_options_30d_cleanroom\build_tournament_unlock_registry.py
python .\cleanroom\code\qqq_options_30d_cleanroom\build_tournament_unlock_handoff.py
```

## Current Policy

- `auto` should resolve through `tournament_profile_handoff.json` before a nightly cycle launches
- execution-aware profile selection should respect explicit evidence floors and audit requirements, not just soft score preferences
- the tournament unlock handoff should be treated as the machine-readable answer to "what unlocks the next tournament tier?"
- `down_choppy_coverage_ranked` is the default active institutional nightly profile and the current execution-aware recommendation when posture is cautious
- `down_choppy_full_ready` is the fallback active profile when the ready universe is already broad enough
- opening-window profiles are intentionally tracked as planned until their session-specific execution wiring is complete
- balanced family expansion remains partially operational, but is not yet wired into the single-command nightly operator cycle
