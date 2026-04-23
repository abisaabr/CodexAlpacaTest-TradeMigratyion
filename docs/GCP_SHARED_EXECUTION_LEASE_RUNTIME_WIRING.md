# GCP Shared Execution Lease Runtime Wiring

This document records the first sanctioned runner revision that wires the shared execution lease into the multi-ticker trader as an explicit, non-default runtime backend.

It exists to answer one question clearly:

- has the project moved from "design plus helper seam" to "real optional runtime wiring"?

## What This Phase Means

At this phase, the sanctioned runner is allowed to:

- expose an ownership backend switch
- accept a `gs://` lease object URI
- construct the GCS-backed lease store only when explicitly requested
- keep the default trader path on the existing file lease

At this phase, the project is still **not** allowed to:

- treat the GCS lease as broker-facing ready by default
- flip workstation tooling over to the cloud lease automatically
- imply that execution exclusivity is solved before VM dry-run validation against the real lease object

## Institutional Boundary

This is a runtime wiring checkpoint, not a promotion checkpoint.

The purpose is to make the sanctioned cloud path testable without destabilizing:

- local health check behavior
- standby failover checks
- current file-lease-based workstation operations

## Required Next Move

The next sanctioned step after this packet is:

- install the runner with the `gcp` extra on `vm-execution-paper-01`
- point ownership at the real GCS lease object under explicit non-default config
- validate acquire / renew / release / stale takeover in dry-run mode
- only after that consider turning the shared execution lease into a promotion-relevant control
