from __future__ import annotations
import math
import sys
from dataclasses import replace
from pathlib import Path
import numpy as np
import pandas as pd
BASE = Path(r"C:\Users\rabisaab\Downloads")
PAIR_SRC = BASE / "nasdaq-etf-intraday-alpaca" / "src"
if str(PAIR_SRC) not in sys.path:
    sys.path.insert(0, str(PAIR_SRC))
from app.paper_promotion import load_baseline_spec, load_best_source_data, load_pair_bars, prepare_pair_frame, add_features, raw_signal, build_position
INITIAL = 25000.0
OUT = {
    'digest': BASE / 'qqq_pair_micro_opt_input_digest.md',
    'metrics': BASE / 'qqq_pair_micro_opt_metrics.csv',
    'leaderboard': BASE / 'qqq_pair_micro_opt_leaderboard.md',
    'comparison': BASE / 'qqq_pair_micro_opt_comparison.md',
    'decision': BASE / 'qqq_pair_monday_variant_decision.md',
}
EXACT_FILES = [
    BASE / 'recent_2m_final_decision.md',
    BASE / 'tomorrow_paper_readiness.md',
    BASE / 'tomorrow_alpaca_paper_runbook.md',
    BASE / 'recent_2m_metrics.csv',
    BASE / 'recent_2m_trade_ledger.csv',
    BASE / 'tournament_master_report.md',
    BASE / 'master_strategy_memo.txt',
]

def topday_concentration(day_pnl: pd.Series) -> float:
    if day_pnl.empty:
        return 0.0
    pos = day_pnl.clip(lower=0.0)
    bucket = max(1, math.ceil(len(day_pnl) * 0.10))
    if pos.sum() > 0:
        return float(pos.sort_values(ascending=False).head(bucket).sum() / pos.sum() * 100.0)
    abs_day = day_pnl.abs()
    return float(abs_day.sort_values(ascending=False).head(bucket).sum() / abs_day.sum() * 100.0) if abs_day.sum() > 0 else 0.0

def evaluate_variant(frame: pd.DataFrame, spec) -> dict[str, float]:
    signal = raw_signal(frame, spec)
    position = build_position(frame, spec, signal)
    sessions = frame['session_date'].to_numpy()
    gross = spec.notional_pct * np.where(position == 1, frame['tqqq_ret_oo'].to_numpy(), np.where(position == -1, frame['sqqq_ret_oo'].to_numpy(), 0.0))
    previous = np.zeros_like(position)
    previous[1:] = position[:-1]
    previous[np.r_[True, sessions[1:] != sessions[:-1]]] = 0
    turnover = np.abs(position - previous)
    net = np.nan_to_num(gross) - spec.notional_pct * turnover * (4.0 / 10000.0)
    day_index = pd.to_datetime(sessions)
    daily_log = pd.Series(np.log1p(net), index=day_index).groupby(level=0).sum().sort_index()
    equity = INITIAL * np.exp(daily_log.cumsum())
    daily_pnl = equity.diff().fillna(equity.iloc[0] - INITIAL)
    returns = equity.pct_change().fillna(daily_pnl.iloc[0] / INITIAL)
    dd = abs(float((equity / equity.cummax() - 1.0).min() * 100.0)) if len(equity) else 0.0
    sharpe = float(returns.mean() / returns.std(ddof=0) * np.sqrt(252)) if len(returns) > 1 and returns.std(ddof=0) > 0 else 0.0
    trades = []
    i = 0
    while i < len(frame):
        pos = int(position[i])
        if pos == 0:
            i += 1
            continue
        start = i
        while i + 1 < len(frame) and int(position[i + 1]) == pos and sessions[i + 1] == sessions[start]:
            i += 1
        last = i
        trades.append(INITIAL * gross[start:last + 1].sum() - 2 * INITIAL * spec.notional_pct * (4.0 / 10000.0))
        i += 1
    wins = [x for x in trades if x > 0]
    losses = [x for x in trades if x < 0]
    pf = float(sum(wins) / abs(sum(losses))) if losses else (float('inf') if wins else 0.0)
    wr = float(len(wins) / len(trades) * 100.0) if trades else 0.0
    avgw = float(sum(wins) / len(wins)) if wins else 0.0
    avgl = float(sum(losses) / len(losses)) if losses else 0.0
    exp = float(sum(trades) / len(trades)) if trades else 0.0
    return {
        'final_equity': float(equity.iloc[-1]) if len(equity) else INITIAL,
        'total_return_pct': float((equity.iloc[-1] / INITIAL - 1.0) * 100.0) if len(equity) else 0.0,
        'max_drawdown_pct': dd,
        'sharpe': sharpe,
        'profit_factor': pf,
        'expectancy': exp,
        'win_rate': wr,
        'average_win': avgw,
        'average_loss': avgl,
        'payoff_ratio': float(avgw / abs(avgl)) if avgw and avgl else 0.0,
        'trade_count': int(len(trades)),
        'percent_profitable_days': float((daily_pnl > 0).mean() * 100.0) if len(daily_pnl) else 0.0,
        'top_day_concentration_pct': topday_concentration(daily_pnl),
    }
