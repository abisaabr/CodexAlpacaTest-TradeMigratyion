from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parent
DEFAULT_OUTPUT_ROOT = ROOT / "output"
DEFAULT_EVAL_SCRIPT = ROOT / "evaluate_incremental_multiticker_candidates.py"


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
        description="Validate a completed down/choppy program against the current live shared-account book."
    )
    parser.add_argument("--program-root", required=True, help="Path to a launch_down_choppy_program output root.")
    parser.add_argument(
        "--output-dir",
        default="",
        help="Directory for validation outputs. Defaults to <program-root>\\live_book_validation.",
    )
    parser.add_argument("--eval-script", default=str(DEFAULT_EVAL_SCRIPT))
    parser.add_argument("--top-combo-count", type=int, default=4)
    parser.add_argument("--live-manifest", default=str(default_live_manifest_path()))
    return parser


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def load_program_status(program_root: Path) -> dict[str, Any]:
    status_path = program_root / "program_status.json"
    if not status_path.exists():
        raise FileNotFoundError(f"program_status.json not found under {program_root}")
    return load_json(status_path)


def load_live_manifest_summary(manifest_path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(manifest_path.read_text(encoding="utf-8")) or {}
    summary = dict(payload.get("summary") or {})
    return {
        "manifest_path": str(manifest_path),
        "strategy_count": int(payload.get("strategy_count") or len(payload.get("strategies") or [])),
        "underlying_count": int(summary.get("underlying_count") or 0),
        "by_underlying_symbol": dict(summary.get("by_underlying_symbol") or {}),
        "by_family": dict(summary.get("by_family") or {}),
    }


def collect_phase2_candidate_sources(program_root: Path) -> tuple[dict[str, dict[str, Any]], str]:
    phase2_root = program_root / "phase2" / "lanes"
    candidates: dict[str, dict[str, Any]] = {}
    if phase2_root.exists():
        for summary_path in sorted(phase2_root.rglob("*_summary.json")):
            if summary_path.name == "master_summary.json":
                continue
            payload = load_json(summary_path)
            ticker = str(payload.get("ticker", summary_path.stem.replace("_summary", ""))).upper()
            candidates[ticker] = {
                "ticker": ticker,
                "source": "phase2",
                "summary_path": str(summary_path),
                "research_dir": str(summary_path.parent),
                "selected_bull_count": len(((payload.get("promoted") or {}).get("selected_bull") or [])),
                "selected_bear_count": len(((payload.get("promoted") or {}).get("selected_bear") or [])),
                "selected_choppy_count": len(((payload.get("promoted") or {}).get("selected_choppy") or [])),
            }
    if candidates:
        return candidates, "phase2"

    shortlist_path = program_root / "shortlist" / "family_wave_shortlist.json"
    if shortlist_path.exists():
        payload = load_json(shortlist_path)
        for row in payload.get("shortlisted_rows", []):
            ticker = str(row.get("ticker", "")).upper()
            if not ticker:
                continue
            candidates[ticker] = {
                "ticker": ticker,
                "source": "shortlist",
                "summary_path": "",
                "research_dir": str(row.get("lane_research_dir", "")),
                "survivor_score": float(row.get("survivor_score", 0.0) or 0.0),
                "lane_id": str(row.get("lane_id", "")),
                "selected_bull_count": int(row.get("selected_bull_count", 0) or 0),
                "selected_bear_count": int(row.get("selected_bear_count", 0) or 0),
                "selected_choppy_count": int(row.get("selected_choppy_count", 0) or 0),
            }
        if candidates:
            return candidates, "shortlist"

    raise RuntimeError(f"no phase2 or shortlist candidates found under {program_root}")


def invoke_incremental_validation(
    *,
    eval_script: Path,
    candidates: list[str],
    output_dir: Path,
    top_combo_count: int,
) -> None:
    command = [
        sys.executable,
        str(eval_script),
        "--candidates",
        ",".join(ticker.lower() for ticker in candidates),
        "--output-dir",
        str(output_dir),
        "--top-combo-count",
        str(top_combo_count),
    ]
    subprocess.run(command, cwd=ROOT, check=True)


def build_validation_payload(
    *,
    program_root: Path,
    candidate_source_map: dict[str, dict[str, Any]],
    candidate_source: str,
    incremental_rows: list[dict[str, str]],
    combo_rows: list[dict[str, str]],
    live_manifest_summary: dict[str, Any],
    output_dir: Path,
) -> dict[str, Any]:
    improved_rows = [row for row in incremental_rows if str(row.get("improved", "")).strip().lower() == "true"]
    improved_tickers = [str(row.get("candidate", "")).upper() for row in improved_rows if row.get("candidate")]
    best_combo = combo_rows[0] if combo_rows else None
    source_details = [candidate_source_map[ticker] for ticker in sorted(candidate_source_map)]
    return {
        "generated_at": datetime.now().astimezone().isoformat(),
        "program_root": str(program_root),
        "candidate_source": candidate_source,
        "candidate_count": len(candidate_source_map),
        "candidate_tickers": sorted(candidate_source_map),
        "candidate_sources": source_details,
        "improved_candidate_count": len(improved_tickers),
        "improved_candidates": improved_tickers,
        "best_combo": best_combo,
        "live_manifest": live_manifest_summary,
        "incremental_results_csv": str(output_dir / "incremental_results.csv"),
        "combo_results_csv": str(output_dir / "combo_results.csv"),
        "validation_report_md": str(output_dir / "live_book_validation.md"),
    }


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "# Live Book Validation",
        "",
        f"- Program root: `{payload['program_root']}`",
        f"- Candidate source: `{payload['candidate_source']}`",
        f"- Candidate count: `{payload['candidate_count']}`",
        f"- Improved candidates: `{payload['improved_candidate_count']}`",
        "",
        "## Live Manifest Snapshot",
        "",
        f"- Strategies: `{payload['live_manifest']['strategy_count']}`",
        f"- Underlyings: `{payload['live_manifest']['underlying_count']}`",
        "",
        "## Candidate Universe",
        "",
    ]

    for item in payload["candidate_sources"]:
        lines.append(
            f"- `{item['ticker']}` from `{item['source']}` | bear `{item.get('selected_bear_count', 0)}` | choppy `{item.get('selected_choppy_count', 0)}` | research dir `{item.get('research_dir', '')}`"
        )

    lines.extend(["", "## Incremental Winners", ""])
    if payload["improved_candidates"]:
        for ticker in payload["improved_candidates"]:
            lines.append(f"- `{ticker}`")
    else:
        lines.append("- none")

    lines.extend(["", "## Best Combo", ""])
    best_combo = payload.get("best_combo")
    if isinstance(best_combo, dict) and best_combo:
        lines.append(
            f"- Added tickers: `{best_combo.get('added_tickers', '')}` | final equity `{best_combo.get('final_equity', '')}` | return `{best_combo.get('total_return_pct', '')}%` | drawdown `{best_combo.get('max_drawdown_pct', '')}%` | calmar `{best_combo.get('calmar_like', '')}`"
        )
    else:
        lines.append("- no combo survivors yet")

    lines.extend(
        [
            "",
            "## Files",
            "",
            f"- Incremental results: `{payload['incremental_results_csv']}`",
            f"- Combo results: `{payload['combo_results_csv']}`",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = build_parser().parse_args()
    program_root = Path(args.program_root).resolve()
    output_dir = Path(args.output_dir).resolve() if args.output_dir else (program_root / "live_book_validation")
    output_dir.mkdir(parents=True, exist_ok=True)

    status = load_program_status(program_root)
    phase = str(status.get("phase", ""))
    if phase not in {"complete", "complete_phase1_only", "complete_no_phase2_survivors"}:
        raise RuntimeError(f"program status is not yet terminal: {phase}")

    candidate_source_map, candidate_source = collect_phase2_candidate_sources(program_root)
    candidates = sorted(candidate_source_map)
    eval_script = Path(args.eval_script).resolve()
    invoke_incremental_validation(
        eval_script=eval_script,
        candidates=candidates,
        output_dir=output_dir,
        top_combo_count=args.top_combo_count,
    )

    incremental_rows = read_csv_rows(output_dir / "incremental_results.csv")
    combo_rows = read_csv_rows(output_dir / "combo_results.csv")
    live_manifest_summary = load_live_manifest_summary(Path(args.live_manifest).resolve())
    payload = build_validation_payload(
        program_root=program_root,
        candidate_source_map=candidate_source_map,
        candidate_source=candidate_source,
        incremental_rows=incremental_rows,
        combo_rows=combo_rows,
        live_manifest_summary=live_manifest_summary,
        output_dir=output_dir,
    )

    json_path = output_dir / "live_book_validation.json"
    md_path = output_dir / "live_book_validation.md"
    write_json(json_path, payload)
    write_markdown(md_path, payload)
    print(json.dumps({"output_dir": str(output_dir), "candidate_count": len(candidates), "improved_count": payload["improved_candidate_count"]}, indent=2))


if __name__ == "__main__":
    main()
