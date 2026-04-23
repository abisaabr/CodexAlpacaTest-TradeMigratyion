# GCP Execution Access Readiness Status

## Snapshot

- Generated at: `2026-04-23T14:12:29.257099-04:00`
- Project ID: `codexalpaca`
- VM: `vm-execution-paper-01`
- Zone: `us-east1-b`
- Bootstrap service account: `sa-bootstrap-admin@codexalpaca.iam.gserviceaccount.com`
- Access readiness: `ready_for_grant`

## API Readiness

- `iap.googleapis.com`: `enabled`
- `oslogin.googleapis.com`: `existing`

## VM / Firewall Checks

- `enable_oslogin`: `ok`
- `block_project_ssh_keys`: `ok`
- `iap_ssh_tag`: `ok`
- `iap_firewall_source_range`: `ok`

## Operator IAM

- operator principal not provided; IAM access grant remains pending

## Next Actions

- Provide the Google principal that should operate the VM so OS Login, IAP tunnel access, and serviceAccountUser can be granted explicitly.
- Keep inbound SSH restricted to IAP and do not open port 22 to the internet.
- Use the validation gate packet next, not ad hoc SSH commands, before trusting the VM for execution.
