# GCP Execution VM Lease Dry-Run Validation Review

## Snapshot

- Generated at: `2026-04-23T16:02:58.708892-04:00`
- VM name: `vm-execution-paper-01`
- Run ID: `vm-execution-paper-01-20260423-160102`
- Review state: `passed`
- Result prefix: `gs://codexalpaca-control-us/bootstrap/2026-04-23/foundation-phase17-lease-dry-run-validation/vm-execution-paper-01-20260423-160102`

## Observed Objects

- `bootstrap/2026-04-23/foundation-phase17-lease-dry-run-validation/vm-execution-paper-01-20260423-160102/doctor.json`
- `bootstrap/2026-04-23/foundation-phase17-lease-dry-run-validation/vm-execution-paper-01-20260423-160102/launch_result.json`
- `bootstrap/2026-04-23/foundation-phase17-lease-dry-run-validation/vm-execution-paper-01-20260423-160102/lease_validation.log`
- `bootstrap/2026-04-23/foundation-phase17-lease-dry-run-validation/vm-execution-paper-01-20260423-160102/lease_validation_status.json`
- `bootstrap/2026-04-23/foundation-phase17-lease-dry-run-validation/vm-execution-paper-01-20260423-160102/pytest_targeted.log`
- `bootstrap/2026-04-23/foundation-phase17-lease-dry-run-validation/vm-execution-paper-01-20260423-160102/validation-run.log`

## Launch Result

- Validation exit code: `0`
- Lease validation status present: `True`
- Doctor present: `True`
- Pytest log present: `True`

## Lease Validation Status

- Observed external IP: `34.139.193.220`
- Lease backend: `gcs_generation_match`
- Lease class: `GenerationMatchOwnershipLease`
- Lease dry run passed: `True`
- Targeted pytest exit code: `0`
- Final record present: `False`

## Next Actions

- The sanctioned VM proved the shared execution lease in dry-run mode without entering the trading loop.
- Keep lease enforcement off by default and use this packet as the prerequisite for the next trusted validation-session discussion.
