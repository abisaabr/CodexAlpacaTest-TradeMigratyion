from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import yaml

from run_multiticker_cleanroom_portfolio import build_strategy_variants, build_timing_profiles


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Export approved cleanroom tournament winners into promoted_strategies.yaml for the live sync script."
    )
    parser.add_argument(
        "--research-dir",
        required=True,
        help="Tournament research directory containing per-ticker *_summary.json files.",
    )
    parser.add_argument(
        "--output-path",
        default=None,
        help="YAML output path. Defaults to <research-dir>/promoted_strategies.yaml.",
    )
    parser.add_argument(
        "--tickers",
        default="",
        help="Optional comma-separated ticker subset. Defaults to all available ticker summary files in the research dir.",
    )
    parser.add_argument(
        "--timing-profiles",
        default="all",
        help="Comma-separated timing profiles to allow in the export. Use 'all' to include every profile.",
    )
    parser.add_argument(
        "--strategy-set",
        default="auto",
        choices=("auto", "standard", "family_expansion", "down_choppy_only", "down_choppy_exhaustive"),
        help="Strategy universe to reconstruct. 'auto' reads strategy_set from master_summary.json when available.",
    )
    parser.add_argument(
        "--allow-missing-tickers",
        action="store_true",
        help="Do not fail if a requested ticker summary is missing.",
    )
    return parser


def _normalize_ticker_list(raw: str) -> list[str]:
    return [item.strip().lower() for item in raw.split(",") if item.strip()]


def _available_tickers(research_dir: Path) -> list[str]:
    tickers: list[str] = []
    for path in sorted(research_dir.glob("*_summary.json")):
        name = path.stem
        if name in {"prep_summary", "master_summary", "standalone_summary", "overnight_run_summary"}:
            continue
        if name.endswith("_summary"):
            ticker = name.removesuffix("_summary")
            if not (research_dir / f"{ticker}_promotion.json").exists():
                continue
            tickers.append(ticker)
    return tickers


