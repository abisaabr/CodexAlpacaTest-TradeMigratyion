# GCP Parallel Runtime Exception

This packet records a temporary exception for the live parallel runner path in `codexalpaca`.

## Purpose

The project currently has:

- one sanctioned codified execution-validation path
- one parallel runner path that will remain in place for now

An institutional project should not leave that situation informal. If a parallel path remains, it should remain only under a narrow, explicit exception with compensating controls and an exit plan.

## What This Exception Means

- the sanctioned path is still the primary architecture
- the parallel runner is tolerated temporarily, not blessed as a second primary architecture
- no new parallel runtime sprawl should be created around that path
- every material change to that path must be documented

## Required Compensating Controls

- no concurrent broker-facing execution across the sanctioned and exception paths
- no widening of IAM privilege for the exception path
- no new runtime resources for the exception path without explicit review
- documented changes in GitHub and the control bucket
- clear keep/migrate/decommission decision path

## Exit Condition

This exception ends only when the parallel runtime path is either:

- codified into the sanctioned control-plane rollout
- or decommissioned

Until then, the presence of the exception is itself a promotion blocker for institutional-grade cloud execution.
