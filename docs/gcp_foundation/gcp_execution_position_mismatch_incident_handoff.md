# GCP Execution Position Mismatch Incident Handoff

As of: 2026-04-24T11:21:56-04:00

Status: mitigated_flat

## Summary

Paper-runner mismatch alerts were traced to two execution-safety problems:

- A stale local Windows desktop runner from the April 22 staged release was active while the sanctioned VM path was not observed running from this machine.
- Residual paper broker option positions existed and the cleanup path could submit spread-leg close orders in an unsafe order.

The local stale runner was stopped. Legacy local Windows scheduled tasks pointing at the April 22 staged release were disabled. Residual paper broker option positions were flattened under explicit incident remediation authority. A read-only broker check after remediation reported zero positions and zero open orders.

## Root Cause

Unexpected-position cleanup used broker API position order. For option spreads, that can remove protective long legs before buying back short legs. Alpaca can reject that sequence because the short leg then becomes insufficiently covered or cash-secured, which produced the observed cleanup failure mode.

## Durable Fix

Runner branch: `codex/qqq-paper-portfolio`

Runner commit: `f008006`

Change: residual option cleanup now prioritizes short-leg buy-to-close orders before protective long-leg sell-to-close orders in both known-trade cleanup and unexpected broker-position cleanup.

## Validation

- Targeted runner suite: `60 passed` with `python -m pytest -q tests/test_multi_ticker_portfolio.py`
- Full runner suite: `140 passed` with `python -m pytest -q`
- Broker flat check: `position_count=0`, `open_order_count=0`
- VM process check: not verified from this local machine because `gcloud compute ssh vm-execution-paper-01` timed out

## Governance Notes

- No live-trading path was enabled.
- No strategy selection or risk policy was changed.
- No live manifest was modified.
- No raw session exhaust or raw trade log was committed.

## Next Safe Actions

1. Pull runner commit `f008006` onto `vm-execution-paper-01` before any next broker-facing paper session.
2. Re-run the VM source/process-stamp check once SSH connectivity is available.
3. Keep the legacy local scheduled tasks disabled and do not use the April 22 staged release as an execution path.
