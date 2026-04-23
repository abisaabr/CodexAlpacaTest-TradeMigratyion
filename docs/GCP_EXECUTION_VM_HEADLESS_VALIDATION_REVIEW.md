# GCP Execution VM Headless Validation Review

This review packet tells us whether the launched headless validation run is still pending, has passed, or has failed.

## Review States

- `pending`: the VM has been reset and the result prefix has not produced `launch_result.json` yet.
- `passed`: `launch_result.json` is present, the validation exit code is `0`, and `validation_status.json` is available.
- `failed`: the result packet exists but the validation exit code is non-zero or the required validation output is incomplete.

## Why This Matters

This keeps the VM cut-in governed from cloud state instead of relying on a human to inspect the VM directly.

## Operator Rule

Do not move toward a trusted validation session until this review packet is `passed`.
