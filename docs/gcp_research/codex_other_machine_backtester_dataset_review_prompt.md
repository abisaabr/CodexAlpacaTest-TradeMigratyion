# Codex Prompt: Backtester And Dataset Review Handoff

You are the Codex reviewer on a second machine for the institutional paper-account strategy lab.

Goal:
Review the backtester, promotion-review chain, QQQ tournament artifacts, and Google Cloud datasets we created. Confirm whether the backtester and promoter are measuring the same edge, whether fill coverage is being interpreted correctly, and what the next safest engineering/backtest step is.

Absolute date context:
- Today is April 30, 2026.
- Do not start trading.
- Do not start a broker-facing paper session.
- Do not change live manifests.
- Do not change risk policy.
- Do not lower the `fill_coverage >= 0.90` gate.
- Promotion means research/governed-validation review only, not live activation.

## Repos To Use

Use current checkouts, not stale folders.

Runner repo:

```text
C:\Users\<you>\Downloads\codexalpaca_repo
```

Canonical runner state:

```text
branch: origin/codex/qqq-paper-portfolio
commit: 91ce125adb33003a1d999ccd74958eec60b9556d
```

Control-plane repo:

```text
C:\Users\<you>\Downloads\CodexAlpacaTest-TradeMigratyion
```

If that checkout is stale, use the clean checkout tracking published `origin/main`.

Review branch/PR created by the first machine:

```text
repo: abisaabr/CodexAlpacaTest-TradeMigratyion
branch: codex/gcp-fill-coverage-diagnostic-20260430
draft PR: https://github.com/abisaabr/CodexAlpacaTest-TradeMigratyion/pull/3
commits:
  a484f7a0baa5892f170b028605d88af1c04b4178
  f5648c8
```

## Read First

Runner repo files:

```text
config\promotion_manifests\multi_ticker_portfolio_beta_promotions.yaml
config\strategy_manifests\multi_ticker_portfolio_live.yaml
scripts\run_gcp_research_wave.py
scripts\run_option_aware_research_backtest.py
scripts\build_research_portfolio_report.py
scripts\build_research_promotion_review_packet.py
scripts\build_option_data_repair_plan.py
scripts\download_option_market_data_for_selected_contracts.py
```

Control-plane files from PR/branch:

```text
docs\gcp_research\gcp_fill_coverage_diagnostic.md
docs\gcp_research\gcp_strategy_repo_backtest_plan.md
docs\gcp_research\gcp_promotion_review_handoff.md
docs\gcp_research\gcp_promotion_review_summary.json
docs\gcp_research\qqq_tournament_runbook_results.csv
docs\gcp_research\qqq_tournament_runbook_results.md
```

Control-plane policy/context docs, if present:

```text
docs\PROJECT_TARGET_OPERATING_MODEL.md
docs\STRATEGY_PROMOTION_POLICY.md
docs\LOSER_TRADE_LEARNING_POLICY.md
docs\STRATEGY_REPO_OPERATING_MODEL.md
docs\strategy_family_registry\strategy_family_registry.json
docs\strategy_family_registry\strategy_family_registry.md
```

## GCS Artifacts To Review

Mirrored control-plane packet:

```text
gs://codexalpaca-control-us/research_results/gcp_research_fill_coverage_diagnostic_20260430/control_plane_packet/
```

Files expected there:

```text
gcp_fill_coverage_diagnostic.md
gcp_strategy_repo_backtest_plan.md
gcp_promotion_review_handoff.md
gcp_promotion_review_summary.json
qqq_tournament_runbook_results.csv
qqq_tournament_runbook_results.md
```

QQQ dense 365d dataset:

```text
stock bars:
gs://codexalpaca-data-us/research_stock_data/qqq_365d_next_trading_day_5x5_20260428/

option inventory:
gs://codexalpaca-data-us/research_option_data/qqq_365d_next_trading_day_5x5_20260428/contract_inventory_silver/option_contract_inventory/underlying=QQQ/

selected contracts:
gs://codexalpaca-control-us/research_results/qqq_365d_next_trading_day_5x5_20260428/research_wave/qqq_365d_next_trading_day_5x5_20260428/dense_universe/selected_option_contracts/

option bars:
gs://codexalpaca-data-us/research_option_data/qqq_365d_next_trading_day_5x5_20260428/option_bars_silver/option_bars/underlying=QQQ/

coverage summary:
gs://codexalpaca-control-us/research_results/qqq_365d_next_trading_day_5x5_20260428/research_wave/qqq_365d_next_trading_day_5x5_20260428/coverage/coverage_summary.json

download packet:
gs://codexalpaca-control-us/research_results/qqq_365d_next_trading_day_5x5_20260428/download_report/qqq_365d_next_trading_day_5x5_option_bars_20250429_20260428/selected_contract_market_data_download_packet.json
```

