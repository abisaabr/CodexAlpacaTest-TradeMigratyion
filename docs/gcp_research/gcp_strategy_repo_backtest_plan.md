# GCP Strategy Repo Backtest Plan

Date: 2026-04-30

This plan defines the repeatable research -> backtest -> repair -> retest -> promotion-review loop for the institutional paper-account strategy lab. It keeps the 0.90 fill gate intact and separates raw data coverage from strategy-level fill coverage.

## Promotion Gates

Use the repo policy if stricter. Otherwise enforce:

- `min_fill_coverage >= 0.90`
- `min_option_trade_count >= 20`
- `min_test_net_pnl > 0`
- `min_net_pnl > 0`
- no unresolved `promotion_blockers`
- no severe loser cluster indicating structural failure
- candidate survives portfolio-context review
- promotion means governed validation review only, not live activation

## Required Metric Split

The current disconnection is that raw data coverage and strategy-level fill coverage are easy to confuse. The backtester and promoter should track both:

- `data_foundation_coverage`: selected contract-days with available market data. QQQ 365d dense option bars currently pass this at `0.998732`.
- `strategy_fill_coverage`: candidate trades whose entry and exit can be filled under the tested lag/cost profile. QQQ 365d replay currently fails this, with top candidate fill around `0.1467` to `0.1733`.
- `fill_failure_reason`: must be populated from a controlled set such as `selected_contract_universe_gap`, `entry_bar_gap_or_entry_timing_mismatch`, `exit_bar_gap_or_exit_policy_mismatch`, `missing_option_price_count`, `illiquid_contract_or_wide_spread`, `strategy_asks_for_contracts_outside_available_chain`, `dataset_partition_or_symbol_date_mismatch`, or `script_schema_mismatch`.

Promotion should only consider strategy-level fill coverage after data-foundation coverage is already proven. If data coverage is below 0.90, run repair. If data coverage is above 0.90 but strategy fill is below 0.90, redesign strategy timing/contract selection or quarantine that parameterization.

## Wave Structure

### Wave 0: Smoke / Plumbing

Purpose: prove paths, schemas, metrics, and promotion packets with a tiny QQQ-only run.

Inputs:

- Stock bars: `gs://codexalpaca-data-us/research_stock_data/qqq_365d_next_trading_day_5x5_20260428/`
- Selected contracts: `gs://codexalpaca-control-us/research_results/qqq_365d_next_trading_day_5x5_20260428/research_wave/qqq_365d_next_trading_day_5x5_20260428/dense_universe/selected_option_contracts/`
- Option bars: `gs://codexalpaca-data-us/research_option_data/qqq_365d_next_trading_day_5x5_20260428/option_bars_silver/option_bars/underlying=QQQ/`

Required output:

- `option_aware_research_run_manifest.json`
- `option_aware_candidate_summary.json`
- `option_aware_trade_economics.json`
- `research_portfolio_report.json`
- `research_promotion_review_packet.json`

Recommended command shape after staging inputs locally or inside the Batch worker:

```powershell
python scripts\run_option_aware_research_backtest.py --queue-json <qqq_smoke_queue.json> --variants-jsonl <qqq_smoke_variants.jsonl> --stock-bars-path <stock_bars.parquet-or-root> --selected-contracts-root <selected_contracts_root> --option-bars-root <option_bars_root> --output-dir <replay_output> --run-id qqq_wave0_smoke --top-n 3 --symbol-filter QQQ --max-entry-lag-minutes 5 --max-exit-lag-minutes 10 --test-date-count 20 --initial-cash 25000 --allocation-fraction 0.05 --slippage-bps 10 --fee-per-contract 0.65 --contract-selection-method entry_liquidity_first_research_only
python scripts\build_research_portfolio_report.py --replay-root <replay_output> --output-dir <portfolio_report> --fill-coverage-gate 0.90 --min-option-trades 20 --min-test-net-pnl 0 --initial-cash 25000
python scripts\build_research_promotion_review_packet.py --portfolio-report-json <portfolio_report>\research_portfolio_report.json --output-dir <promotion_packet>
```

### Wave 1: Live Benchmark Retest

Purpose: benchmark exact live strategies from `multi_ticker_portfolio_live.yaml`, starting with QQQ, then all live manifest symbols.

Rules:

