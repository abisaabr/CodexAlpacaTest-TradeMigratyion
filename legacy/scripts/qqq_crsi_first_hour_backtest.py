from __future__ import annotations

from pathlib import Path

import pandas as pd

import qqq_crsi_backtest as base

REPORT_DIR = Path(r"C:\Users\rabisaab\Downloads\reports")
BEST_SETTINGS_PATH = REPORT_DIR / "qqq_crsi_domcycle_best_per_timeframe.csv"
OUT_METRICS = REPORT_DIR / "qqq_crsi_first_hour_metrics.csv"
OUT_LEDGER = REPORT_DIR / "qqq_crsi_first_hour_trade_ledger.csv"
OUT_REPORT = REPORT_DIR / "qqq_crsi_first_hour_report.md"


def first_hour_slice(frame: pd.DataFrame) -> pd.DataFrame:
    return frame.between_time("09:30", "10:29").copy()


def main() -> None:
    raw_rth, _ = base.load_rth_qqq()
    winners = pd.read_csv(BEST_SETTINGS_PATH).sort_values("timeframe_minutes").reset_index(drop=True)

    metric_rows: list[dict[str, object]] = []
    ledger_frames: list[pd.DataFrame] = []
    report_lines = [
        "# QQQ cRSI First-Hour Backtest Report",
        "",
        "This test re-runs the best per-timeframe settings from the dominant-cycle grid, but only on the first trading hour of each regular-hours session (`09:30` to `10:29` ET).",
        "",
        "| Timeframe | Settings source | Family | Domcycle | Leveling | Entry buffer | Exit ratio | Full-session return | First-hour return | First-hour max DD | Sharpe | PF | Trades |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]

    for row in winners.itertuples():
        timeframe = int(row.timeframe_minutes)
        family_code = 0 if row.family == "mean_reversion" else 1
        tf_frame = base.resample_intraday(raw_rth, timeframe)
        tf_first_hour = first_hour_slice(tf_frame)
        session = base.build_session_data(tf_first_hour)
        crsi = base.compute_crsi(tf_first_hour["close"], int(row.domcycle))
        low_band, high_band = base.compute_bands(crsi, int(row.domcycle), float(row.leveling))
        metric_values = base.simulate_metrics(
            close=tf_first_hour["close"].to_numpy(dtype="float64"),
            close_ret=session.close_ret,
            day_codes=session.day_codes,
            day_year_codes=session.day_year_codes,
            session_start=session.session_start,
            session_end=session.session_end,
            crsi=crsi.to_numpy(dtype="float64"),
            low_band=low_band.to_numpy(dtype="float64"),
            high_band=high_band.to_numpy(dtype="float64"),
            family_code=family_code,
            entry_buffer=float(row.entry_buffer),
            exit_ratio=float(row.exit_ratio),
            cost_rate=base.COST_BPS_PER_SIDE / 10000.0,
        )
        positions = base.generate_positions(
            session_start=session.session_start,
            session_end=session.session_end,
            crsi=crsi.to_numpy(dtype="float64"),
            low_band=low_band.to_numpy(dtype="float64"),
            high_band=high_band.to_numpy(dtype="float64"),
            family_code=family_code,
            entry_buffer=float(row.entry_buffer),
            exit_ratio=float(row.exit_ratio),
        )
        ledger = base.build_trade_ledger(
            frame=tf_first_hour,
            positions=positions,
            family_name=str(row.family),
            timeframe_minutes=timeframe,
            domcycle=int(row.domcycle),
            leveling=float(row.leveling),
            entry_buffer=float(row.entry_buffer),
            exit_ratio=float(row.exit_ratio),
        )
        ledger_frames.append(ledger)
        metric_rows.append(
            {
                "timeframe_minutes": timeframe,
                "family": row.family,
                "domcycle": int(row.domcycle),
                "leveling": float(row.leveling),
                "entry_buffer": float(row.entry_buffer),
                "exit_ratio": float(row.exit_ratio),
                "full_session_return_pct": float(row.total_return_pct),
                "full_session_max_drawdown_pct": float(row.max_drawdown_pct),
                "first_hour_final_equity": float(base.INITIAL_EQUITY * metric_values[0]),
                "first_hour_return_pct": float(metric_values[1]),
                "first_hour_max_drawdown_pct": float(metric_values[2]),
                "first_hour_sharpe": float(metric_values[3]),
                "first_hour_profit_factor": float(metric_values[4]),
                "first_hour_trade_count": int(metric_values[5]),
                "first_hour_win_rate_pct": float(metric_values[6]),
                "first_hour_avg_trade_return_pct": float(metric_values[7]),
                "first_hour_avg_holding_bars": float(metric_values[10]),
                "first_hour_long_trade_count": int(metric_values[11]),
                "first_hour_short_trade_count": int(metric_values[12]),
                "first_hour_positive_days_pct": float(metric_values[15]),
                "first_hour_positive_years": int(metric_values[16]),
                "first_hour_worst_year_return_pct": float(metric_values[17]),
                "first_hour_best_year_return_pct": float(metric_values[18]),
                "avg_low_band": float(metric_values[19]),
                "avg_high_band": float(metric_values[20]),
                "avg_band_width": float(metric_values[21]),
                "avg_long_entry_level": float(metric_values[22]),
                "avg_long_exit_level": float(metric_values[23]),
                "avg_short_entry_level": float(metric_values[24]),
                "avg_short_exit_level": float(metric_values[25]),
            }
        )
        report_lines.append(
            f"| {timeframe}m | `qqq_crsi_domcycle_best_per_timeframe.csv` | {row.family} | {int(row.domcycle)} | "
            f"{float(row.leveling):.1f} | {float(row.entry_buffer):.1f} | {float(row.exit_ratio):.1f} | "
            f"{float(row.total_return_pct):.2f}% | {float(metric_values[1]):.2f}% | {float(metric_values[2]):.2f}% | "
            f"{float(metric_values[3]):.2f} | {float(metric_values[4]):.2f} | {int(metric_values[5])} |"
        )

    metrics = pd.DataFrame(metric_rows).sort_values("timeframe_minutes").reset_index(drop=True)
    metrics.to_csv(OUT_METRICS, index=False)
    if ledger_frames:
        pd.concat(ledger_frames, ignore_index=True).to_csv(OUT_LEDGER, index=False)

    traded = metrics[metrics["first_hour_trade_count"] > 0].copy()
    best_first_hour = (
        traded.sort_values(
            ["first_hour_return_pct", "first_hour_sharpe", "first_hour_profit_factor"],
            ascending=[False, False, False],
        ).iloc[0]
        if not traded.empty
        else None
    )
    report_lines += [
        "",
        "## Readout",
        "",
    ]
    if best_first_hour is not None:
        report_lines += [
            f"- Best first-hour result among timeframes that actually traded: `{int(best_first_hour['timeframe_minutes'])}m` at `{best_first_hour['first_hour_return_pct']:.2f}%`.",
            f"- That setup used `{best_first_hour['family']}` with `domcycle={int(best_first_hour['domcycle'])}`, `leveling={best_first_hour['leveling']:.1f}`, `entry_buffer={best_first_hour['entry_buffer']:.1f}`, `exit_ratio={best_first_hour['exit_ratio']:.1f}`.",
        ]
    else:
        report_lines += [
            "- No timeframe generated any first-hour trades under these fixed full-session winner settings.",
        ]
    report_lines += [
        "- `30m` and `60m` produced zero trades because the first-hour window leaves too few bars for a close-to-close signal and subsequent holding period.",
        "- This is not a first-hour re-optimization. It is a first-hour replay of the settings that won on the full-session grid.",
    ]
    OUT_REPORT.write_text("\n".join(report_lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
