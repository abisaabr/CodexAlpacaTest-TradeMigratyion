# Phase32b Unexplored Top100 Tranche2 Status

## State

- Phase ID: `phase32b_unexplored_top100_tranche2_20260428122500`
- Batch job: `phase32b-unexplored-top100-tranche2-20260428122500`
- Latest state: `RUNNING`
- Latest task counts: `3` succeeded / `2` running / `10` pending
- Location: `codexalpaca/us-central1`
- Tasks: `15`
- Parallelism: `3`
- Broker-facing: `false`
- Trading effect: `none`
- Live manifest effect: `none`
- Risk policy effect: `none`

## Scope

Phase32b expands candidate-rich unexplored top100 coverage across:

`NOW`, `BKNG`, `MA`, `CSCO`, `JNJ`, `CVX`, `WMT`, `HOOD`, `KRE`, `CAT`, `GS`, `IBM`, `SLV`, `XLK`, and `BA`.

It was launched after direct inspection showed the Phase32 `AMD` shard had completed selected-contract construction and Alpaca historical option-data download with zero failed chunks.

## Gate

No Phase32b output can be promoted directly. A portfolio-level aggregation packet is required after shards finish cleanly, and the `0.90` fill-coverage gate remains mandatory.

## Hard Rules

Do not trade, arm a window, start a broker-facing session, modify live manifests, change risk policy, or relax the `0.90` fill gate.
