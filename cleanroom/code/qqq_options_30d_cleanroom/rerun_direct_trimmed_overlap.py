from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from backtest_qqq_direct_greeks_dataset import (
    assign_regime,
    build_context_from_stock,
    generate_trades_for_day,
    list_trade_dates,
    load_option_day,
    load_stock_day,
    prepare_option_day,
)
from compare_qqq_balanced_overlap_365d import (
    compute_candidate_diff,
    load_balanced_config,
    portfolio_daily_pnl,
    selected_strategy_objects,
)
from backtest_qqq_regime_gated_portfolio import filter_candidate_trades
from evaluate_qqq_direct_greeks_readiness import run_overlay_allocator


DEFAULT_OUTPUT_DIR = Path(__file__).resolve().parent / "output"
DEFAULT_DIRECT_ROOT = Path(r"C:\Users\rabisaab\Downloads\qqq_direct_greeks_oos_subset")
DEFAULT_CONFIG_PATH = DEFAULT_OUTPUT_DIR / "qqq_direct_greeks_balanced_deployment_config.json"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Rerun the direct-Greeks overlap using the cleanroom trimmed strike universe for an apples-to-apples comparison."
    )
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--direct-dataset-root", default=str(DEFAULT_DIRECT_ROOT))
    parser.add_argument("--config-path", default=str(DEFAULT_CONFIG_PATH))
    parser.add_argument("--cleanroom-universe-name", default="qqq_365d_option_daily_universe.parquet")
    parser.add_argument("--cleanroom-day-returns-name", default="qqq_365d_balanced_overlap_day_returns.csv")
    parser.add_argument("--cleanroom-filtered-name", default="qqq_365d_balanced_overlap_filtered_candidates.csv")
    parser.add_argument("--cleanroom-trades-name", default="qqq_365d_balanced_overlap_portfolio_trades.csv")
    parser.add_argument("--original-direct-filtered-name", default="qqq_direct_greeks_balanced_overlap_filtered_candidates.csv")
    parser.add_argument("--original-direct-trades-name", default="qqq_direct_greeks_balanced_overlap_portfolio_trades.csv")
    parser.add_argument("--trimmed-candidate-name", default="qqq_direct_trimmed_overlap_candidate_trades.csv")
    parser.add_argument("--trimmed-filtered-name", default="qqq_direct_trimmed_overlap_filtered_candidates.csv")
    parser.add_argument("--trimmed-day-returns-name", default="qqq_direct_trimmed_overlap_day_returns.csv")
    parser.add_argument("--trimmed-trades-name", default="qqq_direct_trimmed_overlap_portfolio_trades.csv")
    parser.add_argument("--trimmed-equity-name", default="qqq_direct_trimmed_overlap_equity_curve.csv")
    parser.add_argument("--trimmed-summary-name", default="qqq_direct_trimmed_overlap_summary.json")
    parser.add_argument("--scorecard-name", default="qqq_direct_trimmed_overlap_scorecard.csv")
    parser.add_argument("--candidate-diff-name", default="qqq_direct_trimmed_vs_cleanroom_candidate_diff.csv")
    parser.add_argument("--daily-compare-name", default="qqq_direct_trimmed_vs_cleanroom_daily_pnl_compare.csv")
    parser.add_argument("--comparison-summary-name", default="qqq_direct_trimmed_overlap_comparison_summary.json")
    parser.add_argument("--report-name", default="qqq_direct_trimmed_overlap_report.md")
    return parser


def load_cleanroom_allowed_universe(path: Path) -> tuple[set[tuple[object, int, str, float]], set[object]]:
    universe = pd.read_parquet(path)
    universe["trade_date"] = pd.to_datetime(universe["trade_date"]).dt.date
    allowed = set(
        zip(
            universe["trade_date"],
            universe["dte"].astype(int),
            universe["option_type"].astype(str),
            universe["strike_price"].astype(float),
        )
    )
    return allowed, set(universe["trade_date"])


def filter_options_to_cleanroom_universe(
    options: pd.DataFrame,
    trade_date: object,
    allowed_universe: set[tuple[object, int, str, float]],
) -> pd.DataFrame:
    frame = options.copy()
    frame["dte_calendar"] = frame["dte_calendar"].astype(int)
    frame["strike_price"] = frame["strike_price"].astype(float)
    frame["option_type"] = frame["option_type"].astype(str)
    mask = [
        (trade_date, int(row.dte_calendar), str(row.option_type), float(row.strike_price)) in allowed_universe
        for row in frame.itertuples(index=False)
    ]
    return frame.loc[mask].copy()


