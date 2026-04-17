from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd


DEFAULT_OUTPUT_DIR = Path(__file__).resolve().parent / "output"
SPREAD_STRATEGIES = [
    "bear_put_spread_next_expiry",
    "bull_call_spread_next_expiry",
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Audit why cleanroom-derived IV/Greeks shift spread economics relative to the direct-Greeks pipeline."
    )
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--cleanroom-filtered-name", default="qqq_365d_balanced_overlap_filtered_candidates.csv")
    parser.add_argument("--direct-filtered-name", default="qqq_direct_greeks_balanced_overlap_filtered_candidates.csv")
    parser.add_argument("--cleanroom-universe-name", default="qqq_365d_option_daily_universe.parquet")
    parser.add_argument("--summary-name", default="qqq_cleanroom_spread_economics_audit_summary.json")
    parser.add_argument("--leg-presence-name", default="qqq_cleanroom_spread_leg_presence.csv")
    parser.add_argument("--matched-comparison-name", default="qqq_cleanroom_spread_matched_comparison.csv")
    parser.add_argument("--strategy-rollup-name", default="qqq_cleanroom_spread_strategy_rollup.csv")
    parser.add_argument("--report-name", default="qqq_cleanroom_spread_economics_audit_report.md")
    return parser


def load_candidates(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path)
    frame["trade_date"] = pd.to_datetime(frame["trade_date"]).dt.date
    frame["candidate_key"] = frame.apply(
        lambda row: f"{row['trade_date']}|{row['strategy']}|{int(row['entry_minute'])}|{int(row['dte'])}",
        axis=1,
    )
    return frame


def parse_legs(raw: str) -> list[dict[str, object]]:
    return list(json.loads(raw))


def build_leg_presence(direct: pd.DataFrame, cleanroom_universe: pd.DataFrame) -> pd.DataFrame:
    cleanroom_universe["trade_date"] = pd.to_datetime(cleanroom_universe["trade_date"]).dt.date
    available = set(
        zip(
            cleanroom_universe["trade_date"],
            cleanroom_universe["dte"].astype(int),
            cleanroom_universe["option_type"],
            cleanroom_universe["strike_price"].astype(float),
        )
    )

    rows: list[dict[str, object]] = []
    direct_spreads = direct[direct["strategy"].isin(SPREAD_STRATEGIES)].copy()
    for row in direct_spreads.itertuples(index=False):
        legs = parse_legs(str(row.legs_json))
        for leg_index, leg in enumerate(legs):
            rows.append(
                {
                    "candidate_key": row.candidate_key,
                    "trade_date": row.trade_date,
                    "strategy": row.strategy,
                    "dte": int(row.dte),
                    "leg_index": leg_index,
                    "side": str(leg["side"]),
                    "option_type": str(leg["option_type"]),
                    "strike_price": float(leg["strike_price"]),
                    "spot_price": float(leg["spot_price"]),
                    "delta": float(leg["delta"]),
                    "target_delta": float(leg["target_delta"]),
                    "delta_distance": abs(float(leg["delta"]) - float(leg["target_delta"])),
                    "present_in_cleanroom_universe": (
                        row.trade_date,
                        int(row.dte),
                        str(leg["option_type"]),
                        float(leg["strike_price"]),
                    )
                    in available,
                }
            )
    return pd.DataFrame(rows)


