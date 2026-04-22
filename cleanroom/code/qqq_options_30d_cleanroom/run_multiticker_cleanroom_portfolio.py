from __future__ import annotations

import argparse
import hashlib
import json
import platform
import socket
import subprocess
import sys
import time
from datetime import datetime, timezone
from dataclasses import dataclass, replace
from itertools import product
from pathlib import Path
import re
from typing import Any

import pandas as pd

import backtest_qqq_greeks_portfolio as bqp
from backtest_qqq_greeks_portfolio import (
    DeltaStrategy,
    build_delta_strategies,
    generate_candidate_trades,
    load_dense_data,
    run_portfolio_allocator,
    summarize_regimes,
)
from backtest_qqq_option_strategies import MINUTES_PER_RTH_SESSION, build_day_contexts, load_daily_universe
from backtest_qqq_regime_gated_portfolio import filter_candidate_trades, select_regime_strategies


DEFAULT_OUTPUT_DIR = Path(__file__).resolve().parent / "output"
DEFAULT_RESEARCH_DIR = DEFAULT_OUTPUT_DIR / "multi_ticker"
DEFAULT_TICKERS = ("qqq", "spy", "iwm", "nvda", "tsla", "msft")
DEFAULT_STARTING_EQUITY = 25_000.0
DEFAULT_INITIAL_TRAIN_DAYS = 126
DEFAULT_TEST_DAYS = 21
DEFAULT_STEP_DAYS = 21
DEFAULT_SELECTION_PROFILE = "balanced"
RUN_CHECKPOINT_VERSION = 1
RUN_MANIFEST_VERSION = 1
MAX_EXECUTION_CALIBRATED_THRESHOLD = 0.65
MIN_EXECUTION_CALIBRATED_RISK_CAP = 0.06
REGIME_THRESHOLD_GRID = [0.30, 0.35, 0.40, 0.45, 0.50, 0.55]
TOP_BULL_GRID = [1, 2, 3, 4]
TOP_BEAR_GRID = [1, 2, 3, 4]
TOP_CHOPPY_GRID = [0, 1, 2]
MIN_TRADE_GRID = [2, 3, 5, 8, 10]
RISK_CAP_GRID = [0.08, 0.10, 0.12, 0.15, 0.18, 0.20]
EMPTY_EQUITY_CURVE_COLUMNS = ("trade_date", "minute_index", "equity")


@dataclass(frozen=True)
class TimingProfile:
    name: str
    orb_window: int
    trend_start: int
    credit_minute: int
    straddle_minute: int
    condor_minute: int


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the phased cleanroom multi-ticker options tournament and portfolio promotion."
    )
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--research-dir", default=str(DEFAULT_RESEARCH_DIR))
    parser.add_argument("--tickers", default=",".join(DEFAULT_TICKERS))
    parser.add_argument("--initial-train-days", type=int, default=DEFAULT_INITIAL_TRAIN_DAYS)
    parser.add_argument("--test-days", type=int, default=DEFAULT_TEST_DAYS)
    parser.add_argument("--step-days", type=int, default=DEFAULT_STEP_DAYS)
    parser.add_argument(
        "--strategy-set",
        choices=("standard", "family_expansion", "down_choppy_only", "down_choppy_exhaustive"),
        default="standard",
        help="Strategy universe to test. 'family_expansion' adds new bull/bear/choppy family candidates, 'down_choppy_only' runs a lean bearish/choppy search surface, and 'down_choppy_exhaustive' expands bearish/choppy parameter sweeps.",
    )
    parser.add_argument(
        "--continue-on-error",
        action="store_true",
        help="Continue the batch when a ticker fails research and record it in the master summary.",
    )
    parser.add_argument(
        "--reuse-completed-tickers",
        action="store_true",
        help="Reuse existing per-ticker artifacts in the research directory when they match the requested strategy/timing setup.",
    )
    parser.add_argument(
        "--selection-profile",
        choices=("balanced", "down_choppy_focus"),
        default=DEFAULT_SELECTION_PROFILE,
        help="How strongly to bias config selection toward bearish and choppy regime robustness.",
    )
    parser.add_argument(
        "--family-include",
        default="",
        help="Comma-separated family or family-bucket filters to include, for example 'Credit call spread,credit_spread,long_vol'.",
    )
    parser.add_argument(
        "--family-exclude",
        default="",
        help="Comma-separated family or family-bucket filters to exclude.",
    )
    parser.add_argument(
        "--execution-calibration-handoff",
        default="",
        help="Optional JSON handoff that translates live Alpaca execution evidence into stricter research selection policy.",
    )
    return parser


def write_json(path: Path, payload: dict[str, Any] | list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def artifact_signature(path: Path) -> dict[str, object]:
    stat = path.stat()
    return {
        "path": str(path.resolve()),
        "size": int(stat.st_size),
        "mtime_ns": int(stat.st_mtime_ns),
    }


def build_run_signature(
    *,
    ticker: str,
    wide_path: Path,
    dense_path: Path,
    universe_path: Path,
    profiles: tuple[TimingProfile, ...],
    strategy_set: str,
    selection_profile: str,
    initial_train_days: int,
    test_days: int,
    step_days: int,
    family_include_filters: list[str],
    family_exclude_filters: list[str],
    execution_calibration_context: dict[str, object],
) -> dict[str, object]:
    code_paths = [
        Path(__file__).resolve(),
        (Path(__file__).resolve().parent / "backtest_qqq_greeks_portfolio.py").resolve(),
        (Path(__file__).resolve().parent / "backtest_qqq_option_strategies.py").resolve(),
        (Path(__file__).resolve().parent / "backtest_qqq_regime_gated_portfolio.py").resolve(),
    ]
    return {
        "version": RUN_CHECKPOINT_VERSION,
        "ticker": ticker.upper(),
        "strategy_set": strategy_set,
        "selection_profile": selection_profile,
        "family_include_filters": family_include_filters,
        "family_exclude_filters": family_exclude_filters,
        "timing_profiles": [profile.name for profile in profiles],
        "initial_train_days": int(initial_train_days),
        "test_days": int(test_days),
        "step_days": int(step_days),
        "input_artifacts": {
            "wide": artifact_signature(wide_path),
            "dense": artifact_signature(dense_path),
            "daily_universe": artifact_signature(universe_path),
        },
        "execution_calibration": execution_calibration_context,
        "code_artifacts": [artifact_signature(path) for path in code_paths],
    }


def run_signature_matches(existing: dict[str, object] | None, expected: dict[str, object]) -> bool:
    return existing == expected


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_run_id(*, tickers: list[str], strategy_set: str, selection_profile: str, research_dir: Path) -> str:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    seed = "|".join(
        [
            strategy_set,
            selection_profile,
            str(research_dir.resolve()),
            ",".join(ticker.upper() for ticker in tickers),
        ]
    ).encode("utf-8")
    suffix = hashlib.sha1(seed).hexdigest()[:10]
    return f"{stamp}_{strategy_set}_{suffix}"


def file_lineage_descriptor(path: Path, *, prefer_full_hash: bool = False, sample_bytes: int = 262_144) -> dict[str, object]:
    descriptor: dict[str, object] = {
        "path": str(path.resolve()),
        "exists": path.exists(),
    }
    if not path.exists():
        return descriptor
    stat = path.stat()
    descriptor.update(
        {
            "size": int(stat.st_size),
            "mtime_ns": int(stat.st_mtime_ns),
        }
    )
    hasher = hashlib.sha256()
    if prefer_full_hash or stat.st_size <= sample_bytes * 2:
        with path.open("rb") as handle:
            while True:
                chunk = handle.read(1024 * 1024)
                if not chunk:
                    break
                hasher.update(chunk)
        descriptor["content_hash_scope"] = "full"
    else:
        with path.open("rb") as handle:
            first = handle.read(sample_bytes)
            hasher.update(first)
            handle.seek(max(0, stat.st_size - sample_bytes))
            last = handle.read(sample_bytes)
            hasher.update(last)
        hasher.update(str(stat.st_size).encode("utf-8"))
        descriptor["content_hash_scope"] = "edge_sample"
    descriptor["sha256"] = hasher.hexdigest()
    return descriptor


def find_git_root(start: Path) -> Path | None:
    current = start.resolve()
    for candidate in (current, *current.parents):
        if (candidate / ".git").exists():
            return candidate
    return None


def git_repo_lineage(start: Path) -> dict[str, object] | None:
    git_root = find_git_root(start)
    if git_root is None:
        return None
    try:
        head = subprocess.run(
            ["git", "-C", str(git_root), "rev-parse", "HEAD"],
            capture_output=True,
            check=True,
            text=True,
        ).stdout.strip()
        branch = subprocess.run(
            ["git", "-C", str(git_root), "branch", "--show-current"],
            capture_output=True,
            check=True,
            text=True,
        ).stdout.strip()
        dirty = bool(
            subprocess.run(
                ["git", "-C", str(git_root), "status", "--porcelain"],
                capture_output=True,
                check=True,
                text=True,
            ).stdout.strip()
        )
        return {
            "git_root": str(git_root),
            "head": head,
            "branch": branch,
            "dirty": dirty,
        }
    except Exception:
        return {
            "git_root": str(git_root),
            "head": "",
            "branch": "",
            "dirty": None,
        }


def collect_code_lineage() -> dict[str, object]:
    code_paths = [
        Path(__file__).resolve(),
        (Path(__file__).resolve().parent / "backtest_qqq_greeks_portfolio.py").resolve(),
        (Path(__file__).resolve().parent / "backtest_qqq_option_strategies.py").resolve(),
        (Path(__file__).resolve().parent / "backtest_qqq_regime_gated_portfolio.py").resolve(),
    ]
    sibling_repo = (Path(__file__).resolve().parent.parent / "codexalpaca_repo").resolve()
    repo_contexts = [context for context in [git_repo_lineage(Path(__file__).resolve()), git_repo_lineage(sibling_repo)] if context]
    unique_repo_contexts: list[dict[str, object]] = []
    seen_roots: set[str] = set()
    for context in repo_contexts:
        root = str(context.get("git_root", ""))
        if root and root not in seen_roots:
            seen_roots.add(root)
            unique_repo_contexts.append(context)
    return {
        "files": [file_lineage_descriptor(path, prefer_full_hash=True) for path in code_paths],
        "git_repositories": unique_repo_contexts,
    }


def collect_machine_lineage() -> dict[str, object]:
    return {
        "hostname": socket.gethostname(),
        "platform": platform.platform(),
        "python_executable": sys.executable,
        "python_version": sys.version,
    }


def ticker_input_lineage(output_dir: Path, ticker: str) -> dict[str, object]:
    ticker_lower = ticker.lower()
    paths = {
        "wide": output_dir / f"{ticker_lower}_365d_option_1min_wide_backtest.parquet",
        "dense": output_dir / f"{ticker_lower}_365d_option_1min_dense.parquet",
        "daily_universe": output_dir / f"{ticker_lower}_365d_option_daily_universe.parquet",
        "audit": output_dir / f"{ticker_lower}_365d_audit_report.json",
    }
    return {name: file_lineage_descriptor(path) for name, path in paths.items()}


def resolve_default_execution_calibration_handoff_path() -> Path | None:
    script_dir = Path(__file__).resolve().parent
    candidates: list[Path] = []
    try:
        candidates.append(script_dir.parents[2] / "docs" / "execution_calibration" / "execution_calibration_handoff.json")
    except IndexError:
        pass
    candidates.extend(
        [
            script_dir / "docs" / "execution_calibration" / "execution_calibration_handoff.json",
            script_dir / "output" / "execution_calibration_handoff.json",
            script_dir.parent / "CodexAlpacaTest-TradeMigratyion" / "docs" / "execution_calibration" / "execution_calibration_handoff.json",
        ]
    )
    seen: set[str] = set()
    for candidate in candidates:
        resolved = candidate.resolve()
        resolved_key = str(resolved).lower()
        if resolved_key in seen:
            continue
        seen.add(resolved_key)
        if resolved.exists():
            return resolved
    return None


def resolve_execution_calibration_handoff_path(raw_value: str) -> Path | None:
    if raw_value.strip():
        path = Path(raw_value).expanduser().resolve()
        if not path.exists():
            raise FileNotFoundError(f"execution calibration handoff not found: {path}")
        return path
    return resolve_default_execution_calibration_handoff_path()


def load_execution_calibration_handoff(path: Path | None) -> dict[str, Any] | None:
    if path is None:
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"execution calibration handoff must be a JSON object: {path}")
    return payload


def build_execution_calibration_context(path: Path | None) -> dict[str, object]:
    if path is None:
        return {
            "enabled": False,
            "handoff_lineage": None,
            "overall_execution_posture": "unavailable",
            "evidence_strength": "none",
            "policy": {},
            "flags": {},
            "selection_adjustments": {
                "threshold_shift": 0.0,
                "min_trade_increment": 0,
                "risk_cap_multiplier": 1.0,
                "notes": ["No execution calibration handoff was available for this run."],
            },
        }

    payload = load_execution_calibration_handoff(path)
    posture = payload.get("posture", {}) if payload is not None else {}
    policy = payload.get("policy", {}) if payload is not None else {}
    flags = dict(posture.get("flags", {})) if isinstance(posture, dict) else {}

    threshold_shift = 0.0
    min_trade_increment = 0
    risk_cap_multiplier = 1.0
    notes: list[str] = []

    if policy.get("entry_penalty_mode") == "raised":
        threshold_shift += 0.05
        notes.append("Raised regime thresholds because live entry friction is elevated.")
    if bool(flags.get("sample_size_limited")):
        min_trade_increment += 2
        notes.append("Raised minimum trade requirements because execution evidence is still sample-limited.")
    if bool(flags.get("high_guardrail_pressure")):
        min_trade_increment += 1
        risk_cap_multiplier *= 0.90
        notes.append("Reduced risk caps modestly because live guardrail pressure has been elevated.")
    if bool(flags.get("elevated_entry_friction")):
        risk_cap_multiplier *= 0.90
        notes.append("Reduced risk caps because observed Alpaca entry friction is running above baseline.")
    if bool(flags.get("exit_telemetry_gap")):
        risk_cap_multiplier *= 0.95
        notes.append("Kept additional risk-cap conservatism because exit-side telemetry is still incomplete.")

    if not notes:
        notes.append("Execution calibration is present but does not currently tighten the selection grid.")

    return {
        "enabled": True,
        "generated_at": payload.get("generated_at") if payload is not None else None,
        "registry_json": payload.get("registry_json") if payload is not None else None,
        "handoff_lineage": file_lineage_descriptor(path, prefer_full_hash=True),
        "overall_execution_posture": posture.get("overall_execution_posture", "unknown") if isinstance(posture, dict) else "unknown",
        "evidence_strength": posture.get("evidence_strength", "unknown") if isinstance(posture, dict) else "unknown",
        "policy": dict(policy) if isinstance(policy, dict) else {},
        "flags": flags,
        "selection_adjustments": {
            "threshold_shift": round(float(threshold_shift), 4),
            "min_trade_increment": int(min_trade_increment),
            "risk_cap_multiplier": round(float(risk_cap_multiplier), 4),
            "notes": notes,
        },
    }


def apply_execution_calibration_to_selection_grids(
    selection_grids: dict[str, list[float] | list[int]],
    execution_calibration_context: dict[str, object],
) -> dict[str, list[float] | list[int]]:
    if not bool(execution_calibration_context.get("enabled")):
        return {key: list(values) for key, values in selection_grids.items()}

    adjustments = execution_calibration_context.get("selection_adjustments", {})
    threshold_shift = float(adjustments.get("threshold_shift", 0.0))
    min_trade_increment = int(adjustments.get("min_trade_increment", 0))
    risk_cap_multiplier = float(adjustments.get("risk_cap_multiplier", 1.0))

    calibrated = {key: list(values) for key, values in selection_grids.items()}
    calibrated["thresholds"] = sorted(
        {
            round(min(MAX_EXECUTION_CALIBRATED_THRESHOLD, float(value) + threshold_shift), 2)
            for value in calibrated["thresholds"]
        }
    )
    calibrated["min_trade_values"] = sorted(
        {
            max(1, int(value) + min_trade_increment)
            for value in calibrated["min_trade_values"]
        }
    )
    calibrated["risk_caps"] = sorted(
        {
            round(max(MIN_EXECUTION_CALIBRATED_RISK_CAP, float(value) * risk_cap_multiplier), 2)
            for value in calibrated["risk_caps"]
        }
    )
    return calibrated


