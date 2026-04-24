# GCP Overnight Research Data Lane Handoff

## Current Read

- The Friday April 24, 2026 target is still one bounded sanctioned VM paper session on `vm-execution-paper-01`.
- The execution window is not armed.
- The research lane may run overnight because it is non-broker-facing and advisory.
- Research outputs must not mutate live strategy selection, risk policy, or manifests.

## Overnight Mission

Use existing downloader, backtest, paper-session, runtime, GCP, and Alpaca-derived evidence assets to produce a governed research substrate and better Friday/Monday selection quality.

## Governed Universe

- `QQQ`
- `SPY`
- `IWM`
- `NVDA`
- `MSFT`
- `AMZN`
- `TSLA`
- `PLTR`
- `XLE`
- `GLD`
- `SLV`

## Required Outputs

- April 23 evidence remains finalized and mirrored.
- April 24 Friday quality scorecard remains current.
- Existing downloader and data inventory is produced.
- Bounded GCS research layout is used for raw, curated, and derived outputs.
- Data-quality verdicts are produced before research outputs are trusted.
- Loser-learning tables classify April 23 losses by symbol, family, daypart, regime, structure, exit reason, and execution quality.

## Hard Boundaries

- Do not arm the exclusive execution window.
- Do not start trading.
- Do not start a broker-facing paper session.
- Do not widen the temporary parallel-runtime exception.
- Do not change live manifest, strategy selection, or risk policy.
- Do not ingest full-chain tick, L2, news, or broad-universe data tonight.

## Morning Success Definition

- GitHub `main` and GCS mirrors are current.
- Friday scorecard is available under `gs://codexalpaca-control-us/research_scorecards/2026-04-24/`.
- Research-data inventory and quality verdicts are available in GCS.
- April 23 loser clusters are summarized for operator review.
- The next live action remains the same: pause the temporary parallel path, arm the exclusive window, confirm `ready_for_launch` and `ready_to_launch`, then launch the single sanctioned VM session.

## Priority Order

1. Execution safety and packet clarity.
2. Evidence and teaching-gate freshness.
3. Friday scorecard freshness.
4. Existing research-data inventory.
5. Data-quality checks.
6. Loser-learning backfill.
7. Bounded market-data fills.

