# Session Reconciliation Registry

Use this registry when the goal is to decide whether recent paper-runner sessions are trustworthy enough to influence research policy, execution calibration, or promotion-style conclusions.

Source builders:
- `cleanroom/code/qqq_options_30d_cleanroom/build_session_reconciliation_registry.py`
- `cleanroom/code/qqq_options_30d_cleanroom/build_session_reconciliation_handoff.py`

Primary generated artifacts:
- `docs/session_reconciliation/session_reconciliation_registry.json`
- `docs/session_reconciliation/session_reconciliation_registry.md`
- `docs/session_reconciliation/session_reconciliation_registry.csv`
- `docs/session_reconciliation/session_reconciliation_handoff.json`
- `docs/session_reconciliation/session_reconciliation_handoff.md`

What it measures:
- whether shutdown reconciliation completed
- whether completed-trade counts reconcile to the session bundle
- whether realized reconciled PnL matches completed-trade economics closely enough
- whether broker-order audit and broker-activity audit were present on traded sessions
- whether broker activity cashflow matches local completed-trade cashflow closely enough when broker activity audit exists
- whether broker/local mismatches, partial fills, cleanup pressure, or residual positions were observed

Trust tiers:
- `trusted`: session is clean enough to influence research and calibration normally
- `caution`: session is usable, but should tighten or qualify policy rather than loosen it
- `review_required`: session should not automatically steer research or promotion decisions until manually checked
- `idle`: no meaningful trading activity to learn from

Institutional use:
- refresh this before or alongside execution calibration
- use it to decide whether recent sessions should tighten research assumptions
- do not let broker/local economics drift sessions loosen tournament selection, fill assumptions, or promotion conclusions
- do not let `review_required` sessions loosen tournament selection, fill assumptions, or promotion conclusions
