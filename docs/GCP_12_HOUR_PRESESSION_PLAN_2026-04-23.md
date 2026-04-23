# GCP 12-Hour Pre-Session Plan

Date context:

- Today: Thursday, April 23, 2026
- Target bounded session: Friday, April 24, 2026

This packet defines the best institutional use of the next 12 hours before the first sanctioned bounded GCP paper session on `vm-execution-paper-01`.

The goal is not to maximize activity. The goal is to maximize expected decision quality for tomorrow while minimizing execution mistakes, evidence gaps, and unforced losses.

## Operator Rule

- The first profit improvement should come from better selection, cleaner execution evidence, and tighter loser-learning, not from impulsive overnight scope expansion.
- Do not spend tonight on changes that make tomorrow harder to govern.
- If a task does not clearly improve execution safety, evidence quality, or bounded session selection, defer it.

## Strategic Priority Order

1. Preserve execution safety and avoid operator error.
2. Produce the cleanest possible first broker-audited trusted evidence bundle tomorrow.
3. Improve tomorrow’s symbol and structure selection quality without mutating the live manifest tonight.
4. Improve loser-trade learning readiness so tomorrow’s session teaches the control plane immediately.
5. Expand research breadth only where it is bounded, reproducible, and clearly lower-risk than the execution path.

## Multi-Agent Topology

Use the next 12 hours as five coordinated lanes.

### Agent A: Control-Plane Sentry

Mission:

- keep canonical `main` and the GCS control mirror aligned
- detect stale packet wording, packet drift, or GCS mirror drift
- confirm the operator packet remains the top-level lifecycle

Must not:

- arm the exclusive window
- change policy or widen the temporary parallel-runtime exception

Primary outputs:

- refreshed packet freshness checks
- refreshed continuity read
- morning-ready operator state confirmation

### Agent B: Execution Evidence Auditor

Mission:

- inspect recent loss and anomaly surfaces
- produce non-broker-facing pre-session quality checks
- identify what should be strictly left unchanged before tomorrow

Must not:

- start the runner
- modify strategy selection or risk policy

Primary outputs:

- no-touch list for tomorrow morning
- pre-session evidence checklist
- anomaly summary and loss-risk review

### Agent C: Research Data Engineer

Mission:

- build the minimum governed GCS research substrate for the current 11-name research universe
- prefer reproducible raw, curated, and derived datasets over broad ingest

Minimum universe:

- `QQQ`
- `SPY`
- `IWM`
- `NVDA`
- `MSFT`
- `AMZN`
- `TSLA`
- `PLTR`
- `XLE`
- `GLD`
- `SLV`

Primary outputs:

- reference masters
- 1-minute, 5-minute, and daily bars
- bounded 5-minute options snapshots
- session-aligned market-context tables

### Agent D: Loser-Learning Engineer

Mission:

- backfill loser-trade taxonomy support
- build the joins required for tomorrow’s post-session assimilation

Primary outputs:

- loser-vs-winner comparison tables
- slippage and spread-width join tables
- anomaly-aware classification tables

### Agent E: Research Quality Analyst

Mission:

- score tomorrow’s bounded session candidates by liquidity, spread quality, anomaly cleanliness, and expected slippage
- prioritize structure quality over breadth

Primary outputs:

- Friday bounded-session execution-quality scorecard
- ranked small liquid governed ticker set
- do-not-favor list for structurally weaker names

## Multi-Phase Schedule

## Phase 0: Freeze The Bounded Session Surface

Time:

- immediately

Goals:

- freeze canonical control-plane truth
- confirm the next action is still the exclusive-window arm, not more architecture work

Actions:

- re-check canonical `main`
- re-check distilled GCS handoffs
- re-check operator packet state
- do not touch execution manifests, risk policy, or runner entrypoints

Success gate:

- packet stack still reads:
  - operator packet: `ready_to_arm_window`
  - trusted validation readiness: `awaiting_exclusive_execution_window`
  - launch pack: `awaiting_window_arm`
  - closeout: `window_already_closed`

## Phase 1: Execution-Risk Reduction

Time:

- next 2 to 3 hours

Owner lanes:

- Agent A
- Agent B

Goals:

- reduce tomorrow’s loss risk without changing strategy logic

Actions:

- review recent incident, halt, and losing-trade surfaces
- build a no-touch list for tomorrow
- confirm exact launch/assimilation/closeout commands
- confirm that the packet stack contains no stale or contradictory operator wording

