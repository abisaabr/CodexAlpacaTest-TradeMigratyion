# GCP Research Option Data Repair Handoff

- Status: `phase25_intc_isolated_stress_blocked_no_promotion`
- Runner branch: `codex/qqq-paper-portfolio`
- Runner commit: `95379e4`
- Tool: `scripts/build_option_data_repair_plan.py`
- Exit-lag tool: `scripts/build_option_exit_lag_feasibility.py`
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
- Completed stress job: `phase23-candidate-stress-20260428062500`
- Completed stress state: `SUCCEEDED`
- Completed stress phase id: `phase23_candidate_stress_holdout_20260428062500`
- Completed stress launch packet: `gs://codexalpaca-control-us/research_results/top100_liquidity_research_20260426/portfolio_event_driven_data/phase23_candidate_stress_holdout_20260428062500/launch/`
- Phase23 portfolio report: `gs://codexalpaca-control-us/research_results/top100_liquidity_research_20260426/portfolio_event_driven_data/phase23_candidate_stress_holdout_20260428062500/portfolio_report/research_portfolio_report.json`
- Phase23 promotion packet: `gs://codexalpaca-control-us/research_results/top100_liquidity_research_20260426/portfolio_event_driven_data/phase23_candidate_stress_holdout_20260428062500/promotion_review_packet/research_promotion_review_packet.json`
- Phase23 decision: `research_only_blocked`
- Phase23 candidate count: `6`
- Phase23 eligible for promotion review: `0`
- Phase23 blocker counts: `fill_coverage_below_0.90=6`, `test_net_pnl_not_above_0=1`
- Phase23 candidate scope: `six Phase22 review candidates only`
- Phase23 underlyings: `AAPL`, `INTC`, `NVDA`
- Phase23 profiles: `10/10`, `30/30`, `60/60`, `60/90`, `60/120`, `60/180 high-cost`
- Phase23 holdout: `test_date_count=5`
- Phase23 result summary: `profitable_but_not_fill_clean_under_short_lag_controls`
- Completed exit-lag feasibility job: `phase24-exit-lag-feas-20260428073500`
- Completed exit-lag feasibility state: `SUCCEEDED`
- Completed exit-lag feasibility phase id: `phase24_exit_lag_feasibility_20260428073500`
- Completed exit-lag feasibility runner source: `gs://codexalpaca-control-us/research_source/codexalpaca_runner_source_95379e4166b4.zip`
- Completed exit-lag feasibility launch packet: `gs://codexalpaca-control-us/research_results/top100_liquidity_research_20260426/portfolio_event_driven_data/phase24_exit_lag_feasibility_20260428073500/launch/`
- Phase24 feasibility packet: `gs://codexalpaca-control-us/research_results/top100_liquidity_research_20260426/portfolio_event_driven_data/phase24_exit_lag_feasibility_20260428073500/exit_lag_feasibility/exit_lag_feasibility_packet.json`
- Phase24 decision: `fill_feasible_under_full_stack`
- Phase24 promotion effect: `none_research_only`
- Phase24 candidate count: `5`
- Phase24 full-stack fill pass count: `1`
- Phase24 wide-lag-only candidate count: `4`
- Phase24 candidate scope: `five profitable Phase23 blocked candidates`
- Phase24 underlyings: `AAPL`, `INTC`, `NVDA`
- Phase24 aggregate missing-exit classes: `illiquid_or_missing_exit_data=56`, `short_lag_execution_timing_mismatch=54`, `late_exit_liquidity_window=19`
- Completed isolated stress job: `phase25-intc-stress-20260428085000`
- Completed isolated stress state: `SUCCEEDED`
- Completed isolated stress phase id: `phase25_intc_isolated_stress_20260428085000`
- Completed isolated stress launch packet: `gs://codexalpaca-control-us/research_results/top100_liquidity_research_20260426/portfolio_event_driven_data/phase25_intc_isolated_stress_20260428085000/launch/`
- Phase25 portfolio report: `gs://codexalpaca-control-us/research_results/top100_liquidity_research_20260426/portfolio_event_driven_data/phase25_intc_isolated_stress_20260428085000/portfolio_report/research_portfolio_report.json`
- Phase25 promotion packet: `gs://codexalpaca-control-us/research_results/top100_liquidity_research_20260426/portfolio_event_driven_data/phase25_intc_isolated_stress_20260428085000/promotion_review_packet/research_promotion_review_packet.json`
- Phase25 candidate: `INTC` `b150__intc__long_call__tight_reward__exit_210__liq_baseline`
- Phase25 decision: `research_only_blocked`
- Phase25 eligible for promotion review: `0`
- Phase25 blockers: `fill_coverage_below_0.90`, `test_net_pnl_not_above_0`, `min_net_pnl_not_positive`
- Phase25 min net PnL: `$-2726.7175`
- Phase25 min test PnL: `$-305.9375`
- Phase25 min fill coverage: `0.8776`
- Phase25 max fill coverage: `0.966`

