# Phase42 Dense Download Replay Status

## State

- Phase ID: `phase42_dense_download_replay_20260428182000`
- Batch job: `phase42-dense-download-replay-20260428182000`
- Latest state: `RUNNING`
- Latest task counts: `9` succeeded / `1` running
- Location: `codexalpaca/us-central1`
- Tasks: `10`
- Parallelism: `4`
- Broker-facing: `false`
- Alpaca data/metadata used: `true`
- Trading effect: `none`
- Live manifest effect: `none`
- Risk policy effect: `none`

## Scope

Phase42 is the first repaired top-10 dense option data download and replay lane after the Phase40/Phase41 fill-foundation repair.

Symbols:

`SPY`, `NVDA`, `QQQ`, `AMZN`, `TSLA`, `MSFT`, `IWM`, `AAPL`, `META`, and `MU`.

It uses:

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

## Gate

Promotion review requires:

- fill coverage `>= 0.90`
- at least `20` option trades
- positive out-of-sample/test net PnL
- survival across cost/lag stress
- no live-manifest or risk-policy change without a governed promotion packet

## Interim Finding

Nine of ten shard portfolio reports are visible; `MSFT` remains running. The visible shards cover `AAPL`, `AMZN`, `IWM`, `META`, `MU`, `NVDA`, `QQQ`, `SPY`, and `TSLA`.

Across the nine visible shards:

- candidates scanned so far: `165`
- eligible for promotion review so far: `0`
- dominant blocker: `fill_coverage_below_0.90` (`165/165`)
- secondary blockers: `option_trades_below_20` (`113`), `test_net_pnl_not_above_0` (`79`), `min_net_pnl_not_positive` (`17`)
- dominant fill failure reason: `exit_bar_gap_or_exit_policy_mismatch`

The repaired dense data foundation is working, but the current strategy/exit designs still do not satisfy the promotion gate.

## Hard Rules

Do not trade, arm a window, start a broker-facing session, modify live manifests, change risk policy, or relax the `0.90` fill gate.
