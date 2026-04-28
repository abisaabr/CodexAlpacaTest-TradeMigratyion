# AAPL Bounded Validation Operator Checklist

## Status

- State: `prepared_not_armed`
- Broker facing: `false`
- Live manifest effect: `none`
- Risk policy effect: `none`
- Candidate manifest: `docs/gcp_foundation/gcp_research_aapl_bounded_validation_manifest_candidate.yaml`
- Candidate: `AAPL` `b150__aapl__long_call__wide_reward__exit_360__liq_baseline`
- Sanctioned execution path: `vm-execution-paper-01`

## Preconditions

Do not run broker-facing paper validation unless all items are true:

- Exclusive execution window is explicitly armed.
- Operator has confirmed no other machine or automation is using the shared paper account.
- `vm-execution-paper-01` is reachable.
- Startup preflight passes with the candidate config.
- The candidate config is copied to the runner repo as a bounded validation config, not as the live manifest.
- The runner remains in paper mode only.
- Post-session assimilation is ready before launch.

## Candidate Config Handling

The control-plane manifest candidate is intentionally stored under `docs/gcp_foundation/`, not under the runner's live `config/` tree. If a bounded session is explicitly authorized later, copy it into the sanctioned VM runner checkout as a temporary validation config such as:

```bash
/opt/codexalpaca/codexalpaca_repo/config/aapl_bounded_validation_candidate.yaml
```

Do not overwrite:

- `config/multi_ticker_paper_portfolio.yaml`
- `config/strategy_manifests/multi_ticker_portfolio_live.yaml`
- `config/risk_controls/multi_ticker_portfolio.yaml`

## Preflight Command

Use preflight first. This command is non-broker-facing:

```bash
cd /opt/codexalpaca/codexalpaca_repo
./.venv/bin/python scripts/run_multi_ticker_portfolio_paper_trader.py \
  --portfolio-config config/aapl_bounded_validation_candidate.yaml \
  --startup-preflight
```

Expected result:

- startup check status is `passed`
- no paper orders are submitted
- ownership lease config is valid
- one AAPL strategy is loaded
- risk caps reflect the bounded validation config

## Broker-Facing Paper Command Template

Do not run this until the exclusive execution window is armed and the operator explicitly authorizes the session:

```bash
cd /opt/codexalpaca/codexalpaca_repo
./.venv/bin/python scripts/run_multi_ticker_portfolio_paper_trader.py \
  --portfolio-config config/aapl_bounded_validation_candidate.yaml \
  --submit-paper-orders
```

## Required Evidence After Any Session

- Broker order audit.
- Broker account-activity audit.
- Ending broker-position snapshot.
- Shutdown reconciliation.
- Completed trade table with broker/local cashflow comparison.
- Loser-trade classification coverage.
- Explicit flatness/reconciliation verdict.
- Post-session assimilation packet.

## Stop Conditions

Stop or do not launch if any of these occur:

- Exclusive execution window is not armed.
- Preflight fails.
- Paper account has unexpected positions before launch.
- Another runtime holds or contests the execution lease.
- Broker/local reconciliation is unavailable.
- Candidate config differs from the control-plane packet without review.

## Governance Rule

This checklist prepares a bounded validation path. It does not promote the strategy, modify live strategy selection, change risk policy, or authorize trading.
