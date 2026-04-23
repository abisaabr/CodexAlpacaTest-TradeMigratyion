# GCP Execution Validation VM Status

## Snapshot

- Generated at: `2026-04-23T13:54:55.459182-04:00`
- Project ID: `codexalpaca`
- Bootstrap service account: `sa-bootstrap-admin@codexalpaca.iam.gserviceaccount.com`
- Region: `us-east1`
- Zone: `us-east1-b`

## Resource Results

- `static_ip` `ip-execution-paper-us-east1`: `created` (address `34.139.193.220`, status `RESERVED`)
- `firewall_rule` `fw-allow-iap-ssh-execution`: `created` (network `vpc-codex-core`, source ranges `35.235.240.0/20`)
- `instance` `vm-execution-paper-01`: `created` (status `RUNNING`, machine `e2-standard-4`, service account `sa-execution-runner@codexalpaca.iam.gserviceaccount.com`, external IP `34.139.193.220`)

## Phase Plan

- `1`: Reserve the execution static IP and keep it attached to the validation VM.
- `2`: Keep the VM validation-only with OS Login, Shielded VM, and IAP-only SSH.
- `3`: Teach the VM bootstrap to pull runtime credentials from Secret Manager instead of workstation .env.
- `4`: Run a trusted validation session and require a full runner evidence packet before cutover.
- `5`: Promote the VM to canonical execution only after the governed readiness gate is clean.

## Next Actions

- Teach the execution VM bootstrap to restore code and pull runtime secrets from Secret Manager.
- Grant operator access with OS Login / IAP before interactive administration is needed.
- Run validation-only checks on the VM and confirm outbound traffic uses the reserved static IP.
- Keep the current workstation runner available until the VM clears the full trusted-session gate.
