# Included Assets

This repo includes the safe subset we can move into GitHub without shipping raw options data.

## Runtime
- `runtime/public_runtime_migration_20260417.zip`
  - Public-safe runtime bundle created with `--skip-env`
  - Includes session state, run folder, and health snapshot
  - Does not include the local `.env`

## Cleanroom
- `cleanroom/code/qqq_options_30d_cleanroom/`
  - Top-level Python scripts from the cleanroom workspace
- `cleanroom/qqq_options_30d_cleanroom_summaries_20260417.zip`
  - Summary CSV/JSON/MD/TXT/LOG outputs
  - Excludes parquet, gzipped raw bars, contracts, dense minute data, and bundle zips
- `cleanroom/manifest.json`
- `cleanroom/README.txt`
- `cleanroom/RESTORE_RESEARCH_WORKSPACE.ps1`

## Safe archive snapshots
- `archives/_alpaca_mcp_pkg.zip`
- `archives/_alpaca_mcp_pkg_archive_20260406.zip`
- `archives/alpaca_lab.zip`
- `archives/alpaca_paper_handoff_20260406_archive_20260406.zip`
- `archives/alpaca-strategy-research_20260415.zip`
- `archives/data.zip`
- `archives/downloads_trading_root_files.zip`
- `archives/reports.zip`
- `archives/reports_20260415.zip`
- `archives/scripts.zip`

## Docs
- `docs/NEW_MACHINE_CODEX_PROMPTS.md`
- `docs/PORTABLE_DEPLOYMENT.md`

Assumption used for this split:
- Strategy code, summary tables, reports, manifests, and helper scripts are okay to publish.
- Raw or reconstructed options market data is not.