def collect_ticker_output_lineage(research_dir: Path, ticker: str) -> dict[str, object]:
    paths = ticker_artifact_paths(research_dir, ticker.lower())
    artifacts: dict[str, object] = {}
    for name, path in paths.items():
        if name == "fold_dir":
            if path.exists():
                artifacts[name] = {
                    "path": str(path.resolve()),
                    "file_count": len(list(path.glob("*"))),
                }
            continue
        if path.exists():
            artifacts[name] = file_lineage_descriptor(path)
    return artifacts


def collect_master_output_lineage(research_dir: Path) -> dict[str, object]:
    paths = {
        "master_summary": research_dir / "master_summary.json",
        "master_report": research_dir / "master_report.md",
        "combined_promoted_candidates": research_dir / "combined_promoted_candidates.csv",
        "combined_promoted_portfolio_trades": research_dir / "combined_promoted_portfolio_trades.csv",
        "combined_promoted_portfolio_equity": research_dir / "combined_promoted_portfolio_equity.csv",
        "shared_account_family_contributions": research_dir / "shared_account_family_contributions.csv",
        "shared_account_family_bucket_contributions": research_dir / "shared_account_family_bucket_contributions.csv",
        "shared_account_premium_bucket_contributions": research_dir / "shared_account_premium_bucket_contributions.csv",
        "family_rankings": research_dir / "family_rankings.csv",
        "family_bucket_rankings": research_dir / "family_bucket_rankings.csv",
        "premium_bucket_rankings": research_dir / "premium_bucket_rankings.csv",
        "run_manifest": research_dir / "run_manifest.json",
    }
    artifacts: dict[str, object] = {}
    for name, path in paths.items():
        if path.exists():
            artifacts[name] = file_lineage_descriptor(path)
    qqq_optional_paths = {
        "qqq_only_promoted_candidates": research_dir / "qqq_only_promoted_candidates.csv",
        "qqq_only_promoted_portfolio_trades": research_dir / "qqq_only_promoted_portfolio_trades.csv",
        "qqq_only_promoted_portfolio_equity": research_dir / "qqq_only_promoted_portfolio_equity.csv",
        "qqq_only_family_contributions": research_dir / "qqq_only_family_contributions.csv",
        "qqq_only_family_bucket_contributions": research_dir / "qqq_only_family_bucket_contributions.csv",
        "qqq_only_premium_bucket_contributions": research_dir / "qqq_only_premium_bucket_contributions.csv",
    }
    for name, path in qqq_optional_paths.items():
        if path.exists():
            artifacts[name] = file_lineage_descriptor(path)
    return artifacts


def write_run_manifest(path: Path, payload: dict[str, object]) -> None:
    manifest = dict(payload)
    manifest["updated_at_iso"] = utc_now_iso()
    write_json(path, manifest)


def append_run_registry(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload) + "\n")


def ticker_artifact_paths(research_dir: Path, ticker_lower: str) -> dict[str, Path]:
    fold_dir = research_dir / f"{ticker_lower}_fold_checkpoints"
    return {
        "candidate_trades": research_dir / f"{ticker_lower}_candidate_trades.csv",
        "regime_summary": research_dir / f"{ticker_lower}_regime_summary.csv",
        "walkforward_folds": research_dir / f"{ticker_lower}_walkforward_folds.csv",
        "frozen_trades": research_dir / f"{ticker_lower}_walkforward_frozen_trades.csv",
        "frozen_equity": research_dir / f"{ticker_lower}_walkforward_frozen_equity.csv",
        "frozen_family_contributions": research_dir / f"{ticker_lower}_walkforward_frozen_family_contributions.csv",
        "frozen_family_bucket_contributions": research_dir / f"{ticker_lower}_walkforward_frozen_family_bucket_contributions.csv",
        "frozen_premium_bucket_contributions": research_dir / f"{ticker_lower}_walkforward_frozen_premium_bucket_contributions.csv",
        "reoptimized_family_contributions": research_dir / f"{ticker_lower}_walkforward_reoptimized_family_contributions.csv",
        "reoptimized_family_bucket_contributions": research_dir / f"{ticker_lower}_walkforward_reoptimized_family_bucket_contributions.csv",
        "reoptimized_premium_bucket_contributions": research_dir / f"{ticker_lower}_walkforward_reoptimized_premium_bucket_contributions.csv",
        "frozen_config": research_dir / f"{ticker_lower}_frozen_config.json",
        "promotion": research_dir / f"{ticker_lower}_promotion.json",
        "summary": research_dir / f"{ticker_lower}_summary.json",
        "phase_status": research_dir / f"{ticker_lower}_phase_status.json",
        "candidate_checkpoint": research_dir / f"{ticker_lower}_candidate_checkpoint.json",
        "walkforward_checkpoint": research_dir / f"{ticker_lower}_walkforward_checkpoint.json",
        "fold_dir": fold_dir,
    }


def fold_artifact_paths(paths: dict[str, Path], fold_id: int) -> dict[str, Path]:
    fold_dir = paths["fold_dir"]
    return {
        "reopt_trades": fold_dir / f"fold_{fold_id:02d}_reopt_trades.parquet",
        "reopt_equity": fold_dir / f"fold_{fold_id:02d}_reopt_equity.parquet",
        "frozen_trades": fold_dir / f"fold_{fold_id:02d}_frozen_trades.parquet",
        "frozen_equity": fold_dir / f"fold_{fold_id:02d}_frozen_equity.parquet",
    }


def write_phase_status(
    path: Path,
    *,
    ticker: str,
    phase: str,
    status: str,
    message: str = "",
    extra: dict[str, object] | None = None,
) -> None:
    payload: dict[str, object] = {
        "ticker": ticker.upper(),
        "phase": phase,
        "status": status,
        "message": message,
        "timestamp_epoch": time.time(),
    }
    if extra:
        payload.update(extra)
    write_json(path, payload)


def empty_equity_curve_df() -> pd.DataFrame:
    return pd.DataFrame(columns=list(EMPTY_EQUITY_CURVE_COLUMNS))


def read_candidate_trades_csv(path: Path, *, expected_trade_count: int | None = None) -> pd.DataFrame:
    if expected_trade_count is not None and int(expected_trade_count) == 0:
        return bqp.empty_candidate_trades_df()
    try:
        trades = pd.read_csv(path)
    except pd.errors.EmptyDataError:
        return bqp.empty_candidate_trades_df()
    if trades.empty and len(trades.columns) == 0:
        return bqp.empty_candidate_trades_df()
    return trades


def try_load_candidate_checkpoint(
    *,
    paths: dict[str, Path],
    run_signature: dict[str, object],
) -> pd.DataFrame | None:
    checkpoint_path = paths["candidate_checkpoint"]
    candidate_trades_path = paths["candidate_trades"]
    if not checkpoint_path.exists() or not candidate_trades_path.exists():
        return None
    checkpoint = json.loads(checkpoint_path.read_text(encoding="utf-8"))
    if checkpoint.get("phase") != "candidate_ready":
        return None
    if not run_signature_matches(checkpoint.get("run_signature"), run_signature):
        return None
    return read_candidate_trades_csv(
        candidate_trades_path,
        expected_trade_count=checkpoint.get("candidate_trade_count"),
    )


def write_candidate_checkpoint(
    *,
    paths: dict[str, Path],
    run_signature: dict[str, object],
    candidate_trade_count: int,
) -> None:
    write_json(
        paths["candidate_checkpoint"],
        {
            "phase": "candidate_ready",
            "run_signature": run_signature,
            "candidate_trade_count": int(candidate_trade_count),
            "completed_at_epoch": time.time(),
        },
    )


def write_fold_artifacts(
    *,
    paths: dict[str, Path],
    fold_id: int,
    reopt_trades: pd.DataFrame,
    reopt_equity: pd.DataFrame,
    frozen_trades: pd.DataFrame,
    frozen_equity: pd.DataFrame,
) -> None:
    paths["fold_dir"].mkdir(parents=True, exist_ok=True)
    fold_paths = fold_artifact_paths(paths, fold_id)
    reopt_trades.to_parquet(fold_paths["reopt_trades"], index=False)
    reopt_equity.to_parquet(fold_paths["reopt_equity"], index=False)
    frozen_trades.to_parquet(fold_paths["frozen_trades"], index=False)
    frozen_equity.to_parquet(fold_paths["frozen_equity"], index=False)


def try_load_walkforward_checkpoint(
    *,
    paths: dict[str, Path],
    run_signature: dict[str, object],
) -> dict[str, object] | None:
    checkpoint_path = paths["walkforward_checkpoint"]
    if not checkpoint_path.exists():
        return None
    checkpoint = json.loads(checkpoint_path.read_text(encoding="utf-8"))
    if not run_signature_matches(checkpoint.get("run_signature"), run_signature):
        return None
    frozen_config = checkpoint.get("frozen_config")
    if not isinstance(frozen_config, dict):
        return None
    completed_folds = [int(fold_id) for fold_id in checkpoint.get("completed_folds", [])]
    reopt_trade_frames: list[pd.DataFrame] = []
    reopt_equity_frames: list[pd.DataFrame] = []
    frozen_trade_frames: list[pd.DataFrame] = []
    frozen_equity_frames: list[pd.DataFrame] = []
    for fold_id in completed_folds:
        fold_paths = fold_artifact_paths(paths, fold_id)
        if not all(path.exists() for path in fold_paths.values()):
            return None
        reopt_trade_frames.append(pd.read_parquet(fold_paths["reopt_trades"]))
        reopt_equity_frames.append(pd.read_parquet(fold_paths["reopt_equity"]))
        frozen_trade_frames.append(pd.read_parquet(fold_paths["frozen_trades"]))
        frozen_equity_frames.append(pd.read_parquet(fold_paths["frozen_equity"]))
    return {
        "frozen_config": frozen_config,
        "completed_folds": set(completed_folds),
        "fold_rows": list(checkpoint.get("fold_rows", [])),
        "reopt_current_equity": float(checkpoint.get("reopt_current_equity", DEFAULT_STARTING_EQUITY)),
        "frozen_current_equity": float(checkpoint.get("frozen_current_equity", DEFAULT_STARTING_EQUITY)),
        "reopt_trade_frames": reopt_trade_frames,
        "reopt_equity_frames": reopt_equity_frames,
        "frozen_trade_frames": frozen_trade_frames,
        "frozen_equity_frames": frozen_equity_frames,
    }


def write_walkforward_checkpoint(
    *,
    paths: dict[str, Path],
    run_signature: dict[str, object],
    frozen_config: dict[str, object],
    completed_folds: set[int],
    fold_rows: list[dict[str, object]],
    reopt_current_equity: float,
    frozen_current_equity: float,
) -> None:
    write_json(
        paths["walkforward_checkpoint"],
        {
            "phase": "walkforward",
            "run_signature": run_signature,
            "frozen_config": frozen_config,
            "completed_folds": sorted(int(fold_id) for fold_id in completed_folds),
            "fold_rows": fold_rows,
            "reopt_current_equity": float(reopt_current_equity),
            "frozen_current_equity": float(frozen_current_equity),
            "updated_at_epoch": time.time(),
        },
    )


def build_timing_profiles(strategy_set: str = "standard") -> tuple[TimingProfile, ...]:
    profiles = (
        TimingProfile(
            name="reactive",
            orb_window=5,
            trend_start=20,
            credit_minute=45,
            straddle_minute=5,
            condor_minute=15,
        ),
        TimingProfile(
            name="fast",
            orb_window=10,
            trend_start=30,
            credit_minute=60,
            straddle_minute=10,
            condor_minute=20,
        ),
        TimingProfile(
            name="base",
            orb_window=15,
            trend_start=45,
            credit_minute=90,
            straddle_minute=15,
            condor_minute=30,
        ),
        TimingProfile(
            name="slow",
            orb_window=20,
            trend_start=60,
            credit_minute=120,
            straddle_minute=20,
            condor_minute=45,
        ),
        TimingProfile(
            name="patient",
            orb_window=25,
            trend_start=75,
            credit_minute=150,
            straddle_minute=25,
            condor_minute=60,
        ),
    )
    if strategy_set in {"down_choppy_only", "down_choppy_exhaustive"}:
        # Keep the bearish/choppy tournament lean so we can cover more symbols faster.
        return tuple(profile for profile in profiles if profile.name in {"reactive", "fast", "base"})
    return profiles


def normalize_family_token(value: str) -> str:
    token = re.sub(r"[^a-z0-9]+", "_", value.strip().lower()).strip("_")
    return token


def parse_family_filters(value: str) -> list[str]:
    if not value.strip():
        return []
    return sorted({normalize_family_token(part) for part in value.split(",") if normalize_family_token(part)})


def step_label(step: int) -> str:
    sign = "p" if step >= 0 else "n"
    return f"{sign}{abs(int(step)):02d}"


def load_wide_data_for_ticker(path: Path, ticker: str) -> pd.DataFrame:
    prefix = ticker.lower()
    rename_map = {
        f"{prefix}_open": "qqq_open",
        f"{prefix}_high": "qqq_high",
        f"{prefix}_low": "qqq_low",
        f"{prefix}_close": "qqq_close",
        f"{prefix}_volume": "qqq_volume",
        f"{prefix}_trade_count": "qqq_trade_count",
        f"{prefix}_vwap": "qqq_vwap",
    }
    wide = pd.read_parquet(path).copy()
    missing = [column for column in rename_map if column not in wide.columns]
    if missing:
        raise KeyError(f"missing expected underlying columns for {ticker.upper()}: {missing}")
    wide = wide.rename(columns=rename_map)
    wide["timestamp_et"] = pd.to_datetime(wide["timestamp_et"])
    wide["trade_date"] = pd.to_datetime(wide["trade_date"]).dt.date
    wide = wide.sort_values(["trade_date", "timestamp_et"]).reset_index(drop=True)
    wide["minute_index"] = wide.groupby("trade_date").cumcount()

    qqq_vwap = wide["qqq_vwap"].where(wide["qqq_vwap"].notna(), wide["qqq_close"])
    notional = qqq_vwap.fillna(wide["qqq_close"]).fillna(0.0) * wide["qqq_volume"].fillna(0.0)
    wide["cum_notional"] = notional.groupby(wide["trade_date"]).cumsum()
    wide["cum_volume"] = wide["qqq_volume"].fillna(0.0).groupby(wide["trade_date"]).cumsum()
    wide["intraday_vwap"] = wide["cum_notional"] / wide["cum_volume"].replace(0.0, pd.NA)
    wide["intraday_vwap"] = wide.groupby("trade_date")["intraday_vwap"].ffill().fillna(wide["qqq_close"])
    wide["ema_fast"] = wide.groupby("trade_date")["qqq_close"].transform(
        lambda series: series.ewm(span=15, adjust=False).mean()
    )
    wide["ema_slow"] = wide.groupby("trade_date")["qqq_close"].transform(
        lambda series: series.ewm(span=60, adjust=False).mean()
    )

    full_session_dates: list[object] = []
    for trade_date, frame in wide.groupby("trade_date", sort=True):
        if len(frame) != MINUTES_PER_RTH_SESSION:
            continue
        if frame["qqq_close"].isna().any():
            continue
        full_session_dates.append(trade_date)
    return wide[wide["trade_date"].isin(full_session_dates)].reset_index(drop=True)


