# QQQ Tournament Runbook And Results

Date: 2026-04-30

Scope: QQQ-only research and replay summary. This file is non-broker-facing. It does not authorize trading, paper sessions, live manifest changes, or a lower fill gate.

## How The Tournament Is Run

The tournament has five gates:

1. Build or verify a dense QQQ data foundation: stock bars, active+inactive option inventory, selected contracts, and option bars.
2. Run option-aware replay for a bounded QQQ strategy/variant queue across explicit entry-lag, exit-lag, slippage, and fee profiles.
3. Build a research portfolio report from the replay root.
4. Build a promotion-review packet from the portfolio report.
5. Promote only to governed validation review if the packet says `eligible_for_promotion_review`; otherwise hold, repair, quarantine, or kill.

Canonical replay command shape:

```powershell
python scripts\run_option_aware_research_backtest.py `
  --queue-json <qqq_smoke_queue.json> `
  --variants-jsonl <qqq_smoke_variants.jsonl> `
  --stock-bars-path <stock_bars> `
  --selected-contracts-root <selected_contracts_root> `
  --option-bars-root <option_bars_root> `
  --output-dir <replay_output> `
  --run-id qqq_wave0_smoke `
  --top-n 3 `
  --symbol-filter QQQ `
  --max-entry-lag-minutes 5 `
  --max-exit-lag-minutes 10 `
  --test-date-count 20 `
  --initial-cash 25000 `
  --allocation-fraction 0.05 `
  --slippage-bps 10 `
  --fee-per-contract 0.65 `
  --contract-selection-method entry_liquidity_first_research_only
```

Canonical report and promotion packet commands:

```powershell
python scripts\build_research_portfolio_report.py `
  --replay-root <replay_output> `
  --output-dir <portfolio_report> `
  --fill-coverage-gate 0.90 `
  --min-option-trades 20 `
  --min-test-net-pnl 0 `
  --initial-cash 25000

python scripts\build_research_promotion_review_packet.py `
  --portfolio-report-json <portfolio_report>\research_portfolio_report.json `
  --output-dir <promotion_packet>
```

## QQQ Data Foundation

Current dense QQQ 365d dataset:

- Stock bars: `gs://codexalpaca-data-us/research_stock_data/qqq_365d_next_trading_day_5x5_20260428/`
- Selected contracts: `gs://codexalpaca-control-us/research_results/qqq_365d_next_trading_day_5x5_20260428/research_wave/qqq_365d_next_trading_day_5x5_20260428/dense_universe/selected_option_contracts/`
- Option bars: `gs://codexalpaca-data-us/research_option_data/qqq_365d_next_trading_day_5x5_20260428/option_bars_silver/option_bars/underlying=QQQ/`
- Coverage summary: `gs://codexalpaca-control-us/research_results/qqq_365d_next_trading_day_5x5_20260428/research_wave/qqq_365d_next_trading_day_5x5_20260428/coverage/coverage_summary.json`

Verified coverage:

| Metric | Value |
| --- | ---: |
| Selected trade dates | 251 |
| Selected contract-days | 5,522 |
| Option bar rows | 1,593,974 |
| Contract-days with bars | 5,515 |
| Missing contract-days | 7 |
| Contract-day coverage | 0.998732 |
| Downloader failed chunks | 0 |

Repair-plan check:

```powershell
python C:\Users\abisa\Downloads\codexalpaca_repo_canonical_91ce125\scripts\build_option_data_repair_plan.py `
  --manifest-json C:\Users\abisa\Downloads\gcp_research_diag_20260430\qqq_365d_download_manifest.json `
  --selected-contracts-root C:\Users\abisa\Downloads\gcp_research_diag_20260430\qqq_365d_selected_contracts `
  --output-dir C:\Users\abisa\Downloads\gcp_research_diag_20260430\qqq_365d_option_bar_repair_plan `
  --plan-id qqq_365d_dense_option_bar_repair_check_20260430 `
  --dataset option_bars `
  --option-batch-size 25
```

Result: `no_repair_needed`.

Interpretation: QQQ's current promotion failure is not caused by missing dense option bars.

## Results So Far

| Step | Status | Candidate count | Eligible count | Key result |
| --- | --- | ---: | ---: | --- |
| QQQ 365d dense data foundation | complete | n/a | n/a | Raw option-bar coverage is `0.998732`. |
| QQQ 365d option-bar repair plan | no repair needed | n/a | n/a | 5,522 expected symbol-days, 5,522 completed, 0 remaining. |
| QQQ next10 gcsfix replay | research-only blocked | 36 | 0 | All candidates failed `fill_coverage >= 0.90`. |
| QQQ promotion-review packet | research-only blocked | 36 | 0 | No governed promotion-review candidate. |

Best observed QQQ replay candidate from the current packet:

| Metric | Value |
| --- | ---: |
| Min net PnL | 7,482.118 |
| Min test net PnL | -8,204.365 |
| Min fill coverage | 0.1467 |
| Max fill coverage | 0.1733 |
| Min option trade count | 88 |

Blockers:

- `fill_coverage_below_0.90`: 36 of 36 candidates.
- `min_net_pnl_not_positive`: 35 of 36 candidates.
- `test_net_pnl_not_above_0`: 31 of 36 candidates.
- Dominant fill failure: `entry_bar_gap_or_entry_timing_mismatch`.

## Current Interpretation

The QQQ data foundation is now strong, but the QQQ replay candidates are not aligned with that data foundation at the strategy-fill level. The disconnect is between strategy entry/exit timing and option-bar fillability, not between Alpaca and our raw QQQ option-bar download.

The next QQQ tournament should be a bounded Wave 0 smoke run with a tiny queue and explicit metrics:

- `strategy_id`
- `family`
- `parameter_set`
- `data_foundation_coverage`
- `strategy_fill_coverage`
- `fill_failure_reason`

If `data_foundation_coverage >= 0.90` and `strategy_fill_coverage < 0.90`, the candidate should move to strategy timing redesign or quarantine, not data repair.

## CSV Companion

Machine-readable results are in:

`docs/gcp_research/qqq_tournament_runbook_results.csv`
