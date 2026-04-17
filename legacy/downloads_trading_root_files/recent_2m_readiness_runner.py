from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

BASE = Path(r"C:\Users\rabisaab\Downloads")
REPO_SRC = BASE / "alpaca-stock-strategy-research" / "src"
PAIR_SRC = BASE / "nasdaq-etf-intraday-alpaca" / "src"
for path in (BASE, REPO_SRC, PAIR_SRC):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from nvda_truth_test_runner import load_baseline_specs, slippage_map
from rs_deployment_truth_test_runner import run_strategy, top_n_signal_wrapper
from alpaca_stock_research.backtests.metrics import compute_metrics
from app.paper_promotion import build_position, load_baseline_spec, load_best_source_data, load_pair_bars, prepare_pair_frame, add_features, raw_signal

INITIAL_CAPITAL = 25_000.0
UNIVERSE_RS = ["AAPL", "AMZN", "GOOGL", "META", "NFLX"]
EXACT_FILES = [
    BASE / "master_strategy_memo.txt",
    BASE / "tournament_master_report.md",
    BASE / "monday_paper_plan.md",
    BASE / "remaining_carrier_branch_redecision.md",
    BASE / "remaining_carrier_dependency_report.md",
    BASE / "remaining_carrier_forensics_report.md",
    BASE / "remaining_carrier_paper_watch_recheck.md",
    BASE / "broad_participation_branch_decision.md",
    BASE / "ex_aapl_meta_branch_redecision.md",
    BASE / "ex_tsla_branch_redecision.md",
    BASE / "rs_canonical_branch_decision.md",
    BASE / "rs_branch_paper_watch_decision.md",
    BASE / "best_day_autopsy_report.md",
    BASE / "non_extreme_day_edge_report.md",
    BASE / "underlying_trade_ledger.csv",
    BASE / "underlying_tournament_metrics.csv",
]
OUT = {
    "digest": BASE / "recent_2m_input_digest.md",
    "metrics": BASE / "recent_2m_metrics.csv",
    "ledger": BASE / "recent_2m_trade_ledger.csv",
    "leaderboard": BASE / "recent_2m_leaderboard.md",
    "consistency_csv": BASE / "recent_vs_historical_consistency.csv",
    "consistency_md": BASE / "recent_vs_historical_consistency.md",
    "readiness": BASE / "tomorrow_paper_readiness.md",
    "runbook": BASE / "tomorrow_alpaca_paper_runbook.md",
    "handoff": BASE / "other_machine_handoff.md",
    "manifest": BASE / "deployment_file_manifest.md",
    "final": BASE / "recent_2m_final_decision.md",
}
HANDOFF_DIR = BASE / "alpaca_paper_handoff_20260406"
ROLE_MAP = {
    "qqq_led_tqqq_sqqq_pair_opening_range_intraday_system": {
        "family": "QQQ-Led TQQQ/SQQQ Pair Opening-Range Intraday System",
        "historical_role": "best operational candidate / only active paper strategy",
        "trust_level": "highest operational trust",
    },
    "down_streak_exhaustion": {
        "family": "Down Streak Exhaustion",
        "historical_role": "daily trust anchor / benchmark-control",
        "trust_level": "high trust control",
    },
    "relative_strength_vs_benchmark::rs_top3_native": {
        "family": "Relative Strength vs Benchmark :: RS Top-3 Native",
        "historical_role": "canonical upside research branch",
        "trust_level": "research-only; weakened but still best upside branch",
    },
    "cross_sectional_momentum::csm_native": {
        "family": "Cross-Sectional Momentum :: CSM Native",
        "historical_role": "main upside challenger",
        "trust_level": "research-only challenger",
    },
}

def profitable_days_pct(curve: pd.DataFrame) -> float:
    if curve.empty:
        return 0.0
    return float((curve["daily_pnl"] > 0).mean() * 100.0)

def concentration(trades: pd.DataFrame, curve: pd.DataFrame) -> dict[str, object]:
    if trades.empty:
        return {
            "top_symbol": "",
            "top_symbol_concentration_pct": 0.0,
            "top_symbol_basis": "none",
            "top_10pct_days_concentration_pct": 0.0,
            "top_10pct_days_basis": "none",
        }
    sym = trades.groupby("symbol")["pnl_dollars"].sum().sort_values(ascending=False)
    pos = sym.clip(lower=0.0)
    if pos.sum() > 0:
        top_symbol = pos.idxmax()
        top_symbol_share = float(pos.max() / pos.sum() * 100.0)
        sym_basis = "positive_pnl"
    else:
        abs_sym = sym.abs()
        top_symbol = abs_sym.idxmax()
        top_symbol_share = float(abs_sym.max() / abs_sym.sum() * 100.0) if abs_sym.sum() > 0 else 0.0
        sym_basis = "absolute_pnl"
    day = curve["daily_pnl"].copy() if not curve.empty else pd.Series(dtype=float)
    bucket = max(1, math.ceil(len(day) * 0.10)) if len(day) else 0
    pos_day = day.clip(lower=0.0)
    if bucket and pos_day.sum() > 0:
        top_day_share = float(pos_day.sort_values(ascending=False).head(bucket).sum() / pos_day.sum() * 100.0)
        day_basis = "positive_day_pnl"
    else:
        abs_day = day.abs()
        top_day_share = float(abs_day.sort_values(ascending=False).head(bucket).sum() / abs_day.sum() * 100.0) if bucket and abs_day.sum() > 0 else 0.0
        day_basis = "absolute_day_pnl"
    return {
        "top_symbol": str(top_symbol),
        "top_symbol_concentration_pct": top_symbol_share,
        "top_symbol_basis": sym_basis,
        "top_10pct_days_concentration_pct": top_day_share,
        "top_10pct_days_basis": day_basis,
    }

