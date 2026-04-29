# GCP Research Option Fill Ladder 20260429 Repair Status

## Current Read

- Status: `repair_launched`
- Campaign: `option_fill_ladder_20260429`
- Mode: `research_only_option_fill_ladder_quota_repair`
- Broker-facing: `false`
- Trading effect: `none`
- Live manifest effect: `none`
- Risk policy effect: `none`

## Why Repair Was Needed

The first launch was code-clean, but the combined jobs exceeded the `us-central1` `SSD_TOTAL_GB` quota because multiple jobs requested `pd-balanced` boot disks concurrently. The quota limit is `500GB`.

The mitigation is to preserve completed outputs, cancel the quota-constrained jobs, and relaunch only incomplete symbol-stage work on `pd-standard` with smaller boot disks and bounded parallelism.

## Preserved Outputs

- `7d_atm`: `10` packets complete. `9/10` pass the `0.90` fill gate. `AMZN` is blocked at `0.80` coverage.
- `30d_atm`: `4` packets completed before repair: `AAPL`, `AMZN`, `META`, `TSLA`.
- `30d_5x5`: `9` packets completed before repair: `AAPL`, `AMD`, `AMZN`, `INTC`, `IWM`, `META`, `MSFT`, `NVDA`, `SPY`.

## Repair Jobs

- `fill-ladder-repair-30d-atm-20260429015546`: `SCHEDULED`, stage `30d_atm`, symbols `SPY`, `IWM`, `NVDA`, `AMD`, `INTC`, `MSFT`, `6` tasks, parallelism `3`, `pd-standard`, `30GB`.
- `fill-ladder-repair-30d-5x5-20260429015546`: `SCHEDULED`, stage `30d_5x5`, symbol `TSLA`, `1` task, parallelism `1`, `pd-standard`, `50GB`.
- `fill-ladder-repair-365d-5x5-20260429015546`: `SCHEDULED`, stage `365d_5x5`, all `10` symbols, `10` tasks, parallelism `3`, `pd-standard`, `100GB`.

## Durable Roots

- Control results: `gs://codexalpaca-control-us/research_results/option_fill_ladder_20260429/`
- Repair Batch configs: `gs://codexalpaca-control-us/research_results/option_fill_ladder_20260429/gcp_batch_repair/`
- Current aggregate summary: `gs://codexalpaca-control-us/research_results/option_fill_ladder_20260429/summary/fill_ladder_aggregate_summary.md`

## Guardrails

- Research-only data download and fill diagnostic.
- Do not trade from this packet.
- Do not arm an execution window from this packet.
- Do not start a broker-facing paper or live session from this packet.
- Do not modify live manifests, strategy selection, or risk policy from this packet.
- Do not relax the `0.90` fill gate for promotion review.

## Next Safe Step

Monitor the repair jobs to completion, refresh the aggregate fill matrix, then replay strategies only on symbol-stage datasets that pass the `0.90` fill gate.
