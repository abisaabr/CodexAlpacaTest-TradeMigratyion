# Phase37 Top10 ATM Rollup Status

## State

- Status: `phase37_top10_atm_rollup_complete`
- Decision: `research_only_blocked`
- Source reports: `10`
- Candidates scanned: `183`
- Eligible for promotion review: `0`
- Research-only capital-plan rows: `0`
- Broker-facing: `false`
- Live manifest effect: `none`
- Risk policy effect: `none`

## Result

The top-10 liquid-underlying ATM-only `0-7` DTE lane did not solve fill. All `183` candidates were blocked by `selected_contract_universe_gap`.

- Maximum minimum-fill coverage: `0.1111`
- Median minimum-fill coverage: `0.0676`
- Fill-failure map: `selected_contract_universe_gap=183`

This is a negative but useful result: ATM-only weekly contracts are too narrow for the current strategy repo and should not be promoted or reused as the primary repair lane.

## Artifacts

```text
gs://codexalpaca-control-us/research_results/top100_liquidity_research_20260426/rollups/phase37_top10_atm_20260428212500/
```

## Next Safe Step

Continue dense/broader contract-universe repair, but require coverage diagnostics so selected trade-date coverage is visible before expensive replay.

## Guardrails

This rollup is research-only. It does not authorize trading, window arming, broker-facing sessions, live manifest changes, risk-policy changes, or fill-gate relaxation.
