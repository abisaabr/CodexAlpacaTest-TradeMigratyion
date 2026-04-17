# Excluded Assets

These artifacts were intentionally kept out of GitHub.

## Raw options and heavy backfills
- `alpaca-market-data-lake.zip`
- `alpaca-stock-strategy-research.zip`
- `cleanroom_research_handoff_20260417_144540.zip`
- `historical_data_downloader_migration_20260417_104734.zip`
- `multi_ticker_alpaca_atm_0_7dte_backfill.zip`
- `qqq_alpaca_atm_0_7dte_backfill.zip`
- `qqq_alpaca_atm_0_7dte_backfill_sanitized_rebuild_source.zip`
- `qqq_alpaca_atm_0_7dte_backfill_with_greeks_clean_rerun.zip`
- `qqq_direct_greeks_oos_subset_20260415.zip`
- `qqq_greeks*.zip`
- `qqq_options_30d_cleanroom*.zip`
- `qqq_options_surface_lab.zip`
- `qqq_sma_options_overnight_tournament.zip`

## Sensitive or unnecessary-for-GitHub artifacts
- Any runtime bundle that includes `.env`
- `CodexAlpacaTest-Trade.zip`
  - The code already lives in the main GitHub repo

## Why
- The new machine can redownload data it needs.
- GitHub is the right home for scripts, strategies, summaries, and setup logic.
- GitHub is the wrong home for raw market data and local secrets.
