# GCP Paper Session Learning Packet

## Snapshot

- Generated at: `2026-04-24T05:56:14.766138-04:00`
- Status: `blocked_no_governed_validation_candidate`
- Raw winners: `1`
- Qualified winners: `0`
- Qualified winners remaining: `20`

## Session Ledger

| Date | Net PnL | Trades | Flat | Evidence | Teaching | Raw Winner | Qualified | Disqualifiers |
|---|---:|---:|---|---|---|---|---|---|
| 2026-04-21 | 0.00 | 0 | True | missing | missing | False | False | net_pnl_below_winner_threshold, evidence_status_missing, teaching_status_missing |
| 2026-04-22 | 1992.50 | 10 | True | review_required | review_required | True | False | evidence_status_review_required, teaching_status_review_required |
| 2026-04-23 | -1717.00 | 14 | True | review_required | review_required | False | False | net_pnl_below_winner_threshold, evidence_status_review_required, teaching_status_review_required, severe_loss_incident |

## Governed Universe Verdicts

| Symbol | Score | Stance | Research Rows | Selected Contracts | Verdict |
|---|---:|---|---:|---:|---|
| QQQ | 77.0 | preferred_if_preopen_liquidity_clean | 2276 | 420 | research_ready_with_quality_score |
| SPY | 43.4 | shadow_or_reduced_only | 0 | 0 | shadow_only |
| IWM | 28.2 | avoid_for_first_gcp_session | 0 | 0 | avoid_for_first_session |
| NVDA | 1.0 | avoid_for_first_gcp_session | 0 | 0 | avoid_for_first_session |
| MSFT | 60.0 | allowed_cautious | 2218 | 196 | research_ready_with_quality_score |
| AMZN | 11.2 | avoid_for_first_gcp_session | 0 | 0 | avoid_for_first_session |
| TSLA | 60.0 | allowed_cautious | 2300 | 238 | research_ready_with_quality_score |
| PLTR | 20.0 | avoid_for_first_gcp_session | 0 | 0 | avoid_for_first_session |
| XLE | 51.4 | shadow_or_reduced_only | 0 | 0 | shadow_only |
| GLD | 60.0 | allowed_cautious | 1947 | 238 | research_ready_with_quality_score |
| SLV | 60.0 | allowed_cautious | 2171 | 238 | research_ready_with_quality_score |

## Loser Learning

- Normalized trades: `24`
- Winners: `8`
- Losers: `16`
- Total loser PnL: `-2379.89`

### Top Losing Symbols

- `GDX` trades `2` net `-632.01` stops `2`
- `NVDA` trades `2` net `-540.62` stops `2`
- `PLTR` trades `2` net `-411.71` stops `1`
- `IWM` trades `2` net `-255.8` stops `1`
- `AMZN` trades `3` net `-215.33` stops `3`
- `SPY` trades `2` net `-181.41` stops `1`
- `BAC` trades `1` net `-90.6` stops `1`
- `SCHW` trades `1` net `-41.3` stops `1`

### Learning Actions

- Suppress or shadow symbols with repeated stop-loss and single-leg directional loser similarity until new evidence clears.
- Require option-aware fill coverage before promoting sparse positive backtest candidates.
- Prefer defined-risk or reduced-risk structures for symbols that repeatedly lose through single-leg directional exits.

## Promotion Readiness

- Candidate state: `blocked_no_governed_validation_candidate`
- Promotion allowed: `False`
- Option-aware status: `hold_option_economics_review`

### Blockers

- `qualified_winner_count_0_below_target_20`
- `session_evidence_or_teaching_review_required`
- `severe_loss_incident_present`
- `option_aware_status_hold_option_economics_review`

### Smallest Next Evidence Package

- Run the April 24 bounded VM paper session and require flat, reconciled, evidence-clean closeout.
- Resolve evidence/teaching review on prior raw winner before counting it as qualified.
- Improve option-aware fill coverage or add quote/spread evidence before considering SLV research candidates.
- Keep Friday execution limited by the current quality scorecard; use loser clusters only as suppressors, not promotions.
