# AAPL Bounded Paper Validation Plan

## Snapshot

- Packet id: `gcp_research_aapl_bounded_paper_validation_plan_20260428`
- State: `ready_to_prepare_bounded_paper_validation`
- Broker facing: `false`
- Live manifest effect: `none`
- Risk policy effect: `none`
- Non-live manifest candidate: `docs/gcp_foundation/gcp_research_aapl_bounded_validation_manifest_candidate.yaml`
- Runner-compatible runtime config: `docs/gcp_foundation/gcp_research_aapl_bounded_validation_runtime_config.yaml`
- Operator checklist: `docs/gcp_foundation/gcp_research_aapl_bounded_validation_operator_checklist.md`
- Latest startup preflight: `passed` in `docs/gcp_foundation/gcp_research_aapl_bounded_validation_preflight_status.md`
- Launch gate: `docs/gcp_foundation/gcp_research_aapl_bounded_validation_launch_gate.md`

## Candidate

- Symbol: `AAPL`
- Candidate variant: `b150__aapl__long_call__wide_reward__exit_360__liq_baseline`
- Source strategy: `aapl__broad150__trend_long_call_research`
- Strategy class: `Class A liquid single-leg directional`
- Directional option type: `call`

## Research Evidence

Phase26 and Phase27 both kept the candidate eligible for research/governed-validation review:

- Phase26 min net PnL: `$1715.93`
- Phase26 min holdout/test net PnL: `$591.28`
- Phase26 min fill coverage: `0.9474`
- Phase27 min net PnL: `$1715.93`
- Phase27 min holdout/test net PnL: `$341.155`
- Phase27 min fill coverage: `0.9474`
- Phase27 worst drawdown: `$-4167.955`
- Phase27 blockers: `none`

## Bounded Validation Plan

This packet does not arm a session and does not change live manifests. It defines the next safe shape if an operator later authorizes a bounded paper validation run.

- Runner scope: `single_candidate_aapl_only`
- Account scope: `paper_only`
- Execution path: `vm-execution-paper-01`
- Requires explicit exclusive window: `true`
- Requires operator launch: `true`
- Requires broker-audited evidence: `true`
- Suggested initial cap: one tiny governed paper validation sleeve, no automatic scale-up
- Session goal: evidence quality and fill realism, not profit maximization
- Promotion goal: count only clean broker-audited evidence toward Class A trusted-session requirements

## Hard Blocks Before Any Run

- Exclusive execution window must be armed.
- Strategy must be wired into the runner-compatible bounded validation runtime config without changing live production selection.
- Risk cap must be explicitly reviewed.
- Paper runner must produce broker-order audit.
- Paper runner must produce account-activity audit.
- Paper runner must end flat or reconcile positions.
- Post-session assimilation must run immediately.

## Startup Preflight

The no-order VM startup preflight passed on `2026-04-28` using the runner-compatible runtime config staged at `/opt/codexalpaca/codexalpaca_repo/config/aapl_bounded_validation_candidate.yaml`. It loaded one AAPL strategy, found required next-expiry call inventory, found zero broker positions, found zero open orders, and kept `submit_paper_orders=false`.

## Do Not Do

- Do not start trading from this packet.
- Do not change the live manifest from this packet.
- Do not relax the fill gate.
- Do not increase risk policy.
- Do not count research results as broker-audited sessions.

## Next Safe Step

The non-live bounded validation governance manifest, runner-compatible runtime config, startup preflight status, launch gate, and operator checklist are prepared. The next safe action is still not trading: arm an explicit exclusive execution window only if the operator decides to run the bounded paper validation, then run the broker-facing command from the checklist. Do not run broker-facing paper validation until the exclusive execution window is armed and the operator explicitly authorizes the session.
