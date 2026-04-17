# Recent Options Shadow Input Digest

Opened files:
- `C:\Users\rabisaab\Downloads\recent_2m_final_decision.md`
- `C:\Users\rabisaab\Downloads\tomorrow_paper_readiness.md`
- `C:\Users\rabisaab\Downloads\tomorrow_alpaca_paper_runbook.md`
- `C:\Users\rabisaab\Downloads\qqq_pair_monday_variant_decision.md`
- `C:\Users\rabisaab\Downloads\recent_2m_trade_ledger.csv`
- `C:\Users\rabisaab\Downloads\recent_2m_metrics.csv`

Exact dates used: `2026-04-01, 2026-04-02, 2026-04-03`
Replay date range: `2026-04-01` through `2026-04-03`
- Recent stock bars were available directly from Alpaca for QQQ/TQQQ/SQQQ.
- RTH-only filtering was applied before rebuilding the pair signals.
- Recent QQQ option bars and trades were available directly from Alpaca for the replay dates.
- Historical option quotes were not available from the Alpaca endpoint used here, so bid/ask/mid fields remain unresolved rather than fabricated.
- Exact 2 DTE and exact 1-strike OTM were selected when available; nearest valid fallback was logged otherwise.
- Recent options replay therefore remains an honest shadow study, not a quote-accurate execution study.