## Why This Exists

Phase19 failed after reaching the 24-hour GCP Batch runtime cap before replay, portfolio reporting, or promotion-review packets could be produced. The final exit-trap artifacts were not visible at the expected final output roots. The durable state is the Phase19 live checkpoint, which contains the selected option contract partitions and enough provenance to relaunch data collection without rebuilding contract inventory.

Phase20 was launched as a sharded repair using the checkpoint selected contracts directly. The job ran one task per underlying for `AAPL`, `AMZN`, `AVGO`, `INTC`, `MSFT`, `MU`, and `NVDA`, with max parallelism `4`, `option_batch_size=20`, and no broker-facing behavior. All seven shards succeeded with zero failed chunks.

Phase21 combined the Phase20 shard roots, ran option-aware replay, produced a portfolio report, and emitted a promotion-review packet. It found 13 research-only positive candidates in the capital plan, but zero candidates passed promotion-review gates because all 13 were still blocked by minimum fill coverage below `0.90`; three were also blocked by non-positive test net PnL.

Phase22 completed as a research-only wide-exit-lag diagnostic using the same repaired data roots. It showed that six candidates can pass the fill-coverage, trade-count, and positive test-PnL gates when replayed with wider exit-lag assumptions. The passing candidates are two `AAPL` long-call variants, two `INTC` long-call variants, and two `NVDA` long-call variants. This classifies much of the Phase21 blocker as a fill-lag/modeling assumption issue, not only missing data.

Phase22 does not authorize live manifest, strategy-selection, or risk-policy changes. The pass is a governed-validation review signal only and must be reviewed against strategy governance, paper-session execution evidence, and stricter stress/holdout checks before any activation discussion.

Phase23 completed as the candidate-only stress/holdout step for the six Phase22 review candidates. It deliberately narrowed compute to `AAPL`, `INTC`, and `NVDA`, reran the same option-aware research path with shorter-lag controls and wider-lag stress, and increased the holdout split to five most-recent filled trade dates.

Phase23 did not promote any candidate to governed-validation review. All six candidates were blocked by minimum fill coverage below `0.90` when the stress stack includes the tight `10/10` and `30/30` lag controls. One `INTC` wide-reward variant also failed the positive holdout PnL gate. The important institutional read is that the best candidates remain economically positive across the stress stack, but the current evidence does not prove they are fill-clean enough for promotion under tighter execution timing.

Phase24 completed as a non-broker-facing exit-lag feasibility diagnostic for the five profitable blocked candidates. It used runner commit `95379e4`, which added `scripts/build_option_exit_lag_feasibility.py` and targeted tests. The diagnostic explains whether the missing short-lag exits are repairable data gaps, execution timing mismatches, or strategy-design problems that require alternate exits.

Phase24 found one full-stack fill-feasible candidate and four wide-lag-only candidates:

