# GCP Research Phase19 Live Monitor Handoff

- Status: `running_active_downloader`
- Batch state: `RUNNING`
- Active stage: `download_option_market_data_for_selected_contracts`
- Latest observed symbol family: `AMZN option contracts`
- Selected-contract files: `266`
- Raw download files: `16898`
- Silver download files: `17164`
- Replay files: `0`
- Portfolio-report files: `0`
- Promotion-review state: `not_started`
- GCS final artifacts visible: `False`

## Operator Rule

- Continue monitoring Phase19; do not relaunch or terminate while the downloader is active and producing files.
- Expect final GCS artifacts only after the container exits and its upload trap runs.
- If the job fails, inspect `run.err.log`, downloader manifest, and partial local/GCS data before deciding whether to relaunch a smaller sharded repair.
- This is research-only. Do not arm windows, start trading, change live manifests, or change risk policy from this packet.
