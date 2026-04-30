# GCP Fill Coverage Diagnostic

Date: 2026-04-30

Scope: non-broker-facing research, replay, repair, and promotion-review diagnostics only. This packet does not authorize trading, paper trading sessions, live manifest edits, risk-policy edits, or a lower fill gate.

## Canonical Inputs

- Runner repo canonical branch: `origin/codex/qqq-paper-portfolio`
- Runner commit confirmed: `91ce125adb33003a1d999ccd74958eec60b9556d`
- Beta manifest: `config/promotion_manifests/multi_ticker_portfolio_beta_promotions.yaml`
- Live manifest: `config/strategy_manifests/multi_ticker_portfolio_live.yaml`
- Control-plane checkout: `C:\Users\abisa\Downloads\CodexAlpacaTest-TradeMigratyion_gcp_lease_lane`
- Control-plane commit at diagnostic start: `c72ff43a78e4cacc2b4909ec40354aa36e639952`

## GCS Data Map

| Data class | Primary bucket/prefix | Notes |
| --- | --- | --- |
| QQQ 365d stock bars | `gs://codexalpaca-data-us/research_stock_data/qqq_365d_next_trading_day_5x5_20260428/` | QQQ chunks from 2025-04-29 through 2026-04-28 were present. |
| QQQ 365d option inventory | `gs://codexalpaca-data-us/research_option_data/qqq_365d_next_trading_day_5x5_20260428/contract_inventory_silver/option_contract_inventory/underlying=QQQ/` | Includes combined inventory and date chunks. |
| QQQ 365d selected contracts | `gs://codexalpaca-control-us/research_results/qqq_365d_next_trading_day_5x5_20260428/research_wave/qqq_365d_next_trading_day_5x5_20260428/dense_universe/selected_option_contracts/` | Next listed expiry after trade date, ATM +/- 5 strikes, calls and puts. |
| QQQ 365d option bars | `gs://codexalpaca-data-us/research_option_data/qqq_365d_next_trading_day_5x5_20260428/option_bars_silver/option_bars/underlying=QQQ/` | 251 option-bar trade-date partitions were present. |
| Top10 ladder stock bars | `gs://codexalpaca-data-us/research_stock_data/option_fill_ladder_20260429/` | AAPL, AMD, AMZN, INTC, IWM, META, MSFT, NVDA, SPY, TSLA. |
| Top10 ladder option data | `gs://codexalpaca-data-us/research_option_data/option_fill_ladder_20260429/` | Same top10 symbol set as stock ladder. |
| Next10 ladder stock bars | `gs://codexalpaca-data-us/research_stock_data/option_fill_ladder_next10_20260429/` | AVGO, GOOGL, MU, NFLX, ORCL, PLTR, QQQ, TSM, XLE, XOM. |
| Next10 ladder option data | `gs://codexalpaca-data-us/research_option_data/option_fill_ladder_next10_20260429/` | Same next10 symbol set as stock ladder. |
| Top100 active/inactive inventory repair | `gs://codexalpaca-data-us/research_option_data/top100_liquidity_research_20260426/phase40_active_inactive_contract_inventory_20260428175500/` | Phase40 fixed the earlier active-only inventory limitation for top10 coverage. |
| Phase42 dense top10 replay/data shards | `gs://codexalpaca-control-us/research_results/top100_liquidity_research_20260426/portfolio_event_driven_data/phase42_dense_download_replay_20260428182000/` | Job succeeded and produced per-symbol shard reports. No wave-level aggregate packet was present at the root. |
| Overnight 365d replay rollup | `gs://codexalpaca-control-us/research_results/overnight_365d_bruteforce_20260429/partial_wave_rollup_gcsfix_03bfc25_20260429T1806Z/wave_rollup/` | Partial rollup over six reports, blocked for promotion review. |
| SPY 365d rerun | `gs://codexalpaca-control-us/research_results/overnight_365d_bruteforce_20260429/top10_replay_gcsfix_spy_rerun_03bfc25_20260429T1810Z/SPY/` | Job succeeded; promotion packet blocked. |

