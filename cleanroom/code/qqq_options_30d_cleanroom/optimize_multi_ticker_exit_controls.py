from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from itertools import product
from pathlib import Path
from typing import Any

import pandas as pd

import run_multiticker_cleanroom_portfolio as mt


DEFAULT_RESEARCH_DIR = Path(__file__).resolve().parent / "output" / "multi_ticker_365d"
DEFAULT_STARTING_EQUITY = 25_000.0
DEFAULT_RISK_CAP = 0.15
DEFAULT_TICKERS = ("qqq", "spy", "iwm", "nvda", "tsla", "msft")
SELECTED_STRATEGIES = (
    "qqq__fast__trend_long_call_next_expiry",
    "qqq__slow__trend_long_call_next_expiry",
    "qqq__fast__trend_long_put_next_expiry",
    "qqq__slow__orb_long_put_same_day",
    "spy__fast__trend_long_call_next_expiry",
    "spy__base__trend_long_put_next_expiry",
    "spy__fast__trend_long_put_next_expiry",
    "iwm__fast__trend_long_call_next_expiry",
    "iwm__slow__trend_long_call_next_expiry",
    "iwm__fast__trend_long_put_next_expiry",
    "iwm__base__trend_long_put_next_expiry",
    "nvda__fast__trend_long_call_next_expiry",
    "nvda__base__trend_long_put_next_expiry",
    "tsla__base__trend_long_call_next_expiry",
    "tsla__base__trend_long_put_next_expiry",
    "tsla__fast__trend_long_put_next_expiry",
    "msft__fast__trend_long_call_next_expiry",
    "msft__base__trend_long_call_next_expiry",
    "msft__slow__trend_long_call_next_expiry",
    "msft__base__trend_long_put_next_expiry",
    "msft__slow__trend_long_put_next_expiry",
)
FAMILY_PARAM_GRID = {
    "trend_long_call_next_expiry": {
        "profit_target_multiple": [0.35, 0.40, 0.45],
        "stop_loss_multiple": [0.22, 0.26, 0.30],
        "hard_exit_minute": [315, 330, 360],
    },
    "trend_long_put_next_expiry": {
        "profit_target_multiple": [0.35, 0.40, 0.45],
        "stop_loss_multiple": [0.22, 0.26, 0.30],
        "hard_exit_minute": [315, 330, 360],
    },
    "orb_long_put_same_day": {
        "profit_target_multiple": [0.40, 0.50, 0.60],
        "stop_loss_multiple": [0.25, 0.30, 0.35],
        "hard_exit_minute": [345, 360, 375],
    },
}


@dataclass(frozen=True)
class ExitParams:
    profit_target_multiple: float
    stop_loss_multiple: float
    hard_exit_minute: int

    def as_dict(self) -> dict[str, Any]:
        return {
            "profit_target_multiple": self.profit_target_multiple,
            "stop_loss_multiple": self.stop_loss_multiple,
            "hard_exit_minute": self.hard_exit_minute,
        }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Analyze and tighten exit controls for the promoted multi-ticker portfolio."
    )
    parser.add_argument("--research-dir", default=str(DEFAULT_RESEARCH_DIR))
    parser.add_argument("--risk-cap", type=float, default=DEFAULT_RISK_CAP)
    return parser


def load_selected_strategy_map() -> dict[str, Any]:
    strategy_map: dict[str, Any] = {}
    profiles = mt.build_timing_profiles()
    for ticker in DEFAULT_TICKERS:
        for strategy in mt.build_strategy_variants(ticker, profiles):
            if strategy.name in SELECTED_STRATEGIES:
                strategy_map[strategy.name] = strategy
    missing = [name for name in SELECTED_STRATEGIES if name not in strategy_map]
    if missing:
        raise KeyError(f"missing selected strategies: {missing}")
    return strategy_map