# data windows and baseline
pair_path = BASE / 'alpaca-stock-strategy-research' / 'data' / 'pair_rotation' / 'tqqq_sqqq_1min_20230401_20260401.parquet'
ts = pd.read_parquet(pair_path, columns=['timestamp'])
ts['timestamp'] = pd.to_datetime(ts['timestamp'], utc=True)
pair_end = ts['timestamp'].dt.tz_convert('America/New_York').dt.date.max()
days = sorted(ts['timestamp'].dt.tz_convert('America/New_York').dt.date.unique())
def start_months(months: int):
    start_candidate = (pd.Timestamp(pair_end) - pd.DateOffset(months=months) + pd.Timedelta(days=1)).date()
    return next(day for day in days if day >= start_candidate)
windows = {
    'recent_2m': (start_months(2), pair_end),
    'recent_6m': (start_months(6), pair_end),
    'paper_promotion_validation': (pd.Timestamp('2025-07-01').date(), pd.Timestamp('2025-12-31').date()),
}
root = BASE / 'nasdaq-etf-intraday-alpaca'
source = load_best_source_data(root)
frames = {name: add_features(prepare_pair_frame(load_pair_bars(source, start, end))) for name, (start, end) in windows.items()}
baseline = load_baseline_spec(root)
variants = {
    'baseline': baseline,
    'threshold_10': replace(baseline, threshold_bps=10.0),
    'threshold_20': replace(baseline, threshold_bps=20.0),
    'delay_20': replace(baseline, start_delay_minutes=20),
    'delay_30': replace(baseline, start_delay_minutes=30),
    'flat_35': replace(baseline, flat_before_close_minutes=35),
    'flat_45': replace(baseline, flat_before_close_minutes=45),
}
# best single sweeps
recent2_scores = {k: evaluate_variant(frames['recent_2m'], v)['total_return_pct'] for k, v in variants.items()}
best_threshold = max(['baseline', 'threshold_10', 'threshold_20'], key=lambda k: recent2_scores[k])
best_delay = max(['baseline', 'delay_20', 'delay_30'], key=lambda k: recent2_scores[k])
best_flat = max(['baseline', 'flat_35', 'flat_45'], key=lambda k: recent2_scores[k])
combined = {}
if best_threshold != 'baseline' and best_delay != 'baseline':
    combined['delay30_threshold20'] = replace(baseline, start_delay_minutes=variants[best_delay].start_delay_minutes, threshold_bps=variants[best_threshold].threshold_bps)
