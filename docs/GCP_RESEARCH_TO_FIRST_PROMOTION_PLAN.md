# GCP Research To First Promotion Plan

This packet defines the multi-phase, multi-agent plan to build the project research arm from current inventory into the first governed research promotion.

The research plane is not session-bound. It may run continuously across nights and weekends. The execution plane remains single-writer, broker-governed, and evidence-gated.

## Promotion Definition

The first near-term promotion is not a live-trading promotion.

The first acceptable promotion is:

- from: `research_only`
- to: `governed_validation_candidate`
- meaning: a strategy or strategy-family variant has enough reproducible research evidence to be reviewed for controlled paper validation
- not meaning: the live manifest changes
- not meaning: risk policy changes
- not meaning: the strategy is allowed into the broker-facing runner without control-plane review

Broker-facing promotion still requires the strategy promotion policy:

- trusted broker-audited paper sessions
- clean evidence contract
- teaching gate allowing automatic learning
- broker/local economics inside tolerance
- no unresolved runner or broker anomalies

## Current State

Current research assets:

- historical dataset builder exists: `scripts/build_historical_dataset.py`
- sample backtest runner exists: `scripts/run_sample_backtest.py`
- backtest config exists: `config/backtest.example.yaml`
- sample backtest reports exist
- multi-ticker paper strategy manifest exists
- April 21, April 22, and April 23 runtime sessions exist
- April 23 evidence is finalized but `review_required`
- April 24 quality scorecard exists and is advisory
- research asset inventory is `ready_for_research_bootstrap`

Current bottlenecks:

- no formal experiment registry yet
- no normalized strategy-family result table yet
- no brute-force orchestration lane yet
- no first research promotion packet yet
- no hard split yet between research hits, paper candidates, and executable manifest changes

## Target State

The first institutional research loop is complete when:

- research data inventory is published to GCS
- baseline data-quality verdict exists for the governed universe
- existing backtest and paper-session artifacts are normalized
- at least one brute-force research wave has completed
- results include train/test or walk-forward separation
- results include costs, slippage, drawdown, and loser-profile attribution
- candidates are ranked with anti-overfit checks
- one candidate is promoted to `governed_validation_candidate`
- the promotion is recorded in GitHub and GCS as advisory, not executable

## Multi-Agent Operating Model

### Agent A - Research Program Steward

Owns the overall research roadmap and keeps research separated from execution.

Responsibilities:

- maintain this packet
- define experiment waves
- assign bounded scopes to other agents
- reject research that cannot be reproduced
- confirm no research output mutates live execution

Primary outputs:

- research roadmap
- weekly research priorities
- first promotion packet

### Agent B - Data Foundation Engineer

Owns raw, curated, and derived GCS data.

Responsibilities:

- inventory downloader and data assets
- run bounded downloader jobs when safe
- partition data by date, symbol, dataset, and source
- produce data-quality verdicts
- publish data manifests

Primary outputs:

- `research_asset_inventory`
- `data_quality_report`
- raw and curated GCS manifests

### Agent C - Strategy Librarian

Owns strategy metadata and experiment identity.

Responsibilities:

- define strategy ids
- map strategy families
- define parameter-grid metadata
- prevent duplicate unnamed variants
- tombstone failed strategies

Primary outputs:

- strategy registry
- family registry
- experiment registry schema
- candidate metadata packet

### Agent D - Backtest Factory Engineer

Owns repeatable backtest execution.

Responsibilities:

- run sample backtest baseline
- extend backtest configs into parameter grids
- run brute-force sweeps on GCP or local lanes
- write compact result summaries
- store raw backtest exhaust in GCS

Primary outputs:

- backtest wave manifests
- brute-force result tables
- train/test summary tables

### Agent E - Statistical Validation Analyst

Owns anti-overfit and robustness checks.

Responsibilities:

- train/test split checks
- walk-forward checks
- parameter stability checks
- one-day and one-symbol concentration checks
- slippage and fee stress checks
- drawdown and tail-loss checks

Primary outputs:

- robustness report
- anti-overfit verdict
- risk-adjusted ranking

### Agent F - Loser-Learning Analyst

Owns failure classification.

