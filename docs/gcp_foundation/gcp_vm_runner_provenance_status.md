# GCP VM Runner Provenance Status

## Snapshot

- Generated at: `2026-04-24T10:33:00.372736-04:00`
- Status: `provenance_matched`
- VM name: `vm-execution-paper-01`
- VM runner path: `/opt/codexalpaca/codexalpaca_repo`
- Local runner branch: `codex/qqq-paper-portfolio`
- Local runner commit: `8acef9ec83d6a89e043201e2aa67e2a3f92870ca`
- VM path present: `True`
- VM Git present: `False`
- VM runner commit: `8acef9ec83d6a89e043201e2aa67e2a3f92870ca`
- VM commit matches local: `True`
- Source fingerprint status: `source_fingerprint_matched`
- Source fingerprint safe to stamp: `True`

## Issues

- none

## Operator Read

- This packet is a source-provenance check only; it does not start trading or change the VM.
- A trusted session is strongest when the VM runner exposes the exact Git commit or a deployment stamp.
- If provenance is unstamped, treat the session as operationally bounded but not fully source-attested until post-session review confirms code identity.
- If the source fingerprint mismatches, reconcile the VM deployment before treating the session as trusted evidence.

## Next Actions

- Keep the VM source stamp in place and refresh provenance after any future runner deployment.
- Use this packet as source-attestation support only; the exclusive-window and broker-evidence gates still control launch and promotion.
- Do not modify strategy selection or risk policy from this provenance packet.
