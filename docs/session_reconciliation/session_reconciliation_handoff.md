# Session Reconciliation Handoff

## Snapshot

- Generated at: `2026-04-22T14:32:10.854123`
- Posture: `caution`
- Evidence strength: `limited`

## Flags

- `review_required_recent`: `false`
- `caution_recent`: `true`
- `broker_order_audit_gap`: `true`
- `broker_activity_audit_gap`: `true`
- `residual_positions`: `false`
- `economics_delta`: `false`
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

## Sessions Needing Attention

- `2026-04-16`: tier `caution`, quality `70`, reasons `broker_order_audit_gap, broker_activity_audit_gap, guardrail_manual_review, severe_loss_flatten_triggered`

