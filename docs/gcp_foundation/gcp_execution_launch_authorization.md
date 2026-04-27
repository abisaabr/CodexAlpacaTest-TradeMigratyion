# GCP Execution Launch Authorization

## Snapshot

- Generated at: `2026-04-27T10:54:26.886211-04:00`
- Status: `blocked`
- Next operator action: `resolve_launch_blockers`
- VM name: `vm-execution-paper-01`
- Operator packet state: `ready_to_arm_window`
- Launch pack state: `awaiting_window_arm`
- Trusted validation readiness: `awaiting_exclusive_execution_window`
- Exclusive window status: `awaiting_operator_confirmation`
- Runtime readiness status: `runtime_ready`
- Runner provenance status: `provenance_matched`
- Source fingerprint status: `source_fingerprint_matched`
- Pre-arm preflight status: `ready_to_arm_window`
- Pre-arm preflight age minutes: `23.5088708`
- Launch-surface audit status: `local_broker_capable_surfaces_fenced_broker_flat`
- Launch-surface audit age minutes: `23.514163766666666`
- Launch-surface broker flat: `True`
- Launch-surface no-new-order watch clean: `True`
- Trader process absent: `True`
- Ownership backend: `file`
- Shared execution lease enforced: `False`

## Commands

### Operator SSH

```bash
gcloud compute ssh vm-execution-paper-01 --project codexalpaca --zone us-east1-b --tunnel-through-iap
```

### VM Session Command

```bash
cd /opt/codexalpaca/codexalpaca_repo && ./.venv/bin/python scripts/run_multi_ticker_portfolio_paper_trader.py --portfolio-config config/multi_ticker_paper_portfolio.yaml --submit-paper-orders
```

### Post-Session Assimilation

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "<control-plane-root>\cleanroom\code\qqq_options_30d_cleanroom\launch_post_session_assimilation.ps1" -ControlPlaneRoot "<control-plane-root>" -RunnerRepoRoot "<runner-repo-root>"
```

### Close Window

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "<control-plane-root>\cleanroom\code\qqq_options_30d_cleanroom\close_gcp_execution_exclusive_window.ps1" -ControlPlaneRoot "<control-plane-root>" -VmName "vm-execution-paper-01" -MirrorToGcs
```

## Issues

- `error` `operator_packet_not_ready_to_launch`: The top-level operator packet must be `ready_to_launch_session` before launch.
- `error` `launch_pack_not_ready`: The launch pack must be `ready_to_launch` before the broker-facing session command is authorized.
- `error` `trusted_validation_not_ready`: Trusted validation readiness must be `ready_for_manual_launch` before launch.
- `error` `exclusive_window_not_ready`: The exclusive-window packet must say `ready_for_launch` before launch.
- `error` `closeout_not_reserved`: Closeout must be reserved as `ready_to_close_window` before launch.
- `error` `prearm_preflight_stale`: The pre-arm preflight is 23.51 minutes old; maximum allowed is 20.
- `error` `launch_surface_audit_stale`: The launch-surface audit is 23.51 minutes old; maximum allowed is 20.

## Required Evidence

- `broker-order audit`
- `broker account-activity audit`
- `ending broker-position snapshot`
- `shutdown reconciliation`
- `completed trade table with broker/local cashflow comparison`

## Operator Read

- This packet is non-broker-facing; it does not start the VM session.
- If status is `blocked`, do not run the VM session command.
- If status is `ready_to_launch_session`, run the VM command manually inside the attested exclusive window, then run post-session assimilation and closeout.
- Do not treat a successful launch authorization as strategy-promotion evidence; only the post-session evidence bundle can support review.
