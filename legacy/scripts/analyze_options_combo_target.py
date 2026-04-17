from __future__ import annotations

import argparse
import itertools
import math
from datetime import datetime
from pathlib import Path

import pandas as pd


ROOT = Path(r"C:\Users\rabisaab\Downloads")
TOURNAMENT_OUTPUTS = ROOT / "equity_strategy_tournament" / "outputs"
DEFAULT_RUNS = [
    TOURNAMENT_OUTPUTS / "options_optimization",
    TOURNAMENT_OUTPUTS / "options_recent_focus",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Analyze recent options backtest setup combinations against a target average daily PnL."
    )
    parser.add_argument("--target-daily-pnl", type=float, default=200.0)
    parser.add_argument("--min-trades", type=int, default=25)
    parser.add_argument("--min-days", type=int, default=10)
    parser.add_argument("--max-combo-size", type=int, default=3)
    parser.add_argument("--max-setups", type=int, default=12)
    parser.add_argument("--per-family", type=int, default=1)
    parser.add_argument("--run-dirs", nargs="*", default=[str(path) for path in DEFAULT_RUNS])
    return parser.parse_args()


def load_run_tables(run_dirs: list[str]) -> tuple[pd.DataFrame, pd.DataFrame]:
    summary_parts: list[pd.DataFrame] = []
    daily_parts: list[pd.DataFrame] = []
    for raw_path in run_dirs:
        run_path = Path(raw_path)
        parameter_summary_path = run_path / "parameter_summary.csv"
        per_day_path = run_path / "per_day_summary.csv"
        if not parameter_summary_path.exists() or not per_day_path.exists():
            continue
        parameter_summary = pd.read_csv(parameter_summary_path)
        parameter_summary["source_run"] = run_path.name
        per_day_summary = pd.read_csv(per_day_path)
        per_day_summary["source_run"] = run_path.name
        summary_parts.append(parameter_summary)
        daily_parts.append(per_day_summary)
    if not summary_parts or not daily_parts:
        raise FileNotFoundError("No usable parameter_summary.csv / per_day_summary.csv files were found in the requested run directories.")
    return pd.concat(summary_parts, ignore_index=True), pd.concat(daily_parts, ignore_index=True)


