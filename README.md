# CodexAlpacaTest-TradeMigratyion

This repo is a GitHub-only migration helper for moving the paper-trader setup to a new machine without carrying raw options datasets.

Primary codebase:
- [abisaabr/CodexAlpacaTest-Trade](https://github.com/abisaabr/CodexAlpacaTest-Trade)

What this repo contains:
- A public-safe runtime handoff bundle with no `.env`
- Cleanroom research scripts
- The current cleanroom tournament conveyor scripts for chained family-expansion runs
- Cleanroom summary outputs without raw option bars
- Legacy strategy scripts, reports, and CSV research artifacts extracted from archive bundles
- Setup docs and a restore script for the new machine

What this repo does not contain:
- Raw options minute data
- Large parquet datasets
- Full backfill archives
- Local secrets

Suggested usage:
1. Clone `abisaabr/CodexAlpacaTest-Trade` to the new machine.
2. Clone this repo beside it.
3. Run [`scripts/RESTORE_PUBLIC_MIGRATION.ps1`](./scripts/RESTORE_PUBLIC_MIGRATION.ps1).
4. Fill `.env` locally in the main repo.
5. Let Codex finish the machine setup using [`docs/EXHAUSTIVE_NEW_MACHINE_PROMPT.md`](./docs/EXHAUSTIVE_NEW_MACHINE_PROMPT.md).

Note:
- The repo name contains a typo, `Migratyion`, because that is the repository that already existed on GitHub.
