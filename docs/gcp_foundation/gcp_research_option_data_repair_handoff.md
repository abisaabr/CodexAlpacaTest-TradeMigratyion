# GCP Research Option Data Repair Handoff

- Status: `prepared_not_launched`
- Runner branch: `codex/qqq-paper-portfolio`
- Runner commit: `952aea4`
- Tool: `scripts/build_option_data_repair_plan.py`
- Current active downloader: `phase19-targeted-fill-diagnostic-20260427022000`
- Active downloader state at preparation: `running_active_downloader`
- Default repair posture: `trades_only_after_phase19_finishes_or_stalls`
- Preferred repair batch size: `20`

## Why This Exists

Phase19 is progressing but slow because it is using `option_batch_size=5` and full-day option-trade downloads. Option bars are effectively complete; the expensive remaining path is option trades. The repair path should not blindly add more Alpaca downloaders while Phase19 is active because API contention can make the campaign slower and less reliable.

## Safe Use

After Phase19 finishes or clearly stalls, copy or expose the final downloader manifest and selected-contract root, then run:

```powershell
python scripts/build_option_data_repair_plan.py `
  --manifest-json <manifest-json> `
  --selected-contracts-root <selected-option-contracts-root> `
  --output-dir <repair-plan-output-dir> `
  --dataset option_trades `
  --option-batch-size 20
```

The planner emits:

- `option_data_repair_plan.json`
- `option_data_repair_plan.md`
- `repair_batches.csv`
- `selected_contracts_subset.csv`
- `selected_option_contracts/`

Then run the recommended command in the plan. It should use `--no-include-option-bars` and a larger `--option-batch-size` so the repair downloads only missing trade symbol-days.

## Guardrails

- Do not start this repair while Phase19 is actively producing fresh files unless Phase19 is stalled or failed.
- Do not use this as a broker-facing process.
- Do not change live manifests, live strategy selection, or risk policy from this packet.
- Treat any candidate promoted by repaired data as research/governed-validation review only until execution evidence clears.

## Next Operator Decision

Keep Phase19 running while fresh file counts and logs continue to advance. If Phase19 exits cleanly, inspect final fill coverage and promotion gates first. If fill coverage remains below target, use the planner to generate a targeted trade-only repair subset instead of rerunning broad bars plus trades.
