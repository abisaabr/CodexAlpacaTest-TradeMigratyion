from __future__ import annotations

from pathlib import Path

from cleanroom.code.qqq_options_30d_cleanroom.build_gcp_vm_runtime_readiness_status import build_payload


def test_runtime_ready_when_paths_doctor_pytest_and_provenance_are_clean(tmp_path: Path) -> None:
    payload = build_payload(
        vm_name="vm-execution-paper-01",
        vm_runner_path="/opt/codexalpaca/codexalpaca_repo",
        source_provenance={"status": "provenance_matched"},
        data_writable=True,
        reports_writable=True,
        state_root_writable=True,
        run_root_writable=True,
        pytest_cache_writable=True,
        doctor_status="passed",
        vm_pytest_status="passed",
        vm_pytest_summary="137 passed",
        report_dir=tmp_path,
    )

    assert payload["status"] == "runtime_ready"
    assert payload["issues"] == []


def test_runtime_readiness_blocks_when_output_paths_are_not_writable(tmp_path: Path) -> None:
    payload = build_payload(
        vm_name="vm-execution-paper-01",
        vm_runner_path="/opt/codexalpaca/codexalpaca_repo",
        source_provenance={"status": "provenance_matched"},
        data_writable=False,
        reports_writable=True,
        state_root_writable=True,
        run_root_writable=True,
        pytest_cache_writable=True,
        doctor_status="passed",
        vm_pytest_status="passed",
        vm_pytest_summary="137 passed",
        report_dir=tmp_path,
    )

    assert payload["status"] == "blocked_vm_runtime_readiness"
    assert any(issue["code"] == "data_not_writable" for issue in payload["issues"])


def test_runtime_readiness_blocks_when_source_provenance_is_blocked(tmp_path: Path) -> None:
    payload = build_payload(
        vm_name="vm-execution-paper-01",
        vm_runner_path="/opt/codexalpaca/codexalpaca_repo",
        source_provenance={"status": "blocked_vm_runner_source_mismatch"},
        data_writable=True,
        reports_writable=True,
        state_root_writable=True,
        run_root_writable=True,
        pytest_cache_writable=True,
        doctor_status="passed",
        vm_pytest_status="passed",
        vm_pytest_summary="137 passed",
        report_dir=tmp_path,
    )

    assert payload["status"] == "blocked_vm_runtime_readiness"
    assert any(issue["code"] == "source_provenance_not_ready" for issue in payload["issues"])
