# Tournament Unlock Workplan

This repo keeps a two-machine unlock workplan so the control plane can turn tournament unlock blockers into concrete missions for the research plane and the execution plane.

## Source Of Truth

- Builders:
  - `cleanroom/code/qqq_options_30d_cleanroom/build_tournament_unlock_workplan.py`
  - `cleanroom/code/qqq_options_30d_cleanroom/build_tournament_unlock_workplan_handoff.py`
- Inputs:
  - `docs/tournament_unlocks/tournament_unlock_registry.json`
  - `docs/tournament_unlocks/tournament_unlock_handoff.json`
- Generated artifacts:
  - `docs/tournament_unlocks/tournament_unlock_workplan.json`
  - `docs/tournament_unlocks/tournament_unlock_workplan.md`
  - `docs/tournament_unlocks/tournament_unlock_workplan_handoff.json`
  - `docs/tournament_unlocks/tournament_unlock_workplan_handoff.md`

## Why It Exists

The unlock registry says what is blocked.

The unlock workplan says who should do what next:

- what the current research machine should wire next
- what the new execution machine should prove next
- what completion gates must clear before the next blocked profile is reconsidered

## Institutional Use

Use this workplan after refreshing the unlock registry when you want a clean answer to:

- what is the current research-plane unlock mission?
- what is the current execution-plane evidence mission?
- what exact completion gates must clear before we reconsider the next blocked profile?

## Refresh Command

From the repo root:

```powershell
python .\cleanroom\code\qqq_options_30d_cleanroom\build_tournament_unlock_workplan.py
python .\cleanroom\code\qqq_options_30d_cleanroom\build_tournament_unlock_workplan_handoff.py
```
