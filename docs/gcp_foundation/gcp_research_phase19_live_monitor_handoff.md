# GCP Research Phase Live Monitor Handoff

- Status: `phase20_repair_succeeded_phase21_replay_launched`
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
- Repair state: `SUCCEEDED`
- Repair launch packet: `gs://codexalpaca-control-us/research_results/top100_liquidity_research_20260426/portfolio_event_driven_data/phase20_sharded_fill_repair_20260428031000/launch/`
- Repair failed chunks: `0`
- Repair option bar rows: `1002599`
- Repair option trade rows: `2317496`
- Replay job: `phase21-replay-from-phase20-20260428034200`
- Replay launch state: `SCHEDULED`
- Replay launch packet: `gs://codexalpaca-control-us/research_results/top100_liquidity_research_20260426/portfolio_event_driven_data/phase21_replay_from_phase20_20260428034200/launch/`

## Operator Rule

- Do not relaunch or terminate a running phase while the active stage is producing files or fresh logs.
- Phase19 is no longer running; it failed at the Batch runtime cap before final artifacts were produced.
- Phase20 succeeded and Phase21 is the active replay/promotion-review path to monitor.
- This is research-only. Do not arm windows, start trading, change live manifests, or change risk policy from this packet.
