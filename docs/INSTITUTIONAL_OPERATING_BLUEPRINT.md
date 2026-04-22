# Institutional Operating Blueprint

This blueprint defines how the project should evolve from a strong single-machine research workflow into an institutional-grade, multi-machine, agentic system.

The goal is not "maximum automation at any cost." The goal is:

- automate repeatable research and evidence collection
- serialize high-consequence production decisions
- preserve lineage, auditability, and rollback safety
- let the paper runner improve over time through champion/challenger review

## Operating Planes

### 1. Research Plane

Primary owner right now:
- the current research machine

Responsibilities:
- heavy cleanroom backtests
- new family design and parameter expansion
- data prep and materialization into `backtester_ready`
- broad discovery waves
- exhaustive follow-up waves
- debugging and hardening research orchestration

Primary workspace:
- `qqq_options_30d_cleanroom`

Outputs:
- `*_summary.json`
- `master_summary.json`
- `run_manifest.json`
- `run_registry.jsonl`
- family registry snapshots
- shortlist packets
- validation and replacement-plan packets

### 2. Control Plane

Primary owner:
- GitHub-backed migration repo

Responsibilities:
- operating model
- strategy-family registry
- steward prompts
- launch packs
- handoff packets
- replacement-plan and morning-handoff review surfaces
- new-machine prompts

Primary workspace:
- `CodexAlpacaTest-TradeMigratyion`

Why it matters:
- both machines should be able to reason from the same docs, packets, prompts, and family taxonomy
- no machine should rely on private memory or terminal-only context to understand what to do next

### 3. Execution Plane

Primary owner:
- the paper-runner repo and the machine currently designated as runner or standby

Responsibilities:
- live manifest
- runner config and risk controls
- paper trading
- health checks
- fills, slippage, and runtime telemetry
- production gating

Primary workspace:
- `codexalpaca_repo`

Hard rule:
- the execution plane consumes approved evidence; it does not invent strategy changes on its own

## Machine Roles

### Current Research Machine

Short-term role:
- primary research and orchestration machine

Use it for:
- large backtests
- new-family prototyping
- orchestration debugging
- broad and exhaustive tournament waves
- postmortem and execution-model improvement

Do not use it as the only long-term production dependency.

### New Machine

Short-term role:
- controlled consumer of GitHub-backed playbooks
- paper-runner or standby-runner host
- lighter research and reproducible conveyor execution

Use it for:
- runner operations
- reproducible family-steward refresh
- repeatable tournament waves from committed prompts and launch packs
- morning handoff consumption

Long-term role:
- production champion executor
- reproducible challenger validator

### GitHub

Long-term role:
- memory, governance, and handoff layer

GitHub should hold:
- agent operating model
- institutional blueprint
- strategy-family registry
- family steward prompt
- launch-pack builders
- validation/replacement-plan docs
- new-machine prompts

## Automation Levels

### Level 1: Automated Discovery

Allowed now:
- family-registry refresh
- coverage refresh
- data prep and materialization
- discovery wave launches
- exhaustive wave launches
- run-registry reporting
- morning handoff generation

These are high-volume, low-consequence tasks once the control plane is correct.

### Level 2: Automated Evaluation

Allowed now, but still review-oriented:
- shortlist building
- shared-account validation
- hardening review
- replacement-plan generation
- paper-runner gate updates

These can be automatic because they produce packets, not production changes.

### Level 3: Human-Gated Production Change

Should remain gated for now:
- live manifest edits
- production risk-policy changes
- auto-promotion into the runner
- large structural changes to strategy families

Institutional-grade means the system can generate recommendations automatically, but production mutation still follows explicit approval.

## Champion / Challenger Model

### Champion

The current live manifest is the champion book.

Properties:
- currently deployed to the paper runner
- protected by the gate
- only changed via explicit reviewed merge

### Challenger

Any research winner is a challenger until it passes:
1. discovery
2. exhaustive validation
3. shared-account validation
4. hardening review
5. replacement-plan review
6. morning handoff approval

Only then can it become a live-manifest candidate.

## Agent System

### Control-Plane Agents

- Strategy Family Steward
- Inventory Steward
- Data Prep Steward
- Strategy Architect
- Reporting Steward
- Promotion Steward

### Research Agents

- 4 discovery lanes
- 2 exhaustive lanes
- 1 shared-account validator

### Execution / Feedback Agents

- postmortem / loss-analysis steward
- fill-calibration / friction steward

## Nightly Rhythm

### Night Before Research

1. Strategy Family Steward refreshes:
   - family registry
   - family handoff packet
2. Inventory Steward refreshes:
   - coverage matrix
   - ready/staged universe view
3. Data Prep Steward materializes missing priority symbols.

### Research Night

4. Discovery lanes run disjoint family cohorts.
5. Reporting Steward builds the shortlist.
6. Exhaustive lanes run only on shortlisted survivors.
7. Shared-Account Validator compares challengers against the champion book.

### Morning

8. Reporting Steward produces:
   - validation packet
   - hardening review
   - replacement plan
   - morning handoff
9. Gate allows the paper runner only after the morning handoff reaches a valid terminal state.
10. Promotion Steward acts only after explicit review.

## Daily Improvement Loops

### Fast Loop: Execution Feedback

Frequency:
- every trading day

Inputs:
- fills
- slippage
- losers
- concentration events
- runner guardrail events

Outputs:
- postmortem notes
- execution-model updates
- risk-control observations

### Slow Loop: Research Improvement

Frequency:
- nightly / multi-day

Inputs:
- family gaps
- research results
- replacement plans
- live-book concentration

Outputs:
- new family waves
- refined validation thresholds
- candidate additions/replacements

## What Should Improve Over Time

The system should get better in these ways:

- broader family coverage
- better diversification away from single-leg concentration
- stronger session-specific specialization
- better friction realism
- better shared-account construction
- fewer manual handoffs
- more trustworthy morning packets

It should not "improve" by:

- auto-expanding the live book without review
- drifting strategy families without lineage
- hiding failures behind wrapper-only success
- mixing research and production concerns on the same agent

## Institutional Controls

### Required Before Trusting A Wave

- valid `run_manifest.json`
- valid `run_registry.jsonl` append
- pack validation passed
- lane completion backed by `master_summary.json`
- active-program report available when long-running
- run-registry packet available after terminal states

### Required Before Trusting A Live-Book Candidate

- exhaustive validation complete
- shared-account validation complete
- hardening review complete
- replacement plan complete
- morning handoff complete

### Required Before Production Change

- explicit human approval
- merge preview available
- no live-manifest shrink unless intentional
- paper-runner gate consistent with reviewed state

## KPIs

Track these over time:

- family coverage breadth
- ready-universe coverage breadth
- share of live book by family
- share of live book by regime
- challenger-to-champion win rate
- friction-adjusted return
- drawdown improvement vs champion
- average time from discovery to reviewed replacement plan
- percent of waves that finish without manual orchestration repair

## Desired End State

### This Machine

- remains the primary heavy-research and strategy-architecture machine
- continues to originate new families and harder validation waves

### New Machine

- runs the champion paper book reliably
- can run committed research workflows from GitHub prompts and launch packs
- can take over increasing portions of the conveyor as confidence grows

### GitHub

- becomes the canonical memory layer
- holds all operating docs, steward prompts, family registry, and handoff surfaces

In the end, the system should feel like:
- research is parallel and evidence-rich
- production is disciplined and gated
- both machines can reason from the same control-plane artifacts
- the paper runner improves through reviewed champion/challenger turnover, not intuition
