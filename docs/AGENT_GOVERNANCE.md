# Agent Governance

This repo now keeps a machine-readable governance layer for the agent system, not just a prose operating model.

## Source Of Truth

- Builder:
  - `cleanroom/code/qqq_options_30d_cleanroom/build_agent_governance_registry.py`
- Generated artifacts:
  - `docs/agent_governance/agent_governance_registry.json`
  - `docs/agent_governance/agent_governance_registry.csv`
  - `docs/agent_governance/agent_governance_registry.md`

## Why It Exists

The operating model tells us which agents exist.

The governance registry makes three institutional decisions explicit:

- discovery agents are split by `family_cohort`
- exhaustive validators are split by `ticker_bundle`
- production decisions stay with a single `live_book` writer

It also makes execution feedback explicit by naming the `Execution Calibration Steward` as the packet-only owner of paper-runner fill, guardrail, and loss evidence before major nightly profile choices.

It also captures:

- which machine should prefer each role now versus later
- which roles may launch backtests
- which roles may edit strategy code
- which roles may update the runner gate
- which roles may write the live manifest
- which actions remain human-gated

## Refresh Command

From the repo root:

```powershell
python .\cleanroom\code\qqq_options_30d_cleanroom\build_agent_governance_registry.py
```

## When To Refresh

- after changing the agent operating model
- after adding a new discovery or validation lane
- before handing a new nightly workflow to the new machine
- before widening automation authority in the execution plane

## Institutional Use

Use this registry as the machine-readable policy layer when deciding:

- whether work should be sharded by family or by ticker
- which machine should own a role
- whether a role may act autonomously or only produce packets
- whether a role may touch the live manifest or runner gate
