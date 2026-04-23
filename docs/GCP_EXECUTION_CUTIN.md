# GCP Execution Cut-In

This runbook defines the institutional cut-in path for moving the paper runner onto Google Cloud without skipping validation.

The goal is:

- create a stable Alpaca-facing execution host with a reserved static IP
- keep the host in validation-only posture first
- preserve rollback to the current workstation runner until cloud validation is clean
- leave a machine-readable packet so any operator or machine can follow the exact cloud state

## Phase 1: Stable Network Identity

Objective:

- reserve the execution-plane static external IP

Deliverables:

- `ip-execution-paper-us-east1`
- address recorded in the control packet

Rules:

- no trading cutover yet
- do not rely on ephemeral VM addresses for broker-facing execution

## Phase 2: Validation-Only Execution Host

Objective:

- create the first dedicated execution VM in a controlled posture

Target:

- instance: `vm-execution-paper-01`
- region: `us-east1`
- zone: `us-east1-b`
- machine type: `e2-standard-4`
- boot disk: `pd-ssd`, `100 GB`
- service account: `sa-execution-runner@codexalpaca.iam.gserviceaccount.com`
- access scope: `cloud-platform`
- labels: execution, paper, validation

Security posture:

- Shielded VM enabled
- OS Login enabled
- project SSH keys blocked
- no broad inbound exposure
- IAP-only SSH firewall rule for port `22`

Validation posture:

- startup script installs only base runtime dependencies
- no automatic runner start
- no cutover to canonical paper execution

## Phase 3: Secret-Aware Runner Bootstrap

Objective:

- make the VM capable of loading runtime credentials from Secret Manager instead of workstation `.env`

Deliverables:

- bootstrap script on the VM
- validation proof that Secret Manager values can be read by `sa-execution-runner`
- runtime directories for code, logs, and artifacts

## Phase 4: Trusted Validation Session

Objective:

- prove the VM can produce the full runner evidence package before we let it own execution

Required evidence:

- broker-order audit
- broker account-activity audit
- ending broker-position snapshot
- shutdown reconciliation
- completed trade table with broker/local cashflow comparison

Rules:

- validation-only session first
- no live-manifest mutation
- blocked tournament profiles remain blocked

## Phase 5: Canonical Execution Promotion

Objective:

- promote the execution VM to the canonical paper runner only after validation is clean

Promotion gate:

- static IP confirmed
- tests pass on the VM
- Secret Manager bootstrap works
- runner unlock baseline is stamped into session summaries
- at least one fresh trusted unlock-grade session exists

Rollback:

- keep the current workstation runner available until the VM clears the full gate

## Builder

Use:

- `cleanroom/code/qqq_options_30d_cleanroom/bootstrap_gcp_execution_validation_vm.py`

Outputs:

- `docs/gcp_foundation/gcp_execution_validation_vm_status.json`
- `docs/gcp_foundation/gcp_execution_validation_vm_status.md`

## Hard Rules

- do not start trading as part of the VM bootstrap
- do not treat VM creation as cutover
- do not rely on a copied `.env` as the final cloud runtime model
- do not collapse research and execution back onto the same runtime host
