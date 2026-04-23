# GCP Parallel Runtime Exception Handoff

## Current Read

- The codified execution path remains the sanctioned path.
- The parallel runner path is temporarily allowed to remain, but only under explicit exception controls.
- This exception does not bless the parallel path as a second sanctioned architecture.

## Operator Rule

- Treat the parallel path as tolerated but frozen.
- Do not create additional runtime sprawl around it.
- Document every material change in GitHub and the GCS control bucket.
- Do not run concurrent broker-facing execution across the sanctioned and exception paths.

## Exit

- The exception ends only when the parallel path is codified into the sanctioned rollout or decommissioned.
