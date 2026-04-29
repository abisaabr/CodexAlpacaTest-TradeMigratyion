# GCP Research Overnight 365D Bruteforce 20260429 Replay Fix Status

## Current Read

- Status: `second_replay_fix_launched`
- Mode: `research_only_overnight_365d_bruteforce`
- Broker-facing: `false`
- Trading effect: `none`
- Live manifest effect: `none`
- Risk policy effect: `none`

## Incident

- Failed jobs: `overnight-top10-365d-replay-20260429023003`, `overnight-top10-365d-replay-fix-20260429023400`
- Failure class: `research_loader_partition_column_loss`
- Symptom: top-10 replay tasks failed with `KeyError: 'symbol'`
- Root cause: the replay loader first lost `key=value` partition columns from parquet paths. After that was fixed, single-symbol GCS download shards still lacked a `symbol=...` path segment, so stock bars required a safe single-symbol fallback from `--symbol-filter`
- Operational effect: diagnosis-only; no trading, broker-facing, manifest, or risk-policy effect

## Fix

- Runner branch: `codex/qqq-paper-portfolio`
- Runner commits: `de58f1a`, `3b86443`
- Active runner commit: `3b86443`
- Changes: restore parquet partition columns, then synthesize the stock-bar symbol from `--symbol-filter` for single-symbol replay shards
- Source archive: `gs://codexalpaca-control-us/research_source/codexalpaca_runner_source_3b86443.zip`
- Validation: targeted runner tests passed, `10 passed`

## Replacement Replay

- Job: `overnight-top10-365d-replay-fix2-20260429024200`
- Region: `us-central1`
- State at fix packet: `SCHEDULED`
- Dataset source: `option_fill_ladder_20260429/365d_5x5`
- Output root: `gs://codexalpaca-control-us/research_results/overnight_365d_bruteforce_20260429/top10_replay_fixed_3b86443/`

Profiles:

- `liq_lag10_slip10_fee065`
- `liq_lag30_slip25_fee100`
- `nearest_lag10_slip10_fee065`

## Parallel Lane

- Next-10 data job: `overnight-next10-365d-data-20260429023003`
- State at fix packet: `RUNNING`
- Symbols: `QQQ`, `MU`, `AVGO`, `GOOGL`, `NFLX`, `TSM`, `PLTR`, `XLE`, `ORCL`, `XOM`
- Progress at fix packet: `6` tasks succeeded, `3` running

## Guardrails

- Research-only jobs.
- Do not trade from raw research output.
- Do not arm an execution window from this packet.
- Do not start broker-facing paper or live sessions from this packet.
- Do not modify live manifests, strategy selection, or risk policy from this packet.
- Do not relax the `0.90` fill gate for promotion review.
- Tomorrow's paper-session use requires a separate operator/control-plane decision after promotion-review packets are clean.

## Next Safe Step

Monitor the second fixed top-10 replay and next-10 data jobs. If the fixed replay succeeds, aggregate portfolio reports into a promotion-review packet. If next-10 data succeeds, aggregate fill coverage and launch the next-10 replay for fill-gate-passing symbols.
