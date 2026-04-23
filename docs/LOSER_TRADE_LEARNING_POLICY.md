# Loser-Trade Learning Policy

This packet defines how the project should analyze losing trades and turn them into governed improvements instead of anecdotal reactions.

The objective is not to eliminate all losers. The objective is to separate healthy losses from structural defects and to stop repeating losses that the machine should already understand.

## Operator Rule

- A losing trade is only useful if it can be classified, compared, and tied back to strategy and market context.
- Broker anomalies, residual-position incidents, or incomplete evidence do not teach research automatically.
- Loser learning must affect calibration, promotion, and unlock policy through explicit rules, not operator memory.

## Loss Taxonomy

Every completed losing trade should receive:

- one primary loss class
- zero or more modifiers
- a confidence score
- a recommended governance action

### Primary Loss Classes

1. `regime_mismatch`

- the strategy structure was wrong for the actual day or intraday regime
- examples:
  - trend-long strategy on mean-reverting chop
  - short-volatility structure into expansion

2. `entry_timing_failure`

- thesis may have been acceptable, but entry timing was poor
- examples:
  - too late after move extension
  - entering before signal confirmation

3. `structure_selection_failure`

- signal may have been right, but the chosen option structure was wrong
- examples:
  - single-leg where defined-risk spread was better
  - wrong DTE
  - wrong delta target

4. `exit_management_failure`

- entry was acceptable, but the trade-management logic destroyed expectancy
- examples:
  - stop too loose
  - profit target too far
  - giveback after favorable excursion

5. `sizing_or_portfolio_pressure`

- loss was amplified by sizing or correlated pile-on
- examples:
  - too many same-family exposures
  - too much sleeve concentration in one market condition

6. `liquidity_or_slippage_failure`

- strategy edge was swamped by spread, fill quality, or fees
- examples:
  - poor fills versus modeled midpoint
  - thin same-day options

7. `broker_or_runner_anomaly`

- execution behavior or reconciliation quality invalidated the trade as a normal teaching sample
- examples:
  - residual positions
  - broker/local cashflow mismatch
  - missing audit coverage

8. `data_or_signal_defect`

- the trade was triggered by stale, bad, or misclassified data or signal logic

9. `event_gap_or_exogenous_shock`

- the trade was overwhelmed by a discontinuous move that was not reasonably captured by normal intraday assumptions

## Required Artifacts

Loser-trade analysis is not governed unless the following exist:

- broker-order audit
- broker account-activity audit
- ending broker-position snapshot
- shutdown reconciliation
- session review artifact
- session evidence contract verdict
- session teaching gate verdict
- intraday risk-incident packet when applicable
- release/certification/promotion stamp for the runner used
- market-context dataset around entry and exit

## Required Trade Fields

Every analyzed trade should carry at least:

- `trade_id`
- `session_date`
- `strategy_id`
- `family_id`
- `underlying_symbol`
- `structure_class`
- `timing_profile`
- `signal_name`
- `entry_timestamp`
- `exit_timestamp`
- `hold_minutes`
- `entry_reason`
- `exit_reason`
- `planned_risk_fraction`
- `max_contracts`
- `actual_contracts`
- `entry_fill_price_local`
- `exit_fill_price_local`
- `entry_fill_price_broker`
- `exit_fill_price_broker`
- `broker_local_cashflow_diff`
- `fees_and_regulatory_costs`
- `slippage_vs_midpoint_entry`
- `slippage_vs_midpoint_exit`
- `spread_width_entry`
- `spread_width_exit`
- `max_favorable_excursion`
- `max_adverse_excursion`
- `realized_pnl`
- `realized_r_multiple`
- `market_regime_label`
- `volatility_context`
- `session_block_or_halt_state`
- `runner_release_id`
- `runner_capability_epoch`
- `teaching_gate_status`
- `evidence_contract_status`

## Winner-Loser Comparison Rule

Losers should not be studied in isolation.

Every loser review should compare the loss against:

- winners from the same strategy when possible
- winners from the same family and regime bucket when strategy sample is still small
- same-daypart peer trades
- same-underlying peer trades

Required comparison dimensions:

- fill quality
- spread width
- entry timing relative to move
- excursion profile
- exit discipline
- portfolio crowding

## Governance Actions From Findings

### Calibration

Use repeated loss findings to adjust:

- slippage envelopes
- liquidity assumptions
- stop-loss and target defaults
- sizing ceilings
- allowed dayparts for a strategy class

Calibration rule:

- do not recalibrate from one session
- require either:
  - 2 trusted sessions with the same loss pattern, or
  - 5 completed trades with the same primary loss class in trusted evidence

### Hold

Put a strategy or family on `hold` when:

- losses are explainable but unresolved
- evidence quality is good enough to trust the diagnosis
- the issue looks fixable without a full ban

### Kill

Kill a strategy when:

- trusted evidence shows negative after-cost expectancy
- the same primary loss class keeps recurring after attempted calibration
- structure selection or regime fit is fundamentally poor

### Quarantine

Quarantine immediately when:

- evidence contract is `gapped` or `review_required`
- teaching gate is not trusted
- broker/local economics drift is material
- residual positions or execution anomalies contaminated the sample

Quarantine is about evidence integrity first, profitability second.

## Feed Into Unlock Policy

Loser-trade findings should affect unlock policy in these ways:

- repeated `liquidity_or_slippage_failure` blocks more aggressive same-day or convexity profiles
- repeated `structure_selection_failure` can hold single-leg profiles while defined-risk alternatives are researched
- any `broker_or_runner_anomaly` removes the affected session from automatic learning
- repeated `sizing_or_portfolio_pressure` should tighten portfolio-wide ceilings before unlocking broader breadth

## Feed Into Promotion Discipline

Promotion packets should include:

- dominant loser class by strategy
- dominant loser class by family
- unresolved anomaly count
- after-cost loser frequency by recency bucket
- whether the loser pattern is getting better, flat, or worse

No strategy should promote on gross PnL alone if the loss taxonomy says the edge is fragile or misclassified.
