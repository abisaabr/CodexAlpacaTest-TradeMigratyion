# Current Research Promotion Board

## State

- State: `phase32b_phase36_phase37_running_phase34_phase35_completed`
- Broker-facing: `false`
- Live manifest effect: `none`
- Risk policy effect: `none`
- Active Batch jobs: `phase32b-unexplored-top100-tranche2-20260428122500` (`RUNNING`, 8 succeeded / 3 running / 4 pending at last check), `phase36-core-liq-20260428180637` (`RUNNING`, 4 running / 11 pending at last check), and `phase37-top10-atm-20260428183723` (`SCHEDULED`, 6 pending at last check)

## Bounded-Validation Candidates

One candidate is ready for a bounded paper-validation operator decision:

- `AAPL` `b150__aapl__long_call__wide_reward__exit_360__liq_baseline`
- Source: `phase27_aapl_governance_stress_20260428141000`
- Minimum net PnL: `$1715.93`
- Minimum holdout/test net PnL: `$341.155`
- Fill coverage: `0.9474-1.0`
- Minimum option trades: `36`
- Worst drawdown: `$-4167.955`
- Current required next step: explicit exclusive-window operator decision before any broker-facing validation.

## Research-Only Blocked

- `NVDA` exit-300 tight-reward tight-liquidity passed Phase28 but failed Phase30 governance stress with `min_net_pnl_not_positive`.
- `AAPL` exit-210 wide-reward tight-liquidity remains blocked by `fill_coverage_below_0.90`.
- `NVDA` exit-360 tight-reward tight-liquidity remains blocked by `test_net_pnl_not_above_0`.
- The Phase31 `AMZN`/`AVGO`/`MSFT`/`MU` wide-lag cluster is blocked and should be quarantined or redesigned, not replayed unchanged.
- Phase32 is actively expanding unexplored top100 coverage across `AMD`, `PLTR`, `GOOG`, `ORCL`, `XOM`, `XLE`, `JPM`, `UNH`, `V`, `BAC`, `CRM`, `XLI`, `GE`, `AMAT`, and `TQQQ`.
- Phase32b is actively expanding candidate-rich unexplored coverage across `NOW`, `BKNG`, `MA`, `CSCO`, `JNJ`, `CVX`, `WMT`, `HOOD`, `KRE`, `CAT`, `GS`, `IBM`, `SLV`, `XLK`, and `BA`.
- Interim Phase32 `XLE` result is research-only blocked: `0/9` eligible, zero download failures, best two variants have positive economics but only about `0.60` fill coverage.
- Interim scan across 23 completed output packets has `0` new governed-validation candidates. The dominant blocker remains `fill_coverage_below_0.90`; the newly scanned `GS` and `MA` packets are also research-only blocked.
- Best research-only fill-repair leads so far: `UNH` tight exit-360, `AMD` balanced exit-360, `GE` tight put exit-360, `ORCL` balanced exit-360, `PLTR` balanced put exit-300, `AMAT` tight exit-210, `KRE` wide exit-360, and `TQQQ` wide exit-300.
- Phase34 completed and blocked all four tested top leads (`AMD`, `GE`, `ORCL`, `PLTR`) because none reached `0.90` fill coverage under tested exit lags.
- Phase35 completed and blocked `UNH`; max fill was `0.6792`, below the mandatory `0.90` gate.
- Phase32 completed all 15 shards with no new governed-validation candidates.
- Phase37 is active as a top-10 liquid-underlying weekly ATM lane using `0-7` DTE, ATM-only contracts, and `entry_liquidity_first_research_only` replay.

## Current Recommendation

- Paper validation: keep scope to `AAPL` exit-360 only, and only if an exclusive execution window is explicitly armed.
- Research: monitor Phase32b, Phase36, and Phase37 to completion; build portfolio-level aggregation from completed packets, then prioritize liquidity-gated candidate discovery rather than economic stress on low-fill names.
- Promotion: do not promote any candidate to live or durable paper allocation without broker-audited bounded paper validation evidence.

## Guardrails

Do not trade, arm a window, start a broker-facing paper/live session, modify live manifests, change risk policy, or relax the `0.90` fill gate from this board.
