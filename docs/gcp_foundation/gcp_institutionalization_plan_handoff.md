# GCP Institutionalization Plan Handoff

## Current Posture

- Project: `codexalpaca`
- Posture: `foundation_present_with_material_drift`
- Strongest controlled asset: `vm-execution-paper-01`
- Strongest remaining risk: unmanaged parallel runtime footprint outside the codified execution path

## What Is Good

- role-separated foundation buckets exist
- runtime service accounts exist
- Secret Manager foundation exists
- validation execution VM exists on `vpc-codex-core`
- headless VM validation gate is green
- trusted validation session gate is prepared

## What Is Not Yet Institutional

- project-level `Owner` is still granted to service accounts
- `multi-ticker-trader-v1` is still running outside the codified rollout
- `multi-ticker-vm`, `multi-ticker-vm-env`, `codexalpaca-runtime-us-central1`, and `codexalpaca-containers` are still unclassified drift
- default-network is still present and permissive
- Workflows, Scheduler, and Batch are enabled but not yet formalized into the sanctioned control plane
- shared execution exclusivity still depends on an operator-managed exclusive window

## Immediate Phase Order

1. Freeze and classify the unmanaged footprint.
2. Remove bootstrap-era IAM from steady-state identities.
3. Run one trusted validation paper session on `vm-execution-paper-01` during an exclusive execution window.
4. Build the cloud-backed shared execution lease.
5. Promote the execution VM only after the trusted validation evidence is clean.
6. Formalize orchestration and research migration after execution governance is stable.

## Decision Rule

- Do not promote cloud execution because the VM exists.
- Promote it only after drift is classified, IAM is narrowed, and the first trusted validation session plus assimilation packet are clean.
