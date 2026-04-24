from __future__ import annotations

import importlib.util
from datetime import datetime, timezone
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "cleanroom"
    / "code"
    / "qqq_options_30d_cleanroom"
    / "build_gcp_execution_session_completion_gate.py"
)
SPEC = importlib.util.spec_from_file_location("build_gcp_execution_session_completion_gate", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


NOW = datetime(2026, 4, 24, 18, 0, tzinfo=timezone.utc)


def _output_paths(tmp_path: Path) -> dict[str, Path]:
    paths = {
        "session_reconciliation_handoff": tmp_path / "session_reconciliation_handoff.json",
        "execution_calibration_handoff": tmp_path / "execution_calibration_handoff.json",
        "execution_evidence_contract_handoff": tmp_path / "execution_evidence_contract_handoff.json",
        "morning_operator_brief_handoff": tmp_path / "morning_operator_brief_handoff.json",
    }
    for path in paths.values():
        path.write_text("{}", encoding="utf-8")
    return paths


def _base_kwargs(tmp_path: Path) -> dict:
    return {
        "report_dir": tmp_path,
        "launch_authorization": {
            "status": "ready_to_launch_session",
            "authorized_command_broker_facing": True,
            "generated_at": "2026-04-24T13:00:00+00:00",
        },
        "assimilation_status": {"status": "ready_for_post_session_assimilation"},
        "closeout_status": {"closeout_status": "window_already_closed"},
        "exclusive_window": {"exclusive_window_status": "awaiting_operator_confirmation"},
        "session_handoff": {
            "latest_traded_session_date": "2026-04-24",
            "posture": {"overall_session_reconciliation_posture": "caution"},
        },
        "execution_handoff": {"posture": {"overall_execution_posture": "caution"}},
        "evidence_handoff": {
            "contract_status": "ready",
            "generated_at": "2026-04-24T17:00:00+00:00",
            "latest_traded_session_date": "2026-04-24",
            "required_next_session_artifacts": ["broker-order audit"],
            "immediate_gaps": [],
        },
        "morning_brief_handoff": {"morning_decision_posture": "review_evidence"},
        "required_output_paths": _output_paths(tmp_path),
        "now": NOW,
    }


def test_completion_gate_awaits_launch_authorization_before_session(tmp_path: Path) -> None:
    kwargs = _base_kwargs(tmp_path)
    kwargs["launch_authorization"] = {
        "status": "blocked",
        "authorized_command_broker_facing": False,
        "generated_at": "2026-04-24T13:00:00+00:00",
    }
    kwargs["evidence_handoff"] = {
        "contract_status": "gapped",
        "generated_at": "2026-04-24T12:00:00+00:00",
        "latest_traded_session_date": "2026-04-16",
        "required_next_session_artifacts": ["broker-order audit"],
        "immediate_gaps": [{"check_id": "broker_order_audit", "summary": "Broker audit missing."}],
    }

    payload = MODULE.build_payload(**kwargs)

    assert payload["completion_status"] == "awaiting_launch_authorization"
    assert payload["next_operator_action"] == "do_not_review_unlaunched_session"
    assert any(issue["code"] == "launch_authorization_not_ready" for issue in payload["issues"])


def test_completion_gate_awaits_broker_session_after_launch_authorization(tmp_path: Path) -> None:
    kwargs = _base_kwargs(tmp_path)
    kwargs["evidence_handoff"] = {
        "contract_status": "gapped",
        "generated_at": "2026-04-24T12:00:00+00:00",
        "required_next_session_artifacts": ["broker-order audit"],
        "immediate_gaps": [{"check_id": "broker_activity_audit", "summary": "Broker activity missing."}],
    }

    payload = MODULE.build_payload(**kwargs)

    assert payload["completion_status"] == "awaiting_broker_session"
    assert payload["next_operator_action"] == "run_vm_session_command"
    assert any(issue["code"] == "post_launch_evidence_not_refreshed" for issue in payload["issues"])


def test_completion_gate_awaits_post_session_assimilation_after_authorized_launch(tmp_path: Path) -> None:
    kwargs = _base_kwargs(tmp_path)
    kwargs["assimilation_status"] = {"status": "blocked"}
    kwargs["evidence_handoff"] = {
        "contract_status": "gapped",
        "generated_at": "2026-04-24T17:00:00+00:00",
        "required_next_session_artifacts": ["broker-order audit"],
        "immediate_gaps": [{"check_id": "broker_activity_audit", "summary": "Broker activity missing."}],
    }

    payload = MODULE.build_payload(**kwargs)

    assert payload["completion_status"] == "awaiting_post_session_assimilation"
    assert payload["next_operator_action"] == "run_post_session_assimilation"
    assert any(issue["code"] == "post_session_assimilation_not_ready" for issue in payload["issues"])


def test_completion_gate_reports_evidence_gapped_after_assimilation(tmp_path: Path) -> None:
    kwargs = _base_kwargs(tmp_path)
    kwargs["evidence_handoff"] = {
        "contract_status": "gapped",
        "generated_at": "2026-04-24T17:00:00+00:00",
        "required_next_session_artifacts": ["broker-order audit"],
        "immediate_gaps": [{"check_id": "broker_order_audit", "summary": "Broker audit missing."}],
    }

    payload = MODULE.build_payload(**kwargs)

    assert payload["completion_status"] == "evidence_gapped"
    assert payload["next_operator_action"] == "repair_execution_evidence_bundle"
    assert any(issue["code"] == "broker_order_audit" for issue in payload["issues"])


def test_completion_gate_waits_for_closeout_before_review(tmp_path: Path) -> None:
    kwargs = _base_kwargs(tmp_path)
    kwargs["closeout_status"] = {"closeout_status": "ready_to_close_window"}

    payload = MODULE.build_payload(**kwargs)

    assert payload["completion_status"] == "awaiting_closeout"
    assert payload["next_operator_action"] == "close_exclusive_window"
    assert any(issue["code"] == "exclusive_window_not_closed" for issue in payload["issues"])


def test_completion_gate_marks_complete_for_review_when_evidence_clean_and_window_closed(tmp_path: Path) -> None:
    payload = MODULE.build_payload(**_base_kwargs(tmp_path))

    assert payload["completion_status"] == "session_complete_for_review"
    assert payload["next_operator_action"] == "review_session_evidence"
    assert payload["issues"] == []


def test_completion_gate_blocks_when_required_outputs_missing(tmp_path: Path) -> None:
    kwargs = _base_kwargs(tmp_path)
    missing_path = kwargs["required_output_paths"]["morning_operator_brief_handoff"]
    missing_path.unlink()

    payload = MODULE.build_payload(**kwargs)

    assert payload["completion_status"] == "control_outputs_missing"
    assert "morning_operator_brief_handoff" in payload["missing_required_outputs"]
