# GCP Paper Winner Session Readiness

## Snapshot

- Generated at: `2026-04-24T00:44:44.323668-04:00`
- Status: `building_sample_with_raw_winners`
- Minimum net PnL for raw winner: `$200.00`
- Target qualified winners: `20`
- Raw winner count: `1`
- Qualified winner count: `0`
- Qualified winners remaining: `20`
- Review-required raw winners: `1`

## Session Ledger

| Date | Net PnL | Raw Winner | Qualified Winner | Evidence | Teaching | Disqualifiers |
|---|---:|---|---|---|---|---|
| 2026-04-21 | 0.00 | False | False | missing | missing | net_pnl_below_winner_threshold, evidence_status_missing, teaching_gate_not_ok |
| 2026-04-22 | 1992.50 | True | False | review_required | review_required | evidence_status_review_required, teaching_gate_not_ok, broker_local_economics_drift |
| 2026-04-23 | -1717.00 | False | False | review_required | review_required | net_pnl_below_winner_threshold, evidence_status_review_required, teaching_gate_not_ok, broker_local_economics_drift, severe_loss_incident |

## Operator Read

- A raw winner only proves the session ended above the PnL threshold.
- A qualified winner must also be flat, reconciled, evidence-clean, teaching-gate clean, and free of severe-loss incidents.
- Do not use raw winners alone for live-trading confidence.

## Next Actions

- Keep the research arm aggressive while the paper runner accumulates qualified winners.
- Use loser-learning and quality scorecards to improve the chance that future sessions clear the qualified-winner gate.
- Treat review-required winners as useful diagnostics, not as live-readiness evidence.
