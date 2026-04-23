# Project Target Operating Model Handoff

## Current Read

- We are building a governed five-plane cloud system, not a collection of ad hoc cloud machines.
- The correct order is:
  - govern the estate
  - prove execution
  - promote execution
  - migrate research
  - automate the loop
- The strongest current cloud asset is `vm-execution-paper-01`.
- The strongest current blocker is that execution governance is still incomplete: shared lease not live, trusted unlock-grade evidence not yet landed, and parallel runtime exception still active.

## Canonical Target

- Governance plane: GitHub
- Control plane: Scheduler + Workflows
- Research plane: Cloud Batch
- Execution plane: one sanctioned Compute Engine VM
- Storage and observability plane: GCS + Logging + Monitoring

## Operator Rule

- Do not expand architecture faster than governance.
- Do not promote cloud execution because infrastructure exists.
- Do not move research fully into Batch before the execution plane is singular and trustworthy.
- Do not let the parallel runner exception become a second unofficial architecture.

## Immediate Priority

1. Finish execution governance.
2. Land the live shared execution lease.
3. Run the first trusted validation paper session on the sanctioned VM.
4. Assimilate that evidence cleanly.
5. Only then consider canonical execution promotion and research migration acceleration.

## What Both Machines Should Optimize For

- maximizing trusted evidence quality
- minimizing execution ambiguity
- increasing research throughput without increasing execution risk
- keeping GitHub and `gs://codexalpaca-control-us` aligned after every material change

## Next Step

- Treat the next critical build step as `optional_gcs_store_wiring` for the shared execution lease, followed by trusted validation-session evidence on `vm-execution-paper-01`.