- Do not mutate the live manifest.
- Use exact live strategy names and exact family split.
- QQQ live sleeve expected split: Call backspread 2, Single-leg long call 2, Single-leg long put 4, Iron butterfly 2.
- Compare against dense data first; do not use sparse historical contract universes.

Decision:

- If exact live strategies fail because data foundation is missing, run `build_option_data_repair_plan.py` and then a targeted selected-contract download.
- If data foundation passes but strategy fill fails, classify as entry/exit timing mismatch and retest only after timing or contract-selection design changes.

### Wave 2: Beta-Promotion Retest

Purpose: retest governed beta families from `multi_ticker_portfolio_beta_promotions.yaml` without pretending governed supersets are exact historical subsets.

Priority:

- Put backspread
- Long straddle
- Iron butterfly retest-gap tickers
- Single-leg long call and Single-leg long put governed gaps after priority families are understood

Family semantics:

| Family | Exact promoted base subset preserved? | Current action |
| --- | --- | --- |
| Call backspread | yes | Benchmark exact live QQQ set. |
| Iron butterfly | no | Retest governed superset for AAPL, AMZN, IWM, SPY plus QQQ live benchmark. |
| Long straddle | no | Retest governed superset for AAPL. |
| Put backspread | no | Retest governed superset for AAPL, ABBV, ADBE, AMD, AMZN, ARM. |
| Single-leg long call | no | Benchmark live set and retest governed gap symbols after priority families. |
| Single-leg long put | no | Benchmark live set and retest governed gap symbols after priority families. |

### Wave 3: Full Strategy Repo Sweep

Purpose: run the entire strategy repository only after Waves 0-2 are clean.

Rules:

- Chunk by family and symbol.
- Use run manifests for every shard.
- Write raw research exhaust to GCS; write distilled promotion-review packets to control-plane/GitHub.
- Do not promote directly from a full sweep. Full sweep candidates must be re-run in focused replay and portfolio context.

## Repair Loop

Run repair only when the blocker is raw data coverage or a selected-contract universe gap.

```powershell
python scripts\build_option_data_repair_plan.py --manifest-json <download_manifest.json> --selected-contracts-root <selected_contracts_root> --output-dir <repair_plan_dir> --plan-id <plan_id> --dataset option_bars --option-batch-size 25
python scripts\download_option_market_data_for_selected_contracts.py --selected-contracts-root <repair_plan_dir>\selected_option_contracts --build-name <repair_build_name> --data-root <data_root> --reports-root <reports_root> --option-batch-size 25 --include-option-bars --no-include-option-trades
```

If `option_data_repair_plan.json` says `no_repair_needed`, do not run a broad download to hide strategy failures. Move to entry/exit timing redesign or quarantine.

## Current Wave Status

| Wave | Status | Result |
| --- | --- | --- |
| Wave 0 QQQ dense-data plumbing | Partially complete through data/repair diagnostics | QQQ option-bar foundation passes; no option-bar repair needed. Need a fresh bounded QQQ smoke replay using exact intended queue/variants. |
| Wave 1 live benchmark | Not clean yet | QQQ and SPY 365d comparable replays exist, but both are blocked by strategy fill/economics. Exact live benchmark should be re-run after Wave 0 confirms queue/variant alignment. |
| Wave 2 beta retest | Partially complete | Phase23/24/25 tested AAPL/INTC/NVDA leads. Phase25 INTC blocked on fill and economics. Wider AAPL/NVDA candidates require exit-policy design before promotion review. |
| Wave 3 full sweep | Not ready for direct promotion | Overnight partial rollup produced 216 candidates and 0 eligible. Treat as research-only evidence, not promotion. |

## Next Engineering Upgrades

- Add `data_foundation_coverage` to portfolio reports and promotion packets so a 99.8% raw data lane cannot be misread as a 15% candidate fill lane.
- Preserve `strategy_id`, `family`, and `parameter_set` in rollup `top_candidates`, `capital_plan`, and `data_repair_targets`; current rollups often expose symbol and economics but not strategy identity.
- Add a pre-promotion invariant: if `data_foundation_coverage >= 0.90` and `strategy_fill_coverage < 0.90`, the next state is `quarantine` or `strategy_design_retest`, not `repair_data_then_retest`.
- Run QQQ Wave 0 with controlled entry/exit lag profiles of 5/10, 10/30, and 30/60 minutes before broadening the tournament.
- For QQQ, prioritize strategies that intentionally trade only during high option-bar availability windows and use the dense next-trading-day ATM +/- 5 universe.