QQQ replay/promotion packet:

```text
gs://codexalpaca-control-us/research_results/overnight_365d_bruteforce_20260429/next10_replay_gcsfix_03bfc25/QQQ/
```

SPY rerun for comparison:

```text
gs://codexalpaca-control-us/research_results/overnight_365d_bruteforce_20260429/top10_replay_gcsfix_spy_rerun_03bfc25_20260429T1810Z/SPY/
```

Overnight partial wave rollup:

```text
gs://codexalpaca-control-us/research_results/overnight_365d_bruteforce_20260429/partial_wave_rollup_gcsfix_03bfc25_20260429T1806Z/wave_rollup/
```

Phase42 dense top10 shards:

```text
gs://codexalpaca-control-us/research_results/top100_liquidity_research_20260426/portfolio_event_driven_data/phase42_dense_download_replay_20260428182000/data_shards/
```

Top10 ladder data:

```text
stock:
gs://codexalpaca-data-us/research_stock_data/option_fill_ladder_20260429/

options:
gs://codexalpaca-data-us/research_option_data/option_fill_ladder_20260429/
```

Next10 ladder data:

```text
stock:
gs://codexalpaca-data-us/research_stock_data/option_fill_ladder_next10_20260429/

options:
gs://codexalpaca-data-us/research_option_data/option_fill_ladder_next10_20260429/
```

## Facts To Verify

The first machine found:

- QQQ 365d dense option-bar selected contract-day coverage is `0.998732`.
- QQQ selected contract-days: `5522`.
- QQQ contract-days with bars: `5515`.
- QQQ option-bar rows: `1593974`.
- QQQ downloader failed chunks: `0`.
- Canonical QQQ option-bar repair check returned `no_repair_needed`.
- QQQ current 365d replay/promotion packet: `36` candidates, `0` eligible.
- QQQ blockers: `fill_coverage_below_0.90` for all 36 candidates, `min_net_pnl_not_positive` for 35, `test_net_pnl_not_above_0` for 31.
- Best observed QQQ candidate in current packet: `min_net_pnl=7482.118`, `min_test_net_pnl=-8204.365`, `min_fill_coverage=0.1467`, `max_fill_coverage=0.1733`, `min_option_trade_count=88`.
- Dominant QQQ fill failure classification: `entry_bar_gap_or_entry_timing_mismatch`.
- Interpretation: raw QQQ option-bar data is not the current blocker; strategy-level fill timing and replay semantics are the blocker.

## Review Questions

1. Does the backtester cleanly separate raw data coverage from strategy-level fill coverage?
2. Does `build_research_portfolio_report.py` preserve enough identity in rollups: `strategy_id`, `family`, `parameter_set`, symbol, and profile?
3. Does `build_research_promotion_review_packet.py` use the same gates we intend?
4. Does the QQQ current replay load the same dataset lineage as the dense coverage check?
5. Are failed fills caused by strategy entry timestamps, exit timestamps, contract-selection mismatch, option-bar partition lookup, or schema/path mismatch?
6. Does the backtester accidentally use nearest-contract selection when the dataset was built for next-trading-day ATM +/- 5 selected contracts?
7. Does the replay reserve out-of-sample/test dates correctly and consistently for QQQ?
8. Are fill failures counted per candidate trade, per leg, or per multi-leg strategy? Confirm this is consistent with promotion intent.
9. Are multi-leg strategies such as call backspread and iron butterfly unfairly penalized by requiring every leg to have same-minute bars, and if so should the design use a bounded entry/exit bar window while preserving the 0.90 gate?
10. What exact patch would make the tournament outputs promotion-grade and auditable?

## Expected Next Step

Do not launch a full sweep first. The next safe step is a bounded QQQ Wave 0 smoke replay:

- QQQ only.
- Tiny queue: one representative live bull, bear, and choppy family if possible.
- Use the QQQ 365d dense selected-contract dataset.
- Emit both `data_foundation_coverage` and `strategy_fill_coverage`.
- Emit `fill_failure_reason` for every candidate.
- Preserve `strategy_id`, `family`, and `parameter_set` through replay, portfolio report, promotion packet, and rollup.

Suggested command shape:

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

## Required Final Report

Report:

- Whether the GitHub branch and GCS handoff were found.
- Whether QQQ dense raw data coverage was independently confirmed.
- Whether the QQQ repair-plan status `no_repair_needed` was independently confirmed.
- Whether replay fill coverage is being calculated correctly.
- Whether the promoter and backtester use consistent candidate identity and gates.
- The exact root cause of QQQ low strategy-fill coverage, if identified.
- The exact patch or commands needed for the next QQQ Wave 0.
- Whether any strategy should move to governed promotion review. If not, say none.

Hard rule:
Do not promote anything unless the generated promotion-review packet says it is eligible.