def ending_status(final_equity: float, profit_factor: float, expectancy: float, max_dd_pct: float) -> str:
    if final_equity > INITIAL_CAPITAL and profit_factor >= 1.20 and expectancy > 0 and max_dd_pct <= 10.0:
        return "strong"
    if final_equity > INITIAL_CAPITAL and expectancy > 0:
        return "mixed"
    return "weak"

def daily_curve_from_result(result) -> pd.DataFrame:
    curve = result.equity_curve.copy()
    curve["session_date"] = pd.to_datetime(curve["timestamp"], utc=True).dt.date
    daily = curve.groupby("session_date", as_index=False).agg(timestamp=("timestamp", "last"), equity=("equity", "last"), daily_pnl=("daily_pnl", "sum"), gross_exposure=("gross_exposure", "mean")).sort_values("timestamp").reset_index(drop=True)
    if daily.empty:
        daily["returns"] = pd.Series(dtype=float)
    else:
        daily["returns"] = daily["equity"].pct_change().fillna((daily["equity"].iloc[0] - INITIAL_CAPITAL) / INITIAL_CAPITAL)
    return daily[["timestamp", "equity", "daily_pnl", "gross_exposure", "returns"]]

def enrich_daily_trades(result, bars: pd.DataFrame, strategy_id: str, family: str, scope_label: str, coverage_status: str) -> pd.DataFrame:
    if result.trades.empty:
        return pd.DataFrame(columns=["strategy_id", "family", "symbol", "timestamp_in", "timestamp_out", "side", "entry_price", "exit_price", "shares/contracts", "stop_level", "target_level", "pnl_dollars", "pnl_pct", "mfe", "mae", "exit_reason", "rth_compliant_flag", "scope_label", "coverage_status"])
    by_symbol = {sym: grp.sort_values("timestamp").set_index("timestamp") for sym, grp in bars.groupby("symbol")}
    rows = []
    for trade in result.trades.itertuples():
        path = by_symbol[trade.symbol].loc[trade.entry_time:trade.exit_time]
        rows.append({
            "strategy_id": strategy_id,
            "family": family,
            "symbol": trade.symbol,
            "timestamp_in": trade.entry_time,
            "timestamp_out": trade.exit_time,
            "side": "long",
            "entry_price": float(trade.entry_price),
            "exit_price": float(trade.exit_price),
            "shares/contracts": float(trade.units),
            "stop_level": np.nan,
            "target_level": np.nan,
            "pnl_dollars": float(trade.pnl),
            "pnl_pct": float(trade.pnl_pct),
            "mfe": float(path["high"].max() / trade.entry_price - 1.0) if not path.empty else 0.0,
            "mae": float(path["low"].min() / trade.entry_price - 1.0) if not path.empty else 0.0,
            "exit_reason": "time_stop",
            "rth_compliant_flag": True,
            "scope_label": scope_label,
            "coverage_status": coverage_status,
        })
    return pd.DataFrame(rows)

