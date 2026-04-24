from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from cleanroom.code.qqq_options_30d_cleanroom.build_gcp_research_data_readiness import build_payload


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_research_data_readiness_summarizes_real_bar_build(tmp_path: Path) -> None:
    build_name = "build"
    runner = tmp_path / "runner"
    stock_path = runner / "data" / "silver" / "historical" / build_name / "stock_bars" / "symbol=QQQ" / "chunk=QQQ" / "part.parquet"
    stock_path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(
        {
            "symbol": ["QQQ", "QQQ"],
            "timestamp": pd.to_datetime(["2026-04-21T13:30:00Z", "2026-04-21T13:31:00Z"], utc=True),
            "close": [100.0, 101.0],
        }
    ).to_parquet(stock_path, index=False)
    contract_path = runner / "data" / "silver" / "historical" / build_name / "option_contract_inventory" / "underlying=QQQ" / "chunk=1" / "part.parquet"
    contract_path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame({"symbol": ["QQQ1", "QQQ2"]}).to_parquet(contract_path, index=False)
    selected_path = runner / "data" / "silver" / "historical" / build_name / "selected_option_contracts" / "underlying=QQQ" / "trade_date=2026-04-21" / "part.parquet"
    selected_path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame({"symbol": ["QQQ1"]}).to_parquet(selected_path, index=False)
    _write_json(runner / "data" / "raw" / "manifests" / f"{build_name}.json", {"datasets": {"stock_bars": {"chunks": {"x": {"status": "completed"}}}}})
    _write_json(runner / "data" / "silver" / "stocks" / f"{build_name}.manifest.json", {"row_count": 2})
    sample_json = tmp_path / "sample.json"
    _write_json(sample_json, {"trade_count": 1, "net_pnl": -5.0, "expectancy": -5.0, "win_rate": 0.0})

    payload = build_payload(
        runner_repo_root=runner,
        build_name=build_name,
        sample_backtest_json=sample_json,
        report_dir=tmp_path,
        gcs_prefix="gs://example",
    )

    assert payload["status"] == "ready_for_real_bar_research_with_warnings"
    assert payload["stock_row_count"] == 2
    assert payload["option_contract_inventory_rows_by_underlying"] == {"QQQ": 2}
    assert payload["selected_contract_rows_by_underlying"] == {"QQQ": 1}
    assert any(issue["code"] == "negative_sample_backtest_expectancy" for issue in payload["issues"])
