# GCP Research To First Promotion Handoff

## Current Read

- The research arm is no longer limited to the next paper-trading session.
- It should run continuously and aggressively, provided it remains advisory.
- The first promotion target is a research-plane promotion to `governed_validation_candidate`, not a live or broker-facing promotion.

## Current Assets

- Historical dataset builder: `scripts/build_historical_dataset.py`
- Sample backtest runner: `scripts/run_sample_backtest.py`
- Sample backtest config: `config/backtest.example.yaml`
- Strategy configs and live manifest exist in the runner repo.
- Runtime sessions exist for April 21-23.
- April 23 evidence is complete but `review_required`.
- Research asset inventory is `ready_for_research_bootstrap`.

## Multi-Agent Workstreams

- Research Program Steward: owns roadmap and promotion packet.
- Data Foundation Engineer: owns GCS data and quality.
- Strategy Librarian: owns strategy/family metadata.
- Backtest Factory Engineer: owns brute-force runs.
- Statistical Validation Analyst: owns robustness and anti-overfit gates.
- Loser-Learning Analyst: owns loser clusters and failure taxonomy.
- Promotion Steward: owns promote/hold/kill/quarantine decision.
- Cloud Cost And Reliability Steward: owns GCS hygiene and job cost.

## Phase Order

1. Safety and separation.
2. Research asset inventory.
3. Strategy registry bootstrap.
4. Data-quality baseline.
5. Evidence normalization.
6. First brute-force wave.
7. Anti-overfit and robustness gate.
8. First promotion packet.
9. Paper validation readiness checklist.

## First Promotion Definition

Allowed:

- `research_only` -> `governed_validation_candidate`

Not allowed from research alone:

- live manifest change
- risk-policy change
- broker-facing activation
- profile unlock
- production execution candidate

## First Brute-Force Waves

- `wave_1_index_defined_risk_opening`: `QQQ`, `SPY`, `IWM`
- `wave_2_qqq_choppy_premium`: `QQQ`
- `wave_3_single_leg_trend_filter_repair`: `NVDA`, `AMZN`, `PLTR`, `IWM`, `SPY`
- `wave_4_regime_diversifiers`: `GLD`, `SLV`, `XLE`

## Promotion Bar

A first research promotion requires:

- train/test or walk-forward separation
- positive after-cost test result
- slippage and fee stress survival
- no single-day PnL concentration above `35%`
- no unresolved data-quality defect
- complete strategy metadata
- loser taxonomy without repeated structural defect

If no candidate clears the bar, the correct decision is `hold`.

## Next Safe Action

Build the strategy registry bootstrap, then the data-quality baseline, then normalize paper-session evidence before launching broad brute-force sweeps.

