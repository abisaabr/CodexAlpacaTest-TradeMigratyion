# GCP Institutional Hardening Plan

As of: 2026-04-24T11:36:45-04:00

Status: ready_for_parallel_non_broker_work_execution_prearm_blocked

## Current State

- Broker is flat.
- Sanctioned execution path remains `vm-execution-paper-01`.
- VM runner source is patched to `f0080066c68d883286f4cb1b9c9e0edc601adf8d`.
- VM runner tests are green: `140 passed`.
- Execution pre-arm is blocked until the unattributed order source is resolved or all candidate launch surfaces are proven disabled.
- Local stale launch surface `GovernedDownChoppyTakeoverUser` is disabled.
- Qualified winner sessions remain `0 / 20`.
- Research wave bootstrap has `2070` variants ready for research-only execution.
- Strategy registry has `94` strategies, with a concentration warning: `95.7%` single-leg.
- Research data is usable with warnings; governed 11-name coverage is not complete yet.

## Agent Lanes

- Execution Safety Steward: keep one sanctioned execution path, source-attested VM state, broker flatness, and no stale desktop scheduler.
- Evidence Closeout Steward: require broker-order audit, account-activity audit, ending positions, shutdown reconciliation, and broker/local economics comparison for every session.
- Research Data Foundation Engineer: complete GCS-backed raw, curated, and derived tiers with data-quality verdicts before expanding into heavier data.
- Backtest Factory Engineer: run research-only sweeps in reproducible chunks with normalized results, after-cost expectancy, slippage stress, and drawdown reports.
- Loser-Learning Analyst: classify loser clusters and turn them into suppressors, repairs, kill decisions, or quarantine recommendations.
- Promotion Steward: allow only `research_only -> governed_validation_candidate` from research; no broker activation, live manifest change, or risk-policy change from research alone.

## Phase Gates

1. Phase 0, execution lockdown: VM source stamp matches intended commit, broker flat, no stale local runner, no active unsanctioned scheduler, and no unattributed broker orders during a pre-arm watch window.
2. Phase 1, evidence contract: next paper session is either evidence-complete or explicitly disqualified.
3. Phase 2, data quality baseline: all governed 11 symbols have quality verdicts and GCS manifests.
4. Phase 3, research wave execution: each chunk leaves normalized results, cost/slippage stress, and hold/kill/quarantine recommendation.
5. Phase 4, first research promotion packet: at most one candidate advances to `governed_validation_candidate`, and only if after-cost, robustness, concentration, loser-learning, and metadata gates clear.
6. Phase 5, trader feedback: apply suppressors and calibration insights first; do not expand execution scope without control-plane approval.

## Hard Rules

- Do not start trading from this plan.
- Do not arm an exclusive execution window from this plan.
- Do not widen the temporary parallel runtime exception.
- Do not modify the live manifest or risk policy from research results.
- Do not count raw PnL winners as qualified winners without flat, reconciled, evidence-clean, teaching-clean closeout.

## Next Safe Actions

- Run pre-arm VM source/process/broker-flat checks immediately before any sanctioned paper session.
- Resolve the unattributed order-source blocker before any exclusive window is armed.
- Keep older local takeover/scheduled-task launch surfaces disabled while research-only work continues.
- Run research-only data-quality expansion for missing governed symbols.
- Start the `2070`-variant research wave only in deterministic chunks with a cost cap and required result artifacts.
- Use loser-learning suppressors before considering any strategy addition.