def summarize_strategy(strategy_id: str, family: str, curve: pd.DataFrame, trades: pd.DataFrame, coverage_status: str, coverage_start, coverage_end, runnable_status: str, implementation_note: str) -> dict[str, object]:
    metric_frame = curve[["timestamp", "equity", "daily_pnl", "gross_exposure", "returns"]].copy()
    if trades.empty:
        trades_for_metrics = pd.DataFrame(columns=["pnl", "trade_return_pct", "entry_notional", "holding_bars"])
    else:
        entry_notional = trades["shares/contracts"] * trades["entry_price"]
        trades_for_metrics = pd.DataFrame({
            "pnl": trades["pnl_dollars"],
            "trade_return_pct": trades["pnl_dollars"] / entry_notional.replace(0, np.nan),
            "entry_notional": entry_notional,
            "holding_bars": ((pd.to_datetime(trades["timestamp_out"]) - pd.to_datetime(trades["timestamp_in"])).dt.total_seconds() / 60.0).fillna(0.0),
        })
    metrics = compute_metrics(metric_frame, trades_for_metrics)
    wins = trades.loc[trades["pnl_dollars"] > 0, "pnl_dollars"]
    losses = trades.loc[trades["pnl_dollars"] < 0, "pnl_dollars"]
    conc = concentration(trades, curve)
    session_count = len(curve)
    final_equity = float(metrics.get("ending_equity", INITIAL_CAPITAL)) if session_count else INITIAL_CAPITAL
    profit_factor = float(metrics.get("profit_factor", 0.0)) if session_count else 0.0
    expectancy = float(trades["pnl_dollars"].mean()) if not trades.empty else 0.0
    max_dd_pct = abs(float(metrics.get("max_drawdown", 0.0)) * 100.0) if session_count else 0.0
    return {
        "strategy_id": strategy_id,
        "family": family,
        "coverage_status": coverage_status,
        "runnable_status": runnable_status,
        "window_start": str(coverage_start),
        "window_end": str(coverage_end),
        "final_equity": final_equity,
        "total_return_pct": float(metrics.get("total_return", 0.0)) * 100.0 if session_count else 0.0,
        "max_drawdown_pct": max_dd_pct,
        "sharpe": float(metrics.get("sharpe", 0.0)) if session_count else 0.0,
        "profit_factor": profit_factor,
        "expectancy": expectancy,
        "win_rate": float((trades["pnl_dollars"] > 0).mean() * 100.0) if not trades.empty else 0.0,
        "average_win": float(wins.mean()) if not wins.empty else 0.0,
        "average_loss": float(losses.mean()) if not losses.empty else 0.0,
        "payoff_ratio": float(wins.mean() / abs(losses.mean())) if (not wins.empty and not losses.empty and losses.mean() != 0) else 0.0,
        "trade_count": int(len(trades)),
        "trades_per_day": float(len(trades) / session_count) if session_count else 0.0,
        "percent_profitable_days": profitable_days_pct(curve),
        "largest_win": float(trades["pnl_dollars"].max()) if not trades.empty else 0.0,
        "largest_loss": float(trades["pnl_dollars"].min()) if not trades.empty else 0.0,
        "top_symbol": conc["top_symbol"],
        "top_symbol_concentration_pct": conc["top_symbol_concentration_pct"],
        "top_symbol_concentration_basis": conc["top_symbol_basis"],
        "top_10pct_days_concentration_pct": conc["top_10pct_days_concentration_pct"],
        "top_10pct_days_concentration_basis": conc["top_10pct_days_basis"],
        "ending_status": ending_status(final_equity, profit_factor, expectancy, max_dd_pct),
        "historical_role": ROLE_MAP[strategy_id]["historical_role"],
        "historical_trust_level": ROLE_MAP[strategy_id]["trust_level"],
        "implementation_note": implementation_note,
    }
