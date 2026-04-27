# Execution Calibration Registry

This registry is the control-plane source of truth for what the paper runner has actually experienced in fills, exits, loss clusters, and guardrail pressure.

## Sources

- Runner repo root: `C:\Users\abisa\Downloads\codexalpaca_repo_vm_f008`
- Reports root: `C:\Users\abisa\Downloads\codexalpaca_runtime\multi_ticker_portfolio_live`
- Sessions scanned: `4`
- Date span: `2026-04-21` -> `2026-04-24`
- Session-reconciliation scope: `trusted_and_cautious_sessions`
- Sessions included by session-reconciliation policy: `2`
- Sessions excluded by session-reconciliation policy: `2`

## Headline Calibration Summary

- Completed trades: `24`
- Reconciliation attempts: `5642`
- Event rows: `5957`
- Sessions with broker-order audit: `0`
- Sessions with broker-activity audit: `0`
- Latest trusted unlock-grade session: `none`
- Latest trusted unlock-grade session age (days): `n/a`
- Broker orders audited: `193`
- Broker activities audited: `0`
- Broker activity unmatched rows: `0`
- Broker status mismatches: `0`
- Local orders without broker match: `0`
- Local filled orders without activity match: `0`
- Ending broker positions: `0`
- Entry fills: `26`
- Exit fills: `24`
- Guardrail fires: `1068`
- Severe-loss flatten sessions: `1`
- Mean absolute entry slippage vs expected: `1.982188`%
- Mean absolute exit slippage vs expected: `1.977095`%
- Mean event-level adverse entry slippage vs expected: `1.711588`%

## Institutional Findings

- `high` `guardrail_pressure`: Severe-loss flatten triggered in 1 session(s). That is a clear signal to pressure-test aggressive opening debit exposure and portfolio loss caps.
- `medium` `broker_audit_gap`: Session-level broker order audit artifacts are not present yet in the execution sample. Entry-side calibration is useful today, but combo-exit and reconciliation policy should still stay conservative until upgraded session bundles accumulate.
- `medium` `broker_activity_audit_gap`: Session-level broker account-activity audit artifacts are not present yet in the execution sample. That means the control plane still lacks a second source of truth for fills beyond local events and broker order snapshots.
- `medium` `runner_unlock_baseline_gap`: Trusted session bundles do not yet include a clean runner-baseline stamp, so unlock-grade evidence should remain blocked even when older paper evidence exists.
- `medium` `loss_cluster`: Losses are concentrated in a small set of strategies: gdx__fast__trend_long_call_next_expiry (-475.80), pltr__fast__trend_long_put_next_expiry (-400.41), nvda__fast__trend_long_call_next_expiry_d70 (-339.91). Those are the best immediate candidates for tighter calibration or challenger replacement pressure.

## Top 10 Entry Slippage Clusters By Ticker

- `GDX`: entry fills `2`, mean absolute entry slippage `10.691526`% of expected, completed trades `2`
- `SCHW`: entry fills `1`, mean absolute entry slippage `3.968254`% of expected, completed trades `1`
- `XLE`: entry fills `1`, mean absolute entry slippage `3.703704`% of expected, completed trades `1`
- `NKE`: entry fills `2`, mean absolute entry slippage `3.516737`% of expected, completed trades `2`
- `BAC`: entry fills `2`, mean absolute entry slippage `2.315018`% of expected, completed trades `2`
- `IWM`: entry fills `3`, mean absolute entry slippage `1.396111`% of expected, completed trades `3`
- `PLTR`: entry fills `3`, mean absolute entry slippage `0.979551`% of expected, completed trades `3`
- `AMZN`: entry fills `3`, mean absolute entry slippage `0.542142`% of expected, completed trades `3`
- `SPY`: entry fills `2`, mean absolute entry slippage `0.325481`% of expected, completed trades `2`
- `NVDA`: entry fills `3`, mean absolute entry slippage `0.223714`% of expected, completed trades `3`

## Top 10 Loss Clusters By Strategy

- `gdx__fast__trend_long_call_next_expiry`: completed trades `1`, estimated total net PnL `-475.80`, top exit reason `stop_loss`
- `pltr__fast__trend_long_put_next_expiry`: completed trades `1`, estimated total net PnL `-400.41`, top exit reason `stop_loss`
- `nvda__fast__trend_long_call_next_expiry_d70`: completed trades `2`, estimated total net PnL `-339.91`, top exit reason `stop_loss`
- `nvda__base__trend_long_put_next_expiry`: completed trades `1`, estimated total net PnL `-183.31`, top exit reason `stop_loss`
- `iwm__base__orb_long_put_next_expiry`: completed trades `2`, estimated total net PnL `-160.80`, top exit reason `profit_target`
- `gdx__fast__trend_long_put_next_expiry`: completed trades `1`, estimated total net PnL `-156.21`, top exit reason `stop_loss`
- `spy__slow__trend_long_call_next_expiry_d70`: completed trades `1`, estimated total net PnL `-131.11`, top exit reason `stop_loss`
- `bac__fast__trend_long_call_next_expiry`: completed trades `1`, estimated total net PnL `-90.60`, top exit reason `stop_loss`
- `amzn__base__trend_long_call_next_expiry`: completed trades `1`, estimated total net PnL `-77.11`, top exit reason `stop_loss`
- `amzn__fast__trend_long_call_next_expiry`: completed trades `1`, estimated total net PnL `-71.11`, top exit reason `stop_loss`

## Session Health

- `2026-04-22`: startup `failed`, completed trades `10`, broker-activity rows `0`, guardrail fires `680`, broker mismatches `0`, unmatched local orders `0`, unmatched broker activities `0`, ending broker positions `0`, blocked new entries `true`, severe-loss flatten `false`
- `2026-04-23`: startup `passed`, completed trades `14`, broker-activity rows `0`, guardrail fires `388`, broker mismatches `0`, unmatched local orders `0`, unmatched broker activities `0`, ending broker positions `0`, blocked new entries `true`, severe-loss flatten `true`

## Data Quality

- Missing summary dates: `none`
- Missing reconciliation dates: `none`
- Missing completed-trade dates: `none`
- Missing state dates: `none`
- Missing event-log dates: `none`
- Missing broker-order audit dates: `none`
- Missing broker-activity audit dates: `none`
- Missing ending-broker-position dates: `none`
- Missing session-reconciliation dates: `none`
- Excluded session dates: `2026-04-21, 2026-04-24`
- Current runner telemetry is materially stronger on entry-side calibration than exit-side slippage calibration.

