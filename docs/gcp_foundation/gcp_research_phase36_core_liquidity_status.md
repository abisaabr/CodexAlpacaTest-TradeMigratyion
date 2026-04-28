# Phase36 Core Liquidity Status

## State

- Phase ID: `phase36_core_liquidity_tranche_20260428180637`
- Batch job: `phase36-core-liq-20260428180637`
- Latest state: `RUNNING`
- Latest task counts: `4` running / `11` pending
- Location: `codexalpaca/us-central1`
- Tasks: `15`
- Parallelism: `4`
- Broker-facing: `false`
- Trading effect: `none`
- Live manifest effect: `none`
- Risk policy effect: `none`

## Scope

Phase36 runs a research-only core-liquidity tranche across:

`SPY`, `QQQ`, `IWM`, `TSLA`, `TSM`, `EFA`, `EEM`, `XLF`, `XLV`, `EWZ`, `WFC`, `GLD`, `NKE`, `XLP`, and `XBI`.

It excludes active Phase32b symbols and the quarantined severe-loser/replay-unchanged clusters. The objective is to find fill-feasible candidates that can satisfy the mandatory `0.90` fill gate, not to promote from this packet.

## Gate

No Phase36 output can be promoted directly. Completed shards must enter portfolio-level aggregation and promotion review. The `0.90` fill-coverage gate remains mandatory.

## Hard Rules

Do not trade, arm a window, start a broker-facing session, modify live manifests, change risk policy, or relax the `0.90` fill gate.
