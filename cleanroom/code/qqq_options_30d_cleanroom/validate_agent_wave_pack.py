from __future__ import annotations

import argparse
import collections
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate a Phase 1 or Phase 2 agent-wave launch pack before execution."
    )
    parser.add_argument("--pack-json", required=True)
    parser.add_argument("--report-path", default="")
    return parser


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def issue(level: str, code: str, message: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = {
        "level": level,
        "code": code,
        "message": message,
    }
    if context:
        payload["context"] = context
    return payload


def parse_command_args(command_args: list[str]) -> dict[str, str]:
    parsed: dict[str, str] = {}
    index = 0
    while index < len(command_args):
        token = str(command_args[index])
        if token.startswith("--") and index + 1 < len(command_args):
            parsed[token] = str(command_args[index + 1])
            index += 2
            continue
        index += 1
    return parsed


def validate_ready_ticker(ready_base_dir: Path, ticker: str) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    ticker_dir = ready_base_dir / ticker.lower()
    if not ticker_dir.exists():
        issues.append(issue("error", "missing_ready_ticker_dir", f"ready dataset folder is missing for {ticker}", {"ticker": ticker, "path": str(ticker_dir)}))
        return issues

    manifest_path = ticker_dir / "manifest.json"
    if not manifest_path.exists():
        issues.append(issue("error", "missing_ready_manifest", f"manifest.json is missing for {ticker}", {"ticker": ticker, "path": str(manifest_path)}))
        return issues

    try:
        manifest = load_json(manifest_path)
    except Exception as exc:  # noqa: BLE001
        issues.append(issue("error", "invalid_ready_manifest", f"manifest.json could not be parsed for {ticker}: {exc}", {"ticker": ticker, "path": str(manifest_path)}))
        return issues

    manifest_symbol = str(manifest.get("symbol", "")).upper()
    if manifest_symbol and manifest_symbol != ticker.upper():
        issues.append(issue("error", "ready_manifest_symbol_mismatch", f"manifest symbol mismatch for {ticker}", {"ticker": ticker, "manifest_symbol": manifest_symbol, "path": str(manifest_path)}))

    paths = manifest.get("paths", {})
    required_keys = ("dense", "wide", "universe", "audit")
    for key in required_keys:
        raw_path = str(paths.get(key, ""))
        if not raw_path:
            issues.append(issue("error", "missing_ready_manifest_path", f"manifest is missing `{key}` for {ticker}", {"ticker": ticker, "path_key": key}))
            continue
        materialized = Path(raw_path)
        if not materialized.exists():
            issues.append(issue("error", "missing_ready_artifact", f"ready artifact `{key}` is missing for {ticker}", {"ticker": ticker, "path_key": key, "path": raw_path}))
    return issues


def validate_pack(pack: dict[str, Any], pack_path: Path) -> dict[str, Any]:
    issues: list[dict[str, Any]] = []
    lanes = pack.get("lanes", [])
    if not isinstance(lanes, list):
        issues.append(issue("error", "invalid_lanes_payload", "pack `lanes` must be a list"))
        lanes = []

    required_top_level = ("phase", "runner_path", "ready_base_dir", "research_root", "governance")
    for key in required_top_level:
        if key not in pack:
            issues.append(issue("error", "missing_pack_key", f"pack is missing required key `{key}`", {"key": key}))

    runner_path = Path(str(pack.get("runner_path", "")))
    if not runner_path.exists():
        issues.append(issue("error", "missing_runner_path", "runner_path does not exist", {"path": str(runner_path)}))

    ready_base_dir = Path(str(pack.get("ready_base_dir", "")))
    if not ready_base_dir.exists():
        issues.append(issue("error", "missing_ready_base_dir", "ready_base_dir does not exist", {"path": str(ready_base_dir)}))

    python_exe = str(pack.get("python_exe", ""))
    if python_exe:
        python_available = (
            Path(python_exe).exists()
            if any(sep in python_exe for sep in ("\\", "/"))
            else shutil.which(python_exe) is not None
        )
        if not python_available:
            issues.append(issue("warning", "python_exe_not_found", "python executable is not currently resolvable", {"python_exe": python_exe}))

    governance = pack.get("governance", {})
    if governance.get("writes_live_state") not in (False, "False", "false", None):
        issues.append(issue("error", "invalid_governance_live_state", "launch packs must not write live state", {"writes_live_state": governance.get("writes_live_state")}))
    if str(governance.get("promotion_mode", "none")).lower() != "none":
        issues.append(issue("error", "invalid_governance_promotion_mode", "launch packs must keep promotion_mode=none", {"promotion_mode": governance.get("promotion_mode")}))
    single_writer_roles = [str(value) for value in governance.get("single_writer_roles", [])]
    if "Promotion Steward" not in single_writer_roles:
        issues.append(issue("warning", "missing_single_writer_role", "Promotion Steward is not listed as a single-writer role"))

    for source_key in ("source_operating_model", "source_coverage_plan_path", "source_phase2_plan_path", "source_shortlist_path", "source_wave_plan_path"):
        source_value = str(pack.get(source_key, "")).strip()
        if source_value and not Path(source_value).exists():
            issues.append(issue("warning", "missing_source_path", f"source path `{source_key}` does not exist", {"source_key": source_key, "path": source_value}))

    build_summary = pack.get("build_summary", {})
    phase = str(pack.get("phase", ""))
    if phase == "phase1_discovery":
        expected_lane_count = int(build_summary.get("expected_lane_count", len(lanes)))
        built_lane_count = int(build_summary.get("built_lane_count", len(lanes)))
        if expected_lane_count != len(lanes):
            issues.append(issue("error", "build_summary_lane_mismatch", "pack build_summary expected_lane_count does not match actual lanes", {"expected": expected_lane_count, "actual": len(lanes)}))
        if built_lane_count != len(lanes):
            issues.append(issue("error", "build_summary_built_mismatch", "pack build_summary built_lane_count does not match actual lanes", {"expected": built_lane_count, "actual": len(lanes)}))
        if len(lanes) == 0:
            issues.append(issue("error", "empty_phase1_pack", "phase1 discovery pack has no lanes"))
    if phase == "phase2_exhaustive":
        planned_lane_count = int(build_summary.get("planned_lane_count", len(lanes)))
        built_lane_count = int(build_summary.get("built_lane_count", len(lanes)))
        if built_lane_count != len(lanes):
            issues.append(issue("error", "phase2_build_summary_built_mismatch", "phase2 pack build_summary built_lane_count does not match actual lanes", {"expected": built_lane_count, "actual": len(lanes)}))
        if planned_lane_count < len(lanes):
            issues.append(issue("error", "phase2_build_summary_planned_mismatch", "phase2 pack has more built lanes than planned lanes", {"planned": planned_lane_count, "actual": len(lanes)}))

    seen_lane_ids: set[str] = set()
    seen_research_dirs: set[str] = set()
    seen_stdout: set[str] = set()
    seen_stderr: set[str] = set()
    actual_lane_tickers: dict[str, list[str]] = {}

    for lane in lanes:
        lane_id = str(lane.get("lane_id", "")).strip()
        if not lane_id:
            issues.append(issue("error", "missing_lane_id", "lane is missing lane_id"))
            continue
        if lane_id in seen_lane_ids:
            issues.append(issue("error", "duplicate_lane_id", f"duplicate lane_id `{lane_id}`", {"lane_id": lane_id}))
        seen_lane_ids.add(lane_id)

        research_dir = str(lane.get("research_dir", "")).strip()
        stdout_path = str(lane.get("stdout_path", "")).strip()
        stderr_path = str(lane.get("stderr_path", "")).strip()
        if research_dir in seen_research_dirs:
            issues.append(issue("error", "duplicate_research_dir", f"duplicate research_dir `{research_dir}`", {"lane_id": lane_id}))
        if stdout_path in seen_stdout:
            issues.append(issue("error", "duplicate_stdout_path", f"duplicate stdout_path `{stdout_path}`", {"lane_id": lane_id}))
        if stderr_path in seen_stderr:
            issues.append(issue("error", "duplicate_stderr_path", f"duplicate stderr_path `{stderr_path}`", {"lane_id": lane_id}))
        seen_research_dirs.add(research_dir)
        seen_stdout.add(stdout_path)
        seen_stderr.add(stderr_path)

        tickers = [str(value).upper() for value in lane.get("tickers", []) if str(value).strip()]
        actual_lane_tickers[lane_id] = tickers
        if not tickers:
            issues.append(issue("warning", "lane_without_tickers", f"lane `{lane_id}` has no tickers", {"lane_id": lane_id}))
        if len(tickers) != len(set(tickers)):
            issues.append(issue("error", "duplicate_ticker_within_lane", f"lane `{lane_id}` has duplicate tickers", {"lane_id": lane_id, "tickers": tickers}))

        command_args = [str(value) for value in lane.get("command_args", [])]
        if not command_args:
            issues.append(issue("error", "missing_command_args", f"lane `{lane_id}` has no command_args", {"lane_id": lane_id}))
        else:
            if command_args[0] != str(runner_path):
                issues.append(issue("error", "runner_path_mismatch", f"lane `{lane_id}` command_args[0] does not match pack runner_path", {"lane_id": lane_id, "command_runner": command_args[0], "pack_runner": str(runner_path)}))
            parsed = parse_command_args(command_args[1:])
            expected_pairs = {
                "--tickers": ",".join(ticker.lower() for ticker in tickers),
                "--ready-base-dir": str(ready_base_dir),
                "--research-dir": research_dir,
                "--strategy-set": str(lane.get("strategy_set", "")),
                "--selection-profile": str(lane.get("selection_profile", "")),
            }
            for key, expected_value in expected_pairs.items():
                if parsed.get(key, "") != expected_value:
                    issues.append(issue("error", "command_arg_mismatch", f"lane `{lane_id}` has mismatched command arg `{key}`", {"lane_id": lane_id, "key": key, "expected": expected_value, "actual": parsed.get(key, "")}))
            family_filters = [str(value) for value in lane.get("family_include_filters", []) if str(value).strip()]
            if family_filters:
                expected_family_value = ",".join(family_filters)
                if parsed.get("--family-include", "") != expected_family_value:
                    issues.append(issue("error", "family_include_mismatch", f"lane `{lane_id}` has mismatched family include filter", {"lane_id": lane_id, "expected": expected_family_value, "actual": parsed.get("--family-include", "")}))

        expected_outputs = [str(value) for value in lane.get("expected_outputs", []) if str(value).strip()]
        if not expected_outputs:
            issues.append(issue("warning", "missing_expected_outputs", f"lane `{lane_id}` has no expected_outputs", {"lane_id": lane_id}))

        for ticker in tickers:
            if ready_base_dir.exists():
                issues.extend(validate_ready_ticker(ready_base_dir, ticker))

    computed_counter: collections.Counter[str] = collections.Counter()
    for tickers in actual_lane_tickers.values():
        computed_counter.update(tickers)
    overlapping = {ticker: count for ticker, count in computed_counter.items() if count > 1}
    overlap_summary = pack.get("overlap_summary", {})
    expected_unique = int(overlap_summary.get("unique_ticker_count", len(computed_counter)))
    expected_total = int(overlap_summary.get("total_lane_slots", sum(computed_counter.values())))
    expected_overlap = int(overlap_summary.get("overlap_ticker_count", len(overlapping)))
    if expected_unique != len(computed_counter):
        issues.append(issue("error", "overlap_summary_unique_mismatch", "pack overlap summary unique_ticker_count does not match lanes", {"expected": expected_unique, "actual": len(computed_counter)}))
    if expected_total != sum(computed_counter.values()):
        issues.append(issue("error", "overlap_summary_total_mismatch", "pack overlap summary total_lane_slots does not match lanes", {"expected": expected_total, "actual": sum(computed_counter.values())}))
    if expected_overlap != len(overlapping):
        issues.append(issue("error", "overlap_summary_overlap_mismatch", "pack overlap summary overlap_ticker_count does not match lanes", {"expected": expected_overlap, "actual": len(overlapping)}))

    errors = [entry for entry in issues if entry["level"] == "error"]
    warnings = [entry for entry in issues if entry["level"] == "warning"]
    return {
        "validated_at": datetime.now().isoformat(),
        "pack_path": str(pack_path),
        "phase": str(pack.get("phase", "")),
        "ok": not errors,
        "error_count": len(errors),
        "warning_count": len(warnings),
        "lane_count": len(lanes),
        "issues": issues,
    }


def main() -> None:
    args = build_parser().parse_args()
    pack_path = Path(args.pack_json).resolve()
    if not pack_path.exists():
        raise FileNotFoundError(f"pack not found: {pack_path}")
    payload = load_json(pack_path)
    report = validate_pack(payload, pack_path)
    if args.report_path:
        report_path = Path(args.report_path).resolve()
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    raise SystemExit(0 if report["ok"] else 1)


if __name__ == "__main__":
    main()
