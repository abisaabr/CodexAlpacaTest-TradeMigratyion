# Research Fill Experiment Comparison Status

## State

- Status: `research_fill_experiment_comparison_complete`
- Decision: `continue_dense_or_broader_contract_universe_repair`
- Baseline lane: `event_sparse`
- Compared lanes: `event_sparse`, `top10_atm`
- Broker-facing: `false`
- Live manifest effect: `none`
- Risk policy effect: `none`

## Result

The completed event-sparse rollup still has better fill than the ATM-only top-10 lane, even though neither lane is promotable.

- `event_sparse`: `640` candidates, `0` eligible, `95` positive-economics candidates, max min-fill `0.747`, median min-fill `0.5294`.
- `top10_atm`: `183` candidates, `0` eligible, `24` positive-economics candidates, max min-fill `0.1111`, median min-fill `0.0676`.
- Aggregate blockers include `276` entry timing gaps, `339` exit timing gaps, `25` mixed low-fill gaps, and `183` selected-contract universe gaps.

Conclusion: the next institutional fix is not to relax the `0.90` gate. It is to repair and instrument the contract-universe/data-foundation path, then rerun exhaustive tests only after selected trade-date coverage is verifiable.

## Artifacts

```text
gs://codexalpaca-control-us/research_results/top100_liquidity_research_20260426/rollups/fill_experiment_comparison_20260428213000/
```

## Guardrails

This comparison is research-only. It does not authorize trading, window arming, broker-facing sessions, live manifest changes, risk-policy changes, or fill-gate relaxation.
