from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build a single morning handoff packet from validation, hardening review, and replacement plan outputs."
    )
    parser.add_argument("--validation-dir", required=True)
    parser.add_argument("--review-dir", default="")
    parser.add_argument("--replacement-plan-dir", default="")
    parser.add_argument("--output-dir", default="")
    return parser


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def resolve_dir(path_value: str, fallback: Path) -> Path:
    if not path_value:
        return fallback.resolve()
    path = Path(path_value).resolve()
    if path.is_file():
        return path.parent
    return path


def existing_path(path: Path) -> str:
    return str(path.resolve())


def build_payload(
    *,
    validation_dir: Path,
    review_dir: Path,
    replacement_plan_dir: Path,
    validation_payload: dict[str, Any],
    review_payload: dict[str, Any] | None,
    replacement_payload: dict[str, Any] | None,
) -> dict[str, Any]:
    improved_candidates = [str(item).upper() for item in (validation_payload.get("improved_candidates") or []) if str(item).strip()]
    recommended_review_tickers = [
        str(item).upper() for item in ((review_payload or {}).get("recommended_review_tickers") or []) if str(item).strip()
    ]
    recommendation_rows = list((replacement_payload or {}).get("recommendations") or [])
    review_add_count = int((replacement_payload or {}).get("review_add_count", 0) or 0)
    review_replace_count = int((replacement_payload or {}).get("review_replace_count", 0) or 0)
    recommended_review_count = int((replacement_payload or {}).get("recommended_review_count", len(recommendation_rows)) or 0)
    no_candidate_validation = bool(validation_payload.get("no_candidate_validation"))
    shortlist_context = dict(validation_payload.get("shortlist_context") or {})

    if no_candidate_validation:
        morning_decision = "keep_live_book_unchanged"
        operator_message = (
            "No shortlist survivors reached validation. Keep the current live manifest unchanged and let the paper runner use the existing book."
        )
    elif recommended_review_count > 0:
        morning_decision = "review_candidates_before_manifest_change"
        operator_message = (
            "Candidate improvements were found. Review the replacement-plan rows before making any manifest changes. "
            "Until then, the current live manifest remains the safe paper-runner source of truth."
        )
    else:
        morning_decision = "keep_live_book_unchanged"
        operator_message = (
            "Validation completed without any add/replace recommendations. Keep the current live manifest unchanged."
        )

    live_manifest = dict(validation_payload.get("live_manifest") or {})
    return {
        "generated_at": validation_payload.get("generated_at"),
        "validation_basis": str(validation_payload.get("validation_basis", "")),
        "candidate_source": str(validation_payload.get("candidate_source", "")),
        "morning_decision": morning_decision,
        "operator_message": operator_message,
        "paper_runner_guidance": "use_current_live_manifest_until_manual_manifest_change",
        "validation_dir": existing_path(validation_dir),
        "validation_json": existing_path(validation_dir / "live_book_validation.json"),
        "validation_report_md": existing_path(validation_dir / "live_book_validation.md"),
        "review_dir": existing_path(review_dir),
        "review_json": existing_path(review_dir / "live_book_hardening_review.json"),
        "review_md": existing_path(review_dir / "live_book_hardening_review.md"),
        "replacement_plan_dir": existing_path(replacement_plan_dir),
        "replacement_plan_json": existing_path(replacement_plan_dir / "live_book_replacement_plan.json"),
        "replacement_plan_md": existing_path(replacement_plan_dir / "live_book_replacement_plan.md"),
        "candidate_count": int(validation_payload.get("candidate_count", 0) or 0),
        "improved_candidate_count": len(improved_candidates),
        "improved_candidates": improved_candidates,
        "recommended_review_ticker_count": len(recommended_review_tickers),
        "recommended_review_tickers": recommended_review_tickers,
        "review_add_count": review_add_count,
        "review_replace_count": review_replace_count,
        "recommended_review_count": recommended_review_count,
        "replacement_recommendations": recommendation_rows,
        "no_candidate_validation": no_candidate_validation,
        "shortlist_context": shortlist_context,
        "live_manifest": {
            "manifest_path": str(live_manifest.get("manifest_path", "")),
            "strategy_count": int(live_manifest.get("strategy_count", 0) or 0),
            "underlying_count": int(live_manifest.get("underlying_count", 0) or 0),
            "by_family": dict(live_manifest.get("by_family") or {}),
        },
    }


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "# Live Book Morning Handoff",
        "",
        f"- Morning decision: `{payload['morning_decision']}`",
        f"- Validation basis: `{payload['validation_basis']}`",
        f"- Candidate source: `{payload['candidate_source']}`",
        f"- Live strategies: `{payload['live_manifest']['strategy_count']}`",
        f"- Live tickers: `{payload['live_manifest']['underlying_count']}`",
        "",
        "## Operator Message",
        "",
        f"- {payload['operator_message']}",
        "",
        "## Overnight Outcome",
        "",
        f"- Validation candidates: `{payload['candidate_count']}`",
        f"- Improved candidates: `{payload['improved_candidate_count']}`",
        f"- Recommended review tickers: `{payload['recommended_review_ticker_count']}`",
        f"- Review-add candidates: `{payload['review_add_count']}`",
        f"- Review-replace candidates: `{payload['review_replace_count']}`",
        "",
        "## Recommended Review Tickers",
        "",
    ]
    if payload["recommended_review_tickers"]:
        for ticker in payload["recommended_review_tickers"]:
            lines.append(f"- `{ticker}`")
    else:
        lines.append("- none")

    lines.extend(["", "## Artifact Paths", ""])
    for key in (
        "validation_json",
        "validation_report_md",
        "review_json",
        "review_md",
        "replacement_plan_json",
        "replacement_plan_md",
    ):
        lines.append(f"- `{key}`: `{payload[key]}`")

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

    lines.extend(["", "## Replacement Recommendations", ""])
    if payload["replacement_recommendations"]:
        for row in payload["replacement_recommendations"]:
            lines.append(
                f"- `{row.get('ticker', '')}` | action `{row.get('recommended_action', '')}` | "
                f"live `{row.get('currently_live', False)}` | selected `{row.get('candidate_selected_total', 0)}`"
            )
    else:
        lines.append("- none")

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = build_parser().parse_args()
    validation_dir = resolve_dir(args.validation_dir, Path(args.validation_dir))
    review_dir = resolve_dir(args.review_dir, validation_dir / "hardening_review")
    replacement_plan_dir = resolve_dir(args.replacement_plan_dir, review_dir / "replacement_plan")
    output_dir = resolve_dir(args.output_dir, review_dir / "morning_handoff")
    output_dir.mkdir(parents=True, exist_ok=True)

    validation_payload = load_json(validation_dir / "live_book_validation.json")
    review_payload = (
        load_json(review_dir / "live_book_hardening_review.json")
        if (review_dir / "live_book_hardening_review.json").exists()
        else None
    )
    replacement_payload = (
        load_json(replacement_plan_dir / "live_book_replacement_plan.json")
        if (replacement_plan_dir / "live_book_replacement_plan.json").exists()
        else None
    )

    payload = build_payload(
        validation_dir=validation_dir,
        review_dir=review_dir,
        replacement_plan_dir=replacement_plan_dir,
        validation_payload=validation_payload,
        review_payload=review_payload,
        replacement_payload=replacement_payload,
    )

    json_path = output_dir / "live_book_morning_handoff.json"
    md_path = output_dir / "live_book_morning_handoff.md"
    write_json(json_path, payload)
    write_markdown(md_path, payload)
    print(
        json.dumps(
            {
                "output_dir": str(output_dir),
                "morning_decision": payload["morning_decision"],
                "recommended_review_count": payload["recommended_review_count"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
