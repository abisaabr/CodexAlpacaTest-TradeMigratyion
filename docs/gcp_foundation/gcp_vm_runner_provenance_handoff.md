# GCP VM Runner Provenance Status

## Snapshot

- Generated at: `2026-04-24T09:59:22.511000-04:00`
- Status: `provenance_unstamped`
- VM name: `vm-execution-paper-01`
- VM runner path: `/opt/codexalpaca/codexalpaca_repo`
- Local runner branch: `codex/qqq-paper-portfolio`
- Local runner commit: `f2b9bae7b2af26eefc086189a244e4d5a6c81a83`
- VM path present: `True`
- VM Git present: `False`
- VM runner commit: `None`
- VM commit matches local: `False`

## Issues

- `warning` `vm_runner_commit_unstamped`: The VM runner path exists but does not expose Git metadata or an observed source commit stamp.

## Operator Read

- This packet is a source-provenance check only; it does not start trading or change the VM.
- A trusted session is strongest when the VM runner exposes the exact Git commit or a deployment stamp.
- If provenance is unstamped, treat the session as operationally bounded but not fully source-attested until post-session review confirms code identity.

## Next Actions

- Add a lightweight deployment source stamp to the VM runner path before the next trusted session, or deploy the runner as a Git checkout.
- Refresh this packet after source provenance is stamped.
- Do not use unstamped VM source provenance to justify strategy promotion.
