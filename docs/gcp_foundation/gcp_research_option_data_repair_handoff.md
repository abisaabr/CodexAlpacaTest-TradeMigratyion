# GCP Research Option Data Repair Handoff

- Status: `phase20_succeeded_phase21_replay_launched`
- Runner branch: `codex/qqq-paper-portfolio`
- Runner commit: `952aea4`
- Tool: `scripts/build_option_data_repair_plan.py`
- Failed downloader: `phase19-targeted-fill-diagnostic-20260427022000`
- Failed downloader state: `FAILED`
- Failure reason: `24h Batch maxRunDuration exceeded before replay/promotion`
- Durable checkpoint: `gs://codexalpaca-control-us/research_results/top100_liquidity_research_20260426/phase19_live_checkpoints/20260427T155608Z`
- Completed repair job: `phase20-sharded-fill-repair-20260428031000`
- Completed repair state: `SUCCEEDED`
- Repair posture: `selected_contract_checkpoint_sharded_by_underlying`
- Repair task count: `7`
- Repair max parallelism: `4`
- Preferred repair batch size: `20`
- Launch packet: `gs://codexalpaca-control-us/research_results/top100_liquidity_research_20260426/portfolio_event_driven_data/phase20_sharded_fill_repair_20260428031000/launch/`
- Repair output root: `gs://codexalpaca-control-us/research_results/top100_liquidity_research_20260426/portfolio_event_driven_data/phase20_sharded_fill_repair_20260428031000/data_shards/`
- Repair data root: `gs://codexalpaca-data-us/research_option_data/top100_liquidity_research_20260426/top100_phase20_<UNDERLYING>_fill_options_20260302_20260423/`
- Repair selected contracts: `67415`
- Repair chunks: `6986`
- Repair failed chunks: `0`
- Repair option bar rows: `1002599`
- Repair option trade rows: `2317496`
- Active replay job: `phase21-replay-from-phase20-20260428034200`
- Active replay state at launch: `SCHEDULED`
- Active replay launch packet: `gs://codexalpaca-control-us/research_results/top100_liquidity_research_20260426/portfolio_event_driven_data/phase21_replay_from_phase20_20260428034200/launch/`

## Why This Exists

Phase19 failed after reaching the 24-hour GCP Batch runtime cap before replay, portfolio reporting, or promotion-review packets could be produced. The final exit-trap artifacts were not visible at the expected final output roots. The durable state is the Phase19 live checkpoint, which contains the selected option contract partitions and enough provenance to relaunch data collection without rebuilding contract inventory.

Phase20 was launched as a sharded repair using the checkpoint selected contracts directly. The job ran one task per underlying for `AAPL`, `AMZN`, `AVGO`, `INTC`, `MSFT`, `MU`, and `NVDA`, with max parallelism `4`, `option_batch_size=20`, and no broker-facing behavior. All seven shards succeeded with zero failed chunks.

Phase21 is now launched to combine the Phase20 shard roots, run option-aware replay, produce a portfolio report, and emit a promotion-review packet.

## Safe Use

Phase21 should be allowed to finish before any new repair or promotion decision. Inspect the replay manifests, portfolio report, and promotion-review packet after the job exits.

If a shard fails or times out, prefer a narrower retry for the failed underlying/date ranges, not another broad monolithic rerun. If a completed shard still has fill gaps, copy or expose that shard's downloader manifest and selected-contract root, then run:

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

Then run the recommended command in the plan. It should use `--no-include-option-bars` when bars are complete and a larger `--option-batch-size` so the repair downloads only missing trade symbol-days.

## Guardrails

- Do not launch another broad monolithic downloader for this campaign while Phase21 is active.
- Do not use this as a broker-facing process.
- Do not change live manifests, live strategy selection, or risk policy from this packet.
- Treat any candidate promoted by repaired data as research/governed-validation review only until execution evidence clears.

## Next Operator Decision

Monitor Phase21 replay state and output artifacts. Require at least `0.90` fill coverage before any research candidate can move to governed-validation review.
