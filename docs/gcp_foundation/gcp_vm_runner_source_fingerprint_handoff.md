# GCP VM Runner Source Fingerprint Status

## Snapshot

- Generated at: `2026-04-24T10:08:55.795549-04:00`
- Status: `source_fingerprint_mismatch`
- VM name: `vm-execution-paper-01`
- VM runner path: `/opt/codexalpaca/codexalpaca_repo`
- Local runner branch: `codex/qqq-paper-portfolio`
- Local runner commit: `f2b9bae7b2af26eefc086189a244e4d5a6c81a83`
- Safe to write source stamp: `False`

## Comparison

- Local file count: `97`
- VM file count: `93`
- Matching file count: `40`
- Changed file count: `53`
- Local-only file count: `4`
- VM-only file count: `0`

## Mismatch Samples

### Changed

- `.env.example`
- `Dockerfile`
- `README.md`
- `alpaca_lab/brokers/alpaca.py`
- `alpaca_lab/config.py`
- `alpaca_lab/execution/__init__.py`
- `alpaca_lab/execution/failover.py`
- `alpaca_lab/execution/migration.py`
- `alpaca_lab/execution/ownership.py`
- `alpaca_lab/multi_ticker_portfolio/__init__.py`
- `alpaca_lab/multi_ticker_portfolio/config.py`
- `alpaca_lab/multi_ticker_portfolio/signals.py`
- `alpaca_lab/multi_ticker_portfolio/trader.py`
- `alpaca_lab/notifications/__init__.py`
- `alpaca_lab/notifications/discord.py`
- `alpaca_lab/notifications/email.py`
- `alpaca_lab/notifications/ntfy.py`
- `alpaca_lab/qqq_portfolio/__init__.py`
- `alpaca_lab/qqq_portfolio/config.py`
- `alpaca_lab/qqq_portfolio/greeks.py`
- `alpaca_lab/qqq_portfolio/signals.py`
- `alpaca_lab/qqq_portfolio/trader.py`
- `alpaca_lab/research_bundle.py`
- `alpaca_lab/strategies/stock_momentum.py`
- `config/qqq_paper_portfolio.yaml`

### Local-only

- `scripts/build_option_aware_research_queue.py`
- `scripts/run_gcp_research_wave.py`
- `scripts/run_option_aware_research_backtest.py`
- `scripts/summarize_gcp_research_runs.py`

### VM-only

- none

## Issues

- `error` `vm_runner_source_fingerprint_mismatch`: The VM runner source fingerprint does not match the canonical local runner checkout.

## Operator Read

- This is a source-fingerprint comparison only; it does not start trading or change the VM.
- A source stamp is defensible only when the VM fingerprint matches the intended runner checkout.
- A mismatch means the VM may still run, but the session should not be treated as source-attested trusted evidence.

## Next Actions

- Do not write a source stamp while the fingerprint mismatch remains.
- Reconcile the VM runner deployment to the canonical runner checkout or intentionally select a different published runner commit.
- Recapture the VM manifest and rebuild this packet before arming a trusted execution window.
