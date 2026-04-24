# GCP Institutional Researcher Buildout Handoff

## Current Read

- The project has enough existing strategy and paper/backtest surface to justify building a serious research plane now.
- Execution is still governed separately through `vm-execution-paper-01`.
- The research plane may run broad offline experiments, but it cannot mutate live strategy selection or risk policy.

## Target State

Build an institutional research factory that:

- inventories existing downloader, data, backtest, and paper-session assets
- stores raw, curated, and derived data in GCS
- normalizes backtest and paper evidence
- produces loser-learning tables
- produces strategy-family league tables
- runs ML-lite ranking for liquidity, slippage, regime, and loser similarity
- emits promotion recommendations that remain advisory until control-plane review

## Overnight Priorities

1. Inventory existing research assets.
2. Publish research manifests to GCS.
3. Normalize April 22 and April 23 paper-session evidence.
4. Backfill April 23 loser clusters.
5. Produce data-quality verdicts for the governed 11-name universe.
6. Refresh Friday scorecard and seed Monday scorecard.

## Research Scope

Allowed:

- broad backtests
- data downloads using existing non-broker-facing paths
- strategy-family experiments
- parameter sweeps
- liquidity and slippage modeling
- loser/winner clustering
- research-only universe exploration after quality gates

Not allowed:

- broker-facing session launch
- exclusive-window arm
- live manifest mutation
- risk-policy mutation
- automatic promotion
- new execution infrastructure

## GCS Targets

- `gs://codexalpaca-data-us/raw/`
- `gs://codexalpaca-data-us/curated/`
- `gs://codexalpaca-data-us/derived/`
- `gs://codexalpaca-control-us/research_manifests/`
- `gs://codexalpaca-control-us/research_scorecards/`

## Promotion Boundary

Research output can say:

- `prefer`
- `allow_cautious`
- `shadow`
- `hold`
- `quarantine_review`
- `kill_review`

Only the control plane can turn that into a manifest, strategy-selection, or risk-policy change.

## Next Safe Action

Run Phase 1 inventory and publish the first research asset manifest. Then run loser-learning and data-quality passes from existing artifacts before downloading any new broad data.