def build_day_return_map(wide: pd.DataFrame) -> tuple[list[object], dict[object, float]]:
    daily = (
        wide.groupby("trade_date")
        .agg(day_open=("qqq_open", "first"), day_close=("qqq_close", "last"))
        .reset_index()
    )
    daily["day_ret_pct"] = (daily["day_close"] / daily["day_open"] - 1.0) * 100.0
    return daily["trade_date"].tolist(), dict(zip(daily["trade_date"], daily["day_ret_pct"]))


def assign_regime(day_ret_pct: float, threshold: float) -> str:
    if day_ret_pct >= threshold:
        return "bull"
    if day_ret_pct <= -threshold:
        return "bear"
    return "choppy"


def relabel_candidate_trades(
    candidate_trades: pd.DataFrame,
    day_return_map: dict[object, float],
    threshold: float,
) -> pd.DataFrame:
    relabeled = candidate_trades.copy()
    if relabeled.empty and len(relabeled.columns) == 0:
        return bqp.empty_candidate_trades_df()
    if "trade_date" not in relabeled.columns:
        return relabeled.iloc[0:0].copy()
    relabeled["trade_date"] = pd.to_datetime(relabeled["trade_date"]).dt.date
    relabeled["regime"] = [
        assign_regime(day_return_map[row.trade_date], threshold=threshold)
        for row in relabeled.itertuples(index=False)
    ]
    return relabeled


def build_folds(
    trade_dates: list[object],
    initial_train_days: int,
    test_days: int,
    step_days: int,
) -> list[dict[str, object]]:
    folds: list[dict[str, object]] = []
    train_end = initial_train_days
    fold_id = 1
    while train_end < len(trade_dates):
        test_end = min(train_end + test_days, len(trade_dates))
        folds.append(
            {
                "fold": fold_id,
                "train_dates": trade_dates[:train_end],
                "test_dates": trade_dates[train_end:test_end],
            }
        )
        if test_end >= len(trade_dates):
            break
        train_end += step_days
        fold_id += 1
    return folds


def subset_trades(trades: pd.DataFrame, dates: set[object]) -> pd.DataFrame:
    if trades.empty or not dates:
        return trades.iloc[0:0].copy() if len(trades.columns) > 0 else bqp.empty_candidate_trades_df()
    if "trade_date" not in trades.columns:
        return trades.iloc[0:0].copy() if len(trades.columns) > 0 else bqp.empty_candidate_trades_df()
    trade_dates = pd.to_datetime(trades["trade_date"]).dt.date
    return trades.loc[trade_dates.isin(dates)].copy()


def score_drawdown(total_return_pct: float, max_drawdown_pct: float) -> float:
    if max_drawdown_pct >= 0.0:
        return total_return_pct if total_return_pct > 0.0 else 0.0
    return total_return_pct / abs(max_drawdown_pct)


def build_selection_grids(
    selection_profile: str,
    strategy_set: str = "standard",
) -> dict[str, list[float] | list[int]]:
    if strategy_set == "down_choppy_only":
        if selection_profile == "down_choppy_focus":
            return {
                "thresholds": [0.35, 0.40, 0.45, 0.50],
                "top_bull_values": [0, 1],
                "top_bear_values": [1, 2, 3],
                "top_choppy_values": [1, 2, 3],
                "min_trade_values": [3, 5, 8],
                "risk_caps": [0.08, 0.10, 0.12],
            }
        return {
            "thresholds": [0.35, 0.40, 0.45, 0.50],
            "top_bull_values": [0, 1, 2],
            "top_bear_values": [1, 2, 3],
            "top_choppy_values": [1, 2, 3],
            "min_trade_values": [3, 5, 8],
            "risk_caps": [0.08, 0.10, 0.12, 0.15],
        }
    if strategy_set == "down_choppy_exhaustive":
        if selection_profile == "down_choppy_focus":
            return {
                "thresholds": [0.30, 0.35, 0.40, 0.45, 0.50],
                "top_bull_values": [0, 1],
                "top_bear_values": [1, 2, 3, 4],
                "top_choppy_values": [1, 2, 3],
                "min_trade_values": [2, 3, 5, 8],
                "risk_caps": [0.08, 0.10, 0.12, 0.15],
            }
        return {
            "thresholds": [0.30, 0.35, 0.40, 0.45, 0.50],
            "top_bull_values": [0, 1, 2],
            "top_bear_values": [1, 2, 3, 4],
            "top_choppy_values": [1, 2, 3],
            "min_trade_values": [2, 3, 5, 8],
            "risk_caps": [0.08, 0.10, 0.12, 0.15],
        }
    if selection_profile == "down_choppy_focus":
        return {
            "thresholds": REGIME_THRESHOLD_GRID,
            "top_bull_values": [1, 2, 3],
            "top_bear_values": [2, 3, 4],
            "top_choppy_values": [1, 2, 3],
            "min_trade_values": [3, 5, 8, 10],
            "risk_caps": [0.08, 0.10, 0.12, 0.15],
        }
    return {
        "thresholds": REGIME_THRESHOLD_GRID,
        "top_bull_values": TOP_BULL_GRID,
        "top_bear_values": TOP_BEAR_GRID,
        "top_choppy_values": TOP_CHOPPY_GRID,
        "min_trade_values": MIN_TRADE_GRID,
        "risk_caps": RISK_CAP_GRID,
    }


def build_regime_selection_metrics(selected_rows: pd.DataFrame) -> dict[str, float | int]:
    metrics: dict[str, float | int] = {
        "bull_trade_count": 0,
        "bear_trade_count": 0,
        "choppy_trade_count": 0,
        "bull_net_pnl": 0.0,
        "bear_net_pnl": 0.0,
        "choppy_net_pnl": 0.0,
    }
    if selected_rows.empty:
        metrics["down_choppy_trade_count"] = 0
        metrics["down_choppy_net_pnl"] = 0.0
        return metrics

    for regime in ("bull", "bear", "choppy"):
        subset = selected_rows[selected_rows["regime"] == regime]
        metrics[f"{regime}_trade_count"] = int(subset["trade_count"].sum()) if not subset.empty else 0
        metrics[f"{regime}_net_pnl"] = float(subset["total_net_pnl_1x"].sum()) if not subset.empty else 0.0

    metrics["down_choppy_trade_count"] = int(metrics["bear_trade_count"]) + int(metrics["choppy_trade_count"])
    metrics["down_choppy_net_pnl"] = float(metrics["bear_net_pnl"]) + float(metrics["choppy_net_pnl"])
    return metrics


def empty_summary(starting_equity: float, risk_cap: float) -> dict[str, object]:
    return {
        "starting_equity": starting_equity,
        "final_equity": starting_equity,
        "total_return_pct": 0.0,
        "trade_count": 0,
        "win_rate_pct": 0.0,
        "max_drawdown_pct": 0.0,
        "portfolio_max_open_risk_fraction": risk_cap,
        "strategy_contributions": [],
    }


def entry_orb_profile(ctx, *, bullish: bool, window: int) -> int | None:
    if len(ctx.frame) <= window:
        return None
    opening_end = window - 1
    opening_range_high = float(ctx.frame.loc[:opening_end, "qqq_high"].max())
    opening_range_low = float(ctx.frame.loc[:opening_end, "qqq_low"].min())
    search_end = min(window + 105, len(ctx.frame) - 1)
    for idx in range(window, search_end + 1):
        row = ctx.frame.iloc[idx]
        if bullish:
            if (
                row["qqq_close"] > opening_range_high * 1.0002
                and row["qqq_close"] > row["intraday_vwap"]
                and row["ema_fast"] > row["ema_slow"]
            ):
                return idx
        else:
            if (
                row["qqq_close"] < opening_range_low * 0.9998
                and row["qqq_close"] < row["intraday_vwap"]
                and row["ema_fast"] < row["ema_slow"]
            ):
                return idx
    return None


def entry_trend_profile(ctx, *, bullish: bool, start_minute: int) -> int | None:
    if len(ctx.frame) <= start_minute:
        return None
    search_end = min(start_minute + 105, len(ctx.frame) - 1)
    for idx in range(start_minute, search_end + 1):
        row = ctx.frame.iloc[idx]
        move_from_open = (row["qqq_close"] / ctx.day_open) - 1.0
        distance_from_vwap = (row["qqq_close"] / row["intraday_vwap"]) - 1.0
        if bullish:
            prev_close_ok = True if ctx.prev_close is None else row["qqq_close"] >= ctx.prev_close * 0.9995
            if (
                move_from_open >= 0.0015
                and distance_from_vwap >= 0.0007
                and row["ema_fast"] > row["ema_slow"]
                and prev_close_ok
            ):
                return idx
        else:
            prev_close_ok = True if ctx.prev_close is None else row["qqq_close"] <= ctx.prev_close * 1.0005
            if (
                move_from_open <= -0.0015
                and distance_from_vwap <= -0.0007
                and row["ema_fast"] < row["ema_slow"]
                and prev_close_ok
            ):
                return idx
    return None


def entry_credit_profile(ctx, *, bullish: bool, minute_index: int) -> int | None:
    if minute_index >= len(ctx.frame):
        return None
    row = ctx.frame.iloc[minute_index]
    session_range_pct = (
        float(ctx.frame.loc[:minute_index, "qqq_high"].max()) - float(ctx.frame.loc[:minute_index, "qqq_low"].min())
    ) / ctx.day_open
    if bullish:
        if (
            session_range_pct <= 0.0085
            and row["qqq_close"] > row["intraday_vwap"]
            and row["ema_fast"] > row["ema_slow"]
            and row["qqq_close"] > ctx.day_open
        ):
            return minute_index
    else:
        if (
            session_range_pct <= 0.0085
            and row["qqq_close"] < row["intraday_vwap"]
            and row["ema_fast"] < row["ema_slow"]
            and row["qqq_close"] < ctx.day_open
        ):
            return minute_index
    return None


def entry_straddle_profile(ctx, *, minute_index: int) -> int | None:
    if minute_index >= len(ctx.frame):
        return None
    range_pct = (
        float(ctx.frame.loc[:minute_index, "qqq_high"].max()) - float(ctx.frame.loc[:minute_index, "qqq_low"].min())
    ) / ctx.day_open
    ret_pct = (float(ctx.frame.loc[minute_index, "qqq_close"]) / ctx.day_open) - 1.0
    if range_pct >= 0.0055 or abs(ret_pct) >= 0.0035:
        return minute_index
    return None


def entry_condor_profile(ctx, *, minute_index: int) -> int | None:
    if minute_index >= len(ctx.frame):
        return None
    row = ctx.frame.iloc[minute_index]
    range_pct = (
        float(ctx.frame.loc[:minute_index, "qqq_high"].max()) - float(ctx.frame.loc[:minute_index, "qqq_low"].min())
    ) / ctx.day_open
    ret_pct = (float(row["qqq_close"]) / ctx.day_open) - 1.0
    close_to_vwap = abs((row["qqq_close"] / row["intraday_vwap"]) - 1.0)
    if range_pct <= 0.0062 and abs(ret_pct) <= 0.0045 and close_to_vwap <= 0.0020:
        return minute_index
    return None


def build_signal_dispatch(profiles: tuple[TimingProfile, ...]) -> dict[str, Any]:
    dispatch: dict[str, Any] = {}
    for profile in profiles:
        dispatch[f"{profile.name}__orb_call"] = (
            lambda ctx, window=profile.orb_window: entry_orb_profile(ctx, bullish=True, window=window)
        )
        dispatch[f"{profile.name}__orb_put"] = (
            lambda ctx, window=profile.orb_window: entry_orb_profile(ctx, bullish=False, window=window)
        )
        dispatch[f"{profile.name}__trend_call"] = (
            lambda ctx, start=profile.trend_start: entry_trend_profile(ctx, bullish=True, start_minute=start)
        )
        dispatch[f"{profile.name}__trend_put"] = (
            lambda ctx, start=profile.trend_start: entry_trend_profile(ctx, bullish=False, start_minute=start)
        )
        dispatch[f"{profile.name}__credit_bull"] = (
            lambda ctx, minute_index=profile.credit_minute: entry_credit_profile(ctx, bullish=True, minute_index=minute_index)
        )
        dispatch[f"{profile.name}__credit_bear"] = (
            lambda ctx, minute_index=profile.credit_minute: entry_credit_profile(ctx, bullish=False, minute_index=minute_index)
        )
        dispatch[f"{profile.name}__long_straddle"] = (
            lambda ctx, minute_index=profile.straddle_minute: entry_straddle_profile(ctx, minute_index=minute_index)
        )
        dispatch[f"{profile.name}__iron_condor"] = (
            lambda ctx, minute_index=profile.condor_minute: entry_condor_profile(ctx, minute_index=minute_index)
        )
    return dispatch


def build_strategy_variants(
    ticker: str,
    profiles: tuple[TimingProfile, ...],
    *,
    strategy_set: str = "standard",
    family_include_filters: list[str] | None = None,
    family_exclude_filters: list[str] | None = None,
) -> list[DeltaStrategy]:
    variants: list[DeltaStrategy] = []
    for base_strategy in build_delta_strategies(strategy_set=strategy_set):
        if not strategy_matches_family_filters(
            base_strategy,
            family_include_filters=family_include_filters or [],
            family_exclude_filters=family_exclude_filters or [],
        ):
            continue
        for profile in profiles:
            variants.append(
                replace(
                    base_strategy,
                    name=f"{ticker.lower()}__{profile.name}__{base_strategy.name}",
                    description=f"{ticker.upper()} [{profile.name}] {base_strategy.description}",
                    signal_name=f"{profile.name}__{base_strategy.signal_name}",
                )
            )
    return variants


def parse_strategy_metadata(strategy_name: str) -> tuple[str, str, str]:
    ticker, profile, base_name = strategy_name.split("__", 2)
    return ticker.upper(), profile, base_name


def enrich_candidate_trades(trades: pd.DataFrame) -> pd.DataFrame:
    if trades.empty:
        return trades
    enriched = trades.copy()
    metadata = [parse_strategy_metadata(name) for name in enriched["strategy"].astype(str)]
    enriched["ticker"] = [item[0] for item in metadata]
    enriched["timing_profile"] = [item[1] for item in metadata]
    enriched["base_strategy"] = [item[2] for item in metadata]
    if "abs_entry_net_premium" not in enriched.columns and "entry_net_premium" in enriched.columns:
        enriched["abs_entry_net_premium"] = enriched["entry_net_premium"].abs()
    if "premium_bucket" not in enriched.columns and "abs_entry_net_premium" in enriched.columns:
        enriched["premium_bucket"] = [
            bqp.classify_premium_bucket(float(value))
            for value in enriched["abs_entry_net_premium"].fillna(0.0)
        ]
    if "is_sub_015_premium" not in enriched.columns and "abs_entry_net_premium" in enriched.columns:
        enriched["is_sub_015_premium"] = enriched["abs_entry_net_premium"] < 0.15
    if "is_sub_030_premium" not in enriched.columns and "abs_entry_net_premium" in enriched.columns:
        enriched["is_sub_030_premium"] = enriched["abs_entry_net_premium"] < 0.30
    if "total_fees_per_combo" not in enriched.columns:
        if {
            "entry_total_fees_per_combo",
            "exit_total_fees_per_combo",
        }.issubset(enriched.columns):
            enriched["total_fees_per_combo"] = (
                enriched["entry_total_fees_per_combo"] + enriched["exit_total_fees_per_combo"]
            )
        elif "total_commission_per_combo" in enriched.columns:
            enriched["total_fees_per_combo"] = enriched["total_commission_per_combo"]
    if "total_commission_per_combo" not in enriched.columns and {
        "entry_commission_per_combo",
        "exit_commission_per_combo",
    }.issubset(enriched.columns):
        enriched["total_commission_per_combo"] = (
            enriched["entry_commission_per_combo"] + enriched["exit_commission_per_combo"]
        )
    return enriched