Responsibilities:

- classify losing backtest and paper trades
- compare losers against winners
- flag repeated structural defects
- map loser similarity penalties

Primary outputs:

- loser-cluster table
- loser-similarity feature table
- quarantine recommendations

### Agent G - Promotion Steward

Owns the first research promotion decision.

Responsibilities:

- enforce promotion thresholds
- verify required evidence and research artifacts
- write promote/hold/kill/quarantine recommendation
- block candidates with contaminated evidence

Primary outputs:

- first promotion packet
- promotion decision log
- next paper-validation checklist

### Agent H - Cloud Cost And Reliability Steward

Owns GCP cost, job hygiene, and durable publication.

Responsibilities:

- keep GCS object layout sane
- prevent runaway brute-force costs
- summarize job cost and runtime
- verify GCS mirrors
- prefer resumable batches over one-off local scratch

Primary outputs:

- cost note
- job manifest
- GCS mirror status

## Data And Artifact Layout

### GCS Data Buckets

Use:

- `gs://codexalpaca-data-us/raw/`
- `gs://codexalpaca-data-us/curated/`
- `gs://codexalpaca-data-us/derived/`

### GCS Control Buckets

Use:

- `gs://codexalpaca-control-us/research_manifests/`
- `gs://codexalpaca-control-us/research_results/`
- `gs://codexalpaca-control-us/research_scorecards/`
- `gs://codexalpaca-control-us/strategy_registry/`
- `gs://codexalpaca-control-us/promotion_packets/`

### GitHub

Use GitHub for:

- schemas
- compact registries
- promotion packets
- policy
- generator code
- reproducible configs

Do not commit:

- raw market data
- massive brute-force result exhaust
- vendor/API response dumps
- transient notebooks

## Experiment Schema

Every brute-force wave must emit:

- `experiment_id`
- `experiment_family`
- `hypothesis`
- `created_at`
- `code_ref`
- `data_ref`
- `universe`
- `strategy_family`
- `parameter_grid`
- `train_window`
- `test_window`
- `cost_model`
- `slippage_model`
- `job_runtime`
- `gcs_artifact_prefix`
- `status`
- `owner_agent`

## Result Schema

Every candidate result must include:

- `candidate_id`
- `experiment_id`
- `strategy_id`
- `family_id`
- `symbol_scope`
- `structure_class`
- `timing_profile`
- `parameter_set`
- `train_trade_count`
- `test_trade_count`
- `train_net_pnl`
- `test_net_pnl`
- `test_profit_factor`
- `test_win_rate`
- `max_drawdown`
- `tail_loss`
- `avg_win`
- `avg_loss`
- `slippage_stress_pnl`
- `fee_stress_pnl`
- `one_day_concentration_pct`
- `one_symbol_concentration_pct`
- `loser_cluster_flags`
- `anti_overfit_status`
- `research_recommendation`

## Phase Plan

### Phase 0 - Safety And Separation

Goal:

- guarantee research cannot mutate execution.

Actions:

- confirm control-plane packets are current
- confirm no exclusive window is armed by research
- define research output states distinct from execution states
- preserve live manifest and risk policy

Done when:

- GitHub and GCS have current research buildout, overnight lane, and promotion-plan packets
- automation prompt forbids broker-facing actions

### Phase 1 - Research Asset Inventory

Goal:

- know what we already have.

Actions:

- run the research asset inventory builder
- publish inventory to GCS
- inventory scripts, configs, reports, runtime sessions, scorecards, and backtest artifacts

Done when:

- inventory status is `ready_for_research_bootstrap`
- GCS has the inventory packet

### Phase 2 - Strategy Registry Bootstrap

Goal:

- create the first strategy/family metadata registry.

Actions:

- parse existing live manifest and config files
- extract strategy ids, family ids, structure classes, symbols, timing profiles, and promotion state
- mark all variants as research-derived, governed, live, shadow, held, or quarantined

Done when:

- `strategy_registry_bootstrap.json` exists
- duplicate or anonymous strategy variants are listed
- no registry output mutates the live manifest

### Phase 3 - Data Quality Baseline

Goal:

- determine which historical data can support brute-force research.

Actions:

