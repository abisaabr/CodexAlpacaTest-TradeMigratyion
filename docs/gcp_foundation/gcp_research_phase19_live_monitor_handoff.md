# GCP Research Phase Live Monitor Handoff

- Status: `failed_runtime_cap_repaired_by_phase20`
- Batch state: `FAILED`
- Active stage: `none_phase19_closed`
- Latest observed symbol family: `AMZN option contracts`
- Latest observed download date: `2026-04-16`
- Selected-contract files at checkpoint: `266`
- Raw download files at checkpoint: `17073`
- Silver download files at checkpoint: `17339`
- Replay files: `0`
- Portfolio-report files: `0`
- Promotion-review state: `not_started`
- GCS final artifacts visible: `False`
- Latest checkpoint prefix: `gs://codexalpaca-control-us/research_results/top100_liquidity_research_20260426/phase19_live_checkpoints/20260427T155608Z`
- Repair job: `phase20-sharded-fill-repair-20260428031000`
- Repair launch state: `SCHEDULED`
- Repair launch packet: `gs://codexalpaca-control-us/research_results/top100_liquidity_research_20260426/portfolio_event_driven_data/phase20_sharded_fill_repair_20260428031000/launch/`

## Operator Rule

- Do not relaunch or terminate a running phase while the active stage is producing files or fresh logs.
- Phase19 is no longer running; it failed at the Batch runtime cap before final artifacts were produced.
- Phase20 is the smaller sharded repair path and should be monitored before any replay/promotion decision.
- This is research-only. Do not arm windows, start trading, change live manifests, or change risk policy from this packet.
