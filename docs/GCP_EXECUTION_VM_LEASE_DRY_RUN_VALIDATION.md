# GCP Execution VM Lease Dry-Run Validation

This packet governs the first real on-VM exercise of the shared execution lease on the sanctioned execution VM.

## Goal

Prove that `vm-execution-paper-01` can:

- restore the sanctioned runner bundle
- install the optional `gcp` dependency path
- build the trader with the non-default GCS ownership backend
- acquire, renew, block, steal-after-expiry, and release the lease

without:

- calling `trader.run()`
- constructing a live Alpaca broker adapter
- starting a broker-facing paper session

## Why This Phase Exists

The project already has:

- a sanctioned execution VM
- a green headless VM validation gate
- a tested GCS generation-match ownership seam in the runner

What it did not have yet was proof that those pieces actually work together on the VM against the real control-bucket lease object.

## Guardrails

- The lease dry-run is non-broker-facing.
- Ownership backend selection happens only through explicit non-default env overrides during validation.
- The validation aborts if the lease object already exists at start.
- The validation is not allowed to leave a residual lease object behind.

## Operator Rule

Do not treat the shared execution lease as ready for broker-facing enforcement until the headless lease dry-run review packet is `passed`.
