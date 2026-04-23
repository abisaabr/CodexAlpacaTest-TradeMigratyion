from __future__ import annotations

import importlib.util
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "cleanroom"
    / "code"
    / "qqq_options_30d_cleanroom"
    / "build_gcp_shared_execution_lease_implementation_status.py"
)
SPEC = importlib.util.spec_from_file_location(
    "build_gcp_shared_execution_lease_implementation_status",
    MODULE_PATH,
)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_build_payload_detects_optional_gcs_store_wiring(tmp_path: Path) -> None:
    runner_repo_root = tmp_path / "runner"
    (runner_repo_root / "alpaca_lab" / "execution").mkdir(parents=True)
    (runner_repo_root / "alpaca_lab" / "multi_ticker_portfolio").mkdir(parents=True)
    (runner_repo_root / "scripts").mkdir(parents=True)
    (runner_repo_root / "tests").mkdir(parents=True)

    (runner_repo_root / "alpaca_lab" / "execution" / "ownership.py").write_text(
        "class LeaseConflictError(RuntimeError):\n    pass\n"
        "class ObjectLeaseRecord:\n    pass\n"
        "class ObjectLeaseStore(Protocol):\n    pass\n"
        "class GCSGenerationMatchLeaseStore:\n    pass\n"
        "class GenerationMatchOwnershipLease:\n"
        "    def renew(self, *, role: str):\n        return None\n"
        "    def release(self, *, role: str):\n        return None\n"
        "generation: str | None = None\n",
        encoding="utf-8",
    )
    (runner_repo_root / "alpaca_lab" / "multi_ticker_portfolio" / "config.py").write_text(
        'from typing import Literal\n'
        'lease_backend: Literal["file", "gcs_generation_match"] = "file"\n'
        "gcs_lease_uri: str | None = None\n",
        encoding="utf-8",
    )
    (runner_repo_root / "alpaca_lab" / "multi_ticker_portfolio" / "trader.py").write_text(
        "def _build_ownership_lease(self) -> Any:\n"
        '    if ownership.lease_backend == "file":\n'
        "        return None\n",
        encoding="utf-8",
    )
    (runner_repo_root / "scripts" / "run_multi_ticker_health_check.py").write_text(
        "def build_health_check_ownership_lease(portfolio_config):\n"
        '    if ownership.lease_backend == "gcs_generation_match":\n'
        "        return None\n",
        encoding="utf-8",
    )
    (runner_repo_root / "tests" / "test_execution_ownership.py").write_text(
        "def test_generation_match_ownership_lease_blocks_other_owner():\n    pass\n"
        "def test_generation_match_ownership_lease_allows_same_owner_multiple_roles():\n    pass\n"
        "def test_generation_match_ownership_lease_can_take_over_expired_lease():\n    pass\n"
        "def test_generation_match_ownership_lease_release_removes_last_role():\n    pass\n"
        "def test_gcs_generation_match_store_round_trips_payload():\n    pass\n"
        ,
        encoding="utf-8",
    )
    (runner_repo_root / "tests" / "test_multi_ticker_portfolio.py").write_text(
        "def test_trader_builds_generation_match_lease_when_gcs_backend_selected():\n    pass\n",
        encoding="utf-8",
    )
    (runner_repo_root / "tests" / "test_run_multi_ticker_health_check.py").write_text(
        "def test_build_health_check_ownership_lease_supports_gcs_backend():\n    pass\n",
        encoding="utf-8",
    )
    (runner_repo_root / "pyproject.toml").write_text(
        "[project]\n"
        "[project.optional-dependencies]\n"
        'gcp = ["google-cloud-storage>=2.18"]\n',
        encoding="utf-8",
    )

    payload = MODULE.build_payload(
        contract={
            "project_id": "codexalpaca",
            "recommended_lease": "gcs_generation_match_lease",
            "lease_object": "gs://codexalpaca-control-us/leases/paper-execution/lease.json",
        },
        runner_repo_root=runner_repo_root,
        targeted_tests_summary="6 passed",
        full_suite_summary="6 passed",
    )

    assert payload["implementation_status"] == "optional_gcs_store_wiring_landed_not_validated"
    assert payload["implementation_findings"]["gcs_store_present"] is True
    assert payload["implementation_findings"]["explicit_gcs_config_present"] is True
    assert payload["implementation_findings"]["health_check_support_present"] is True
    assert payload["implementation_findings"]["gcs_wiring_tests_present"] is True
    assert payload["implementation_findings"]["default_trader_path_is_still_file_lease"] is True
