# GCP Project State Audit

## Snapshot

- Generated at: `2026-04-23T14:55:38.866941-04:00`
- Project ID: `codexalpaca`
- Audit posture: `foundation_present_with_material_drift`

## Foundation Summary

- Enabled services: `49`
- Buckets: `7`
- Service accounts: `8`
- Compute instances: `2`
- Static addresses: `2`
- Secrets: `6`
- Artifact repositories: `2`

## Managed Execution Footprint

- `vm-execution-paper-01` in `us-east1-b`: `RUNNING` via `sa-execution-runner@codexalpaca.iam.gserviceaccount.com`

## Drift / Unmanaged Footprint

- `compute_instance` `multi-ticker-trader-v1`: `running outside the codified execution-validation footprint`
- `bucket` `codexalpaca-runtime-us-central1`: `not part of the codified role-separated storage foundation`
- `bucket` `codexalpaca-transfer-922745393036`: `not part of the codified role-separated storage foundation`
- `bucket` `codexalpaca_cloudbuild`: `not part of the codified role-separated storage foundation`
- `service_account` `multi-ticker-vm@codexalpaca.iam.gserviceaccount.com`: `not part of the codified runtime identity set`
- `network` `default`: `default network remains enabled and broad`

## Highest-Risk Findings

- `Project-level Owner remains granted to service accounts, including the bootstrap identity and ramzi-service-account; this is too broad for steady-state runtime operations.`
- `A second running VM (`multi-ticker-trader-v1`) and its supporting runtime resources exist outside the codified control-plane rollout, creating architecture drift and possible execution ambiguity.`
- `The default VPC network still exists alongside the intended `vpc-codex-core`, which weakens network posture and can hide ungoverned resources.`
- `Cloud Batch, Workflows, and Cloud Scheduler APIs are enabled, but there are no codified jobs/workflows/schedules yet; orchestration capability exists without an institutional deployment layer.`
- `We have a validation-grade execution VM, but not yet a cloud-backed shared execution lease, so the first broker-facing cloud session still depends on an explicit exclusive operator window.`

## Immediate Recommendations

- Freeze architecture drift by classifying `multi-ticker-trader-v1`, `multi-ticker-vm`, `multi-ticker-vm-env`, `codexalpaca-runtime-us-central1`, and `codexalpaca-containers` as either formalized or decommissioned.
- Step down IAM by removing project-level Owner from service accounts after replacing it with narrowly scoped runtime and bootstrap roles.
- Adopt `vpc-codex-core` as the only sanctioned runtime network and plan retirement or explicit quarantine of default-network usage.
- Use the green headless validation packet to run one trusted validation paper session only during an explicitly exclusive paper-account window.
- Build the missing orchestration layer next: Cloud Build/Artifact Registry image pipeline, Workflows/Scheduler control plane, and Batch-backed research execution.
