# QQQ Pair Micro-Optimization Input Digest

## Exact files opened

- `C:\Users\rabisaab\Downloads\recent_2m_final_decision.md`: opened
- `C:\Users\rabisaab\Downloads\tomorrow_paper_readiness.md`: opened
- `C:\Users\rabisaab\Downloads\tomorrow_alpaca_paper_runbook.md`: opened
- `C:\Users\rabisaab\Downloads\recent_2m_metrics.csv`: opened
- `C:\Users\rabisaab\Downloads\recent_2m_trade_ledger.csv`: opened
- `C:\Users\rabisaab\Downloads\tournament_master_report.md`: opened
- `C:\Users\rabisaab\Downloads\master_strategy_memo.txt`: opened

## Harness used

- Repo/backtest harness: `C:\Users\rabisaab\Downloads\nasdaq-etf-intraday-alpaca\src\app\paper_promotion.py` bar-only adverse-cost evaluation path.
- Source data: `C:\Users\rabisaab\Downloads\alpaca-stock-strategy-research\data\pair_rotation\tqqq_sqqq_1min_20230401_20260401.parquet`.
- Core signal semantics held fixed: opening window `10`, decision interval `15m`, same pair breakout logic, same adverse bar-cost model, same 50% notional reference.

## Date windows used

- Recent 2 months: `2026-02-02` through `2026-03-31`.
- Recent 6 months: `2025-10-01` through `2026-03-31`.
- Existing paper-promotion validation window: `2025-07-01` through `2025-12-31`.

## Data limitations

- The blocked-opening variant was not tested because the current implementation only supports blocking whole hours, not just the earliest eligible decision bucket cleanly.
- This was intentionally a tiny sweep: threshold, start-delay, and flatten-buffer one-variable checks plus one combined finalist.
