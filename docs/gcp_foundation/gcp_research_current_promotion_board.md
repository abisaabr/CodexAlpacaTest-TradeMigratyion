# Current Research Promotion Board

## State

- State: `phase41_dense_coverage_passed_phase42_download_replay_running`
- Broker-facing: `false`
- Live manifest effect: `none`
- Risk policy effect: `none`
- Active Batch jobs: `phase38-dense-top10-20260428203428` (`RUNNING`, older baseline lane) and `phase42-dense-download-replay-20260428182000` (`SCHEDULED`, repaired dense option download/replay). Phase41 completed and passed dense selected-contract coverage for all ten top-liquid symbols.

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
- Phase32b completed candidate-rich unexplored coverage across `NOW`, `BKNG`, `MA`, `CSCO`, `JNJ`, `CVX`, `WMT`, `HOOD`, `KRE`, `CAT`, `GS`, `IBM`, `SLV`, `XLK`, and `BA`.
- Interim Phase32 `XLE` result is research-only blocked: `0/9` eligible, zero download failures, best two variants have positive economics but only about `0.60` fill coverage.
- Interim scan across 32 completed output packets has `0` new governed-validation candidates. The dominant blocker remains `fill_coverage_below_0.90`; Phase36 has now completed and is awaiting aggregation.
- Best research-only fill-repair leads so far: `UNH` tight exit-360, `AMD` balanced exit-360, `GE` tight put exit-360, `ORCL` balanced exit-360, `PLTR` balanced put exit-300, `AMAT` tight exit-210, `KRE` wide exit-360, and `TQQQ` wide exit-300.
- Phase34 completed and blocked all four tested top leads (`AMD`, `GE`, `ORCL`, `PLTR`) because none reached `0.90` fill coverage under tested exit lags.
- Phase35 completed and blocked `UNH`; max fill was `0.6792`, below the mandatory `0.90` gate.
- Phase32 completed all 15 shards with no new governed-validation candidates.
- Phase32b completed all 15 shards and is ready for wave-level aggregation; no Phase32b result can be promoted directly without the rollup and gate review.
- Phase37 completed as a top-10 liquid-underlying weekly ATM lane using `0-7` DTE, ATM-only contracts, and `entry_liquidity_first_research_only` replay. Its rollup scanned `183` candidates, found `0` eligible, and classified all candidates as `selected_contract_universe_gap`; max min-fill was only `0.1111`.
- The local QQQ dense cleanroom downloader succeeded for `2026-03-18` through `2026-04-17` with `2794/2794` successful contract-day requests and `96.242%` dense selected-contract-day fill. This is a data-foundation repair template, not a promotion packet.
- Phase38 is active as the direct dense-universe fill diagnostic for `SPY`, `NVDA`, `QQQ`, `AMZN`, `TSLA`, `MSFT`, `IWM`, `AAPL`, `META`, and `MU`; the first visible shards (`MSFT`, `NVDA`, `QQQ`) are still blocked by `selected_contract_universe_gap`.
- Phase38 dense-universe packets for visible shards selected only `4` trade dates, not the full intended `2026-03-02` to `2026-04-23` window. The next engineering fix is dense-universe reference-date coverage diagnostics and repair.
- Phase39 completed using runner commit `b6e48cddce0f` and the curated top-150 stock parquet (`2026-04-01` to `2026-04-23`). It showed stock reference coverage was usable (`16/17` weekdays) but dense selected-contract coverage failed (`4/17` weekdays for most symbols, `0/17` for `MU`), proving the current top100 option contract inventory is incomplete for historical `0-7` DTE testing.
- Runner commit `91d75fb36c7c` adds `scripts/download_historical_option_contract_inventory.py`, a research-only active+inactive contract inventory downloader based on the proven QQQ dense cleanroom pattern.
- Phase40 completed and fixed the top-10 option contract inventory foundation: all ten symbols reached `17/17` requested weekday coverage for the `0-7` DTE inventory window.
- Phase41 completed and passed dense selected-contract coverage for all ten top-liquid symbols (`16/17` selected weekdays, `0.941176` coverage).
- Phase42 is now launched to download option bars/trades and replay top-10 strategy queues against the repaired dense selected-contract roots.
- Runner commit `5578a6803ae7` adds the wave-level rollup tool that aggregates shard-level portfolio reports into one capital plan, fill-failure map, data-repair queue, strategy-redesign queue, and promotion-review packet.
- Runner commit `6dca362e41bf` hardens the rollup to infer fill-failure reasons from older shard packets.
- Runner commit `83e2803b4aab` adds the fill-experiment comparison tool so sparse, ATM-only, dense, and future stock/ETF fallback lanes can be compared under one gate.
- Completed Phase32/Phase32b/Phase36 rollup scanned `45` source reports and `640` candidates; `0` are eligible for governed promotion review. Fill blockers are `276` entry timing gaps, `339` exit timing gaps, and `25` mixed low-fill gaps.
- Fill comparison between the completed event-sparse rollup and Phase37 ATM-only rollup concludes `continue_dense_or_broader_contract_universe_repair`; ATM-only is worse than sparse/event-selected fill and is not a promotion path.

## Current Recommendation

- Paper validation: keep scope to `AAPL` exit-360 only, and only if an exclusive execution window is explicitly armed.
- Research: monitor Phase42 completion, then aggregate shard portfolio reports into a wave-level promotion review. Do not promote from individual shard packets.
- Aggregation: use `scripts/build_research_wave_portfolio_rollup.py` and `scripts/build_research_fill_experiment_comparison.py` after shards are staged locally so promotion review is systematic and not manually cherry-picked from individual shard packets.
- Promotion: do not promote any candidate to live or durable paper allocation without broker-audited bounded paper validation evidence.

## Guardrails

Do not trade, arm a window, start a broker-facing paper/live session, modify live manifests, change risk policy, or relax the `0.90` fill gate from this board.
