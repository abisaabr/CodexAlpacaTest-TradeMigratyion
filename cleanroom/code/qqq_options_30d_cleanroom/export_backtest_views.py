from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


def step_label(step: int) -> str:
    sign = "p" if step >= 0 else "n"
    return f"{sign}{abs(int(step)):02d}"


def slot_label(dte: int, option_type: str, strike_step_distance: int) -> str:
    return f"dte{int(dte):02d}_{option_type}_step_{step_label(int(strike_step_distance))}"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Export dense and wide backtest views from the QQQ options clean-room output.")
    parser.add_argument("--output-dir", default="output")
    parser.add_argument("--dense-csv-name", default="qqq_option_1min_dense.csv")
    parser.add_argument("--wide-csv-name", default="qqq_option_1min_wide_backtest.csv")
    parser.add_argument("--wide-parquet-name", default="qqq_option_1min_wide_backtest.parquet")
    parser.add_argument("--slot-map-name", default="qqq_option_slot_map.csv")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    output_dir = Path(args.output_dir).resolve()

    dense_path = output_dir / "qqq_option_1min_dense.parquet"
    underlying_path = output_dir / "qqq_underlying_1min.parquet"
    if not dense_path.exists():
        raise FileNotFoundError(f"missing dense panel: {dense_path}")
    if not underlying_path.exists():
        raise FileNotFoundError(f"missing underlying bars: {underlying_path}")

    dense = pd.read_parquet(dense_path).copy()
    underlying = pd.read_parquet(underlying_path).copy()

    dense["timestamp_et"] = pd.to_datetime(dense["timestamp_et"])
    dense["timestamp"] = pd.to_datetime(dense["timestamp"], utc=True)
    dense["trade_date"] = pd.to_datetime(dense["trade_date"]).dt.date
    dense["expiration_date"] = pd.to_datetime(dense["expiration_date"]).dt.date
    dense["slot"] = [
        slot_label(dte=row.dte, option_type=row.option_type, strike_step_distance=row.strike_step_distance)
        for row in dense.itertuples(index=False)
    ]

    dense_csv = dense.copy()
    dense_csv["timestamp_et"] = dense_csv["timestamp_et"].astype(str)
    dense_csv["timestamp"] = dense_csv["timestamp"].astype(str)
    dense_csv["trade_date"] = dense_csv["trade_date"].astype(str)
    dense_csv["expiration_date"] = dense_csv["expiration_date"].astype(str)
    dense_csv.to_csv(output_dir / args.dense_csv_name, index=False)

    slot_map = (
        dense[
            [
                "trade_date",
                "slot",
                "symbol",
                "expiration_date",
                "dte",
                "option_type",
                "strike_price",
                "strike_step_distance",
                "spot_reference",
                "session_has_any_trade",
            ]
        ]
        .drop_duplicates()
        .sort_values(["trade_date", "dte", "option_type", "strike_step_distance", "symbol"])
        .reset_index(drop=True)
    )
    slot_map["trade_date"] = slot_map["trade_date"].astype(str)
    slot_map["expiration_date"] = slot_map["expiration_date"].astype(str)
    slot_map.to_csv(output_dir / args.slot_map_name, index=False)

    features = ["close", "volume", "trade_count", "vwap", "has_trade_bar", "is_synthetic_bar"]
    dense_sorted = dense.sort_values(["timestamp_et", "slot"])
    wide_parts: list[pd.DataFrame] = []
    for feature in features:
        pivot = dense_sorted.pivot(index="timestamp_et", columns="slot", values=feature)
        pivot.columns = [f"{col}_{feature}" for col in pivot.columns]
        wide_parts.append(pivot)

    wide = pd.concat(wide_parts, axis=1).sort_index(axis=1)
    wide = wide.reset_index()
    wide["timestamp_utc"] = wide["timestamp_et"].dt.tz_convert("UTC")
    wide["trade_date"] = wide["timestamp_et"].dt.date

    underlying["timestamp"] = pd.to_datetime(underlying["timestamp"], utc=True)
    if "symbol" in underlying.columns:
        underlying = underlying[underlying["symbol"] == "QQQ"].copy()
    if "S" in underlying.columns:
        underlying = underlying[underlying["S"] == "QQQ"].copy()
    underlying["timestamp_et"] = underlying["timestamp"].dt.tz_convert("America/New_York")
    underlying_small = underlying[
        ["timestamp_et", "open", "high", "low", "close", "volume", "trade_count", "vwap"]
    ].rename(
        columns={
            "open": "qqq_open",
            "high": "qqq_high",
            "low": "qqq_low",
            "close": "qqq_close",
            "volume": "qqq_volume",
            "trade_count": "qqq_trade_count",
            "vwap": "qqq_vwap",
        }
    )
    wide = wide.merge(underlying_small, on="timestamp_et", how="left")

    front_cols = ["timestamp_et", "timestamp_utc", "trade_date", "qqq_open", "qqq_high", "qqq_low", "qqq_close", "qqq_volume", "qqq_trade_count", "qqq_vwap"]
    remaining_cols = [col for col in wide.columns if col not in front_cols]
    wide = wide[front_cols + remaining_cols]

    wide_csv = wide.copy()
    wide_csv["timestamp_et"] = wide_csv["timestamp_et"].astype(str)
    wide_csv["timestamp_utc"] = wide_csv["timestamp_utc"].astype(str)
    wide_csv["trade_date"] = wide_csv["trade_date"].astype(str)
    wide_csv.to_csv(output_dir / args.wide_csv_name, index=False)
    wide.to_parquet(output_dir / args.wide_parquet_name, index=False)

    print(
        {
            "dense_csv": str(output_dir / args.dense_csv_name),
            "wide_csv": str(output_dir / args.wide_csv_name),
            "wide_parquet": str(output_dir / args.wide_parquet_name),
            "slot_map": str(output_dir / args.slot_map_name),
            "dense_rows": int(len(dense)),
            "wide_rows": int(len(wide)),
            "wide_columns": int(len(wide.columns)),
            "slot_count": int(slot_map["slot"].nunique()),
        }
    )


if __name__ == "__main__":
    main()
