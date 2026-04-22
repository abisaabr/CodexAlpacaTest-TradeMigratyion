from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parent


def default_live_manifest_path() -> Path:
    candidates = [
        ROOT.parent / "codexalpaca_repo" / "config" / "strategy_manifests" / "multi_ticker_portfolio_live.yaml",
        Path(
            r"C:\Users\rabisaab\OneDrive\CodexAlpaca\downloads_remaining_20260417\folders\codexalpaca_repo\config\strategy_manifests\multi_ticker_portfolio_live.yaml"
        ),
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build a non-destructive live-book replacement plan from validation and hardening review outputs."
    )
    parser.add_argument("--validation-dir", required=True)
    parser.add_argument("--review-dir", default="")
    parser.add_argument("--output-dir", default="")
    parser.add_argument("--live-manifest", default=str(default_live_manifest_path()))
    return parser


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def load_live_manifest(manifest_path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(manifest_path.read_text(encoding="utf-8")) or {}
    summary = dict(payload.get("summary") or {})
    strategies = list(payload.get("strategies") or [])
    by_ticker: dict[str, dict[str, Any]] = {}
    for strategy in strategies:
        symbol = str(strategy.get("underlying_symbol", "")).upper().strip()
        if not symbol:
            continue
        row = by_ticker.setdefault(
            symbol,
            {
                "strategy_count": 0,
                "families": Counter(),
                "regimes": Counter(),
                "timing_profiles": Counter(),
                "names": [],
            },
        )
        row["strategy_count"] += 1
        family = str(strategy.get("family", "")).strip()
        regime = str(strategy.get("regime", "")).strip()
        timing_profile = str(strategy.get("timing_profile", "")).strip()
        if family:
            row["families"][family] += 1
        if regime:
            row["regimes"][regime] += 1
        if timing_profile:
            row["timing_profiles"][timing_profile] += 1
        name = str(strategy.get("name", "")).strip()
        if name:
            row["names"].append(name)

    normalized_by_ticker: dict[str, dict[str, Any]] = {}
    for ticker, row in by_ticker.items():
        normalized_by_ticker[ticker] = {
            "strategy_count": int(row["strategy_count"]),
            "families": dict(sorted(row["families"].items())),
            "regimes": dict(sorted(row["regimes"].items())),
            "timing_profiles": dict(sorted(row["timing_profiles"].items())),
            "names": sorted(row["names"]),
        }

    return {
        "manifest_path": str(manifest_path),
        "strategy_count": int(payload.get("strategy_count") or len(strategies)),
        "underlying_count": int(summary.get("underlying_count") or len(normalized_by_ticker)),
        "by_family": dict(summary.get("by_family") or {}),
        "tickers": sorted(normalized_by_ticker),
        "by_ticker": normalized_by_ticker,
    }


def load_summary_payload(summary_path: str) -> dict[str, Any]:
    if not summary_path:
        return {}
    path = Path(summary_path)
    if not path.exists():
        return {}
    payload = load_json(path)
    return payload if isinstance(payload, dict) else {}


def collect_selected_names(promoted: dict[str, Any]) -> dict[str, list[str]]:
    return {
        "bull": [str(name) for name in (promoted.get("selected_bull") or []) if str(name).strip()],
        "bear": [str(name) for name in (promoted.get("selected_bear") or []) if str(name).strip()],
        "choppy": [str(name) for name in (promoted.get("selected_choppy") or []) if str(name).strip()],
    }


def collect_selected_family_hints(summary_payload: dict[str, Any]) -> list[str]:
    rows = list((summary_payload.get("frozen_initial_config") or {}).get("selected_summary_rows") or [])
    families = {
        str(row.get("family", "")).strip()
        for row in rows
        if isinstance(row, dict) and str(row.get("family", "")).strip()
    }
    return sorted(families)


def resolve_review_tickers(validation_payload: dict[str, Any], review_payload: dict[str, Any] | None) -> list[str]:
    if isinstance(review_payload, dict):
        tickers = [str(ticker).upper() for ticker in (review_payload.get("recommended_review_tickers") or []) if str(ticker).strip()]
        if tickers:
            return tickers
    best_combo = validation_payload.get("best_combo") or {}
    combo_tickers = [token.strip().upper() for token in str(best_combo.get("added_tickers", "") or "").split(",") if token.strip()]
    if combo_tickers:
        return combo_tickers
    return [str(ticker).upper() for ticker in (validation_payload.get("improved_candidates") or []) if str(ticker).strip()]


def build_recommendation_rows(
    *,
    validation_payload: dict[str, Any],
    review_payload: dict[str, Any] | None,
    live_manifest: dict[str, Any],
) -> list[dict[str, Any]]:
    candidate_source_map = {
        str(item.get("ticker", "")).upper(): item
        for item in (validation_payload.get("candidate_sources") or [])
        if isinstance(item, dict) and str(item.get("ticker", "")).strip()
    }
    recommended_tickers = resolve_review_tickers(validation_payload, review_payload)
    rows: list[dict[str, Any]] = []
    for ticker in recommended_tickers:
        source = dict(candidate_source_map.get(ticker, {}))
        summary_payload = load_summary_payload(str(source.get("summary_path", "")))
        promoted = dict(summary_payload.get("promoted") or {})
        selected_names = collect_selected_names(promoted)
        selected_family_hints = collect_selected_family_hints(summary_payload)
        live_row = dict((live_manifest.get("by_ticker") or {}).get(ticker, {}))
        currently_live = bool(live_row)
        current_families = set((live_row.get("families") or {}).keys())
        candidate_family_set = set(selected_family_hints)
        rows.append(
            {
                "ticker": ticker,
                "currently_live": currently_live,
                "recommended_action": "review_replace" if currently_live else "review_add",
                "validation_source": str(source.get("source", "")),
                "research_dir": str(source.get("research_dir", "")),
                "summary_path": str(source.get("summary_path", "")),
                "current_live_strategy_count": int(live_row.get("strategy_count", 0) or 0),
                "current_live_families": dict(live_row.get("families") or {}),
                "current_live_regimes": dict(live_row.get("regimes") or {}),
                "candidate_selected_bull": list(selected_names["bull"]),
                "candidate_selected_bear": list(selected_names["bear"]),
                "candidate_selected_choppy": list(selected_names["choppy"]),
                "candidate_selected_total": int(
                    len(selected_names["bull"]) + len(selected_names["bear"]) + len(selected_names["choppy"])
                ),
                "candidate_family_hints": selected_family_hints,
                "candidate_family_overlap": sorted(current_families & candidate_family_set),
                "candidate_family_new_to_live": sorted(candidate_family_set - current_families),
                "candidate_regime_threshold_pct": float(promoted.get("regime_threshold_pct", 0.0) or 0.0),
                "candidate_reoptimized_total_return_pct": float(
                    ((summary_payload.get("reoptimized") or {}).get("total_return_pct", 0.0) or 0.0)
                ),
                "candidate_reoptimized_max_drawdown_pct": float(
                    ((summary_payload.get("reoptimized") or {}).get("max_drawdown_pct", 0.0) or 0.0)
                ),
                "candidate_frozen_total_return_pct": float(
                    ((summary_payload.get("frozen_initial") or {}).get("total_return_pct", 0.0) or 0.0)
                ),
                "candidate_frozen_max_drawdown_pct": float(
                    ((summary_payload.get("frozen_initial") or {}).get("max_drawdown_pct", 0.0) or 0.0)
                ),
                "selected_bear_count": int(source.get("selected_bear_count", 0) or 0),
                "selected_choppy_count": int(source.get("selected_choppy_count", 0) or 0),
            }
        )
    return rows


def build_payload(
    *,
    validation_dir: Path,
    review_dir: Path,
    validation_payload: dict[str, Any],
    review_payload: dict[str, Any] | None,
    live_manifest: dict[str, Any],
) -> dict[str, Any]:
    rows = build_recommendation_rows(
        validation_payload=validation_payload,
        review_payload=review_payload,
        live_manifest=live_manifest,
    )
    no_candidate_validation = bool(validation_payload.get("no_candidate_validation"))
    note = (
        "No replacement candidates are available because validation produced no candidate survivors."
        if no_candidate_validation
        else "No manifest changes were applied. Use this packet to review add/replace candidates against the current live book."
    )
    add_count = sum(1 for row in rows if row["recommended_action"] == "review_add")
    replace_count = sum(1 for row in rows if row["recommended_action"] == "review_replace")
    return {
        "generated_at": validation_payload.get("generated_at"),
        "validation_dir": str(validation_dir),
        "review_dir": str(review_dir),
        "validation_basis": str(validation_payload.get("validation_basis", "")),
        "candidate_source": str(validation_payload.get("candidate_source", "")),
        "live_manifest": live_manifest,
        "validation_candidate_count": int(validation_payload.get("candidate_count", 0) or 0),
        "recommended_review_count": len(rows),
        "review_add_count": add_count,
        "review_replace_count": replace_count,
        "recommendations": rows,
        "shortlist_context": dict(validation_payload.get("shortlist_context") or {}),
        "note": note,
    }


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "# Live Book Replacement Plan",
        "",
        f"- Validation basis: `{payload['validation_basis']}`",
        f"- Candidate source: `{payload['candidate_source']}`",
        f"- Live strategies: `{payload['live_manifest']['strategy_count']}`",
        f"- Live tickers: `{payload['live_manifest']['underlying_count']}`",
        f"- Replacement candidates: `{payload['recommended_review_count']}`",
        f"- Add candidates: `{payload['review_add_count']}`",
        f"- Replace candidates: `{payload['review_replace_count']}`",
        "",
        "## Summary",
        "",
        f"- {payload['note']}",
        "",
        "## Recommendations",
        "",
    ]
    if payload["recommendations"]:
        for row in payload["recommendations"]:
            lines.append(
                f"- `{row['ticker']}` | action `{row['recommended_action']}` | live `{row['currently_live']}` | selected `{row['candidate_selected_total']}` | reoptimized return `{row['candidate_reoptimized_total_return_pct']}`% | drawdown `{row['candidate_reoptimized_max_drawdown_pct']}`% | new family hints `{', '.join(row['candidate_family_new_to_live']) if row['candidate_family_new_to_live'] else 'none'}`"
            )
    else:
        lines.append("- none")

    lines.extend(["", "## Notes", ""])
    lines.append(f"- Validation dir: `{payload['validation_dir']}`")
    lines.append(f"- Review dir: `{payload['review_dir']}`")
    if payload.get("shortlist_context"):
        shortlist = payload["shortlist_context"]
        lines.append(f"- Shortlisted rows: `{shortlist.get('shortlisted_count', 0)}` out of `{shortlist.get('evaluated_count', 0)}` evaluated.")

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = build_parser().parse_args()
    validation_dir = Path(args.validation_dir).resolve()
    review_dir = Path(args.review_dir).resolve() if args.review_dir else (validation_dir / "hardening_review")
    output_dir = Path(args.output_dir).resolve() if args.output_dir else (review_dir / "replacement_plan")
    output_dir.mkdir(parents=True, exist_ok=True)

    validation_payload = load_json(validation_dir / "live_book_validation.json")
    review_payload = load_json(review_dir / "live_book_hardening_review.json") if (review_dir / "live_book_hardening_review.json").exists() else None
    live_manifest = load_live_manifest(Path(args.live_manifest).resolve())
    payload = build_payload(
        validation_dir=validation_dir,
        review_dir=review_dir,
        validation_payload=validation_payload,
        review_payload=review_payload,
        live_manifest=live_manifest,
    )

    json_path = output_dir / "live_book_replacement_plan.json"
    md_path = output_dir / "live_book_replacement_plan.md"
    write_json(json_path, payload)
    write_markdown(md_path, payload)
    print(
        json.dumps(
            {
                "output_dir": str(output_dir),
                "recommended_review_count": payload["recommended_review_count"],
                "review_add_count": payload["review_add_count"],
                "review_replace_count": payload["review_replace_count"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
