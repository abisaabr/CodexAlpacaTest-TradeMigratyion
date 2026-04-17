from __future__ import annotations

import json
import sys
from itertools import product
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent
DOWNLOADS_ROOT = ROOT.parent
REPO_ROOT = DOWNLOADS_ROOT / "codexalpaca_repo"

sys.path.append(str(ROOT))
sys.path.append(str(REPO_ROOT))

import evaluate_qqq_direct_greeks_readiness as readiness
import run_multiticker_cleanroom_portfolio as mt
from alpaca_lab.multi_ticker_portfolio.config import load_portfolio_config
from backtest_qqq_greeks_portfolio import DeltaLegTemplate, DeltaStrategy


OUTPUT_DIR = ROOT / "output" / "multi_ticker_365d"
DEFAULT_CANDIDATES = OUTPUT_DIR / "combined_promoted_candidates.csv"
DEFAULT_CONFIG_PATH = REPO_ROOT / "config" / "multi_ticker_paper_portfolio.yaml"


def build_strategy_objects(config_path: Path) -> list[DeltaStrategy]:
    config = load_portfolio_config(config_path)
    strategies: list[DeltaStrategy] = []
    for strategy in config.strategies:
        legs = tuple(
            DeltaLegTemplate(
                option_type=leg.option_type,
                side=leg.side,
                target_delta=leg.target_delta,
                min_abs_delta=leg.min_abs_delta,
                max_abs_delta=leg.max_abs_delta,
            )
            for leg in strategy.legs
        )
        strategies.append(
            DeltaStrategy(
                name=strategy.name,
                family=strategy.family,
                description=strategy.description,
                dte_mode=strategy.dte_mode,
                legs=legs,
                signal_name=strategy.signal_name,
                hard_exit_minute=strategy.hard_exit_minute,
                risk_fraction=strategy.risk_fraction,
                max_contracts=strategy.max_contracts,
                profit_target_multiple=strategy.profit_target_multiple,
                stop_loss_multiple=strategy.stop_loss_multiple,
            )
        )
    return strategies


def load_selected_candidates(path: Path, strategy_names: set[str]) -> pd.DataFrame:
    trades = pd.read_csv(path)
    trades = trades.loc[trades["strategy"].isin(strategy_names)].copy()
    return trades.sort_values(["trade_date", "entry_minute", "strategy"]).reset_index(drop=True)


def run_raw_baseline(
    *,
    strategies: list[DeltaStrategy],
    trades: pd.DataFrame,
    risk_cap: float,
) -> dict[str, object]:
    _, _, summary = mt.run_portfolio_allocator(
        strategies=strategies,
        trades_df=trades,
        portfolio_max_open_risk_fraction=risk_cap,
        starting_equity=25_000.0,
    )
    return {
        "scenario": "raw_baseline",
        "daily_loss_gate_pct": None,
        "max_open_positions": None,
        "delever_drawdown_pct": None,
        "delever_risk_scale": 1.0,
        **summary,
    }


def run_overlay_scenario(
    *,
    scenario: str,
    strategies: list[DeltaStrategy],
    trades: pd.DataFrame,
    risk_cap: float,
    daily_loss_gate_pct: float | None,
    max_open_positions: int | None,
    delever_drawdown_pct: float | None,
    delever_risk_scale: float,
) -> dict[str, object]:
    _, _, summary = readiness.run_overlay_allocator(
        strategies=strategies,
        trades_df=trades,
        risk_cap=risk_cap,
        daily_loss_gate_pct=daily_loss_gate_pct,
        max_open_positions=max_open_positions,
        delever_drawdown_pct=delever_drawdown_pct,
        delever_risk_scale=delever_risk_scale,
    )
    return {
        "scenario": scenario,
        "daily_loss_gate_pct": daily_loss_gate_pct,
        "max_open_positions": max_open_positions,
        "delever_drawdown_pct": delever_drawdown_pct,
        "delever_risk_scale": delever_risk_scale,
        **summary,
    }


def score_summary(summary: dict[str, object]) -> tuple[bool, float, float, float]:
    return (
        float(summary["total_return_pct"]) > 0.0,
        float(summary["calmar_like"]),
        float(summary["final_equity"]),
        float(summary["win_rate_pct"]),
    )


def pick_defensive_candidate(results: pd.DataFrame, baseline: pd.Series) -> pd.Series:
    candidates = results[results["scenario"] != "raw_baseline"].copy()
    candidates = candidates[candidates["total_return_pct"] >= float(baseline["total_return_pct"]) * 0.95]
    if candidates.empty:
        return baseline
    candidates = candidates.sort_values(
        ["max_drawdown_pct", "final_equity"],
        ascending=[False, False],
    ).reset_index(drop=True)
    return candidates.iloc[0]


