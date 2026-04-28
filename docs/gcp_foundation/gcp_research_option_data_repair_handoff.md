# GCP Research Option Data Repair Handoff

- Status: `phase23_candidate_stress_holdout_active`
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
- Completed replay job: `phase21-replay-from-phase20-20260428034200`
- Completed replay state: `SUCCEEDED`
- Completed replay launch packet: `gs://codexalpaca-control-us/research_results/top100_liquidity_research_20260426/portfolio_event_driven_data/phase21_replay_from_phase20_20260428034200/launch/`
- Phase21 portfolio report: `gs://codexalpaca-control-us/research_results/top100_liquidity_research_20260426/portfolio_event_driven_data/phase21_replay_from_phase20_20260428034200/portfolio_report/research_portfolio_report.json`
- Phase21 promotion packet: `gs://codexalpaca-control-us/research_results/top100_liquidity_research_20260426/portfolio_event_driven_data/phase21_replay_from_phase20_20260428034200/promotion_review_packet/research_promotion_review_packet.json`
- Phase21 decision: `research_only_blocked`
- Phase21 candidate count: `13`
- Phase21 eligible for promotion review: `0`
- Phase21 blocker counts: `fill_coverage_below_0.90=13`, `test_net_pnl_not_above_0=3`
- Phase21 best research-only symbols: `AAPL`, `MU`, `NVDA`, `AVGO`, `INTC`, `MSFT`
- Completed diagnostic job: `phase22-wide-lag-diagnostic-20260428045000`
- Completed diagnostic state: `SUCCEEDED`
- Completed diagnostic launch packet: `gs://codexalpaca-control-us/research_results/top100_liquidity_research_20260426/portfolio_event_driven_data/phase22_wide_lag_diagnostic_20260428045000/launch/`
- Phase22 portfolio report: `gs://codexalpaca-control-us/research_results/top100_liquidity_research_20260426/portfolio_event_driven_data/phase22_wide_lag_diagnostic_20260428045000/portfolio_report/research_portfolio_report.json`
- Phase22 promotion packet: `gs://codexalpaca-control-us/research_results/top100_liquidity_research_20260426/portfolio_event_driven_data/phase22_wide_lag_diagnostic_20260428045000/promotion_review_packet/research_promotion_review_packet.json`
- Phase22 decision: `ready_for_governed_validation_review`
- Phase22 promotion scope: `research_governed_validation_review_only`
- Phase22 candidate count: `13`
- Phase22 eligible for promotion review: `6`
- Phase22 eligible symbols: `AAPL`, `INTC`, `NVDA`
- Phase22 blocker counts: `fill_coverage_below_0.90=5`, `test_net_pnl_not_above_0=2`
- Phase22 research-only capital plan: `AAPL=25%`, `INTC=25%`, `NVDA=25%`, `unallocated=25%`
- Phase22 caveat: `wide_exit_lag_diagnostic_not_deployment_authorization`
- Active stress job: `phase23-candidate-stress-20260428062500`
- Active stress state at launch: `SCHEDULED`
- Active stress phase id: `phase23_candidate_stress_holdout_20260428062500`
- Active stress launch packet: `gs://codexalpaca-control-us/research_results/top100_liquidity_research_20260426/portfolio_event_driven_data/phase23_candidate_stress_holdout_20260428062500/launch/`
- Active stress candidate scope: `six Phase22 review candidates only`
- Active stress underlyings: `AAPL`, `INTC`, `NVDA`
- Active stress profiles: `10/10`, `30/30`, `60/60`, `60/90`, `60/120`, `60/180 high-cost`
- Active stress holdout: `test_date_count=5`

## Why This Exists

Phase19 failed after reaching the 24-hour GCP Batch runtime cap before replay, portfolio reporting, or promotion-review packets could be produced. The final exit-trap artifacts were not visible at the expected final output roots. The durable state is the Phase19 live checkpoint, which contains the selected option contract partitions and enough provenance to relaunch data collection without rebuilding contract inventory.

Phase20 was launched as a sharded repair using the checkpoint selected contracts directly. The job ran one task per underlying for `AAPL`, `AMZN`, `AVGO`, `INTC`, `MSFT`, `MU`, and `NVDA`, with max parallelism `4`, `option_batch_size=20`, and no broker-facing behavior. All seven shards succeeded with zero failed chunks.

Phase21 combined the Phase20 shard roots, ran option-aware replay, produced a portfolio report, and emitted a promotion-review packet. It found 13 research-only positive candidates in the capital plan, but zero candidates passed promotion-review gates because all 13 were still blocked by minimum fill coverage below `0.90`; three were also blocked by non-positive test net PnL.

Phase22 completed as a research-only wide-exit-lag diagnostic using the same repaired data roots. It showed that six candidates can pass the fill-coverage, trade-count, and positive test-PnL gates when replayed with wider exit-lag assumptions. The passing candidates are two `AAPL` long-call variants, two `INTC` long-call variants, and two `NVDA` long-call variants. This classifies much of the Phase21 blocker as a fill-lag/modeling assumption issue, not only missing data.

Phase22 does not authorize live manifest, strategy-selection, or risk-policy changes. The pass is a governed-validation review signal only and must be reviewed against strategy governance, paper-session execution evidence, and stricter stress/holdout checks before any activation discussion.

Phase23 was launched as the candidate-only stress/holdout step for the six Phase22 review candidates. It deliberately narrows compute to `AAPL`, `INTC`, and `NVDA`, reruns the same option-aware research path with shorter-lag controls and wider-lag stress, and increases the holdout split to five most-recent filled trade dates. Its output should decide whether Phase22 is a robust review signal or only a lag-sensitive artifact.

## Safe Use

Phase22 is complete. Use the Phase22 promotion packet as the current research-only review queue, not as a deployment packet. The current eligible review candidates are:

- `b150__aapl__long_call__wide_reward__exit_210__liq_tight`
- `b150__intc__long_call__tight_reward__exit_210__liq_baseline`
- `b150__aapl__long_call__wide_reward__exit_360__liq_baseline`
- `b150__nvda__long_call__tight_reward__exit_300__liq_tight`
- `b150__nvda__long_call__tight_reward__exit_360__liq_tight`
- `b150__intc__long_call__wide_reward__exit_210__liq_baseline`

Treat these as research/governed-validation review only. Phase23 is now running candidate-only stress and holdout validation that explicitly compares Phase21 shorter-lag failures against Phase22 wider-lag passes.

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

- Do not launch another broad monolithic downloader for this campaign.
- Do not use this as a broker-facing process.
- Do not change live manifests, live strategy selection, or risk policy from this packet.
- Treat any candidate promoted by repaired data as research/governed-validation review only until execution evidence clears.
- Do not treat Phase22 as a production promotion because the pass depends on wide exit-lag assumptions.

## Next Operator Decision

Monitor Phase23 until it emits portfolio and promotion-review packets. Keep the `0.90` fill-coverage gate intact, preserve the non-broker-facing posture, and require clean broker-audited paper-session evidence before any live manifest or strategy-selection change.
