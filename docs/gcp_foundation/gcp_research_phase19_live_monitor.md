# GCP Research Phase Live Monitor

## Snapshot

- Generated at: `2026-04-27T11:52:42.832895-04:00`
- Job ID: `phase19-targeted-fill-diagnostic-20260427022000`
- Wave ID: `top100_liquidity_research_20260426`
- Status: `running_active_downloader`
- Batch state: `RUNNING`
- Observed runtime seconds: `48922`
- Batch VM: `phase19-targeted-f-8f0eaf56-aa9c-40b50-group0-0-ths5`
- Container: `1303f69b-face-4dab-aae3-eb4316b4ed79`
- Container status: `Up 14 hours`
- Active stage: `download_option_market_data_for_selected_contracts`
- Active stage detail: Alpaca options-data downloader is still active; replay and portfolio-report stages have not started.
- Latest log observation text: `04/27/26 15:52:34`
- Latest observed symbol family: `AMZN option contracts`
- Latest observed download date: `2026-04-01`

## Local Container Evidence

- Selected-contract files: `266`
- Raw download files: `17036`
- Raw download bytes: `263647854`
- Silver download files: `17302`
- Silver download bytes: `142782729`
- Download-report files: `0`
- Replay files: `0`
- Portfolio-report files: `0`
- Promotion-review files: `0`
- GCS final artifacts visible: `False`
- Artifact upload model: `final_exit_trap`
- Promotion-review state: `not_started`

## Operator Read

- Do not relaunch or terminate a running phase while the active stage is producing files or fresh logs.
- Expect final GCS artifacts only after the container exits if the job uses an exit-trap upload model.
- If the job fails, inspect run.err.log, downloader manifest, and partial local/GCS data before deciding on a smaller sharded repair.
- This is research-only. Do not arm windows, start trading, change live manifests, or change risk policy from this packet.

## Guardrails

- Broker-facing: `False`
- Trading started: `False`
- Manifest changed: `False`
- Risk policy changed: `False`