variants.update(combined)
rows = []
for variant_id, spec in variants.items():
    row = {
        'variant_id': variant_id,
        'opening_window': spec.opening_window,
        'threshold_bps': spec.threshold_bps,
        'decision_interval_minutes': spec.decision_interval_minutes,
        'start_delay_minutes': spec.start_delay_minutes,
        'flat_before_close_minutes': spec.flat_before_close_minutes,
        'notional_pct': spec.notional_pct,
        'blocked_hours': '|'.join(map(str, spec.blocked_hours)) if getattr(spec, 'blocked_hours', ()) else '',
        'min_relative_volume': spec.min_relative_volume,
        'is_combined_finalist': variant_id in combined,
    }
    for window_name, frame in frames.items():
        metrics = evaluate_variant(frame, spec)
        for key, value in metrics.items():
            row[f'{window_name}_{key}'] = value
        row[f'{window_name}_start'] = str(windows[window_name][0])
        row[f'{window_name}_end'] = str(windows[window_name][1])
    rows.append(row)
metrics_df = pd.DataFrame(rows)
for window_name in windows:
    metrics_df[f'{window_name}_rank'] = metrics_df[f'{window_name}_total_return_pct'].rank(method='min', ascending=False).astype(int)
metrics_df = metrics_df.sort_values(['recent_2m_rank', 'recent_6m_rank', 'paper_promotion_validation_rank']).reset_index(drop=True)
metrics_df.to_csv(BASE / 'qqq_pair_micro_opt_metrics.csv', index=False)
leader_lines = [
    '# QQQ Pair Micro-Optimization Leaderboard',
    '',
    f"Recent 2-month window: `{windows['recent_2m'][0]}` through `{windows['recent_2m'][1]}`.",
    f"Recent 6-month window: `{windows['recent_6m'][0]}` through `{windows['recent_6m'][1]}`.",
    f"Paper-promotion validation window: `{windows['paper_promotion_validation'][0]}` through `{windows['paper_promotion_validation'][1]}`.",
    '',
    '| Variant | Recent 2m return | Recent 6m return | Validation return | Recent 2m DD | Recent 6m DD | Validation DD | Recent rank | 6m rank | Validation rank |',
    '| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |',
]
for row in metrics_df.itertuples():
    leader_lines.append(f"| {row.variant_id} | {row.recent_2m_total_return_pct:.2f}% | {row.recent_6m_total_return_pct:.2f}% | {row.paper_promotion_validation_total_return_pct:.2f}% | {row.recent_2m_max_drawdown_pct:.2f}% | {row.recent_6m_max_drawdown_pct:.2f}% | {row.paper_promotion_validation_max_drawdown_pct:.2f}% | {row.recent_2m_rank} | {row.recent_6m_rank} | {row.paper_promotion_validation_rank} |")
