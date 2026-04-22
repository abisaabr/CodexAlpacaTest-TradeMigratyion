# CodexAlpacaTest-TradeMigratyion

This repo is a GitHub-only migration helper for moving the paper-trader setup to a new machine without carrying raw options datasets.

Primary codebase:
- [abisaabr/CodexAlpacaTest-Trade](https://github.com/abisaabr/CodexAlpacaTest-Trade)

What this repo contains:
- A public-safe runtime handoff bundle with no `.env`
- Cleanroom research scripts
- A formal GitHub-backed strategy-family registry for cataloging family coverage, live-book overlay, and next research priorities
- A machine-readable agent governance registry for split axis, machine ownership, and production-state permissions
- A machine-readable tournament profile registry for approved active and planned institutional research cycles
- A machine-readable tournament profile handoff packet so the nightly operator can resolve the active cycle from execution posture instead of prompt drift
- A machine-readable tournament unlock registry and handoff packet so the operator can see what evidence or implementation work is still blocking the next research tier
- A machine-readable tournament unlock workplan and handoff packet so the research plane and execution plane each get one explicit next mission
- A machine-readable execution evidence contract and handoff packet so the next paper-runner session can be judged against an explicit unlock-worthy evidence checklist
- A machine-readable execution calibration registry for feeding paper-runner fill, guardrail, and loss evidence back into the research/control planes
- A concise execution calibration handoff packet so nightly operators can act on posture and policy guidance instead of raw execution metrics alone
- A machine-readable repo update registry and handoff packet so the new machine can systematically check GitHub drift before paper-runner or nightly work
- A runner execution upgrade handoff and Codex prompt for applying current paper-runner improvements on the new machine
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
