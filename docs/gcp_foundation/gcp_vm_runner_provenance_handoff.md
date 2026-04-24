# GCP VM Runner Provenance Status

## Snapshot

- Generated at: `2026-04-24T10:20:18.063096-04:00`
- Status: `provenance_matched`
- VM name: `vm-execution-paper-01`
- VM runner path: `/opt/codexalpaca/codexalpaca_repo`
- Local runner branch: `codex/qqq-paper-portfolio`
- Local runner commit: `f2b9bae7b2af26eefc086189a244e4d5a6c81a83`
- VM path present: `True`
- VM Git present: `False`
- VM runner commit: `f2b9bae7b2af26eefc086189a244e4d5a6c81a83`
- VM commit matches local: `True`
- Source fingerprint status: `source_fingerprint_matched`
- Source fingerprint safe to stamp: `True`

## Issues


## Operator Read

- This packet is a source-provenance check only; it does not start trading or change the VM.
- A trusted session is strongest when the VM runner exposes the exact Git commit or a deployment stamp.
- If provenance is unstamped, treat the session as operationally bounded but not fully source-attested until post-session review confirms code identity.
- If the source fingerprint mismatches, reconcile the VM deployment before treating the session as trusted evidence.

## Next Actions

- Add a lightweight deployment source stamp only after the VM source fingerprint matches the intended runner checkout.
- Refresh this packet after source provenance is stamped.
- Do not use unstamped VM source provenance to justify strategy promotion.
