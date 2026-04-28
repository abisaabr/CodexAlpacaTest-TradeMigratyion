# AAPL Bounded Validation Launch Gate

## State

- Packet id: `gcp_research_aapl_bounded_validation_launch_gate_20260428`
- State: `ready_for_exclusive_window_operator_decision`
- Broker-facing session started: `false`
- Exclusive window armed: `false`
- Live manifest effect: `none`
- Risk policy effect: `none`
- Sanctioned execution path: `vm-execution-paper-01`

This packet does not authorize trading. It records that the AAPL candidate has cleared research review, adversarial stress, runtime-config schema validation, and no-order VM startup preflight.

## Candidate

- Symbol: `AAPL`
- Candidate variant: `b150__aapl__long_call__wide_reward__exit_360__liq_baseline`
- Strategy: `aapl__governed_validation__trend_long_call_next_expiry_wide_reward_exit360`
- Runtime config source: `docs/gcp_foundation/gcp_research_aapl_bounded_validation_runtime_config.yaml`
- VM runtime config: `/opt/codexalpaca/codexalpaca_repo/config/aapl_bounded_validation_candidate.yaml`
- Runtime config SHA-256: `d5fefd9540b8a0483f443b368fa7a1569653624c353d040c57d3d907ed3bc5fd`

## Current Gates

- Phase26 research review: `passed`
- Phase27 adversarial stress: `passed`
- Runner runtime-config schema: `passed`
- VM no-order startup preflight: `passed`
- Broker positions at preflight: `0`
- Open orders at preflight: `0`
- Post-session assimilation path: `prepared`
- Exclusive window: `not_armed`
- Broker-facing authorization: `not_authorized`

## Evidence Assimilation Path

The AAPL bounded config writes to an AAPL-specific runner path:

```text
/opt/codexalpaca/codexalpaca_repo/reports/multi_ticker_portfolio/aapl_bounded_validation/runs
/opt/codexalpaca/codexalpaca_repo/reports/multi_ticker_portfolio/aapl_bounded_validation/state
```

After any authorized bounded paper session, copy those VM outputs into:

```text
C:\Users\abisa\Downloads\codexalpaca_runtime\aapl_bounded_validation\runs
C:\Users\abisa\Downloads\codexalpaca_runtime\aapl_bounded_validation\state
```

Then run post-session assimilation with `-RuntimeRoot "C:\Users\abisa\Downloads\codexalpaca_runtime\aapl_bounded_validation"` so the control-plane builders consume the AAPL-specific evidence bundle.

## Required Session Artifacts

- `multi_ticker_portfolio_session_summary.json`
- `multi_ticker_portfolio_session_summary_completed_trades.csv`
- `multi_ticker_portfolio_session_summary_trade_reconciliation.csv`
- `multi_ticker_portfolio_session_summary_trade_reconciliation_events.csv`
- `multi_ticker_portfolio_session_summary_broker_order_audit.csv`
- `multi_ticker_portfolio_session_summary_broker_account_activities.csv`
- `multi_ticker_portfolio_session_summary_ending_broker_positions.csv`

## Commands

Rerun no-order preflight immediately before any launch decision:

```bash
gcloud compute ssh vm-execution-paper-01 --project codexalpaca --zone us-east1-b --tunnel-through-iap --command "cd /opt/codexalpaca/codexalpaca_repo && ./.venv/bin/python scripts/run_multi_ticker_portfolio_paper_trader.py --portfolio-config config/aapl_bounded_validation_candidate.yaml --no-submit-paper-orders --startup-preflight"
```

Broker-facing bounded session command, only after an explicit exclusive window is armed:

```bash
gcloud compute ssh vm-execution-paper-01 --project codexalpaca --zone us-east1-b --tunnel-through-iap --command "cd /opt/codexalpaca/codexalpaca_repo && ./.venv/bin/python scripts/run_multi_ticker_portfolio_paper_trader.py --portfolio-config config/aapl_bounded_validation_candidate.yaml --submit-paper-orders"
```

Copy VM evidence to the local AAPL runtime root after the session:

```powershell
$root='C:\Users\abisa\Downloads\codexalpaca_runtime\aapl_bounded_validation'
New-Item -ItemType Directory -Force $root | Out-Null
gcloud compute scp --recurse vm-execution-paper-01:/opt/codexalpaca/codexalpaca_repo/reports/multi_ticker_portfolio/aapl_bounded_validation/runs $root --project codexalpaca --zone us-east1-b --tunnel-through-iap
gcloud compute scp --recurse vm-execution-paper-01:/opt/codexalpaca/codexalpaca_repo/reports/multi_ticker_portfolio/aapl_bounded_validation/state $root --project codexalpaca --zone us-east1-b --tunnel-through-iap
```

Run post-session assimilation:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "<control-plane-root>\cleanroom\code\qqq_options_30d_cleanroom\launch_post_session_assimilation.ps1" -ControlPlaneRoot "<control-plane-root>" -RunnerRepoRoot "C:\Users\abisa\Downloads\codexalpaca_repo_gcp_lease_lane_refreshed" -RuntimeRoot "C:\Users\abisa\Downloads\codexalpaca_runtime\aapl_bounded_validation" -MirrorToGcs
```

## Do Not Do

- Do not run the broker-facing session until the exclusive window is explicitly armed.
- Do not overwrite the live manifest.
- Do not change risk policy.
- Do not relax the fill gate.
- Do not count preflight as a trusted validation session.
- Do not commit raw session outputs.