def write_report(
    *,
    path: Path,
    baseline: pd.Series,
    current_live: pd.Series,
    best_overall: pd.Series,
    best_defensive: pd.Series,
    results: pd.DataFrame,
) -> None:
    lines: list[str] = []
    lines.append("# Multi-Ticker Risk Overlay Optimization")
    lines.append("")
    lines.append(
        f"- Raw baseline: ${baseline['final_equity']:.2f}, {baseline['total_return_pct']:.2f}%, drawdown {baseline['max_drawdown_pct']:.2f}%, trades {int(baseline['trade_count'])}."
    )
    lines.append(
        f"- Current live overlay config: ${current_live['final_equity']:.2f}, {current_live['total_return_pct']:.2f}%, drawdown {current_live['max_drawdown_pct']:.2f}%, trades {int(current_live['trade_count'])}."
    )
    lines.append(
        f"- Best overall overlay: `{best_overall['scenario']}` -> ${best_overall['final_equity']:.2f}, {best_overall['total_return_pct']:.2f}%, drawdown {best_overall['max_drawdown_pct']:.2f}%."
    )
    lines.append(
        f"- Best defensive overlay keeping at least 95% of raw return: `{best_defensive['scenario']}` -> ${best_defensive['final_equity']:.2f}, {best_defensive['total_return_pct']:.2f}%, drawdown {best_defensive['max_drawdown_pct']:.2f}%."
    )
    lines.append("")
    lines.append("## Key Read")
    lines.append("")
    lines.append(
        f"- Current daily loss gate cost: {baseline['total_return_pct'] - current_live['total_return_pct']:.2f} return points and {current_live['max_drawdown_pct'] - baseline['max_drawdown_pct']:.2f} drawdown points."
    )
    lines.append(
        f"- Best overlay lift vs raw baseline: {best_overall['total_return_pct'] - baseline['total_return_pct']:.2f} return points and {best_overall['max_drawdown_pct'] - baseline['max_drawdown_pct']:.2f} drawdown points."
    )
    lines.append("")
    lines.append("## Top Scenarios")
    lines.append("")
    for row in results.head(10).itertuples(index=False):
        lines.append(
            f"- `{row.scenario}`: final ${row.final_equity:.2f}, return {row.total_return_pct:.2f}%, drawdown {row.max_drawdown_pct:.2f}%, trades {int(row.trade_count)}."
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    strategies = build_strategy_objects(DEFAULT_CONFIG_PATH)
    strategy_names = {strategy.name for strategy in strategies}
    trades = load_selected_candidates(DEFAULT_CANDIDATES, strategy_names)
    risk_cap = 0.15

    rows: list[dict[str, object]] = []
    baseline = run_raw_baseline(strategies=strategies, trades=trades, risk_cap=risk_cap)
    rows.append(baseline)

    current_cfg = load_portfolio_config(DEFAULT_CONFIG_PATH).risk
    rows.append(
        run_overlay_scenario(
            scenario="current_live_config",
            strategies=strategies,
            trades=trades,
            risk_cap=risk_cap,
            daily_loss_gate_pct=current_cfg.daily_loss_gate_pct,
            max_open_positions=current_cfg.max_open_positions,
            delever_drawdown_pct=current_cfg.delever_drawdown_pct,
            delever_risk_scale=current_cfg.delever_risk_scale,
        )
    )

    daily_gate_values: list[float | None] = [None, 0.02, 0.025, 0.03, 0.035, 0.04, 0.05]
    max_open_values: list[int | None] = [None, 10, 8]
    delever_values: list[tuple[float | None, float]] = [
        (None, 1.0),
        (8.0, 0.75),
        (8.0, 0.50),
        (10.0, 0.75),
        (12.0, 0.75),
    ]

    for daily_gate_pct, max_open_positions, (delever_drawdown_pct, delever_risk_scale) in product(
        daily_gate_values,
        max_open_values,
        delever_values,
    ):
        scenario = (
            f"gate={daily_gate_pct if daily_gate_pct is not None else 'none'}"
            f"|max_open={max_open_positions if max_open_positions is not None else 'none'}"
            f"|dd={delever_drawdown_pct if delever_drawdown_pct is not None else 'none'}"
            f"|scale={delever_risk_scale:.2f}"
        )
        rows.append(
            run_overlay_scenario(
                scenario=scenario,
                strategies=strategies,
                trades=trades,
                risk_cap=risk_cap,
                daily_loss_gate_pct=daily_gate_pct,
                max_open_positions=max_open_positions,
                delever_drawdown_pct=delever_drawdown_pct,
                delever_risk_scale=delever_risk_scale,
            )
        )

    results = pd.DataFrame(rows).drop_duplicates(subset=["scenario"]).reset_index(drop=True)
    results["return_vs_raw_pct"] = results["total_return_pct"] - float(baseline["total_return_pct"])
    results["drawdown_vs_raw_pct"] = results["max_drawdown_pct"] - float(baseline["max_drawdown_pct"])
    results = results.sort_values(
        ["calmar_like", "final_equity", "total_return_pct"],
        ascending=[False, False, False],
    ).reset_index(drop=True)

    baseline_row = results.loc[results["scenario"] == "raw_baseline"].iloc[0]
    current_live_row = results.loc[results["scenario"] == "current_live_config"].iloc[0]
    best_overall = results.iloc[0]
    best_defensive = pick_defensive_candidate(results, baseline_row)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    results.to_csv(OUTPUT_DIR / "multi_ticker_risk_overlay_sweep.csv", index=False)

    summary_payload = {
        "raw_baseline": baseline_row.to_dict(),
        "current_live_config": current_live_row.to_dict(),
        "best_overall": best_overall.to_dict(),
        "best_defensive": best_defensive.to_dict(),
    }
    (OUTPUT_DIR / "multi_ticker_risk_overlay_best.json").write_text(
        json.dumps(summary_payload, indent=2, default=str),
        encoding="utf-8",
    )
    write_report(
        path=OUTPUT_DIR / "multi_ticker_risk_overlay_report.md",
        baseline=baseline_row,
        current_live=current_live_row,
        best_overall=best_overall,
        best_defensive=best_defensive,
        results=results,
    )
    print(json.dumps(summary_payload, indent=2, default=str))


if __name__ == "__main__":
    main()