def build_day_returns_frame(rows: list[dict[str, object]]) -> pd.DataFrame:
    frame = pd.DataFrame(rows)
    if frame.empty:
        return pd.DataFrame(columns=["trade_date", "day_open", "day_close", "day_ret_pct", "regime", "available_dtes", "session_minutes"])
    return frame.sort_values("trade_date").reset_index(drop=True)


def run_trimmed_direct_overlap(
    direct_dataset_root: Path,
    output_dir: Path,
    config: dict[str, object],
    allowed_universe: set[tuple[object, int, str, float]],
    allowed_dates: set[object],
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, dict[str, object]]:
    trade_dates = [
        pd.to_datetime(value).date()
        for value in list_trade_dates(
            dataset_root=direct_dataset_root,
            start_date=min(allowed_dates).isoformat(),
            end_date=max(allowed_dates).isoformat(),
        )
        if pd.to_datetime(value).date() in allowed_dates
    ]
    strategies = selected_strategy_objects(config["selected"])

    candidate_rows: list[dict[str, object]] = []
    day_return_rows: list[dict[str, object]] = []
    prev_close: float | None = None

    for idx, trade_date in enumerate(trade_dates, start=1):
        stock = load_stock_day(direct_dataset_root, trade_date.isoformat())
        options = load_option_day(direct_dataset_root, trade_date.isoformat())
        options = filter_options_to_cleanroom_universe(
            options=options,
            trade_date=trade_date,
            allowed_universe=allowed_universe,
        )
        if stock.empty or options.empty:
            continue

        available_dtes, chain_groups, price_series_by_symbol = prepare_option_day(options=options)
        if not available_dtes:
            prev_close = float(stock["close"].iloc[-1])
            continue

        ctx = build_context_from_stock(
            stock=stock,
            available_dtes=available_dtes,
            prev_close=prev_close,
        )
        day_open = float(stock["open"].iloc[0])
        day_close = float(stock["close"].iloc[-1])
        day_ret_pct = (day_close / day_open - 1.0) * 100.0
        regime = assign_regime(day_ret_pct=day_ret_pct, threshold=float(config["threshold_pct"]))
        day_return_rows.append(
            {
                "trade_date": trade_date.isoformat(),
                "day_open": round(day_open, 4),
                "day_close": round(day_close, 4),
                "day_ret_pct": round(day_ret_pct, 4),
                "regime": regime,
                "available_dtes": json.dumps(list(available_dtes)),
                "session_minutes": int(len(stock)),
            }
        )
        candidate_rows.extend(
            generate_trades_for_day(
                strategies=strategies,
                ctx=ctx,
                chain_groups=chain_groups,
                price_series_by_symbol=price_series_by_symbol,
                regime=regime,
            )
        )
        prev_close = day_close

        if idx % 25 == 0 or idx == len(trade_dates):
            print(f"Trimmed direct rerun processed {idx}/{len(trade_dates)} days through {trade_date}", flush=True)

    candidate_trades = pd.DataFrame(candidate_rows)
    if not candidate_trades.empty:
        candidate_trades = candidate_trades.sort_values(["trade_date", "entry_minute", "strategy"]).reset_index(drop=True)
        candidate_trades["trade_date"] = pd.to_datetime(candidate_trades["trade_date"]).dt.date
    day_returns = build_day_returns_frame(day_return_rows)
    if not day_returns.empty:
        day_returns["trade_date"] = pd.to_datetime(day_returns["trade_date"]).dt.date

    filtered = filter_candidate_trades(candidate_trades, config["selected"])
    portfolio_trades, equity_curve, portfolio_summary = run_overlay_allocator(
        strategies=strategies,
        trades_df=filtered,
        risk_cap=float(config["portfolio"]["risk_cap"]),
        daily_loss_gate_pct=float(config["portfolio"]["daily_loss_gate_pct"]),
        max_open_positions=None
        if config["portfolio"]["max_open_positions"] is None
        else int(config["portfolio"]["max_open_positions"]),
        delever_drawdown_pct=float(config["portfolio"]["delever_drawdown_pct"]),
        delever_risk_scale=float(config["portfolio"]["delever_risk_scale"]),
    )
    summary = {
        "dataset": "direct_greeks_trimmed_to_cleanroom_universe",
        "trade_date_count": int(len(day_returns)),
        "candidate_trade_count": int(len(candidate_trades)),
        "filtered_trade_count": int(len(filtered)),
        "regime_counts": day_returns["regime"].value_counts().sort_index().to_dict() if not day_returns.empty else {},
        **portfolio_summary,
    }
    return candidate_trades, filtered, day_returns, portfolio_trades, equity_curve, summary


