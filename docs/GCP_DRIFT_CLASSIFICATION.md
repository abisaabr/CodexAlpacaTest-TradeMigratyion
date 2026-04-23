# GCP Drift Classification

This packet formalizes **Phase 0** of the GCP institutionalization plan: freeze new runtime sprawl, classify every unmanaged resource, and avoid promoting cloud execution while drift remains unresolved.

## Why This Exists

The live `codexalpaca` project now has two truths at once:

- a strong codified execution-validation path
- a separate unmanaged runtime path created outside that rollout

That means the right institutional response is not "build faster." It is "freeze, classify, and then decide."

## What Counts As Drift

For this project, drift means any live cloud runtime resource that is not already part of the codified execution path around:

- `vm-execution-paper-01`
- `vpc-codex-core`
- the role-separated foundation buckets
- the governed validation and trusted-session packets in the control plane

## Allowed Phase 0 Decisions

Every resource under review must land in exactly one bucket:

- `keep`
- `quarantine`
- `decommission`
- `formalize_or_retire`

## Phase 0 Freeze Rule

Until drift classification is resolved:

- do not create another runner VM
- do not create more runtime secrets
- do not create more parallel runtime identities
- do not start broker-facing execution from unmanaged hosts
- do not promote cloud execution because infrastructure exists

## Institutional Goal

By the end of Phase 0, there should be only one answer to the question:

"What is the sanctioned cloud execution path?"

If there is more than one answer, the project is not yet ready for institutional promotion.