def family_bucket_for_strategy_family(family: str) -> str:
    if family in {"Single-leg long call", "Single-leg long put"}:
        return "Single-leg"
    if family in {"Debit call spread", "Debit put spread"}:
        return "Debit spread"
    if family in {"Credit put spread", "Credit call spread"}:
        return "Credit spread"
    if family in {
        "Iron condor",
        "Iron butterfly",
        "Call butterfly",
        "Put butterfly",
        "Broken-wing call butterfly",
        "Broken-wing put butterfly",
    }:
        return "Neutral premium"
    if family in {"Long straddle", "Long strangle", "Call backspread", "Put backspread"}:
        return "Long-vol"
    return family


def strategy_family_tokens(strategy: DeltaStrategy) -> set[str]:
    family = strategy.family
    bucket = family_bucket_for_strategy_family(family)
    return {
        normalize_family_token(family),
        normalize_family_token(bucket),
        normalize_family_token(strategy.name),
    }


def strategy_matches_family_filters(
    strategy: DeltaStrategy,
    *,
    family_include_filters: list[str],
    family_exclude_filters: list[str],
) -> bool:
    tokens = strategy_family_tokens(strategy)
    if family_include_filters and not any(token in tokens for token in family_include_filters):
        return False
    if family_exclude_filters and any(token in tokens for token in family_exclude_filters):
        return False
    return True


def summarize_group_contributions(
    *,
    trades_df: pd.DataFrame,
    group_column: str,
    group_values: list[str] | None = None,
) -> list[dict[str, object]]:
    if trades_df.empty or group_column not in trades_df.columns:
        return []
    enriched = trades_df.copy()
    if group_values is not None:
        enriched[group_column] = group_values
    agg_spec: dict[str, tuple[str, str | object]] = {
        "portfolio_net_pnl": ("portfolio_net_pnl", "sum"),
        "trade_count": ("portfolio_net_pnl", "size"),
        "win_rate_pct": ("portfolio_net_pnl", lambda values: (values > 0).mean() * 100.0),
        "avg_trade_pnl": ("portfolio_net_pnl", "mean"),
    }
    if "abs_entry_net_premium" in enriched.columns:
        agg_spec["avg_entry_premium"] = ("abs_entry_net_premium", "mean")
        agg_spec["median_entry_premium"] = ("abs_entry_net_premium", "median")
    if "total_friction_per_combo" in enriched.columns:
        agg_spec["avg_total_friction_per_combo"] = ("total_friction_per_combo", "mean")
    if "friction_pct_of_entry_premium" in enriched.columns:
        agg_spec["avg_friction_pct_of_entry_premium"] = ("friction_pct_of_entry_premium", "mean")
    if "is_sub_030_premium" in enriched.columns:
        agg_spec["sub_030_trade_share_pct"] = ("is_sub_030_premium", lambda values: values.mean() * 100.0)
    grouped = (
        enriched.groupby(group_column, as_index=False)
        .agg(**agg_spec)
        .sort_values(["portfolio_net_pnl", "trade_count"], ascending=[False, False])
        .reset_index(drop=True)
    )
    for column in (
        "portfolio_net_pnl",
        "win_rate_pct",
        "avg_trade_pnl",
        "avg_entry_premium",
        "median_entry_premium",
        "avg_total_friction_per_combo",
        "avg_friction_pct_of_entry_premium",
        "sub_030_trade_share_pct",
    ):
        if column in grouped.columns:
            grouped[column] = grouped[column].round(2)
    return grouped.to_dict(orient="records")


def build_friction_profile(trades_df: pd.DataFrame) -> dict[str, float | int]:
    if trades_df.empty:
        return {
            "trade_count": 0,
            "avg_entry_premium": 0.0,
            "median_entry_premium": 0.0,
            "avg_total_fees_per_combo": 0.0,
            "median_total_fees_per_combo": 0.0,
            "avg_total_friction_per_combo": 0.0,
            "median_total_friction_per_combo": 0.0,
            "avg_friction_pct_of_entry_premium": 0.0,
            "median_friction_pct_of_entry_premium": 0.0,
            "total_broker_commission": 0.0,
            "total_regulatory_fees": 0.0,
            "total_orf_fees": 0.0,
            "total_occ_clearing_fees": 0.0,
            "total_cat_fees": 0.0,
            "total_taf_fees": 0.0,
            "total_fees": 0.0,
            "broker_commission_share_of_total_fees_pct": 0.0,
            "regulatory_fee_share_of_total_fees_pct": 0.0,
            "orf_share_of_total_fees_pct": 0.0,
            "occ_clearing_share_of_total_fees_pct": 0.0,
            "cat_share_of_total_fees_pct": 0.0,
            "taf_share_of_total_fees_pct": 0.0,
            "total_commission": 0.0,
            "total_slippage": 0.0,
            "total_friction": 0.0,
            "friction_share_of_total_premium_pct": 0.0,
            "trade_count_sub_0_15": 0,
            "trade_count_sub_0_30": 0,
            "trade_share_sub_0_15_pct": 0.0,
            "trade_share_sub_0_30_pct": 0.0,
            "net_pnl_sub_0_15": 0.0,
            "net_pnl_sub_0_30": 0.0,
        }
    quantity = trades_df["quantity"] if "quantity" in trades_df.columns else 1.0
    premium_series = trades_df["abs_entry_net_premium"] if "abs_entry_net_premium" in trades_df.columns else pd.Series(0.0, index=trades_df.index)
    total_broker_commission_per_combo = (
        trades_df["total_broker_commission_per_combo"]
        if "total_broker_commission_per_combo" in trades_df.columns
        else pd.Series(0.0, index=trades_df.index)
    )
    total_regulatory_fees_per_combo = (
        trades_df["total_regulatory_fees_per_combo"]
        if "total_regulatory_fees_per_combo" in trades_df.columns
        else pd.Series(0.0, index=trades_df.index)
    )
    total_orf_fees_per_combo = (
        trades_df["total_orf_fees_per_combo"]
        if "total_orf_fees_per_combo" in trades_df.columns
        else pd.Series(0.0, index=trades_df.index)
    )
    total_occ_clearing_fees_per_combo = (
        trades_df["total_occ_clearing_fees_per_combo"]
        if "total_occ_clearing_fees_per_combo" in trades_df.columns
        else pd.Series(0.0, index=trades_df.index)
    )
    total_cat_fees_per_combo = (
        trades_df["total_cat_fees_per_combo"]
        if "total_cat_fees_per_combo" in trades_df.columns
        else pd.Series(0.0, index=trades_df.index)
    )
    total_taf_fees_per_combo = (
        trades_df["total_taf_fees_per_combo"]
        if "total_taf_fees_per_combo" in trades_df.columns
        else pd.Series(0.0, index=trades_df.index)
    )
    total_fees_per_combo = (
        trades_df["total_fees_per_combo"]
        if "total_fees_per_combo" in trades_df.columns
        else trades_df["total_commission_per_combo"]
        if "total_commission_per_combo" in trades_df.columns
        else pd.Series(0.0, index=trades_df.index)
    )
    total_commission_per_combo = trades_df["total_commission_per_combo"] if "total_commission_per_combo" in trades_df.columns else pd.Series(0.0, index=trades_df.index)
    total_slippage_per_combo = trades_df["total_slippage_per_combo"] if "total_slippage_per_combo" in trades_df.columns else pd.Series(0.0, index=trades_df.index)
    total_friction_per_combo = trades_df["total_friction_per_combo"] if "total_friction_per_combo" in trades_df.columns else pd.Series(0.0, index=trades_df.index)
    friction_pct_series = trades_df["friction_pct_of_entry_premium"] if "friction_pct_of_entry_premium" in trades_df.columns else pd.Series(0.0, index=trades_df.index)
    pnl_column = "portfolio_net_pnl" if "portfolio_net_pnl" in trades_df.columns else "net_pnl_per_combo"
    pnl_series = trades_df[pnl_column] if pnl_column in trades_df.columns else pd.Series(0.0, index=trades_df.index)
    sub_015_mask = trades_df["is_sub_015_premium"] if "is_sub_015_premium" in trades_df.columns else (premium_series < 0.15)
    sub_030_mask = trades_df["is_sub_030_premium"] if "is_sub_030_premium" in trades_df.columns else (premium_series < 0.30)
    total_premium_dollars = float((premium_series * 100.0 * quantity).sum())
    total_broker_commission = float((total_broker_commission_per_combo * quantity).sum())
    total_regulatory_fees = float((total_regulatory_fees_per_combo * quantity).sum())
    total_orf_fees = float((total_orf_fees_per_combo * quantity).sum())
    total_occ_clearing_fees = float((total_occ_clearing_fees_per_combo * quantity).sum())
    total_cat_fees = float((total_cat_fees_per_combo * quantity).sum())
    total_taf_fees = float((total_taf_fees_per_combo * quantity).sum())
    total_fees = float((total_fees_per_combo * quantity).sum())
    total_commission = float((total_commission_per_combo * quantity).sum())
    total_slippage = float((total_slippage_per_combo * quantity).sum())
    total_friction = float((total_friction_per_combo * quantity).sum())
    trade_count = int(len(trades_df))
    return {
        "trade_count": trade_count,
        "avg_entry_premium": round(float(premium_series.mean()), 4),
        "median_entry_premium": round(float(premium_series.median()), 4),
        "avg_total_fees_per_combo": round(float(total_fees_per_combo.mean()), 4),
        "median_total_fees_per_combo": round(float(total_fees_per_combo.median()), 4),
        "avg_total_friction_per_combo": round(float(total_friction_per_combo.mean()), 4),
        "median_total_friction_per_combo": round(float(total_friction_per_combo.median()), 4),
        "avg_friction_pct_of_entry_premium": round(float(friction_pct_series.mean()), 2),
        "median_friction_pct_of_entry_premium": round(float(friction_pct_series.median()), 2),
        "total_broker_commission": round(total_broker_commission, 2),
        "total_regulatory_fees": round(total_regulatory_fees, 2),
        "total_orf_fees": round(total_orf_fees, 2),
        "total_occ_clearing_fees": round(total_occ_clearing_fees, 2),
        "total_cat_fees": round(total_cat_fees, 2),
        "total_taf_fees": round(total_taf_fees, 2),
        "total_fees": round(total_fees, 2),
        "broker_commission_share_of_total_fees_pct": round((total_broker_commission / total_fees) * 100.0, 2) if total_fees > 0.0 else 0.0,
        "regulatory_fee_share_of_total_fees_pct": round((total_regulatory_fees / total_fees) * 100.0, 2) if total_fees > 0.0 else 0.0,
        "orf_share_of_total_fees_pct": round((total_orf_fees / total_fees) * 100.0, 2) if total_fees > 0.0 else 0.0,
        "occ_clearing_share_of_total_fees_pct": round((total_occ_clearing_fees / total_fees) * 100.0, 2) if total_fees > 0.0 else 0.0,
        "cat_share_of_total_fees_pct": round((total_cat_fees / total_fees) * 100.0, 2) if total_fees > 0.0 else 0.0,
        "taf_share_of_total_fees_pct": round((total_taf_fees / total_fees) * 100.0, 2) if total_fees > 0.0 else 0.0,
        "total_commission": round(total_commission, 2),
        "total_slippage": round(total_slippage, 2),
        "total_friction": round(total_friction, 2),
        "friction_share_of_total_premium_pct": round((total_friction / total_premium_dollars) * 100.0, 2) if total_premium_dollars > 0.0 else 0.0,
        "trade_count_sub_0_15": int(sub_015_mask.sum()),
        "trade_count_sub_0_30": int(sub_030_mask.sum()),
        "trade_share_sub_0_15_pct": round(float(sub_015_mask.mean() * 100.0), 2),
        "trade_share_sub_0_30_pct": round(float(sub_030_mask.mean() * 100.0), 2),
        "net_pnl_sub_0_15": round(float(pnl_series[sub_015_mask].sum()), 2),
        "net_pnl_sub_0_30": round(float(pnl_series[sub_030_mask].sum()), 2),
    }


def attach_family_contributions(
    *,
    summary: dict[str, object],
    trades_df: pd.DataFrame,
    strategy_map: dict[str, DeltaStrategy] | None,
) -> dict[str, object]:
    enriched = dict(summary)
    if trades_df.empty or not strategy_map:
        enriched["family_contributions"] = []
        enriched["family_bucket_contributions"] = []
        enriched["premium_bucket_contributions"] = []
        enriched["friction_profile"] = build_friction_profile(pd.DataFrame())
        return enriched
    trade_strategies = trades_df["strategy"].astype(str)
    family_values = [
        strategy_map.get(name).family if strategy_map.get(name) is not None else "Unknown"
        for name in trade_strategies
    ]
    family_bucket_values = [
        family_bucket_for_strategy_family(strategy_map.get(name).family) if strategy_map.get(name) is not None else "Unknown"
        for name in trade_strategies
    ]
    enriched["family_contributions"] = summarize_group_contributions(
        trades_df=trades_df,
        group_column="family",
        group_values=family_values,
    )
    enriched["family_bucket_contributions"] = summarize_group_contributions(
        trades_df=trades_df,
        group_column="family_bucket",
        group_values=family_bucket_values,
    )
    enriched["premium_bucket_contributions"] = summarize_group_contributions(
        trades_df=trades_df,
        group_column="premium_bucket",
    )
    enriched["friction_profile"] = build_friction_profile(trades_df)
    return enriched


def contribution_rows_to_frame(rows: list[dict[str, object]], label_column: str) -> pd.DataFrame:
    frame = pd.DataFrame(rows)
    if frame.empty:
        return pd.DataFrame(
            columns=[
                label_column,
                "portfolio_net_pnl",
                "trade_count",
                "win_rate_pct",
                "avg_trade_pnl",
                "avg_entry_premium",
                "median_entry_premium",
                "avg_total_friction_per_combo",
                "avg_friction_pct_of_entry_premium",
                "sub_030_trade_share_pct",
            ]
        )
    return frame


def summarize_run(
    trades_df: pd.DataFrame,
    equity_df: pd.DataFrame,
    starting_equity: float,
    strategy_map: dict[str, DeltaStrategy] | None = None,
) -> dict[str, object]:
    if equity_df.empty:
        final_equity = starting_equity
        max_drawdown_pct = 0.0
    else:
        final_equity = float(equity_df["equity"].iloc[-1])
        peak = equity_df["equity"].cummax()
        drawdown = (equity_df["equity"] / peak) - 1.0
        max_drawdown_pct = float(drawdown.min()) * 100.0
    trade_count = int(len(trades_df))
    win_rate_pct = float((trades_df["portfolio_net_pnl"] > 0).mean() * 100.0) if trade_count > 0 else 0.0
    summary = {
        "starting_equity": starting_equity,
        "final_equity": round(final_equity, 2),
        "total_return_pct": round(((final_equity / starting_equity) - 1.0) * 100.0, 2),
        "trade_count": trade_count,
        "win_rate_pct": round(win_rate_pct, 2),
        "max_drawdown_pct": round(max_drawdown_pct, 2),
    }
    if trade_count > 0:
        contributions = (
            trades_df.groupby("strategy", as_index=False)["portfolio_net_pnl"]
            .sum()
            .sort_values("portfolio_net_pnl", ascending=False)
        )
        summary["strategy_contributions"] = contributions.to_dict(orient="records")
    else:
        summary["strategy_contributions"] = []
    return attach_family_contributions(summary=summary, trades_df=trades_df, strategy_map=strategy_map)


def strategy_objects_from_names(
    selected_names: list[str],
    strategy_map: dict[str, DeltaStrategy],
) -> list[DeltaStrategy]:
    return [strategy_map[name] for name in sorted(set(selected_names)) if name in strategy_map]


