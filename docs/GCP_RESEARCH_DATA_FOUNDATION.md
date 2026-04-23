# GCP Research Data Foundation

This packet defines the minimum governed research-data substrate for the `codexalpaca` project.

The goal is not to ingest everything we can buy. The goal is to store the smallest market-data set that materially improves research breadth, strategy quality, and broker-audited learning without creating uncontrolled cost or data sprawl.

## Operator Rule

- Build the research plane around the current execution bottleneck, not around hypothetical future strategy scale.
- Store only data that can improve strategy selection, loser-trade diagnosis, execution calibration, or promotion discipline.
- Keep raw market-data ingestion narrower than the strategy universe until the first trusted VM validation session and its governed post-session evidence are clean.

## What Market Data Should Be Stored In GCS Now

### Reference Data

Store now:

- underlying symbol master for the governed research universe
- exchange/session calendars
- splits and dividend adjustments
- option contract master snapshots for the minimum viable research universe
- canonical session timestamps used by both research and execution review

Why:

- every downstream dataset needs stable symbol, contract, and calendar joins
- this is low-cost and high-value

### Raw Underlying Market Data

Store now:

- 1-minute OHLCV bars for the minimum viable research universe
- 5-minute OHLCV bars for the same universe
- daily OHLCV bars for the same universe

Why:

- this supports the current runner families and most first-order regime features
- it is enough for opening-window, trend, and choppy-family research without tick-level sprawl

### Raw Options Market Data

Store now:

- bounded option-chain snapshots for the minimum viable research universe
- snapshots should capture:
  - timestamp
  - underlying symbol
  - expiration
  - strike
  - option type
  - bid
  - ask
  - midpoint
  - last
  - volume
  - open interest when available
  - implied volatility when available

Initial cadence:

- every 5 minutes during the main cash session
- event-triggered snapshots around governed entry and exit windows for executed or shortlisted contracts

Why:

- this is enough to study structure choice, slippage envelopes, spread quality, and family selection
- it avoids the cost explosion of full-chain tick capture

### Execution-Linked Market Context

Store now:

- the market snapshots needed to explain executed trades:
  - underlying bars around entry and exit
  - option quotes around entry and exit
  - realized volatility context
  - spread width context

Why:

- loser-trade learning is weak if trade evidence cannot be joined to the actual market state

## What Should Not Be Ingested Yet

Do not ingest yet:

- full tick-by-tick option quote history for every chain
- Level 2 or order-book depth
- news sentiment, social, or alternative text data
- broad cross-asset macro feeds
- low-liquidity long-tail option universes
- duplicate vendor feeds for the same raw layer
- research-only exhaust with no governed retention policy

These are not banned forever. They are simply not justified before the execution plane has landed trusted broker-audited evidence and proven the current learning loop.

## Minimum Viable Research Universe

The minimum viable governed research universe should be:

- index and benchmark anchors:
  - `QQQ`
  - `SPY`
  - `IWM`
- liquid single-name execution anchors:
  - `NVDA`
  - `MSFT`
  - `AMZN`
  - `TSLA`
  - `PLTR`
- regime diversifiers for non-single-leg concentration:
  - `XLE`
  - `GLD`
  - `SLV`

Why this set:

- it covers the current live and near-live execution reality
- it preserves liquid options and tighter spreads
- it gives enough breadth to test trend, opening-window, choppy, and commodity-linked diversification without expanding to the full 21-symbol book immediately

Universe-expansion rule:

- do not widen the raw-options ingest universe beyond this set until:
  - the first trusted VM validation session is complete
  - governed post-session assimilation is clean
  - at least two fresh trusted sessions exist with broker-audited evidence

## Data Tiers

### 1. Raw

Purpose:

- immutable vendor-normalized ingest

Examples:

- underlying 1-minute, 5-minute, and daily bars
- option-chain snapshots
- reference master snapshots

Storage rules:

- partition by `trade_date`, `underlying_symbol`, and dataset family
- store as compressed columnar files where practical
- never hand-edit

### 2. Curated

Purpose:

- cleaned, schema-stable datasets used by research jobs

Examples:

- adjusted bar sets
- option snapshot joins with contract master and calendar data
- session-aligned chain panels
- candidate feature tables for discovery or validation waves

Storage rules:

- reproducible from raw plus versioned transforms
- schema changes require explicit doc updates

### 3. Derived

Purpose:

- strategy-ready and learning-ready outputs

Examples:

- feature matrices
- slippage envelopes
- liquidity buckets
- strategy family scorecards
- loser vs winner comparison tables
- promotion and hold candidate summaries

Storage rules:

- derived data must point back to raw or curated lineage
- no derived dataset should become governance truth unless a control-plane packet explicitly says so

## Cost Guardrails

Initial guardrails:

- hot research-data storage target: under `300 GB`
- raw options ingest target: under `10 GB/day`
- monthly storage plus routine query target: under `$250/month` before trusted VM evidence is clean
- object-count sprawl guardrail: prefer larger partitioned files over millions of tiny snapshots

Escalation rule:

- if a proposed expansion breaches the cost target, it must show one of:
  - materially better loser-trade explainability
  - materially better strategy-family coverage
  - materially better promotion discrimination

## Freshness Guardrails

Freshness targets:

- reference data: refresh daily, and additionally on corporate-action events
- underlying bars: available by overnight research start
- option snapshots: available same day and fully landed before overnight research
- execution-linked market context: available immediately after session finalization

Do not require:

- sub-second freshness
- streaming research ingest
- real-time cloud-wide data replication

The research plane should be T+0 and overnight-correct, not over-engineered for intrasecond analytics it does not yet use.

## Retention Guardrails

- raw: 90 days hot, archive afterward
- curated: 180 to 365 days hot depending on research reuse
- derived: keep only governed outputs or reproducible aggregates; purge ad hoc scratch derivations

## Promotion Gate For Data Expansion

Before the project adds broader data types or a larger universe, all of the following should be true:

- first trusted VM validation session complete
- broker-audited evidence package complete
- loser-trade learning packet has usable artifact coverage
- strategy promotion policy is using trusted sessions instead of mixed-quality history

Until then, better data discipline is worth more than more data.
