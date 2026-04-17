# Excluded Assets

These artifacts were left out on purpose.

## Excluded because they are raw options data or data-heavy rebuilds
- `alpaca-market-data-lake.zip`
- `alpaca-stock-strategy-research.zip`
- `cleanroom_research_handoff_20260417_144540.zip`
- `historical_data_downloader_migration_20260417_104734.zip`
- `multi_ticker_alpaca_atm_0_7dte_backfill.zip`
- `qqq_alpaca_atm_0_7dte_backfill.zip`
- `qqq_alpaca_atm_0_7dte_backfill_sanitized_rebuild_source.zip`
- `qqq_alpaca_atm_0_7dte_backfill_with_greeks_clean_rerun.zip`
- `qqq_direct_greeks_oos_subset_20260415.zip`
- `qqq_greeks.zip`
- `qqq_greeks_20260415.zip`
- `qqq_greeks_smoketest.zip`
- `qqq_greeks_smoketest_retry.zip`
- `qqq_greeks_smoketest_retry2.zip`
- `qqq_options_30d_cleanroom.zip`
- `qqq_options_30d_cleanroom_raw_csv_part01_20260415.zip`
- `qqq_options_30d_cleanroom_raw_csv_part02_20260415.zip`
- `qqq_options_30d_cleanroom_remainder_20260415.zip`
- `qqq_options_30d_cleanroom_with_greeks_raw_csv_20260415.zip`
- `qqq_options_30d_cleanroom_with_greeks_remainder_20260415.zip`
- `qqq_options_surface_lab.zip`
- `qqq_sma_options_overnight_tournament.zip`

## Excluded because GitHub is the wrong home for them
- `CodexAlpacaTest-Trade.zip`
  - The code already lives in the main GitHub repo
- Full runtime migration bundle that includes `.env`
  - Kept out to avoid publishing secrets

## Notes
- This repo is meant to be enough for code, docs, runtime state without secrets, and research scaffolding.
- If we need the raw options datasets later, we should move them through a private transfer channel instead of a public GitHub repo.