def select_best_config(
    *,
    candidate_trades: pd.DataFrame,
    day_return_map: dict[object, float],
    strategy_map: dict[str, DeltaStrategy],
    thresholds: list[float],
    top_bull_values: list[int],
    top_bear_values: list[int],
    top_choppy_values: list[int],
    min_trade_values: list[int],
    risk_caps: list[float],
    selection_profile: str,
) -> dict[str, object]:
    best_row: dict[str, object] | None = None
    cache_by_threshold: dict[float, tuple[pd.DataFrame, pd.DataFrame]] = {}
    for regime_threshold, top_bull, top_bear, top_choppy, min_regime_trades, risk_cap in product(
        thresholds,
        top_bull_values,
        top_bear_values,
        top_choppy_values,
        min_trade_values,
        risk_caps,
    ):
        if regime_threshold not in cache_by_threshold:
            relabeled = relabel_candidate_trades(
                candidate_trades=candidate_trades,
                day_return_map=day_return_map,
                threshold=regime_threshold,
            )
            cache_by_threshold[regime_threshold] = (relabeled, summarize_regimes(relabeled))
        relabeled, regime_summary = cache_by_threshold[regime_threshold]
        selected, selected_rows = select_regime_strategies(
            regime_summary=regime_summary,
            top_bull=top_bull,
            top_bear=top_bear,
            top_choppy=top_choppy,
            min_regime_trades=min_regime_trades,
        )
        filtered = filter_candidate_trades(trades=relabeled, selected=selected)
        selected_names = (
            list(selected["bull"]) + list(selected["bear"]) + list(selected["choppy"])
        )
        strategies = strategy_objects_from_names(selected_names, strategy_map=strategy_map)
        if filtered.empty or not strategies:
            summary = attach_family_contributions(
                summary=empty_summary(starting_equity=DEFAULT_STARTING_EQUITY, risk_cap=risk_cap),
                trades_df=pd.DataFrame(),
                strategy_map=strategy_map,
            )
        else:
            portfolio_trades, _, summary = run_portfolio_allocator(
                strategies=strategies,
                trades_df=filtered,
                portfolio_max_open_risk_fraction=risk_cap,
                starting_equity=DEFAULT_STARTING_EQUITY,
            )
            summary = attach_family_contributions(
                summary=summary,
                trades_df=portfolio_trades,
                strategy_map=strategy_map,
            )
        row = {
            "regime_threshold_pct": regime_threshold,
            "top_bull": top_bull,
            "top_bear": top_bear,
            "top_choppy": top_choppy,
            "selection_profile": selection_profile,
            "min_regime_trades": min_regime_trades,
            "risk_cap": risk_cap,
            "selected_bull": list(selected["bull"]),
            "selected_bear": list(selected["bear"]),
            "selected_choppy": list(selected["choppy"]),
            "selected_summary_rows": selected_rows.to_dict(orient="records"),
            "portfolio_trade_count": int(summary["trade_count"]),
            "final_equity": float(summary["final_equity"]),
            "total_return_pct": float(summary["total_return_pct"]),
            "win_rate_pct": float(summary["win_rate_pct"]),
            "max_drawdown_pct": float(summary["max_drawdown_pct"]),
            "calmar_like": score_drawdown(
                total_return_pct=float(summary["total_return_pct"]),
                max_drawdown_pct=float(summary["max_drawdown_pct"]),
            ),
            "strategy_contributions": list(summary.get("strategy_contributions", [])),
            "family_contributions": list(summary.get("family_contributions", [])),
            "family_bucket_contributions": list(summary.get("family_bucket_contributions", [])),
            "premium_bucket_contributions": list(summary.get("premium_bucket_contributions", [])),
            "friction_profile": dict(summary.get("friction_profile", {})),
        }
        row.update(build_regime_selection_metrics(selected_rows))
        if best_row is None:
            best_row = row
            continue
        if selection_profile == "down_choppy_focus":
            current_tuple = (
                row["total_return_pct"] > 0.0,
                row["bear_trade_count"] > 0,
                row["choppy_trade_count"] > 0,
                row["down_choppy_net_pnl"] > 0.0,
                row["down_choppy_trade_count"] >= 6,
                row["down_choppy_net_pnl"],
                row["calmar_like"],
                row["final_equity"],
                row["portfolio_trade_count"],
            )
            best_tuple = (
                best_row["total_return_pct"] > 0.0,
                best_row["bear_trade_count"] > 0,
                best_row["choppy_trade_count"] > 0,
                best_row["down_choppy_net_pnl"] > 0.0,
                best_row["down_choppy_trade_count"] >= 6,
                best_row["down_choppy_net_pnl"],
                best_row["calmar_like"],
                best_row["final_equity"],
                best_row["portfolio_trade_count"],
            )
        else:
            current_tuple = (
                row["total_return_pct"] > 0.0,
                row["portfolio_trade_count"] >= 10,
                row["calmar_like"],
                row["final_equity"],
                row["portfolio_trade_count"],
            )
            best_tuple = (
                best_row["total_return_pct"] > 0.0,
                best_row["portfolio_trade_count"] >= 10,
                best_row["calmar_like"],
                best_row["final_equity"],
                best_row["portfolio_trade_count"],
            )
        if current_tuple > best_tuple:
            best_row = row
    if best_row is None:
        raise RuntimeError("no config selected")
    return best_row


def evaluate_config(
    *,
    candidate_trades: pd.DataFrame,
    day_return_map: dict[object, float],
    config: dict[str, object],
    strategy_map: dict[str, DeltaStrategy],
    test_dates: set[object],
    starting_equity: float,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, object], pd.DataFrame]:
    test_trades = subset_trades(trades=candidate_trades, dates=test_dates)
    relabeled = relabel_candidate_trades(
        candidate_trades=test_trades,
        day_return_map=day_return_map,
        threshold=float(config["regime_threshold_pct"]),
    )
    selected = {
        "bull": list(config["selected_bull"]),
        "bear": list(config["selected_bear"]),
        "choppy": list(config["selected_choppy"]),
    }
    filtered = filter_candidate_trades(trades=relabeled, selected=selected)
    strategies = strategy_objects_from_names(
        list(selected["bull"]) + list(selected["bear"]) + list(selected["choppy"]),
        strategy_map=strategy_map,
    )
    if filtered.empty or not strategies:
        return (
            filtered.iloc[0:0].copy(),
            empty_equity_curve_df(),
            attach_family_contributions(
                summary=empty_summary(starting_equity, float(config["risk_cap"])),
                trades_df=filtered.iloc[0:0].copy(),
                strategy_map=strategy_map,
            ),
            filtered,
        )
    portfolio_trades, equity_curve, summary = run_portfolio_allocator(
        strategies=strategies,
        trades_df=filtered,
        portfolio_max_open_risk_fraction=float(config["risk_cap"]),
        starting_equity=starting_equity,
    )
    summary = attach_family_contributions(
        summary=summary,
        trades_df=portfolio_trades,
        strategy_map=strategy_map,
    )
    return portfolio_trades, equity_curve, summary, filtered


def promote_config(
    *,
    ticker: str,
    frozen_config: dict[str, object],
    frozen_summary: dict[str, object],
) -> dict[str, object]:
    promoted = {
        "ticker": ticker.upper(),
        "regime_threshold_pct": float(frozen_config["regime_threshold_pct"]),
        "risk_cap": float(frozen_config["risk_cap"]),
        "selected_bull": list(frozen_config["selected_bull"]),
        "selected_bear": list(frozen_config["selected_bear"]),
        "selected_choppy": list(frozen_config["selected_choppy"]),
    }
    positive_contributors = {
        item["strategy"]
        for item in frozen_summary.get("strategy_contributions", [])
        if float(item["portfolio_net_pnl"]) > 0.0
    }
    for regime_key in ["selected_bull", "selected_bear", "selected_choppy"]:
        promoted[regime_key] = [
            name for name in promoted[regime_key] if name in positive_contributors
        ]
    if promoted["selected_bull"] or promoted["selected_bear"] or promoted["selected_choppy"]:
        return promoted
    contributions = list(frozen_summary.get("strategy_contributions", []))
    fallback_name = None
    if contributions:
        fallback_name = str(contributions[0]["strategy"])
    else:
        all_selected = (
            list(frozen_config["selected_bull"])
            + list(frozen_config["selected_bear"])
            + list(frozen_config["selected_choppy"])
        )
        if all_selected:
            fallback_name = str(all_selected[0])
    if fallback_name is not None:
        if fallback_name in frozen_config["selected_bull"]:
            promoted["selected_bull"] = [fallback_name]
        elif fallback_name in frozen_config["selected_bear"]:
            promoted["selected_bear"] = [fallback_name]
        else:
            promoted["selected_choppy"] = [fallback_name]
    return promoted


