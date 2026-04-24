# GCP Execution Position Mismatch Incident Handoff

As of: 2026-04-24T11:28:32-04:00

Status: mitigated_flat_vm_patched

## Summary

Paper-runner mismatch alerts were traced to two execution-safety problems:

- A stale local Windows desktop runner from the April 22 staged release was active while the sanctioned VM path was not observed running from this machine.
- Residual paper broker option positions existed and the cleanup path could submit spread-leg close orders in an unsafe order.

The local stale runner was stopped. Legacy local Windows scheduled tasks pointing at the April 22 staged release were disabled. Residual paper broker option positions were flattened under explicit incident remediation authority. A read-only broker check after remediation reported zero positions and zero open orders.

The sanctioned VM runner source has now been patched to runner commit `f008006` using a Git archive overlay with backup. IAP SSH verified no active runner process before the deployment, and no broker-facing session was started.

## Root Cause

Unexpected-position cleanup used broker API position order. For option spreads, that can remove protective long legs before buying back short legs. Alpaca can reject that sequence because the short leg then becomes insufficiently covered or cash-secured, which produced the observed cleanup failure mode.

## Durable Fix

Runner branch: `codex/qqq-paper-portfolio`

Runner commit: `f008006`

Change: residual option cleanup now prioritizes short-leg buy-to-close orders before protective long-leg sell-to-close orders in both known-trade cleanup and unexpected broker-position cleanup.

## Validation

- Local targeted runner suite: `60 passed` with `python -m pytest -q tests/test_multi_ticker_portfolio.py`
- Local full runner suite: `140 passed` with `python -m pytest -q`
- VM targeted runner suite: `60 passed` with `.venv/bin/python -m pytest -q tests/test_multi_ticker_portfolio.py`
- VM full runner suite: `140 passed` with `.venv/bin/python -m pytest -q`
- Broker flat check: `position_count=0`, `open_order_count=0`
- VM process check: IAP SSH access works; no active runner process was observed before deployment
- VM source stamp: `runner_commit=f0080066c68d883286f4cb1b9c9e0edc601adf8d`
- VM source fingerprint: `source_fingerprint_matched`

## Governance Notes

- No live-trading path was enabled.
- No strategy selection or risk policy was changed.
- No live manifest was modified.
- No raw session exhaust or raw trade log was committed.

## Next Safe Actions

1. Keep runner commit `f008006` on `vm-execution-paper-01` before any next broker-facing paper session.
2. Re-run the VM source/process-stamp check immediately before arming any exclusive execution window.
3. Keep the legacy local scheduled tasks disabled and do not use the April 22 staged release as an execution path.
