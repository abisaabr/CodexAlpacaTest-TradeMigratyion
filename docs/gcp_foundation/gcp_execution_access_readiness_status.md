# GCP Execution Access Readiness Status

## Snapshot

- Generated at: `2026-04-23T14:22:22.754118-04:00`
- Project ID: `codexalpaca`
- VM: `vm-execution-paper-01`
- Zone: `us-east1-b`
- Bootstrap service account: `sa-bootstrap-admin@codexalpaca.iam.gserviceaccount.com`
- Access readiness: `ready_for_operator_validation`

## API Readiness

- `iap.googleapis.com`: `existing`
- `oslogin.googleapis.com`: `existing`

## VM / Firewall Checks

- `enable_oslogin`: `ok`
- `block_project_ssh_keys`: `ok`
- `iap_ssh_tag`: `ok`
- `iap_firewall_source_range`: `ok`

## Operator IAM

- `project` `roles/iap.tunnelResourceAccessor` -> `serviceAccount:ramzi-service-account@codexalpaca.iam.gserviceaccount.com`: `bound`
- `project` `roles/compute.osAdminLogin` -> `serviceAccount:ramzi-service-account@codexalpaca.iam.gserviceaccount.com`: `bound`
- `project` `roles/compute.viewer` -> `serviceAccount:ramzi-service-account@codexalpaca.iam.gserviceaccount.com`: `bound`
- `service_account` `roles/iam.serviceAccountUser` -> `serviceAccount:ramzi-service-account@codexalpaca.iam.gserviceaccount.com`: `bound` on `sa-execution-runner@codexalpaca.iam.gserviceaccount.com`

## Next Actions

- Use the new operator principal to connect through gcloud compute ssh with --tunnel-through-iap.
- Keep inbound SSH restricted to IAP and do not open port 22 to the internet.
- Use the validation gate packet next, not ad hoc SSH commands, before trusting the VM for execution.
