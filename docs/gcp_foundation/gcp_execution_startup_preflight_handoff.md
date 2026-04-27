# GCP Execution Startup Preflight Handoff

Generated: 2026-04-27T11:12:00-04:00

## Status

- Gate state: `blocking_until_passed`
- Sanctioned VM: `vm-execution-paper-01`
- Runner commit on VM: `cd5abfb0211757d7a1168dee160851b0c3448c71`
- Preflight command status: `available`
- Latest preflight result: `startup_preflight_failed`
- Latest blocker: `IWM stock data stale at 189s`; `JPM stock data stale at 189s`
- Broker positions in latest preflight: `0`
- Underlyings checked: `21`

## Operator Rule

Run the read-only startup preflight immediately before any exclusive-window arm. Do not arm the window, and do not launch the broker-facing paper runner, unless the result is `startup_preflight_passed`.

## Command

```bash
cd /opt/codexalpaca/codexalpaca_repo
./.venv/bin/python scripts/run_multi_ticker_portfolio_paper_trader.py --portfolio-config config/multi_ticker_paper_portfolio.yaml --startup-preflight
```

## Durable Evidence

- `gs://codexalpaca-control-us/gcp_foundation/trusted_validation_attempts/20260427/startup_preflight_20260427T1510Z.json`
- `gs://codexalpaca-control-us/gcp_foundation/trusted_validation_attempts/20260427/startup_preflight_20260427T1510Z.stderr`

## Next Safe Action

Wait and rerun the startup preflight. If it passes, refresh the normal pre-arm packet and only then consider arming a bounded exclusive execution window. If it continues to fail on intermittent IEX freshness for otherwise liquid symbols, treat that as a data-feed readiness issue and fix it through governance rather than weakening the live risk gate ad hoc.