- `INTC` `b150__intc__long_call__tight_reward__exit_210__liq_baseline`: full-stack fill pass, shortest passing lag `10` minutes, fill curve `10=0.932`, `30=0.9524`, `60=0.966`, `90+=1.0`.
- `AAPL` `b150__aapl__long_call__wide_reward__exit_360__liq_baseline`: short-lag review candidate but not full-stack, shortest passing lag `30` minutes, fill curve `10=0.8684`, `30=0.9211`, `60=0.9737`, `90+=1.0`.
- `NVDA` `b150__nvda__long_call__tight_reward__exit_300__liq_tight`: wide-lag only, shortest passing lag `60` minutes, fill curve `10=0.8806`, `30=0.8955`, `60=0.9403`, `90+=0.9851`.
- `NVDA` `b150__nvda__long_call__tight_reward__exit_360__liq_tight`: wide-lag only, shortest passing lag `60` minutes, fill curve `10=0.8525`, `30=0.8852`, `60=0.9344`, `90+=0.9836`.
- `AAPL` `b150__aapl__long_call__wide_reward__exit_210__liq_tight`: wide-lag only, shortest passing lag `60` minutes, fill curve `10=0.7903`, `30=0.871`, `60+=0.9032`.

This does not authorize promotion. Phase24 is a feasibility classification packet; it does not rerun economic stress, does not include broker-audited execution evidence, and does not change the Phase23 conclusion that no candidate should be promoted from the current full evidence stack.

Phase25 completed as the isolated economic stress packet for the only Phase24 full-stack fill-feasible candidate: `INTC` `b150__intc__long_call__tight_reward__exit_210__liq_baseline`. It was intentionally single-candidate and research-only. Its purpose was to test whether the candidate survives tighter cost assumptions while preserving the `0.90` fill-coverage gate and five-date holdout posture.

Phase25 blocked the INTC candidate. The baseline `10/10` profile remained positive, but harsher cost assumptions exposed fragility:

- `10/10 slip10 fee0.65`: fill `0.8776`, net `$4433.36`, test `$549.771`.
- `10/10 slip25 fee1.00`: fill `0.8776`, net `$2614.885`, test `$334.6775`.
- `10/10 slip50 fee1.50`: fill `0.8776`, net `$-90.23`, test `$-2.645`.
- `10/10 slip75 fee2.00`: fill `0.8776`, net `$-2726.7175`, test `$-305.9375`.
- `30/30 slip25 fee1.00`: fill `0.9456`, net `$850.4475`, test `$-39.795`.
- `60/60 slip25 fee1.00`: fill `0.966`, net `$4076.0425`, test `$200.985`.

The institutional read is that INTC is not a promotion candidate today. It is a cost-sensitive research lead requiring better execution assumptions, spread modeling, or strategy redesign before any governed validation discussion.

Phase26 has been launched as the next non-broker-facing research step for the remaining AAPL/NVDA wide-lag candidates. This is an exit-policy and cost-sensitivity diagnostic, not a promotion packet and not a live-manifest change.

- Job: `phase26-widelag-policy-20260428100000`
- State: `SUCCEEDED`
- Phase id: `phase26_widelag_exit_policy_20260428100000`
- Scope: four Phase24 wide-lag-only or short-lag-conditional candidates across `AAPL` and `NVDA`
- Profiles: `30/30 slip25 fee1.00`, `30/30 slip50 fee1.50`, `60/60 slip25 fee1.00`, `60/60 slip50 fee1.50`, `60/90 slip25 fee1.00`, `60/120 slip50 fee1.50`
- Launch packet: `gs://codexalpaca-control-us/research_results/top100_liquidity_research_20260426/portfolio_event_driven_data/phase26_widelag_exit_policy_20260428100000/launch/`
- Result root: `gs://codexalpaca-control-us/research_results/top100_liquidity_research_20260426/portfolio_event_driven_data/phase26_widelag_exit_policy_20260428100000/`
- Promotion effect: `none_research_only`

Phase26 should answer whether the AAPL/NVDA leads are merely short-exit-lag mismatches or whether their economics break under realistic wider-lag and higher-cost assumptions.