def to_numeric(frame: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    out = frame.copy()
    for column in columns:
        if column in out.columns:
            out[column] = pd.to_numeric(out[column], errors="coerce")
    return out


def choose_candidates(
    parameter_summary: pd.DataFrame,
    *,
    min_trades: int,
    min_days: int,
    max_setups: int,
    per_family: int,
) -> pd.DataFrame:
    numeric_columns = [
        "days_tested",
        "trade_count",
        "total_pnl",
        "pnl_per_day",
        "expectancy",
        "max_drawdown",
        "max_daily_loss_observed",
        "positive_day_ratio",
        "daily_pnl_std",
        "drawdown_adjusted_return",
    ]
    candidates = to_numeric(parameter_summary, numeric_columns)
    candidates = candidates.loc[
        (candidates["days_tested"] >= min_days)
        & (candidates["trade_count"] >= min_trades)
        & (candidates["pnl_per_day"] > 0)
        & (candidates["expectancy"] > 0)
    ].copy()
    if candidates.empty:
        return candidates
    candidates["family_key"] = (
        candidates["symbol"].astype(str)
        + "::"
        + candidates["strategy_name"].astype(str)
        + "::"
        + candidates["contract_target"].astype(str)
    )
    candidates["setup_label"] = (
        candidates["source_run"].astype(str)
        + " | "
        + candidates["symbol"].astype(str)
        + " | "
        + candidates["strategy_name"].astype(str)
        + " | "
        + candidates["contract_target"].astype(str)
    )
    candidates = candidates.sort_values(
        [
            "pnl_per_day",
            "drawdown_adjusted_return",
            "expectancy",
            "positive_day_ratio",
        ],
        ascending=[False, False, False, False],
    )
    candidates = candidates.groupby("family_key", group_keys=False).head(per_family)
    return candidates.head(max_setups).reset_index(drop=True)


def build_daily_matrix(per_day_summary: pd.DataFrame, setup_ids: list[str]) -> pd.DataFrame:
    daily = per_day_summary.loc[per_day_summary["setup_id"].isin(setup_ids)].copy()
    if daily.empty:
        raise ValueError("No per-day rows matched the selected candidate setup ids.")
    daily["trade_date"] = pd.to_datetime(daily["trade_date"], errors="coerce")
    daily["total_pnl"] = pd.to_numeric(daily["total_pnl"], errors="coerce").fillna(0.0)
    matrix = (
        daily.pivot_table(index="trade_date", columns="setup_id", values="total_pnl", aggfunc="sum", fill_value=0.0)
        .sort_index()
        .copy()
    )
    for setup_id in setup_ids:
        if setup_id not in matrix.columns:
            matrix[setup_id] = 0.0
    return matrix[setup_ids].copy()


def max_drawdown_from_series(series: pd.Series) -> float:
    equity_curve = series.cumsum()
    drawdown = equity_curve - equity_curve.cummax()
    return float(drawdown.min()) if not drawdown.empty else 0.0


def average_pairwise_correlation(matrix: pd.DataFrame, setup_ids: tuple[str, ...]) -> float:
    if len(setup_ids) < 2:
        return 0.0
    subset = matrix.loc[:, list(setup_ids)].copy()
    correlation = subset.corr()
    if correlation.empty:
        return 0.0
    values: list[float] = []
    ids = list(setup_ids)
    for left_index in range(len(ids)):
        for right_index in range(left_index + 1, len(ids)):
            value = correlation.loc[ids[left_index], ids[right_index]]
            if pd.notna(value):
                values.append(float(value))
    return float(sum(values) / len(values)) if values else 0.0


def analyze_combinations(
    candidates: pd.DataFrame,
    matrix: pd.DataFrame,
    *,
    target_daily_pnl: float,
    max_combo_size: int,
) -> pd.DataFrame:
    records: list[dict[str, object]] = []
    metadata = candidates.set_index("setup_id", drop=False)
    for combo_size in range(1, max_combo_size + 1):
        for setup_ids in itertools.combinations(candidates["setup_id"].tolist(), combo_size):
            pnl_series = matrix.loc[:, list(setup_ids)].sum(axis=1)
            avg_daily_pnl = float(pnl_series.mean())
            if avg_daily_pnl <= 0:
                uniform_scale = None
            else:
                uniform_scale = int(math.ceil(target_daily_pnl / avg_daily_pnl))
            max_drawdown = max_drawdown_from_series(pnl_series)
            worst_day = float(pnl_series.min()) if not pnl_series.empty else 0.0
            best_day = float(pnl_series.max()) if not pnl_series.empty else 0.0
            positive_day_ratio = float((pnl_series > 0).mean()) if not pnl_series.empty else 0.0
            target_hit_ratio = float((pnl_series >= target_daily_pnl).mean()) if not pnl_series.empty else 0.0
            avg_pairwise_corr = average_pairwise_correlation(matrix, setup_ids)
            labels = [str(metadata.loc[setup_id, "setup_label"]) for setup_id in setup_ids]
            records.append(
                {
                    "combo_size": combo_size,
                    "setup_ids": ";".join(setup_ids),
                    "setup_labels": " || ".join(labels),
                    "component_symbols": ";".join(sorted({str(metadata.loc[setup_id, 'symbol']) for setup_id in setup_ids})),
                    "component_strategies": ";".join(sorted({str(metadata.loc[setup_id, 'strategy_name']) for setup_id in setup_ids})),
                    "source_runs": ";".join(sorted({str(metadata.loc[setup_id, 'source_run']) for setup_id in setup_ids})),
                    "days_tested_common": int(len(pnl_series)),
                    "total_pnl": float(pnl_series.sum()),
                    "avg_daily_pnl": avg_daily_pnl,
                    "median_daily_pnl": float(pnl_series.median()),
                    "daily_pnl_std": float(pnl_series.std(ddof=0)) if len(pnl_series) else 0.0,
                    "positive_day_ratio": positive_day_ratio,
                    "max_drawdown": max_drawdown,
                    "worst_day_pnl": worst_day,
                    "best_day_pnl": best_day,
                    "target_hit_ratio_at_1x": target_hit_ratio,
                    "avg_pairwise_corr": avg_pairwise_corr,
                    "drawdown_adjusted_return": (avg_daily_pnl / abs(max_drawdown)) if max_drawdown < 0 else avg_daily_pnl,
                    "uniform_scale_to_target": uniform_scale or "",
                    "scaled_avg_daily_pnl": (avg_daily_pnl * uniform_scale) if uniform_scale else "",
                    "scaled_max_drawdown": (max_drawdown * uniform_scale) if uniform_scale else "",
                    "scaled_worst_day_pnl": (worst_day * uniform_scale) if uniform_scale else "",
                }
            )
    combos = pd.DataFrame(records)
    if combos.empty:
        return combos
    combos = combos.sort_values(
        [
            "avg_daily_pnl",
            "drawdown_adjusted_return",
            "positive_day_ratio",
            "avg_pairwise_corr",
        ],
        ascending=[False, False, False, True],
    ).reset_index(drop=True)
    return combos


def render_summary(
    *,
    target_daily_pnl: float,
    candidates: pd.DataFrame,
    combos: pd.DataFrame,
    output_dir: Path,
) -> str:
    lines = [
        "# Options Combo Target Analysis",
        "",
        f"Generated: {datetime.now().astimezone().isoformat()}",
        f"Target average daily PnL: `{target_daily_pnl:.2f}`",
        "",
        "## Candidate Setups",
    ]
    if candidates.empty:
        lines.append("- No positive-expectancy candidate setups cleared the minimum trade/day filters.")
    else:
        for row in candidates.itertuples(index=False):
            lines.append(
                "- "
                + f"`{row.setup_label}` | pnl/day `{row.pnl_per_day:.2f}` | expectancy `{row.expectancy:.2f}` | "
                + f"max drawdown `{row.max_drawdown:.2f}` | positive-day ratio `{row.positive_day_ratio:.2%}`"
            )
    lines.extend(["", "## Top Raw Combinations"])
    if combos.empty:
        lines.append("- No combinations were produced.")
    else:
        for row in combos.head(10).itertuples(index=False):
            scale_text = f"`{row.uniform_scale_to_target}`" if row.uniform_scale_to_target != "" else "`n/a`"
            lines.append(
                "- "
                + f"`{row.setup_labels}` | avg/day `{row.avg_daily_pnl:.2f}` | drawdown `{row.max_drawdown:.2f}` | "
                + f"positive-day ratio `{row.positive_day_ratio:.2%}` | scale-to-target `{scale_text}`"
            )
    lines.extend(["", "## Practical Read"])
    if combos.empty:
        lines.append("- There is no data-backed combo here that can even be framed as a serious path toward the target yet.")
    else:
        best = combos.iloc[0]
        if float(best["avg_daily_pnl"]) >= target_daily_pnl:
            lines.append("- At least one 1x combo clears the target on average over the sampled window.")
        else:
            lines.append(
                "- "
                + f"No 1x combo hit `{target_daily_pnl:.2f}` average daily PnL. The best observed 1x combo averaged "
                + f"`{float(best['avg_daily_pnl']):.2f}` per day."
            )
            if best["uniform_scale_to_target"] != "":
                lines.append(
                    "- "
                    + f"Reaching the target by simple scaling would need about `{int(best['uniform_scale_to_target'])}x` size, "
                    + f"which linearly projects drawdown toward `{float(best['scaled_max_drawdown']):.2f}` "
                    + f"and the worst observed day toward `{float(best['scaled_worst_day_pnl']):.2f}`."
                )
    lines.extend(
        [
            "",
            "## Files",
            f"- Candidate setups CSV: `{output_dir / 'candidate_setups.csv'}`",
            f"- Combination leaderboard CSV: `{output_dir / 'combo_leaderboard.csv'}`",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    args = parse_args()
    parameter_summary, per_day_summary = load_run_tables(args.run_dirs)
    candidates = choose_candidates(
        parameter_summary,
        min_trades=args.min_trades,
        min_days=args.min_days,
        max_setups=args.max_setups,
        per_family=args.per_family,
    )
    output_dir = ROOT / "reports" / f"options_combo_target_{datetime.now().astimezone().strftime('%Y%m%d_%H%M%S')}"
    output_dir.mkdir(parents=True, exist_ok=True)
    if candidates.empty:
        candidates.to_csv(output_dir / "candidate_setups.csv", index=False)
        pd.DataFrame().to_csv(output_dir / "combo_leaderboard.csv", index=False)
        summary_text = render_summary(
            target_daily_pnl=args.target_daily_pnl,
            candidates=candidates,
            combos=pd.DataFrame(),
            output_dir=output_dir,
        )
        (output_dir / "summary.md").write_text(summary_text, encoding="utf-8")
        print(f"output_dir={output_dir}")
        return 0
    matrix = build_daily_matrix(per_day_summary, candidates["setup_id"].tolist())
    combos = analyze_combinations(
        candidates,
        matrix,
        target_daily_pnl=args.target_daily_pnl,
        max_combo_size=args.max_combo_size,
    )
    candidates.to_csv(output_dir / "candidate_setups.csv", index=False)
    combos.to_csv(output_dir / "combo_leaderboard.csv", index=False)
    summary_text = render_summary(
        target_daily_pnl=args.target_daily_pnl,
        candidates=candidates,
        combos=combos,
        output_dir=output_dir,
    )
    (output_dir / "summary.md").write_text(summary_text, encoding="utf-8")
    print(f"output_dir={output_dir}")
    print(f"candidates={len(candidates)}")
    print(f"combos={len(combos)}")
    if not combos.empty:
        print(combos.head(10).to_string(index=False, max_colwidth=120))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
