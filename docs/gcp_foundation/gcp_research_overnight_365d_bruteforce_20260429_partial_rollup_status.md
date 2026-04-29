# Overnight 365d Bruteforce Partial Rollup Status

Generated: 2026-04-29T18:10:45Z

Campaign: `overnight_365d_bruteforce_20260429`

Mode: research-only. No broker-facing session was started, no trading was started, and no live manifest, strategy selection, or risk policy was changed.

## Current Replay State

Valid replay roots:

- `gs://codexalpaca-control-us/research_results/overnight_365d_bruteforce_20260429/top10_replay_gcsfix_03bfc25/`
- `gs://codexalpaca-control-us/research_results/overnight_365d_bruteforce_20260429/next10_replay_gcsfix_03bfc25/`

Invalidated replay root:

- `gs://codexalpaca-control-us/research_results/overnight_365d_bruteforce_20260429/top10_replay_fixed_03bfc25/`

Reason: the embedded GCS downloader wrote inputs outside the intended local tree, yielding `no_source_stock_trades`. Do not use that root for promotion.

Top-10 job `overnight-top10-365d-replay-fix4-20260429030000` is still running:

- Succeeded: `IWM`, `NVDA`
- Running: `AMD`, `AMZN`, `MSFT`
- Pending: `AAPL`, `META`, `TSLA`, `INTC`
- Failed: `SPY`

SPY failed because the task exceeded the Batch maximum runtime and exited with code `50005`.

Repair launched:

- Job: `overnight-spy-365d-replay-rerun-20260429181000`
- Region: `us-central1`
- State at launch: `QUEUED`
- Scope: SPY only, research-only, same queue and same strategy/risk gates, max runtime raised to `86400s`
- Output root: `gs://codexalpaca-control-us/research_results/overnight_365d_bruteforce_20260429/top10_replay_gcsfix_spy_rerun_03bfc25_20260429T1810Z/`

Next-10 job `overnight-next10-365d-replay-fix2-20260429030000` is still running:

- Succeeded: `QQQ`, `MU`, `AVGO`, `GOOGL`
- Running: `NFLX`, `TSM`, `PLTR`, `ORCL`
- Pending: `XLE`, `XOM`
- Failed: none

## Partial Rollup

Partial rollup was built from 6 valid completed reports and mirrored to:

`gs://codexalpaca-control-us/research_results/overnight_365d_bruteforce_20260429/partial_wave_rollup_gcsfix_03bfc25_20260429T1806Z/wave_rollup/`

Source symbols:

- `AVGO`
- `GOOGL`
- `IWM`
- `MU`
- `NVDA`
- `QQQ`

Result:

- Candidates reviewed: 216
- Eligible for promotion review: 0
- Decision: `research_only_blocked`
- Dominant blocker: `fill_coverage_below_0.90`

Top blocked research leads:

- `b150__googl__long_call__balanced_reward__exit_210__liq_baseline`: min net PnL 19641.9975, min test net PnL 11389.78, min fill coverage 0.3359.
- `b150__googl__long_call__tight_reward__exit_210__liq_tight`: min net PnL 14591.376, min test net PnL 12941.824, min fill coverage 0.3780.
- `b150__iwm__long_put__wide_reward__exit_360__liq_tight`: min net PnL 9677.6475, min test net PnL 8178.935, min fill coverage 0.0753.

## Next Safe Step

Continue monitoring the valid replay tasks. Diagnose and relaunch the failed SPY research-only shard with a runtime-aware profile split if needed. Aggregate the full valid report set when additional reports land. Do not relax the `0.90` fill gate.
