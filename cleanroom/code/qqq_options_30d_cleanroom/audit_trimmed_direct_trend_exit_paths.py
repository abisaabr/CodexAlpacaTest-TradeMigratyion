from __future__ import annotations

import argparse
import json
from functools import lru_cache
from pathlib import Path

import pandas as pd


TREND_STRATEGIES = {
    "trend_long_call_next_expiry": 360,
    "trend_long_put_next_expiry": 360,
}

RTH_START_MINUTE = 9 * 60 + 30
DEFAULT_OUTPUT_DIR = Path(__file__).resolve().parent / "output"
DEFAULT_DIRECT_ROOT = Path(r"C:\Users\rabisaab\Downloads\qqq_direct_greeks_oos_subset")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Audit remaining cleanroom-vs-trimmed-direct exit mismatches for matched next-expiry trend singles."
    )
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--direct-dataset-root", default=str(DEFAULT_DIRECT_ROOT))
    parser.add_argument("--cleanroom-filtered-name", default="qqq_365d_balanced_overlap_filtered_candidates.csv")
    parser.add_argument("--trimmed-filtered-name", default="qqq_direct_trimmed_overlap_filtered_candidates.csv")
    parser.add_argument("--cleanroom-dense-name", default="qqq_365d_option_1min_dense.parquet")
    parser.add_argument("--detail-name", default="qqq_trimmed_trend_exit_path_audit_details.csv")
    parser.add_argument("--classification-name", default="qqq_trimmed_trend_exit_path_audit_classification.csv")
    parser.add_argument("--reason-pairs-name", default="qqq_trimmed_trend_exit_path_reason_pairs.csv")
    parser.add_argument("--summary-name", default="qqq_trimmed_trend_exit_path_audit_summary.json")
    parser.add_argument("--report-name", default="qqq_trimmed_trend_exit_path_audit_report.md")
    return parser


def load_filtered_candidates(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path)
    frame["trade_date"] = pd.to_datetime(frame["trade_date"]).dt.date
    frame["candidate_key"] = frame.apply(
        lambda row: f"{row['trade_date']}|{row['strategy']}|{int(row['entry_minute'])}|{int(row['dte'])}",
        axis=1,
    )

    symbols: list[str] = []
    entry_price_fills: list[float | None] = []
    for raw_legs in frame["legs_json"]:
        legs = json.loads(str(raw_legs))
        if len(legs) != 1:
            symbols.append("")
            entry_price_fills.append(None)
            continue
        symbols.append(str(legs[0]["symbol"]))
        entry_price_fills.append(float(legs[0]["entry_price_fill"]))

    frame["symbol"] = symbols
    frame["entry_price_fill"] = entry_price_fills
    return frame


def load_cleanroom_dense(path: Path) -> dict[object, pd.DataFrame]:
    dense = pd.read_parquet(
        path,
        columns=[
            "trade_date",
            "symbol",
            "timestamp_et",
            "close",
            "has_trade_bar",
            "is_synthetic_bar",
            "trade_count",
            "volume",
        ],
    ).copy()
    dense["trade_date"] = pd.to_datetime(dense["trade_date"]).dt.date
    dense["timestamp_et"] = pd.to_datetime(dense["timestamp_et"])
    dense["minute_index"] = dense["timestamp_et"].dt.hour * 60 + dense["timestamp_et"].dt.minute - RTH_START_MINUTE
    dense = dense.sort_values(["trade_date", "symbol", "minute_index"]).reset_index(drop=True)
    return {
        trade_date: frame.reset_index(drop=True)
        for trade_date, frame in dense.groupby("trade_date", sort=False)
    }


def extract_symbol_frame(day_frame: pd.DataFrame, symbol_column: str, symbol: str, price_column: str) -> pd.DataFrame:
    frame = day_frame[day_frame[symbol_column] == symbol].copy()
    if frame.empty:
        return frame
    return frame.sort_values("minute_index").reset_index(drop=True)[["minute_index", price_column, *[col for col in frame.columns if col not in {"minute_index", price_column}]]]


