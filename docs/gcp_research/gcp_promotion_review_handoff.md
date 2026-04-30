# GCP Promotion Review Handoff

Date: 2026-04-30

This handoff summarizes the non-broker-facing research state after the fill-coverage diagnostic. No trading was started, no broker-facing paper session was started, no live manifest was changed, and the 0.90 fill gate was not relaxed.

## Current GCP Job State

Recent relevant Batch jobs:

| Job | State | Notes |
| --- | --- | --- |
| `phase42-dense-download-replay-20260428182000` | `SUCCEEDED` | Produced per-symbol dense data shards under Phase42. |
| `overnight-next10-365d-replay-fix2-20260429030000` | `SUCCEEDED` | Produced next10 gcsfix replay reports. |
| `overnight-spy-365d-replay-rerun-20260429181000` | `SUCCEEDED` | Produced SPY rerun reports. |
| `overnight-top10-365d-replay-fix4-20260429030000` | `FAILED` | Failed from task runtime after earlier global CPU quota pressure; not a promotion result. |

There was no active Batch job requiring intervention at the time of this handoff.

## Promotion-Review Results

| Candidate set | Decision | Candidate count | Eligible count | State |
| --- | --- | ---: | ---: | --- |
| QQQ next10 gcsfix 365d replay | `research_only_blocked` | 36 | 0 | `quarantine` current parameterizations until entry timing is redesigned |
| SPY 365d rerun | `research_only_blocked` | 36 | 0 | `quarantine` current parameterizations until entry/exit timing is redesigned |
| Overnight partial wave rollup | `research_only_blocked` | 216 | 0 | `hold_for_more_data` only for uncovered beta symbols; otherwise `quarantine` low-fill parameterizations |
| Phase23 AAPL/INTC/NVDA stress | `research_only_blocked` | 6 | 0 | `repair_data_then_retest` was already superseded by Phase24 feasibility |
| Phase24 exit-lag feasibility | `fill_feasible_under_full_stack` | 5 | not promotion | `hold_for_exit_policy_design` |
| Phase25 INTC isolated stress | `research_only_blocked` | 1 | 0 | `quarantine` current INTC candidate |

No candidate cleared governed promotion-review eligibility in this pass.

## Important Findings

- QQQ raw option-bar coverage is strong: `0.998732` selected contract-day coverage over 5,522 contract-days.
- QQQ option-bar repair plan returned `no_repair_needed`.
- QQQ strategy replay fill remains weak: 36/36 candidates failed the 0.90 fill gate; the top QQQ candidate had `min_fill_coverage=0.1467` and failed OOS/test PnL.
- SPY shows the same structural pattern: raw data exists, but 36/36 candidates failed the 0.90 fill gate, dominated by entry timing mismatch.
- The broad partial 365d rollup produced profitable-looking candidates, but none were eligible because strategy fill coverage and/or economics did not clear the gates.

## State Decisions

- `promote_to_governed_validation_review`: none.
- `hold_for_more_data`: beta symbols not proven in the inspected dense 365d roots, including ABBV, ADBE, ARM, ASTS, BA, BABA, CRWV, DAL, DIS, GME, GOOG, HIMS, IONQ, IREN, OXY, QCOM, RKLB, SMCI, SNDK, TTD, UPRO, URA, and WULF.
- `repair_data_then_retest`: only if `build_option_data_repair_plan.py` reports missing selected option-bar or option-trade symbol-days for the exact selected-contract root. QQQ option bars do not currently need repair.
- `quarantine`: current QQQ, SPY, and INTC replay parameterizations that fail fill despite a healthy data foundation or also fail economics.
- `kill`: not assigned globally. Individual parameterizations can be killed after one more controlled Wave 0/Wave 1 rerun proves they still fail under aligned queue, selected-contract universe, and timing windows.

## Next Best Step

Run a fresh QQQ-only Wave 0 smoke replay using the dense 365d selected-contract data and a deliberately tiny queue. The goal is not to find five promotions immediately; it is to prove that:

- stock bars, selected contracts, and option bars are staged from the same dataset lineage;
- `data_foundation_coverage` and `strategy_fill_coverage` are both emitted;
- failure causes are populated at strategy level;
- `research_portfolio_report.json` and `research_promotion_review_packet.json` preserve `strategy_id`, `family`, and `parameter_set`.

If Wave 0 still shows data foundation above 0.90 and strategy fill below 0.90, the correct action is strategy timing redesign, not another broad data pull.

