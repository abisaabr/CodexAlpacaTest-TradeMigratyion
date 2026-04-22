# Tournament Profile Registry

This repo keeps a machine-readable tournament profile registry so the nightly operator does not need to infer profile intent from prompts alone.

## Source Of Truth

- Builder:
  - `cleanroom/code/qqq_options_30d_cleanroom/build_tournament_profile_registry.py`
- Generated artifacts:
  - `docs/tournament_profiles/tournament_profile_registry.json`
  - `docs/tournament_profiles/tournament_profile_registry.csv`
  - `docs/tournament_profiles/tournament_profile_registry.md`

## Why It Exists

The family registry tells us **what** is under-tested.

The tournament profile registry tells us **how** to search for it:

- which regime/session profile to run
- which entrypoint is valid today
- whether the profile is active, partial, or planned
- how discovery and validation should be split
- which machine should prefer to own the run now versus later

## Institutional Use

Use this registry before large waves to answer:

- are we running the default active nightly challenger cycle?
- is this profile executable today, or only planned?
- should discovery be split by family or by ticker here?
- is the new machine allowed to own this cycle yet?

## Refresh Command

From the repo root:

```powershell
python .\cleanroom\code\qqq_options_30d_cleanroom\build_tournament_profile_registry.py
```

## Current Policy

- `down_choppy_coverage_ranked` is the default active institutional nightly profile
- `down_choppy_full_ready` is the fallback active profile when the ready universe is already broad enough
- opening-window profiles are intentionally tracked as planned until their session-specific execution wiring is complete
- balanced family expansion remains partially operational, but is not yet wired into the single-command nightly operator cycle