The beta-promotion universe is larger than the current dense ladders. QQQ, SPY, IWM, AMZN, AAPL, AMD, AVGO, MSFT, NVDA, TSLA, XLE, and XOM have dense ladder evidence in the inspected roots. Beta symbols such as ABBV, ADBE, ARM, ASTS, BA, BABA, CRWV, DAL, DIS, GME, GOOG, HIMS, IONQ, IREN, OXY, QCOM, RKLB, SMCI, SNDK, TTD, UPRO, URA, and WULF were not proven covered by the current inspected 365d dense roots and require symbol-specific inventory/data confirmation before replay promotion review.

## QQQ 365d Dense Coverage

The QQQ 365d next-trading-day ATM +/- 5 strike dataset is healthy at the raw option-bar layer:

- Dataset: `qqq_365d_next_trading_day_5x5_20260428`
- Trade dates selected: 251
- Selected contract-days: 5,522
- Option bar rows: 1,593,974
- Contract-days with any bar: 5,515
- Contract-day coverage: `0.998732`
- Missing contract-days: 7
- Downloader failed chunks: 0

The canonical repair tool was run against this selected-contract universe and downloader manifest for `option_bars`. Result: `no_repair_needed`.

Repair-plan result:

```text
selected_source_rows: 5522
selected_subset_rows: 0
datasets: option_bars
repair_chunk_count: 0
expected_symbol_days: 5522
completed_symbol_days: 5522
remaining_symbol_days: 0
```

Interpretation: QQQ's current low replay fill is not caused by missing raw QQQ option bars in the dense 365d dataset. If a future replay requires quotes or option trades instead of option bars, those must be downloaded and tracked separately; this check only validates the option-bar path used by the dense selected-contract download.

## Promotion-Replay Fill Failures

| Replay packet | Result | Dominant blocker | Classification |
| --- | --- | --- | --- |
| QQQ next10 gcsfix 365d replay | 36 candidates, 0 eligible | all 36 below `fill_coverage >= 0.90`; 31 also failed test PnL and 35 failed min net PnL | `entry_bar_gap_or_entry_timing_mismatch` plus poor economics |
| SPY 365d rerun | 36 candidates, 0 eligible | all 36 below fill gate; 30 failed min net PnL and 33 failed test PnL | mostly `entry_bar_gap_or_entry_timing_mismatch`, some `exit_bar_gap_or_exit_policy_mismatch` |
| Overnight partial wave rollup | 216 candidates, 0 eligible | rollup reports every candidate below fill gate; many also failed economics | 196 entry timing mismatch, 18 exit-policy mismatch, 2 mixed low-fill gap |
| Phase23 AAPL/INTC/NVDA candidate stress | 6 candidates, 0 eligible | all six below fill gate; one INTC variant also failed test PnL | short-lag fill stack not robust enough |
| Phase24 exit-lag feasibility | 5 candidates tested, not promotion | 1 full-stack fill-feasible, 4 wide-lag or conditional only | exit policy can recover some fill but changes strategy behavior |
| Phase25 isolated INTC stress | 1 candidate, 0 eligible | fill below 0.90, min net PnL <= 0, test net PnL <= 0 | cost-sensitive lead should be quarantined for current promotion lane |

## Cause Classification

