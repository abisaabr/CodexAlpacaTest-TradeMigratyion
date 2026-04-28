# Phase42 Dense Download Replay Status

## State

- Phase ID: `phase42_dense_download_replay_20260428182000`
- Batch job: `phase42-dense-download-replay-20260428182000`
- Latest state: `SUCCEEDED`
- Latest task counts: `10` succeeded / `0` failed
- Location: `codexalpaca/us-central1`
- Tasks: `10`
- Parallelism: `4`
- Broker-facing: `false`
- Alpaca data/metadata used: `true`
- Trading effect: `none`
- Live manifest effect: `none`
- Risk policy effect: `none`

## Scope

Phase42 is the repaired top-10 dense option data download and replay lane after the Phase40/Phase41 fill-foundation repair.

Symbols: `SPY`, `NVDA`, `QQQ`, `AMZN`, `TSLA`, `MSFT`, `IWM`, `AAPL`, `META`, and `MU`.

It used:

- source archive: `gs://codexalpaca-control-us/research_source/codexalpaca_runner_source_91d75fb36c7c.zip`
- selected contracts: Phase41 dense selected-contract roots
- stock reference source: `gs://codexalpaca-data-us/curated/stocks/research_150_1min_20260401_20260423_stock_only.parquet`
- option data window: `2026-04-01` through `2026-04-23`
- initial cash: `$25,000`
- allocation fraction: `0.10`
- strategy queue: `top100_portfolio_bruteforce_queue.json`
- variants source: `broad_150_stock_proxy_variants.jsonl`

Stress profiles:

- `phase42_lag5_exit10_slip10_fee065`
- `phase42_lag10_exit30_slip25_fee100`
- `phase42_lag30_exit60_slip50_fee150`

## Final Result

- Wave rollup decision: `research_only_blocked`
- Source shard reports: `10`
- Candidates scanned: `183`
- Eligible for governed promotion review: `0`
- Fill gate: `0.9`
- Minimum option trades gate: `20`
- Blocker counts: `{'fill_coverage_below_0.90': 183, 'min_net_pnl_not_positive': 17, 'option_trades_below_20': 120, 'test_net_pnl_not_above_0': 89}`
- Fill failure counts: `{'exit_bar_gap_or_exit_policy_mismatch': 183}`
- Rollup artifact root: `gs://codexalpaca-control-us/research_results/top100_liquidity_research_20260426/rollups/phase42_dense_download_replay_20260428232000/output/`

## Research-Only Capital Plan

The rollup produced a research-only allocation sketch for comparison, not a promotion packet. Every row remains blocked by `fill_coverage_below_0.90`.

- `TSLA` `b150__tsla__long_call__balanced_reward__exit_360__liq_baseline` weight `12.80%` min_net `$10413.765` min_test `$23910.1625` fill `0.6667` blockers `fill_coverage_below_0.90`
- `TSLA` `b150__tsla__long_call__wide_reward__exit_300__liq_tight` weight `12.20%` min_net `$9775.3675` min_test `$21775.2375` fill `0.6897` blockers `fill_coverage_below_0.90`
- `MSFT` `b150__msft__long_call__wide_reward__exit_210__liq_baseline` weight `13.89%` min_net `$26388.665` min_test `$5313.96` fill `0.7333` blockers `fill_coverage_below_0.90`
- `AMZN` `b150__amzn__long_call__tight_reward__exit_210__liq_baseline` weight `14.96%` min_net `$28268.085` min_test `$2439.931` fill `0.7895` blockers `fill_coverage_below_0.90`
- `AAPL` `b150__aapl__long_call__balanced_reward__exit_210__liq_baseline` weight `15.27%` min_net `$19272.609` min_test `$5542.945` fill `0.6897` blockers `fill_coverage_below_0.90`
- `MSFT` `b150__msft__long_call__balanced_reward__exit_210__liq_baseline` weight `11.11%` min_net `$28901.22` min_test `$1801.825` fill `0.7812` blockers `fill_coverage_below_0.90`
- `AAPL` `b150__aapl__long_call__tight_reward__exit_210__liq_tight` weight `9.73%` min_net `$16912.174` min_test `$6006.405` fill `0.6774` blockers `fill_coverage_below_0.90`
- `NVDA` `b150__nvda__long_call__tight_reward__exit_210__liq_baseline` weight `10.04%` min_net `$10900.35` min_test `$641.05` fill `0.6452` blockers `fill_coverage_below_0.90`

## Highest Research Leads

