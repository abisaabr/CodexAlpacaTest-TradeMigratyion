# GCP Execution VM Headless Validation

This runbook launches the execution VM validation gate without relying on an interactive SSH session.

## Purpose

Use this when we want the validation VM to prove its runtime bootstrap, secret access, doctor checks, and test suite in a governed, auditable way from cloud state alone.

## What It Does

1. Reads the published VM validation gate packet.
2. Builds a composite startup script that preserves the VM's baseline validation-only bootstrap and then runs the validation shell script.
3. Writes the composite startup script into instance metadata.
4. Resets the VM so the one-shot validation run executes on boot.
5. Uploads the resulting validation artifacts back into the control bucket.

## Guardrails

- This is validation-only and does not start trading.
- The VM keeps `codexalpaca-validation-only=true`.
- The validation launch is auditable from GitHub and GCS.
- Result review should happen before any trusted validation session is attempted.

## Output Contract

The launched run should publish a result prefix containing:

- `launch_result.json`
- `validation_status.json`
- `doctor.json`
- `pytest.log`
- `validation-run.log`

## Recommended Operator Sequence

1. Confirm access readiness is `ready_for_operator_validation`.
2. Launch the headless validation run.
3. Inspect the result prefix in GCS.
4. Only if the packet is clean, move to the trusted validation-session phase.
