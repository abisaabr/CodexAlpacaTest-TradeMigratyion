# GCP Research Overnight 365D Bruteforce 20260429 Replay Fix Status

## Current Read

- Status: `gcs_downloader_fix_replays_running`
- Mode: `research_only_overnight_365d_bruteforce`
- Broker-facing: `false`
- Trading effect: `none`
- Live manifest effect: `none`
- Risk policy effect: `none`

## Incident

- Failed jobs: `overnight-top10-365d-replay-20260429023003`, `overnight-top10-365d-replay-fix-20260429023400`, `overnight-top10-365d-replay-fix2-20260429024200`, `overnight-top10-365d-replay-fix3-20260429025100`
- Failure class: `research_loader_partition_column_loss`
- Symptom: top-10 replay tasks failed with `KeyError: 'symbol'`
- Root cause: the replay loader first lost `key=value` partition columns from parquet paths. After that was fixed, single-symbol GCS download shards still exposed stock-bar frames without a stable symbol column. The final replay blocker was the embedded Batch GCS helper stripping the trailing slash from directory prefixes; relative object paths began with `/`, so downloads were written outside the intended input tree and replays ran against empty local inputs
- Operational effect: diagnosis-only; no trading, broker-facing, manifest, or risk-policy effect

## Fix

- Runner branch: `codex/qqq-paper-portfolio`
- Runner commits: `de58f1a`, `3b86443`, `03bfc25`
- Active runner commit: `03bfc25`
- Changes: restore parquet partition columns, synthesize the stock-bar symbol from `--symbol-filter`, and tolerate symbolless single-symbol stock bars in the stock-trade path
- Source archive: `gs://codexalpaca-control-us/research_source/codexalpaca_runner_source_03bfc25.zip`
- Validation: targeted runner tests passed, `11 passed`

## Replacement Replay

- Job: `overnight-top10-365d-replay-fix4-20260429030000`
- Region: `us-central1`
- State at fix packet: `RUNNING`
- Dataset source: `option_fill_ladder_20260429/365d_5x5`
- Output root: `gs://codexalpaca-control-us/research_results/overnight_365d_bruteforce_20260429/top10_replay_gcsfix_03bfc25/`

Profiles:

- `liq_lag10_slip10_fee065`
- `liq_lag30_slip25_fee100`
- `nearest_lag10_slip10_fee065`

## Parallel Lane

- Next-10 data job: `overnight-next10-365d-data-20260429023003`
- State: `SUCCEEDED`
- Symbols: `QQQ`, `MU`, `AVGO`, `GOOGL`, `NFLX`, `TSM`, `PLTR`, `XLE`, `ORCL`, `XOM`
- Fill coverage: `10/10` passed, min `0.947224`, average `0.9829024`

## Next-10 Replay

- Job: `overnight-next10-365d-replay-fix2-20260429030000`
- Region: `us-central1`
- State at fix packet: `RUNNING`
- Dataset source: `option_fill_ladder_next10_20260429/365d_5x5`
- Output root: `gs://codexalpaca-control-us/research_results/overnight_365d_bruteforce_20260429/next10_replay_gcsfix_03bfc25/`

## Invalidated Output

- Root: `gs://codexalpaca-control-us/research_results/overnight_365d_bruteforce_20260429/top10_replay_fixed_03bfc25/`
- Reason: replay completed against empty local stock/option inputs and all candidates showed `no_source_stock_trades`

## Guardrails

- Research-only jobs.
- Do not trade from raw research output.
- Do not arm an execution window from this packet.
- Do not start broker-facing paper or live sessions from this packet.
- Do not modify live manifests, strategy selection, or risk policy from this packet.
- Do not relax the `0.90` fill gate for promotion review.
- Tomorrow's paper-session use requires a separate operator/control-plane decision after promotion-review packets are clean.

## Next Safe Step

Monitor the GCS-helper-fixed top-10 and next-10 replay jobs. If either succeeds, aggregate portfolio reports into promotion-review packets and continue until five or more research-governed candidates are available or a new blocker is proven.
