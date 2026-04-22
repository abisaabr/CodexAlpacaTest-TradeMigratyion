# Nightly Operator Playbook

This playbook is the operator-facing implementation of the institutional blueprint.

Use it when the goal is to run one full research-to-handoff nightly cycle in a disciplined, repeatable way.

Preferred entrypoint:
- `cleanroom/code/qqq_options_30d_cleanroom/launch_nightly_operator_cycle.ps1`

Before assigning agent work, refresh and inspect:
- `docs/REPO_UPDATE_CONTROL.md`
- `docs/repo_updates/repo_update_registry.md`
- `docs/repo_updates/repo_update_handoff.md`
- `docs/AGENT_GOVERNANCE.md`
- `docs/SESSION_RECONCILIATION_REGISTRY.md`
- `docs/session_reconciliation/session_reconciliation_registry.md`
- `docs/session_reconciliation/session_reconciliation_handoff.md`
- `docs/EXECUTION_CALIBRATION_REGISTRY.md`
- `docs/execution_calibration/execution_calibration_registry.md`
- `docs/execution_calibration/execution_calibration_handoff.md`
- `docs/agent_governance/agent_governance_registry.md`
- `docs/TOURNAMENT_PROFILE_REGISTRY.md`
- `docs/tournament_profiles/tournament_profile_registry.md`
- `docs/tournament_profiles/tournament_profile_handoff.md`

It is written for the current two-machine setup:
- current research machine = primary research plane
- new machine = execution / reproducible challenger plane
- GitHub migration repo = control plane

## Objective

Every night, the system should do four things well:

1. refresh the family and coverage view
2. refresh execution evidence and session trust from the paper runner
3. run the highest-value challenger research
4. validate challenger results against the champion book
5. leave behind a clear morning packet without auto-mutating production

## Core Rule

Research can be highly parallel.

Production decisions must remain serialized and reviewable.

## Nightly Sequence

### Phase -1: Repo Update Control

Owner:
- Repo Update Steward

Required outputs:
- `repo_update_registry.json`
- `repo_update_registry.md`
- `repo_update_handoff.json`
- `repo_update_handoff.md`

Tasks:
- refresh the repo update registry against GitHub
- verify the control-plane repo is current enough for governed nightly work
- verify the execution repo is current enough for the paper runner and contains required runner commits
- stop and surface an attention item if either repo is dirty, on the wrong branch, or behind a required branch

Go / no-go:
- do not start a governed nightly cycle from stale or branch-drifted repos when the handoff says update work is required

### Phase 0: Control-Plane Refresh

Owner:
- Strategy Family Steward
- Inventory Steward

Required outputs:
- `session_reconciliation_registry.json`
- `session_reconciliation_registry.md`
- `session_reconciliation_handoff.json`
- `session_reconciliation_handoff.md`
- `execution_calibration_registry.json`
- `execution_calibration_registry.md`
- `execution_calibration_handoff.json`
- `execution_calibration_handoff.md`
- `tournament_profile_registry.json`
- `tournament_profile_registry.md`
- `tournament_profile_handoff.json`
- `tournament_profile_handoff.md`
- `strategy_family_registry.json`
- `strategy_family_registry.md`
- `strategy_family_handoff.json`
- `strategy_family_handoff.md`
- refreshed ticker coverage outputs

Tasks:
- refresh the session reconciliation registry from the paper runner
- refresh the session reconciliation handoff so the nightly cycle can distinguish trusted sessions from review-required sessions before using paper evidence to steer research
- refresh the execution calibration registry from the paper runner
- refresh the execution calibration handoff packet so the nightly cycle has a machine-readable posture and policy recommendation
- confirm the backtester will consume that handoff so nightly selection grids tighten automatically when live execution posture is in `caution`
- confirm the fill model overlay is active so entry/exit slippage assumptions tighten automatically under the same posture
- confirm deterministic fill-capacity / no-fill logic is active so challenger sizing reflects weak-leg liquidity and combo complexity instead of assuming every requested size fills
- confirm exit-cleanup degradation is active so larger multi-leg positions can realize worse-than-combo exits when liquidity would not plausibly clear the whole order at the scheduled mark
- refresh the tournament profile registry and tournament profile handoff so profile choice is resolved from approved executable profiles plus current execution posture
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
- do not let `review_required` paper-runner sessions loosen research policy, fill assumptions, or promotion conclusions
- do not launch discovery if the execution calibration packet shows a telemetry or guardrail issue that should change fill assumptions first

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
- execution calibration refreshed
- tournament profile policy refreshed
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
3. refresh tournament profile policy
4. refresh coverage
5. materialize missing priority symbols if needed
6. run discovery lanes
7. run exhaustive follow-up
8. run shared-account validation
9. generate review packets
10. generate morning handoff
11. keep the live manifest unchanged until explicit review
