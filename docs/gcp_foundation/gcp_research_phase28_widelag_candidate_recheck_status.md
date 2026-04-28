# Phase28 Wide-Lag Candidate Recheck Status

## State

- State: `succeeded`
- Batch job: `phase28-widelag-recheck-20260428110100`
- Batch location: `codexalpaca/us-central1`
- Phase id: `phase28_widelag_candidate_recheck_20260428110100`
- Broker-facing: `false`
- Live manifest effect: `none`
- Risk policy effect: `none`
- Exclusive-window effect: `none`

## Objective

Phase28 is a narrow, non-broker-facing diagnostic for three profitable but promotion-blocked candidates from the top100 campaign:

- `AAPL` `b150__aapl__long_call__wide_reward__exit_210__liq_tight`
- `NVDA` `b150__nvda__long_call__tight_reward__exit_300__liq_tight`
- `NVDA` `b150__nvda__long_call__tight_reward__exit_360__liq_tight`

The purpose is to decide whether these candidates can survive defensible wider entry/exit-lag and cost assumptions, or whether they should be quarantined as strategy-design or data-fill failures.

## Result

- Decision: `ready_for_governed_validation_review`
- Candidate count: `3`
- Eligible for review: `1`
- Review candidate: `NVDA` `b150__nvda__long_call__tight_reward__exit_300__liq_tight`
- Minimum net PnL: `$1593.1625`
- Median net PnL: `$3308.97`
- Minimum holdout/test net PnL: `$484.1825`
- Fill coverage: `0.9254-0.9701`
- Minimum option trades: `62`
- Worst drawdown: `$-4769.23`
- Positive net profiles: `6/6`
- Positive holdout/test profiles: `6/6`

Blocked candidates:

- `AAPL` `b150__aapl__long_call__wide_reward__exit_210__liq_tight`: blocked by `fill_coverage_below_0.90`.
- `NVDA` `b150__nvda__long_call__tight_reward__exit_360__liq_tight`: blocked by `test_net_pnl_not_above_0`.

## Gates

- Fill coverage must remain at least `0.90`.
- Minimum option trades must be at least `20`.
- Holdout/test net PnL must remain above `0`.
- Initial cash remains `$25,000`.
- Portfolio constraints remain `max_positions=3`, `max_strategies_per_symbol=2`, and `max_symbol_weight=0.25`.

## Artifact Roots

- Launch root: `gs://codexalpaca-control-us/research_results/top100_liquidity_research_20260426/portfolio_event_driven_data/phase28_widelag_candidate_recheck_20260428110100/launch/`
- Result root: `gs://codexalpaca-control-us/research_results/top100_liquidity_research_20260426/portfolio_event_driven_data/phase28_widelag_candidate_recheck_20260428110100/`

## Operator Guardrails

Do not trade, arm an exclusive window, start a broker-facing paper/live session, modify live manifests, change risk policy, or relax the `0.90` fill gate from this packet.
