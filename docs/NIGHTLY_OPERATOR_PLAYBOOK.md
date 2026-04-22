# Nightly Operator Playbook

This playbook is the operator-facing implementation of the institutional blueprint.

Use it when the goal is to run one full research-to-handoff nightly cycle in a disciplined, repeatable way.

It is written for the current two-machine setup:
- current research machine = primary research plane
- new machine = execution / reproducible challenger plane
- GitHub migration repo = control plane

## Objective

Every night, the system should do four things well:

1. refresh the family and coverage view
2. run the highest-value challenger research
3. validate challenger results against the champion book
4. leave behind a clear morning packet without auto-mutating production

## Core Rule

Research can be highly parallel.

Production decisions must remain serialized and reviewable.

## Nightly Sequence

### Phase 0: Control-Plane Refresh

Owner:
- Strategy Family Steward
- Inventory Steward

Required outputs:
- `strategy_family_registry.json`
- `strategy_family_registry.md`
- `strategy_family_handoff.json`
- `strategy_family_handoff.md`
- refreshed ticker coverage outputs

Tasks:
- refresh the formal family registry
- refresh the family handoff packet
- refresh ticker-family coverage
- confirm which families are:
  - `priority_discovery`
  - `priority_validation`
  - `promotion_follow_up`
  - `live_benchmark`

Go / no-go:
- do not launch discovery until family and coverage surfaces are current

### Phase 0.5: Data Prep

Owner:
- Data Prep Steward

Required outputs:
- `materialization_status.json` when prep is needed
- widened `backtester_ready` universe when staged/registry symbols are promoted into ready form

Tasks:
- compare ready universe vs staged/registry frontier
- materialize missing priority symbols if discovery would otherwise be too narrow

Go / no-go:
- do not mix research and materialization in the same lane

### Phase 1: Discovery

Owner:
- Bear Directional
- Bear Premium
- Bear Convexity
- Butterfly Lab

Required outputs per lane:
- `run_manifest.json`
- `run_registry.jsonl` append
- `master_summary.json`
- per-ticker `*_summary.json`
- lane-level rankings

Tasks:
- build an exact launch pack
- validate the pack
- run disjoint family cohorts
- keep promotion off

Go / no-go:
- any lane without `master_summary.json` is failed, even if the wrapper says exit code `0`

### Phase 2: Exhaustive Follow-Up

Owner:
- Down/Choppy Exhaustive
- Balanced Expansion when needed

Required outputs:
- `phase2_plan.json`
- exact Phase 2 launch pack
- exhaustive lane `master_summary.json`

Tasks:
- shortlist survivors from Phase 1
- run only validated survivors
- keep the exhaustive surface small and resume-safe

Go / no-go:
- no Phase 2 lane should be launched without shortlist provenance

### Phase 3: Shared-Account Validation

Owner:
- Shared-Account Validator

Required outputs:
- `live_book_validation.json`

Tasks:
- compare challengers against the current live champion book
- reject standalone winners that do not improve shared-account behavior

Go / no-go:
- do not interpret standalone strength as production readiness

### Phase 4: Review Packets

Owner:
- Reporting Steward

Required outputs:
- `live_book_hardening_review.json`
- `live_book_replacement_plan.json`
- `live_book_morning_handoff.json`
- `live_book_morning_handoff.md`

Tasks:
- turn validation results into reviewable add/replace packets
- produce one clean morning handoff

Go / no-go:
- the paper-runner gate should not clear until the morning handoff reaches a valid terminal state

### Phase 5: Production Decision

Owner:
- human reviewer
- Promotion Steward after approval

Required outputs:
- reviewed merge preview
- optional approved manifest update

Tasks:
- review `review_add` / `review_replace` packets
- decide whether the champion book changes

Go / no-go:
- no auto-promotion into the live manifest

## What This Machine Should Own Tonight

Use the current research machine for:
- heavy family-expansion research
- new-family discovery
- orchestration debugging
- large validation passes

This machine is still the best place for:
- expensive backtests
- new family prototyping
- control-plane hardening when the conveyor misbehaves

## What The New Machine Should Own Tonight

Use the new machine for:
- paper-runner operations
- deterministic prompt-driven steward refreshes
- reproducible challenger waves after the control plane is stable enough
- morning handoff consumption

The new machine should not become the sole source of strategy invention yet.

## Recommended Nightly Artifacts Checklist

Before signing off on a nightly run, confirm:
- family registry refreshed
- family handoff refreshed
- coverage refreshed
- launch pack validated
- every successful lane has `master_summary.json`
- run-registry packet exists
- validation packet exists
- replacement plan exists
- morning handoff exists
- paper-runner gate matches the reviewed state

## Escalation Rules

Escalate and stop automatic progression when:
- a lane exits without `master_summary.json`
- pack validation fails
- run-registry packet shows unresolved attention items
- validation cannot find the expected terminal artifacts
- replacement plan recommends a manifest shrink unexpectedly
- the paper-runner gate conflicts with the morning handoff

## Default Nightly Recommendation

When no extraordinary event changes priorities, the default order is:

1. refresh family registry
2. refresh family handoff
3. refresh coverage
4. materialize missing priority symbols if needed
5. run discovery lanes
6. run exhaustive follow-up
7. run shared-account validation
8. generate review packets
9. generate morning handoff
10. keep the live manifest unchanged until explicit review
