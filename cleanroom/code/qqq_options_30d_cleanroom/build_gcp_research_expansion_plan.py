from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[2]
DEFAULT_REPORT_DIR = REPO_ROOT / "docs" / "gcp_foundation"
DEFAULT_WAVE_MANIFEST_JSON = DEFAULT_REPORT_DIR / "gcp_research_wave_manifest.json"
DEFAULT_DATA_GCS_PREFIX = "gs://codexalpaca-data-us"
DEFAULT_CONTROL_GCS_PREFIX = "gs://codexalpaca-control-us"

TARGET_INITIAL_CASH = 25_000
TARGET_STRATEGY_VARIANTS = 1_000
TARGET_TICKER_COUNT = 150

TICKER_UNIVERSE_150 = [
    "AAPL",
    "ABBV",
    "ABNB",
    "ABT",
    "ACN",
    "ADBE",
    "ADI",
    "ADP",
    "ALB",
    "AMAT",
    "AMD",
    "AMGN",
    "AMZN",
    "ANET",
    "ARKK",
    "ASML",
    "AVGO",
    "AXP",
    "BA",
    "BABA",
    "BAC",
    "BIDU",
    "BKNG",
    "BMY",
    "BX",
    "C",
    "CAT",
    "CHWY",
    "CL",
    "CMCSA",
    "COIN",
    "COP",
    "COST",
    "CRM",
    "CRWD",
    "CSCO",
    "CVS",
    "CVX",
    "DASH",
    "DD",
    "DE",
    "DIA",
    "DIS",
    "DKNG",
    "DOCU",
    "DOW",
    "EA",
    "EBAY",
    "EEM",
    "EFA",
    "EMR",
    "ENPH",
    "EWZ",
    "F",
    "FCX",
    "FDX",
    "FXI",
    "GE",
    "GILD",
    "GLD",
    "GM",
    "GOOG",
    "GOOGL",
    "GS",
    "HD",
    "HON",
    "HOOD",
    "IBM",
    "INTC",
    "IWM",
    "JETS",
    "JNJ",
    "JPM",
    "KO",
    "KRE",
    "LOW",
    "LULU",
    "LYFT",
    "MA",
    "MARA",
    "MCD",
    "MDT",
    "META",
    "MRK",
    "MRNA",
    "MS",
    "MSFT",
    "MU",
    "NFLX",
    "NIO",
    "NKE",
    "NOW",
    "NVDA",
    "ORCL",
    "PANW",
    "PFE",
    "PG",
    "PLTR",
    "PYPL",
    "QCOM",
    "QQQ",
    "RBLX",
    "RIOT",
    "ROKU",
    "SBUX",
    "SHOP",
    "SLV",
    "SMCI",
    "SNAP",
    "SNOW",
    "SOFI",
    "SPY",
    "SQ",
    "T",
    "TGT",
    "TLT",
    "TNA",
    "TQQQ",
    "TSLA",
    "TSM",
    "U",
    "UAL",
    "UBER",
    "UNG",
    "UNH",
    "UPS",
    "USO",
    "V",
    "VIXY",
    "VLO",
    "VWO",
    "VXX",
    "WBA",
    "WFC",
    "WMT",
    "X",
    "XBI",
    "XHB",
    "XLC",
    "XLE",
    "XLF",
    "XLI",
    "XLK",
    "XLP",
    "XLU",
    "XLV",
    "XLY",
    "XOM",
    "XOP",
    "ZM",
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build the governed 150-ticker / 1000+ strategy research expansion plan."
    )
    parser.add_argument("--wave-manifest-json", default=str(DEFAULT_WAVE_MANIFEST_JSON))
    parser.add_argument("--report-dir", default=str(DEFAULT_REPORT_DIR))
    parser.add_argument("--data-gcs-prefix", default=DEFAULT_DATA_GCS_PREFIX)
    parser.add_argument("--control-gcs-prefix", default=DEFAULT_CONTROL_GCS_PREFIX)
    return parser


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    return payload if isinstance(payload, dict) else {}


