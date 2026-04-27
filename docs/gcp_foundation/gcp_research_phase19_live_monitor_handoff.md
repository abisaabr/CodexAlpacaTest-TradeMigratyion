# GCP Research Phase Live Monitor Handoff

- Status: `running_active_downloader`
- Batch state: `RUNNING`
- Active stage: `download_option_market_data_for_selected_contracts`
- Latest observed symbol family: `AMZN option contracts`
- Latest observed download date: `2026-04-01`
- Selected-contract files: `266`
- Raw download files: `17036`
- Silver download files: `17302`
- Replay files: `0`
- Portfolio-report files: `0`
- Promotion-review state: `not_started`
- GCS final artifacts visible: `False`
- Latest lightweight checkpoint: `gs://codexalpaca-control-us/research_results/top100_liquidity_research_20260426/phase19_live_checkpoints/20260427T155608Z`

## Operator Rule

- Do not relaunch or terminate a running phase while the active stage is producing files or fresh logs.
- Expect final GCS artifacts only after the container exits if the job uses an exit-trap upload model.
- If the job fails, inspect run.err.log, downloader manifest, and partial local/GCS data before deciding on a smaller sharded repair.
- This is research-only. Do not arm windows, start trading, change live manifests, or change risk policy from this packet.