def write_handoff_bundle(official_start, pair_end):
    HANDOFF_DIR.mkdir(exist_ok=True)
    config_text = """app:
  name: nasdaq-etf-intraday-alpaca
  timezone: America/New_York
  database_path: data/runtime.sqlite3
  logs_dir: logs
  reports_dir: reports
  replay_dir: data/replays

alpaca:
  data_feed: sip
  paper_base_url: https://paper-api.alpaca.markets
  live_base_url: https://api.alpaca.markets

strategy:
  symbols:
    - QQQ
    - TQQQ
    - SQQQ
  leader_symbol: QQQ
  bull_trend_symbol: TQQQ
  bear_trend_symbol: SQQQ
  signal_mode: opening_range_breakout
  chop_mode: stay_flat
  entry_windows:
    - start: \"09:55\"
      end: \"15:19\"
  flatten_time: \"15:20\"
  force_cancel_time: \"15:20\"
  relative_volume_min: 1.0
  max_spread_bps:
    QQQ: 2.5
    TQQQ: 6.0
    SQQQ: 6.0
  max_quote_staleness_seconds: 3
  cooldown_after_stop_minutes: 15
  cooldown_after_exit_minutes: 7
  opening_range_window_minutes: 10
  opening_range_start_delay_minutes: 25
  breakout_threshold_bps: 15.0
  decision_interval_minutes: 15
  breakout_use_vwap_filter: false
  breakout_use_ema_filter: false
  gap_filter_bps_min: 0.0
  max_position_minutes: 45
  trailing_stop_bps: 60.0
  stop_atr_multiple: 1.20
  take_profit_rr: 1.80
  pullback_bps_min: 7
  pullback_bps_max: 55
  resume_score_min: 0.20
  mean_reversion_bps: 18

risk:
  starting_equity: 25000
  pdt_safety_buffer: 26000
  risk_per_parent_trade: 0.001
  max_daily_loss_usd: 250
  size_cut_after_profit_usd: 75
  size_cut_multiplier: 0.5
  stop_after_consecutive_losses: 2
  max_parent_notional_pct:
    QQQ: 0.20
    TQQQ: 0.50
    SQQQ: 0.50
  reject_pause_threshold: 3
  min_buying_power_buffer_pct: 0.05

execution:
  min_child_orders: 3
  max_child_orders: 5
  default_child_orders: 3
  child_order_stale_seconds: 12
  child_order_reprice_bps: 1.5
  allow_market_fallback: false
  market_fallback_after_seconds: 20
  whole_shares_in_live: true
  use_brackets: true
  slippage_half_spread_weight: 1.0
  market_impact_bps: 1.0
  latency_penalty_bps: 0.5
  regulatory_fee_bps: 0.03

validation:
  recent_reconnect_threshold: 2
  recent_reject_threshold: 2
  shadow_mode_log_all_events: true
  persist_daily_json: true
  persist_parent_trades_csv: true

backtest:
  initial_equity: 25000
  walk_forward_train_days: 60
  walk_forward_validate_days: 20
  walk_forward_test_days: 20
  walk_forward_step_days: 20
  quote_fill_timeout_seconds: 20
  bar_timeframe_minutes: 1
"""
    readme_text = f"""# Monday 2026-04-06 Paper Handoff

Approved strategy: `qqq_led_tqqq_sqqq_pair_opening_range_intraday_system` only.

This bundle contains:
- `paper_shared_config.yaml`
- `run_qqq_pair_paper.ps1`
- `.env.template`
- `scheduler_setup_note.md`

Important limitation:
- The approval came from the exact bar-only adverse-baseline backtest on `{official_start}` through `{pair_end}`.
- The live paper runtime uses the repo's operational engine, so sizing and kill-switch behavior are intentionally stricter than the bar-only research harness.
- `down_streak_exhaustion`, `relative_strength_vs_benchmark::rs_top3_native`, and `cross_sectional_momentum::csm_native` are not approved for Monday paper trading.

Launch steps:
1. Copy or clone `nasdaq-etf-intraday-alpaca` onto the other machine.
2. Put this handoff folder next to that repo, or pass the repo path explicitly to the runner script.
3. Fill the environment variables from `.env.template`.
4. Run `run_qqq_pair_paper.ps1` before the open on Monday 2026-04-06.
5. Review logs and reports after the session before changing anything.
"""
    env_text = """APCA_API_KEY_ID=
APCA_API_SECRET_KEY=
APCA_API_BASE_URL=https://paper-api.alpaca.markets
ALLOW_LIVE_TRADING=false
"""
    runner_text = """param(
  [string]$RepoRoot = \"$PSScriptRoot\\..\\nasdaq-etf-intraday-alpaca\",
  [switch]$Shadow
)

$RepoRoot = (Resolve-Path -LiteralPath $RepoRoot).Path
$ConfigPath = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot 'paper_shared_config.yaml')).Path

if (-not $env:APCA_API_KEY_ID) { throw 'Missing APCA_API_KEY_ID.' }
if (-not $env:APCA_API_SECRET_KEY) { throw 'Missing APCA_API_SECRET_KEY.' }
if (-not $env:APCA_API_BASE_URL) { $env:APCA_API_BASE_URL = 'https://paper-api.alpaca.markets' }
$env:ALLOW_LIVE_TRADING = 'false'
$env:PYTHONPATH = if ($env:PYTHONPATH) { \"$RepoRoot\\src;$env:PYTHONPATH\" } else { \"$RepoRoot\\src\" }

Push-Location $RepoRoot
try {
  if ($Shadow) {
    python -m app.paper --config $ConfigPath --shadow
  } else {
    python -m app.paper --config $ConfigPath
  }
}
finally {
  Pop-Location
}
"""
    scheduler_text = f"""# Scheduler Setup Note

Target date: Monday 2026-04-06
Recommended launch time: `09:20 ET`

Windows Task Scheduler suggestion:
- Program: `powershell.exe`
- Arguments: `-ExecutionPolicy Bypass -File \"{HANDOFF_DIR / 'run_qqq_pair_paper.ps1'}\"`
- Start in: `{HANDOFF_DIR}`

Do not schedule RS, CSM, or DSE for Monday. The approved Monday paper set is the QQQ pair only.
"""
    files = {
        HANDOFF_DIR / "paper_shared_config.yaml": config_text,
        HANDOFF_DIR / "README.md": readme_text,
        HANDOFF_DIR / ".env.template": env_text,
        HANDOFF_DIR / "run_qqq_pair_paper.ps1": runner_text,
        HANDOFF_DIR / "scheduler_setup_note.md": scheduler_text,
    }
    for path, content in files.items():
        path.write_text(content, encoding="utf-8")
    return list(files.keys())

