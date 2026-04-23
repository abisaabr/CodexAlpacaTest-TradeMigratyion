# GCP Project State Audit

This runbook defines the live-state audit for the `codexalpaca` Google Cloud project.

## Purpose

We use this audit to answer one question cleanly:

> What actually exists in GCP right now, and how much of it is codified versus drifting?

## Scope

The audit covers:

- enabled APIs
- buckets
- service accounts
- compute instances
- static IPs
- firewall rules
- networks and subnetworks
- Artifact Registry repositories
- Secret Manager secrets
- Workflows, Batch jobs, and Scheduler jobs
- relevant project IAM bindings

## Why This Matters

An institutional-grade cloud project is not just “resources that work.”
It is:

- resources that are codified
- identities that are least-privileged
- runtime footprints that are explainable
- drift that is visible
- promotion and decommission decisions that are explicit

## Output Files

- `docs/gcp_foundation/gcp_project_state_audit_status.json`
- `docs/gcp_foundation/gcp_project_state_audit_status.md`