def build_matched_comparison(cleanroom: pd.DataFrame, direct: pd.DataFrame, leg_presence: pd.DataFrame) -> pd.DataFrame:
    clean_spreads = cleanroom[cleanroom["strategy"].isin(SPREAD_STRATEGIES)].copy()
    direct_spreads = direct[direct["strategy"].isin(SPREAD_STRATEGIES)].copy()
    merged = clean_spreads.merge(
        direct_spreads,
        on="candidate_key",
        how="inner",
        suffixes=("_cleanroom", "_direct"),
    )

    direct_short_presence = leg_presence[
        (leg_presence["leg_index"] == 1) & (leg_presence["side"] == "short")
    ][["candidate_key", "present_in_cleanroom_universe"]].rename(
        columns={"present_in_cleanroom_universe": "direct_short_present_in_cleanroom_universe"}
    )

    rows: list[dict[str, object]] = []
    for row in merged.itertuples(index=False):
        clean_legs = parse_legs(str(row.legs_json_cleanroom))
        direct_legs = parse_legs(str(row.legs_json_direct))
        rows.append(
            {
                "candidate_key": row.candidate_key,
                "trade_date": row.trade_date_cleanroom,
                "strategy": row.strategy_cleanroom,
                "dte": int(row.dte_cleanroom),
                "entry_minute": int(row.entry_minute_cleanroom),
                "entry_cash_diff": float(row.entry_cash_per_combo_cleanroom) - float(row.entry_cash_per_combo_direct),
                "exit_cash_diff": float(row.exit_cash_per_combo_cleanroom) - float(row.exit_cash_per_combo_direct),
                "net_pnl_diff": float(row.net_pnl_per_combo_cleanroom) - float(row.net_pnl_per_combo_direct),
                "long_symbol_same": clean_legs[0]["symbol"] == direct_legs[0]["symbol"],
                "short_symbol_same": clean_legs[1]["symbol"] == direct_legs[1]["symbol"],
                "same_both_legs": (
                    clean_legs[0]["symbol"] == direct_legs[0]["symbol"]
                    and clean_legs[1]["symbol"] == direct_legs[1]["symbol"]
                ),
                "clean_long_strike": float(clean_legs[0]["strike_price"]),
                "direct_long_strike": float(direct_legs[0]["strike_price"]),
                "clean_short_strike": float(clean_legs[1]["strike_price"]),
                "direct_short_strike": float(direct_legs[1]["strike_price"]),
                "clean_long_delta_distance": abs(float(clean_legs[0]["delta"]) - float(clean_legs[0]["target_delta"])),
                "direct_long_delta_distance": abs(float(direct_legs[0]["delta"]) - float(direct_legs[0]["target_delta"])),
                "clean_short_delta_distance": abs(float(clean_legs[1]["delta"]) - float(clean_legs[1]["target_delta"])),
                "direct_short_delta_distance": abs(float(direct_legs[1]["delta"]) - float(direct_legs[1]["target_delta"])),
                "clean_long_iv": float(clean_legs[0].get("implied_vol")) if clean_legs[0].get("implied_vol") is not None else None,
                "direct_long_iv": float(direct_legs[0].get("implied_vol")) if direct_legs[0].get("implied_vol") is not None else None,
                "clean_short_iv": float(clean_legs[1].get("implied_vol")) if clean_legs[1].get("implied_vol") is not None else None,
                "direct_short_iv": float(direct_legs[1].get("implied_vol")) if direct_legs[1].get("implied_vol") is not None else None,
            }
        )
    comparison = pd.DataFrame(rows)
    comparison = comparison.merge(direct_short_presence, on="candidate_key", how="left")
    return comparison.sort_values(["trade_date", "strategy", "entry_minute"]).reset_index(drop=True)