- `AAPL` `b150__aapl__long_call__wide_reward__exit_360__liq_tight` min_net `$26168.521` min_test `$25793.475` fill `0.3125-0.375` blockers `fill_coverage_below_0.90, option_trades_below_20`
- `AAPL` `b150__aapl__long_call__wide_reward__exit_360__liq_baseline` min_net `$24603.5225` min_test `$24364.915` fill `0.3125-0.375` blockers `fill_coverage_below_0.90, option_trades_below_20`
- `AAPL` `b150__aapl__long_call__balanced_reward__exit_360__liq_tight` min_net `$26045.08` min_test `$21455.595` fill `0.3529-0.4118` blockers `fill_coverage_below_0.90, option_trades_below_20`
- `AAPL` `b150__aapl__long_call__wide_reward__exit_300__liq_baseline` min_net `$20572.3225` min_test `$24433.275` fill `0.5-0.6` blockers `fill_coverage_below_0.90, option_trades_below_20`
- `QQQ` `b150__qqq__long_call__tight_reward__exit_360__liq_tight` min_net `$19239.4675` min_test `$19239.4675` fill `0.2222-0.2222` blockers `fill_coverage_below_0.90, option_trades_below_20`
- `QQQ` `b150__qqq__long_call__wide_reward__exit_360__liq_tight` min_net `$18225.01` min_test `$18225.01` fill `0.2353-0.2353` blockers `fill_coverage_below_0.90, option_trades_below_20`
- `QQQ` `b150__qqq__long_call__balanced_reward__exit_360__liq_tight` min_net `$18225.01` min_test `$18225.01` fill `0.2353-0.2353` blockers `fill_coverage_below_0.90, option_trades_below_20`
- `TSLA` `b150__tsla__long_call__balanced_reward__exit_360__liq_baseline` min_net `$10413.765` min_test `$23910.1625` fill `0.6667-0.7` blockers `fill_coverage_below_0.90`
- `MSFT` `b150__msft__long_call__wide_reward__exit_300__liq_baseline` min_net `$28815.32` min_test `$13254.075` fill `0.7083-0.7083` blockers `fill_coverage_below_0.90, option_trades_below_20`
- `TSLA` `b150__tsla__long_call__wide_reward__exit_360__liq_tight` min_net `$9992.161` min_test `$22761.9275` fill `0.6552-0.6897` blockers `fill_coverage_below_0.90, option_trades_below_20`
- `QQQ` `b150__qqq__long_call__tight_reward__exit_360__liq_baseline` min_net `$17018.4475` min_test `$17018.4475` fill `0.2632-0.2632` blockers `fill_coverage_below_0.90, option_trades_below_20`
- `TSLA` `b150__tsla__long_call__wide_reward__exit_300__liq_tight` min_net `$9775.3675` min_test `$21775.2375` fill `0.6897-0.7241` blockers `fill_coverage_below_0.90`

## Symbol Summary

- `AAPL` candidates `18` eligible `0` best_score `78061.726` best_min_fill `0.3125`
- `QQQ` candidates `18` eligible `0` best_score `56774.90875` best_min_fill `0.2222`
- `TSLA` candidates `21` eligible `0` best_score `52230.185` best_min_fill `0.6667`
- `MSFT` candidates `18` eligible `0` best_score `51710.095` best_min_fill `0.7083`
- `NVDA` candidates `18` eligible `0` best_score `42462.505` best_min_fill `0.3125`
- `META` candidates `18` eligible `0` best_score `33142.8225` best_min_fill `0.4545`
- `AMZN` candidates `18` eligible `0` best_score `30379.707` best_min_fill `0.7895`
- `SPY` candidates `18` eligible `0` best_score `25147.34` best_min_fill `0.1667`
- `IWM` candidates `18` eligible `0` best_score `12088.7275` best_min_fill `0.2105`
- `MU` candidates `18` eligible `0` best_score `10144.67` best_min_fill `0.8085`

## Interpretation

Phase40 and Phase41 fixed the historical contract-inventory/selected-contract foundation. Phase42 proves the remaining blocker is strategy exit execution: every candidate failed with `exit_bar_gap_or_exit_policy_mismatch` under the unchanged `0.90` fill gate.

The next safe research step is not more broad contract inventory repair. It is candidate-specific exit-policy redesign and a parallel stock/ETF fallback portfolio lane so daily PnL research is not dependent on sparse option exits.

## Hard Rules

Do not trade, arm a window, start a broker-facing session, modify live manifests, change risk policy, or relax the `0.90` fill gate.
