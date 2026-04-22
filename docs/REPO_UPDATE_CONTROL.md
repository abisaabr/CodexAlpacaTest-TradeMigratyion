# Repo Update Control

This guide defines the institutional GitHub update-check layer for the new machine and any other governed operator box.

Primary builder:
- `cleanroom/code/qqq_options_30d_cleanroom/build_repo_update_registry.py`

Preferred entrypoint:
- `cleanroom/code/qqq_options_30d_cleanroom/launch_repo_update_check.ps1`

Generated artifacts:
- `docs/repo_updates/repo_update_registry.json`
- `docs/repo_updates/repo_update_registry.md`
- `docs/repo_updates/repo_update_registry.csv`
- `docs/repo_updates/repo_update_handoff.json`
- `docs/repo_updates/repo_update_handoff.md`

## Objective

Before the machine starts the paper runner or a governed nightly cycle, it should answer three questions with evidence instead of memory:

1. is the control-plane repo current enough to trust the prompts and governance docs?
2. is the execution repo current enough to trust the paper runner?
3. is either repo dirty, on the wrong branch, or missing required institutional commits?

## What It Checks

For the control-plane repo:
- expected branch `main`
- remote `origin/main`
- ahead / behind counts
- dirty worktree state

For the execution repo:
- expected branch `codex/qqq-paper-portfolio`
- remote `origin/codex/qqq-paper-portfolio`
- ahead / behind counts
- dirty worktree state
- required runner commits:
  - `50764cf`
  - `4292514`
  - `f6d6168`
  - `8037710`
  - `bdd7663`
  - `1e72e18`

## Institutional Use

Run this check:
- before the paper runner becomes active
- before a governed nightly operator cycle
- after a new GitHub push that is intended for the execution machine

Treat the handoff as the machine-readable answer to whether update work is required or whether the machine is current enough to proceed unchanged.

The control-plane cleanliness check intentionally ignores changes under `docs/repo_updates/` so the update-control layer does not flag its own freshly regenerated packet as drift.

## Important Rule

Do not mix repo-update work with live-manifest mutation.

Update control is about:
- branch state
- required commits
- clean worktrees
- whether GitHub integration is needed

It is not permission to change:
- live strategy selection
- risk policy
- production manifest contents

## Refresh Commands

Preferred wrapper:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "C:\Users\rabisaab\Downloads\CodexAlpacaTest-TradeMigratyion\cleanroom\code\qqq_options_30d_cleanroom\launch_repo_update_check.ps1" `
  -ControlPlaneRoot "C:\Users\rabisaab\Downloads\CodexAlpacaTest-TradeMigratyion" `
  -ExecutionRepoRoot "C:\Users\rabisaab\Downloads\codexalpaca_repo"
```

Direct builder:

```powershell
python "C:\Users\rabisaab\Downloads\CodexAlpacaTest-TradeMigratyion\cleanroom\code\qqq_options_30d_cleanroom\build_repo_update_registry.py"
```

If you need an inspection-only pass without fetching:

```powershell
python "C:\Users\rabisaab\Downloads\CodexAlpacaTest-TradeMigratyion\cleanroom\code\qqq_options_30d_cleanroom\build_repo_update_registry.py" --skip-fetch
```
