# GCP Execution Trusted Validation Launch Pack

## Snapshot

- Generated at: `2026-04-23T16:14:02.387924-04:00`
- Launch pack state: `awaiting_window_arm`
- Project ID: `codexalpaca`
- VM name: `vm-execution-paper-01`
- Zone: `us-east1-b`
- Runner branch: `codex/qqq-paper-portfolio`
- Runner commit: `a6cf50aa424a51440f5744ec0c634150e82fc7c0`
- Exclusive window status: `awaiting_operator_confirmation`

## Operator Commands

- IAP SSH: `gcloud compute ssh vm-execution-paper-01 --project codexalpaca --zone us-east1-b --tunnel-through-iap`
- Trusted validation launch: `gcloud compute ssh vm-execution-paper-01 --project codexalpaca --zone us-east1-b --tunnel-through-iap --command "cd /opt/codexalpaca/codexalpaca_repo && ./.venv/bin/python scripts/run_multi_ticker_portfolio_paper_trader.py --portfolio-config config/multi_ticker_paper_portfolio.yaml --submit-paper-orders"`
- Post-session assimilation: `powershell -NoProfile -ExecutionPolicy Bypass -File "C:\Users\rabisaab\Downloads\CodexAlpacaTest-TradeMigratyion\cleanroom\code\qqq_options_30d_cleanroom\launch_post_session_assimilation.ps1" -ControlPlaneRoot "C:\Users\rabisaab\Downloads\CodexAlpacaTest-TradeMigratyion" -RunnerRepoRoot "C:\Users\rabisaab\OneDrive\CodexAlpaca\downloads_remaining_20260417\folders\codexalpaca_repo"`

## Required Evidence

- `broker-order audit`
- `broker account-activity audit`
- `ending broker-position snapshot`
- `shutdown reconciliation`
- `completed trade table with broker/local cashflow comparison`

## By-Window Success

- The VM session exits and leaves a fresh runner bundle under the multi_ticker_portfolio reports tree.
- The session leaves the full broker-audited evidence package: order audit, activity audit, ending positions, reconciliation inputs, and broker/local economics comparison.
- Governed post-session assimilation refreshes morning_brief, unlock, workplan, and execution-evidence packets without relaxing policy automatically.
- The refreshed morning brief still matches the evidence honestly, even if the result is to keep blocked profiles blocked.

## Next Actions

- Arm the exclusive execution window first, then use this launch pack unchanged.
- Keep the parallel runtime exception paused or otherwise ruled out for the full session window.
- Once the window is explicit, run the trusted validation launch command and then the assimilation command.
