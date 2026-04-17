# CodexAlpacaTest-TradeMigratyion

This repo is a temporary migration landing zone for the multi-ticker paper trader and the cleanroom research workspace.

What is here:
- Public-safe runtime handoff state with no `.env`
- Cleanroom research code and summary metadata
- Small and medium archive snapshots that do not contain raw options minute data
- Operator docs and copy/paste Codex prompts for the new machine

What is not here:
- Raw options datasets
- Large parquet backfills
- Full cleanroom snapshot with minute-bar option data
- Local secrets

Primary code repo:
- [abisaabr/CodexAlpacaTest-Trade](https://github.com/abisaabr/CodexAlpacaTest-Trade)

Quick use:
1. Clone this repo.
2. Clone `abisaabr/CodexAlpacaTest-Trade` beside it.
3. Run [`scripts/RESTORE_PUBLIC_MIGRATION.ps1`](./scripts/RESTORE_PUBLIC_MIGRATION.ps1) to restore the public-safe runtime state and the cleanroom code-only workspace.
4. Fill secrets locally in the main repo `.env`.
5. Follow [`docs/NEW_MACHINE_CODEX_PROMPTS.md`](./docs/NEW_MACHINE_CODEX_PROMPTS.md) and [`docs/PORTABLE_DEPLOYMENT.md`](./docs/PORTABLE_DEPLOYMENT.md).

Important note:
- The repo name contains a typo: `Migratyion`. I kept it as-is to match the repository that already exists.
