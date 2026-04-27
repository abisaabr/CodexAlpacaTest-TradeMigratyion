# GCP Execution Startup Preflight

## Purpose

The startup preflight is a read-only VM-side gate that runs the paper runner's launch-time readiness checks without entering the trading loop. It is intended to catch market-data freshness, option-inventory, broker-flatness, and open-order blockers before an exclusive execution window is armed.

## Current Rule

Do not arm an exclusive execution window and do not start a broker-facing paper session unless the latest `--startup-preflight` result from `vm-execution-paper-01` is `startup_preflight_passed`.

The preflight must be run immediately before any launch attempt because IEX stock-bar freshness can change within minutes.

## Command

Run from the sanctioned VM:

```bash
cd /opt/codexalpaca/codexalpaca_repo
./.venv/bin/python scripts/run_multi_ticker_portfolio_paper_trader.py \
  --portfolio-config config/multi_ticker_paper_portfolio.yaml \
  --startup-preflight
```

Expected successful result:

```json
{
  "status": "startup_preflight_passed",
  "startup_check_status": "passed",
  "submit_paper_orders": false,
  "broker_cleanup_allowed": false,
  "would_allow_trading": true
}
```

Any non-passed result is a launch blocker. The command exits `43` when the preflight does not pass.

## Safety Properties

- Forces `submit_paper_orders=false`.
- Suppresses broker cleanup during preflight.
- Does not enter the trading loop.
- Does not modify strategy selection, risk policy, or the live manifest.
- Produces machine-readable JSON on stdout.

## April 27 Evidence

- Runner commit deployed to `vm-execution-paper-01`: `cd5abfb0211757d7a1168dee160851b0c3448c71`.
- VM-side startup-preflight tests passed.
- First clean-output VM preflight failed closed with no broker exposure because `IWM` and `JPM` stock bars were stale at 189 seconds against the 180-second gate.
- Evidence mirrored to `gs://codexalpaca-control-us/gcp_foundation/trusted_validation_attempts/20260427/startup_preflight_20260427T1510Z.json`.
