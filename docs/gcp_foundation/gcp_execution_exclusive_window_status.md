# GCP Execution Exclusive Window Status

## Snapshot

- Generated at: `2026-04-24T12:35:59-04:00`
- Project ID: `codexalpaca`
- VM name: `vm-execution-paper-01`
- Window state: `awaiting_operator_attestation`
- Window status: `awaiting_operator_confirmation`
- Parallel runtime exception: `active_temporary_exception`
- Attestation path: `docs/gcp_foundation/gcp_execution_exclusive_window_attestation.json`
- Template window minutes: `45`

## Required Assertions

- `no_other_machine_active`
- `parallel_exception_path_not_running_broker_session`
- `session_starts_only_on_sanctioned_vm`
- `post_session_assimilation_reserved`

## Guardrails

- Bound the window to one sanctioned writer on `vm-execution-paper-01`.
- Do not start a concurrent broker-facing session on the temporary exception path.
- Do not treat the attestation as open-ended; it must have start and expiry timestamps.
- Do not promote the VM to canonical execution from the first trusted validation session alone.

## Attestation Template

```json
{
  "window_id": "trusted-validation-session-vm-execution-paper-01",
  "confirmed_by": "user@example.com",
  "confirmed_at": "2026-04-24T12:35:59-04:00",
  "window_starts_at": "2026-04-24T12:35:59-04:00",
  "window_expires_at": "2026-04-24T13:20:59-04:00",
  "target_vm_name": "vm-execution-paper-01",
  "scope": "paper_account_single_writer",
  "assertions": {
    "no_other_machine_active": true,
    "parallel_exception_path_not_running_broker_session": true,
    "session_starts_only_on_sanctioned_vm": true,
    "post_session_assimilation_reserved": true
  },
  "notes": "Bounded exclusive window for the first sanctioned GCP trusted validation session."
}
```

## Next Actions

- Populate `docs/gcp_foundation/gcp_execution_exclusive_window_attestation.json` with a bounded exclusive-window attestation before starting the first trusted validation session.
- Keep the temporary parallel runtime exception frozen and do not run concurrent broker-facing execution across the sanctioned and exception paths.
- Run governed post-session assimilation immediately after the trusted validation session ends.
