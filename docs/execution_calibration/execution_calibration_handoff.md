# Execution Calibration Handoff

## Snapshot

- Generated at: `2026-04-27T10:53:29.129201`
- Posture: `caution`
- Evidence strength: `limited`
- Unlock evidence strength: `no_recent_trade_sessions`
- Trusted unlock-grade sessions: `0`
- Trusted runner-baseline sessions: `0`
- Latest trusted unlock-grade session: `none`
- Latest trusted unlock-grade session age (days): `n/a`

## Flags

- `sample_size_limited`: `true`
- `session_reconciliation_filter_active`: `true`
- `sessions_excluded_by_session_reconciliation`: `true`
- `high_guardrail_pressure`: `true`
- `elevated_entry_friction`: `true`
- `exit_telemetry_gap`: `false`
- `reconciliation_pressure`: `false`
- `partial_fill_pressure`: `false`
- `broker_order_audit_gap`: `true`
- `broker_activity_audit_gap`: `true`
- `runner_unlock_baseline_gap`: `true`
- `unlock_evidence_stale`: `true`

## Policy Guidance

- Entry penalty mode: `raised`
- Exit model posture: `observed_exit_calibration`
- Opening-window debit posture: `caution`
- Preferred research bias: `defined_risk_and_premium_defense`
- Profile activation confidence: `bootstrapping`
- Max execution risk tier: `moderate`
- Broker-audited profile activation permitted: `false`
- Opening-window aggressive profiles permitted: `false`
- Recommended profiles: `down_choppy_coverage_ranked, opening_30m_premium_defense`
- Deprioritized profiles: `opening_30m_convexity_butterfly, opening_30m_single_vs_multileg`

## Operator Actions

- Use `raised` entry-fill penalties while observed entry friction remains around 1.98% mean absolute slippage and 1.71% mean adverse event slippage.
- Keep exit-side execution modeling conservative until explicit exit slippage telemetry becomes reliable.
- Do not activate tournament profiles above `moderate` risk until execution evidence improves.
- Trust session reconciliation to exclude review-required paper-runner sessions before they can loosen execution calibration.
- Treat excluded paper-runner sessions as evidence to inspect, not evidence to learn from automatically.
- Favor premium-defense and defined-risk opening-window challengers before adding more aggressive debit-heavy opening profiles.
- Treat current execution evidence as directional rather than fully authoritative because the completed-trade sample is still small.
- Treat broker-order audit coverage itself as a telemetry gap until upgraded session bundles start landing from the execution machine.
- Treat broker account-activity audit coverage as a telemetry gap until upgraded session bundles start landing from the execution machine.
- Do not treat legacy or dirty-runner sessions as unlock-grade evidence until a fresh clean runner-baseline session lands from the execution machine.
- Refresh broker-audited unlock evidence before activating blocked profiles; older trusted sessions should guide calibration, not unlock higher-risk tournaments.
- Do not activate broker-audited-only profiles until both broker-order and broker-activity audit coverage are present in trusted learning sessions.
- Keep aggressive opening-window and combo-heavy profiles behind the execution evidence floor until broad audited evidence and exit telemetry are present.

## Top Entry Slippage Clusters

- `AMZN`: mean absolute entry slippage `0.542142`% of expected across `3` filled entries
- `PLTR`: mean absolute entry slippage `0.979551`% of expected across `3` filled entries
- `IWM`: mean absolute entry slippage `1.396111`% of expected across `3` filled entries
- `NVDA`: mean absolute entry slippage `0.223714`% of expected across `3` filled entries
- `QQQ`: mean absolute entry slippage `0.185713`% of expected across `4` filled entries

## Top Loss Clusters

- `gdx__fast__trend_long_call_next_expiry`: estimated total net PnL `-475.80`, exit reason `stop_loss`
- `pltr__fast__trend_long_put_next_expiry`: estimated total net PnL `-400.41`, exit reason `stop_loss`
- `nvda__fast__trend_long_call_next_expiry_d70`: estimated total net PnL `-339.91`, exit reason `stop_loss`
- `nvda__base__trend_long_put_next_expiry`: estimated total net PnL `-183.31`, exit reason `stop_loss`
- `iwm__base__orb_long_put_next_expiry`: estimated total net PnL `-160.80`, exit reason `profit_target`

