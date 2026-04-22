# Repo Update Check Prompt

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
3. If the handoff says updates are required for the execution repo, fetch and integrate them deliberately from `origin/codex/qqq-paper-portfolio` without changing live strategy selection, risk policy, or the live manifest.
4. If the handoff says updates are required for the control-plane repo, summarize the exact gap and whether the machine should pause governed nightly work until those docs and builders are current.
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
- if you integrate updates, do so deliberately and summarize exactly what changed
```
