from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build an operator-friendly live status report for an active down/choppy program."
    )
    parser.add_argument("--program-root", required=True)
    parser.add_argument("--report-dir", default="")
    parser.add_argument("--stale-minutes", type=int, default=20)
    return parser


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def parse_iso_timestamp(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    normalized = value.strip()
    if normalized.endswith("Z"):
        normalized = normalized[:-1] + "+00:00"
    try:
        return datetime.fromisoformat(normalized)
    except ValueError:
        return None


def iso_or_blank(moment: datetime | None) -> str:
    return moment.isoformat() if moment is not None else ""


def latest_iso_timestamp(*values: Any) -> str:
    moments = [parse_iso_timestamp(value) for value in values]
    valid_moments = [moment for moment in moments if moment is not None]
    if not valid_moments:
        return ""
    return max(valid_moments).isoformat()


def safe_mtime(path: Path | None) -> datetime | None:
    if path is None or not path.exists():
        return None
    return datetime.fromtimestamp(path.stat().st_mtime).astimezone()


def tail_nonempty_lines(path: Path, *, max_lines: int = 3) -> list[str]:
    if not path.exists():
        return []
    lines = [line.rstrip() for line in path.read_text(encoding="utf-8", errors="replace").splitlines()]
    return [line for line in lines if line.strip()][-max_lines:]


def process_is_running(pid: int | None) -> bool | None:
    if pid is None or pid <= 0:
        return None
    result = subprocess.run(
        ["tasklist", "/FI", f"PID eq {pid}", "/FO", "CSV", "/NH"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return None
    output = result.stdout.strip()
    if not output or "No tasks are running" in output:
        return False
    return str(pid) in output


def existing_path(path: Path) -> str | None:
    return str(path.resolve()) if path.exists() else None


def load_status(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    payload = load_json(path)
    return payload if isinstance(payload, dict) else {}


def effective_followon_statuses(
    *,
    validation_status: dict[str, Any],
    review_status: dict[str, Any],
    resume_followon_status: dict[str, Any],
    lane_source: str,
) -> tuple[dict[str, str], dict[str, str], dict[str, str], dict[str, str]]:
    validation_effective = {
        "phase": str(validation_status.get("phase", "")),
        "message": str(validation_status.get("message", "")),
        "updated_at_iso": str(validation_status.get("updated_at", "")),
    }
    review_effective = {
        "phase": str(review_status.get("phase", "")),
        "message": str(review_status.get("message", "")),
        "updated_at_iso": str(review_status.get("updated_at", "")),
    }
    replacement_effective = {
        "phase": "",
        "message": "",
        "updated_at_iso": "",
    }
    handoff_effective = {
        "phase": "",
        "message": "",
        "updated_at_iso": "",
    }

    resume_phase = str(resume_followon_status.get("phase", ""))
    resume_message = str(resume_followon_status.get("message", ""))
    resume_updated = str(resume_followon_status.get("updated_at", ""))

    if lane_source == "phase2_launch_pack" and resume_phase:
        if resume_phase in {"waiting", "phase2_running"}:
            validation_effective = {
                "phase": "pending_resume",
                "message": resume_message or "Resumed Phase 2 path is still running before validation starts.",
                "updated_at_iso": resume_updated,
            }
            review_effective = {
                "phase": "pending_resume",
                "message": "Waiting for resumed validation to finish before hardening review starts.",
                "updated_at_iso": resume_updated,
            }
            replacement_effective = {
                "phase": "pending_resume",
                "message": "Waiting for resumed validation and hardening review before replacement planning starts.",
                "updated_at_iso": resume_updated,
            }
            handoff_effective = {
                "phase": "pending_resume",
                "message": "Waiting for resumed validation, hardening review, and replacement planning before morning handoff starts.",
                "updated_at_iso": resume_updated,
            }
        elif resume_phase == "validating":
            validation_effective = {
                "phase": "validating",
                "message": resume_message or "Running live-book validation from the resumed Phase 2 path.",
                "updated_at_iso": resume_updated,
            }
            review_effective = {
                "phase": "pending_resume",
                "message": "Waiting for resumed validation to finish before hardening review starts.",
                "updated_at_iso": resume_updated,
            }
            replacement_effective = {
                "phase": "pending_resume",
                "message": "Waiting for resumed validation and hardening review before replacement planning starts.",
                "updated_at_iso": resume_updated,
            }
            handoff_effective = {
                "phase": "pending_resume",
                "message": "Waiting for resumed validation, hardening review, and replacement planning before morning handoff starts.",
                "updated_at_iso": resume_updated,
            }
        elif resume_phase == "reviewing":
            validation_effective = {
                "phase": "completed_resume",
                "message": "Validation completed through the resumed Phase 2 path.",
                "updated_at_iso": resume_updated,
            }
            review_effective = {
                "phase": "reviewing",
                "message": resume_message or "Building the hardening review from the resumed Phase 2 path.",
                "updated_at_iso": resume_updated,
            }
            replacement_effective = {
                "phase": "pending_resume",
                "message": "Waiting for resumed hardening review before replacement planning starts.",
                "updated_at_iso": resume_updated,
            }
            handoff_effective = {
                "phase": "pending_resume",
                "message": "Waiting for resumed replacement planning before morning handoff starts.",
                "updated_at_iso": resume_updated,
            }
        elif resume_phase == "planning_replacement":
            validation_effective = {
                "phase": "completed_resume",
                "message": "Validation completed through the resumed Phase 2 path.",
                "updated_at_iso": resume_updated,
            }
            review_effective = {
                "phase": "completed_resume",
                "message": "Hardening review completed through the resumed Phase 2 path.",
                "updated_at_iso": resume_updated,
            }
            replacement_effective = {
                "phase": "planning_replacement",
                "message": resume_message or "Building the replacement plan from the resumed Phase 2 path.",
                "updated_at_iso": resume_updated,
            }
            handoff_effective = {
                "phase": "pending_resume",
                "message": "Waiting for resumed replacement planning before morning handoff starts.",
                "updated_at_iso": resume_updated,
            }
        elif resume_phase == "building_morning_handoff":
            validation_effective = {
                "phase": "completed_resume",
                "message": "Validation completed through the resumed Phase 2 path.",
                "updated_at_iso": resume_updated,
            }
            review_effective = {
                "phase": "completed_resume",
                "message": "Hardening review completed through the resumed Phase 2 path.",
                "updated_at_iso": resume_updated,
            }
            replacement_effective = {
                "phase": "completed_resume",
                "message": "Replacement plan completed through the resumed Phase 2 path.",
                "updated_at_iso": resume_updated,
            }
            handoff_effective = {
                "phase": "building_morning_handoff",
                "message": resume_message or "Building the morning handoff packet from the resumed Phase 2 path.",
                "updated_at_iso": resume_updated,
            }
        elif resume_phase == "completed":
            validation_effective = {
                "phase": "completed_resume",
                "message": "Validation completed through the resumed Phase 2 path.",
                "updated_at_iso": resume_updated,
            }
            review_effective = {
                "phase": "completed_resume",
                "message": "Hardening review completed through the resumed Phase 2 path.",
                "updated_at_iso": resume_updated,
            }
            replacement_effective = {
                "phase": "completed_resume",
                "message": "Replacement plan completed through the resumed Phase 2 path.",
                "updated_at_iso": resume_updated,
            }
            handoff_effective = {
                "phase": "completed_resume",
                "message": "Morning handoff completed through the resumed Phase 2 path.",
                "updated_at_iso": resume_updated,
            }
        elif resume_phase == "failed":
            validation_effective = {
                "phase": "failed_resume",
                "message": resume_message or "Resumed Phase 2 follow-on failed.",
                "updated_at_iso": resume_updated,
            }
            review_effective = {
                "phase": "failed_resume",
                "message": "Resumed Phase 2 follow-on failed before hardening review could complete.",
                "updated_at_iso": resume_updated,
            }
            replacement_effective = {
                "phase": "failed_resume",
                "message": "Resumed Phase 2 follow-on failed before replacement planning could complete.",
                "updated_at_iso": resume_updated,
            }
            handoff_effective = {
                "phase": "failed_resume",
                "message": "Resumed Phase 2 follow-on failed before the morning handoff could complete.",
                "updated_at_iso": resume_updated,
            }

    return validation_effective, review_effective, replacement_effective, handoff_effective


def summarize_phase_statuses(research_dir: Path) -> dict[str, Any]:
    phase_files = sorted(research_dir.glob("*_phase_status.json"))
    rows: list[dict[str, Any]] = []
    for path in phase_files:
        payload = load_status(path)
        ticker = str(payload.get("ticker", path.stem.replace("_phase_status", ""))).upper()
        status = str(payload.get("status", "unknown"))
        phase = str(payload.get("phase", ""))
        message = str(payload.get("message", ""))
        timestamp_epoch = payload.get("timestamp_epoch")
        updated_at = (
            datetime.fromtimestamp(float(timestamp_epoch)).astimezone()
            if isinstance(timestamp_epoch, (int, float))
            else safe_mtime(path)
        )
        rows.append(
            {
                "ticker": ticker,
                "status": status,
                "phase": phase,
                "message": message,
                "phase_status_path": str(path),
                "updated_at_iso": iso_or_blank(updated_at),
            }
        )

    status_counts: dict[str, int] = {}
    for row in rows:
        status_counts[row["status"]] = status_counts.get(row["status"], 0) + 1

    running_rows = [row for row in rows if row["status"] == "running"]
    latest_row = max(
        rows,
        key=lambda row: parse_iso_timestamp(row["updated_at_iso"]) or datetime.min.astimezone(),
        default=None,
    )
    active_row = max(
        running_rows,
        key=lambda row: parse_iso_timestamp(row["updated_at_iso"]) or datetime.min.astimezone(),
        default=latest_row,
    )

    return {
        "phase_status_count": len(rows),
        "status_counts": status_counts,
        "active_ticker": active_row.get("ticker", "") if isinstance(active_row, dict) else "",
        "active_phase": active_row.get("phase", "") if isinstance(active_row, dict) else "",
        "active_message": active_row.get("message", "") if isinstance(active_row, dict) else "",
        "active_updated_at_iso": active_row.get("updated_at_iso", "") if isinstance(active_row, dict) else "",
        "phase_rows": rows,
    }


def summarize_lane(
    lane_row: dict[str, Any],
    *,
    stale_cutoff: datetime,
) -> dict[str, Any]:
    research_dir = Path(str(lane_row.get("research_dir", "")).strip())
    stdout_path = Path(str(lane_row.get("stdout_path", "")).strip()) if lane_row.get("stdout_path") else None
    stderr_path = Path(str(lane_row.get("stderr_path", "")).strip()) if lane_row.get("stderr_path") else None
    research_log_path = research_dir / "logs" / "research.log"
    master_summary_path = research_dir / "master_summary.json"
    run_manifest_path = research_dir / "run_manifest.json"

    phase_info = summarize_phase_statuses(research_dir) if research_dir.exists() else {
        "phase_status_count": 0,
        "status_counts": {},
        "active_ticker": "",
        "active_phase": "",
        "active_message": "",
        "active_updated_at_iso": "",
        "phase_rows": [],
    }

    activity_moments = [
        safe_mtime(stdout_path),
        safe_mtime(stderr_path),
        safe_mtime(research_log_path),
        parse_iso_timestamp(phase_info.get("active_updated_at_iso")),
    ]
    latest_activity = max([moment for moment in activity_moments if moment is not None], default=None)
    pid = int(lane_row["pid"]) if lane_row.get("pid") not in (None, "") else None
    process_running = process_is_running(pid)

    attention: list[str] = []
    if process_running is False and not master_summary_path.exists():
        attention.append("exited_without_master_summary")
    if process_running is True and latest_activity is not None and latest_activity < stale_cutoff:
        attention.append("activity_stale")
    if stdout_path is not None and not stdout_path.exists():
        attention.append("missing_stdout_log")
    if research_log_path.exists() and phase_info["phase_status_count"] == 0:
        attention.append("missing_phase_status_files")

    return {
        "lane_id": str(lane_row.get("lane_id", "")),
        "pid": pid,
        "process_running": process_running,
        "research_dir": str(research_dir),
        "stdout_path": existing_path(stdout_path) if stdout_path is not None else None,
        "stderr_path": existing_path(stderr_path) if stderr_path is not None else None,
        "research_log_path": existing_path(research_log_path),
        "run_manifest_path": existing_path(run_manifest_path),
        "master_summary_path": existing_path(master_summary_path),
        "has_master_summary": master_summary_path.exists(),
        "stdout_tail": tail_nonempty_lines(stdout_path) if stdout_path is not None else [],
        "stderr_tail": tail_nonempty_lines(stderr_path) if stderr_path is not None else [],
        "research_log_tail": tail_nonempty_lines(research_log_path),
        "latest_activity_at_iso": iso_or_blank(latest_activity),
        "phase_status_count": phase_info["phase_status_count"],
        "phase_status_counts": phase_info["status_counts"],
        "active_ticker": phase_info["active_ticker"],
        "active_phase": phase_info["active_phase"],
        "active_message": phase_info["active_message"],
        "active_updated_at_iso": phase_info["active_updated_at_iso"],
        "attention": attention,
    }


def build_payload(program_root: Path, *, stale_minutes: int) -> dict[str, Any]:
    now = datetime.now().astimezone()
    stale_cutoff = now - timedelta(minutes=stale_minutes)
    program_status = load_status(program_root / "program_status.json")
    phase1_status = load_status(program_root / "phase1_status.json")
    phase2_status = load_status(program_root / "phase2_status.json")
    phase2_launch_status = load_status(program_root / "phase2" / "launch_pack" / "launch_status.json")
    validation_status = load_status(program_root / "live_book_validation" / "validation_followon_status.json")
    review_status = load_status(
        program_root / "live_book_validation" / "hardening_review" / "hardening_review_followon_status.json"
    )
    replacement_plan_status = load_status(
        program_root / "live_book_validation" / "hardening_review" / "replacement_plan" / "replacement_plan_followon_status.json"
    )
    morning_handoff_status = load_status(
        program_root / "live_book_validation" / "hardening_review" / "morning_handoff" / "morning_handoff_followon_status.json"
    )
    resume_followon_status = load_status(program_root / "phase2_resume_followon_status.json")

    lane_source = "phase1"
    lane_rows = phase1_status.get("lanes") if isinstance(phase1_status.get("lanes"), list) else []
    if not lane_rows:
        lane_rows = phase2_status.get("lanes") if isinstance(phase2_status.get("lanes"), list) else []
        lane_source = "phase2"
    if isinstance(phase2_launch_status.get("rows"), list) and phase2_launch_status.get("rows"):
        lane_rows = phase2_launch_status.get("rows")
        lane_source = "phase2_launch_pack"

    program_phase = str(program_status.get("phase", ""))
    if lane_source == "phase2_launch_pack":
        resume_phase = str(resume_followon_status.get("phase", ""))
        launch_phase = str(phase2_launch_status.get("phase", ""))
        if resume_phase:
            program_phase = f"phase2_resumed:{resume_phase}"
        elif launch_phase:
            program_phase = f"phase2_resumed:{launch_phase}"

    validation_effective, review_effective, replacement_effective, handoff_effective = effective_followon_statuses(
        validation_status=validation_status,
        review_status=review_status,
        resume_followon_status=resume_followon_status,
        lane_source=lane_source,
    )
    if replacement_plan_status and not replacement_effective["phase"]:
        replacement_effective = {
            "phase": str(replacement_plan_status.get("phase", "")),
            "message": str(replacement_plan_status.get("message", "")),
            "updated_at_iso": str(replacement_plan_status.get("updated_at", "")),
        }
    if morning_handoff_status and not handoff_effective["phase"]:
        handoff_effective = {
            "phase": str(morning_handoff_status.get("phase", "")),
            "message": str(morning_handoff_status.get("message", "")),
            "updated_at_iso": str(morning_handoff_status.get("updated_at", "")),
        }

    summarized_lanes = [summarize_lane(dict(row), stale_cutoff=stale_cutoff) for row in lane_rows if isinstance(row, dict)]
    attention_items: list[dict[str, Any]] = []
    for lane in summarized_lanes:
        for token in lane["attention"]:
            attention_items.append(
                {
                    "type": token,
                    "lane_id": lane["lane_id"],
                    "research_dir": lane["research_dir"],
                    "active_ticker": lane["active_ticker"],
                    "active_phase": lane["active_phase"],
                }
            )

    program_updated_at_iso = latest_iso_timestamp(
        program_status.get("updated_at"),
        phase1_status.get("updated_at"),
        phase2_status.get("updated_at"),
        phase2_launch_status.get("updated_at"),
        resume_followon_status.get("updated_at"),
        validation_effective.get("updated_at_iso"),
        review_effective.get("updated_at_iso"),
        replacement_effective.get("updated_at_iso"),
        handoff_effective.get("updated_at_iso"),
        *[lane.get("latest_activity_at_iso") for lane in summarized_lanes],
    )

    return {
        "generated_at": iso_or_blank(now),
        "program_root": str(program_root),
        "program_phase": program_phase,
        "program_updated_at_iso": program_updated_at_iso,
        "stale_minutes": stale_minutes,
        "lane_source": lane_source,
        "phase1_status_path": existing_path(program_root / "phase1_status.json"),
        "phase2_status_path": existing_path(program_root / "phase2_status.json"),
        "phase2_launch_status_path": existing_path(program_root / "phase2" / "launch_pack" / "launch_status.json"),
        "validation_status": validation_effective,
        "hardening_review_status": review_effective,
        "replacement_plan_status": replacement_effective,
        "morning_handoff_status": handoff_effective,
        "phase2_resume_followon_status": {
            "phase": str(resume_followon_status.get("phase", "")),
            "message": str(resume_followon_status.get("message", "")),
            "updated_at_iso": str(resume_followon_status.get("updated_at", "")),
        },
        "lane_count": len(summarized_lanes),
        "running_lane_count": sum(1 for lane in summarized_lanes if lane.get("process_running") is True),
        "attention_count": len(attention_items),
        "attention_items": attention_items,
        "lanes": summarized_lanes,
    }


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "# Active Program Report",
        "",
        f"- Program root: `{payload['program_root']}`",
        f"- Program phase: `{payload['program_phase']}`",
        f"- Program updated: `{payload['program_updated_at_iso']}`",
        f"- Lane source: `{payload['lane_source']}`",
        f"- Lane count: `{payload['lane_count']}`",
        f"- Running lanes: `{payload['running_lane_count']}`",
        f"- Attention items: `{payload['attention_count']}`",
        "",
        "## Follow-On Status",
        "",
        f"- Validation: `{payload['validation_status']['phase']}` | {payload['validation_status']['message']}",
        f"- Hardening review: `{payload['hardening_review_status']['phase']}` | {payload['hardening_review_status']['message']}",
        f"- Replacement plan: `{payload['replacement_plan_status']['phase']}` | {payload['replacement_plan_status']['message']}",
        f"- Morning handoff: `{payload['morning_handoff_status']['phase']}` | {payload['morning_handoff_status']['message']}",
        f"- Phase 2 resume watcher: `{payload['phase2_resume_followon_status']['phase']}` | {payload['phase2_resume_followon_status']['message']}",
        "",
        "## Lanes",
        "",
    ]

    for lane in payload["lanes"]:
        lines.append(
            f"- `{lane['lane_id']}` | pid `{lane['pid']}` | running `{lane['process_running']}` | active `{lane['active_ticker']}` / `{lane['active_phase']}` | latest `{lane['latest_activity_at_iso']}`"
        )
        if lane["active_message"]:
            lines.append(f"  - message: {lane['active_message']}")
        if lane["phase_status_counts"]:
            counts = ", ".join(f"{key}={value}" for key, value in sorted(lane["phase_status_counts"].items()))
            lines.append(f"  - phase counts: {counts}")
        if lane["attention"]:
            lines.append(f"  - attention: {', '.join(lane['attention'])}")
        for line in lane["research_log_tail"][-2:]:
            lines.append(f"  - research.log: {line}")
        for line in lane["stdout_tail"][-2:]:
            if line not in lane["research_log_tail"]:
                lines.append(f"  - stdout: {line}")

    if payload["attention_items"]:
        lines.extend(["", "## Attention", ""])
        for item in payload["attention_items"]:
            lines.append(
                f"- `{item['type']}` on `{item['lane_id']}` | ticker `{item['active_ticker']}` | phase `{item['active_phase']}` | dir `{item['research_dir']}`"
            )

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = build_parser().parse_args()
    program_root = Path(args.program_root).resolve()
    report_dir = Path(args.report_dir).resolve() if args.report_dir else (program_root / "active_program_report")
    report_dir.mkdir(parents=True, exist_ok=True)

    payload = build_payload(program_root, stale_minutes=args.stale_minutes)
    write_json(report_dir / "active_program_report.json", payload)
    write_markdown(report_dir / "active_program_report.md", payload)
    print(
        json.dumps(
            {
                "report_dir": str(report_dir),
                "program_phase": payload["program_phase"],
                "lane_count": payload["lane_count"],
                "running_lane_count": payload["running_lane_count"],
                "attention_count": payload["attention_count"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