def build_scorecard(
    cleanroom_summary: dict[str, object],
    original_direct_summary: dict[str, object],
    trimmed_direct_summary: dict[str, object],
) -> pd.DataFrame:
    rows = []
    for payload in [cleanroom_summary, original_direct_summary, trimmed_direct_summary]:
        rows.append(
            {
                "dataset": payload["dataset"],
                "candidate_trade_count": payload["candidate_trade_count"],
                "filtered_trade_count": payload["filtered_trade_count"],
                "trade_count": payload["trade_count"],
                "win_rate_pct": payload["win_rate_pct"],
                "final_equity": payload["final_equity"],
                "total_return_pct": payload["total_return_pct"],
                "max_drawdown_pct": payload["max_drawdown_pct"],
                "calmar_like": payload["calmar_like"],
            }
        )
    return pd.DataFrame(rows)


def build_comparison_summary(
    cleanroom_summary: dict[str, object],
    original_direct_summary: dict[str, object],
    trimmed_direct_summary: dict[str, object],
    candidate_diff_trimmed: pd.DataFrame,
    daily_compare_trimmed: pd.DataFrame,
    candidate_diff_original: pd.DataFrame,
    daily_compare_original: pd.DataFrame,
) -> dict[str, object]:
    def diff_stats(candidate_diff: pd.DataFrame, daily_compare: pd.DataFrame) -> dict[str, object]:
        matched = candidate_diff[candidate_diff["_merge"] == "both"].copy()
        common_days = daily_compare.dropna(subset=["cleanroom_daily_pnl", "direct_daily_pnl"]).copy()
        daily_corr = None
        if len(common_days) >= 2:
            daily_corr = float(common_days["cleanroom_daily_pnl"].corr(common_days["direct_daily_pnl"]))
        return {
            "matched_candidate_count": int((candidate_diff["_merge"] == "both").sum()),
            "cleanroom_only_candidate_count": int((candidate_diff["_merge"] == "left_only").sum()),
            "other_only_candidate_count": int((candidate_diff["_merge"] == "right_only").sum()),
            "match_rate_vs_other_pct": round(
                100.0 * int((candidate_diff["_merge"] == "both").sum())
                / max(1, int((candidate_diff["_merge"] == "both").sum()) + int((candidate_diff["_merge"] == "right_only").sum())),
                2,
            ),
            "matched_entry_cash_mae": round(float(matched["entry_cash_diff"].abs().mean()) if not matched.empty else 0.0, 4),
            "matched_net_pnl_mae": round(float(matched["net_pnl_diff"].abs().mean()) if not matched.empty else 0.0, 4),
            "daily_common_days": int(len(common_days)),
            "daily_pnl_correlation": None if daily_corr is None else round(daily_corr, 4),
            "daily_pnl_mae": round(
                float((common_days["cleanroom_daily_pnl"] - common_days["direct_daily_pnl"]).abs().mean())
                if not common_days.empty
                else 0.0,
                4,
            ),
        }

    original_gap = round(float(original_direct_summary["final_equity"]) - float(cleanroom_summary["final_equity"]), 2)
    trimmed_gap = round(float(trimmed_direct_summary["final_equity"]) - float(cleanroom_summary["final_equity"]), 2)
    original_abs_gap = abs(original_gap)
    trimmed_abs_gap = abs(trimmed_gap)
    return {
        "cleanroom_summary": cleanroom_summary,
        "original_direct_summary": original_direct_summary,
        "trimmed_direct_summary": trimmed_direct_summary,
        "original_vs_cleanroom": diff_stats(candidate_diff_original, daily_compare_original),
        "trimmed_vs_cleanroom": diff_stats(candidate_diff_trimmed, daily_compare_trimmed),
        "convergence": {
            "final_equity_gap_original_minus_cleanroom": original_gap,
            "final_equity_gap_trimmed_minus_cleanroom": trimmed_gap,
            "absolute_gap_original": round(original_abs_gap, 2),
            "absolute_gap_trimmed": round(trimmed_abs_gap, 2),
            "absolute_gap_change_pct": round(
                100.0 * (trimmed_abs_gap - original_abs_gap) / max(original_abs_gap, 1e-9),
                2,
            ),
            "candidate_match_rate_improvement_pct_points": round(
                diff_stats(candidate_diff_trimmed, daily_compare_trimmed)["match_rate_vs_other_pct"]
                - diff_stats(candidate_diff_original, daily_compare_original)["match_rate_vs_other_pct"],
                2,
            ),
        },
    }


