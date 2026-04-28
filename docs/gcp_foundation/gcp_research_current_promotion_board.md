# Current Research Promotion Board

## State

- State: `phase32_phase32b_and_phase34_running`
- Broker-facing: `false`
- Live manifest effect: `none`
- Risk policy effect: `none`
- Active Batch jobs: `phase32-unexplored-top100-tranche1-20260428120500` (`RUNNING`, 11 succeeded / 4 running at last check), `phase32b-unexplored-top100-tranche2-20260428122500` (`RUNNING`, 3 succeeded / 2 running / 10 pending at last check), and `phase34-top-lead-exitlag-20260428172500` (`SCHEDULED`, 4 pending at launch)

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
- Interim scan across 14 completed output packets has `0` new governed-validation candidates. The dominant blocker remains `fill_coverage_below_0.90`.
- Best research-only fill-repair leads so far: `AMD` balanced exit-360, `GE` tight put exit-360, `ORCL` balanced exit-360, `PLTR` balanced put exit-300, `AMAT` tight exit-210, `KRE` wide exit-360, and `TQQQ` wide exit-300.
- Phase34 is actively testing those four best fill-repair leads for exit-lag feasibility. Phase34 is diagnostic only and cannot directly promote candidates.

## Current Recommendation

- Paper validation: keep scope to `AAPL` exit-360 only, and only if an exclusive execution window is explicitly armed.
- Research: monitor Phase32, Phase32b, and Phase34; if unexplored shards finish cleanly, aggregate per-symbol promotion packets into a portfolio-level review, and use Phase34 only to decide whether top fill-blocked leads deserve isolated economic stress or redesign.
- Promotion: do not promote any candidate to live or durable paper allocation without broker-audited bounded paper validation evidence.

## Guardrails

Do not trade, arm a window, start a broker-facing paper/live session, modify live manifests, change risk policy, or relax the `0.90` fill gate from this board.
