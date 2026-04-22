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
2. Verify whether commits `50764cf`, `4292514`, and `f6d6168` are already present.
3. If they are not present on the current local branch, integrate them deliberately from `origin/codex/qqq-paper-portfolio` without changing unrelated strategy logic or risk settings.
4. Verify that the runner now has:
   - combo-native Alpaca `mleg` entry/exit routing in `alpaca_lab/multi_ticker_portfolio/trader.py`
   - Alpaca-aligned option fee modeling in the same file
   - cleanup fallback for not-filled multi-leg combo exits in the same file
5. Run `python -m pytest -q`.
6. Summarize:
   - whether the full suite is green
   - whether the runner now supports multi-leg combo execution
   - whether the runner fee model is aligned with Alpaca's current options fee posture
   - whether a not-filled combo exit now degrades into an explicit cleanup path
   - whether the machine is safe to keep using as the execution-plane paper runner

Hard rules:
- do not change live strategy selection or risk policy in this step
- do not modify the live manifest
- do not start trading as part of this implementation step
- if there is any ambiguity, prefer inspection and reporting over speculative changes
```