def build_baseline_family_params(strategy_map: dict[str, Any]) -> dict[str, ExitParams]:
    family_params: dict[str, ExitParams] = {}
    for strategy in strategy_map.values():
        family_params.setdefault(
            mt.parse_strategy_metadata(strategy.name)[2],
            ExitParams(
                profit_target_multiple=float(strategy.profit_target_multiple),
                stop_loss_multiple=float(strategy.stop_loss_multiple),
                hard_exit_minute=int(strategy.hard_exit_minute),
            ),
        )
    return family_params


def parse_mtm(row: pd.Series) -> dict[int, float]:
    payload = json.loads(str(row["mark_to_market_json"]))
    return {int(key): float(value) for key, value in payload.items()}


def compute_net_pnl(entry_cash_per_combo: float, entry_commission_per_combo: float, mtm_value: float) -> float:
    return float(entry_cash_per_combo) - float(entry_commission_per_combo) + float(mtm_value)


def adjust_trade_row(row: pd.Series, params: ExitParams) -> dict[str, Any]:
    adjusted = row.to_dict()
    mtm = parse_mtm(row)
    entry_cash_per_combo = float(row["entry_cash_per_combo"])
    entry_commission_per_combo = float(row["entry_commission_per_combo"])
    exit_commission_per_combo = float(row["exit_commission_per_combo"])
    target_dollars = abs(entry_cash_per_combo) * float(params.profit_target_multiple)
    stop_dollars = abs(entry_cash_per_combo) * float(params.stop_loss_multiple)

    default_mtm = float(row["exit_cash_per_combo"]) - exit_commission_per_combo
    chosen_minute = int(row["exit_minute"])
    chosen_reason = str(row["exit_reason"])
    chosen_mtm = default_mtm

    for minute_index, mtm_value in sorted(mtm.items()):
        if minute_index <= int(row["entry_minute"]):
            continue
        current_pnl = compute_net_pnl(entry_cash_per_combo, entry_commission_per_combo, mtm_value)
        if current_pnl >= target_dollars:
            chosen_minute = minute_index
            chosen_reason = "profit_target"
            chosen_mtm = mtm_value
            break
        if current_pnl <= -stop_dollars:
            chosen_minute = minute_index
            chosen_reason = "stop_loss"
            chosen_mtm = mtm_value
            break
        if minute_index >= int(params.hard_exit_minute):
            chosen_minute = minute_index
            chosen_reason = "time_exit"
            chosen_mtm = mtm_value
            break

    net_pnl_per_combo = compute_net_pnl(entry_cash_per_combo, entry_commission_per_combo, chosen_mtm)
    adjusted["exit_minute"] = int(chosen_minute)
    adjusted["exit_reason"] = chosen_reason
    adjusted["exit_cash_per_combo"] = round(chosen_mtm + exit_commission_per_combo, 4)
    adjusted["net_pnl_per_combo"] = round(net_pnl_per_combo, 4)
    adjusted["holding_minutes"] = int(chosen_minute) - int(row["entry_minute"])
    adjusted["return_on_risk_pct"] = (
        round((net_pnl_per_combo / float(row["max_loss_per_combo"])) * 100.0, 4)
        if float(row["max_loss_per_combo"]) > 0.0
        else 0.0
    )
    if row["entry_time_et"]:
        entry_time = pd.Timestamp(row["entry_time_et"])
        adjusted["exit_time_et"] = (entry_time + pd.Timedelta(minutes=adjusted["holding_minutes"])).isoformat()
    return adjusted


def apply_family_params(
    candidates: pd.DataFrame,
    family_params: dict[str, ExitParams],
) -> pd.DataFrame:
    adjusted_rows: list[dict[str, Any]] = []
    for row in candidates.to_dict(orient="records"):
        params = family_params[str(row["base_strategy"])]
        adjusted_rows.append(adjust_trade_row(pd.Series(row), params))
    adjusted = pd.DataFrame(adjusted_rows)
    adjusted["trade_date"] = pd.to_datetime(adjusted["trade_date"]).dt.date
    adjusted = adjusted.sort_values(["trade_date", "entry_minute", "strategy"]).reset_index(drop=True)
    return adjusted