## Exact GCS Artifacts

- QQQ 365d coverage: `gs://codexalpaca-control-us/research_results/qqq_365d_next_trading_day_5x5_20260428/research_wave/qqq_365d_next_trading_day_5x5_20260428/coverage/coverage_summary.json`
- QQQ 365d download packet: `gs://codexalpaca-control-us/research_results/qqq_365d_next_trading_day_5x5_20260428/download_report/qqq_365d_next_trading_day_5x5_option_bars_20250429_20260428/selected_contract_market_data_download_packet.json`
- Phase42 dense shards: `gs://codexalpaca-control-us/research_results/top100_liquidity_research_20260426/portfolio_event_driven_data/phase42_dense_download_replay_20260428182000/data_shards/`
- Overnight partial rollup: `gs://codexalpaca-control-us/research_results/overnight_365d_bruteforce_20260429/partial_wave_rollup_gcsfix_03bfc25_20260429T1806Z/wave_rollup/`
- QQQ gcsfix replay: `gs://codexalpaca-control-us/research_results/overnight_365d_bruteforce_20260429/next10_replay_gcsfix_03bfc25/QQQ/`
- SPY rerun: `gs://codexalpaca-control-us/research_results/overnight_365d_bruteforce_20260429/top10_replay_gcsfix_spy_rerun_03bfc25_20260429T1810Z/SPY/`

## Commands Used

```powershell
gcloud batch jobs describe phase42-dense-download-replay-20260428182000 --location us-central1 --project codexalpaca --format=json
gcloud batch jobs describe overnight-next10-365d-replay-fix2-20260429030000 --location us-central1 --project codexalpaca --format=json
gcloud batch jobs describe overnight-top10-365d-replay-fix4-20260429030000 --location us-central1 --project codexalpaca --format=json
gcloud batch jobs describe overnight-spy-365d-replay-rerun-20260429181000 --location us-central1 --project codexalpaca --format=json
gcloud storage cp gs://codexalpaca-control-us/research_results/top100_liquidity_research_20260426/portfolio_event_driven_data/phase23_candidate_stress_holdout_20260428062500/promotion_review_packet/research_promotion_review_packet.json C:\Users\abisa\Downloads\gcp_research_diag_20260430\phase23_promotion_review_packet.json
gcloud storage cp gs://codexalpaca-control-us/research_results/top100_liquidity_research_20260426/portfolio_event_driven_data/phase24_exit_lag_feasibility_20260428073500/exit_lag_feasibility/exit_lag_feasibility_packet.json C:\Users\abisa\Downloads\gcp_research_diag_20260430\phase24_exit_lag_feasibility_packet.json
gcloud storage cp gs://codexalpaca-control-us/research_results/top100_liquidity_research_20260426/portfolio_event_driven_data/phase25_intc_isolated_stress_20260428085000/promotion_review_packet/research_promotion_review_packet.json C:\Users\abisa\Downloads\gcp_research_diag_20260430\phase25_promotion_review_packet.json
gcloud storage cp gs://codexalpaca-control-us/research_results/overnight_365d_bruteforce_20260429/partial_wave_rollup_gcsfix_03bfc25_20260429T1806Z/wave_rollup/research_wave_portfolio_rollup.json C:\Users\abisa\Downloads\gcp_research_diag_20260430\overnight_partial_wave_rollup.json
gcloud storage cp gs://codexalpaca-control-us/research_results/overnight_365d_bruteforce_20260429/partial_wave_rollup_gcsfix_03bfc25_20260429T1806Z/wave_rollup/promotion_review_packet/research_promotion_review_packet.json C:\Users\abisa\Downloads\gcp_research_diag_20260430\overnight_partial_promotion_review_packet.json
gcloud storage cp gs://codexalpaca-control-us/research_results/overnight_365d_bruteforce_20260429/next10_replay_gcsfix_03bfc25/QQQ/promotion_packet/research_promotion_review_packet.json C:\Users\abisa\Downloads\gcp_research_diag_20260430\qqq_next10_promotion_review_packet.json
gcloud storage cp gs://codexalpaca-control-us/research_results/overnight_365d_bruteforce_20260429/top10_replay_gcsfix_spy_rerun_03bfc25_20260429T1810Z/SPY/promotion_packet/research_promotion_review_packet.json C:\Users\abisa\Downloads\gcp_research_diag_20260430\spy_rerun_promotion_review_packet.json
```
