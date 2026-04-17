Open `C:\Users\<you>\Downloads\codexalpaca_repo` and treat this as the main live repo. Also inspect the sibling repo `C:\Users\<you>\Downloads\CodexAlpacaTest-TradeMigratyion` for migration payloads, cleanroom scripts, legacy strategy assets, docs, and restore helpers.

Goal:
- fully set up this Windows machine to run the multi-ticker paper trader safely
- restore the public-safe runtime state
- restore the cleanroom research code and summaries
- harden the machine for safe takeover
- verify the runner, health check, close guard, and failover behavior

Constraints:
- do not change strategy logic or risk settings unless required to fix a real operational bug
- do not assume OneDrive is available
- use the local shared-drive lease path I provide or preserve the current configured lease path if it is already valid
- if secrets are missing, tell me exactly which ones I still need to provide locally

Work plan:
1. Inspect both repos and summarize what is already present.
2. In `CodexAlpacaTest-TradeMigratyion`, run `scripts\\RESTORE_PUBLIC_MIGRATION.ps1` so the public-safe runtime state is restored into `codexalpaca_repo` and the cleanroom code is restored beside it.
3. In `codexalpaca_repo`, run the Windows native setup path, not Docker.
4. Verify the Python environment, dependencies, `doctor.py`, tests, and scheduled-task install scripts.
5. Confirm the machine has:
   - paper trader task
   - hourly health check task
   - EOD close guard task
   - ownership lease configured
   - ntfy configured if possible
6. Verify the standby failover preflight and make sure this machine can safely act as standby or active owner.
7. Inspect the restored runtime session state, health snapshot, and reports so the machine is aware of the latest known paper-trader state.
8. Inspect the restored cleanroom code, summary bundle, and legacy strategy assets so the research environment is usable even before data is redownloaded.
9. If safe operational issues exist, fix them directly.
10. Do not leave the setup half-finished. Carry it through to a clear ready/not-ready verdict.

Required deliverables:
- a readiness verdict for live paper-trader takeover
- exact remaining local secrets or manual steps, if any
- the exact command to run a small cleanroom ticker batch
- the exact command to run the standby failover check
- the exact command to run the health check
- confirmation that scheduled tasks are installed and correct
- confirmation that the machine label is unique and the lease path is correct

When you report back, organize the answer into:
- Ready State
- Remaining Gaps
- Exact Commands
- Any Safe Fixes You Applied
