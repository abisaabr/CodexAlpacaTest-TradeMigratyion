# Phase38 Dense Top10 Universe Handoff

## Operator Read

Phase38 is a research-only fill-rate diagnostic and candidate-discovery lane. It should be monitored alongside Phase37, not used for trading.

Current state at launch handoff: `RUNNING`, with `1` running and `9` pending tasks as of `2026-04-28T20:38:10.260460299Z`.

## Launch Inputs

- Batch job: `phase38-dense-top10-20260428203428`
- Phase ID: `phase38_dense_top10_universe_20260428203428`
- Runner source archive: `gs://codexalpaca-control-us/research_source/codexalpaca_runner_source_133a1a7f5cd1.zip`
- Runner commit: `133a1a7f5cd12eaeca7d36d1d907a695ea10c3a6`
- Worker script: `docs/gcp_foundation/phase38_dense_top10_universe_worker.sh`
- Batch config: `docs/gcp_foundation/phase38_dense_top10_universe_batch_job.yaml`

## Monitor

```powershell
gcloud batch jobs describe phase38-dense-top10-20260428203428 --project codexalpaca --location us-central1 --format=json
```

Artifacts land under:

```text
gs://codexalpaca-control-us/research_results/top100_liquidity_research_20260426/portfolio_event_driven_data/phase38_dense_top10_universe_20260428203428/
gs://codexalpaca-data-us/research_option_data/top100_liquidity_research_20260426/top100_phase38_<SYMBOL>_dense_atm5_options_20260302_20260423/
```

## Post-Completion Steps

1. Inspect each symbol's `dense_option_universe_packet.json`.
2. Inspect each symbol's downloader manifest and quality report.
3. Aggregate replay summaries across all `data_shards/<SYMBOL>/replay` folders.
4. Compare `fill_failure_counts` against Phase37 and Phase32b.
5. Only consider research-governed promotion review for candidates that keep `>=0.90` fill coverage across all profiles.

## Decision Rule

If Phase38 materially improves fill, the systematic brute-force pipeline should shift from sparse event-selected contracts to dense liquid-contract universes for top names. If Phase38 still fails fill, the next move is strategy/exit-policy redesign and stock/ETF fallback portfolio testing, not relaxation of the `0.90` gate.

## Guardrails

This packet does not authorize trading, window arming, broker-facing sessions, live manifest changes, risk-policy changes, or fill-gate relaxation.
