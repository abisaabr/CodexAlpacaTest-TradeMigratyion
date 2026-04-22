# Overnight Phased Plan

This guide defines the governed overnight plan packet for the two-machine operating model.

Use it when the goal is to answer:
- what should the current research machine do tonight
- what should the new machine do tonight
- what must stay blocked tonight
- what evidence must land before the next tournament tier can be reconsidered tomorrow

The overnight phased plan is built from the current control-plane handoffs, not from memory:
- `docs/repo_updates/repo_update_handoff.json`
- `docs/tournament_unlocks/tournament_unlock_handoff.json`
- `docs/tournament_unlocks/tournament_unlock_workplan_handoff.json`
- `docs/execution_evidence/execution_evidence_contract_handoff.json`

Generated outputs:
- `docs/overnight_plan/overnight_phased_plan.json`
- `docs/overnight_plan/overnight_phased_plan.md`
- `docs/overnight_plan/overnight_phased_plan_handoff.json`
- `docs/overnight_plan/overnight_phased_plan_handoff.md`

Primary builder flow:
1. `build_overnight_phased_plan.py`
2. `build_overnight_phased_plan_handoff.py`

What the packet should do:
- keep the currently unlocked governed profile explicit
- make the current research-plane mission explicit
- make the current execution-plane evidence mission explicit
- restate the next-session evidence contract in operational terms
- keep blocked profiles blocked until their real gates are cleared
- give the operator a by-morning success definition

Institutional rule:
- the overnight phased plan is an operator packet, not a permission slip
- it must not override repo update control, session reconciliation, execution calibration, tournament unlock policy, or review gates
- if those upstream packets change, rebuild the overnight phased plan instead of improvising