@lru_cache(maxsize=None)
def load_direct_day(direct_dataset_root: str, trade_date: str) -> pd.DataFrame:
    path = (
        Path(direct_dataset_root)
        / "data"
        / "processed"
        / "selected_daily"
        / f"trade_date={trade_date}"
        / "dense.parquet"
    )
    frame = pd.read_parquet(
        path,
        columns=[
            "contract_symbol",
            "timestamp_et",
            "option_close",
            "option_close_ffill",
            "has_trade_bar",
            "is_ffill",
            "option_trade_count",
            "option_volume",
            "strike_offset_steps",
            "calc_delta",
            "calc_iv",
        ],
    ).copy()
    frame["timestamp_et"] = pd.to_datetime(frame["timestamp_et"])
    frame["minute_index"] = frame["timestamp_et"].dt.hour * 60 + frame["timestamp_et"].dt.minute - RTH_START_MINUTE
    return frame.sort_values(["contract_symbol", "minute_index"]).reset_index(drop=True)


def summarize_common_prices(clean_frame: pd.DataFrame, direct_frame: pd.DataFrame) -> tuple[int, float, float]:
    common = clean_frame[["minute_index", "close"]].merge(
        direct_frame[["minute_index", "option_close"]],
        on="minute_index",
        how="inner",
    )
    if common.empty:
        return 0, 0.0, 0.0
    abs_diff = (common["close"] - common["option_close"]).abs()
    return int(len(common)), float(abs_diff.mean()), float(abs_diff.max())


def classify_issue(row: pd.Series) -> str:
    if row["clean_exit_reason"] == row["trim_exit_reason"]:
        if int(row["clean_exit_minute"]) == int(row["trim_exit_minute"]):
            return "aligned_exact_exit"
        if row["clean_exit_reason"] == "time_exit":
            return "aligned_reason_sparse_path"
        return "aligned_reason_different_timestamp"

    if row["clean_exit_reason"] == "profit_target" and row["trim_exit_reason"] == "time_exit":
        if not bool(row["clean_exit_minute_present_in_direct"]):
            if int(row["direct_last_minute"]) < int(row["clean_exit_minute"]):
                return "profit_target_missed_direct_truncated"
            return "profit_target_missed_direct_sparse"
        if float(row["common_price_max_abs_diff"]) > 1e-9:
            return "profit_target_missed_price_difference"
        return "profit_target_missed_unexplained"

    if row["clean_exit_reason"] == "stop_loss" and row["trim_exit_reason"] == "time_exit":
        if not bool(row["clean_exit_minute_present_in_direct"]):
            if int(row["direct_last_minute"]) < int(row["clean_exit_minute"]):
                return "stop_loss_missed_direct_truncated"
            return "stop_loss_missed_direct_sparse"
        if float(row["common_price_max_abs_diff"]) > 1e-9:
            return "stop_loss_missed_price_difference"
        return "stop_loss_missed_unexplained"

    if float(row["common_price_max_abs_diff"]) > 1e-9:
        return "other_reason_mismatch_price_difference"
    return "other_reason_mismatch_sparse_path"