def _dedupe(values: list[str]) -> list[str]:
    seen = set()
    output = []
    for value in values:
        ticker = value.upper().strip()
        if ticker and ticker not in seen:
            output.append(ticker)
            seen.add(ticker)
    return output


def _ticker_buckets(tickers: list[str], bucket_count: int = 10) -> list[dict[str, Any]]:
    buckets = []
    bucket_size = max(1, (len(tickers) + bucket_count - 1) // bucket_count)
    for index in range(0, len(tickers), bucket_size):
        bucket_tickers = tickers[index : index + bucket_size]
        buckets.append(
            {
                "bucket_id": f"ticker_bucket_{len(buckets) + 1:02d}",
                "ticker_count": len(bucket_tickers),
                "tickers": bucket_tickers,
            }
        )
    return buckets


def build_payload(
    *,
    wave_manifest_json: Path,
    report_dir: Path,
    data_gcs_prefix: str,
    control_gcs_prefix: str,
) -> dict[str, Any]:
    wave = _read_json(wave_manifest_json)
    tickers = _dedupe(TICKER_UNIVERSE_150)
    variant_count = int(wave.get("variant_count") or 0)
    issues: list[dict[str, str]] = []
    if len(tickers) != TARGET_TICKER_COUNT:
        issues.append(
            {
                "severity": "error",
                "code": "ticker_universe_count_mismatch",
                "message": f"Expected {TARGET_TICKER_COUNT} tickers; observed {len(tickers)}.",
            }
        )
    if variant_count < TARGET_STRATEGY_VARIANTS:
        issues.append(
            {
                "severity": "error",
                "code": "strategy_variant_count_below_target",
                "message": f"Need at least {TARGET_STRATEGY_VARIANTS} variants; observed {variant_count}.",
            }
        )
    if str(wave.get("status") or "") != "ready_for_research_only_wave":
        issues.append(
            {
                "severity": "error",
                "code": "research_wave_not_ready",
                "message": "The strategy wave manifest is not ready for research-only execution.",
            }
        )

    status = "ready_for_parallel_data_and_strategy_expansion"
    if any(issue["severity"] == "error" for issue in issues):
        status = "blocked_research_expansion_plan"

    return {
        "generated_at": datetime.now().astimezone().isoformat(),
        "status": status,
        "report_dir": str(report_dir),
        "wave_manifest_json": str(wave_manifest_json),
        "target_initial_cash": TARGET_INITIAL_CASH,
        "target_strategy_variants": TARGET_STRATEGY_VARIANTS,
        "observed_strategy_variants": variant_count,
        "observed_wave_id": wave.get("wave_id"),
        "target_ticker_count": TARGET_TICKER_COUNT,
        "ticker_count": len(tickers),
        "ticker_universe": tickers,
        "ticker_buckets": _ticker_buckets(tickers),
        "broker_facing": False,
        "live_manifest_effect": "none",
        "risk_policy_effect": "none",
        "data_gcs_layout": {
            "raw": f"{data_gcs_prefix}/raw/",
            "curated": f"{data_gcs_prefix}/curated/",
            "derived": f"{data_gcs_prefix}/derived/",
            "reports": f"{data_gcs_prefix}/reports/",
        },
        "control_gcs_layout": {
            "research_manifests": f"{control_gcs_prefix}/research_manifests/",
            "research_results": f"{control_gcs_prefix}/research_results/",
            "research_scorecards": f"{control_gcs_prefix}/research_scorecards/",
            "strategy_registry": f"{control_gcs_prefix}/strategy_registry/",
            "promotion_packets": f"{control_gcs_prefix}/promotion_packets/",
        },
        "search_lanes": [
            {
                "lane": "smoke",
                "purpose": "Reject broken/no-trade/pathological variants cheaply.",
                "method": "Run all variants on compact data windows before expensive option-aware testing.",
            },
            {
                "lane": "coarse_discovery",
                "purpose": "Find broad edge neighborhoods across tickers and regimes.",
                "method": "Use low-discrepancy or Latin-hypercube-like parameter coverage instead of dense grids.",
            },
            {
                "lane": "successive_halving",
                "purpose": "Spend compute on winners without hiding early losers.",
                "method": "Advance only candidates with enough trades, positive after-cost expectancy, and sane drawdown.",
            },
            {
                "lane": "local_refinement",
                "purpose": "Promote stable neighborhoods, not one lucky parameter point.",
                "method": "Search adjacent stops, targets, timing windows, liquidity gates, and DTE choices around survivors.",
            },
            {
                "lane": "walk_forward_stress",
                "purpose": "Protect against overfit and fragile market-regime dependence.",
                "method": "Require train/test or rolling splits plus slippage, fee, and fill-coverage stress.",
            },
        ],
        "promotion_contract": {
            "allowed_transition": "research_only_to_governed_validation_candidate",
            "not_allowed": [
                "live_manifest_change",
                "risk_policy_change",
                "broker_facing_activation",
                "profile_unlock",
            ],
            "required_to_promote": [
                "positive after-cost out-of-sample result",
                "enough completed trades or option fills",
                "fee and slippage stress survival",
                "single-day PnL concentration <= 35%",
                "stable adjacent parameter neighborhood",
                "complete strategy metadata and reproducible code/data refs",
                "loser taxonomy without repeated unresolved structural defect",
            ],
        },
        "execution_plan": [
            "Build/publish the 150-ticker raw and curated data manifest.",
            "Run current 2070-variant 25k-account smoke on existing 5-symbol data.",
            "Scale to 150 tickers only after data-quality verdicts are clean enough.",
            "Shard strategy x ticker x parameter blocks into resumable GCP Batch jobs.",
            "Reduce results into a single evidence ledger and promotion packet.",
        ],
        "issues": issues,
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "# GCP Research Expansion Plan",
        "",
        f"- Generated at: `{payload['generated_at']}`",
        f"- Status: `{payload['status']}`",
        f"- Target initial cash: `${payload['target_initial_cash']:,}`",
        f"- Observed strategy variants: `{payload['observed_strategy_variants']}`",
        f"- Target ticker count: `{payload['target_ticker_count']}`",
        f"- Ticker count: `{payload['ticker_count']}`",
        f"- Broker facing: `{payload['broker_facing']}`",
        f"- Live manifest effect: `{payload['live_manifest_effect']}`",
        f"- Risk policy effect: `{payload['risk_policy_effect']}`",
        "",
        "## Search Lanes",
        "",
    ]
    for lane in payload["search_lanes"]:
        lines.append(f"- `{lane['lane']}`: {lane['purpose']} {lane['method']}")
    lines.extend(["", "## Ticker Buckets", ""])
    for bucket in payload["ticker_buckets"]:
        lines.append(
            f"- `{bucket['bucket_id']}` count `{bucket['ticker_count']}`: "
            + ", ".join(bucket["tickers"])
        )
    lines.extend(["", "## Promotion Contract", ""])
    contract = payload["promotion_contract"]
    lines.append(f"- Allowed transition: `{contract['allowed_transition']}`")
    for item in contract["required_to_promote"]:
        lines.append(f"- Required: {item}")
    lines.extend(["", "## Execution Plan", ""])
    for step in payload["execution_plan"]:
        lines.append(f"- {step}")
    if payload["issues"]:
        lines.extend(["", "## Issues", ""])
        for issue in payload["issues"]:
            lines.append(f"- `{issue['severity']}` `{issue['code']}`: {issue['message']}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = build_parser().parse_args()
    report_dir = Path(args.report_dir)
    payload = build_payload(
        wave_manifest_json=Path(args.wave_manifest_json),
        report_dir=report_dir,
        data_gcs_prefix=args.data_gcs_prefix,
        control_gcs_prefix=args.control_gcs_prefix,
    )
    write_json(report_dir / "gcp_research_expansion_plan.json", payload)
    write_markdown(report_dir / "gcp_research_expansion_plan.md", payload)
    write_markdown(report_dir / "gcp_research_expansion_plan_handoff.md", payload)
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
