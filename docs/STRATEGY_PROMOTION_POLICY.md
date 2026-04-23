# Strategy Promotion Policy

This packet defines how strategies move through governed paper-account tiers.

The system should reward trustworthy evidence, not just attractive backtests or a few lucky sessions.

## Operator Rule

- A strategy does not promote because it exists, because it backtests well, or because it had one good day.
- Promotion depends on trusted broker-audited evidence, after-cost economics, and repeatability.
- Review-required sessions are not unlock-grade evidence.

## Canonical Decision States

- `promote`
- `hold`
- `kill`
- `quarantine`

## Promotion Tiers

1. `research_only`

- research output exists
- not yet governed for broker-facing validation

2. `governed_validation`

- executable and allowed into controlled paper validation
- not yet unlock-grade

3. `unlocked_profile`

- allowed inside a governed tournament or paper profile

4. `preferred_profile`

- strong enough to be the preferred governed profile within its slot

5. `canonical_execution_candidate`

- evidence strong enough for discussion as part of the sanctioned execution baseline

## Strategy Classes

### Class A: Liquid single-leg next-expiry directional

Examples:

- trend long call
- trend long put

### Class B: Same-day or opening-window single-leg

Examples:

- ORB same-day options
- high-gamma opening-window variants

### Class C: Defined-risk multi-leg debit structures

Examples:

- call backspreads
- verticals

### Class D: Complex choppy, premium, or convexity-sensitive structures

Examples:

- iron butterfly
- higher-risk multi-leg convexity profiles

## Minimum Trusted Sessions By Strategy Class

### To Move From `governed_validation` To `unlocked_profile`

- Class A: `3` trusted sessions and at least `15` completed trades
- Class B: `4` trusted sessions and at least `20` completed trades
- Class C: `5` trusted sessions and at least `15` completed positions
- Class D: `6` trusted sessions and at least `20` completed positions

### To Move From `unlocked_profile` To `preferred_profile`

- Class A: `6` trusted sessions and at least `30` completed trades
- Class B: `8` trusted sessions and at least `40` completed trades
- Class C: `8` trusted sessions and at least `25` completed positions
- Class D: `10` trusted sessions and at least `35` completed positions

### To Become A `canonical_execution_candidate`

- Class A: `10` trusted sessions
- Class B: `12` trusted sessions
- Class C: `12` trusted sessions
- Class D: `15` trusted sessions

Plus:

- no quarantine incidents in the counted window
- no unresolved broker/local economics drift
- at least two recent trusted sessions in the last 10 trading days

## Mandatory Evidence Before Any Promotion

Mandatory for all classes:

- broker-order audit
- broker account-activity audit
- ending broker-position snapshot
- shutdown reconciliation
- completed trade table with broker/local cashflow comparison
- session evidence contract not `gapped`
- session teaching gate allowing automatic learning
- runner release and capability stamp
- loser-trade classification coverage

If any item is missing:

- decision defaults to `quarantine` if evidence integrity is compromised
- decision defaults to `hold` if the evidence is merely incomplete but non-contaminated

## Promote Criteria

Promote only when all of the following are true in the counted trusted sample:

- after-cost expectancy is positive
- median slippage is inside the calibrated envelope
- no residual-position incidents
- no review-required evidence sessions are counted
- loser-trade taxonomy does not show an unresolved repeated structural defect
- drawdown is acceptable for the strategy class
- recency requirements are met

Class-specific profitability floor:

- Class A: profit factor at least `1.10`
- Class B: profit factor at least `1.15`
- Class C: profit factor at least `1.10`
- Class D: profit factor at least `1.20`

## Hold Criteria

Hold when:

- evidence count is below threshold
- expectancy is near flat but not decisively negative
- loser patterns are present but plausibly fixable
- recency is stale
- evidence quality is acceptable but not strong enough to promote

Default state for most early strategies should be `hold`, not `promote`.

## Kill Criteria

Kill when trusted evidence shows:

- negative after-cost expectancy after minimum sample
- repeated `regime_mismatch` or `structure_selection_failure` that survives calibration attempts
- repeated loss concentration that is not offset by the winner cohort
- weak economics across recent sessions, not just old history

Kill is a governed retirement. Keep tombstone metadata; do not silently delete history.

## Quarantine Criteria

Quarantine immediately when any of the following occur:

- session evidence contract is `gapped` or `review_required`
- broker/local economics drift exceeds tolerance
- ending positions are not flat when flatness is required
- a broker or runner anomaly contaminates the sample
- strategy behavior violates declared structure or risk metadata

Quarantine blocks automatic learning, unlock progression, and promotion counting.

## Recency Policy

Recency should matter more than deep stale history.

Rules:

- at least `2` counted trusted sessions must be from the last `10` trading days
- sessions older than `20` trading days should count only as supporting context, not primary promotion proof
- if a strategy has not traded recently, it should drift to `hold`, not stay implicitly promoted forever

## Promotion By Family, Not Just By Strategy

Before promoting an aggressive variant, review the family:

- if the family is already showing repeated loser-taxonomy defects, do not promote a nearby variant just because its isolated PnL is positive
- family-level slippage or anomaly patterns should cap the whole family

## Early-Phase Bias

During the early VM-validation phase:

- prefer `hold` over `promote`
- prefer `quarantine` over accidental teaching from dirty evidence
- require stronger evidence before moving Class C or Class D structures upward

The lab should grow slower than the research imagination until execution evidence is unquestionably trustworthy.
