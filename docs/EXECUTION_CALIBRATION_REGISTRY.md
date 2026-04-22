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

## What It Reads

From the execution repo:
- `reports/multi_ticker_portfolio/runs/*/multi_ticker_portfolio_session_summary.json`
- `reports/multi_ticker_portfolio/runs/*/multi_ticker_portfolio_session_summary_trade_reconciliation.csv`
- `reports/multi_ticker_portfolio/runs/*/multi_ticker_portfolio_session_summary_completed_trades.csv`
- `reports/multi_ticker_portfolio/runs/*/trade_reconciliation_events.json`
- `reports/multi_ticker_portfolio/state/session_*.json`

## Institutional Use

Refresh this registry before major nightly research cycles so the operator can:
- tighten fill assumptions when live entry friction is worse than expected
- identify opening-window execution pressure
- spot loss clusters that deserve challenger pressure
- keep guardrail behavior visible in the control plane

Then build the execution calibration handoff so the nightly operator has a concise policy posture, not just raw metrics.

Primary handoff builder:
- `cleanroom/code/qqq_options_30d_cleanroom/build_execution_calibration_handoff.py`

## Important Limitation

The current runner artifacts are much stronger on entry-side calibration than exit-side slippage calibration.

That means:
- entry-fill calibration is actionable today
- exit-side modeling should stay conservative until expected exit pricing and exit slippage are captured more consistently

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