Phase26 opened one research/governed-validation review candidate and kept three candidates blocked:

- `AAPL` `b150__aapl__long_call__wide_reward__exit_360__liq_baseline`: eligible for research review only, min net `$1715.93`, min holdout/test net `$591.28`, fill `0.9474-1.0`, min option trades `36`, worst drawdown `$-3330.115`, no blockers.
- `NVDA` `b150__nvda__long_call__tight_reward__exit_300__liq_tight`: blocked by `fill_coverage_below_0.90`, min net `$2521.905`, min holdout/test net `$658.86`, fill `0.8657-0.9701`.
- `AAPL` `b150__aapl__long_call__wide_reward__exit_210__liq_tight`: blocked by `fill_coverage_below_0.90`, min net `$1331.56`, min holdout/test net `$321.165`, fill `0.8871-0.9032`.
- `NVDA` `b150__nvda__long_call__tight_reward__exit_360__liq_tight`: blocked by `fill_coverage_below_0.90` and `test_net_pnl_not_above_0`, min net `$2124.85`, min holdout/test net `$-29.005`, fill `0.8525-0.9672`.

The Phase26 capital plan allocates only `25%` research weight to the AAPL review candidate and leaves `$18750` unallocated. This is intentionally conservative. It is not an instruction to update live strategy selection or risk policy.

## Safe Use

Phase22 is complete. Use the Phase22 promotion packet as the current research-only review queue, not as a deployment packet. The current eligible review candidates are:

- `b150__aapl__long_call__wide_reward__exit_210__liq_tight`
- `b150__intc__long_call__tight_reward__exit_210__liq_baseline`
- `b150__aapl__long_call__wide_reward__exit_360__liq_baseline`
- `b150__nvda__long_call__tight_reward__exit_300__liq_tight`
- `b150__nvda__long_call__tight_reward__exit_360__liq_tight`
- `b150__intc__long_call__wide_reward__exit_210__liq_baseline`

Treat these as research/governed-validation review only. Phase23 has now shown that none of the six should advance while the promotion rule requires the full stress stack to clear the `0.90` fill-coverage gate.

Best blocked candidates from Phase23:

- `NVDA` `b150__nvda__long_call__tight_reward__exit_300__liq_tight`: min net `$4033.80`, min test `$747.93`, min fill `0.8657`.
- `AAPL` `b150__aapl__long_call__wide_reward__exit_210__liq_tight`: min net `$2952.09`, min test `$226.67`, min fill `0.7581`.
- `INTC` `b150__intc__long_call__tight_reward__exit_210__liq_baseline`: min net `$2778.05`, min test `$199.18`, min fill `0.8776`.
- `NVDA` `b150__nvda__long_call__tight_reward__exit_360__liq_tight`: min net `$3357.40`, min test `$63.00`, min fill `0.8525`.
- `AAPL` `b150__aapl__long_call__wide_reward__exit_360__liq_baseline`: min net `$878.77`, min test `$810.01`, min fill `0.8684`.

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

Do not promote the Phase22 candidates from the current evidence. Keep the `0.90` fill-coverage gate intact, preserve the non-broker-facing posture, and require clean broker-audited paper-session evidence before any live manifest or strategy-selection change.

Do not promote candidates, relax gates, or change strategy/risk policy from Phase23 or Phase24 alone. Use Phase24 only to choose the next research repair path.

Keep INTC in research-only hold. Do not promote candidates, relax gates, or change strategy/risk policy from Phase24 or Phase25 alone. The next safest research step is not more promotion review; it is execution-cost sensitivity work and exit-policy design across the AAPL/NVDA wide-lag candidates, with explicit spread/slippage assumptions.

Phase26 completed the active diagnostic for that next step. Do not promote candidates, relax gates, or change strategy/risk policy from Phase26 alone. The next safe step is a governance review packet for the AAPL research candidate plus a separate fill-repair or strategy-design decision for the blocked NVDA/AAPL leads.
