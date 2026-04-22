# Execution Calibration Registry

This guide defines the institutional execution-calibration layer for the project.

Primary builder:
- `cleanroom/code/qqq_options_30d_cleanroom/build_execution_calibration_registry.py`

Generated artifacts:
- `docs/execution_calibration/execution_calibration_registry.json`
- `docs/execution_calibration/execution_calibration_registry.md`
- `docs/execution_calibration/execution_calibration_registry.csv`
- `docs/execution_calibration/execution_calibration_handoff.json`
- `docs/execution_calibration/execution_calibration_handoff.md`

## Objective

The family registry tells us what strategy surface exists.

The tournament profile registry tells us which governed research cycles exist.

The execution calibration registry tells us what the paper runner has actually experienced in fills, guardrails, exits, and loss clusters, so the backtester can learn from real execution behavior instead of drift toward optimistic assumptions.

The session reconciliation registry now sits in front of it. That means execution calibration is expected to learn only from session bundles that are trusted enough for policy use, instead of letting review-required sessions quietly loosen research assumptions.

## What It Reads

From the execution repo:
- `reports/multi_ticker_portfolio/runs/*/multi_ticker_portfolio_session_summary.json`
- `reports/multi_ticker_portfolio/runs/*/multi_ticker_portfolio_session_summary_trade_reconciliation.csv`
- `reports/multi_ticker_portfolio/runs/*/multi_ticker_portfolio_session_summary_completed_trades.csv`
- `reports/multi_ticker_portfolio/runs/*/multi_ticker_portfolio_session_summary_broker_order_audit.csv`
- `reports/multi_ticker_portfolio/runs/*/multi_ticker_portfolio_session_summary_ending_broker_positions.csv`
- `reports/multi_ticker_portfolio/runs/*/trade_reconciliation_events.json`
- `reports/multi_ticker_portfolio/state/session_*.json`

## Institutional Use

Refresh this registry before major nightly research cycles so the operator can:
- tighten fill assumptions when live entry friction is worse than expected
- identify opening-window execution pressure
- spot loss clusters that deserve challenger pressure
- surface combo-exit reconciliation pressure such as broker-status mismatches, unmatched local orders, partial fills, and residual broker positions
- keep guardrail behavior visible in the control plane

Then build the execution calibration handoff so the nightly operator has a concise policy posture, not just raw metrics.

That handoff is not just advisory anymore. The cleanroom now consumes it in four places:
- the selector in `cleanroom/code/qqq_options_30d_cleanroom/run_multiticker_cleanroom_portfolio.py` tightens regime thresholds, minimum trade-count requirements, and risk-cap grids when live Alpaca evidence says fills and guardrails are running hot
- the fill model in `cleanroom/code/qqq_options_30d_cleanroom/backtest_qqq_option_strategies.py` raises entry and exit slippage multipliers in a governed, phase-aware way so the simulator itself becomes more conservative under the same posture
- the deterministic fill-capacity layer in that same cleanroom stack can now reject obviously unfillable signals and cap requested size when combo complexity and weak-leg liquidity say the market would not reasonably fill the full request
- the exit path can now degrade from a clean combo exit into a cleanup-style exit when liquidity suggests the full position would not clear cleanly at the scheduled combo mark
- the operator policy layer can now keep combo-heavy profiles on a tighter leash when upgraded runner bundles show reconciliation pressure or partial-fill stress in the broker-order audit

Primary handoff builder:
- `cleanroom/code/qqq_options_30d_cleanroom/build_execution_calibration_handoff.py`

Session-trust inputs:
- `docs/session_reconciliation/session_reconciliation_registry.json`
- `docs/session_reconciliation/session_reconciliation_handoff.json`

## Important Limitation

The current runner artifacts are much stronger on entry-side calibration than exit-side slippage calibration.

That means:
- entry-fill calibration is actionable today
- broker-order audit and ending-position telemetry are now useful for reconciliation pressure and cleanup realism
- exit-side price slippage modeling should still stay conservative until expected exit pricing and exit slippage are captured more consistently

The registry should surface that limitation clearly instead of pretending we have better evidence than we do.

## Refresh Command

```powershell
python "C:\Users\rabisaab\Downloads\CodexAlpacaTest-TradeMigratyion\cleanroom\code\qqq_options_30d_cleanroom\build_execution_calibration_registry.py"
python "C:\Users\rabisaab\Downloads\CodexAlpacaTest-TradeMigratyion\cleanroom\code\qqq_options_30d_cleanroom\build_execution_calibration_handoff.py"
```

If the runner repo is not in the default sibling location, pass it explicitly:

```powershell
python "C:\Users\rabisaab\Downloads\CodexAlpacaTest-TradeMigratyion\cleanroom\code\qqq_options_30d_cleanroom\build_execution_calibration_registry.py" --runner-repo-root "C:\path\to\codexalpaca_repo"
```
