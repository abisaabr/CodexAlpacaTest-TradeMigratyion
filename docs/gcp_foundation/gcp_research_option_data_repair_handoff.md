# GCP Research Option Data Repair Handoff

- Status: `phase20_sharded_repair_launched`
- Runner branch: `codex/qqq-paper-portfolio`
- Runner commit: `952aea4`
- Tool: `scripts/build_option_data_repair_plan.py`
- Failed downloader: `phase19-targeted-fill-diagnostic-20260427022000`
- Failed downloader state: `FAILED`
- Failure reason: `24h Batch maxRunDuration exceeded before replay/promotion`
- Durable checkpoint: `gs://codexalpaca-control-us/research_results/top100_liquidity_research_20260426/phase19_live_checkpoints/20260427T155608Z`
- Active repair job: `phase20-sharded-fill-repair-20260428031000`
- Active repair state at launch: `SCHEDULED`
- Repair posture: `selected_contract_checkpoint_sharded_by_underlying`
- Repair task count: `7`
- Repair max parallelism: `4`
- Preferred repair batch size: `20`
- Launch packet: `gs://codexalpaca-control-us/research_results/top100_liquidity_research_20260426/portfolio_event_driven_data/phase20_sharded_fill_repair_20260428031000/launch/`

## Why This Exists

Phase19 failed after reaching the 24-hour GCP Batch runtime cap before replay, portfolio reporting, or promotion-review packets could be produced. The final exit-trap artifacts were not visible at the expected final output roots. The durable state is the Phase19 live checkpoint, which contains the selected option contract partitions and enough provenance to relaunch data collection without rebuilding contract inventory.

Phase20 was launched as a sharded repair using the checkpoint selected contracts directly. The job runs one task per underlying for `AAPL`, `AMZN`, `AVGO`, `INTC`, `MSFT`, `MU`, and `NVDA`, with max parallelism `4`, `option_batch_size=20`, and no broker-facing behavior.

## Safe Use

If Phase20 finishes cleanly, inspect each shard's downloader manifest and fill coverage first. Only then combine the shard data roots for replay and portfolio promotion-review.

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

- Do not launch another broad monolithic downloader for this campaign while Phase20 is active.
- Do not use this as a broker-facing process.
- Do not change live manifests, live strategy selection, or risk policy from this packet.
- Treat any candidate promoted by repaired data as research/governed-validation review only until execution evidence clears.

## Next Operator Decision

Monitor Phase20 shard status and per-underlying artifacts. After all seven shards succeed, run a replay/portfolio/promotion-review phase from the combined shard data roots. Require at least `0.90` fill coverage before any research candidate can move to governed-validation review.