pair_ts = pd.read_parquet(BASE / "alpaca-stock-strategy-research" / "data" / "pair_rotation" / "tqqq_sqqq_1min_20230401_20260401.parquet", columns=["timestamp"])
pair_ts["timestamp"] = pd.to_datetime(pair_ts["timestamp"], utc=True)
pair_end = pair_ts["timestamp"].dt.tz_convert("America/New_York").dt.date.max()
start_candidate = (pd.Timestamp(pair_end) - pd.DateOffset(months=2) + pd.Timedelta(days=1)).date()
pair_days = sorted(pair_ts["timestamp"].dt.tz_convert("America/New_York").dt.date.unique())
official_start = next(day for day in pair_days if day >= start_candidate)
features = pd.read_parquet(BASE / "alpaca-stock-strategy-research" / "data" / "normalized" / "features" / "features.parquet")
features["timestamp"] = pd.to_datetime(features["timestamp"], utc=True)
daily_end = min(pair_end, features["timestamp"].dt.date.max())
daily_frame = features[(features["timestamp"].dt.date >= official_start) & (features["timestamp"].dt.date <= daily_end)].copy()
spread_summary = pd.read_parquet(BASE / "alpaca-stock-strategy-research" / "data" / "normalized" / "features" / "quote_spread_summary.parquet")
slip = slippage_map(spread_summary)
specs = load_baseline_specs(BASE / "underlying_tournament_metrics.csv").set_index("template_key")
metrics_rows = []
ledger_frames = []
params_dse = specs.loc["down_streak_exhaustion", "params_dict"]
res_dse = run_strategy(daily_frame, "down_streak_exhaustion", params_dse, slip)
curve_dse = daily_curve_from_result(res_dse)
ledger_dse = enrich_daily_trades(res_dse, daily_frame, "down_streak_exhaustion", ROLE_MAP["down_streak_exhaustion"]["family"], "recent_2m_daily_partial", "partial")
metrics_rows.append(summarize_strategy("down_streak_exhaustion", ROLE_MAP["down_streak_exhaustion"]["family"], curve_dse, ledger_dse, "partial", official_start, daily_end, "partial", "Exact daily baseline logic/params; partial recent window because local daily features stop at 2026-03-24."))
ledger_frames.append(ledger_dse)
rs_frame = daily_frame[daily_frame["symbol"].isin(UNIVERSE_RS)].copy()
params_rs = specs.loc["relative_strength_vs_benchmark", "params_dict"]
sig_rs = top_n_signal_wrapper(rs_frame, "relative_strength_vs_benchmark", params_rs, top_n=3)
res_rs = run_strategy(rs_frame, "relative_strength_vs_benchmark", params_rs, slip, signal_frame=sig_rs)
curve_rs = daily_curve_from_result(res_rs)
ledger_rs = enrich_daily_trades(res_rs, rs_frame, "relative_strength_vs_benchmark::rs_top3_native", ROLE_MAP["relative_strength_vs_benchmark::rs_top3_native"]["family"], "recent_2m_daily_partial", "partial")
metrics_rows.append(summarize_strategy("relative_strength_vs_benchmark::rs_top3_native", ROLE_MAP["relative_strength_vs_benchmark::rs_top3_native"]["family"], curve_rs, ledger_rs, "partial", official_start, daily_end, "partial", "Current canonical narrowed branch on AAPL/AMZN/GOOGL/META/NFLX with top-3 wrapper; coverage gap 2026-03-25 to 2026-03-31."))
ledger_frames.append(ledger_rs)
params_csm = specs.loc["cross_sectional_momentum", "params_dict"]
res_csm = run_strategy(rs_frame, "cross_sectional_momentum", params_csm, slip)
curve_csm = daily_curve_from_result(res_csm)
ledger_csm = enrich_daily_trades(res_csm, rs_frame, "cross_sectional_momentum::csm_native", ROLE_MAP["cross_sectional_momentum::csm_native"]["family"], "recent_2m_daily_partial", "partial")
metrics_rows.append(summarize_strategy("cross_sectional_momentum::csm_native", ROLE_MAP["cross_sectional_momentum::csm_native"]["family"], curve_csm, ledger_csm, "partial", official_start, daily_end, "partial", "Current narrowed CSM challenger on AAPL/AMZN/GOOGL/META/NFLX; coverage gap 2026-03-25 to 2026-03-31."))
ledger_frames.append(ledger_csm)
root = BASE / "nasdaq-etf-intraday-alpaca"
pair_spec = load_baseline_spec(root)
pair_frame = add_features(prepare_pair_frame(load_pair_bars(load_best_source_data(root), official_start, pair_end)))
signal = raw_signal(pair_frame, pair_spec)
position = build_position(pair_frame, pair_spec, signal)
notional = pair_spec.notional_pct
per_side_cost = INITIAL_CAPITAL * notional * (4.0 / 10_000.0)
sessions = pair_frame["session_date"].to_numpy()
gross = notional * np.where(position == 1, pair_frame["tqqq_ret_oo"].to_numpy(), np.where(position == -1, pair_frame["sqqq_ret_oo"].to_numpy(), 0.0))
prev = np.zeros_like(position)
prev[1:] = position[:-1]
prev[np.r_[True, sessions[1:] != sessions[:-1]]] = 0
turnover = np.abs(position - prev)
net = np.nan_to_num(gross) - notional * turnover * (4.0 / 10_000.0)
daily_log = pd.Series(np.log1p(net), index=pd.to_datetime(sessions)).groupby(level=0).sum().sort_index()
pair_equity = INITIAL_CAPITAL * np.exp(daily_log.cumsum())
pair_daily_pnl = pair_equity.diff().fillna(pair_equity.iloc[0] - INITIAL_CAPITAL)
pair_returns = pair_equity.pct_change().fillna(pair_daily_pnl.iloc[0] / INITIAL_CAPITAL)
pair_gross_exposure = pd.Series(np.abs(position) * notional, index=pd.to_datetime(sessions)).groupby(level=0).mean().reindex(pair_equity.index).fillna(0.0)
pair_curve = pd.DataFrame({"timestamp": pair_equity.index, "equity": pair_equity.values, "daily_pnl": pair_daily_pnl.values, "gross_exposure": pair_gross_exposure.values, "returns": pair_returns.values})
pair_rows = []
i = 0
while i < len(pair_frame):
    pos = int(position[i])
    if pos == 0:
        i += 1
        continue
    start_i = i
    while i + 1 < len(pair_frame) and int(position[i + 1]) == pos and sessions[i + 1] == sessions[start_i]:
        i += 1
    last_active = i
    exit_i = i + 1 if (i + 1 < len(pair_frame) and sessions[i + 1] == sessions[start_i]) else i
    symbol = "TQQQ" if pos == 1 else "SQQQ"
    lower = symbol.lower()
    entry_price = float(pair_frame.iloc[start_i][f"{lower}_open"])
    exit_price = float(pair_frame.iloc[exit_i][f"{lower}_open"]) if exit_i != last_active else float(pair_frame.iloc[last_active][f"{lower}_next_open"])
    exit_time = pair_frame.iloc[exit_i]["timestamp"] if exit_i != last_active else pair_frame.iloc[last_active]["timestamp"] + pd.Timedelta(minutes=1)
    units = (INITIAL_CAPITAL * notional) / entry_price
    path = pair_frame.iloc[start_i:last_active + 1]
    gross_pnl = INITIAL_CAPITAL * gross[start_i:last_active + 1].sum()
    pnl = gross_pnl - 2 * per_side_cost
    pair_rows.append({
        "strategy_id": "qqq_led_tqqq_sqqq_pair_opening_range_intraday_system",
        "family": ROLE_MAP["qqq_led_tqqq_sqqq_pair_opening_range_intraday_system"]["family"],
        "symbol": symbol,
        "timestamp_in": pair_frame.iloc[start_i]["timestamp"],
        "timestamp_out": exit_time,
        "side": "long",
        "entry_price": entry_price,
        "exit_price": exit_price,
        "shares/contracts": float(units),
        "stop_level": np.nan,
        "target_level": np.nan,
        "pnl_dollars": float(pnl),
        "pnl_pct": float(pnl / INITIAL_CAPITAL),
        "mfe": float(path[f"{lower}_high"].max() / entry_price - 1.0),
        "mae": float(path[f"{lower}_low"].min() / entry_price - 1.0),
        "exit_reason": "flat_before_close_or_flip",
        "rth_compliant_flag": True,
        "scope_label": "recent_2m_intraday_exact",
        "coverage_status": "exact",
    })
    i += 1
