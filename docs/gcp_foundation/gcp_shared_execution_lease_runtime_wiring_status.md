# GCP Shared Execution Lease Runtime Wiring

## Snapshot

- Generated at: `2026-04-23T16:14:47.390090-04:00`
- Project ID: `codexalpaca`
- Runtime wiring phase: `foundation-phase16-lease-runtime-wiring`
- Runtime wiring status: `optional_backend_wired_not_enforced`
- Runner branch: `codex/qqq-paper-portfolio`
- Runner commit: `a6cf50aa424a`
- Runner dirty: `False`

## Wiring Findings

- `gcs_store_present`: `True`
- `config_backend_switch_present`: `True`
- `config_gcs_uri_present`: `True`
- `env_backend_override_present`: `True`
- `env_gcs_uri_override_present`: `True`
- `trader_optional_wiring_present`: `True`
- `default_file_lease_still_present`: `True`
- `health_check_supports_gcs_backend`: `True`
- `health_check_default_path_still_file_scoped`: `True`
- `standby_check_passes_lease_backend`: `True`
- `standby_check_rejects_non_file_backend`: `True`
- `gcp_extra_declared`: `True`

## Validation

- Full suite: `80 passed`
- Full suite command: `python -m pytest -q`

## Guardrails

- The default trader path still remains on the file lease unless ownership.lease_backend is explicitly switched.
- The GCS lease backend still depends on explicit config and the optional 'gcp' dependency path.
- Health-check now understands the non-default GCS backend, but the default posture is still the file lease unless explicitly overridden.
- Standby failover remains intentionally file-scoped and rejects non-file ownership backends while the temporary parallel-runtime exception is in force.
- This wiring does not by itself clear the project for broker-facing cloud lease enforcement.

## Next Step

- Name: `vm_dry_run_gcs_lease_validation`
- Install the runner with the gcp extra on vm-execution-paper-01, point ownership at the GCS lease object under explicit non-default config, and validate acquire/renew/release behavior without starting a broker-facing session.
