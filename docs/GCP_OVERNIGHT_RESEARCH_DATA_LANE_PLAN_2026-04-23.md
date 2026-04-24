# GCP Overnight Research Data Lane Plan - 2026-04-23

This packet defines the overnight non-broker-facing research lane for the April 24, 2026 bounded sanctioned VM paper session.

The goal is to use existing runner, downloader, backtest, paper-session, GCP, and Alpaca-derived evidence assets without contaminating the execution plane. The output should improve Friday and Monday selection quality, loser learning, and promotion discipline. It must not arm the exclusive execution window, start trading, widen the temporary parallel-runtime exception, or mutate live strategy or risk policy.

## Scope

Run overnight research work only inside these boundaries:

- governed universe: `QQQ`, `SPY`, `IWM`, `NVDA`, `MSFT`, `AMZN`, `TSLA`, `PLTR`, `XLE`, `GLD`, `SLV`
- data types: underlying bars, bounded option snapshots, execution-linked context, derived quality features, loser-learning tables
- storage: GCS for durable research artifacts and local runtime for temporary derived packets
- execution: no broker-facing session, no live manifest mutation, no risk-policy mutation

## Agent Topology

### Agent A - Control-Plane Sentry

Owns takeover and launch safety.

Tasks:

- confirm canonical `main` is clean and pushed
- confirm GCS mirrors match current distilled control packets
- confirm operator packet remains `ready_to_arm_window`
- confirm launch pack remains `awaiting_window_arm`
- confirm closeout remains `window_already_closed`
- surface drift immediately if any packet suggests launch readiness before the operator explicitly arms the window

Outputs:

- refreshed control-plane packet status
- GCS mirror freshness note
- morning go/no-go summary

### Agent B - Research Data Engineer

Owns bounded market-data collection and layout.

Tasks:

- inventory existing downloader commands and historical data outputs
- map existing data to the canonical GCS layout
- fetch only missing bars or bounded snapshots needed for the governed 11-name universe if a non-broker downloader path already exists
- write raw, curated, and derived manifests with source, time range, symbol coverage, and schema notes

Target GCS layout:

- `gs://codexalpaca-data-us/raw/market_data/underlying_bars/date=<date>/symbol=<symbol>/`
- `gs://codexalpaca-data-us/raw/market_data/option_snapshots/date=<date>/symbol=<symbol>/`
- `gs://codexalpaca-data-us/curated/market_data/underlying_bars/date=<date>/`
- `gs://codexalpaca-data-us/curated/market_data/option_context/date=<date>/`
- `gs://codexalpaca-data-us/derived/research_features/date=<date>/`
- `gs://codexalpaca-control-us/research_scorecards/2026-04-24/`

### Agent C - Data Quality Auditor

Owns quality gates before research outputs are trusted.

Tasks:

- check symbol coverage
- check missing timestamps
- check duplicate rows
- check impossible OHLC values
- check stale bars
- check sparse option snapshots
- check excessive option spread samples
- estimate API/data cost when possible

Outputs:

- data-quality report
- pass/review-required verdict for each data tier
- explicit list of missing symbols or stale ranges

### Agent D - Loser-Learning Analyst

Owns turning April 23 into actionable guardrails.

Tasks:

- classify losing trades by symbol, strategy family, daypart, regime, structure, exit reason, spread quality, and slippage/economics issue
- produce a loser-cluster table
- identify similarity penalties for Friday and Monday scorecards
- keep automatic learning disabled for `review_required` sessions

Outputs:

- loser-learning table for April 23
- top loser clusters
- hold/quarantine recommendations for review only

### Agent E - Scorecard Analyst

Owns Friday and Monday selection quality.

Tasks:

- refresh the April 24 scorecard from updated data and evidence
- rank symbols and structures by liquidity, spread quality, realized loser similarity, and evidence confidence
- preserve the distinction between recommendation and execution mutation

Outputs:

- Friday quality scorecard
- Monday watchlist seed
- explicit avoid/shadow list

## Phase Plan

### Phase 0 - Safety Freeze

Status target: complete before any research work.

Checks:

- canonical control-plane `main` clean and pushed
- exclusive window unarmed
- operator packet `ready_to_arm_window`
- launch pack `awaiting_window_arm`
- no broker-facing session running from this plan

Stop condition:

- any packet indicates a live or armed execution window that was not explicitly operator-triggered

### Phase 1 - Evidence And Scorecard Baseline

Status target: already started on April 23 evening.

Actions:

- refresh April 23 session review
- refresh April 23 evidence contract
- refresh April 23 teaching gate
- refresh April 23 trade review
- refresh April 23 postmortem
- refresh April 23 audit-chain report
- produce initial April 24 quality scorecard

Required current verdict:

- April 23 session may remain `review_required`
- automatic learning must remain disabled unless the evidence contract becomes `ok`

### Phase 2 - Downloader Inventory And Data Layout

Actions:

- locate existing downloader entrypoints
- identify current local/GCS historical datasets
- produce an inventory of available symbols, dates, intervals, and option-snapshot coverage
- write the inventory to GCS under the research-data lane

Do not:

- create a new data vendor integration
- ingest broad symbols outside the governed 11-name universe
- ingest full tick or L2 feeds

### Phase 3 - Bounded Data Fill

Actions:

- fill missing 1-minute, 5-minute, and daily bars for the 11-name universe when a safe existing downloader exists
- fill only bounded option snapshots needed for liquidity/spread analysis
- capture execution-linked market context around April 23 entry/exit timestamps

Stop condition:

- downloader path requires broker order placement or live execution credentials beyond market-data access

### Phase 4 - Data Quality Gate

Actions:

- run schema and coverage checks
- classify each dataset as `ok`, `review_required`, or `missing`
- produce a cost/freshness note

Minimum pass:

- all 11 symbols have usable underlying bars for the relevant historical window
- option context is either present or explicitly marked missing without blocking the whole scorecard

### Phase 5 - Loser-Learning Backfill

Actions:

- join April 23 completed trades to market context where available
- classify loser clusters
- generate family/symbol/daypart penalties
- publish derived loser-learning artifacts to GCS

Hard rule:

- loser-learning outputs may recommend hold or quarantine, but may not mutate manifests or risk policy.

### Phase 6 - Friday And Monday Scorecards

Actions:

- refresh Friday scorecard before pre-open
- generate Monday watchlist seed for weekend review
- explicitly separate `preferred`, `allowed_cautious`, `shadow`, `avoid`, and `quarantine_review`

Morning use:

- advisory only for Friday
- no automatic strategy promotion

## Overnight Automation Rules

Allowed:

- packet freshness checks
- GCS mirror checks
- downloader inventory
- bounded market-data downloads
- data-quality reports
- loser-learning tables
- scorecard refreshes

Forbidden:

- arm exclusive execution window
- start a broker-facing session
- modify live manifest
- modify risk policy
- widen temporary parallel-runtime exception
- create new execution infrastructure

## Morning Success Definition

By Friday morning, the project should have:

- canonical control-plane packets current in GitHub and GCS
- April 23 evidence finalized and mirrored
- an April 24 quality scorecard in GCS
- a downloader/data inventory for the governed 11-name universe
- data-quality verdicts for whatever research data was available overnight
- loser-learning clusters for April 23
- one clear operator action: arm the exclusive window only after paper account availability and temporary parallel-path pause are confirmed

## Priority Order

If time or compute is limited:

1. preserve execution safety and packet clarity
2. complete evidence and teaching-gate refresh
3. refresh Friday scorecard
4. inventory existing research data
5. run data-quality gates
6. backfill loser-learning
7. download missing bounded market data

