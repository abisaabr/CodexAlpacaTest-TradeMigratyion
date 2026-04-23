# GCP Shared Execution Lease Implementation

This document tracks the first sanctioned implementation checkpoint after the shared execution lease contract.

The intent is narrow on purpose:

- land the compare-and-set ownership seam in the sanctioned runner
- validate it locally and on the sanctioned branch
- keep enforcement off by default
- avoid implying that broker-facing cloud execution is already lease-protected

## Current Implementation Boundary

The sanctioned runner implementation lives in:

- `alpaca_lab/execution/ownership.py`
- `tests/test_execution_ownership.py`

At this phase, the runner is allowed to contain:

- the generic generation-match ownership helper
- the compare-and-set store protocol
- dry-run and in-memory validation tests
- release and renew symmetry with the current file lease

At this phase, the runner is **not** yet allowed to do any of the following by default:

- switch the multi-ticker trader off the existing file lease automatically
- assume a live Google Cloud Storage dependency path is already sanctioned
- treat the cloud lease as broker-facing ready

## Required Guardrails

- The default trader ownership path must remain the file lease until optional GCS store wiring is validated.
- Full runner regression coverage must stay green when the helper seam lands.
- The trusted validation-session gate remains in force even after helper implementation.
- The temporary parallel-runtime exception remains documented and bounded while the cloud lease is still not live.

## Next Build Step

The next sanctioned implementation step is:

- add an optional GCS-backed `ObjectLeaseStore`
- keep it behind explicit non-default config
- validate acquire / renew / release / stale takeover against the real lease object
- only after that consider enforcement-on promotion

## Operator Read

If the status packet shows `dry_run_helper_landed`, the right interpretation is:

- the implementation seam is real
- the runner branch is ready for optional store wiring
- the project is still not cleared for cloud lease enforcement by default