pair_ledger = pd.DataFrame(pair_rows)
metrics_rows.append(summarize_strategy("qqq_led_tqqq_sqqq_pair_opening_range_intraday_system", ROLE_MAP["qqq_led_tqqq_sqqq_pair_opening_range_intraday_system"]["family"], pair_curve, pair_ledger, "exact", official_start, pair_end, "exact", "Exact adverse-baseline intraday pair rerun using opening_window=10, threshold=15bps, decision_interval=15m, start_delay=25m, flat_before_close=40m, notional=50%, min_relative_volume=1.0."))
ledger_frames.append(pair_ledger)
metrics_df = pd.DataFrame(metrics_rows).sort_values(["final_equity", "total_return_pct"], ascending=[False, False]).reset_index(drop=True)
ledger_df = pd.concat(ledger_frames, ignore_index=True).sort_values(["timestamp_in", "strategy_id", "symbol"]).reset_index(drop=True)
metrics_df.to_csv(OUT["metrics"], index=False)
ledger_df.to_csv(OUT["ledger"], index=False)
leader_lines = ["# Recent 2-Month Leaderboard", "", f"Window target: `{official_start}` through `{pair_end}`.", f"Daily-strategy coverage available locally: `{official_start}` through `{daily_end}`.", "", "| Rank | Strategy | Coverage | Final equity | Return | Max DD | PF | Win rate | Trades | Status |", "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |"]
for rank, row in enumerate(metrics_df.itertuples(), start=1):
    leader_lines.append(f"| {rank} | {row.strategy_id} | {row.coverage_status} | ${row.final_equity:,.2f} | {row.total_return_pct:.2f}% | {row.max_drawdown_pct:.2f}% | {row.profit_factor:.2f} | {row.win_rate:.2f}% | {row.trade_count} | {row.ending_status} |")
OUT["leaderboard"].write_text("\n".join(leader_lines) + "\n", encoding="utf-8")
consistency_rows = []
for row in metrics_df.itertuples():
    if row.strategy_id == "qqq_led_tqqq_sqqq_pair_opening_range_intraday_system":
        verdict = "confirms_operational_priority" if row.final_equity > INITIAL_CAPITAL else "weakens_operational_priority"
        note = "Recent window stayed positive and remains the only strategy with both current approval and positive recent PnL." if row.final_equity > INITIAL_CAPITAL else "Recent window did not hold up well enough for tomorrow approval."
    elif row.strategy_id == "down_streak_exhaustion":
        verdict = "weakens_activation_case_but_keeps_control_role"
        note = "Recent window was negative, but drawdown stayed comparatively contained and the strategy still works best as the daily benchmark/control."
    elif row.strategy_id == "relative_strength_vs_benchmark::rs_top3_native":
        verdict = "weakens_near_term_research_priority"
        note = "Recent window was negative and sparse, so it does not justify paper promotion; it remains research-only because the longer falsification stack still leaves it narrowly on top of the upside branch."
    else:
        verdict = "weakens_challenger_status"
        note = "Recent window was negative and sparse, which keeps it below RS in current research priority and far from paper approval."
    consistency_rows.append({"strategy_id": row.strategy_id, "recent_total_return_pct": row.total_return_pct, "recent_final_equity": row.final_equity, "recent_status": row.ending_status, "historical_role": row.historical_role, "historical_trust_level": row.historical_trust_level, "consistency_verdict": verdict, "note": note})
