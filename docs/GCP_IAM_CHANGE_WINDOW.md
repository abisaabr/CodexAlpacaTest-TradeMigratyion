# GCP IAM Change Window

This packet converts the IAM hardening recommendation into an explicit execution plan.

## Scope

The first change window is intentionally narrow:

- remove project-level `Owner` from `ramzi-service-account`
- remove project-level `Owner` from `sa-bootstrap-admin`

It does **not**:

- change the human owner principal
- widen or narrow sanctioned runtime service-account roles
- modify the quarantined `multi-ticker-vm` identity

## Why This Narrow Scope Matters

Institutional hardening is safer when the first cut is small, reversible, and easy to audit.

This first cutover is meant to prove that:

- bootstrap-era service-account ownership can be removed cleanly
- operator access remains intact through explicit minimal roles
- the project can re-audit itself immediately after the change

## Execution Discipline

- take a before snapshot
- remove one class of broad privilege
- take an after snapshot
- rerun the audit packets
- publish the result before broader work resumes

## Separation Of Concerns

Do not combine this IAM change window with:

- trusted validation-session execution
- shared execution lease rollout
- decommission of the parallel runtime

Each of those deserves its own governed event.
