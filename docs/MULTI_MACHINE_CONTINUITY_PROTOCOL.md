# Multi-Machine Continuity Protocol

This document defines how the project stays operable if one machine or one Codex thread disappears without warning.

## Goal

Make every material project state recoverable from:

- GitHub `main`
- open GitHub PRs
- GCS control packets when available
- compact operator-facing handoff packets

No important decision should depend on one machine's shell history, one unstaged working tree, or one operator's memory.

## Canonical Sources

### Governance Truth

- GitHub `main`

Use GitHub `main` as the canonical policy and control-plane line.

### Runtime / Control Mirror

- `gs://codexalpaca-control-us`

Use GCS as the runtime mirror for distilled control packets and cloud-state artifacts when a machine has working GCP tooling.

### Sanctioned Execution Path

- `vm-execution-paper-01`

This remains the only sanctioned cloud execution path.

### Parallel Runtime Status

- tolerated only under explicit temporary exception control

The parallel runtime path is not a second sanctioned architecture.

## Current Cross-Machine Truth

At the current project moment:

- the first sanctioned VM trusted validation session is not launched yet
- the execution plane is technically ready enough to attempt it
- the remaining gating step is an explicitly armed bounded exclusive execution window
- current effort split should remain approximately:
  - `70%` execution evidence, loser-learning quality, and promotion discipline
  - `30%` new research breadth

## Required Takeover Read Order

Any machine taking over should read in this order:

1. `docs/PROJECT_TARGET_OPERATING_MODEL.md`
2. `docs/gcp_foundation/project_target_operating_model_handoff.md`
3. `docs/gcp_foundation/research_strategy_governance_handoff.md`
4. `docs/gcp_foundation/gcp_execution_trusted_validation_operator_handoff.md`
5. `docs/gcp_foundation/gcp_execution_trusted_validation_session_status.md`
6. `docs/gcp_foundation/gcp_execution_exclusive_window_handoff.md`
7. `docs/gcp_foundation/gcp_execution_trusted_validation_launch_handoff.md`
8. `docs/gcp_foundation/gcp_execution_closeout_handoff.md`

## Required GitHub Checks

Before continuing work, the takeover machine should:

1. fetch `origin`
2. inspect `origin/main`
3. inspect any open control-plane PRs that are ahead of `main`
4. decide whether to:
   - merge the PR
   - integrate equivalent changes onto `main`
   - or continue on a fresh branch from `origin/main`

## Branch Discipline

- do not rely on stale local `main`
- if local `main` diverges, prefer creating a clean branch from `origin/main`
- prefer small scoped PRs over large local-only piles of changes
- if a branch contains takeover-relevant work, record the branch and PR in a handoff packet before leaving it

## Logging Rules

Every material change should be logged in at least one durable place before the operator stops:

1. GitHub branch or `main`
2. GitHub PR description or PR comment if the branch is not yet merged
3. GCS control mirror when available

Do not let important state exist only in:

- local shell output
- an unstaged file
- uncommitted packet changes
- one machine's memory

## Execution Rules

- do not arm an exclusive execution window casually
- do not start a broker-facing session unless the refreshed launch pack says `ready_to_launch`
- do not skip post-session assimilation
- do not leave the exclusive window armed after the session ends

## Research Rules

- keep research governed and bounded during this early phase
- do not scale research breadth faster than evidence quality and promotion discipline
- prefer selective GCS data foundation over broad uncontrolled ingestion

## Immediate Priority Order

1. arm a bounded exclusive execution window only when ready to use it
2. run the first sanctioned VM trusted validation session
3. assimilate immediately
4. apply loser-trade learning and promotion policy before scaling strategy breadth
5. expand research breadth only after the evidence loop remains clean

## Continuity Standard

The project is continuity-safe when a second machine can recover the correct next action from GitHub alone within minutes.
