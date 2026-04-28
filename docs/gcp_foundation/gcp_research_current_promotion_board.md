# Current Research Promotion Board

## State

- State: `phase42_dense_download_replay_complete_promotion_blocked_exit_policy_redesign_required`
- Broker-facing: `false`
- Live manifest effect: `none`
- Risk policy effect: `none`
- Active Batch jobs: `none` in `codexalpaca/us-central1` from this research monitor
- Latest durable rollup: `gs://codexalpaca-control-us/research_results/top100_liquidity_research_20260426/rollups/phase42_dense_download_replay_20260428232000/output/`

## Bounded-Validation Candidates

One pre-existing candidate remains ready for a bounded paper-validation operator decision. It is unchanged by Phase42 and is not live-promoted:

- `AAPL` `b150__aapl__long_call__wide_reward__exit_360__liq_baseline`
- Source: `phase27_aapl_governance_stress_20260428141000`
- Minimum net PnL: `$1715.93`
- Minimum holdout/test net PnL: `$341.155`
- Fill coverage: `0.9474-1.0`
- Minimum option trades: `36`
- Worst drawdown: `$-4167.955`
- Required next step: explicit exclusive-window operator decision before any broker-facing validation.

## Phase42 Final

Phase42 completed all ten dense top-liquid shards over `SPY`, `NVDA`, `QQQ`, `AMZN`, `TSLA`, `MSFT`, `IWM`, `AAPL`, `META`, and `MU`.

- Source reports: `10`
- Candidates scanned: `183`
- Eligible for governed promotion review: `0`
- Decision: `research_only_blocked`
- Blocker counts: `{'fill_coverage_below_0.90': 183, 'min_net_pnl_not_positive': 17, 'option_trades_below_20': 120, 'test_net_pnl_not_above_0': 89}`
- Fill failure counts: `{'exit_bar_gap_or_exit_policy_mismatch': 183}`
- Highest observed minimum fill across all candidates: `0.8594`
- Best minimum-fill row: `MU` `b150__mu__long_call__tight_reward__exit_210__liq_baseline` with fill `0.8594-0.9062`, min_net `$2469.63`, min_test `$-849.8375`, blockers `fill_coverage_below_0.90, test_net_pnl_not_above_0`

The dense data foundation is now materially better: Phase40 gave `17/17` inventory coverage and Phase41 gave `16/17` dense selected weekdays. Phase42 still found `0/183` eligible because every candidate failed the unchanged `0.90` fill gate, dominated by `exit_bar_gap_or_exit_policy_mismatch`.

## Research-Only Leads

The Phase42 research-only capital plan is useful for redesign priority, not promotion:

- `TSLA` `b150__tsla__long_call__balanced_reward__exit_360__liq_baseline` weight `12.80%` min_net `$10413.765` min_test `$23910.1625` fill `0.6667` blockers `fill_coverage_below_0.90`
- `TSLA` `b150__tsla__long_call__wide_reward__exit_300__liq_tight` weight `12.20%` min_net `$9775.3675` min_test `$21775.2375` fill `0.6897` blockers `fill_coverage_below_0.90`
- `MSFT` `b150__msft__long_call__wide_reward__exit_210__liq_baseline` weight `13.89%` min_net `$26388.665` min_test `$5313.96` fill `0.7333` blockers `fill_coverage_below_0.90`
- `AMZN` `b150__amzn__long_call__tight_reward__exit_210__liq_baseline` weight `14.96%` min_net `$28268.085` min_test `$2439.931` fill `0.7895` blockers `fill_coverage_below_0.90`
- `AAPL` `b150__aapl__long_call__balanced_reward__exit_210__liq_baseline` weight `15.27%` min_net `$19272.609` min_test `$5542.945` fill `0.6897` blockers `fill_coverage_below_0.90`
- `MSFT` `b150__msft__long_call__balanced_reward__exit_210__liq_baseline` weight `11.11%` min_net `$28901.22` min_test `$1801.825` fill `0.7812` blockers `fill_coverage_below_0.90`
- `AAPL` `b150__aapl__long_call__tight_reward__exit_210__liq_tight` weight `9.73%` min_net `$16912.174` min_test `$6006.405` fill `0.6774` blockers `fill_coverage_below_0.90`
- `NVDA` `b150__nvda__long_call__tight_reward__exit_210__liq_baseline` weight `10.04%` min_net `$10900.35` min_test `$641.05` fill `0.6452` blockers `fill_coverage_below_0.90`

## Current Recommendation

- Paper validation: keep broker-facing validation limited to the pre-existing AAPL exit-360 candidate, and only after an explicit exclusive-window operator decision.
- Options research: stop treating broad data repair as the primary blocker for top-10 dense names; redesign exits around actually fillable exit bars and rerun candidate-specific stress.
- Portfolio research: build the stock/ETF fallback lane in parallel so daily PnL research can proceed without depending entirely on option fill coverage.
- Promotion: do not promote Phase42 candidates; no option candidate from Phase42 satisfies the `0.90` fill gate.

## Guardrails

Do not trade, arm a window, start a broker-facing paper/live session, modify live manifests, change risk policy, or relax the `0.90` fill gate from this board.
