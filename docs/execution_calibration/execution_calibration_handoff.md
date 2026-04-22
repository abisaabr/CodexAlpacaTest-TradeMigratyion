# Execution Calibration Handoff

## Snapshot

- Generated at: `2026-04-22T14:37:03.516841`
- Posture: `caution`
- Evidence strength: `limited_entry_only`

## Flags

- `sample_size_limited`: `true`
- `session_reconciliation_filter_active`: `true`
- `sessions_excluded_by_session_reconciliation`: `true`
- `high_guardrail_pressure`: `true`
- `elevated_entry_friction`: `true`
- `exit_telemetry_gap`: `true`
- `reconciliation_pressure`: `false`
- `partial_fill_pressure`: `false`
- `broker_order_audit_gap`: `true`
- `broker_activity_audit_gap`: `true`

## Policy Guidance

- Entry penalty mode: `raised`
- Exit model posture: `conservative_fallback`
- Opening-window debit posture: `caution`
- Preferred research bias: `defined_risk_and_premium_defense`
- Recommended profiles: `down_choppy_coverage_ranked, opening_30m_premium_defense`
- Deprioritized profiles: `opening_30m_convexity_butterfly, opening_30m_single_vs_multileg`

## Operator Actions

- Use `raised` entry-fill penalties while observed entry friction remains around 0.80% mean absolute slippage and 0.65% mean adverse event slippage.
- Keep exit-side execution modeling conservative until explicit exit slippage telemetry becomes reliable.
- Trust session reconciliation to exclude review-required paper-runner sessions before they can loosen execution calibration.
- Treat excluded paper-runner sessions as evidence to inspect, not evidence to learn from automatically.
- Favor premium-defense and defined-risk opening-window challengers before adding more aggressive debit-heavy opening profiles.
- Treat current execution evidence as directional rather than fully authoritative because the completed-trade sample is still small.
- Treat broker-order audit coverage itself as a telemetry gap until upgraded session bundles start landing from the execution machine.
- Treat broker account-activity audit coverage as a telemetry gap until upgraded session bundles start landing from the execution machine.

## Top Entry Slippage Clusters

- `PLTR`: mean absolute entry slippage `0.0`% of expected across `1` filled entries
- `TSLA`: mean absolute entry slippage `0.769231`% of expected across `1` filled entries
- `QQQ`: mean absolute entry slippage `0.320366`% of expected across `1` filled entries
- `SPY`: mean absolute entry slippage `0.539084`% of expected across `1` filled entries
- `ARKK`: mean absolute entry slippage `2.389078`% of expected across `1` filled entries

## Top Loss Clusters

- `qqq__slow__orb_long_put_same_day`: estimated total net PnL `-507.50`, exit reason `severe_loss_flatten_all`
- `pltr__fast__trend_long_put_next_expiry`: estimated total net PnL `-498.90`, exit reason `severe_loss_flatten_all`
- `tsla__fast__trend_long_put_next_expiry`: estimated total net PnL `-196.30`, exit reason `severe_loss_flatten_all`
- `spy__fast__trend_long_put_next_expiry`: estimated total net PnL `-98.60`, exit reason `severe_loss_flatten_all`
- `arkk__fast__trend_long_put_next_expiry`: estimated total net PnL `-42.30`, exit reason `severe_loss_flatten_all`

