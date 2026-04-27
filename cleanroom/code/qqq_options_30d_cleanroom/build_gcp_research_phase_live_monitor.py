from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[2]
DEFAULT_REPORT_DIR = REPO_ROOT / "docs" / "gcp_foundation"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build a distilled live-monitor packet for a long-running GCP research phase."
    )
    parser.add_argument("--observation-json", required=True)
    parser.add_argument("--report-dir", default=str(DEFAULT_REPORT_DIR))
    parser.add_argument("--packet-prefix", default="gcp_research_phase19_live_monitor")
    return parser


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _int_or_zero(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes"}
    return bool(value)


def _duration_seconds(value: Any) -> int | None:
    text = str(value or "").strip()
    if not text:
        return None
    if text.endswith("s"):
        text = text[:-1]
    try:
        return int(float(text))
    except ValueError:
        return None


def _latest_observed_symbol_family(log_tail: str) -> str | None:
    matches = re.findall(r"([A-Z]{1,6})\d{6}[CP]\d{8}", log_tail)
    if not matches:
        return None
    return f"{matches[-1]} option contracts"


def _latest_observed_download_date(log_tail: str) -> str | None:
    matches = re.findall(r"'start': '(\d{4}-\d{2}-\d{2})T", log_tail)
    if not matches:
        matches = re.findall(r"start=(\d{4}-\d{2}-\d{2})T", log_tail)
    return matches[-1] if matches else None


def _latest_log_observation_text(log_tail: str) -> str | None:
    matches = re.findall(r"\[(\d{2}/\d{2}/\d{2} \d{2}:\d{2}:\d{2})\]", log_tail)
    return matches[-1] if matches else None


def _active_stage(remote: dict[str, Any], gcs_final_artifacts_visible: bool) -> str:
    if _int_or_zero(remote.get("promotion_review_files")) > 0:
        return "promotion_review_packet"
    if _int_or_zero(remote.get("portfolio_report_files")) > 0:
        return "portfolio_report"
    if _int_or_zero(remote.get("replay_files")) > 0:
        return "option_aware_replay"
    if _int_or_zero(remote.get("raw_download_files")) > 0 or _int_or_zero(
        remote.get("silver_download_files")
    ) > 0:
        return "download_option_market_data_for_selected_contracts"
    if _int_or_zero(remote.get("selected_contract_files")) > 0:
        return "event_driven_contract_selection"
    if gcs_final_artifacts_visible:
        return "artifact_upload_or_completed"
    return "bootstrap_or_waiting"


def _status(batch_state: str, active_stage: str, remote: dict[str, Any]) -> str:
    if batch_state in {"FAILED", "DELETION_IN_PROGRESS", "CANCELLED"}:
        return "failed_needs_diagnosis"
    if batch_state == "SUCCEEDED":
        if active_stage in {"promotion_review_packet", "portfolio_report", "artifact_upload_or_completed"}:
            return "completed_artifacts_available"
        return "completed_artifacts_incomplete"
    if batch_state == "RUNNING":
        if active_stage == "download_option_market_data_for_selected_contracts":
            return "running_active_downloader"
        if active_stage in {"option_aware_replay", "portfolio_report", "promotion_review_packet"}:
            return f"running_{active_stage}"
        if remote.get("container_found") is False:
            return "running_container_not_found"
        return "running_progress_unclear"
    return f"batch_{batch_state.lower() or 'unknown'}"


def build_payload(observation: dict[str, Any]) -> dict[str, Any]:
    now = datetime.now(timezone.utc)
    remote = observation.get("remote_observation") or {}
    if not isinstance(remote, dict):
        remote = {}
    batch_state = str(observation.get("batch_state") or "UNKNOWN")
    gcs_final_artifacts_visible = _bool(observation.get("gcs_final_artifacts_visible"))
    active_stage = _active_stage(remote, gcs_final_artifacts_visible)
    log_tail = str(remote.get("log_tail_redacted") or "")
    run_duration_seconds = _duration_seconds(observation.get("batch_run_duration"))
    status = _status(batch_state, active_stage, remote)

    selected_contract_files = _int_or_zero(remote.get("selected_contract_files"))
    raw_download_files = _int_or_zero(remote.get("raw_download_files"))
    silver_download_files = _int_or_zero(remote.get("silver_download_files"))
    replay_files = _int_or_zero(remote.get("replay_files"))
    portfolio_report_files = _int_or_zero(remote.get("portfolio_report_files"))
    promotion_review_files = _int_or_zero(remote.get("promotion_review_files"))

    promotion_review_state = "not_started"
    if promotion_review_files > 0:
        promotion_review_state = "packet_files_present"
    elif portfolio_report_files > 0:
        promotion_review_state = "portfolio_report_ready"
    elif replay_files > 0:
        promotion_review_state = "replay_started"

    operator_read = [
        "Do not relaunch or terminate a running phase while the active stage is producing files or fresh logs.",
        "Expect final GCS artifacts only after the container exits if the job uses an exit-trap upload model.",
        "If the job fails, inspect run.err.log, downloader manifest, and partial local/GCS data before deciding on a smaller sharded repair.",
        "This is research-only. Do not arm windows, start trading, change live manifests, or change risk policy from this packet.",
    ]

    if status == "running_active_downloader":
        active_stage_detail = (
            "Alpaca options-data downloader is still active; replay and portfolio-report stages have not started."
        )
    elif status.startswith("running_option_aware_replay"):
        active_stage_detail = "Option-aware replay has started; promotion review remains downstream."
    elif status == "completed_artifacts_available":
        active_stage_detail = "Final artifacts are available for promotion review."
    else:
        active_stage_detail = "Inspect logs and artifact counts before changing orchestration."

    return {
        "generated_at": now.astimezone().isoformat(),
        "generated_at_utc": now.isoformat(),
        "project_id": observation.get("project_id"),
        "location": observation.get("location"),
        "zone": observation.get("zone"),
        "job_id": observation.get("job_id"),
        "wave_id": observation.get("wave_id"),
        "phase_id": observation.get("phase_id"),
        "status": status,
        "batch_state": batch_state,
        "run_duration_seconds_observed": run_duration_seconds,
        "batch_vm": observation.get("batch_vm"),
        "container": remote.get("container_name") or observation.get("container"),
        "container_status": remote.get("container_status"),
        "container_found": remote.get("container_found"),
        "active_stage": active_stage,
        "active_stage_detail": active_stage_detail,
        "latest_log_observation_text": _latest_log_observation_text(log_tail),
        "latest_observed_symbol_family": _latest_observed_symbol_family(log_tail),
        "latest_observed_download_date": _latest_observed_download_date(log_tail),
        "selected_contract_files": selected_contract_files,
        "raw_download_files": raw_download_files,
        "raw_download_bytes": _int_or_zero(remote.get("raw_download_bytes")),
        "silver_download_files": silver_download_files,
        "silver_download_bytes": _int_or_zero(remote.get("silver_download_bytes")),
        "download_report_files": _int_or_zero(remote.get("download_report_files")),
        "replay_files": replay_files,
        "portfolio_report_files": portfolio_report_files,
        "promotion_review_files": promotion_review_files,
        "gcs_final_artifacts_visible": gcs_final_artifacts_visible,
        "artifact_upload_model": str(observation.get("artifact_upload_model") or "final_exit_trap"),
        "promotion_review_state": promotion_review_state,
        "runtime_evidence_path": observation.get("runtime_evidence_path"),
        "operator_read": operator_read,
        "hard_rules": {
            "broker_facing": False,
            "trading_started": False,
            "manifest_changed": False,
            "risk_policy_changed": False,
        },
    }


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "# GCP Research Phase Live Monitor",
        "",
        "## Snapshot",
        "",
        f"- Generated at: `{payload['generated_at']}`",
        f"- Job ID: `{payload['job_id']}`",
        f"- Wave ID: `{payload['wave_id']}`",
        f"- Status: `{payload['status']}`",
        f"- Batch state: `{payload['batch_state']}`",
        f"- Observed runtime seconds: `{payload['run_duration_seconds_observed']}`",
        f"- Batch VM: `{payload['batch_vm']}`",
        f"- Container: `{payload['container']}`",
        f"- Container status: `{payload['container_status']}`",
        f"- Active stage: `{payload['active_stage']}`",
        f"- Active stage detail: {payload['active_stage_detail']}",
        f"- Latest log observation text: `{payload['latest_log_observation_text']}`",
        f"- Latest observed symbol family: `{payload['latest_observed_symbol_family']}`",
        f"- Latest observed download date: `{payload['latest_observed_download_date']}`",
        "",
        "## Local Container Evidence",
        "",
        f"- Selected-contract files: `{payload['selected_contract_files']}`",
        f"- Raw download files: `{payload['raw_download_files']}`",
        f"- Raw download bytes: `{payload['raw_download_bytes']}`",
        f"- Silver download files: `{payload['silver_download_files']}`",
        f"- Silver download bytes: `{payload['silver_download_bytes']}`",
        f"- Download-report files: `{payload['download_report_files']}`",
        f"- Replay files: `{payload['replay_files']}`",
        f"- Portfolio-report files: `{payload['portfolio_report_files']}`",
        f"- Promotion-review files: `{payload['promotion_review_files']}`",
        f"- GCS final artifacts visible: `{payload['gcs_final_artifacts_visible']}`",
        f"- Artifact upload model: `{payload['artifact_upload_model']}`",
        f"- Promotion-review state: `{payload['promotion_review_state']}`",
        "",
        "## Operator Read",
        "",
    ]
    for row in payload["operator_read"]:
        lines.append(f"- {row}")
    lines.extend(
        [
            "",
            "## Guardrails",
            "",
            f"- Broker-facing: `{payload['hard_rules']['broker_facing']}`",
            f"- Trading started: `{payload['hard_rules']['trading_started']}`",
            f"- Manifest changed: `{payload['hard_rules']['manifest_changed']}`",
            f"- Risk policy changed: `{payload['hard_rules']['risk_policy_changed']}`",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_handoff(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "# GCP Research Phase Live Monitor Handoff",
        "",
        f"- Status: `{payload['status']}`",
        f"- Batch state: `{payload['batch_state']}`",
        f"- Active stage: `{payload['active_stage']}`",
        f"- Latest observed symbol family: `{payload['latest_observed_symbol_family']}`",
        f"- Latest observed download date: `{payload['latest_observed_download_date']}`",
        f"- Selected-contract files: `{payload['selected_contract_files']}`",
        f"- Raw download files: `{payload['raw_download_files']}`",
        f"- Silver download files: `{payload['silver_download_files']}`",
        f"- Replay files: `{payload['replay_files']}`",
        f"- Portfolio-report files: `{payload['portfolio_report_files']}`",
        f"- Promotion-review state: `{payload['promotion_review_state']}`",
        f"- GCS final artifacts visible: `{payload['gcs_final_artifacts_visible']}`",
        "",
        "## Operator Rule",
        "",
    ]
    for row in payload["operator_read"]:
        lines.append(f"- {row}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = build_parser().parse_args()
    report_dir = Path(args.report_dir).resolve()
    payload = build_payload(read_json(Path(args.observation_json).resolve()))
    write_json(report_dir / f"{args.packet_prefix}.json", payload)
    write_markdown(report_dir / f"{args.packet_prefix}.md", payload)
    write_handoff(report_dir / f"{args.packet_prefix}_handoff.md", payload)
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