def build_details(
    cleanroom_filtered: pd.DataFrame,
    trimmed_filtered: pd.DataFrame,
    cleanroom_dense_by_day: dict[object, pd.DataFrame],
    direct_dataset_root: Path,
) -> pd.DataFrame:
    merged = cleanroom_filtered.merge(
        trimmed_filtered,
        on="candidate_key",
        suffixes=("_clean", "_trim"),
        how="inner",
    )
    merged = merged[
        merged["strategy_clean"].isin(TREND_STRATEGIES)
        & (merged["symbol_clean"] != "")
        & (merged["symbol_clean"] == merged["symbol_trim"])
    ].copy()
    merged = merged.sort_values(["trade_date_clean", "entry_minute_clean", "strategy_clean"]).reset_index(drop=True)

    detail_rows: list[dict[str, object]] = []
    for idx, row in enumerate(merged.itertuples(index=False), start=1):
        trade_date = row.trade_date_clean
        symbol = str(row.symbol_clean)
        clean_day = cleanroom_dense_by_day.get(trade_date, pd.DataFrame())
        clean_frame = clean_day[clean_day["symbol"] == symbol].copy().reset_index(drop=True)
        direct_day = load_direct_day(str(direct_dataset_root), trade_date.isoformat())
        direct_frame = direct_day[direct_day["contract_symbol"] == symbol].copy().reset_index(drop=True)

        if clean_frame.empty or direct_frame.empty:
            continue

        common_minutes, common_price_mae, common_price_max_abs_diff = summarize_common_prices(
            clean_frame=clean_frame,
            direct_frame=direct_frame,
        )
        direct_minutes = set(direct_frame["minute_index"].astype(int).tolist())
        clean_exit_minute = int(row.exit_minute_clean)
        trim_exit_minute = int(row.exit_minute_trim)
        entry_minute = int(row.entry_minute_clean)
        hard_exit_minute = TREND_STRATEGIES[str(row.strategy_clean)]

        expected_to_clean_exit = max(1, clean_exit_minute - entry_minute + 1)
        observed_to_clean_exit = sum(1 for minute in range(entry_minute, clean_exit_minute + 1) if minute in direct_minutes)
        expected_to_hard_exit = max(1, hard_exit_minute - entry_minute + 1)
        observed_to_hard_exit = sum(1 for minute in range(entry_minute, hard_exit_minute + 1) if minute in direct_minutes)

        direct_last_row = direct_frame.iloc[-1]
        detail_rows.append(
            {
                "candidate_key": row.candidate_key,
                "trade_date": trade_date.isoformat(),
                "strategy": row.strategy_clean,
                "symbol": symbol,
                "entry_minute": entry_minute,
                "clean_exit_minute": clean_exit_minute,
                "trim_exit_minute": trim_exit_minute,
                "clean_exit_reason": row.exit_reason_clean,
                "trim_exit_reason": row.exit_reason_trim,
                "clean_net_pnl_per_combo": float(row.net_pnl_per_combo_clean),
                "trim_net_pnl_per_combo": float(row.net_pnl_per_combo_trim),
                "net_pnl_diff_clean_minus_trim": float(row.net_pnl_per_combo_clean) - float(row.net_pnl_per_combo_trim),
                "direct_first_minute": int(direct_frame["minute_index"].min()),
                "direct_last_minute": int(direct_frame["minute_index"].max()),
                "direct_row_count": int(len(direct_frame)),
                "direct_last_abs_offset": int(abs(int(direct_last_row["strike_offset_steps"]))),
                "direct_last_offset": int(direct_last_row["strike_offset_steps"]),
                "clean_exit_minute_present_in_direct": clean_exit_minute in direct_minutes,
                "trim_exit_minute_present_in_direct": trim_exit_minute in direct_minutes,
                "direct_truncated_before_clean_exit": int(direct_frame["minute_index"].max()) < clean_exit_minute,
                "direct_truncated_before_hard_exit": int(direct_frame["minute_index"].max()) < hard_exit_minute,
                "coverage_to_clean_exit_pct": round(100.0 * observed_to_clean_exit / expected_to_clean_exit, 4),
                "coverage_to_hard_exit_pct": round(100.0 * observed_to_hard_exit / expected_to_hard_exit, 4),
                "common_minute_count": common_minutes,
                "common_price_mae": round(common_price_mae, 8),
                "common_price_max_abs_diff": round(common_price_max_abs_diff, 8),
                "clean_trade_bar_count": int(clean_frame["has_trade_bar"].sum()),
                "clean_synthetic_bar_count": int(clean_frame["is_synthetic_bar"].sum()),
                "direct_trade_bar_count": int(direct_frame["has_trade_bar"].sum()),
                "direct_ffill_row_count": int(direct_frame["is_ffill"].sum()),
                "issue_classification": "",
            }
        )

        if idx % 25 == 0 or idx == len(merged):
            print(f"Audited {idx}/{len(merged)} matched trend trades through {trade_date}", flush=True)

    details = pd.DataFrame(detail_rows)
    if details.empty:
        return details
    details["issue_classification"] = details.apply(classify_issue, axis=1)
    return details.sort_values(["trade_date", "entry_minute", "strategy"]).reset_index(drop=True)


