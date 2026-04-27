# GCP Research Phase19 Live Monitor

## Snapshot

- Generated at: `2026-04-27T11:39:00-04:00`
- Job ID: `phase19-targeted-fill-diagnostic-20260427022000`
- Wave ID: `top100_liquidity_research_20260426`
- Status: `running_active_downloader`
- Batch state: `RUNNING`
- Observed runtime seconds: `48076`
- Batch VM: `phase19-targeted-f-8f0eaf56-aa9c-40b50-group0-0-ths5`
- Container: `1303f69b-face-4dab-aae3-eb4316b4ed79`
- Active stage: `download_option_market_data_for_selected_contracts`
- Latest log observation UTC: `2026-04-27T15:38:52Z`
- Latest observed symbol family: `AMZN option contracts`
- Latest observed download date: `2026-03-27`

## Local Container Evidence

- Selected-contract files: `266`
- Raw download files: `16898`
- Raw download bytes: `261911981`
- Silver download files: `17164`
- Silver download bytes: `141954301`
- Download-report files: `0`
- Replay files: `0`
- Portfolio-report files: `0`
- GCS final artifacts visible: `False`
- Artifact upload model: `final_exit_trap`
- Promotion-review state: `not_started`

## Operator Read

- Do not relaunch or kill Phase19 solely because GCS final artifacts are absent; this job uploads final artifacts on exit.
- The active container has already produced local raw and silver option-data files, so the job is doing useful work.
- Replay, portfolio report, and promotion-review packet have not started yet.
- Next action is monitoring or adding future heartbeat/progress upload support, not changing live manifests or trading policy.

## Guardrails

- Broker-facing: `False`
- Trading started: `False`
- Manifest changed: `False`
- Risk policy changed: `False`