- inspect local and GCS data coverage
- run underlying-bar quality checks for the governed 11-name universe
- inspect option snapshot availability
- classify each symbol as `ok`, `review_required`, or `missing`

Done when:

- `research_data_quality_2026-04-24.json` exists
- missing data worklist is explicit

### Phase 4 - Evidence Normalization

Goal:

- make paper sessions and backtests comparable.

Actions:

- normalize April 21-23 paper sessions
- normalize completed trades
- normalize strategy performance
- attach evidence contract and teaching gate status
- attach risk incident and broker/local economics status

Done when:

- `paper_session_learning_table` exists
- review-required sessions are not counted as trusted evidence

### Phase 5 - First Brute-Force Wave

Goal:

- run a broad but bounded search for research hits.

Initial waves:

- `wave_1_index_defined_risk_opening`: `QQQ`, `SPY`, `IWM`
- `wave_2_qqq_choppy_premium`: `QQQ`
- `wave_3_single_leg_trend_filter_repair`: `NVDA`, `AMZN`, `PLTR`, `IWM`, `SPY`
- `wave_4_regime_diversifiers`: `GLD`, `SLV`, `XLE`

Parameter dimensions:

- entry minute
- daypart
- DTE
- delta target
- spread width ceiling
- profit target
- stop loss
- max hold time
- regime filter
- liquidity filter
- loser-similarity filter

Done when:

- each wave writes experiment manifests and compact result tables
- at least one wave completes train/test or walk-forward validation

### Phase 6 - Anti-Overfit And Robustness Gate

Goal:

- kill false positives before they become paper candidates.

Checks:

- out-of-sample profitability
- trade-count minimum
- no single-day dependence
- no single-symbol dependence unless explicitly symbol-specific
- slippage and fee stress survival
- drawdown limit
- stable parameter neighborhood
- loser-class explainability

Done when:

- candidates are ranked as `discard`, `investigate`, `shadow`, or `promotion_review`

### Phase 7 - First Promotion Packet

Goal:

- produce one controlled research promotion.

First promotion criteria:

- status can only move to `governed_validation_candidate`
- not broker-facing yet
- must include data lineage
- must include experiment id
- must include train/test results
- must include slippage and fee stress
- must include loser analysis
- must include risk notes
- must include exact runner implementation gap, if any

Done when:

- `first_research_promotion_packet.json` exists
- `first_research_promotion_packet.md` exists
- promotion decision is either `promote_to_governed_validation_candidate` or `hold`

### Phase 8 - Paper Validation Readiness

Goal:

- prepare the promoted research candidate for future controlled paper validation.

Actions:

- identify whether runner code already supports the candidate
- identify manifest changes that would be required later
- define evidence needed for paper validation
- do not apply those changes automatically

Done when:

- paper validation checklist exists
- execution-plane work is explicitly separated from research promotion

## First Promotion Bar

A candidate may receive the first research promotion only if:

- train and test windows are both positive after costs, or test window is positive and train is not curve-fit dependent
- profit factor is at least `1.15` for directional strategies or `1.20` for complex structures
- max drawdown is inside family budget
- slippage-stressed PnL remains non-negative
- no single day contributes more than `35%` of test PnL
- no unresolved data-quality issue contaminates the result
- loser taxonomy has no repeated structural defect
- strategy metadata is complete

If no candidate passes:

- the correct result is `hold`, not forced promotion.

## Compute Policy

Use GCP aggressively for:

- parallel backtests
- parameter sweeps
- feature generation
- result aggregation
- data-quality checks
- loser/winner clustering

Do not use GCP to:

- run parallel broker-facing traders
- bypass the exclusive-window lifecycle
- write live manifests
- mutate risk policy

## Immediate Work Queue

1. Build strategy registry bootstrap from current configs.
2. Build data-quality baseline for the governed universe.
3. Normalize April 21-23 paper-session evidence.
4. Define experiment/result schemas in code.
5. Run sample backtest baseline and publish its result as the first research run manifest.
6. Run first brute-force wave on `QQQ`, `SPY`, and `IWM` defined-risk/opening-window ideas.
7. Rank candidates and produce the first promotion packet.

