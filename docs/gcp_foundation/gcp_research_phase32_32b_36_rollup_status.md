# Phase32/32b/36 Wave Rollup Status

## State

- Status: `phase32_32b_36_wave_rollup_complete`
- Decision: `research_only_blocked`
- Source reports: `45`
- Candidates scanned: `640`
- Eligible for promotion review: `0`
- Research-only capital-plan rows: `8`
- Broker-facing: `false`
- Live manifest effect: `none`
- Risk policy effect: `none`

## Result

The completed Phase32, Phase32b, and Phase36 shard reports produced no governed-validation candidate. The positive-economics rows remain data-repair or strategy-redesign leads only.

Fill-failure map:

- `entry_bar_gap_or_entry_timing_mismatch`: `276`
- `exit_bar_gap_or_exit_policy_mismatch`: `339`
- `mixed_low_fill_gap`: `25`

Top data-repair leads remain concentrated in `UNH`, `AMD`, and `ORCL`; these are not promotable because fill is far below `0.90`.

## Artifacts

```text
gs://codexalpaca-control-us/research_results/top100_liquidity_research_20260426/rollups/phase32_32b_36_20260428204500/
```

## Next Safe Step

Continue Phase37 and Phase38. The key comparison is:

- Phase37: top-10 liquid names, ATM-only `0-7` DTE
- Phase38: top-10 liquid names, dense daily `0-7` DTE ATM +/- 5 strikes

If Phase38 materially improves fill, use dense liquid-contract universes as the default brute-force data foundation. If Phase38 still fails fill, redesign entry/exit timing and use stock/ETF fallback portfolios rather than relaxing the `0.90` gate.

## Guardrails

This rollup is research-only. It does not authorize trading, window arming, broker-facing sessions, live manifest changes, risk-policy changes, or fill-gate relaxation.
