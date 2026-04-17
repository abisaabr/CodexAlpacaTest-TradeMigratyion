# Strategy Consolidation And Paper Run

Generated: 2026-04-06T11:27:26.188080-04:00

## Local Research Conclusions
- Best confirmed research family: `down_streak_exhaustion`.
- Best deployable intraday engine: `qqq_led_tqqq_sqqq_pair_opening_range_intraday_system`.
- Best paper-only supporting family: durable cRSI presets.
- Latest local runbook approved only the QQQ-led pair for the Monday 2026-04-06 session.
- This run preserved existing account positions and only submitted new orders where the live signal and symbol-specific backtest both cleared risk gates.

## Account Snapshot
- Equity: `96667.73`
- Buying power: `315103.72`
- Options trading level: `3`
- Open positions before this run: `4`

## Active Strategy Variants Today
- `AMD` | `rs_lb60_hold20_thr0p0` | PF `2.69` | return `85.14%` | drawdown `32.66%`
- `AMD` | `rs_lb60_hold20_thr0p05` | PF `2.37` | return `65.86%` | drawdown `32.66%`
- `AMD` | `rs_lb60_hold10_thr0p0` | PF `1.96` | return `34.94%` | drawdown `17.78%`
- `AMD` | `pullback_pw55_dd0p05_hold10` | PF `1.89` | return `36.54%` | drawdown `16.02%`
- `AMD` | `rs_lb60_hold10_thr0p05` | PF `1.85` | return `28.81%` | drawdown `18.63%`
- `AMD` | `rs_lb60_hold5_thr0p05` | PF `1.75` | return `18.84%` | drawdown `10.63%`
- `AMD` | `rs_lb60_hold5_thr0p0` | PF `1.67` | return `18.60%` | drawdown `10.59%`
- `AMD` | `pullback_pw55_dd0p03_hold10` | PF `1.66` | return `32.77%` | drawdown `17.88%`
- `AMD` | `pullback_pw55_dd0p05_hold5` | PF `1.57` | return `18.74%` | drawdown `10.31%`
- `AMD` | `pullback_pw55_dd0p03_hold5` | PF `1.48` | return `18.18%` | drawdown `10.57%`
- `AMD` | `rs_lb20_hold5_thr0p05` | PF `1.19` | return `4.12%` | drawdown `11.52%`
- `AMD` | `rs_lb20_hold5_thr0p0` | PF `1.15` | return `4.45%` | drawdown `14.41%`

## Orders Submitted
- `AMD` | status `new` | variant `rs_lb60_hold10_thr0p0` | qty `15` | limit `219.79` | stop `212.09` | take-profit `233.65`

## Source Notes
Source: best_strategies_consolidated.txt
BEST STRATEGIES CONSOLIDATED
Scan date: 2026-04-04 America/New_York
Scope scanned: C:\Users\rabisaab\Downloads recursively, with emphasis on text-readable repo/report/config/code files and strategy result artifacts.

EXECUTIVE SUMMARY

I found 13 canonical strategy families/entries after grouping closely related versions.

Highest-confidence conclusions:
- Overall best confirmed backtest candidate: down_streak_exhaustion in C:\Users\rabisaab\Downloads\alpaca-stock-strategy-research. It is the strongest combination of confirmed net return, profit factor, Sharpe, drawdown control, stressed-cost survival, and benchmark-beating evidence, but the repo's own confirmation verdict is still "fragile" because subset and regime robustness are uneven.
- Best practical / deployable system: the QQQ-led TQQQ/SQQQ pair opening-range intraday system in C:\Users\rabisaab\Downloads\nasdaq-etf-intraday-alpaca. It has explicit paper-trading runbooks, validation/promotion artifacts, guarded live path, and positive adverse-cost validation/test PnL, but promotion is still blocked by slippage realism and concentration.
- Best paper-only supporting signal family: durable cRSI presets in C:\Users\rabisaab\Downloads\alpaca-stock-strategy-research. These are symbol-specific, overnight-aware, and surprisingly resilient at 10-15 bps friction, but the paper sample is too short and every preset is still marked needs_cleaner_ops.

Source: daily_paper_engine_candidates.md
# Daily Paper-Engine Candidates

- `qqq_led_tqqq_sqqq_pair_opening_range_intraday_system`: estimated `2.15` trade events per active day across the adverse baseline slice; symbols `QQQ -> TQQQ/SQQQ`; option structure `shadow only for now`; average hold `intraday, flat before close`; overlap `low-to-moderate`; portfolio heat `50% notional in native spec`; liquidity concern `options replay still blocked by historical quote gap`; standalone use `best`; >60% win-rate screen `no (59.32% test)`; $100k screen `not evaluated on a full 5-year window`; robustness under conservative fills `yes in adverse, not enough for promotion`; edge cluster `10:00 hour`; deployability `paper-only now, promotion blocked`.
- `down_streak_exhaustion`: estimated `0.18` trades/day on the standardized 5-year user subset; symbols `SPY, QQQ, IWM, NVDA, META, AAPL, AMZN, NFLX, TSLA`; option structure `not recommended until daily timestamp-to-option replay is solved`; average hold `2-5 trading days`; overlap `moderate across symbols`; portfolio heat `low`; liquidity concern `daily option decay and no quote history`; >60% win-rate screen `no`; $100k screen `no on the user subset`; robustness `fragile`; edge cluster `META and TSLA pockets`; deployability `research-only benchmark, not a promoted sleeve`.
- `durable_crsi_family`: trade frequency is too low and overnight dependence is too strong for the current options-paper goal; deployability `watchlist-only` until more live paper evidence accumulates.
- `momentum_relative_strength_family`: the standardized 5-year user-subset run clears both the >60% win-rate and $100k growth screens, but the family still fails trust and concentration checks; deployability `research-only challenger`, not paper-engine ready.
- `breakout_trend_continuation_family`: moderate daily frequency, but the evidence stack is too conflicted for paper promotion; deployability `research-only`.

Source: recent_2m_final_decision.md
# Recent 2-Month Final Decision

Window target used: `2026-02-02` through `2026-03-31`.
Daily-strategy coverage available locally: `2026-02-02` through `2026-03-24`.

- Best recent performer: `qqq_led_tqqq_sqqq_pair_opening_range_intraday_system`.
- Best recent operational candidate: `qqq_led_tqqq_sqqq_pair_opening_range_intraday_system`.
- Best recent trust anchor: `down_streak_exhaustion` by role, even though its last-two-month return was negative.
- Strategy that actually deserves to run tomorrow: `qqq_led_tqqq_sqqq_pair_opening_range_intraday_system` only.
- Strategies that should wait: `down_streak_exhaustion`, `relative_strength_vs_benchmark::rs_top3_native`, and `cross_sectional_momentum::csm_native`.
- Next step after tomorrow's paper run: compare the actual Monday paper log and report bundle against the approved opening-range baseline, then keep RS and CSM offline until they show cleaner recent evidence than they did here.

Source: tomorrow_alpaca_paper_runbook.md
# Tomorrow Alpaca Paper Runbook

Date: Monday 2026-04-06
Approved strategy set: `qqq_led_tqqq_sqqq_pair_opening_range_intraday_system` only.

## Strategy and symbols

- Strategy: `qqq_led_tqqq_sqqq_pair_opening_range_intraday_system`
- Leader symbol to watch: `QQQ`
- Trade symbols: `TQQQ` for bull signals, `SQQQ` for bear signals
- Exact research baseline settings: opening window `10`, threshold `15 bps`, decision interval `15m`, start delay `25m`, flat before close `40m`, notional `50%`, blocked hours `[]`, minimum relative volume `1.0`

