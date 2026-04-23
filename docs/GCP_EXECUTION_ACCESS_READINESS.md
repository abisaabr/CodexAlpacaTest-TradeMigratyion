# GCP Execution Access Readiness

This runbook defines the access-governance gate for operating the execution VM safely.

The goal is:

- verify the execution VM is ready for OS Login and IAP-based administration
- enable the required Google APIs if they are still missing
- make operator access explicit in IAM instead of relying on ad hoc access
- record the remaining blocker clearly if the operator principal is not yet known

## Access Model

Use:

- OS Login for Linux account access
- IAP TCP forwarding for SSH transport

Do not rely on:

- broad inbound SSH exposure
- project metadata SSH keys
- permanent shared admin credentials

## Required Project / VM Conditions

- `enable-oslogin=TRUE` on the VM
- `block-project-ssh-keys=TRUE` on the VM
- IAP SSH firewall rule exists for source range `35.235.240.0/20`
- `iap.googleapis.com` enabled
- `oslogin.googleapis.com` enabled

## Required Operator Roles

For a named operator principal, the preferred minimum access set is:

- project: `roles/iap.tunnelResourceAccessor`
- project: `roles/compute.osAdminLogin`
- project: `roles/compute.viewer`
- service account `sa-execution-runner`: `roles/iam.serviceAccountUser`

If the operator principal belongs to a different Google Cloud organization than the VM, additional organization-level OS Login access may be required.

## Builder

Use:

- `cleanroom/code/qqq_options_30d_cleanroom/bootstrap_gcp_execution_access_readiness.py`

Outputs:

- `docs/gcp_foundation/gcp_execution_access_readiness_status.json`
- `docs/gcp_foundation/gcp_execution_access_readiness_status.md`

## Hard Rules

- do not grant broad project-owner access just to make SSH work
- do not open inbound SSH to the internet
- do not treat missing operator identity as a reason to weaken the access model
