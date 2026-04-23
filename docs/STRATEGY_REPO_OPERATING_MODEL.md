# Strategy Repo Operating Model

This packet defines how the strategy library should be structured so the project gains breadth without turning the runner repo into a junk drawer.

The project needs more high-quality strategies. It does not need more anonymous variants scattered across manifests, notebooks, and scratch files.

## Operator Rule

- Separate executable promoted strategy manifests from the broader research library.
- Every strategy must have governed metadata before it is eligible for a broker-facing path.
- Raw research exhaust belongs in GCS, not in the runner repo.

## Canonical Responsibility Split

### Control-Plane Repo

Owns:

- policy
- registries
- unlock logic
- promotion and hold decisions
- family and tournament governance

### Runner Repo

Owns:

- executable strategy definitions that the sanctioned runner can actually trade
- governed live manifests
- code entrypoints and signal wiring
- release-ready metadata for broker-facing candidates

### GCS

Owns:

- raw research outputs
- backtest exhaust
- tournament results
- large derived feature tables
- archived evidence bundles

## Repo Structure

The runner repo should remain narrow:

- `config/strategy_manifests/`
  - promoted and governed executable manifests only
- `docs/`
  - operator and deployment documentation
- code paths under `alpaca_lab/`
  - execution and signal implementations

The broader strategy library should be governed through metadata, not by shoving every generated variant into the live manifest.

Recommended governed library shape:

```text
strategy_library/
  families/
    <family_id>/
      family.yaml
      rationale.md
  strategies/
    <strategy_id>.yaml
  bundles/
    validation_candidates.yaml
    unlocked_profiles.yaml
    preferred_profiles.yaml
```

This can live in the runner repo later if needed, but only after the metadata model is enforced. Until then, the live manifest should stay small and explicit.

## Strategy Metadata Schema

Every governed strategy should declare:

- `strategy_id`
- `display_name`
- `family_id`
- `structure_class`
- `regime`
- `timing_profile`
- `signal_name`
- `dte_mode`
- `underlying_scope`
- `liquidity_tier`
- `entry_window`
- `hard_exit_window`
- `risk_fraction`
- `max_contracts`
- `legs`
- `promotion_tier`
- `promotion_state`
- `required_evidence_class`
- `required_audit_coverage`
- `owner_plane`
- `source_tournament_profile`
- `source_research_run_id`
- `runner_entrypoint_status`
- `last_reviewed_at`
- `last_decision`
- `quarantine_reason`
- `kill_reason`
- `parent_strategy_id`
- `runner_capability_epoch_min`

Rules:

- `strategy_id` is immutable
- one strategy belongs to one primary family
- if a strategy is killed or quarantined, keep the metadata and record the reason

## Avoiding Junk-Drawer Sprawl

Do not allow:

- unnamed experimental YAMLs in the live manifest directory
- one-off notebook outputs committed beside executable manifests
- multiple competing names for the same strategy concept
- hidden variants whose only identity is a different filename

Use these controls instead:

- immutable `strategy_id`
- required metadata schema
- one canonical location for promoted manifests
- one canonical registry for family mapping
- tombstones for killed strategies
- GCS for large raw research outputs

## Breadth Without Losing Rigor

Breadth should be quota-driven by family gaps, not by random strategy generation.

Required breadth controls:

- no more than `40%` of new research slots should go to already dominant single-leg families while multi-leg and choppy families remain under-covered
- at least one active research lane should always target an underrepresented family
- new variants should be created in clusters around a thesis, not as isolated random parameter tweaks

Preferred breadth order:

1. family gaps
2. daypart gaps
3. structure gaps
4. underlying diversification
5. parameter refinement

## Searchability Model

The library should be searchable by:

- family
- structure class
- regime
- timing profile
- DTE
- underlying scope
- promotion tier
- evidence state
- review state

This means metadata must be queryable without reading freeform strategy descriptions.

## Promotion Discipline Inside The Repo

A strategy should not appear in a broker-facing manifest unless:

- it has a governed metadata record
- it has a family mapping
- it has a clear promotion state
- it has evidence requirements declared

That prevents the live book from becoming the accidental master registry.

## What Should Stay Out Of The Repo

Do not commit:

- raw intraday market exhaust
- large backtest output trees
- raw trade logs
- temporary tournament scratch variants
- intermediate feature tables that can be reproduced

Commit instead:

- compact metadata
- compact registries
- handoff packets
- promoted manifests
- decision records

## Early-Phase Recommendation

In the current phase, use the runner repo as:

- a governed executable strategy surface
- a promotion-ready manifest surface
- a release-ready codebase

Do not use it as the exhaustive storage surface for every research variant yet.

That keeps the repo searchable, reviewable, and institutionally governable while the project is still proving execution trust.
