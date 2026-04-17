from __future__ import annotations

from pathlib import Path

import pandas as pd

import qqq_crsi_backtest as base

REPORT_DIR = Path(r"C:\Users\rabisaab\Downloads\reports")
OUT_METRICS = REPORT_DIR / "qqq_crsi_domcycle_grid_metrics.csv"
OUT_WINNERS = REPORT_DIR / "qqq_crsi_domcycle_best_per_timeframe.csv"
OUT_REPORT = REPORT_DIR / "qqq_crsi_domcycle_grid_report.md"

DCL_VALUES = tuple(range(10, 61, 2))


def main() -> None:
    raw_rth, _ = base.load_rth_qqq()
    best_rows: list[dict[str, object]] = []
    top_tables: dict[int, pd.DataFrame] = {}

    for timeframe in base.TIMEFRAMES:
        tf_frame = base.resample_intraday(raw_rth, timeframe)
        session = base.build_session_data(tf_frame)
        close = tf_frame["close"].to_numpy(dtype="float64")
        timeframe_rows: list[dict[str, object]] = []

        for domcycle in DCL_VALUES:
            configs: list[dict[str, object]] = []
            crsi = base.compute_crsi(tf_frame["close"], domcycle)
            crsi_np = crsi.to_numpy(dtype="float64")
            for leveling in base.LEVELINGS:
                low_band, high_band = base.compute_bands(crsi, domcycle, leveling)
                low_np = low_band.to_numpy(dtype="float64")
                high_np = high_band.to_numpy(dtype="float64")
                for family_code, family_name in base.FAMILY_MAP.items():
                    for entry_buffer in base.ENTRY_BUFFERS:
                        for exit_ratio in base.EXIT_RATIOS:
                            metric_values = base.simulate_metrics(
                                close=close,
                                close_ret=session.close_ret,
                                day_codes=session.day_codes,
                                day_year_codes=session.day_year_codes,
                                session_start=session.session_start,
                                session_end=session.session_end,
                                crsi=crsi_np,
                                low_band=low_np,
                                high_band=high_np,
                                family_code=family_code,
                                entry_buffer=entry_buffer,
                                exit_ratio=exit_ratio,
                                cost_rate=base.COST_BPS_PER_SIDE / 10000.0,
                            )
                            configs.append(
                                {
                                    "timeframe_minutes": timeframe,
                                    "domcycle": domcycle,
                                    "family": family_name,
                                    "leveling": leveling,
                                    "entry_buffer": entry_buffer,
                                    "exit_ratio": exit_ratio,
                                    "final_equity": float(base.INITIAL_EQUITY * metric_values[0]),
                                    "total_return_pct": float(metric_values[1]),
                                    "max_drawdown_pct": float(metric_values[2]),
                                    "sharpe": float(metric_values[3]),
                                    "profit_factor": float(metric_values[4]),
                                    "trade_count": int(metric_values[5]),
                                    "win_rate_pct": float(metric_values[6]),
                                    "avg_trade_return_pct": float(metric_values[7]),
                                    "avg_holding_bars": float(metric_values[10]),
                                    "long_trade_count": int(metric_values[11]),
                                    "short_trade_count": int(metric_values[12]),
                                    "positive_days_pct": float(metric_values[15]),
                                    "positive_years": int(metric_values[16]),
                                    "worst_year_return_pct": float(metric_values[17]),
                                    "best_year_return_pct": float(metric_values[18]),
                                    "avg_low_band": float(metric_values[19]),
                                    "avg_high_band": float(metric_values[20]),
                                    "avg_band_width": float(metric_values[21]),
                                    "avg_long_entry_level": float(metric_values[22]),
                                    "avg_long_exit_level": float(metric_values[23]),
                                    "avg_short_entry_level": float(metric_values[24]),
                                    "avg_short_exit_level": float(metric_values[25]),
                                }
                            )
            domcycle_df = pd.DataFrame(configs)
            best_row = base.choose_timeframe_winner(domcycle_df)
            timeframe_rows.append(best_row.to_dict())

        timeframe_df = pd.DataFrame(timeframe_rows).sort_values(
            ["total_return_pct", "sharpe", "profit_factor"],
            ascending=[False, False, False],
        ).reset_index(drop=True)
        timeframe_df["rank_in_timeframe"] = range(1, len(timeframe_df) + 1)
        top_tables[timeframe] = timeframe_df.head(5).copy()
        best_rows.append(base.choose_timeframe_winner(timeframe_df).to_dict())

        if OUT_METRICS.exists():
            mode = "a"
            header = False
        else:
            mode = "w"
            header = True
        timeframe_df.to_csv(OUT_METRICS, mode=mode, header=header, index=False)

    winners = pd.DataFrame(best_rows).sort_values("timeframe_minutes").reset_index(drop=True)
    winners.to_csv(OUT_WINNERS, index=False)

    lines = [
        "# QQQ cRSI Dominant Cycle Grid Report",
        "",
        "This report runs a dedicated dominant-cycle grid while re-optimizing the other cRSI settings inside each cycle-length bucket.",
        "",
        f"- Dominant cycle values tested: `{DCL_VALUES[0]}` through `{DCL_VALUES[-1]}` in steps of `2`.",
        f"- Other settings re-optimized inside each dominant-cycle bucket: `leveling {base.LEVELINGS}`, `entry buffer {base.ENTRY_BUFFERS}`, `exit ratio {base.EXIT_RATIOS}`, families `{tuple(base.FAMILY_MAP.values())}`.",
        "",
        "| Timeframe | Best domcycle | Family | Leveling | Entry buffer | Exit ratio | Return | Max DD | Sharpe | PF | Trades |",
        "| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]

    for row in winners.itertuples():
        lines.append(
            f"| {int(row.timeframe_minutes)}m | {int(row.domcycle)} | {row.family} | {row.leveling:.1f} | "
            f"{row.entry_buffer:.1f} | {row.exit_ratio:.1f} | {row.total_return_pct:.2f}% | "
            f"{row.max_drawdown_pct:.2f}% | {row.sharpe:.2f} | {row.profit_factor:.2f} | {int(row.trade_count)} |"
        )

    lines += ["", "## Top 5 Dominant Cycles By Timeframe", ""]
    for timeframe in base.TIMEFRAMES:
        lines.append(f"### {timeframe}m")
        lines.append("")
        lines.append("| Rank | Domcycle | Family | Return | Max DD | Sharpe | PF |")
        lines.append("| ---: | ---: | --- | ---: | ---: | ---: | ---: |")
        table = top_tables[timeframe]
        for row in table.itertuples():
            lines.append(
                f"| {int(row.rank_in_timeframe)} | {int(row.domcycle)} | {row.family} | "
                f"{row.total_return_pct:.2f}% | {row.max_drawdown_pct:.2f}% | {row.sharpe:.2f} | {row.profit_factor:.2f} |"
            )
        lines.append("")

    OUT_REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    if OUT_METRICS.exists():
        OUT_METRICS.unlink()
    main()