def _load_summary(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Summary payload must be an object: {path}")
    return payload


def _detect_strategy_set(research_dir: Path, requested: str) -> str:
    if requested != "auto":
        return requested
    master_summary_path = research_dir / "master_summary.json"
    if not master_summary_path.exists():
        return "standard"
    payload = _load_summary(master_summary_path)
    strategy_set = payload.get("strategy_set")
    if strategy_set in {"standard", "family_expansion", "down_choppy_only", "down_choppy_exhaustive"}:
        return str(strategy_set)
    return "standard"


def _allowed_timing_profiles(raw: str) -> set[str]:
    all_profiles = {profile.name for profile in build_timing_profiles()}
    if raw.strip().lower() == "all":
        return all_profiles
    requested = {item.strip() for item in raw.split(",") if item.strip()}
    unknown = sorted(requested - all_profiles)
    if unknown:
        raise ValueError(f"Unknown timing profiles requested: {unknown}")
    return requested


def _strategy_payload(*, strategy, regime: str, alias_name: str | None = None) -> dict[str, object]:
    ticker, timing_profile, _ = str(strategy.name).split("__", 2)
    signal_name = str(strategy.signal_name).split("__", 1)[-1]
    description = str(strategy.description)
    if alias_name and alias_name != strategy.name:
        description = f"{description} [{regime}]"
    return {
        "name": alias_name or str(strategy.name),
        "underlying_symbol": ticker.upper(),
        "regime": regime,
        "family": str(strategy.family),
        "description": description,
        "dte_mode": str(strategy.dte_mode),
        "signal_name": signal_name,
        "timing_profile": timing_profile,
        "hard_exit_minute": int(strategy.hard_exit_minute),
        "risk_fraction": float(strategy.risk_fraction),
        "max_contracts": int(strategy.max_contracts),
        "profit_target_multiple": float(strategy.profit_target_multiple),
        "stop_loss_multiple": float(strategy.stop_loss_multiple),
        "legs": [
            {
                "option_type": str(leg.option_type),
                "side": str(leg.side),
                "target_delta": float(leg.target_delta),
                "min_abs_delta": float(leg.min_abs_delta),
                "max_abs_delta": float(leg.max_abs_delta),
            }
            for leg in strategy.legs
        ],
    }


def _promotion_rows(summary: dict[str, object]) -> list[tuple[str, str]]:
    promoted = summary.get("promoted")
    if not isinstance(promoted, dict):
        raise ValueError("Summary payload is missing a promoted config block.")
    rows: list[tuple[str, str]] = []
    for regime_key, regime in (
        ("selected_bull", "bull"),
        ("selected_bear", "bear"),
        ("selected_choppy", "choppy"),
    ):
        names = promoted.get(regime_key, [])
        if not isinstance(names, list):
            raise ValueError(f"Promoted block has invalid {regime_key} list.")
        for name in names:
            rows.append((regime, str(name)))
    return rows


def export_promoted_strategies(
    *,
    research_dir: Path,
    tickers: list[str],
    output_path: Path,
    allowed_profiles: set[str],
    allow_missing_tickers: bool,
    strategy_set: str,
) -> dict[str, object]:
    all_profiles = build_timing_profiles()
    strategies: list[dict[str, object]] = []
    used_names: set[str] = set()
    skipped: list[dict[str, object]] = []
    ticker_exports: list[dict[str, object]] = []

    for ticker in tickers:
        summary_path = research_dir / f"{ticker}_summary.json"
        if not summary_path.exists():
            if allow_missing_tickers:
                skipped.append(
                    {
                        "ticker": ticker.upper(),
                        "reason": "missing_summary",
                        "summary_path": str(summary_path),
                    }
                )
                continue
            raise FileNotFoundError(f"Ticker summary not found: {summary_path}")

        summary = _load_summary(summary_path)
        strategy_map = {
            strategy.name: strategy
            for strategy in build_strategy_variants(
                ticker,
                all_profiles,
                strategy_set=strategy_set,
            )
        }
        exported_names: list[str] = []
        per_ticker_skipped: list[dict[str, object]] = []
        seen_base_names: dict[str, str] = {}

        for regime, strategy_name in _promotion_rows(summary):
            strategy = strategy_map.get(strategy_name)
            if strategy is None:
                item = {
                    "ticker": ticker.upper(),
                    "strategy_name": strategy_name,
                    "regime": regime,
                    "reason": "missing_strategy_definition",
                }
                skipped.append(item)
                per_ticker_skipped.append(item)
                continue

            _, timing_profile, _ = str(strategy.name).split("__", 2)
            if timing_profile not in allowed_profiles:
                item = {
                    "ticker": ticker.upper(),
                    "strategy_name": strategy_name,
                    "regime": regime,
                    "reason": "unsupported_timing_profile",
                    "timing_profile": timing_profile,
                }
                skipped.append(item)
                per_ticker_skipped.append(item)
                continue

            alias_name: str | None = None
            if strategy_name in seen_base_names and seen_base_names[strategy_name] != regime:
                alias_name = f"{strategy_name}__{regime}"
            elif strategy_name in used_names:
                alias_name = f"{strategy_name}__{regime}"

            payload = _strategy_payload(strategy=strategy, regime=regime, alias_name=alias_name)
            used_names.add(str(payload["name"]))
            seen_base_names[strategy_name] = regime
            strategies.append(payload)
            exported_names.append(str(payload["name"]))

        promoted = summary.get("promoted", {})
        ticker_exports.append(
            {
                "ticker": ticker.upper(),
                "summary_path": str(summary_path),
                "regime_threshold_pct": float(promoted.get("regime_threshold_pct", 0.0)) if isinstance(promoted, dict) else None,
                "risk_cap": float(promoted.get("risk_cap", 0.0)) if isinstance(promoted, dict) else None,
                "exported_strategy_names": exported_names,
                "skipped": per_ticker_skipped,
            }
        )

    by_regime = Counter(str(strategy["regime"]) for strategy in strategies)
    by_family = Counter(str(strategy["family"]) for strategy in strategies)
    document = {
        "version": 1,
        "description": "Tournament-approved strategy export for scripts/sync_live_strategy_manifest.py.",
        "generated_at_et": datetime.now(ZoneInfo("America/New_York")).isoformat(),
        "source_research_dir": str(research_dir),
        "requested_tickers": [ticker.upper() for ticker in tickers],
        "strategy_set": strategy_set,
        "allowed_timing_profiles": sorted(allowed_profiles),
        "exported_strategy_count": len(strategies),
        "summary": {
            "by_regime": dict(sorted(by_regime.items())),
            "by_family": dict(sorted(by_family.items())),
        },
        "ticker_exports": ticker_exports,
        "skipped": skipped,
        "strategies": strategies,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(yaml.safe_dump(document, sort_keys=False), encoding="utf-8")
    return document


def main() -> None:
    args = build_parser().parse_args()
    research_dir = Path(args.research_dir).resolve()
    if not research_dir.exists():
        raise FileNotFoundError(f"Research dir not found: {research_dir}")
    tickers = _normalize_ticker_list(args.tickers) or _available_tickers(research_dir)
    if not tickers:
        raise SystemExit("No ticker summaries found to export.")
    strategy_set = _detect_strategy_set(research_dir, args.strategy_set)
    allowed_profiles = _allowed_timing_profiles(args.timing_profiles)
    output_path = Path(args.output_path).resolve() if args.output_path else (research_dir / "promoted_strategies.yaml")
    document = export_promoted_strategies(
        research_dir=research_dir,
        tickers=tickers,
        output_path=output_path,
        allowed_profiles=allowed_profiles,
        allow_missing_tickers=args.allow_missing_tickers,
        strategy_set=strategy_set,
    )
    print(f"output_path={output_path}")
    print(f"exported_strategy_count={document['exported_strategy_count']}")
    print("requested_tickers=" + ",".join(document["requested_tickers"]))
    print("strategy_set=" + str(document["strategy_set"]))
    print("allowed_timing_profiles=" + ",".join(document["allowed_timing_profiles"]))
    print(f"skipped_count={len(document['skipped'])}")


if __name__ == "__main__":
    main()