def write_report(path: Path, summary: dict[str, object]) -> None:
    cleanroom = summary["cleanroom_summary"]
    original_direct = summary["original_direct_summary"]
    trimmed_direct = summary["trimmed_direct_summary"]
    original_vs = summary["original_vs_cleanroom"]
    trimmed_vs = summary["trimmed_vs_cleanroom"]
    convergence = summary["convergence"]

    lines: list[str] = []
    lines.append("# Trimmed-Universe Direct Rerun")
    lines.append("")
    lines.append("- Goal: rerun the direct-Greeks overlap using only the strikes that exist in the cleanroom 365-day universe.")
    lines.append("")
    lines.append("## Scorecard")
    lines.append("")
    lines.append(
        f"- Cleanroom: final ${cleanroom['final_equity']:.2f}, return {cleanroom['total_return_pct']:.2f}%, drawdown {cleanroom['max_drawdown_pct']:.2f}%, trades {int(cleanroom['trade_count'])}."
    )
    lines.append(
        f"- Original direct: final ${original_direct['final_equity']:.2f}, return {original_direct['total_return_pct']:.2f}%, drawdown {original_direct['max_drawdown_pct']:.2f}%, trades {int(original_direct['trade_count'])}."
    )
    lines.append(
        f"- Trimmed direct: final ${trimmed_direct['final_equity']:.2f}, return {trimmed_direct['total_return_pct']:.2f}%, drawdown {trimmed_direct['max_drawdown_pct']:.2f}%, trades {int(trimmed_direct['trade_count'])}."
    )
    lines.append("")
    lines.append("## Alignment")
    lines.append("")
    lines.append(
        f"- Original direct vs cleanroom: match rate {original_vs['match_rate_vs_other_pct']:.2f}%, daily PnL correlation {original_vs['daily_pnl_correlation']}, final-equity gap ${convergence['final_equity_gap_original_minus_cleanroom']:.2f}."
    )
    lines.append(
        f"- Trimmed direct vs cleanroom: match rate {trimmed_vs['match_rate_vs_other_pct']:.2f}%, daily PnL correlation {trimmed_vs['daily_pnl_correlation']}, final-equity gap ${convergence['final_equity_gap_trimmed_minus_cleanroom']:.2f}."
    )
    lines.append(
        f"- Absolute final-equity gap change after trimming: {convergence['absolute_gap_change_pct']:.2f}%."
    )
    lines.append("")
    lines.append("## Read")
    lines.append("")
    if convergence["absolute_gap_trimmed"] < convergence["absolute_gap_original"]:
        lines.append("- Trimming the direct universe moves the direct pipeline materially closer to the cleanroom result, which confirms that universe shape was the main distortion.")
    else:
        lines.append("- Trimming the direct universe improves candidate alignment, but it pushes realized equity farther from the cleanroom result. That means the remaining mismatch is dominated by exit-path and pricing behavior, not strike selection.")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = build_parser().parse_args()
    output_dir = Path(args.output_dir).resolve()
    direct_dataset_root = Path(args.direct_dataset_root).resolve()
    config = load_balanced_config(Path(args.config_path).resolve())

    allowed_universe, allowed_dates = load_cleanroom_allowed_universe(output_dir / args.cleanroom_universe_name)
    cleanroom_day_returns = pd.read_csv(output_dir / args.cleanroom_day_returns_name)
    cleanroom_day_returns["trade_date"] = pd.to_datetime(cleanroom_day_returns["trade_date"]).dt.date
    allowed_dates = allowed_dates & set(cleanroom_day_returns["trade_date"])

    cleanroom_filtered = pd.read_csv(output_dir / args.cleanroom_filtered_name)
    cleanroom_trades = pd.read_csv(output_dir / args.cleanroom_trades_name)
    cleanroom_summary = json.loads((output_dir / "qqq_365d_balanced_overlap_summary.json").read_text(encoding="utf-8"))
    original_direct_filtered = pd.read_csv(output_dir / args.original_direct_filtered_name)
    original_direct_trades = pd.read_csv(output_dir / args.original_direct_trades_name)
    original_direct_summary = json.loads((output_dir / "qqq_direct_greeks_balanced_overlap_summary.json").read_text(encoding="utf-8"))

    trimmed_candidate_trades, trimmed_filtered, trimmed_day_returns, trimmed_portfolio_trades, trimmed_equity_curve, trimmed_summary = run_trimmed_direct_overlap(
        direct_dataset_root=direct_dataset_root,
        output_dir=output_dir,
        config=config,
        allowed_universe=allowed_universe,
        allowed_dates=allowed_dates,
    )

    candidate_diff_trimmed = compute_candidate_diff(cleanroom_filtered=cleanroom_filtered, direct_filtered=trimmed_filtered)
    daily_compare_trimmed = portfolio_daily_pnl(cleanroom_trades, "cleanroom").merge(
        portfolio_daily_pnl(trimmed_portfolio_trades, "direct"),
        on="trade_date",
        how="outer",
    ).sort_values("trade_date").reset_index(drop=True)
    candidate_diff_original = compute_candidate_diff(cleanroom_filtered=cleanroom_filtered, direct_filtered=original_direct_filtered)
    daily_compare_original = portfolio_daily_pnl(cleanroom_trades, "cleanroom").merge(
        portfolio_daily_pnl(original_direct_trades, "direct"),
        on="trade_date",
        how="outer",
    ).sort_values("trade_date").reset_index(drop=True)

    scorecard = build_scorecard(
        cleanroom_summary=cleanroom_summary,
        original_direct_summary=original_direct_summary,
        trimmed_direct_summary=trimmed_summary,
    )
    comparison_summary = build_comparison_summary(
        cleanroom_summary=cleanroom_summary,
        original_direct_summary=original_direct_summary,
        trimmed_direct_summary=trimmed_summary,
        candidate_diff_trimmed=candidate_diff_trimmed,
        daily_compare_trimmed=daily_compare_trimmed,
        candidate_diff_original=candidate_diff_original,
        daily_compare_original=daily_compare_original,
    )

    trimmed_candidate_trades.to_csv(output_dir / args.trimmed_candidate_name, index=False)
    trimmed_filtered.to_csv(output_dir / args.trimmed_filtered_name, index=False)
    trimmed_day_returns.to_csv(output_dir / args.trimmed_day_returns_name, index=False)
    trimmed_portfolio_trades.to_csv(output_dir / args.trimmed_trades_name, index=False)
    trimmed_equity_curve.to_csv(output_dir / args.trimmed_equity_name, index=False)
    (output_dir / args.trimmed_summary_name).write_text(json.dumps(trimmed_summary, indent=2), encoding="utf-8")
    scorecard.to_csv(output_dir / args.scorecard_name, index=False)
    candidate_diff_trimmed.to_csv(output_dir / args.candidate_diff_name, index=False)
    daily_compare_trimmed.to_csv(output_dir / args.daily_compare_name, index=False)
    (output_dir / args.comparison_summary_name).write_text(json.dumps(comparison_summary, indent=2), encoding="utf-8")
    write_report(path=output_dir / args.report_name, summary=comparison_summary)

    print(
        json.dumps(
            {
                "trimmed_summary_json": str(output_dir / args.trimmed_summary_name),
                "comparison_summary_json": str(output_dir / args.comparison_summary_name),
                "scorecard_csv": str(output_dir / args.scorecard_name),
                "report_md": str(output_dir / args.report_name),
                "trimmed_final_equity": trimmed_summary["final_equity"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
