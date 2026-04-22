# Runner Execution Upgrade Prompt

```text
Open these sibling folders and use them together:

1. C:\Users\<you>\Downloads\codexalpaca_repo
2. C:\Users\<you>\Downloads\CodexAlpacaTest-TradeMigratyion

Read first:
- docs/INSTITUTIONAL_OPERATING_BLUEPRINT.md
- docs/RUNNER_EXECUTION_UPGRADE_HANDOFF.md

Then act as the execution-plane Codex operator for the paper runner.

In C:\Users\<you>\Downloads\codexalpaca_repo:

1. Fetch `origin/codex/qqq-paper-portfolio`.
2. Verify whether commits `50764cf`, `4292514`, `f6d6168`, `8037710`, `bdd7663`, `1e72e18`, and `3d1de76` are already present.
3. If they are not present on the current local branch, integrate them deliberately from `origin/codex/qqq-paper-portfolio` without changing unrelated strategy logic or risk settings.
4. Verify that the runner now has:
   - combo-native Alpaca `mleg` entry/exit routing in `alpaca_lab/multi_ticker_portfolio/trader.py`
   - Alpaca-aligned option fee modeling in the same file
   - cleanup fallback for not-filled multi-leg combo exits in the same file
   - leg-aware close-order detection for open Alpaca `mleg` exits in the same file
   - broker-position-aware cleanup sizing for partially filled combo exits in the same file
   - a broker-order audit in the session summary output path
   - a broker account-activity audit in the session summary output path
   - an ending broker-position snapshot in the session summary output path
   - runner unlock-baseline metadata in the session summary output path, including the current capability stamp and clean repo state
5. Run `python -m pytest -q`.
6. Summarize:
   - whether the full suite is green
   - whether the runner now supports multi-leg combo execution
   - whether the runner fee model is aligned with Alpaca's current options fee posture
   - whether a not-filled combo exit now degrades into an explicit cleanup path
   - whether open combo close orders and partial-fill cleanup are reconciled safely enough for paper-runner use
   - whether the runner now leaves behind a broker-order audit, broker account-activity audit, and ending broker-position snapshot for post-session reconciliation
   - whether the runner now leaves behind a session-level unlock-baseline stamp that the control plane can trust
   - whether local runner order events, Alpaca order state, and Alpaca account activity reconcile cleanly enough for execution-plane use
   - whether the machine is safe to keep using as the execution-plane paper runner

Hard rules:
- do not change live strategy selection or risk policy in this step
- do not modify the live manifest
- do not start trading as part of this implementation step
- if there is any ambiguity, prefer inspection and reporting over speculative changes
```