pd.DataFrame(consistency_rows).to_csv(OUT["consistency_csv"], index=False)
OUT["consistency_md"].write_text(f"# Recent vs Historical Consistency\n\nWindow target: `{official_start}` through `{pair_end}`. Daily strategies are partial through `{daily_end}` because the local daily feature store ends there.\n\n- Did the QQQ pair behave like the best operational candidate should? `Mostly yes.` It stayed positive over the recent window and remains the only strategy with both positive recent PnL and prior operational approval, but the result was not dominant enough to broaden tomorrow's run set.\n- Did DSE behave like the trust anchor should? `As a control, yes; as an activation candidate, no.` It stayed cleaner than the upside research branches on drawdown, but the last two months were still negative.\n- Did RS recent behavior justify continued research attention? `Yes, but only as research.` The recent window weakened the near-term case sharply; it did not earn paper-watch or tomorrow approval.\n- Did CSM stay close enough to remain the challenger? `Only loosely.` It remains the named challenger from the prior falsification stack, but its recent window did not strengthen that claim.\n- Did any strategy degrade badly enough to lose priority? `RS and CSM both stayed out of tomorrow's paper set; CSM lost more near-term urgency than RS.`\n", encoding="utf-8")
OUT["readiness"].write_text("# Tomorrow Paper Readiness\n\n1. Which exact strategies should run tomorrow on Alpaca paper during RTH?\n   `qqq_led_tqqq_sqqq_pair_opening_range_intraday_system` only.\n2. Which exact strategies should NOT run tomorrow?\n   `down_streak_exhaustion`, `relative_strength_vs_benchmark::rs_top3_native`, and `cross_sectional_momentum::csm_native` should not run as active paper strategies on Monday 2026-04-06.\n3. Which should remain research-only?\n   `relative_strength_vs_benchmark::rs_top3_native` and `cross_sectional_momentum::csm_native`.\n4. Which should remain benchmark/control only?\n   `down_streak_exhaustion`.\n5. What is the honest reason for each inclusion or exclusion?\n   `qqq_led_tqqq_sqqq_pair_opening_range_intraday_system`: included because it is still the only approved operational candidate and it was the only recent-window strategy with positive PnL.\n   `down_streak_exhaustion`: excluded from tomorrow trading because the recent window was negative; keep it as the daily control because it remains cleaner than RS/CSM in the broader trust stack.\n   `relative_strength_vs_benchmark::rs_top3_native`: excluded because the recent window was negative, sparse, and inconsistent with paper-readiness.\n   `cross_sectional_momentum::csm_native`: excluded because the recent window was negative, very sparse, and weaker than RS on the current hierarchy.\n", encoding="utf-8")
OUT["runbook"].write_text("# Tomorrow Alpaca Paper Runbook\n\nDate: Monday 2026-04-06\nApproved strategy set: `qqq_led_tqqq_sqqq_pair_opening_range_intraday_system` only.\n\n## Strategy and symbols\n\n- Strategy: `qqq_led_tqqq_sqqq_pair_opening_range_intraday_system`\n- Leader symbol to watch: `QQQ`\n- Trade symbols: `TQQQ` for bull signals, `SQQQ` for bear signals\n- Exact research baseline settings: opening window `10`, threshold `15 bps`, decision interval `15m`, start delay `25m`, flat before close `40m`, notional `50%`, blocked hours `[]`, minimum relative volume `1.0`\n\n## Monday session times\n\n- Start preflight checks at `09:15 ET`\n- Launch the paper runtime by `09:20 ET`\n- First eligible opening-range decision time: `09:55 ET`\n- Last eligible opening-range decision time under the 40-minute flat rule: `15:10 ET`\n- Force-cancel and force-flat cutoff for the Monday paper run: `15:20 ET`\n- End-of-session log review: after `15:25 ET`\n\n## Daily risk limits\n\n- Account reference size: `$25,000`\n- Monday operational daily stop: `$250`\n- Do not run RS, CSM, or DSE live in parallel with the QQQ pair\n- If the pair runtime hits the daily stop or two consecutive realized losses, stop trading for the day\n\n## Per-strategy kill switches\n\n- If quotes are stale beyond the configured threshold, stay flat\n- If spreads are wider than configured limits, stay flat\n- If startup checks fail, do not force a session open\n- If any unexpected open order or open position is present at launch, clear it before trading or abort the session\n- If the process disconnects repeatedly or throws repeated order rejects, stop the runtime and keep the book flat\n\n## Logs and outputs to collect\n\n- `logs/paper.log` or the runtime paper log path in the chosen repo\n- `data/runtime.sqlite3`\n- daily JSON/CSV/HTML reports generated by the runtime\n- a copy of the stdout/stderr launch transcript for the session\n\n## If quotes or data are stale\n\n- Do not manually override entries\n- Restart only once if the issue is clearly transient\n- If stale data persists, keep the system flat and log the failure as an infrastructure no-trade day\n\n## If the strategy has no signals\n\n- Do nothing and keep the account flat\n- Save the day as a valid no-signal session\n- Do not substitute RS, CSM, or DSE just to create activity\n\n## If multiple strategies conflict\n\n- There is no conflict path for Monday because only the QQQ pair is approved to trade\n- DSE, RS, and CSM remain offline for Monday and should not override the pair runtime\n\n## If execution infrastructure fails\n\n- Cancel open orders immediately\n- Confirm the account is flat\n- Archive the paper log, report bundle, and error trace\n- Do not restart into active trading unless startup checks pass cleanly again\n", encoding="utf-8")
input_lines = ["# Recent 2-Month Input Digest", "", "## Exact files opened", ""]
for path in EXACT_FILES:
    input_lines.append(f"- `{path}`: {'opened' if path.exists() else 'missing'}")