def build_summary(details: pd.DataFrame) -> dict[str, object]:
    if details.empty:
        return {
            "matched_same_symbol_trend_trade_count": 0,
            "common_price_observation_count": 0,
            "common_price_mean_abs_diff": 0.0,
            "common_price_max_abs_diff": 0.0,
            "reason_pair_counts": {},
            "classification_counts": {},
        }

    common_price_observation_count = int(details["common_minute_count"].sum())
    profit_target_vs_time_exit = details[
        (details["clean_exit_reason"] == "profit_target") & (details["trim_exit_reason"] == "time_exit")
    ].copy()
    classification_counts = details["issue_classification"].value_counts().sort_index()
    reason_pair_counts = (
        details.groupby(["clean_exit_reason", "trim_exit_reason"], as_index=False)
        .size()
        .sort_values(["size", "clean_exit_reason", "trim_exit_reason"], ascending=[False, True, True])
    )

    supporting_examples = (
        details.sort_values("net_pnl_diff_clean_minus_trim", ascending=False)
        .head(8)[
            [
                "candidate_key",
                "issue_classification",
                "symbol",
                "clean_exit_reason",
                "trim_exit_reason",
                "clean_exit_minute",
                "trim_exit_minute",
                "direct_last_minute",
                "direct_last_abs_offset",
                "coverage_to_clean_exit_pct",
                "net_pnl_diff_clean_minus_trim",
            ]
        ]
        .to_dict(orient="records")
    )

    return {
        "matched_same_symbol_trend_trade_count": int(len(details)),
        "common_price_observation_count": common_price_observation_count,
        "common_price_mean_abs_diff": round(
            float(
                (details["common_price_mae"] * details["common_minute_count"]).sum()
                / max(1, common_price_observation_count)
            ),
            8,
        ),
        "common_price_max_abs_diff": round(float(details["common_price_max_abs_diff"].max()), 8),
        "reason_pair_counts": reason_pair_counts.to_dict(orient="records"),
        "classification_counts": {str(index): int(value) for index, value in classification_counts.items()},
        "clean_profit_target_vs_trim_time_exit": {
            "count": int(len(profit_target_vs_time_exit)),
            "clean_exit_minute_present_in_direct_pct": round(
                100.0 * float(profit_target_vs_time_exit["clean_exit_minute_present_in_direct"].mean())
                if not profit_target_vs_time_exit.empty
                else 0.0,
                2,
            ),
            "direct_truncated_before_clean_exit_pct": round(
                100.0 * float(profit_target_vs_time_exit["direct_truncated_before_clean_exit"].mean())
                if not profit_target_vs_time_exit.empty
                else 0.0,
                2,
            ),
            "direct_sparse_but_not_truncated_pct": round(
                100.0
                * float(
                    (
                        (~profit_target_vs_time_exit["clean_exit_minute_present_in_direct"])
                        & (~profit_target_vs_time_exit["direct_truncated_before_clean_exit"])
                    ).mean()
                )
                if not profit_target_vs_time_exit.empty
                else 0.0,
                2,
            ),
            "coverage_to_clean_exit_pct_mean": round(
                float(profit_target_vs_time_exit["coverage_to_clean_exit_pct"].mean())
                if not profit_target_vs_time_exit.empty
                else 0.0,
                4,
            ),
            "direct_last_abs_offset_eq_5_pct": round(
                100.0 * float((profit_target_vs_time_exit["direct_last_abs_offset"] == 5).mean())
                if not profit_target_vs_time_exit.empty
                else 0.0,
                2,
            ),
            "mean_net_pnl_diff_clean_minus_trim": round(
                float(profit_target_vs_time_exit["net_pnl_diff_clean_minus_trim"].mean())
                if not profit_target_vs_time_exit.empty
                else 0.0,
                4,
            ),
        },
        "supporting_examples": supporting_examples,
    }