def run_single_ticker_research(
    *,
    ticker: str,
    output_dir: Path,
    research_dir: Path,
    run_id: str,
    initial_train_days: int,
    test_days: int,
    step_days: int,
    profiles: tuple[TimingProfile, ...],
    strategy_set: str,
    selection_profile: str,
    family_include_filters: list[str],
    family_exclude_filters: list[str],
    execution_calibration_context: dict[str, object],
) -> dict[str, object]:
    ticker_lower = ticker.lower()
    research_dir.mkdir(parents=True, exist_ok=True)
    paths = ticker_artifact_paths(research_dir, ticker_lower)
    wide_path = output_dir / f"{ticker_lower}_365d_option_1min_wide_backtest.parquet"
    dense_path = output_dir / f"{ticker_lower}_365d_option_1min_dense.parquet"
    universe_path = output_dir / f"{ticker_lower}_365d_option_daily_universe.parquet"
    try:
        write_phase_status(
            paths["phase_status"],
            ticker=ticker,
            phase="loading_inputs",
            status="running",
            message="Loading wide, universe, and dense data.",
        )
        wide = load_wide_data_for_ticker(wide_path, ticker_lower)
        _, _, available_dtes = load_daily_universe(universe_path)
        day_contexts = build_day_contexts(wide=wide, available_dtes=available_dtes)
        valid_trade_dates = {ctx.trade_date for ctx in day_contexts}
        chain_index, price_index = load_dense_data(
            path=dense_path,
            valid_trade_dates=valid_trade_dates,
            wide=wide,
        )

        run_signature = build_run_signature(
            ticker=ticker,
            wide_path=wide_path,
            dense_path=dense_path,
            universe_path=universe_path,
            profiles=profiles,
            strategy_set=strategy_set,
            selection_profile=selection_profile,
            initial_train_days=initial_train_days,
            test_days=test_days,
            step_days=step_days,
            family_include_filters=family_include_filters,
            family_exclude_filters=family_exclude_filters,
            execution_calibration_context=execution_calibration_context,
        )

        strategy_variants = build_strategy_variants(
            ticker_lower,
            profiles,
            strategy_set=strategy_set,
            family_include_filters=family_include_filters,
            family_exclude_filters=family_exclude_filters,
        )
        if not strategy_variants:
            raise RuntimeError(f"no strategies remain for {ticker.upper()} after family filtering")
        strategy_map = {strategy.name: strategy for strategy in strategy_variants}

        candidate_trades = try_load_candidate_checkpoint(
            paths=paths,
            run_signature=run_signature,
        )
        if candidate_trades is not None:
            write_phase_status(
                paths["phase_status"],
                ticker=ticker,
                phase="candidate_generation",
                status="reused",
                message="Loaded candidate trades from checkpoint.",
                extra={"candidate_trade_count": int(len(candidate_trades))},
            )
            print(
                f"Resuming {ticker.upper()} from candidate checkpoint with {len(candidate_trades)} trades.",
                flush=True,
            )
        else:
            write_phase_status(
                paths["phase_status"],
                ticker=ticker,
                phase="candidate_generation",
                status="running",
                message="Generating candidate trades.",
            )
            original_dispatch = bqp.SIGNAL_DISPATCH
            try:
                bqp.SIGNAL_DISPATCH = build_signal_dispatch(profiles)
                ticker_started_at = time.perf_counter()

                def _progress_callback(progress: dict[str, object]) -> None:
                    strategy_index = int(progress["strategy_index"])
                    strategy_count = int(progress["strategy_count"])
                    if strategy_index != 1 and strategy_index % 5 != 0 and strategy_index != strategy_count:
                        return
                    print(
                        (
                            f"{ticker.upper()} candidate progress: "
                            f"{strategy_index}/{strategy_count} "
                            f"{progress['strategy_name']} "
                            f"new_trades={int(progress['new_trade_count'])} "
                            f"total_trades={int(progress['trade_count'])} "
                            f"elapsed={float(progress['elapsed_seconds']):.1f}s"
                        ),
                        flush=True,
                    )

                candidate_trades = generate_candidate_trades(
                    strategies=strategy_variants,
                    day_contexts=day_contexts,
                    chain_index=chain_index,
                    price_index=price_index,
                    regime_map=bqp.build_regime_map(wide),
                    progress_callback=_progress_callback,
                )
                print(
                    f"{ticker.upper()} candidate generation complete in {time.perf_counter() - ticker_started_at:.1f}s "
                    f"with {len(candidate_trades)} trades.",
                    flush=True,
                )
            finally:
                bqp.SIGNAL_DISPATCH = original_dispatch

        candidate_trades = enrich_candidate_trades(candidate_trades)
        ordered_trade_dates, day_return_map = build_day_return_map(wide=wide)
        folds = build_folds(
            trade_dates=ordered_trade_dates,
            initial_train_days=initial_train_days,
            test_days=test_days,
            step_days=step_days,
        )
        if not folds:
            raise RuntimeError(f"no folds built for {ticker.upper()}")

        regime_summary = summarize_regimes(candidate_trades)
        candidate_trades.to_csv(paths["candidate_trades"], index=False)
        regime_summary.to_csv(paths["regime_summary"], index=False)
        write_candidate_checkpoint(
            paths=paths,
            run_signature=run_signature,
            candidate_trade_count=len(candidate_trades),
        )
        write_phase_status(
            paths["phase_status"],
            ticker=ticker,
            phase="candidate_generation",
            status="completed",
            message="Candidate trades are ready.",
            extra={"candidate_trade_count": int(len(candidate_trades))},
        )

        selection_grids = apply_execution_calibration_to_selection_grids(
            build_selection_grids(selection_profile, strategy_set),
            execution_calibration_context,
        )
        walkforward_state = try_load_walkforward_checkpoint(
            paths=paths,
            run_signature=run_signature,
        )

        if walkforward_state is not None:
            frozen_config = dict(walkforward_state["frozen_config"])
            completed_folds = set(walkforward_state["completed_folds"])
            fold_rows = list(walkforward_state["fold_rows"])
            reopt_current_equity = float(walkforward_state["reopt_current_equity"])
            frozen_current_equity = float(walkforward_state["frozen_current_equity"])
            reopt_trade_frames = list(walkforward_state["reopt_trade_frames"])
            reopt_equity_frames = list(walkforward_state["reopt_equity_frames"])
            frozen_trade_frames = list(walkforward_state["frozen_trade_frames"])
            frozen_equity_frames = list(walkforward_state["frozen_equity_frames"])
            write_phase_status(
                paths["phase_status"],
                ticker=ticker,
                phase="walkforward",
                status="reused",
                message="Resuming walkforward from checkpoint.",
                extra={"completed_folds": sorted(completed_folds)},
            )
            print(
                f"Resuming {ticker.upper()} walkforward from completed folds {sorted(completed_folds)}.",
                flush=True,
            )
        else:
            train_dates = set(folds[0]["train_dates"])
            write_phase_status(
                paths["phase_status"],
                ticker=ticker,
                phase="config_selection",
                status="running",
                message="Selecting initial frozen config.",
            )
            frozen_config = select_best_config(
                candidate_trades=subset_trades(candidate_trades, train_dates),
                day_return_map=day_return_map,
                strategy_map=strategy_map,
                thresholds=selection_grids["thresholds"],
                top_bull_values=selection_grids["top_bull_values"],
                top_bear_values=selection_grids["top_bear_values"],
                top_choppy_values=selection_grids["top_choppy_values"],
                min_trade_values=selection_grids["min_trade_values"],
                risk_caps=selection_grids["risk_caps"],
                selection_profile=selection_profile,
            )
            completed_folds: set[int] = set()
            reopt_trade_frames = []
            reopt_equity_frames = []
            frozen_trade_frames = []
            frozen_equity_frames = []
            fold_rows = []
            reopt_current_equity = DEFAULT_STARTING_EQUITY
            frozen_current_equity = DEFAULT_STARTING_EQUITY
            write_walkforward_checkpoint(
                paths=paths,
                run_signature=run_signature,
                frozen_config=frozen_config,
                completed_folds=completed_folds,
                fold_rows=fold_rows,
                reopt_current_equity=reopt_current_equity,
                frozen_current_equity=frozen_current_equity,
            )

        for fold in folds:
            if fold["fold"] in completed_folds:
                continue
            write_phase_status(
                paths["phase_status"],
                ticker=ticker,
                phase="walkforward",
                status="running",
                message=f"Running fold {fold['fold']} of {len(folds)}.",
                extra={
                    "current_fold": int(fold["fold"]),
                    "fold_count": len(folds),
                    "completed_folds": sorted(completed_folds),
                },
            )
            reopt_config = select_best_config(
                candidate_trades=subset_trades(candidate_trades, set(fold["train_dates"])),
                day_return_map=day_return_map,
                strategy_map=strategy_map,
                thresholds=selection_grids["thresholds"],
                top_bull_values=selection_grids["top_bull_values"],
                top_bear_values=selection_grids["top_bear_values"],
                top_choppy_values=selection_grids["top_choppy_values"],
                min_trade_values=selection_grids["min_trade_values"],
                risk_caps=selection_grids["risk_caps"],
                selection_profile=selection_profile,
            )
            reopt_trades, reopt_equity, reopt_summary, _ = evaluate_config(
                candidate_trades=candidate_trades,
                day_return_map=day_return_map,
                config=reopt_config,
                strategy_map=strategy_map,
                test_dates=set(fold["test_dates"]),
                starting_equity=reopt_current_equity,
            )
            frozen_trades, frozen_equity, frozen_summary, _ = evaluate_config(
                candidate_trades=candidate_trades,
                day_return_map=day_return_map,
                config=frozen_config,
                strategy_map=strategy_map,
                test_dates=set(fold["test_dates"]),
                starting_equity=frozen_current_equity,
            )
            if not reopt_trades.empty:
                tagged = reopt_trades.copy()
                tagged["fold"] = fold["fold"]
                reopt_trade_frames.append(tagged)
            else:
                tagged = reopt_trades.copy()
                tagged["fold"] = fold["fold"]
                reopt_trade_frames.append(tagged)
            if not reopt_equity.empty:
                tagged = reopt_equity.copy()
                tagged["fold"] = fold["fold"]
                reopt_equity_frames.append(tagged)
            else:
                tagged = reopt_equity.copy()
                tagged["fold"] = fold["fold"]
                reopt_equity_frames.append(tagged)
            if not frozen_trades.empty:
                tagged = frozen_trades.copy()
                tagged["fold"] = fold["fold"]
                frozen_trade_frames.append(tagged)
            else:
                tagged = frozen_trades.copy()
                tagged["fold"] = fold["fold"]
                frozen_trade_frames.append(tagged)
            if not frozen_equity.empty:
                tagged = frozen_equity.copy()
                tagged["fold"] = fold["fold"]
                frozen_equity_frames.append(tagged)
            else:
                tagged = frozen_equity.copy()
                tagged["fold"] = fold["fold"]
                frozen_equity_frames.append(tagged)
            fold_rows.append(
                {
                    "fold": fold["fold"],
                    "train_start": fold["train_dates"][0].isoformat(),
                    "train_end": fold["train_dates"][-1].isoformat(),
                    "test_start": fold["test_dates"][0].isoformat(),
                    "test_end": fold["test_dates"][-1].isoformat(),
                    "reopt_final_equity": reopt_summary["final_equity"],
                    "reopt_return_pct": reopt_summary["total_return_pct"],
                    "frozen_final_equity": frozen_summary["final_equity"],
                    "frozen_return_pct": frozen_summary["total_return_pct"],
                }
            )
            latest_reopt_trades = reopt_trade_frames[-1]
            latest_reopt_equity = reopt_equity_frames[-1]
            latest_frozen_trades = frozen_trade_frames[-1]
            latest_frozen_equity = frozen_equity_frames[-1]
            write_fold_artifacts(
                paths=paths,
                fold_id=int(fold["fold"]),
                reopt_trades=latest_reopt_trades,
                reopt_equity=latest_reopt_equity,
                frozen_trades=latest_frozen_trades,
                frozen_equity=latest_frozen_equity,
            )
            completed_folds.add(int(fold["fold"]))
            reopt_current_equity = float(reopt_summary["final_equity"])
            frozen_current_equity = float(frozen_summary["final_equity"])
            write_walkforward_checkpoint(
                paths=paths,
                run_signature=run_signature,
                frozen_config=frozen_config,
                completed_folds=completed_folds,
                fold_rows=fold_rows,
                reopt_current_equity=reopt_current_equity,
                frozen_current_equity=frozen_current_equity,
            )

        reopt_trade_frames = [frame for frame in reopt_trade_frames if not frame.empty]
        reopt_equity_frames = [frame for frame in reopt_equity_frames if not frame.empty]
        frozen_trade_frames = [frame for frame in frozen_trade_frames if not frame.empty]
        frozen_equity_frames = [frame for frame in frozen_equity_frames if not frame.empty]
        reopt_trades_df = pd.concat(reopt_trade_frames, ignore_index=True) if reopt_trade_frames else bqp.empty_candidate_trades_df()
        reopt_equity_df = pd.concat(reopt_equity_frames, ignore_index=True) if reopt_equity_frames else empty_equity_curve_df()
        frozen_trades_df = pd.concat(frozen_trade_frames, ignore_index=True) if frozen_trade_frames else bqp.empty_candidate_trades_df()
        frozen_equity_df = pd.concat(frozen_equity_frames, ignore_index=True) if frozen_equity_frames else empty_equity_curve_df()
        frozen_summary = summarize_run(
            trades_df=frozen_trades_df,
            equity_df=frozen_equity_df,
            starting_equity=DEFAULT_STARTING_EQUITY,
            strategy_map=strategy_map,
        )
        reoptimized_summary = summarize_run(
            trades_df=reopt_trades_df,
            equity_df=reopt_equity_df,
            starting_equity=DEFAULT_STARTING_EQUITY,
            strategy_map=strategy_map,
        )
        promoted = promote_config(
            ticker=ticker_lower,
            frozen_config=frozen_config,
            frozen_summary=frozen_summary,
        )

        pd.DataFrame(fold_rows).to_csv(paths["walkforward_folds"], index=False)
        frozen_trades_df.to_csv(paths["frozen_trades"], index=False)
        frozen_equity_df.to_csv(paths["frozen_equity"], index=False)
        contribution_rows_to_frame(
            list(frozen_summary.get("family_contributions", [])),
            "family",
        ).to_csv(paths["frozen_family_contributions"], index=False)
        contribution_rows_to_frame(
            list(frozen_summary.get("family_bucket_contributions", [])),
            "family_bucket",
        ).to_csv(paths["frozen_family_bucket_contributions"], index=False)
        contribution_rows_to_frame(
            list(frozen_summary.get("premium_bucket_contributions", [])),
            "premium_bucket",
        ).to_csv(paths["frozen_premium_bucket_contributions"], index=False)
        contribution_rows_to_frame(
            list(reoptimized_summary.get("family_contributions", [])),
            "family",
        ).to_csv(paths["reoptimized_family_contributions"], index=False)
        contribution_rows_to_frame(
            list(reoptimized_summary.get("family_bucket_contributions", [])),
            "family_bucket",
        ).to_csv(paths["reoptimized_family_bucket_contributions"], index=False)
        contribution_rows_to_frame(
            list(reoptimized_summary.get("premium_bucket_contributions", [])),
            "premium_bucket",
        ).to_csv(paths["reoptimized_premium_bucket_contributions"], index=False)
        write_json(paths["frozen_config"], frozen_config)
        write_json(paths["promotion"], promoted)
        summary = {
            "run_id": run_id,
            "ticker": ticker.upper(),
            "trade_date_start": ordered_trade_dates[0].isoformat(),
            "trade_date_end": ordered_trade_dates[-1].isoformat(),
            "day_count": len(ordered_trade_dates),
            "candidate_trade_count": int(len(candidate_trades)),
            "strategy_set": strategy_set,
            "selection_profile": selection_profile,
            "timing_profiles": [profile.name for profile in profiles],
            "family_include_filters": family_include_filters,
            "family_exclude_filters": family_exclude_filters,
            "execution_calibration": execution_calibration_context,
            "selection_grids": selection_grids,
            "frozen_initial_config": frozen_config,
            "reoptimized": reoptimized_summary,
            "frozen_initial": frozen_summary,
            "promoted": promoted,
        }
        write_json(paths["summary"], summary)
        write_phase_status(
            paths["phase_status"],
            ticker=ticker,
            phase="completed",
            status="completed",
            message="Ticker research finished successfully.",
            extra={
                "candidate_trade_count": int(len(candidate_trades)),
                "fold_count": len(folds),
                "frozen_final_equity": float(summary["frozen_initial"]["final_equity"]),
            },
        )
        write_walkforward_checkpoint(
            paths=paths,
            run_signature=run_signature,
            frozen_config=frozen_config,
            completed_folds={int(fold["fold"]) for fold in folds},
            fold_rows=fold_rows,
            reopt_current_equity=reopt_current_equity,
            frozen_current_equity=frozen_current_equity,
        )
        return {
            "ticker": ticker.upper(),
            "candidate_trades": candidate_trades,
            "day_return_map": day_return_map,
            "ordered_trade_dates": ordered_trade_dates,
            "strategy_map": strategy_map,
            "regime_summary": regime_summary,
            "summary": summary,
        }
    except Exception as exc:
        write_phase_status(
            paths["phase_status"],
            ticker=ticker,
            phase="failed",
            status="failed",
            message=f"{type(exc).__name__}: {exc}",
        )
        raise


def try_load_existing_ticker_result(
    *,
    ticker: str,
    output_dir: Path,
    research_dir: Path,
    profiles: tuple[TimingProfile, ...],
    strategy_set: str,
    selection_profile: str,
    family_include_filters: list[str],
    family_exclude_filters: list[str],
    execution_calibration_context: dict[str, object],
) -> dict[str, object] | None:
    ticker_lower = ticker.lower()
    summary_path = research_dir / f"{ticker_lower}_summary.json"
    candidate_trades_path = research_dir / f"{ticker_lower}_candidate_trades.csv"
    regime_summary_path = research_dir / f"{ticker_lower}_regime_summary.csv"
    wide_path = output_dir / f"{ticker_lower}_365d_option_1min_wide_backtest.parquet"

    if not summary_path.exists() or not candidate_trades_path.exists() or not wide_path.exists():
        return None

    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    expected_profiles = [profile.name for profile in profiles]
    if summary.get("timing_profiles") != expected_profiles:
        return None
    if summary.get("strategy_set", "standard") != strategy_set:
        return None
    if summary.get("selection_profile", DEFAULT_SELECTION_PROFILE) != selection_profile:
        return None
    if summary.get("family_include_filters", []) != family_include_filters:
        return None
    if summary.get("family_exclude_filters", []) != family_exclude_filters:
        return None
    if summary.get("execution_calibration") != execution_calibration_context:
        return None

    strategy_variants = build_strategy_variants(
        ticker_lower,
        profiles,
        strategy_set=strategy_set,
        family_include_filters=family_include_filters,
        family_exclude_filters=family_exclude_filters,
    )
    strategy_map = {strategy.name: strategy for strategy in strategy_variants}
    promoted = summary.get("promoted", {})
    selected_names = (
        list(promoted.get("selected_bull", []))
        + list(promoted.get("selected_bear", []))
        + list(promoted.get("selected_choppy", []))
    )
    if any(name not in strategy_map for name in selected_names):
        return None

    candidate_trades = read_candidate_trades_csv(candidate_trades_path)
    regime_summary = (
        summarize_regimes(candidate_trades)
        if not regime_summary_path.exists()
        else (
            pd.read_csv(regime_summary_path)
            if regime_summary_path.stat().st_size > 0
            else summarize_regimes(candidate_trades)
        )
    )
    wide = load_wide_data_for_ticker(wide_path, ticker_lower)
    ordered_trade_dates, day_return_map = build_day_return_map(wide=wide)
    return {
        "ticker": ticker.upper(),
        "candidate_trades": candidate_trades,
        "day_return_map": day_return_map,
        "ordered_trade_dates": ordered_trade_dates,
        "strategy_map": strategy_map,
        "regime_summary": regime_summary,
        "summary": summary,
        "reused_existing": True,
    }


def build_combined_promoted_candidates(
    *,
    ticker_results: list[dict[str, object]],
    oos_dates: set[object],
) -> tuple[pd.DataFrame, dict[str, DeltaStrategy]]:
    filtered_frames: list[pd.DataFrame] = []
    strategy_map: dict[str, DeltaStrategy] = {}
    for result in ticker_results:
        promoted = result["summary"]["promoted"]
        selected = {
            "bull": list(promoted["selected_bull"]),
            "bear": list(promoted["selected_bear"]),
            "choppy": list(promoted["selected_choppy"]),
        }
        candidate_trades = subset_trades(result["candidate_trades"], oos_dates)
        relabeled = relabel_candidate_trades(
            candidate_trades=candidate_trades,
            day_return_map=result["day_return_map"],
            threshold=float(promoted["regime_threshold_pct"]),
        )
        filtered = filter_candidate_trades(trades=relabeled, selected=selected)
        if not filtered.empty:
            filtered_frames.append(filtered)
        selected_names = list(selected["bull"]) + list(selected["bear"]) + list(selected["choppy"])
        for name in selected_names:
            strategy_map[name] = result["strategy_map"][name]
    combined = pd.concat(filtered_frames, ignore_index=True) if filtered_frames else bqp.empty_candidate_trades_df()
    if not combined.empty:
        combined = combined.sort_values(["trade_date", "entry_minute", "strategy"]).reset_index(drop=True)
    return combined, strategy_map


def optimize_shared_portfolio(
    *,
    candidate_trades: pd.DataFrame,
    strategy_map: dict[str, DeltaStrategy],
    risk_caps: list[float],
) -> tuple[dict[str, object], pd.DataFrame, pd.DataFrame]:
    best_summary: dict[str, object] | None = None
    best_trades = bqp.empty_candidate_trades_df()
    best_equity = pd.DataFrame()
    for risk_cap in risk_caps:
        if candidate_trades.empty or "strategy" not in candidate_trades.columns:
            summary = attach_family_contributions(
                summary=empty_summary(DEFAULT_STARTING_EQUITY, risk_cap),
                trades_df=bqp.empty_candidate_trades_df(),
                strategy_map=strategy_map,
            )
            trades = bqp.empty_candidate_trades_df()
            equity = pd.DataFrame()
        else:
            strategies = strategy_objects_from_names(candidate_trades["strategy"].tolist(), strategy_map)
            if not strategies:
                summary = attach_family_contributions(
                    summary=empty_summary(DEFAULT_STARTING_EQUITY, risk_cap),
                    trades_df=bqp.empty_candidate_trades_df(),
                    strategy_map=strategy_map,
                )
                trades = bqp.empty_candidate_trades_df()
                equity = pd.DataFrame()
            else:
                trades, equity, summary = run_portfolio_allocator(
                    strategies=strategies,
                    trades_df=candidate_trades,
                    portfolio_max_open_risk_fraction=risk_cap,
                    starting_equity=DEFAULT_STARTING_EQUITY,
                )
                summary = attach_family_contributions(
                    summary=summary,
                    trades_df=trades,
                    strategy_map=strategy_map,
                )
        row = {
            "risk_cap": risk_cap,
            "final_equity": float(summary["final_equity"]),
            "total_return_pct": float(summary["total_return_pct"]),
            "trade_count": int(summary["trade_count"]),
            "win_rate_pct": float(summary["win_rate_pct"]),
            "max_drawdown_pct": float(summary["max_drawdown_pct"]),
            "calmar_like": score_drawdown(
                total_return_pct=float(summary["total_return_pct"]),
                max_drawdown_pct=float(summary["max_drawdown_pct"]),
            ),
            "strategy_contributions": list(summary.get("strategy_contributions", [])),
            "family_contributions": list(summary.get("family_contributions", [])),
            "family_bucket_contributions": list(summary.get("family_bucket_contributions", [])),
            "premium_bucket_contributions": list(summary.get("premium_bucket_contributions", [])),
            "friction_profile": dict(summary.get("friction_profile", {})),
        }
        if best_summary is None:
            best_summary = row
            best_trades = trades
            best_equity = equity
            continue
        current_tuple = (
            row["total_return_pct"] > 0.0,
            row["calmar_like"],
            row["final_equity"],
            row["trade_count"],
        )
        best_tuple = (
            best_summary["total_return_pct"] > 0.0,
            best_summary["calmar_like"],
            best_summary["final_equity"],
            best_summary["trade_count"],
        )
        if current_tuple > best_tuple:
            best_summary = row
            best_trades = trades
            best_equity = equity
    if best_summary is None:
        raise RuntimeError("shared portfolio optimization produced no result")
    return best_summary, best_trades, best_equity


