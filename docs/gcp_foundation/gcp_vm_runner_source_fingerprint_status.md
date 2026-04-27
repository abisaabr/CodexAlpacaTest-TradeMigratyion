# GCP VM Runner Source Fingerprint Status

## Snapshot

- Generated at: `2026-04-27T10:25:50.824148-04:00`
- Status: `source_fingerprint_matched`
- VM name: `vm-execution-paper-01`
- VM runner path: `/opt/codexalpaca/codexalpaca_repo`
- Local runner branch: `HEAD`
- Local runner commit: `f0080066c68d883286f4cb1b9c9e0edc601adf8d`
- Safe to write source stamp: `True`

## Comparison

- Local file count: `97`
- VM file count: `97`
- Matching file count: `97`
- Changed file count: `0`
- Local-only file count: `0`
- VM-only file count: `0`

## Mismatch Samples

### Changed

- none

### Local-only

- none

### VM-only

- none

## Issues

- none

## Operator Read

- This is a source-fingerprint comparison only; it does not start trading or change the VM.
- A source stamp is defensible only when the VM fingerprint matches the intended runner checkout.
- A mismatch means the VM may still run, but the session should not be treated as source-attested trusted evidence.

## Next Actions

- Keep the VM source stamp in place and refresh this packet after any future runner deployment.
- Use this packet as source-attestation support only; the exclusive-window and broker-evidence gates still control launch and promotion.
- Do not modify strategy selection or risk policy from this provenance packet.