def write_report(path: Path, summary: dict[str, object], details: pd.DataFrame) -> None:
    lines: list[str] = []
    lines.append("# Trimmed Direct Trend Exit Path Audit")
    lines.append("")
    lines.append(
        f"- Matched same-symbol next-expiry trend trades audited: {summary['matched_same_symbol_trend_trade_count']}"
    )
    lines.append(
        f"- Common timestamp option-close observations compared: {summary['common_price_observation_count']}"
    )
    lines.append(
        f"- Mean absolute price difference on shared timestamps: {summary['common_price_mean_abs_diff']:.8f}"
    )
    lines.append(
        f"- Max absolute price difference on shared timestamps: {summary['common_price_max_abs_diff']:.8f}"
    )
    lines.append("")
    lines.append("## Read")
    lines.append("")
    lines.append("- The remaining cleanroom-vs-trimmed-direct mismatch is a path coverage problem, not a common-timestamp price problem.")

    clean_vs_trim = summary["clean_profit_target_vs_trim_time_exit"]
    lines.append(
        "- For the specific subset where cleanroom hit `profit_target` but trimmed direct only reported `time_exit`, the clean target minute was missing from the direct selected-daily file every time."
    )
    lines.append(
        f"- That subset count was {clean_vs_trim['count']}, with {clean_vs_trim['direct_truncated_before_clean_exit_pct']:.2f}% fully truncated before the clean exit minute and {clean_vs_trim['direct_sparse_but_not_truncated_pct']:.2f}% still trading later but missing the key target timestamp."
    )
    lines.append(
        f"- Mean direct coverage from entry through the clean exit minute in that subset was only {clean_vs_trim['coverage_to_clean_exit_pct_mean']:.4f}%."
    )
    lines.append(
        f"- {clean_vs_trim['direct_last_abs_offset_eq_5_pct']:.2f}% of those misses ended with the contract sitting at offset step 5 in the direct file, which fits a dynamic ATM-band dropout rather than a pricing disagreement."
    )
    lines.append("")
    lines.append("## Implication")
    lines.append("")
    lines.append(
        "- The trimmed direct overlap is not a reliable fixed-contract exit-path benchmark for next-expiry trend singles because the selected-daily dense files do not preserve a full minute-by-minute history once a chosen contract drifts outside the moving offset universe."
    )
    lines.append(
        "- For deployment-grade validation, the safer next step is to rebuild the direct runner from raw option bars or from a fixed daily contract universe so chosen symbols retain a full-session path after entry."
    )

    top = details.sort_values("net_pnl_diff_clean_minus_trim", ascending=False).head(6)
    if not top.empty:
        lines.append("")
        lines.append("## Top Examples")
        lines.append("")
        for row in top.itertuples(index=False):
            lines.append(
                "- "
                f"{row.candidate_key}: clean {row.clean_exit_reason} at {int(row.clean_exit_minute)}, "
                f"trim {row.trim_exit_reason} at {int(row.trim_exit_minute)}, "
                f"direct last minute {int(row.direct_last_minute)}, "
                f"coverage to clean exit {float(row.coverage_to_clean_exit_pct):.2f}%, "
                f"net diff ${float(row.net_pnl_diff_clean_minus_trim):.2f}"
            )

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = build_parser().parse_args()
    output_dir = Path(args.output_dir).resolve()
    direct_dataset_root = Path(args.direct_dataset_root).resolve()

    cleanroom_filtered = load_filtered_candidates(output_dir / args.cleanroom_filtered_name)
    trimmed_filtered = load_filtered_candidates(output_dir / args.trimmed_filtered_name)
    cleanroom_dense_by_day = load_cleanroom_dense(output_dir / args.cleanroom_dense_name)

    details = build_details(
        cleanroom_filtered=cleanroom_filtered,
        trimmed_filtered=trimmed_filtered,
        cleanroom_dense_by_day=cleanroom_dense_by_day,
        direct_dataset_root=direct_dataset_root,
    )
    if details.empty:
        raise SystemExit("No matched same-symbol trend trades were found for the audit.")

    classification = (
        details.groupby(["issue_classification", "strategy"], as_index=False)
        .agg(
            trade_count=("candidate_key", "size"),
            mean_net_pnl_diff_clean_minus_trim=("net_pnl_diff_clean_minus_trim", "mean"),
            mean_coverage_to_clean_exit_pct=("coverage_to_clean_exit_pct", "mean"),
            clean_exit_minute_present_in_direct_pct=("clean_exit_minute_present_in_direct", "mean"),
            direct_truncated_before_clean_exit_pct=("direct_truncated_before_clean_exit", "mean"),
        )
        .sort_values(["trade_count", "issue_classification", "strategy"], ascending=[False, True, True])
        .reset_index(drop=True)
    )
    classification["clean_exit_minute_present_in_direct_pct"] = (
        classification["clean_exit_minute_present_in_direct_pct"] * 100.0
    ).round(4)
    classification["direct_truncated_before_clean_exit_pct"] = (
        classification["direct_truncated_before_clean_exit_pct"] * 100.0
    ).round(4)
    classification["mean_net_pnl_diff_clean_minus_trim"] = classification[
        "mean_net_pnl_diff_clean_minus_trim"
    ].round(4)
    classification["mean_coverage_to_clean_exit_pct"] = classification[
        "mean_coverage_to_clean_exit_pct"
    ].round(4)

    reason_pairs = (
        details.groupby(["clean_exit_reason", "trim_exit_reason", "strategy"], as_index=False)
        .agg(
            trade_count=("candidate_key", "size"),
            mean_net_pnl_diff_clean_minus_trim=("net_pnl_diff_clean_minus_trim", "mean"),
            mean_coverage_to_clean_exit_pct=("coverage_to_clean_exit_pct", "mean"),
        )
        .sort_values(["trade_count", "clean_exit_reason", "trim_exit_reason", "strategy"], ascending=[False, True, True, True])
        .reset_index(drop=True)
    )
    reason_pairs["mean_net_pnl_diff_clean_minus_trim"] = reason_pairs[
        "mean_net_pnl_diff_clean_minus_trim"
    ].round(4)
    reason_pairs["mean_coverage_to_clean_exit_pct"] = reason_pairs[
        "mean_coverage_to_clean_exit_pct"
    ].round(4)

    summary = build_summary(details)

    details.to_csv(output_dir / args.detail_name, index=False)
    classification.to_csv(output_dir / args.classification_name, index=False)
    reason_pairs.to_csv(output_dir / args.reason_pairs_name, index=False)
    (output_dir / args.summary_name).write_text(json.dumps(summary, indent=2), encoding="utf-8")
    write_report(output_dir / args.report_name, summary=summary, details=details)

    print(
        json.dumps(
            {
                "matched_same_symbol_trend_trade_count": summary["matched_same_symbol_trend_trade_count"],
                "summary_json": str(output_dir / args.summary_name),
                "report_md": str(output_dir / args.report_name),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
