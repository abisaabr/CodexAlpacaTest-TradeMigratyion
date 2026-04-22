# Overnight Phased Plan

## Snapshot

- Generated at: `2026-04-22T17:30:17.670340`
- Repo update status: `ready`
- Current unlocked profile: `down_choppy_coverage_ranked`
- Execution posture: `caution`
- Session trust posture: `caution`
- Execution evidence contract: `gapped`

## Hard Rules

- Do not modify the live manifest during the overnight plan itself.
- Do not activate policy-blocked or implementation-blocked profiles just because they are strategically interesting.
- Do not let review-required or incomplete broker-audit sessions loosen research policy.
- Keep production decisions serialized and review-gated.

## By-Morning Success

- `down_choppy_coverage_ranked` completes or remains healthy as the governed overnight research run.
- A fresh paper-runner session lands with trusted broker-order and broker account-activity audit coverage.
- Session reconciliation, execution calibration, unlock, workplan, and execution evidence artifacts are refreshed from the latest evidence.
- The control plane can state clearly whether the next blocked profile is still blocked or has moved closer to being unlocked.

## Phases

### Confirm governed repo state before overnight work begins.

- Code: `phase_0_governance_preflight`
- Owner: `shared_control_plane`
- Objective: Start only from current, branch-aligned repos and the currently unlocked tournament profile.
- Actions:
  - Both governed repos are current enough to proceed without update action.
  - Keep `down_choppy_coverage_ranked` as the safe overnight default unless the refreshed unlock handoff changes it.
  - Do not activate any policy-blocked or implementation-blocked profile during preflight.
- Success criteria:
  - repo_update_handoff overall status is `ready`
  - safe_to_run_nightly_cycle = true
  - current unlocked profile remains `down_choppy_coverage_ranked`
- Gates:
  - If repo update control is not ready, pause overnight execution until GitHub drift is cleared.

### Run the currently unlocked governed research profile.

- Code: `phase_1_current_research_launch`
- Owner: `current_research_machine`
- Objective: Use the safe unlocked profile to keep research moving while higher-risk profiles remain blocked by execution evidence.
- Recommended profile: `down_choppy_coverage_ranked`
- Actions:
  - Launch `down_choppy_coverage_ranked` through `launch_nightly_operator_cycle.ps1`.
  - Keep promotion review-only and leave the live manifest untouched.
  - Treat higher-tier blocked profiles as out of bounds for tonight even if they are strategically interesting.
- Success criteria:
  - `down_choppy_coverage_ranked` launches through the governed nightly operator path
  - discovery stays parallel and production decisions remain serialized
  - the live manifest remains unchanged
- Gates:
  - If the unlock handoff changes the current resolved profile, stop and re-evaluate the overnight plan before launching research.

### No research-plane unlock wiring is immediately required.

- Code: `phase_2_research_unlock_progress`
- Owner: `current_research_machine`
- Objective: The current unlock surface is blocked more by execution evidence than by missing governed entrypoints.
- Gates:
  - Do this through the governed control-plane path, not as an ad hoc side script.

### Produce the next trusted broker-audited execution evidence package.

- Code: `phase_3_execution_evidence_capture`
- Owner: `new_machine_execution_plane`
- Objective: The execution plane should focus on landing fresh trusted paper-runner evidence that removes the current audit and evidence-floor blockers from the nearest unlock targets.
- Primary target profiles: `opening_30m_premium_defense, balanced_family_expansion_benchmark`
- Required next session artifacts:
  - broker-order audit
  - broker account-activity audit
  - ending broker-position snapshot
  - shutdown reconciliation
  - completed trade table with broker/local economics comparison
- Actions:
  - Run the current unlocked profile without changing live strategy selection, risk policy, or the live manifest.
  - Ensure the session bundle captures broker-order audit, broker account-activity audit, and ending broker-position snapshot artifacts.
  - Immediately rerun session reconciliation, execution calibration, tournament unlock registry, and tournament unlock handoff after the next trusted session lands.
  - Treat trusted broker-order and broker-activity audit coverage as the primary missing evidence package.
  - Aim to improve execution evidence beyond `limited_entry_only` by landing a trusted, fully reconciled paper session.
  - Keep live strategy selection, risk policy, and the live manifest unchanged while producing evidence.
- Success criteria:
  - At least one fresh trusted paper session lands with broker-order audit coverage.
  - At least one fresh trusted paper session lands with broker account-activity audit coverage.
  - The refreshed session reconciliation handoff remains `trusted_and_cautious_sessions` or better without flipping the new session to `review_required`.
  - The refreshed execution calibration handoff improves the evidence floor or removes audit-gap blockers for the nearest unlock target.
- Gates:
  - Only trusted or caution sessions with complete broker-audit evidence should be allowed to teach research policy.
- Current evidence gaps:
  - `broker_order_audit`: Broker-order audit coverage must be present in the session bundle.
  - `broker_activity_audit`: Broker account-activity audit coverage must be present in the session bundle.
  - `broker_local_cashflow_comparable`: Broker/local economics comparison must be available when broker activity audit exists.
  - `evidence_strength_progress`: Execution evidence should improve beyond `limited_entry_only` for the nearest unlock target.

### Refresh reconciliation, calibration, unlock, and evidence artifacts from the latest trusted session.

- Code: `phase_4_post_session_assimilation`
- Owner: `new_machine_execution_plane`
- Objective: Turn the next paper-runner session into governed control-plane learning instead of raw local exhaust.
- Actions:
  - Run `launch_post_session_assimilation.ps1` as the governed entrypoint for post-session control-plane refresh.
  - Rebuild session reconciliation registry and handoff.
  - Rebuild execution calibration registry and handoff.
  - Rebuild tournament unlock registry, unlock handoff, unlock workplan, and execution evidence contract.
  - Build the morning operator brief and handoff so tomorrow starts from one compact decision packet.
  - Commit only distilled governance artifacts if they changed materially.
- Success criteria:
  - session reconciliation is rebuilt from the latest session bundle
  - execution calibration is rebuilt from trusted session evidence only
  - tournament unlock, workplan, and execution evidence artifacts are refreshed
- Gates:
  - Do not commit raw session exhaust, raw order logs, or raw intraday trade activity.

### Review the refreshed overnight state before any profile escalation or manifest mutation.

- Code: `phase_5_morning_decision_packet`
- Owner: `human_reviewer_and_promotion_steward`
- Objective: Decide what changed overnight, what remains blocked, and whether the next tournament tier is any closer to being safely unlocked.
- Actions:
  - Inspect the refreshed overnight phased plan handoff.
  - Inspect tournament unlock and execution evidence handoffs before choosing tomorrow's research profile.
  - Keep blocked profiles blocked until their audit and evidence gates are actually cleared.
- Success criteria:
  - morning operator can see the current unlocked profile, the next blocked targets, and the missing evidence package
  - blocked profiles remain blocked unless the refreshed evidence genuinely clears their gates
  - the live manifest stays review-gated
- Gates:
  - No auto-promotion into the live manifest.