def build_strategy_rollup(leg_presence: pd.DataFrame, matched: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for strategy in SPREAD_STRATEGIES:
        presence_subset = leg_presence[leg_presence["strategy"] == strategy].copy()
        matched_subset = matched[matched["strategy"] == strategy].copy()
        if matched_subset.empty:
            continue

        def pct(series: pd.Series) -> float:
            return float(series.mean() * 100.0) if len(series) else 0.0

        presence_summary = (
            presence_subset.groupby(["leg_index", "side"], as_index=False)["present_in_cleanroom_universe"]
            .mean()
            .rename(columns={"present_in_cleanroom_universe": "presence_rate"})
        )
        long_presence = presence_summary[
            (presence_summary["leg_index"] == 0) & (presence_summary["side"] == "long")
        ]["presence_rate"]
        short_presence = presence_summary[
            (presence_summary["leg_index"] == 1) & (presence_summary["side"] == "short")
        ]["presence_rate"]

        matched_same_both = matched_subset[matched_subset["same_both_legs"]]
        matched_diff_any = matched_subset[~matched_subset["same_both_legs"]]
        short_missing = matched_subset[~matched_subset["direct_short_present_in_cleanroom_universe"]]
        short_present = matched_subset[matched_subset["direct_short_present_in_cleanroom_universe"]]

        rows.append(
            {
                "strategy": strategy,
                "matched_trade_count": int(len(matched_subset)),
                "direct_long_presence_rate_pct": round(float(long_presence.iloc[0] * 100.0) if not long_presence.empty else 0.0, 2),
                "direct_short_presence_rate_pct": round(float(short_presence.iloc[0] * 100.0) if not short_presence.empty else 0.0, 2),
                "same_both_legs_rate_pct": round(pct(matched_subset["same_both_legs"]), 2),
                "long_symbol_same_rate_pct": round(pct(matched_subset["long_symbol_same"]), 2),
                "short_symbol_same_rate_pct": round(pct(matched_subset["short_symbol_same"]), 2),
                "clean_long_delta_distance_mean": round(float(matched_subset["clean_long_delta_distance"].mean()), 4),
                "direct_long_delta_distance_mean": round(float(matched_subset["direct_long_delta_distance"].mean()), 4),
                "clean_short_delta_distance_mean": round(float(matched_subset["clean_short_delta_distance"].mean()), 4),
                "direct_short_delta_distance_mean": round(float(matched_subset["direct_short_delta_distance"].mean()), 4),
                "same_both_legs_net_pnl_diff_mean": round(float(matched_same_both["net_pnl_diff"].mean()) if len(matched_same_both) else 0.0, 2),
                "same_both_legs_net_pnl_diff_mae": round(float(matched_same_both["net_pnl_diff"].abs().mean()) if len(matched_same_both) else 0.0, 2),
                "diff_any_leg_net_pnl_diff_mean": round(float(matched_diff_any["net_pnl_diff"].mean()) if len(matched_diff_any) else 0.0, 2),
                "diff_any_leg_net_pnl_diff_mae": round(float(matched_diff_any["net_pnl_diff"].abs().mean()) if len(matched_diff_any) else 0.0, 2),
                "short_missing_entry_cash_diff_mean": round(float(short_missing["entry_cash_diff"].mean()) if len(short_missing) else 0.0, 2),
                "short_missing_net_pnl_diff_mean": round(float(short_missing["net_pnl_diff"].mean()) if len(short_missing) else 0.0, 2),
                "short_present_entry_cash_diff_mean": round(float(short_present["entry_cash_diff"].mean()) if len(short_present) else 0.0, 2),
                "short_present_net_pnl_diff_mean": round(float(short_present["net_pnl_diff"].mean()) if len(short_present) else 0.0, 2),
            }
        )

    return pd.DataFrame(rows).sort_values("strategy").reset_index(drop=True)


def build_summary(strategy_rollup: pd.DataFrame, matched: pd.DataFrame) -> dict[str, object]:
    examples: dict[str, list[dict[str, object]]] = {}
    for strategy in SPREAD_STRATEGIES:
        subset = matched[matched["strategy"] == strategy].copy()
        subset = subset.reindex(subset["net_pnl_diff"].abs().sort_values(ascending=False).index)
        top_rows = subset.head(5)[
            [
                "trade_date",
                "candidate_key",
                "entry_cash_diff",
                "exit_cash_diff",
                "net_pnl_diff",
                "clean_long_strike",
                "direct_long_strike",
                "clean_short_strike",
                "direct_short_strike",
                "direct_short_present_in_cleanroom_universe",
            ]
        ].to_dict(orient="records")
        normalized_rows: list[dict[str, object]] = []
        for row in top_rows:
            normalized = dict(row)
            if normalized.get("trade_date") is not None:
                normalized["trade_date"] = str(normalized["trade_date"])
            normalized_rows.append(normalized)
        examples[strategy] = normalized_rows

    return {
        "headline": {
            "primary_driver": "cleanroom_universe_truncation",
            "secondary_driver": "residual_exit_pricing_drift",
        },
        "strategy_rollup": strategy_rollup.to_dict(orient="records"),
        "largest_divergence_examples": examples,
    }


def write_report(path: Path, summary: dict[str, object]) -> None:
    rollup = pd.DataFrame(summary["strategy_rollup"])
    lines: list[str] = []
    lines.append("# Cleanroom Spread Economics Audit")
    lines.append("")
    lines.append("- Scope: explain why cleanroom-derived IV/Greeks shift economics versus the direct-Greeks pipeline for the two next-expiry debit spreads.")
    lines.append("- Compared strategies: `bear_put_spread_next_expiry` and `bull_call_spread_next_expiry`.")
    lines.append("")
    lines.append("## Findings")
    lines.append("")
    for row in rollup.itertuples(index=False):
        lines.append(
            f"- `{row.strategy}`: direct short leg is present in the cleanroom universe only {row.direct_short_presence_rate_pct:.2f}% of the time, versus {row.direct_long_presence_rate_pct:.2f}% for the long leg."
        )
        lines.append(
            f"- `{row.strategy}`: when the direct short leg is missing, cleanroom short-leg delta distance rises to the forced-selection regime and average entry debit shifts by about ${row.short_missing_entry_cash_diff_mean:.2f} per combo."
        )
        lines.append(
            f"- `{row.strategy}`: when both spread legs match exactly, residual net-PnL drift is much smaller, with mean difference {row.same_both_legs_net_pnl_diff_mean:.2f} and MAE {row.same_both_legs_net_pnl_diff_mae:.2f}."
        )
    lines.append("")
    lines.append("## Read")
    lines.append("")
    lines.append("- Primary cause: the 365-day cleanroom dataset is a trimmed `ATM +/- 5 step` universe, so many direct pipeline short spread legs simply do not exist there.")
    lines.append("- Secondary cause: even when the same symbols match, cleanroom exit pricing still drifts modestly versus the direct path, but that effect is much smaller than the universe truncation effect.")
    lines.append("- Implication: the cleanroom spread results are not a fair like-for-like judgment of the spread sleeves until the cleanroom universe is widened or the deployment book is constrained to the same trimmed universe in both pipelines.")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = build_parser().parse_args()
    output_dir = Path(args.output_dir).resolve()

    cleanroom = load_candidates(output_dir / args.cleanroom_filtered_name)
    direct = load_candidates(output_dir / args.direct_filtered_name)
    cleanroom_universe = pd.read_parquet(output_dir / args.cleanroom_universe_name)

    leg_presence = build_leg_presence(direct=direct, cleanroom_universe=cleanroom_universe)
    matched = build_matched_comparison(cleanroom=cleanroom, direct=direct, leg_presence=leg_presence)
    strategy_rollup = build_strategy_rollup(leg_presence=leg_presence, matched=matched)
    summary = build_summary(strategy_rollup=strategy_rollup, matched=matched)

    leg_presence.to_csv(output_dir / args.leg_presence_name, index=False)
    matched.to_csv(output_dir / args.matched_comparison_name, index=False)
    strategy_rollup.to_csv(output_dir / args.strategy_rollup_name, index=False)
    (output_dir / args.summary_name).write_text(json.dumps(summary, indent=2), encoding="utf-8")
    write_report(path=output_dir / args.report_name, summary=summary)

    print(
        json.dumps(
            {
                "summary_json": str(output_dir / args.summary_name),
                "leg_presence_csv": str(output_dir / args.leg_presence_name),
                "matched_comparison_csv": str(output_dir / args.matched_comparison_name),
                "strategy_rollup_csv": str(output_dir / args.strategy_rollup_name),
                "report_md": str(output_dir / args.report_name),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
