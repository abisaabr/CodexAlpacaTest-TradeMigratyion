# Session Reconciliation Handoff

## Snapshot

- Generated at: `2026-04-22T18:00:38.621377`
- Posture: `caution`
- Evidence strength: `limited`
- Latest traded session: `2026-04-16`
- Latest traded session age days: `6`
- Freshness posture: `stale`

## Flags

- `review_required_recent`: `false`
- `caution_recent`: `true`
- `broker_order_audit_gap`: `true`
- `broker_activity_audit_gap`: `true`
- `broker_cashflow_comparison_gap`: `false`
- `runner_unlock_baseline_gap`: `true`
- `residual_positions`: `false`
- `economics_delta`: `false`
- `broker_economics_delta`: `false`
- `mismatch_pressure`: `false`
- `partial_fill_pressure`: `false`
- `cleanup_pressure`: `false`

## Policy Guidance

- Trusted learning scope: `trusted_and_cautious_sessions`
- Promotion readiness: `review_only`

## Operator Actions

- Use `trusted_and_cautious_sessions` when deciding which paper-runner sessions should influence research calibration and tournament policy.
- Treat broker-order audit coverage as incomplete and avoid over-trusting clean local order logs alone.
- Treat broker account-activity coverage as incomplete and avoid over-trusting local fill telemetry alone.
- Treat pre-baseline or dirty-runner sessions as calibration-only evidence, not unlock-grade evidence for blocked tournament profiles.

## Sessions Needing Attention

- `2026-04-16`: tier `caution`, quality `70`, reasons `broker_order_audit_gap, broker_activity_audit_gap, runner_unlock_baseline_gap, guardrail_manual_review, severe_loss_flatten_triggered`

