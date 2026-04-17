# Cross-Repo Operator Summary

## 1. What changed in REPO_A?

- Core4 scheduler support was tightened to the approved hourly in-hours cadence.
- The paper-shadow runtime now collapses all-stale after-hours core snapshots into a run-level `freshness_skip` when no live safety state exists.
- Ready-to-use daily and weekly operator prompt files were added.
- Repo-local instructions in [AGENTS.md](/C:/Users/rabisaab/Downloads/alpaca-strategy-research/AGENTS.md) were cleaned up to reflect the real current state.

## 2. Were the Core4 scheduled tasks created successfully?

- Yes. All five tasks are registered and currently `Ready`.
- Verified task names:
  - `Core4_Preflight_0920_ET`
  - `Core4_PaperShadow_InHours`
  - `Core4_Truthing_InHours`
  - `Core4_EOD_Truthing_1610_ET`
  - `Core4_Weekly_Maintenance_Sat_1000_ET`

## 3. Exact Core4 install / inspect / disable / remove commands

```powershell
Set-Location C:\Users\rabisaab\Downloads\alpaca-strategy-research
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File .\scripts\overnight_lab\install_core4_scheduler.ps1
Get-ScheduledTask -TaskName "Core4_*" | Sort-Object TaskName | Get-ScheduledTaskInfo
schtasks /Query /TN Core4_PaperShadow_InHours /V /FO LIST
Start-ScheduledTask -TaskName "Core4_PaperShadow_InHours"
Disable-ScheduledTask -TaskName "Core4_Preflight_0920_ET"
Disable-ScheduledTask -TaskName "Core4_PaperShadow_InHours"
Disable-ScheduledTask -TaskName "Core4_Truthing_InHours"
Disable-ScheduledTask -TaskName "Core4_EOD_Truthing_1610_ET"
Disable-ScheduledTask -TaskName "Core4_Weekly_Maintenance_Sat_1000_ET"
Enable-ScheduledTask -TaskName "Core4_Preflight_0920_ET"
Enable-ScheduledTask -TaskName "Core4_PaperShadow_InHours"
Enable-ScheduledTask -TaskName "Core4_Truthing_InHours"
Enable-ScheduledTask -TaskName "Core4_EOD_Truthing_1610_ET"
Enable-ScheduledTask -TaskName "Core4_Weekly_Maintenance_Sat_1000_ET"
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File .\scripts\overnight_lab\remove_core4_scheduler.ps1
```

## 4. What remains unproven in Core4?

- A fresh in-hours broker-connected order lifecycle is still unproven after the scheduler refresh.
- Borrow/shortability observability is intact and constructive, but it has not yet been exercised alongside a fresh submitted paper order cycle.

## 5. Did REPO_B get a manifest-only honesty write, or remain dry-run only?

- It remained effectively dry-run only.
- The approval-gated write path was exercised safely, but it resolved to `no_op` because `run_manifest.data_readiness` already matches the live canonical audit.

## 6. What exact fields changed in REPO_B?

- In the manifest-write phase: none.
- In the winner-like relevance phase, the strict comparison metrics changed:
  - `joined_pair_overlap: 1 -> 4`
  - `quote_rows: 2 -> 8`
  - `greek_rows: 2 -> 4`
  - `joined_rows: 2 -> 4`

## 7. Did any board-facing status fields move?

- No.

## 8. Did current-winner relevance improve? By how much?

- Yes.
- Strict current-winner pair-matched overlap improved from `1` true target pair to `4`, a net gain of `+3`.
- The stronger result remains narrow and does not clear the trust or promotion gates.

## 9. Next smallest safe action in each repo

- REPO_A: let the next fresh weekday in-hours scheduler cycle run and validate one real broker-connected paper session against the documented first-cycle success criteria.
- REPO_B: stop touching handoff mechanics unless the manifest drifts again; if more evidence is needed, source additional exact quote/greek coverage for the current 09:45 winner-like target pairs only.
