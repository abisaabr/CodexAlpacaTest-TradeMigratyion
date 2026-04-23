# GCP Execution VM Runtime Bootstrap Status

## Snapshot

- Generated at: `2026-04-23T14:03:18.055620-04:00`
- Project ID: `codexalpaca`
- VM name: `vm-execution-paper-01`
- Runtime repo root: `C:\Users\rabisaab\OneDrive\CodexAlpaca\downloads_remaining_20260417\folders\codexalpaca_repo`

## Bundle

- Local bundle: `C:\Users\rabisaab\Downloads\CodexAlpacaTest-TradeMigratyion\output\gcp_execution_vm_runtime\codexalpaca_repo_source_vm-execution-paper-01_20260423.zip`
- Backup bucket URI: `gs://codexalpaca-backups-us/bootstrap/2026-04-23/execution-vm/codexalpaca_repo_source_vm-execution-paper-01_20260423.zip`
- Included files: `144`
- Bundle SHA256: `d1959c65354343e2b2a5659636f8725273596d60ffc4b7b60e4c8abc43b53dd7`

## Bootstrap Script

- Local script: `C:\Users\rabisaab\Downloads\CodexAlpacaTest-TradeMigratyion\output\gcp_execution_vm_runtime\execution_vm_runtime_bootstrap_vm-execution-paper-01_20260423.sh`
- Control bucket URI: `gs://codexalpaca-control-us/bootstrap/2026-04-23/foundation-phase2-runtime/execution_vm_runtime_bootstrap_vm-execution-paper-01_20260423.sh`

## Validation Config

- `ALPACA_DATA_FEED`
- `ALPACA_PAPER_TRADE`
- `APCA_API_BASE_URL`
- `DATA_ROOT`
- `DEFAULT_UNDERLYINGS`
- `DRY_RUN`
- `EMAIL_FROM`
- `EMAIL_SMTP_HOST`
- `EMAIL_SMTP_PORT`
- `EMAIL_SUBJECT_PREFIX`
- `EMAIL_TO`
- `EMAIL_USERNAME`
- `EMAIL_USE_STARTTLS`
- `LIVE_TRADING`
- `LOG_LEVEL`
- `MAX_NOTIONAL_PER_TRADE`
- `MAX_OPEN_POSITIONS`
- `MAX_ORDERS_PER_RUN`
- `NTFY_BASE_URL`
- `NTFY_TOPIC`
- `REPORTS_ROOT`
- `REQUEST_TIMEOUT_SECONDS`
- `RETRY_ATTEMPTS`
- `MULTI_TICKER_MACHINE_LABEL`
- `MULTI_TICKER_OWNERSHIP_ENABLED`

## Secret Mappings

- `ALPACA_API_KEY` -> `execution-alpaca-paper-api-key`: `required`, `present_locally`
- `ALPACA_SECRET_KEY` -> `execution-alpaca-paper-secret-key`: `required`, `present_locally`
- `DISCORD_WEBHOOK_URL` -> `notification-discord-webhook-url`: `optional`, `present_locally`
- `NTFY_ACCESS_TOKEN` -> `notification-ntfy-access-token`: `optional`, `pending_locally`
- `EMAIL_PASSWORD` -> `notification-email-password`: `optional`, `pending_locally`

## Next Actions

- Use OS Login and IAP to connect to the validation VM before running the bootstrap script.
- Run the bootstrap script on the VM in validation-only mode and confirm scripts/bootstrap_linux.sh completes cleanly.
- Run doctor and test validation on the VM before attempting any paper-runner session.
- Keep ownership leasing disabled on the VM until promotion to canonical execution is intentional.
