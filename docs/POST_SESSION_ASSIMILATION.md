# Post-Session Assimilation

Use this workflow after the paper runner completes a session and before relying on that session to influence research or unlock policy.

Preferred entrypoint:
- `cleanroom/code/qqq_options_30d_cleanroom/launch_post_session_assimilation.ps1`

## Objective

Turn the latest paper-runner session into governed control-plane learning.

That means:
- rebuild session reconciliation from the latest runner bundle
- rebuild execution calibration from trusted session evidence only
- rebuild tournament profile, unlock, workplan, and execution evidence artifacts
- produce one compact morning operator brief that says what remains unlocked, what remains blocked, and what changed

## Required Inputs

- current control-plane repo on `main`
- current execution repo with the latest runner artifacts
- latest paper-runner session bundle under `codexalpaca_repo/reports/multi_ticker_portfolio/runs`

## Required Outputs

- `docs/session_reconciliation/*`
- `docs/execution_calibration/*`
- `docs/tournament_profiles/*`
- `docs/tournament_unlocks/*`
- `docs/execution_evidence/*`
- `docs/overnight_plan/*`
- `docs/morning_brief/morning_operator_brief.json`
- `docs/morning_brief/morning_operator_brief.md`
- `docs/morning_brief/morning_operator_brief_handoff.json`
- `docs/morning_brief/morning_operator_brief_handoff.md`
- `docs/morning_brief/post_session_assimilation_status.json`

## Hard Rules

- do not modify the live manifest
- do not change live strategy selection or risk policy
- do not commit raw session exhaust, raw order logs, or raw intraday trade activity
- do not let `review_required` sessions loosen research policy or unlock aggressive profiles

## Interpretation

If the morning brief still says:
- `keep_blocked_profiles_blocked`

then the control plane is telling us to stay on the current unlocked profile and keep gathering execution evidence.

If the morning brief advances to a reassessment posture, use the refreshed unlock and workplan packets to decide whether the nearest blocked profile is any closer to safe activation.
