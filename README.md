# CodexAlpacaTest-TradeMigratyion

This repo is a GitHub-only migration helper for moving the paper-trader setup to a new machine without carrying raw options datasets.

Primary codebase:
- [abisaabr/CodexAlpacaTest-Trade](https://github.com/abisaabr/CodexAlpacaTest-Trade)

What this repo contains:
- A public-safe runtime handoff bundle with no `.env`
- Cleanroom research scripts
- A formal GitHub-backed strategy-family registry for cataloging family coverage, live-book overlay, and next research priorities
- An institutional operating blueprint for machine roles, automation boundaries, and champion/challenger governance
- A nightly operator playbook and prompt for running the full research-to-handoff cycle
- A top-level nightly operator entrypoint for governed overnight research-to-handoff execution
- The current cleanroom tournament conveyor scripts for chained family-expansion runs
- Cleanroom run-lineage support so large research batches emit `run_manifest.json` plus an append-only `run_registry.jsonl`
- Cleanroom run-registry reporting so operators can summarize run history, lineage, ticker states, and terminal outcomes with `build_run_registry_report.py`
- Agent-sharding and operating-model docs for running the research conveyor with clear ownership and promotion gates
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