Do not do:

- any live-manifest mutation
- strategy selection changes
- risk-ceiling changes
- lease-enforcement changes

Success gate:

- tomorrow’s operator path is unmistakable and free of stale control-plane instructions

## Phase 2: Build The Minimum Governed Research Data Foundation

Time:

- next 4 to 8 hours

Owner lanes:

- Agent C

Goals:

- use cloud compute and storage for bounded, high-value data work
- improve tomorrow’s and next week’s decision quality without affecting live execution

Actions:

- land reference masters for the 11-name governed research universe
- land 1-minute, 5-minute, and daily bars
- land bounded options snapshot history
- stage these in raw / curated / derived tiers

Cost and freshness rules:

- no full-chain tick ingest
- no L2
- no alt-data
- keep the ingest bounded and reproducible

Success gate:

- the data foundation is rich enough to support slippage modeling, loser analysis, and session-quality scoring tomorrow

## Phase 3: Build Loser-Learning Readiness

Time:

- parallel with Phase 2

Owner lanes:

- Agent D

Goals:

- ensure tomorrow’s first trusted session can be assimilated into real learning immediately

Actions:

- build loser-taxonomy join tables
- join market context, slippage, spread width, excursions, and evidence verdicts
- make sure the pipeline distinguishes:
  - healthy losses
  - structure failures
  - liquidity failures
  - anomaly-contaminated sessions

Success gate:

- tomorrow’s broker-audited evidence bundle can flow straight into hold / kill / calibration logic

## Phase 4: Produce The Friday Bounded-Session Quality Scorecard

Time:

- late overnight, after Phases 2 and 3 have enough substrate

Owner lanes:

- Agent E

Goals:

- maximize tomorrow’s expected quality, not tomorrow’s theoretical breadth

Actions:

- rank the 11-name governed universe by:
  - spread quality
  - recent slippage
  - anomaly cleanliness
  - liquidity stability
  - family balance value
- produce a recommended bounded small set for tomorrow’s first sanctioned VM session

Decision rule:

- prefer high-liquidity, cleaner, more stable names over broad experimentation
- do not broaden the universe tonight

Success gate:

- tomorrow morning has a compact operator-readable selection scorecard

## Phase 5: Morning Go/No-Go Prep

Time:

- final 1 to 2 hours before operator handoff

Owner lanes:

- Agent A
- Agent B
- Steward

Goals:

- make the next safe action binary and explicit

Actions:

- confirm packets still fresh
- confirm GCS mirror current
- confirm no new blocker emerged
- confirm the exact command sequence:
  - arm window
  - SSH
  - VM session
  - post-session assimilation
  - closeout

Success gate:

- morning operator can proceed without improvisation

## Overnight Automation Model

What should be automated tonight:

- control-plane packet freshness checks
- GCS mirror freshness checks
- runner commit and packet-state verification
- non-broker-facing research data jobs
- loser-learning backfill jobs
- bounded execution-quality scorecard build

What should not be automated tonight:

- exclusive-window arm
- broker-facing VM session
- live-manifest changes
- strategy promotion
- widening the temporary parallel-runtime exception

## Compute Use Policy

Use Google Cloud compute tonight for:

- bounded market-data extraction
- reproducible feature generation
- slippage and liquidity-quality modeling
- loser-learning joins
- scorecard generation

Do not use it tonight for:

- new live predictive models for deployment tomorrow
- broad strategy generation without clear family purpose
- infrastructure sprawl

## Profit And Loss Reality Check

The best way to maximize profit tomorrow is:

- avoid operational mistakes
- avoid structurally weak symbols and dirty fills
- select a small cleaner bounded set
- capture the cleanest possible broker-audited evidence

The best way to minimize loss tomorrow is:

- no overnight execution-path churn
- no last-minute strategy/risk improvisation
- no scope expansion beyond governed quality

## Deliverables By Morning

1. Canonical control-plane packets still aligned in GitHub and GCS
2. No-touch execution checklist
3. Governed 11-name GCS research substrate
4. Loser-learning readiness tables
5. Friday bounded-session quality scorecard
6. One exact morning command sequence for the first sanctioned VM session

## Default Effort Split

- `60%` execution safety, evidence readiness, and operator clarity
- `25%` governed data foundation and quality scoring
- `15%` loser-learning backfill and calibration readiness

This is slightly more execution-heavy than the standing `70/30` strategic split for one reason: the next 12 hours are pre-session preparation hours, not general roadmap hours.
