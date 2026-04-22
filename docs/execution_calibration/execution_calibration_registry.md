# Execution Calibration Registry

This registry is the control-plane source of truth for what the paper runner has actually experienced in fills, exits, loss clusters, and guardrail pressure.

## Sources

- Runner repo root: `C:\Users\rabisaab\OneDrive\CodexAlpaca\downloads_remaining_20260417\folders\codexalpaca_repo`
- Reports root: `C:\Users\rabisaab\OneDrive\CodexAlpaca\downloads_remaining_20260417\folders\codexalpaca_repo\reports\multi_ticker_portfolio`
- Sessions scanned: `7`
- Date span: `2026-04-12` -> `2026-04-21`

## Headline Calibration Summary

- Completed trades: `5`
- Reconciliation attempts: `690`
- Event rows: `6235`
- Entry fills: `5`
- Exit fills: `5`
- Guardrail fires: `61`
- Severe-loss flatten sessions: `1`
- Mean absolute entry slippage vs expected: `0.803552`%
- Mean event-level adverse entry slippage vs expected: `1.499969`%

## Institutional Findings

- `high` `telemetry_gap`: Exit slippage is still not captured reliably in the condensed runner artifacts. Entry-side calibration is actionable today, but exit-side execution modeling should remain conservative until expected exit pricing and exit slippage are logged consistently.
- `high` `guardrail_pressure`: Severe-loss flatten triggered in 1 session(s). That is a clear signal to pressure-test aggressive opening debit exposure and portfolio loss caps.
- `medium` `loss_cluster`: Losses are concentrated in a small set of strategies: qqq__slow__orb_long_put_same_day (-507.50), pltr__fast__trend_long_put_next_expiry (-498.90), tsla__fast__trend_long_put_next_expiry (-196.30). Those are the best immediate candidates for tighter calibration or challenger replacement pressure.

## Top 10 Entry Slippage Clusters By Ticker

- `ARKK`: entry fills `1`, mean absolute entry slippage `2.389078`% of expected, completed trades `1`
- `TSLA`: entry fills `1`, mean absolute entry slippage `0.769231`% of expected, completed trades `1`
- `SPY`: entry fills `1`, mean absolute entry slippage `0.539084`% of expected, completed trades `1`
- `QQQ`: entry fills `1`, mean absolute entry slippage `0.320366`% of expected, completed trades `1`
- `PLTR`: entry fills `1`, mean absolute entry slippage `0.0`% of expected, completed trades `1`

## Top 10 Loss Clusters By Strategy

- `qqq__slow__orb_long_put_same_day`: completed trades `1`, estimated total net PnL `-507.50`, top exit reason `severe_loss_flatten_all`
- `pltr__fast__trend_long_put_next_expiry`: completed trades `1`, estimated total net PnL `-498.90`, top exit reason `severe_loss_flatten_all`
- `tsla__fast__trend_long_put_next_expiry`: completed trades `1`, estimated total net PnL `-196.30`, top exit reason `severe_loss_flatten_all`
- `spy__fast__trend_long_put_next_expiry`: completed trades `1`, estimated total net PnL `-98.60`, top exit reason `severe_loss_flatten_all`
- `arkk__fast__trend_long_put_next_expiry`: completed trades `1`, estimated total net PnL `-42.30`, top exit reason `severe_loss_flatten_all`

## Session Health

- `2026-04-12`: startup `pending`, completed trades `0`, guardrail fires `0`, blocked new entries `false`, severe-loss flatten `false`
- `2026-04-13`: startup `passed`, completed trades `0`, guardrail fires `0`, blocked new entries `false`, severe-loss flatten `false`
- `2026-04-14`: startup `passed`, completed trades `0`, guardrail fires `0`, blocked new entries `false`, severe-loss flatten `false`
- `2026-04-15`: startup `passed`, completed trades `0`, guardrail fires `0`, blocked new entries `true`, severe-loss flatten `false`
- `2026-04-16`: startup `passed`, completed trades `5`, guardrail fires `61`, blocked new entries `true`, severe-loss flatten `true`
- `2026-04-17`: startup `passed`, completed trades `0`, guardrail fires `0`, blocked new entries `false`, severe-loss flatten `false`
- `2026-04-21`: startup `pending`, completed trades `0`, guardrail fires `0`, blocked new entries `false`, severe-loss flatten `false`

## Data Quality

- Missing summary dates: `2026-04-13, 2026-04-14, 2026-04-15, 2026-04-17`
- Missing reconciliation dates: `2026-04-12, 2026-04-13, 2026-04-14, 2026-04-15, 2026-04-17, 2026-04-21`
- Missing completed-trade dates: `2026-04-12, 2026-04-13, 2026-04-14, 2026-04-15, 2026-04-17, 2026-04-21`
- Missing state dates: `none`
- Missing event-log dates: `2026-04-12, 2026-04-21`
- Current runner telemetry is materially stronger on entry-side calibration than exit-side slippage calibration.

