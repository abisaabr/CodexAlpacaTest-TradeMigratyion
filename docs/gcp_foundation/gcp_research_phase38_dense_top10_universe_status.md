# Phase38 Dense Top10 Universe Status

## State

- Phase ID: `phase38_dense_top10_universe_20260428203428`
- Batch job: `phase38-dense-top10-20260428203428`
- Latest state: `DELETED`
- Latest task counts at stop request: `6` succeeded / `1` running / `3` pending
- Created: `2026-04-28T20:37:06.446050181Z`
- Updated: `2026-04-28T21:30:38Z`
- Location: `codexalpaca/us-central1`
- Tasks: `10`
- Parallelism: `2`
- Broker-facing: `false`
- Trading effect: `none`
- Live manifest effect: `none`
- Risk policy effect: `none`

## Scope

Phase38 is the direct fill-rate repair lane for the top liquid names:

`SPY`, `NVDA`, `QQQ`, `AMZN`, `TSLA`, `MSFT`, `IWM`, `AAPL`, `META`, and `MU`.

It uses runner commit `133a1a7f5cd12eaeca7d36d1d907a695ea10c3a6`, which added:

- generic dense option-universe construction equivalent to the proven QQQ cleanroom download pattern
- candidate-level fill-failure classification
- portfolio reports that separate data-repair candidates from strategy-redesign candidates

Each symbol builds a dense daily `0-7` DTE, ATM +/- 5 strike universe from `2026-03-02` through `2026-04-23`, downloads bars/trades for those selected contracts, then replays the symbol's strategy queue across three cost/lag profiles.

## Purpose

The test separates three failure modes:

- `selected_contract_universe_gap`: sparse/event-selected contract universe is too thin
- `entry_bar_gap_or_entry_timing_mismatch`: data exists, but entry timing is not executable enough
- `exit_bar_gap_or_exit_policy_mismatch`: strategy exits are not aligned with liquid prints

The `0.90` fill gate remains mandatory. Phase38 can open a research-only governed-validation review queue, but it cannot modify live manifests, strategy selection, or risk policy.

## Interim Finding

The first visible dense shards (`MSFT`, `NVDA`, and `QQQ`) remain blocked by `selected_contract_universe_gap`. The dense-universe packets selected only `4` trade dates, not the full `2026-03-02` to `2026-04-23` window. Downloads for the selected contracts completed, so the next fix is not to relax promotion gates; it is to instrument and repair dense-universe reference-date coverage before judging strategy economics.

## Disposition

Phase38 was superseded by Phase39, Phase40, and Phase41. Phase39 proved the blocker was incomplete option contract inventory, Phase40 repaired inventory with active+inactive contract discovery, and Phase41 passed dense selected-contract coverage. Phase38 was deleted to free Batch capacity for Phase42.

## Gate

Promotion review requires:

- fill coverage `>= 0.90`
- at least `20` option trades
- positive out-of-sample/test net PnL
- survival across the full cost/lag stack

## Hard Rules

Do not trade, arm a window, start a broker-facing session, modify live manifests, change risk policy, or relax the `0.90` fill gate.