- `selected_contract_universe_gap`: This was the main pre-Phase40 issue. Phase39/40/41 established that active-only inventory was insufficient and that active+inactive inventory plus dense selected contracts materially improved raw selected-contract coverage.
- `dataset_partition_or_symbol_date_mismatch`: This affected invalid previous replay outputs under `top10_replay_fixed_03bfc25`, where input downloads landed outside the intended local tree and caused `no_source_stock_trades`. The corrected gcsfix downloader path fixed the pathing issue for later replays.
- `entry_bar_gap_or_entry_timing_mismatch`: This is now the dominant live blocker for QQQ, SPY, and the overnight partial wave. Raw option bars exist, but candidate entry timestamps or contract selection do not map to available option bars within the tested lag window often enough to clear 0.90.
- `exit_bar_gap_or_exit_policy_mismatch`: This affects IWM, part of SPY, and the Phase24 wide-lag-only AAPL/NVDA candidates. It means the exit policy asks for fills at times that are not consistently covered by the selected option-bar data.
- `missing_option_price_count`: Not dominant for QQQ option bars after the dense 365d repair check. It remains possible for replays that require option trades or quotes instead of bars.
- `illiquid_contract_or_wide_spread`: Not the primary raw-data cause in the QQQ 365d dense set, but still a likely economic/execution-quality risk for candidates that require wide lag, high slippage tolerance, or illiquid strikes.
- `strategy_asks_for_contracts_outside_available_chain`: Mitigated by the dense next-trading-day ATM +/- 5 universe for QQQ and top10, but still a risk for broad beta symbols not yet proven covered.
- `script_schema_mismatch`: No current schema mismatch was proven in the QQQ repair-plan check. The older GCS path bug was a downloader pathing issue, not a promotion-policy issue.

## Commands Used

```powershell
git -C C:\Users\abisa\Downloads\codexalpaca_repo fetch origin --prune
git -C C:\Users\abisa\Downloads\codexalpaca_repo rev-parse origin/codex/qqq-paper-portfolio
git -C C:\Users\abisa\Downloads\CodexAlpacaTest-TradeMigratyion_gcp_lease_lane fetch origin --prune
gcloud batch jobs list --location us-central1 --project codexalpaca --format=json
gcloud storage cp gs://codexalpaca-control-us/research_results/qqq_365d_next_trading_day_5x5_20260428/research_wave/qqq_365d_next_trading_day_5x5_20260428/coverage/coverage_summary.json C:\Users\abisa\Downloads\gcp_research_diag_20260430\qqq_365d_coverage_summary.json
gcloud storage cp gs://codexalpaca-control-us/research_results/qqq_365d_next_trading_day_5x5_20260428/download_report/qqq_365d_next_trading_day_5x5_option_bars_20250429_20260428/selected_contract_market_data_download_packet.json C:\Users\abisa\Downloads\gcp_research_diag_20260430\qqq_365d_download_packet.json
gcloud storage cp gs://codexalpaca-control-us/research_results/qqq_365d_next_trading_day_5x5_20260428/download_report/qqq_365d_next_trading_day_5x5_option_bars_20250429_20260428/manifest.json C:\Users\abisa\Downloads\gcp_research_diag_20260430\qqq_365d_download_manifest.json
gcloud storage cp -r gs://codexalpaca-control-us/research_results/qqq_365d_next_trading_day_5x5_20260428/research_wave/qqq_365d_next_trading_day_5x5_20260428/dense_universe/selected_option_contracts/* C:\Users\abisa\Downloads\gcp_research_diag_20260430\qqq_365d_selected_contracts
python C:\Users\abisa\Downloads\codexalpaca_repo_canonical_91ce125\scripts\build_option_data_repair_plan.py --manifest-json C:\Users\abisa\Downloads\gcp_research_diag_20260430\qqq_365d_download_manifest.json --selected-contracts-root C:\Users\abisa\Downloads\gcp_research_diag_20260430\qqq_365d_selected_contracts --output-dir C:\Users\abisa\Downloads\gcp_research_diag_20260430\qqq_365d_option_bar_repair_plan --plan-id qqq_365d_dense_option_bar_repair_check_20260430 --dataset option_bars --option-batch-size 25
```

## Bottom Line

For QQQ, the fill issue is no longer raw option-bar availability. The promoter is correctly blocking current candidates because strategy-level fill coverage remains far below 0.90 in replay. The next repair is not another broad QQQ option-bar pull; it is alignment of strategy entry/exit timing, selected-contract replay semantics, and promotion packet interpretation.
