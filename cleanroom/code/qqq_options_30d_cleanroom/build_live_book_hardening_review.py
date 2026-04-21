from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parent


def default_live_manifest_path() -> Path:
    candidates = [
        Path(r"C:\Users\rabisaab\Downloads\codexalpaca_repo\config\strategy_manifests\multi_ticker_portfolio_live.yaml"),
        Path(r"C:\Users\rabisaab\OneDrive\CodexAlpaca\downloads_remaining_20260417\folders\codexalpaca_repo\config\strategy_manifests\multi_ticker_portfolio_live.yaml"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build a non-destructive live-book hardening review packet from validation outputs."
    )
    parser.add_argument("--validation-dir", required=True)
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
    return {
        "manifest_path": str(manifest_path),
        "strategy_count": int(payload.get("strategy_count") or len(payload.get("strategies") or [])),
        "underlying_count": int(summary.get("underlying_count") or 0),
        "tickers": sorted((summary.get("by_underlying_symbol") or {}).keys()),
        "by_family": dict(summary.get("by_family") or {}),
    }


def parse_best_combo_tickers(best_combo: dict[str, Any] | None) -> list[str]:
    if not isinstance(best_combo, dict):
        return []
    raw = str(best_combo.get("added_tickers", "") or "")
    return [token.strip().upper() for token in raw.split(",") if token.strip()]


def build_payload(validation_payload: dict[str, Any], live_manifest: dict[str, Any]) -> dict[str, Any]:
    improved = [str(ticker).upper() for ticker in validation_payload.get("improved_candidates", []) if str(ticker).strip()]
    best_combo_tickers = parse_best_combo_tickers(validation_payload.get("best_combo"))
    recommended = best_combo_tickers or improved
    source_map = {
        str(item.get("ticker", "")).upper(): item
        for item in validation_payload.get("candidate_sources", [])
        if str(item.get("ticker", "")).strip()
    }
    live_tickers = set(live_manifest.get("tickers", []))
    recommendations: list[dict[str, Any]] = []
    for ticker in recommended:
        source = dict(source_map.get(ticker, {}))
        recommendations.append(
            {
                "ticker": ticker,
                "currently_live": ticker in live_tickers,
                "recommended_action": "review_replace" if ticker in live_tickers else "review_add",
                "research_dir": str(source.get("research_dir", "")),
                "summary_path": str(source.get("summary_path", "")),
                "source": str(source.get("source", "")),
                "selected_bear_count": int(source.get("selected_bear_count", 0) or 0),
                "selected_choppy_count": int(source.get("selected_choppy_count", 0) or 0),
            }
        )

    no_candidate_validation = bool(validation_payload.get("no_candidate_validation"))
    note = (
        "No manifest changes were applied. The hardened overnight program produced no shortlist survivors, so there is nothing to review for live-book replacement yet."
        if no_candidate_validation
        else "No manifest changes were applied. This packet is for review-driven live-book hardening only."
    )

    return {
        "generated_at": validation_payload.get("generated_at"),
        "validation_dir": validation_payload.get("validation_report_md", ""),
        "validation_candidate_count": int(validation_payload.get("candidate_count", 0) or 0),
        "no_candidate_validation": no_candidate_validation,
        "live_manifest": live_manifest,
        "improved_candidates": improved,
        "best_combo_tickers": best_combo_tickers,
        "recommended_review_tickers": recommended,
        "recommendations": recommendations,
        "shortlist_context": dict(validation_payload.get("shortlist_context") or {}),
        "note": note,
    }


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "# Live Book Hardening Review",
        "",
        f"- Live strategies: `{payload['live_manifest']['strategy_count']}`",
        f"- Live tickers: `{payload['live_manifest']['underlying_count']}`",
        f"- Validation candidate count: `{payload['validation_candidate_count']}`",
        f"- Improved candidates: `{len(payload['improved_candidates'])}`",
        "",
        "## Summary",
        "",
        f"- {payload['note']}",
        "",
        "## Recommended Review Tickers",
        "",
    ]
    if payload["recommendations"]:
        for item in payload["recommendations"]:
            lines.append(
                f"- `{item['ticker']}` | action `{item['recommended_action']}` | source `{item['source']}` | bear `{item['selected_bear_count']}` | choppy `{item['selected_choppy_count']}` | research dir `{item['research_dir']}`"
            )
    else:
        lines.append("- none")

    shortlist_context = payload.get("shortlist_context") or {}
    if shortlist_context:
        lines.extend(
            [
                "",
                "## Shortlist Diagnostics",
                "",
                f"- Evaluated rows: `{shortlist_context.get('evaluated_count', 0)}`",
                f"- Shortlisted rows: `{shortlist_context.get('shortlisted_count', 0)}`",
                f"- Phase 2 lanes planned: `{shortlist_context.get('phase2_lane_count', 0)}`",
            ]
        )

    lines.extend(
        [
            "",
            "## Current Live Families",
            "",
        ]
    )
    for family, count in sorted((payload["live_manifest"].get("by_family") or {}).items()):
        lines.append(f"- `{family}`: `{count}`")

    lines.extend(
        [
            "",
            "## Notes",
            "",
            f"- {payload['note']}",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = build_parser().parse_args()
    validation_dir = Path(args.validation_dir).resolve()
    output_dir = Path(args.output_dir).resolve() if args.output_dir else (validation_dir / "hardening_review")
    output_dir.mkdir(parents=True, exist_ok=True)

    validation_payload = load_json(validation_dir / "live_book_validation.json")
    live_manifest = load_live_manifest(Path(args.live_manifest).resolve())
    payload = build_payload(validation_payload, live_manifest)

    json_path = output_dir / "live_book_hardening_review.json"
    md_path = output_dir / "live_book_hardening_review.md"
    write_json(json_path, payload)
    write_markdown(md_path, payload)
    print(json.dumps({"output_dir": str(output_dir), "recommended_review_count": len(payload["recommended_review_tickers"])}, indent=2))


if __name__ == "__main__":
    main()
