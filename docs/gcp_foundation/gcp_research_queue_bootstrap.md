# GCP Research Queue Bootstrap

## Snapshot

- Generated at: `2026-04-23T22:21:50.976677-04:00`
- Status: `ready_with_research_warnings`
- Strategy count: `94`
- Target trade date: `2026-04-24`
- Scorecard status: `ready_with_review_required_evidence`
- Single-leg strategy share: `95.7%`
- Estimated research variants: `2070`
- GCS prefix: `gs://codexalpaca-control-us/research_queue/bootstrap`

## Preferred Research Symbols

- `QQQ`
- `GLD`
- `MSFT`
- `SLV`
- `TSLA`

## Avoid Or Shadow Symbols

- `XLE`
- `SPY`
- `IWM`
- `PLTR`
- `AMZN`
- `NVDA`

## Queue

### RQ-001-defined-risk-family-expansion

- Priority: `1`
- Estimated variants: `240`
- Mission: Expand under-covered defined-risk and choppy/premium structures before adding more directional single-leg variants.
- Symbols: `QQQ, GLD, MSFT, SLV, TSLA`
- Live manifest effect: `none`

### RQ-002-single-leg-repair-and-loss-filter

- Priority: `2`
- Estimated variants: `1242`
- Mission: Repair existing single-leg families with stricter exits, liquidity gates, and loser-similarity filters.
- Symbols: `QQQ, GLD, MSFT, SLV, TSLA`
- Live manifest effect: `none`

### RQ-003-loser-cluster-shadow-diagnostics

- Priority: `3`
- Estimated variants: `522`
- Mission: Use avoid/shadow symbols to learn what failed without granting them execution eligibility.
- Symbols: `XLE, SPY, IWM, PLTR, AMZN, NVDA`
- Live manifest effect: `none`

### RQ-004-regime-and-liquidity-feature-grid

- Priority: `4`
- Estimated variants: `66`
- Mission: Build symbol/regime/liquidity features that explain when each strategy family should be suppressed.
- Symbols: `QQQ, SPY, IWM, NVDA, MSFT, AMZN, TSLA, PLTR, XLE, GLD, SLV`
- Live manifest effect: `none`

## Issues

- `warning` `single_leg_concentration`: Current manifest is 95.7% single-leg directional strategies.

## Guardrails

- `research_queue_is_advisory_only`
- `do_not_mutate_live_manifest`
- `do_not_change_risk_policy`
- `do_not_start_broker_facing_session`
- `require_promotion_packet_before_runner_eligibility`