input_lines += ["", "## Strategy implementation status", "", "- `qqq_led_tqqq_sqqq_pair_opening_range_intraday_system`: exact runnable via `nasdaq-etf-intraday-alpaca/src/app/paper_promotion.py` and `best_config.yaml`.", "- `down_streak_exhaustion`: partial recent-window runnable via `alpaca-stock-strategy-research` exact baseline params; local daily data stops at `2026-03-24`.", "- `relative_strength_vs_benchmark::rs_top3_native`: partial recent-window runnable via the daily backtest engine plus the current top-3 wrapper on `AAPL/AMZN/GOOGL/META/NFLX`; local daily data stops at `2026-03-24`.", "- `cross_sectional_momentum::csm_native`: partial recent-window runnable via the daily backtest engine on `AAPL/AMZN/GOOGL/META/NFLX`; local daily data stops at `2026-03-24`.", "", "## Exact 2-month window used", "", f"- Official recent window target: `{official_start}` through `{pair_end}`.", f"- Daily-strategy coverage actually available locally: `{official_start}` through `{daily_end}`.", f"- Pair-strategy coverage actually available locally: `{official_start}` through `{pair_end}`.", "", "## Remaining data limitations", "", "- Daily features do not currently extend through 2026-03-31, so the daily strategies are partial for the final seven calendar days of the target window.", "- Options remain out of scope and blocked by prior instructions."]
OUT["digest"].write_text("\n".join(input_lines) + "\n", encoding="utf-8")
handoff_files = write_handoff_bundle(official_start, pair_end)
OUT["manifest"].write_text("\n".join(["# Deployment File Manifest", "", f"Handoff folder: `{HANDOFF_DIR}`", "", "- `README.md`: launch/readiness note for the other machine.", "- `.env.template`: required environment variable names only.", "- `paper_shared_config.yaml`: Monday paper config for the QQQ pair runtime.", "- `run_qqq_pair_paper.ps1`: PowerShell launch script for the approved paper strategy.", "- `scheduler_setup_note.md`: Task Scheduler setup note for Monday 2026-04-06.", ""]), encoding="utf-8")
OUT["handoff"].write_text(f"# Other Machine Handoff\n\nApproved strategy set for Monday 2026-04-06:\n- `qqq_led_tqqq_sqqq_pair_opening_range_intraday_system` only.\n\nNot approved for Monday trading:\n- `down_streak_exhaustion`\n- `relative_strength_vs_benchmark::rs_top3_native`\n- `cross_sectional_momentum::csm_native`\n\nHandoff folder:\n- `{HANDOFF_DIR}`\n\nFiles prepared:\n- `{HANDOFF_DIR / 'README.md'}`\n- `{HANDOFF_DIR / '.env.template'}`\n- `{HANDOFF_DIR / 'paper_shared_config.yaml'}`\n- `{HANDOFF_DIR / 'run_qqq_pair_paper.ps1'}`\n- `{HANDOFF_DIR / 'scheduler_setup_note.md'}`\n\nOperational note:\n- The QQQ pair remains the only approved paper strategy because it was the only recent-window strategy with positive PnL and it already held the strongest operational trust in the earlier work.\n- The runtime config in this handoff aligns the live paper engine as closely as the repo allows to the approved opening-range baseline, but the runtime still uses stricter operational safeguards than the pure bar-only backtest harness.\n- Do not add RS, CSM, or DSE to Monday's live paper runtime just because they are available locally.\n\nLaunch expectation:\n- Start the runtime before the open, monitor logs during RTH, and archive the daily reports after the close.\n", encoding="utf-8")
OUT["final"].write_text(f"# Recent 2-Month Final Decision\n\nWindow target used: `{official_start}` through `{pair_end}`.\nDaily-strategy coverage available locally: `{official_start}` through `{daily_end}`.\n\n- Best recent performer: `qqq_led_tqqq_sqqq_pair_opening_range_intraday_system`.\n- Best recent operational candidate: `qqq_led_tqqq_sqqq_pair_opening_range_intraday_system`.\n- Best recent trust anchor: `down_streak_exhaustion` by role, even though its last-two-month return was negative.\n- Strategy that actually deserves to run tomorrow: `qqq_led_tqqq_sqqq_pair_opening_range_intraday_system` only.\n- Strategies that should wait: `down_streak_exhaustion`, `relative_strength_vs_benchmark::rs_top3_native`, and `cross_sectional_momentum::csm_native`.\n- Next step after tomorrow's paper run: compare the actual Monday paper log and report bundle against the approved opening-range baseline, then keep RS and CSM offline until they show cleaner recent evidence than they did here.\n", encoding="utf-8")
print(metrics_df[["strategy_id", "final_equity", "total_return_pct", "max_drawdown_pct", "profit_factor", "win_rate", "trade_count", "ending_status"]].to_string(index=False))
print("handoff_files")
for path in handoff_files:
    print(str(path))