def evaluate_portfolio(
    candidates: pd.DataFrame,
    strategy_map: dict[str, Any],
    *,
    risk_cap: float,
) -> tuple[dict[str, Any], pd.DataFrame, pd.DataFrame]:
    strategies = mt.strategy_objects_from_names(list(SELECTED_STRATEGIES), strategy_map)
    trades, equity, summary = mt.run_portfolio_allocator(
        strategies=strategies,
        trades_df=candidates,
        portfolio_max_open_risk_fraction=risk_cap,
        starting_equity=DEFAULT_STARTING_EQUITY,
    )
    result = {
        "risk_cap": risk_cap,
        "final_equity": float(summary["final_equity"]),
        "total_return_pct": float(summary["total_return_pct"]),
        "trade_count": int(summary["trade_count"]),
        "win_rate_pct": float(summary["win_rate_pct"]),
        "max_drawdown_pct": float(summary["max_drawdown_pct"]),
        "calmar_like": mt.score_drawdown(
            total_return_pct=float(summary["total_return_pct"]),
            max_drawdown_pct=float(summary["max_drawdown_pct"]),
        ),
        "strategy_contributions": list(summary.get("strategy_contributions", [])),
    }
    return result, trades, equity


def build_mae_mfe_tables(candidates: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    trade_rows: list[dict[str, Any]] = []
    for row in candidates.to_dict(orient="records"):
        mtm = parse_mtm(pd.Series(row))
        pnl_path = [
            compute_net_pnl(
                float(row["entry_cash_per_combo"]),
                float(row["entry_commission_per_combo"]),
                mtm_value,
            )
            for _, mtm_value in sorted(mtm.items())
        ]
        if not pnl_path:
            continue
        trade_rows.append(
            {
                "strategy": row["strategy"],
                "ticker": row["ticker"],
                "base_strategy": row["base_strategy"],
                "trade_date": row["trade_date"],
                "exit_reason": row["exit_reason"],
                "net_pnl_per_combo": float(row["net_pnl_per_combo"]),
                "mae_dollars": round(min(pnl_path), 4),
                "mfe_dollars": round(max(pnl_path), 4),
            }
        )
    trade_df = pd.DataFrame(trade_rows)
    family_df = (
        trade_df.groupby("base_strategy", as_index=False)
        .agg(
            trade_count=("strategy", "size"),
            avg_mae_dollars=("mae_dollars", "mean"),
            median_mae_dollars=("mae_dollars", "median"),
            avg_mfe_dollars=("mfe_dollars", "mean"),
            median_mfe_dollars=("mfe_dollars", "median"),
            avg_final_net_pnl=("net_pnl_per_combo", "mean"),
        )
        .sort_values("avg_final_net_pnl", ascending=False)
        .reset_index(drop=True)
    )
    return trade_df, family_df


def format_params(params: ExitParams) -> str:
    return (
        f"target={params.profit_target_multiple:.2f}, "
        f"stop={params.stop_loss_multiple:.2f}, "
        f"hard_exit={params.hard_exit_minute}"
    )


def main() -> None:
    args = build_parser().parse_args()
    research_dir = Path(args.research_dir).resolve()
    strategy_map = load_selected_strategy_map()
    baseline_family_params = build_baseline_family_params(strategy_map)

    candidates = pd.read_csv(research_dir / "combined_promoted_candidates.csv")
    candidates = candidates[candidates["strategy"].isin(SELECTED_STRATEGIES)].copy()
    candidates["trade_date"] = pd.to_datetime(candidates["trade_date"]).dt.date
    candidates = candidates.sort_values(["trade_date", "entry_minute", "strategy"]).reset_index(drop=True)

    mae_trade_df, mae_family_df = build_mae_mfe_tables(candidates)
    mae_trade_df.to_csv(research_dir / "multi_ticker_exit_mae_mfe_trade_level.csv", index=False)
    mae_family_df.to_csv(research_dir / "multi_ticker_exit_mae_mfe_by_family.csv", index=False)

    baseline_summary, baseline_trades, baseline_equity = evaluate_portfolio(
        candidates,
        strategy_map,
        risk_cap=args.risk_cap,
    )

    family_rows: list[dict[str, Any]] = []
    top_family_params: dict[str, list[ExitParams]] = {}
    for family_name, grid in FAMILY_PARAM_GRID.items():
        best_rows: list[dict[str, Any]] = []
        for target_multiple, stop_multiple, hard_exit_minute in product(
            grid["profit_target_multiple"],
            grid["stop_loss_multiple"],
            grid["hard_exit_minute"],
        ):
            trial_family_params = dict(baseline_family_params)
            trial_family_params[family_name] = ExitParams(
                profit_target_multiple=float(target_multiple),
                stop_loss_multiple=float(stop_multiple),
                hard_exit_minute=int(hard_exit_minute),
            )
            adjusted_candidates = apply_family_params(candidates, trial_family_params)
            trial_summary, _, _ = evaluate_portfolio(
                adjusted_candidates,
                strategy_map,
                risk_cap=args.risk_cap,
            )
            row = {
                "family": family_name,
                **trial_family_params[family_name].as_dict(),
                "final_equity": trial_summary["final_equity"],
                "total_return_pct": trial_summary["total_return_pct"],
                "trade_count": trial_summary["trade_count"],
                "win_rate_pct": trial_summary["win_rate_pct"],
                "max_drawdown_pct": trial_summary["max_drawdown_pct"],
                "calmar_like": trial_summary["calmar_like"],
            }
            family_rows.append(row)
            best_rows.append(row)
        family_df = pd.DataFrame(best_rows).sort_values(
            ["calmar_like", "total_return_pct", "final_equity"],
            ascending=[False, False, False],
        )
        top_family_params[family_name] = [
            ExitParams(
                profit_target_multiple=float(item["profit_target_multiple"]),
                stop_loss_multiple=float(item["stop_loss_multiple"]),
                hard_exit_minute=int(item["hard_exit_minute"]),
            )
            for item in family_df.head(3).to_dict(orient="records")
        ]

    family_sweep_df = pd.DataFrame(family_rows).sort_values(
        ["family", "calmar_like", "total_return_pct"],
        ascending=[True, False, False],
    )
    family_sweep_df.to_csv(research_dir / "multi_ticker_exit_family_sweep.csv", index=False)

    joint_rows: list[dict[str, Any]] = []
    best_joint_summary: dict[str, Any] | None = None
    best_joint_params = dict(baseline_family_params)
    best_joint_candidates = candidates.copy()
    best_joint_trades = baseline_trades
    best_joint_equity = baseline_equity
    for call_params, put_params, orb_params in product(
        top_family_params["trend_long_call_next_expiry"],
        top_family_params["trend_long_put_next_expiry"],
        top_family_params["orb_long_put_same_day"],
    ):
        joint_params = dict(baseline_family_params)
        joint_params["trend_long_call_next_expiry"] = call_params
        joint_params["trend_long_put_next_expiry"] = put_params
        joint_params["orb_long_put_same_day"] = orb_params
        adjusted_candidates = apply_family_params(candidates, joint_params)
        joint_summary, joint_trades, joint_equity = evaluate_portfolio(
            adjusted_candidates,
            strategy_map,
            risk_cap=args.risk_cap,
        )
        row = {
            "trend_long_call_next_expiry": format_params(call_params),
            "trend_long_put_next_expiry": format_params(put_params),
            "orb_long_put_same_day": format_params(orb_params),
            "final_equity": joint_summary["final_equity"],
            "total_return_pct": joint_summary["total_return_pct"],
            "trade_count": joint_summary["trade_count"],
            "win_rate_pct": joint_summary["win_rate_pct"],
            "max_drawdown_pct": joint_summary["max_drawdown_pct"],
            "calmar_like": joint_summary["calmar_like"],
        }
        joint_rows.append(row)
        if best_joint_summary is None:
            best_joint_summary = joint_summary
            best_joint_params = joint_params
            best_joint_candidates = adjusted_candidates
            best_joint_trades = joint_trades
            best_joint_equity = joint_equity
            continue
        current_tuple = (
            row["calmar_like"],
            row["total_return_pct"],
            row["final_equity"],
        )
        best_tuple = (
            best_joint_summary["calmar_like"],
            best_joint_summary["total_return_pct"],
            best_joint_summary["final_equity"],
        )
        if current_tuple > best_tuple:
            best_joint_summary = joint_summary
            best_joint_params = joint_params
            best_joint_candidates = adjusted_candidates
            best_joint_trades = joint_trades
            best_joint_equity = joint_equity

    if best_joint_summary is None:
        raise RuntimeError("joint exit sweep produced no result")

    joint_df = pd.DataFrame(joint_rows).sort_values(
        ["calmar_like", "total_return_pct", "final_equity"],
        ascending=[False, False, False],
    )
    joint_df.to_csv(research_dir / "multi_ticker_exit_joint_sweep.csv", index=False)
    best_joint_candidates.to_csv(research_dir / "multi_ticker_exit_optimized_candidates.csv", index=False)
    best_joint_trades.to_csv(research_dir / "multi_ticker_exit_optimized_portfolio_trades.csv", index=False)
    best_joint_equity.to_csv(research_dir / "multi_ticker_exit_optimized_portfolio_equity.csv", index=False)

    best_payload = {
        "baseline_summary": baseline_summary,
        "optimized_summary": best_joint_summary,
        "baseline_family_params": {
            name: params.as_dict() for name, params in baseline_family_params.items()
        },
        "optimized_family_params": {
            name: params.as_dict() for name, params in best_joint_params.items()
        },
        "return_lift_pct": round(
            float(best_joint_summary["total_return_pct"]) - float(baseline_summary["total_return_pct"]),
            2,
        ),
        "drawdown_change_pct": round(
            float(best_joint_summary["max_drawdown_pct"]) - float(baseline_summary["max_drawdown_pct"]),
            2,
        ),
    }
    (research_dir / "multi_ticker_exit_best_config.json").write_text(
        json.dumps(best_payload, indent=2),
        encoding="utf-8",
    )

    report_lines = [
        "# Multi-Ticker Exit Optimization",
        "",
        f"- Baseline refined live book: ${baseline_summary['final_equity']:.2f}, {baseline_summary['total_return_pct']:.2f}%, drawdown {baseline_summary['max_drawdown_pct']:.2f}%, risk cap {args.risk_cap * 100:.0f}%.",
        f"- Optimized exit book: ${best_joint_summary['final_equity']:.2f}, {best_joint_summary['total_return_pct']:.2f}%, drawdown {best_joint_summary['max_drawdown_pct']:.2f}%.",
        f"- Return lift vs baseline: {best_payload['return_lift_pct']:.2f} percentage points.",
        f"- Drawdown change vs baseline: {best_payload['drawdown_change_pct']:.2f} points.",
        "",
        "## Recommended Family Params",
        "",
    ]
    for family_name in ["trend_long_call_next_expiry", "trend_long_put_next_expiry", "orb_long_put_same_day"]:
        report_lines.append(f"- `{family_name}`: {format_params(best_joint_params[family_name])}")
    report_lines.extend(
        [
            "",
            "## MAE / MFE",
            "",
            mae_family_df.to_markdown(index=False),
            "",
        ]
    )
    (research_dir / "multi_ticker_exit_report.md").write_text(
        "\n".join(report_lines) + "\n",
        encoding="utf-8",
    )

    print(json.dumps(best_payload, indent=2))


if __name__ == "__main__":
    main()
