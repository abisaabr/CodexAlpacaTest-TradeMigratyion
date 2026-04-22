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
- docs/AGENT_GOVERNANCE.md
- docs/EXECUTION_CALIBRATION_REGISTRY.md
- docs/TOURNAMENT_PROFILE_REGISTRY.md
- docs/NIGHTLY_OPERATOR_PLAYBOOK.md
- docs/AGENT_OPERATING_MODEL.md
- docs/STRATEGY_FAMILY_REGISTRY.md
- docs/STRATEGY_FAMILY_STEWARD.md

Your job is to run one disciplined nightly cycle that:
1. refreshes the execution calibration registry and execution calibration handoff from paper-runner evidence
2. refreshes the family registry and handoff packet
3. refreshes the ticker coverage view
4. materializes any missing priority symbols when needed
5. runs the next family discovery wave
6. runs exhaustive follow-up on survivors
7. validates challengers against the current live champion book
8. builds hardening review, replacement plan, and morning handoff packets
9. leaves the live manifest unchanged unless I explicitly approve a reviewed add/replace packet

Hard rules:
- Do not auto-promote strategies into the live manifest.
- Do not shrink the live book accidentally.
- Treat any lane without `master_summary.json` as failed.
- Use the GitHub-backed docs and packets as the source of truth, not memory.
- Keep discovery parallel and production decisions serialized.

Execution order:
1. Run `build_execution_calibration_registry.py`
2. Run `build_execution_calibration_handoff.py`
3. Run `build_strategy_family_registry.py`
4. Run `build_strategy_family_handoff.py`
5. Run `build_ticker_family_coverage.py`
6. If needed, run `materialize_backtester_ready.py`
7. Build and validate the Phase 1 launch pack
8. Run the discovery lanes
9. Build the shortlist
10. Build and validate the Phase 2 launch pack
11. Run exhaustive follow-up
12. Run shared-account validation
13. Build hardening review
14. Build replacement plan
15. Build morning handoff
16. Refresh the run-registry packet and active-program packet where appropriate

Prefer using `cleanroom/code/qqq_options_30d_cleanroom/launch_nightly_operator_cycle.ps1` as the top-level entrypoint when it is available, so the cycle is executed as one governed operator flow instead of a loose sequence of manual steps. If you need to inspect or repair a phase, do that surgically, then return to the top-level cycle.
Use the tournament profile registry to decide whether to run the default `down_choppy_coverage_ranked` cycle, the `down_choppy_full_ready` fallback, or a still-planned opening-window profile that should remain in design rather than execution.

Output requirements:
- show what ran
- show what families were targeted
- show what failed, if anything
- show which challengers survived
- show whether any `review_add` or `review_replace` packets were produced
- show whether the paper-runner gate is aligned with the morning handoff
- explicitly state that the live manifest remains unchanged unless an approval step happened
```