def build_family_ranking_rows(
    *,
    scope: str,
    ticker: str | None,
    summary: dict[str, object],
    contribution_key: str,
    label_key: str,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for item in summary.get(contribution_key, []):
        rows.append(
            {
                "scope": scope,
                "ticker": ticker or "",
                label_key: item.get(label_key, ""),
                "portfolio_net_pnl": float(item.get("portfolio_net_pnl", 0.0)),
                "trade_count": int(item.get("trade_count", 0)),
                "win_rate_pct": float(item.get("win_rate_pct", 0.0)),
                "avg_trade_pnl": float(item.get("avg_trade_pnl", 0.0)),
                "avg_entry_premium": float(item.get("avg_entry_premium", 0.0)),
                "median_entry_premium": float(item.get("median_entry_premium", 0.0)),
                "avg_total_friction_per_combo": float(item.get("avg_total_friction_per_combo", 0.0)),
                "avg_friction_pct_of_entry_premium": float(item.get("avg_friction_pct_of_entry_premium", 0.0)),
                "sub_030_trade_share_pct": float(item.get("sub_030_trade_share_pct", 0.0)),
            }
        )
    return rows


def write_master_report(path: Path, payload: dict[str, object]) -> None:
    lines: list[str] = []
    failed_tickers = list(payload.get("failed_tickers", []))
    lines.append("# Multi-Ticker Cleanroom Portfolio Report")
    lines.append("")
    lines.append(
        f"- Tickers tested: {', '.join(payload['tickers'])}"
    )
    lines.append(
        f"- Training window: {payload['initial_train_days']} days, test window: {payload['test_days']} days, step: {payload['step_days']} days."
    )
    lines.append(f"- Selection profile: {payload.get('selection_profile', DEFAULT_SELECTION_PROFILE)}")
    execution_calibration = dict(payload.get("execution_calibration", {}))
    if execution_calibration.get("enabled"):
        adjustments = dict(execution_calibration.get("selection_adjustments", {}))
        lines.append(
            f"- Execution calibration: `{execution_calibration.get('overall_execution_posture', 'unknown')}` posture with `{execution_calibration.get('evidence_strength', 'unknown')}` evidence; threshold shift {adjustments.get('threshold_shift', 0.0):.2f}, min-trade increment {adjustments.get('min_trade_increment', 0)}, risk-cap multiplier {adjustments.get('risk_cap_multiplier', 1.0):.2f}."
        )
    else:
        lines.append("- Execution calibration: unavailable; static selection grids were used.")
    lines.append(
        f"- Successful tickers: {', '.join(payload.get('successful_tickers', [])) if payload.get('successful_tickers') else 'none'}"
    )
    lines.append(
        f"- Failed tickers: {', '.join(row['ticker'] for row in failed_tickers) if failed_tickers else 'none'}"
    )
    lines.append("")
    lines.append("## Promoted Strategies")
    lines.append("")
    for row in payload["ticker_promotions"]:
        lines.append(f"### {row['ticker']}")
        lines.append(
            f"- Bull: {', '.join(f'`{name}`' for name in row['selected_bull']) if row['selected_bull'] else 'none'}"
        )
        lines.append(
            f"- Bear: {', '.join(f'`{name}`' for name in row['selected_bear']) if row['selected_bear'] else 'none'}"
        )
        lines.append(
            f"- Choppy: {', '.join(f'`{name}`' for name in row['selected_choppy']) if row['selected_choppy'] else 'none'}"
        )
        lines.append(
            f"- OOS frozen result: ${row['frozen_final_equity']:.2f}, {row['frozen_total_return_pct']:.2f}%, drawdown {row['frozen_max_drawdown_pct']:.2f}%."
        )
        lines.append("")
    lines.append("## Shared Account")
    lines.append("")
    shared = payload["shared_account"]
    qqq_only = payload.get("qqq_only")
    lines.append(
        f"- Combined promoted book: ${shared['final_equity']:.2f}, {shared['total_return_pct']:.2f}%, drawdown {shared['max_drawdown_pct']:.2f}%, risk cap {shared['risk_cap'] * 100:.0f}%."
    )
    if qqq_only is None:
        lines.append("- QQQ-only promoted book: unavailable for this batch.")
        lines.append("- Relative lift vs QQQ-only: unavailable for this batch.")
    else:
        lines.append(
            f"- QQQ-only promoted book: ${qqq_only['final_equity']:.2f}, {qqq_only['total_return_pct']:.2f}%, drawdown {qqq_only['max_drawdown_pct']:.2f}%, risk cap {qqq_only['risk_cap'] * 100:.0f}%."
        )
        lines.append(
            f"- Relative lift vs QQQ-only: {payload['relative_return_vs_qqq_only_pct']:.2f} percentage points."
        )
    family_rankings = payload.get("family_rankings", {})
    premium_bucket_rankings = payload.get("premium_bucket_rankings", {})
    friction_profiles = payload.get("friction_profiles", {})
    shared_buckets = list(family_rankings.get("shared_account_buckets", []))
    qqq_buckets = list(family_rankings.get("qqq_only_buckets", []))
    per_ticker_buckets = list(family_rankings.get("per_ticker_frozen_buckets", []))
    shared_premium_buckets = list(premium_bucket_rankings.get("shared_account_buckets", []))
    qqq_premium_buckets = list(premium_bucket_rankings.get("qqq_only_buckets", []))
    shared_friction = dict(friction_profiles.get("shared_account", {}))
    lines.append("")
    lines.append("## Family Leaders")
    lines.append("")
    lines.append("### Shared Account Buckets")
    lines.append("")
    if shared_buckets:
        for row in shared_buckets:
            lines.append(
                f"- `{row['family_bucket']}`: ${row['portfolio_net_pnl']:.2f} across {row['trade_count']} trades, win rate {row['win_rate_pct']:.2f}%."
            )
    else:
        lines.append("- none")
    lines.append("")
    lines.append("### QQQ-Only Buckets")
    lines.append("")
    if qqq_buckets:
        for row in qqq_buckets:
            lines.append(
                f"- `{row['family_bucket']}`: ${row['portfolio_net_pnl']:.2f} across {row['trade_count']} trades, win rate {row['win_rate_pct']:.2f}%."
            )
    else:
        lines.append("- none")
    lines.append("")
    lines.append("### Per-Ticker Frozen Leaders")
    lines.append("")
    if per_ticker_buckets:
        for row in per_ticker_buckets:
            lines.append(
                f"- `{row['ticker']}` / `{row['family_bucket']}`: ${row['portfolio_net_pnl']:.2f} across {row['trade_count']} trades, win rate {row['win_rate_pct']:.2f}%."
            )
    else:
        lines.append("- none")
    lines.append("")
    lines.append("## Friction Profile")
    lines.append("")
    if shared_friction:
        lines.append(
            f"- Shared median entry premium: ${shared_friction.get('median_entry_premium', 0.0):.4f}; average total friction/combo: ${shared_friction.get('avg_total_friction_per_combo', 0.0):.2f}; sub-$0.30 share: {shared_friction.get('trade_share_sub_0_30_pct', 0.0):.2f}%."
        )
        lines.append(
            f"- Shared total friction paid: ${shared_friction.get('total_friction', 0.0):.2f} on ${shared_friction.get('total_fees', shared_friction.get('total_commission', 0.0)):.2f} fees and ${shared_friction.get('total_slippage', 0.0):.2f} slippage."
        )
        lines.append(
            f"- Fee mix: regulatory ${shared_friction.get('total_regulatory_fees', 0.0):.2f} ({shared_friction.get('regulatory_fee_share_of_total_fees_pct', 0.0):.2f}%), "
            f"ORF ${shared_friction.get('total_orf_fees', 0.0):.2f}, OCC ${shared_friction.get('total_occ_clearing_fees', 0.0):.2f}, "
            f"CAT ${shared_friction.get('total_cat_fees', 0.0):.2f}, TAF ${shared_friction.get('total_taf_fees', 0.0):.2f}."
        )
    else:
        lines.append("- none")
    lines.append("")
    lines.append("### Shared Account Premium Buckets")
    lines.append("")
    if shared_premium_buckets:
        for row in shared_premium_buckets:
            lines.append(
                f"- `{row['premium_bucket']}`: ${row['portfolio_net_pnl']:.2f} across {row['trade_count']} trades, win rate {row['win_rate_pct']:.2f}%, avg friction {row.get('avg_total_friction_per_combo', 0.0):.2f}."
            )
    else:
        lines.append("- none")
    lines.append("")
    lines.append("### QQQ-Only Premium Buckets")
    lines.append("")
    if qqq_premium_buckets:
        for row in qqq_premium_buckets:
            lines.append(
                f"- `{row['premium_bucket']}`: ${row['portfolio_net_pnl']:.2f} across {row['trade_count']} trades, win rate {row['win_rate_pct']:.2f}%, avg friction {row.get('avg_total_friction_per_combo', 0.0):.2f}."
            )
    else:
        lines.append("- none")
    if failed_tickers:
        lines.append("")
        lines.append("## Failed Tickers")
        lines.append("")
        for row in failed_tickers:
            lines.append(
                f"- `{row['ticker']}`: {row['error_type']} - {row['message']}"
            )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = build_parser().parse_args()
    output_dir = Path(args.output_dir).resolve()
    research_dir = Path(args.research_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    research_dir.mkdir(parents=True, exist_ok=True)
    execution_calibration_handoff_path = resolve_execution_calibration_handoff_path(args.execution_calibration_handoff)
    execution_calibration_context = build_execution_calibration_context(execution_calibration_handoff_path)
    tickers = [ticker.strip().lower() for ticker in args.tickers.split(",") if ticker.strip()]
    profiles = build_timing_profiles(args.strategy_set)
    family_include_filters = parse_family_filters(args.family_include)
    family_exclude_filters = parse_family_filters(args.family_exclude)
    run_id = build_run_id(
        tickers=tickers,
        strategy_set=args.strategy_set,
        selection_profile=args.selection_profile,
        research_dir=research_dir,
    )
    manifest_path = research_dir / "run_manifest.json"
    registry_path = output_dir / "run_registry.jsonl"
    run_manifest: dict[str, object] = {
        "version": RUN_MANIFEST_VERSION,
        "run_id": run_id,
        "status": "running",
        "created_at_iso": utc_now_iso(),
        "research_dir": str(research_dir),
        "output_dir": str(output_dir),
        "parameters": {
            "tickers": [ticker.upper() for ticker in tickers],
            "strategy_set": args.strategy_set,
            "selection_profile": args.selection_profile,
            "initial_train_days": int(args.initial_train_days),
            "test_days": int(args.test_days),
            "step_days": int(args.step_days),
            "timing_profiles": [profile.name for profile in profiles],
            "family_include_filters": family_include_filters,
            "family_exclude_filters": family_exclude_filters,
            "execution_calibration_handoff": str(execution_calibration_handoff_path) if execution_calibration_handoff_path is not None else None,
            "execution_calibration": execution_calibration_context,
            "continue_on_error": bool(args.continue_on_error),
            "reuse_completed_tickers": bool(args.reuse_completed_tickers),
            "argv": sys.argv,
        },
        "lineage": {
            "machine": collect_machine_lineage(),
            "code": collect_code_lineage(),
            "execution_calibration_handoff": file_lineage_descriptor(execution_calibration_handoff_path, prefer_full_hash=True)
            if execution_calibration_handoff_path is not None
            else None,
            "ticker_inputs": {
                ticker.upper(): ticker_input_lineage(output_dir, ticker)
                for ticker in tickers
            },
        },
        "ticker_states": {
            ticker.upper(): {
                "status": "pending",
                "updated_at_iso": utc_now_iso(),
            }
            for ticker in tickers
        },
        "result_snapshot": {},
        "master_outputs": {},
    }

    def sync_manifest(*, status: str | None = None, message: str | None = None) -> None:
        if status is not None:
            run_manifest["status"] = status
        if message is not None:
            run_manifest["message"] = message
        write_run_manifest(manifest_path, run_manifest)

    sync_manifest(status="running", message="Run initialized.")
    if execution_calibration_context.get("enabled"):
        print(
            "Execution calibration active: "
            f"{execution_calibration_context.get('overall_execution_posture', 'unknown')} posture, "
            f"{execution_calibration_context.get('evidence_strength', 'unknown')} evidence.",
            flush=True,
        )
    append_run_registry(
        registry_path,
        {
            "version": RUN_MANIFEST_VERSION,
            "event": "started",
            "timestamp_iso": utc_now_iso(),
            "run_id": run_id,
            "status": "running",
            "research_dir": str(research_dir),
            "tickers": [ticker.upper() for ticker in tickers],
            "strategy_set": args.strategy_set,
            "selection_profile": args.selection_profile,
            "execution_calibration": execution_calibration_context,
            "timing_profiles": [profile.name for profile in profiles],
            "family_include_filters": family_include_filters,
            "family_exclude_filters": family_exclude_filters,
            "continue_on_error": bool(args.continue_on_error),
            "reuse_completed_tickers": bool(args.reuse_completed_tickers),
            "hostname": socket.gethostname(),
        },
    )

    ticker_results: list[dict[str, object]] = []
    failed_tickers: list[dict[str, object]] = []
    for ticker in tickers:
        ticker_key = ticker.upper()
        run_manifest["ticker_states"][ticker_key] = {
            "status": "running",
            "phase": "ticker_research",
            "updated_at_iso": utc_now_iso(),
        }
        sync_manifest(message=f"Running {ticker_key} research.")
        if args.reuse_completed_tickers:
            reused = try_load_existing_ticker_result(
                ticker=ticker,
                output_dir=output_dir,
                research_dir=research_dir,
                profiles=profiles,
                strategy_set=args.strategy_set,
                selection_profile=args.selection_profile,
                family_include_filters=family_include_filters,
                family_exclude_filters=family_exclude_filters,
                execution_calibration_context=execution_calibration_context,
            )
            if reused is not None:
                ticker_results.append(reused)
                run_manifest["ticker_states"][ticker_key] = {
                    "status": "reused_existing",
                    "updated_at_iso": utc_now_iso(),
                    "summary_path": str((research_dir / f"{ticker.lower()}_summary.json").resolve()),
                    "output_lineage": collect_ticker_output_lineage(research_dir, ticker),
                }
                sync_manifest(message=f"Reused {ticker_key} existing results.")
                print(
                    f"Reusing {ticker.upper()} existing results from {research_dir}.",
                    flush=True,
                )
                continue
        print(f"Running {ticker.upper()} research...", flush=True)
        try:
            result = run_single_ticker_research(
                ticker=ticker,
                output_dir=output_dir,
                research_dir=research_dir,
                run_id=run_id,
                initial_train_days=args.initial_train_days,
                test_days=args.test_days,
                step_days=args.step_days,
                profiles=profiles,
                strategy_set=args.strategy_set,
                selection_profile=args.selection_profile,
                family_include_filters=family_include_filters,
                family_exclude_filters=family_exclude_filters,
                execution_calibration_context=execution_calibration_context,
            )
        except Exception as exc:
            error_row = {
                "ticker": ticker.upper(),
                "error_type": type(exc).__name__,
                "message": str(exc),
            }
            failed_tickers.append(error_row)
            run_manifest["ticker_states"][ticker_key] = {
                "status": "failed",
                "updated_at_iso": utc_now_iso(),
                "error_type": type(exc).__name__,
                "message": str(exc),
                "output_lineage": collect_ticker_output_lineage(research_dir, ticker),
            }
            sync_manifest(message=f"{ticker_key} failed.")
            print(
                f"{ticker.upper()} failed: {type(exc).__name__}: {exc}",
                flush=True,
            )
            if not args.continue_on_error:
                run_manifest["result_snapshot"] = {
                    "successful_tickers": [result["ticker"] for result in ticker_results],
                    "failed_tickers": failed_tickers,
                }
                sync_manifest(status="failed", message=f"{ticker_key} failed and stopped the run.")
                append_run_registry(
                    registry_path,
                    {
                        "version": RUN_MANIFEST_VERSION,
                        "event": "failed",
                        "timestamp_iso": utc_now_iso(),
                        "run_id": run_id,
                        "status": "failed",
                        "research_dir": str(research_dir),
                        "successful_tickers": [result["ticker"] for result in ticker_results],
                        "failed_tickers": failed_tickers,
                        "error_type": type(exc).__name__,
                        "message": str(exc),
                    },
                )
                raise
            continue
        ticker_results.append(result)
        run_manifest["ticker_states"][ticker_key] = {
            "status": "completed",
            "updated_at_iso": utc_now_iso(),
            "summary_path": str((research_dir / f"{ticker.lower()}_summary.json").resolve()),
            "candidate_trade_count": int(result["summary"]["candidate_trade_count"]),
            "frozen_final_equity": float(result["summary"]["frozen_initial"]["final_equity"]),
            "output_lineage": collect_ticker_output_lineage(research_dir, ticker),
        }
        sync_manifest(message=f"{ticker_key} complete.")
        print(
            f"{ticker.upper()} complete: frozen ${result['summary']['frozen_initial']['final_equity']:.2f}",
            flush=True,
        )

    if not ticker_results:
        run_manifest["result_snapshot"] = {
            "successful_tickers": [],
            "failed_tickers": failed_tickers,
        }
        sync_manifest(status="failed", message="All requested tickers failed research.")
        append_run_registry(
            registry_path,
            {
                "version": RUN_MANIFEST_VERSION,
                "event": "failed",
                "timestamp_iso": utc_now_iso(),
                "run_id": run_id,
                "status": "failed",
                "research_dir": str(research_dir),
                "successful_tickers": [],
                "failed_tickers": failed_tickers,
                "error_type": "RuntimeError",
                "message": "all requested tickers failed research",
            },
        )
        raise RuntimeError("all requested tickers failed research")

    common_dates = set(ticker_results[0]["ordered_trade_dates"][args.initial_train_days :])
    combined_candidates, combined_strategy_map = build_combined_promoted_candidates(
        ticker_results=ticker_results,
        oos_dates=common_dates,
    )
    combined_summary, combined_trades, combined_equity = optimize_shared_portfolio(
        candidate_trades=combined_candidates,
        strategy_map=combined_strategy_map,
        risk_caps=[0.08, 0.10, 0.12, 0.15],
    )

    qqq_result = next((result for result in ticker_results if result["ticker"] == "QQQ"), None)
    if qqq_result is None:
        qqq_candidates = pd.DataFrame()
        qqq_trades = pd.DataFrame()
        qqq_equity = pd.DataFrame()
        qqq_summary = None
    else:
        qqq_candidates, qqq_strategy_map = build_combined_promoted_candidates(
            ticker_results=[qqq_result],
            oos_dates=common_dates,
        )
        qqq_summary, qqq_trades, qqq_equity = optimize_shared_portfolio(
            candidate_trades=qqq_candidates,
            strategy_map=qqq_strategy_map,
            risk_caps=[0.08, 0.10, 0.12, 0.15],
        )

    ticker_promotions: list[dict[str, object]] = []
    family_detail_rows: list[dict[str, object]] = []
    family_bucket_rows: list[dict[str, object]] = []
    per_ticker_frozen_bucket_leaders: list[dict[str, object]] = []
    premium_bucket_rows: list[dict[str, object]] = []
    per_ticker_frozen_premium_leaders: list[dict[str, object]] = []
    for result in ticker_results:
        summary = result["summary"]
        promoted = summary["promoted"]
        ticker_promotions.append(
            {
                "ticker": result["ticker"],
                "selected_bull": list(promoted["selected_bull"]),
                "selected_bear": list(promoted["selected_bear"]),
                "selected_choppy": list(promoted["selected_choppy"]),
                "regime_threshold_pct": float(promoted["regime_threshold_pct"]),
                "frozen_final_equity": float(summary["frozen_initial"]["final_equity"]),
                "frozen_total_return_pct": float(summary["frozen_initial"]["total_return_pct"]),
                "frozen_max_drawdown_pct": float(summary["frozen_initial"]["max_drawdown_pct"]),
            }
        )
        family_detail_rows.extend(
            build_family_ranking_rows(
                scope="ticker_frozen",
                ticker=result["ticker"],
                summary=summary["frozen_initial"],
                contribution_key="family_contributions",
                label_key="family",
            )
        )
        family_detail_rows.extend(
            build_family_ranking_rows(
                scope="ticker_reoptimized",
                ticker=result["ticker"],
                summary=summary["reoptimized"],
                contribution_key="family_contributions",
                label_key="family",
            )
        )
        family_bucket_rows.extend(
            build_family_ranking_rows(
                scope="ticker_frozen",
                ticker=result["ticker"],
                summary=summary["frozen_initial"],
                contribution_key="family_bucket_contributions",
                label_key="family_bucket",
            )
        )
        family_bucket_rows.extend(
            build_family_ranking_rows(
                scope="ticker_reoptimized",
                ticker=result["ticker"],
                summary=summary["reoptimized"],
                contribution_key="family_bucket_contributions",
                label_key="family_bucket",
            )
        )
        premium_bucket_rows.extend(
            build_family_ranking_rows(
                scope="ticker_frozen",
                ticker=result["ticker"],
                summary=summary["frozen_initial"],
                contribution_key="premium_bucket_contributions",
                label_key="premium_bucket",
            )
        )
        premium_bucket_rows.extend(
            build_family_ranking_rows(
                scope="ticker_reoptimized",
                ticker=result["ticker"],
                summary=summary["reoptimized"],
                contribution_key="premium_bucket_contributions",
                label_key="premium_bucket",
            )
        )
        top_bucket = list(summary["frozen_initial"].get("family_bucket_contributions", []))
        if top_bucket:
            leader = dict(top_bucket[0])
            leader["ticker"] = result["ticker"]
            per_ticker_frozen_bucket_leaders.append(leader)
        top_premium_bucket = list(summary["frozen_initial"].get("premium_bucket_contributions", []))
        if top_premium_bucket:
            leader = dict(top_premium_bucket[0])
            leader["ticker"] = result["ticker"]
            per_ticker_frozen_premium_leaders.append(leader)

    family_detail_rows.extend(
        build_family_ranking_rows(
            scope="shared_account",
            ticker=None,
            summary=combined_summary,
            contribution_key="family_contributions",
            label_key="family",
        )
    )
    if qqq_summary is not None:
        family_detail_rows.extend(
            build_family_ranking_rows(
                scope="qqq_only",
                ticker="QQQ",
                summary=qqq_summary,
                contribution_key="family_contributions",
                label_key="family",
            )
        )
    family_bucket_rows.extend(
        build_family_ranking_rows(
                scope="shared_account",
                ticker=None,
                summary=combined_summary,
                contribution_key="family_bucket_contributions",
                label_key="family_bucket",
        )
    )
    if qqq_summary is not None:
        family_bucket_rows.extend(
            build_family_ranking_rows(
                scope="qqq_only",
                ticker="QQQ",
                summary=qqq_summary,
                contribution_key="family_bucket_contributions",
                label_key="family_bucket",
            )
        )
    premium_bucket_rows.extend(
        build_family_ranking_rows(
            scope="shared_account",
            ticker=None,
            summary=combined_summary,
            contribution_key="premium_bucket_contributions",
            label_key="premium_bucket",
        )
    )
    if qqq_summary is not None:
        premium_bucket_rows.extend(
            build_family_ranking_rows(
                scope="qqq_only",
                ticker="QQQ",
                summary=qqq_summary,
                contribution_key="premium_bucket_contributions",
                label_key="premium_bucket",
            )
        )

    family_detail_rows = sorted(
        family_detail_rows,
        key=lambda row: (row["scope"], -row["portfolio_net_pnl"], -row["trade_count"]),
    )
    family_bucket_rows = sorted(
        family_bucket_rows,
        key=lambda row: (row["scope"], -row["portfolio_net_pnl"], -row["trade_count"]),
    )
    per_ticker_frozen_bucket_leaders = sorted(
        per_ticker_frozen_bucket_leaders,
        key=lambda row: (-float(row["portfolio_net_pnl"]), -int(row["trade_count"])),
    )
    premium_bucket_rows = sorted(
        premium_bucket_rows,
        key=lambda row: (row["scope"], -row["portfolio_net_pnl"], -row["trade_count"]),
    )
    per_ticker_frozen_premium_leaders = sorted(
        per_ticker_frozen_premium_leaders,
        key=lambda row: (-float(row["portfolio_net_pnl"]), -int(row["trade_count"])),
    )

    master_payload = {
        "run_id": run_id,
        "tickers": [ticker.upper() for ticker in tickers],
        "strategy_set": args.strategy_set,
        "selection_profile": args.selection_profile,
        "family_include_filters": family_include_filters,
        "family_exclude_filters": family_exclude_filters,
        "execution_calibration": execution_calibration_context,
        "successful_tickers": [result["ticker"] for result in ticker_results],
        "failed_tickers": failed_tickers,
        "initial_train_days": args.initial_train_days,
        "test_days": args.test_days,
        "step_days": args.step_days,
        "ticker_promotions": ticker_promotions,
        "shared_account": combined_summary,
        "qqq_only": qqq_summary,
        "relative_return_vs_qqq_only_pct": round(
            float(combined_summary["total_return_pct"]) - float(qqq_summary["total_return_pct"]),
            2,
        ) if qqq_summary is not None else None,
        "family_rankings": {
            "shared_account_families": list(combined_summary.get("family_contributions", [])),
            "shared_account_buckets": list(combined_summary.get("family_bucket_contributions", [])),
            "qqq_only_families": list(qqq_summary.get("family_contributions", [])) if qqq_summary is not None else [],
            "qqq_only_buckets": list(qqq_summary.get("family_bucket_contributions", [])) if qqq_summary is not None else [],
            "per_ticker_frozen_buckets": per_ticker_frozen_bucket_leaders,
        },
        "premium_bucket_rankings": {
            "shared_account_buckets": list(combined_summary.get("premium_bucket_contributions", [])),
            "qqq_only_buckets": list(qqq_summary.get("premium_bucket_contributions", [])) if qqq_summary is not None else [],
            "per_ticker_frozen_buckets": per_ticker_frozen_premium_leaders,
        },
        "friction_profiles": {
            "shared_account": dict(combined_summary.get("friction_profile", {})),
            "qqq_only": dict(qqq_summary.get("friction_profile", {})) if qqq_summary is not None else None,
            "per_ticker_frozen": {
                result["ticker"]: dict(result["summary"]["frozen_initial"].get("friction_profile", {}))
                for result in ticker_results
            },
        },
    }

    combined_candidates.to_csv(research_dir / "combined_promoted_candidates.csv", index=False)
    combined_trades.to_csv(research_dir / "combined_promoted_portfolio_trades.csv", index=False)
    combined_equity.to_csv(research_dir / "combined_promoted_portfolio_equity.csv", index=False)
    if qqq_summary is not None:
        qqq_candidates.to_csv(research_dir / "qqq_only_promoted_candidates.csv", index=False)
        qqq_trades.to_csv(research_dir / "qqq_only_promoted_portfolio_trades.csv", index=False)
        qqq_equity.to_csv(research_dir / "qqq_only_promoted_portfolio_equity.csv", index=False)
    contribution_rows_to_frame(
        list(combined_summary.get("family_contributions", [])),
        "family",
    ).to_csv(research_dir / "shared_account_family_contributions.csv", index=False)
    contribution_rows_to_frame(
        list(combined_summary.get("family_bucket_contributions", [])),
        "family_bucket",
    ).to_csv(research_dir / "shared_account_family_bucket_contributions.csv", index=False)
    contribution_rows_to_frame(
        list(combined_summary.get("premium_bucket_contributions", [])),
        "premium_bucket",
    ).to_csv(research_dir / "shared_account_premium_bucket_contributions.csv", index=False)
    if qqq_summary is not None:
        contribution_rows_to_frame(
            list(qqq_summary.get("family_contributions", [])),
            "family",
        ).to_csv(research_dir / "qqq_only_family_contributions.csv", index=False)
        contribution_rows_to_frame(
            list(qqq_summary.get("family_bucket_contributions", [])),
            "family_bucket",
        ).to_csv(research_dir / "qqq_only_family_bucket_contributions.csv", index=False)
        contribution_rows_to_frame(
            list(qqq_summary.get("premium_bucket_contributions", [])),
            "premium_bucket",
        ).to_csv(research_dir / "qqq_only_premium_bucket_contributions.csv", index=False)
    pd.DataFrame(family_detail_rows).to_csv(research_dir / "family_rankings.csv", index=False)
    pd.DataFrame(family_bucket_rows).to_csv(research_dir / "family_bucket_rankings.csv", index=False)
    pd.DataFrame(premium_bucket_rows).to_csv(research_dir / "premium_bucket_rankings.csv", index=False)
    (research_dir / "master_summary.json").write_text(json.dumps(master_payload, indent=2), encoding="utf-8")
    write_master_report(research_dir / "master_report.md", master_payload)
    run_manifest["result_snapshot"] = {
        "successful_tickers": [result["ticker"] for result in ticker_results],
        "failed_tickers": failed_tickers,
        "shared_account": {
            "final_equity": float(combined_summary["final_equity"]),
            "total_return_pct": float(combined_summary["total_return_pct"]),
            "max_drawdown_pct": float(combined_summary["max_drawdown_pct"]),
            "trade_count": int(combined_summary["trade_count"]),
        },
        "qqq_only": {
            "final_equity": float(qqq_summary["final_equity"]),
            "total_return_pct": float(qqq_summary["total_return_pct"]),
            "max_drawdown_pct": float(qqq_summary["max_drawdown_pct"]),
            "trade_count": int(qqq_summary["trade_count"]),
        } if qqq_summary is not None else None,
    }
    run_manifest["master_outputs"] = collect_master_output_lineage(research_dir)
    sync_manifest(status="completed", message="Run completed successfully.")
    append_run_registry(
        registry_path,
        {
            "version": RUN_MANIFEST_VERSION,
            "event": "completed",
            "timestamp_iso": utc_now_iso(),
            "run_id": run_id,
            "status": "completed",
            "research_dir": str(research_dir),
            "successful_tickers": [result["ticker"] for result in ticker_results],
            "failed_tickers": failed_tickers,
            "shared_account_final_equity": float(combined_summary["final_equity"]),
            "shared_account_total_return_pct": float(combined_summary["total_return_pct"]),
            "shared_account_max_drawdown_pct": float(combined_summary["max_drawdown_pct"]),
            "shared_account_trade_count": int(combined_summary["trade_count"]),
            "master_summary_path": str((research_dir / "master_summary.json").resolve()),
        },
    )
    print(json.dumps(master_payload, indent=2))


if __name__ == "__main__":
    main()