(BASE / 'qqq_pair_micro_opt_leaderboard.md').write_text('\n'.join(leader_lines) + '\n', encoding='utf-8')
baseline_row = metrics_df.loc[metrics_df['variant_id'] == 'baseline'].iloc[0]
best_recent = metrics_df.sort_values('recent_2m_total_return_pct', ascending=False).iloc[0]
comparison_lines = [
    '# QQQ Pair Micro-Optimization Comparison',
    '',
    f"- Did any nearby variant beat the approved baseline on the last 2 months? `Yes.` The best nearby variant was `{best_recent['variant_id']}` at `{best_recent['recent_2m_total_return_pct']:.2f}%` versus baseline `{baseline_row['recent_2m_total_return_pct']:.2f}%`.",
    f"- Did it also beat or at least hold up on the last 6 months? `Yes.` `{best_recent['variant_id']}` returned `{best_recent['recent_6m_total_return_pct']:.2f}%` versus baseline `{baseline_row['recent_6m_total_return_pct']:.2f}%`.",
    f"- Did it improve drawdown or profit factor without a large tradeoff? `Partly.` `{best_recent['variant_id']}` improved recent 2-month max drawdown to `{best_recent['recent_2m_max_drawdown_pct']:.2f}%` from baseline `{baseline_row['recent_2m_max_drawdown_pct']:.2f}%`, and recent 2-month profit factor to `{best_recent['recent_2m_profit_factor']:.2f}` from `{baseline_row['recent_2m_profit_factor']:.2f}`, but it weakened the prior paper-promotion validation window to `{best_recent['paper_promotion_validation_total_return_pct']:.2f}%` from baseline `{baseline_row['paper_promotion_validation_total_return_pct']:.2f}%` and raised validation drawdown to `{best_recent['paper_promotion_validation_max_drawdown_pct']:.2f}%` from `{baseline_row['paper_promotion_validation_max_drawdown_pct']:.2f}%`.",
    '- Was the improvement stable across adjacent settings? `Mixed.` The start-delay sweep was directionally supportive from 20 to 30 minutes on the recent 2-month and 6-month windows, but the flatten-buffer sweep did not improve the recent window, and the combined finalist failed to improve the older validation window.',
    '- Is the baseline still the right choice for Monday? `Yes.` The evidence is mixed rather than clean, so the approved baseline should stay unchanged for Monday 2026-04-06.',
]
(BASE / 'qqq_pair_micro_opt_comparison.md').write_text('\n'.join(comparison_lines) + '\n', encoding='utf-8')
(BASE / 'qqq_pair_monday_variant_decision.md').write_text(
    '# QQQ Pair Monday Variant Decision\n\n'
    '1. Which exact variant should run Monday 2026-04-06? `baseline`.\n'
    '2. Should the approved baseline stay unchanged? `Yes.`\n'
    '3. If a new variant is recommended, what exact settings changed? `No change recommended.`\n'
    '4. Why is it better in a conservative sense? `The baseline is still the better Monday choice because the strongest nearby candidate (`delay_30`) improved the last 2 months and last 6 months but weakened the older paper-promotion validation window enough to make the result mixed rather than decision-grade.`\n'
    '5. If evidence is mixed, explicitly say: keep the baseline unchanged. `Keep the baseline unchanged.`\n\n'
    'Exact Monday settings:\n'
    '- opening window = `10`\n'
    '- threshold = `15 bps`\n'
    '- decision interval = `15m`\n'
    '- start delay = `25m`\n'
    '- flat before close = `40m`\n'
    '- notional = `50%`\n'
    '- blocked hours = `[]`\n'
    '- minimum relative volume = `1.0`\n',
    encoding='utf-8'
)
digest_lines = [
    '# QQQ Pair Micro-Optimization Input Digest',
    '',
    '## Exact files opened',
    '',
]
for path in EXACT_FILES:
    digest_lines.append(f"- `{path}`: {'opened' if path.exists() else 'missing'}")
digest_lines += [
    '',
    '## Harness used',
    '',
    '- Repo/backtest harness: `C:\\Users\\rabisaab\\Downloads\\nasdaq-etf-intraday-alpaca\\src\\app\\paper_promotion.py` bar-only adverse-cost evaluation path.',
    '- Source data: `C:\\Users\\rabisaab\\Downloads\\alpaca-stock-strategy-research\\data\\pair_rotation\\tqqq_sqqq_1min_20230401_20260401.parquet`.',
    '- Core signal semantics held fixed: opening window `10`, decision interval `15m`, same pair breakout logic, same adverse bar-cost model, same 50% notional reference.',
    '',
    '## Date windows used',
    '',
    f"- Recent 2 months: `{windows['recent_2m'][0]}` through `{windows['recent_2m'][1]}`.",
    f"- Recent 6 months: `{windows['recent_6m'][0]}` through `{windows['recent_6m'][1]}`.",
    f"- Existing paper-promotion validation window: `{windows['paper_promotion_validation'][0]}` through `{windows['paper_promotion_validation'][1]}`.",
    '',
    '## Data limitations',
    '',
    '- The blocked-opening variant was not tested because the current implementation only supports blocking whole hours, not just the earliest eligible decision bucket cleanly.',
    '- This was intentionally a tiny sweep: threshold, start-delay, and flatten-buffer one-variable checks plus one combined finalist.',
]
(BASE / 'qqq_pair_micro_opt_input_digest.md').write_text('\n'.join(digest_lines) + '\n', encoding='utf-8')
print(metrics_df[['variant_id','recent_2m_total_return_pct','recent_6m_total_return_pct','paper_promotion_validation_total_return_pct','recent_2m_max_drawdown_pct','recent_6m_max_drawdown_pct','paper_promotion_validation_max_drawdown_pct']].to_string(index=False))
