# Execution Evidence Contract

This repo keeps a machine-readable execution evidence contract so the next paper-runner session can be judged against an explicit evidence package instead of a vague “get better telemetry” request.

## Source Of Truth

- Builders:
  - `cleanroom/code/qqq_options_30d_cleanroom/build_execution_evidence_contract.py`
  - `cleanroom/code/qqq_options_30d_cleanroom/build_execution_evidence_contract_handoff.py`
- Inputs:
  - `docs/tournament_unlocks/tournament_unlock_workplan.json`
  - `docs/session_reconciliation/session_reconciliation_registry.json`
  - `docs/session_reconciliation/session_reconciliation_handoff.json`
  - `docs/execution_calibration/execution_calibration_handoff.json`
- Generated artifacts:
  - `docs/execution_evidence/execution_evidence_contract.json`
  - `docs/execution_evidence/execution_evidence_contract.md`
  - `docs/execution_evidence/execution_evidence_contract_handoff.json`
  - `docs/execution_evidence/execution_evidence_contract_handoff.md`

## Why It Exists

The unlock workplan says what the execution plane should accomplish next.

The execution evidence contract says what a qualifying next session must actually contain:

- what artifacts must exist
- what trust checks must pass
- whether the session came from a clean runner checkout that stamped the current unlock baseline
- whether the latest traded session already satisfies the contract
- what gaps still prevent that session from teaching research or helping unlock the next profile tier

## Institutional Use

Use this contract when you want a precise answer to:

- what should the next trusted paper session leave behind?
- is the latest traded session already good enough to teach research?
- what exact evidence gap is still stopping the next unlock target?

## Refresh Command

From the repo root:

```powershell
python .\cleanroom\code\qqq_options_30d_cleanroom\build_execution_evidence_contract.py
python .\cleanroom\code\qqq_options_30d_cleanroom\build_execution_evidence_contract_handoff.py
```
