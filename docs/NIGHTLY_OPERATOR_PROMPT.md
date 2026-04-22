# Nightly Operator Prompt

Use this prompt on the new machine or the current research machine when you want one full institutional nightly cycle.

```text
Open and use these sibling folders together:

1. C:\Users\<you>\Downloads\codexalpaca_repo
2. C:\Users\<you>\Downloads\CodexAlpacaTest-TradeMigratyion
3. C:\Users\<you>\Downloads\qqq_options_30d_cleanroom

Operate as the nightly research operator under the institutional blueprint.

Read first:
- docs/INSTITUTIONAL_OPERATING_BLUEPRINT.md
- docs/REPO_UPDATE_CONTROL.md
- docs/AGENT_GOVERNANCE.md
- docs/SESSION_RECONCILIATION_REGISTRY.md
- docs/EXECUTION_CALIBRATION_REGISTRY.md
- docs/TOURNAMENT_PROFILE_REGISTRY.md
- docs/TOURNAMENT_UNLOCK_REGISTRY.md
- docs/TOURNAMENT_UNLOCK_WORKPLAN.md
- docs/EXECUTION_EVIDENCE_CONTRACT.md
- docs/NIGHTLY_OPERATOR_PLAYBOOK.md
- docs/AGENT_OPERATING_MODEL.md
- docs/STRATEGY_FAMILY_REGISTRY.md
- docs/STRATEGY_FAMILY_STEWARD.md

Your job is to run one disciplined nightly cycle that:
1. refreshes the repo update registry and handoff so GitHub drift is visible before work begins
2. refreshes the session reconciliation registry and handoff from paper-runner session bundles
3. refreshes the execution calibration registry and execution calibration handoff from paper-runner evidence, using the fresh session-reconciliation handoff so review-required sessions, including broker/local economics-drift sessions, do not loosen research policy
4. refreshes the tournament profile registry and tournament profile handoff, respecting execution evidence floors and audit gates before activating more aggressive or opening-window profiles
5. refreshes the tournament unlock registry and tournament unlock handoff so the machine can explain what evidence or implementation work still blocks the next profile tier
6. refreshes the tournament unlock workplan and workplan handoff so the research plane and execution plane each get one explicit next mission
7. refreshes the execution evidence contract and contract handoff so the next trusted paper session has an explicit acceptance checklist
8. refreshes the family registry and handoff packet
9. refreshes the ticker coverage view
10. materializes any missing priority symbols when needed
11. runs the next family discovery wave
12. runs exhaustive follow-up on survivors
13. validates challengers against the current live champion book
14. builds hardening review, replacement plan, and morning handoff packets
15. leaves the live manifest unchanged unless I explicitly approve a reviewed add/replace packet

Hard rules:
- Do not auto-promote strategies into the live manifest.
- Do not shrink the live book accidentally.
- Treat any lane without `master_summary.json` as failed.
- Use the GitHub-backed docs and packets as the source of truth, not memory.
- Keep discovery parallel and production decisions serialized.

Execution order:
1. Run `launch_repo_update_check.ps1`
2. Run `build_session_reconciliation_registry.py`
3. Run `build_session_reconciliation_handoff.py`
4. Run `build_execution_calibration_registry.py`
5. Run `build_execution_calibration_handoff.py`
6. Run `build_tournament_profile_registry.py`
7. Run `build_tournament_profile_handoff.py`
8. Run `build_tournament_unlock_registry.py`
9. Run `build_tournament_unlock_handoff.py`
10. Run `build_tournament_unlock_workplan.py`
11. Run `build_tournament_unlock_workplan_handoff.py`
12. Run `build_execution_evidence_contract.py`
13. Run `build_execution_evidence_contract_handoff.py`
14. Run `build_strategy_family_registry.py`
15. Run `build_strategy_family_handoff.py`
16. Run `build_ticker_family_coverage.py`
17. If needed, run `materialize_backtester_ready.py`
18. Build and validate the Phase 1 launch pack
19. Run the discovery lanes
20. Build the shortlist
21. Build and validate the Phase 2 launch pack
22. Run exhaustive follow-up
23. Run shared-account validation
24. Build hardening review
25. Build replacement plan
26. Build morning handoff
27. Refresh the run-registry packet and active-program packet where appropriate

Prefer using `cleanroom/code/qqq_options_30d_cleanroom/launch_nightly_operator_cycle.ps1` as the top-level entrypoint when it is available, so the cycle is executed as one governed operator flow instead of a loose sequence of manual steps. If you need to inspect or repair a phase, do that surgically, then return to the top-level cycle.
Use the tournament profile registry and tournament profile handoff together so the machine resolves the nightly cycle from approved executable profiles plus current execution posture, instead of treating profile choice as a static prompt default.
Use the tournament unlock registry and tournament unlock handoff to explain what evidence or implementation work still blocks the next profile tier, instead of inferring unlock conditions from scattered reasons or score penalties.
Use the tournament unlock workplan and workplan handoff to keep the next research-plane mission and the next execution-plane evidence mission separate and explicit.
Use the execution evidence contract and contract handoff to make the next paper-runner session pass or fail against a concrete acceptance checklist instead of a vague telemetry goal.

Output requirements:
- show what ran
- show what families were targeted
- show what failed, if anything
- show which challengers survived
- show whether any `review_add` or `review_replace` packets were produced
- show whether the paper-runner gate is aligned with the morning handoff
- explicitly state that the live manifest remains unchanged unless an approval step happened
```
