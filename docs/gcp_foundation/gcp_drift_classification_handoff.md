# GCP Drift Classification Handoff

## Current Read

- Phase 0 freeze is active.
- The sanctioned execution asset is `vm-execution-paper-01`.
- The highest-risk drift asset is `multi-ticker-trader-v1`.
- The project should not create more runtime resources until drift classification is resolved.

## Keep

- `vm-execution-paper-01`
- `vpc-codex-core` execution path
- role-separated foundation buckets

## Quarantine

- `multi-ticker-trader-v1`
- `multi-ticker-vm@codexalpaca.iam.gserviceaccount.com`
- `multi-ticker-vm-env`
- `codexalpaca-runtime-us-central1`
- `codexalpaca-containers`
- `default` VPC runtime use

## Next Decisions

- Keep, migrate, or decommission multi-ticker-trader-v1.
- Keep or decommission the multi-ticker-vm identity and multi-ticker-vm-env secret.
- Keep or decommission codexalpaca-runtime-us-central1.
- Formalize or retire codexalpaca-containers and codexalpaca_cloudbuild.
- Define when default VPC can be considered empty enough to quarantine.

## Rule

- Do not promote cloud execution or create new runner infrastructure until the quarantined footprint is either codified or decommissioned.
