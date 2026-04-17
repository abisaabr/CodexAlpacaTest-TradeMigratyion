# Other Machine Handoff

Approved strategy set for Monday 2026-04-06:
- `qqq_led_tqqq_sqqq_pair_opening_range_intraday_system` only.

Not approved for Monday trading:
- `down_streak_exhaustion`
- `relative_strength_vs_benchmark::rs_top3_native`
- `cross_sectional_momentum::csm_native`

Handoff folder:
- `C:\Users\rabisaab\Downloads\alpaca_paper_handoff_20260406`

Files prepared:
- `C:\Users\rabisaab\Downloads\alpaca_paper_handoff_20260406\README.md`
- `C:\Users\rabisaab\Downloads\alpaca_paper_handoff_20260406\.env.template`
- `C:\Users\rabisaab\Downloads\alpaca_paper_handoff_20260406\paper_shared_config.yaml`
- `C:\Users\rabisaab\Downloads\alpaca_paper_handoff_20260406\run_qqq_pair_paper.ps1`
- `C:\Users\rabisaab\Downloads\alpaca_paper_handoff_20260406\scheduler_setup_note.md`

Operational note:
- The QQQ pair remains the only approved paper strategy because it was the only recent-window strategy with positive PnL and it already held the strongest operational trust in the earlier work.
- The runtime config in this handoff aligns the live paper engine as closely as the repo allows to the approved opening-range baseline, but the runtime still uses stricter operational safeguards than the pure bar-only backtest harness.
- Do not add RS, CSM, or DSE to Monday's live paper runtime just because they are available locally.

Launch expectation:
- Start the runtime before the open, monitor logs during RTH, and archive the daily reports after the close.
